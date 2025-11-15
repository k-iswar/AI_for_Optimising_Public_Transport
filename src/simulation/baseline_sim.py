import json
import math
import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import simpy
from sqlalchemy import create_engine

DB_CONNECTION_STRING = "postgresql://user:password@db:5432/gtfs_db"
PASSENGER_PATH = Path("data/raw/passenger_demand.csv")
RESULTS_DIR = Path("data/processed")
RESULTS_FILE = RESULTS_DIR / "baseline_simulation_results.json"
TOTAL_KM = 645_000
KM_COST = 116.26


def time_to_seconds(time_str):
    """Convert HH:MM:SS time string to seconds."""
    hours, minutes, seconds = map(int, time_str.split(":"))
    return hours * 3600 + minutes * 60 + seconds


class BaselineSimulation:
    """
    Simulates the "baseline" static schedule.
    It loads all passengers and the real GTFS schedule, then calculates
    how long each passenger would have to wait.
    """

    def __init__(self, sample_size=None):
        """
        Initialize the baseline simulation.
        
        Args:
            sample_size: If provided, only simulate first N passengers (for testing)
        """
        self.env = simpy.Environment()
        self.engine = create_engine(DB_CONNECTION_STRING)
        self.sample_size = sample_size
        
        # Load passengers
        try:
            self.passengers = pd.read_csv(PASSENGER_PATH)
            if self.sample_size:
                self.passengers = self.passengers.head(self.sample_size)
            # Ensure origin_id is string for matching
            self.passengers['origin_id'] = self.passengers['origin_id'].astype(str)
            self.passengers = self.passengers.sort_values("request_time").reset_index(drop=True)
        except FileNotFoundError:
            print(f"FATAL ERROR: Passenger file not found at {PASSENGER_PATH}", file=sys.stderr)
            print("Please run 'docker compose run --rm web python src/data/generate_passengers.py' first.", file=sys.stderr)
            sys.exit(1)

        # Load static schedule
        print("Loading static GTFS schedule...")
        schedule_df = pd.read_sql("SELECT trip_id, stop_id, arrival_time FROM stop_times", self.engine)
        
        # Ensure stop_id is string (critical for matching)
        schedule_df['stop_id'] = schedule_df['stop_id'].astype(str)
        
        # Convert HH:MM:SS time to seconds for simulation
        schedule_df['arrival_seconds'] = schedule_df['arrival_time'].apply(time_to_seconds)
        
        # Create a dictionary for faster lookup (more robust than groupby)
        self.schedule_by_stop = {}
        for stop_id, group in schedule_df.groupby('stop_id'):
            self.schedule_by_stop[str(stop_id)] = group.sort_values('arrival_seconds')
        
        # Diagnostic: Check overlap between passenger stops and schedule stops
        passenger_stops = set(self.passengers['origin_id'].astype(str).unique())
        schedule_stops = set(self.schedule_by_stop.keys())
        overlap = passenger_stops.intersection(schedule_stops)
        
        print(f"...Schedule loaded.")
        print(f"   Unique stops in schedule: {len(schedule_stops):,}")
        print(f"   Unique stops in passenger data: {len(passenger_stops):,}")
        print(f"   Overlapping stops: {len(overlap):,}")
        
        if len(overlap) == 0:
            print("   ⚠️  WARNING: No matching stops found! Check stop_id formats.")
            # Show sample stop_ids for debugging
            print(f"   Sample passenger stop_ids: {list(passenger_stops)[:5]}")
            print(f"   Sample schedule stop_ids: {list(schedule_stops)[:5]}")
        elif len(overlap) < len(passenger_stops) * 0.5:
            print(f"   ⚠️  WARNING: Only {len(overlap)/len(passenger_stops)*100:.1f}% of passenger stops have schedules!")

        # KPI trackers
        self.wait_times = []
        self.passengers_failed = 0
        self.passengers_served = 0

    def passenger_process(self, passenger):
        """A process for a single passenger."""
        request_time = int(passenger['request_time'])
        origin_id = str(passenger['origin_id'])
        
        # Wait until their request time (simulation starts at 0)
        if request_time > self.env.now:
            yield self.env.timeout(request_time - self.env.now)
        
        # Check if this stop has a schedule
        if origin_id not in self.schedule_by_stop:
            # This stop_id was in passenger data but not in stop_times
            self.passengers_failed += 1
            return
        
        try:
            # Get the schedule for this stop
            stop_schedule = self.schedule_by_stop[origin_id]
            
            # Find all buses arriving at this stop *after* the passenger's request time
            # Use the sorted arrival_seconds column
            next_buses = stop_schedule[stop_schedule['arrival_seconds'] > request_time]
            
            if len(next_buses) == 0:
                # No more buses today for this stop after request time
                self.passengers_failed += 1
                return

            # Find the *very next* bus and calculate wait time
            next_bus_time = next_buses['arrival_seconds'].min()
            wait_time = next_bus_time - request_time
            
            # Wait for the bus (with a 45-min timeout)
            if wait_time > (45 * 60):
                self.passengers_failed += 1
                return
                
            yield self.env.timeout(wait_time)
            
            self.wait_times.append(wait_time)
            self.passengers_served += 1
            
        except Exception as e:
            # Log error but don't spam (only first few)
            if self.passengers_failed < 5:
                print(f"Sim error for stop {origin_id}: {e}", file=sys.stderr)
            self.passengers_failed += 1

    def run(self):
        """Runs the simulation by creating a process for each passenger."""
        total_passengers = len(self.passengers)
        print(f"--- Running Baseline (Static Schedule) Simulation for {total_passengers:,} passengers ---")
        
        for _, passenger in self.passengers.iterrows():
            self.env.process(self.passenger_process(passenger))
        
        self.env.run()  # Run the simulation
        return self.get_results()

    def get_results(self):
        """Returns results as a dictionary (for notebook use)."""
        avg_wait_min = (np.mean(self.wait_times) / 60) if self.wait_times else 0
        total_cost = TOTAL_KM * KM_COST
        cost_per_pax = total_cost / self.passengers_served if self.passengers_served > 0 else 0

        return {
            'average_wait_minutes': avg_wait_min,
            'total_cost': total_cost,
            'total_km': TOTAL_KM,
            'passengers_served': self.passengers_served,
            'passengers_failed': self.passengers_failed,
            'cost_per_passenger': cost_per_pax
        }

    def save_results(self, results):
        """Save results to JSON file for notebook loading."""
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Add metadata
        output = {
            'simulation_type': 'baseline',
            'timestamp': datetime.now().isoformat(),
            'sample_size': self.sample_size if self.sample_size else len(self.passengers),
            'results': results
        }
        
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {RESULTS_FILE}")

    def print_results(self):
        """Prints the final KPI table for our research."""
        results = self.get_results()
        print("\n=== Baseline Simulation Summary ===")
        print(f"Average Wait Time (minutes): {results['average_wait_minutes']:.2f}")
        print(f"Total Cost (₹): {results['total_cost']:,.2f}")
        print(f"Total KMs Driven: {results['total_km']:,}")
        print(f"Passengers Served: {results['passengers_served']:,}")
        print(f"Passengers Failed: {results['passengers_failed']:,}")
        print(f"Cost per Passenger (₹): {results['cost_per_passenger']:.2f}")
        
        # Save to file
        self.save_results(results)


def run_simulation(sample_size=None):
    """Convenience function for running the simulation."""
    sim = BaselineSimulation(sample_size=sample_size)
    results = sim.run()
    sim.print_results()
    return results


if __name__ == "__main__":
    run_simulation()

