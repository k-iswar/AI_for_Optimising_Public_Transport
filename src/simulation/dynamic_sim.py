import json
import pickle
import math
from collections import defaultdict, deque
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import simpy
from sqlalchemy import create_engine

DB_CONNECTION_STRING = "postgresql://user:password@db:5432/gtfs_db"
PASSENGER_PATH = Path("data/raw/passenger_demand.csv")
CLUSTERS_PATH = Path("data/raw/stop_clusters.csv")
MODELS_DIR = Path("models_artifacts/forecast_models")
RESULTS_DIR = Path("data/processed")
RESULTS_FILE = RESULTS_DIR / "dynamic_simulation_results.json"
BUS_CAPACITY = 60
DISPATCH_INTERVAL = 30 * 60  # seconds
SIM_DURATION = 24 * 60 * 60  # one day
AVG_SPEED_KMPH = 18  # rough city average
SIM_START_DATE = pd.Timestamp("2024-11-01")


def haversine_km(coord1, coord2):
    if coord1 is None or coord2 is None:
        return 0.0

    lat1, lon1 = coord1
    lat2, lon2 = coord2

    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


class DynamicSimulation:
    def __init__(self, sample_size=None):
        """
        Initialize the dynamic AI-driven simulation.
        
        Args:
            sample_size: If provided, only simulate first N passengers (for testing)
        """
        self.sample_size = sample_size
        self.passengers = self._load_passengers()
        (
            self.stop_to_cluster,
            self.cluster_to_stops,
        ) = self._load_clusters()
        self.prophet_models = self._load_models()
        self.stop_coordinates = self._load_stop_coordinates()

        self.env = simpy.Environment()
        self.stop_queues = defaultdict(deque)
        self.active_buses = defaultdict(int)

        self.wait_times = []
        self.total_km = 0.0
        self.passengers_served = 0

    def _load_passengers(self):
        df = pd.read_csv(PASSENGER_PATH)
        if self.sample_size:
            df = df.head(self.sample_size)
        df["origin_id"] = df["origin_id"].astype(str)
        df["destination_id"] = df["destination_id"].astype(str)
        df = df.sort_values("request_time").reset_index(drop=True)
        return df

    def _load_clusters(self):
        clusters_df = pd.read_csv(CLUSTERS_PATH)
        clusters_df["stop_id"] = clusters_df["stop_id"].astype(str)

        stop_to_cluster = clusters_df.set_index("stop_id")["cluster"].to_dict()
        cluster_to_stops = defaultdict(list)
        for stop_id, cluster in stop_to_cluster.items():
            cluster_to_stops[int(cluster)].append(stop_id)

        return stop_to_cluster, cluster_to_stops

    def _load_models(self):
        models = {}
        for cluster_id in range(10):
            model_path = MODELS_DIR / f"prophet_model_cluster_{cluster_id}.pkl"
            if not model_path.exists():
                raise FileNotFoundError(f"Missing model file {model_path}")
            with open(model_path, "rb") as fp:
                models[cluster_id] = pickle.load(fp)
        return models

    def _load_stop_coordinates(self):
        engine = create_engine(DB_CONNECTION_STRING)
        query = "SELECT stop_id, stop_lat, stop_lon FROM stops;"
        df = pd.read_sql(query, engine)
        df["stop_id"] = df["stop_id"].astype(str)
        coords = df.set_index("stop_id")[["stop_lat", "stop_lon"]].apply(tuple, axis=1)
        return coords.to_dict()

    def passenger_generator(self):
        last_time = 0
        for passenger in self.passengers.itertuples(index=False):
            wait_until = int(passenger.request_time)
            delta = max(0, wait_until - last_time)
            last_time = wait_until
            yield self.env.timeout(delta)

            queue = self.stop_queues[passenger.origin_id]
            queue.append(
                {
                    "arrival_time": self.env.now,
                    "origin_id": passenger.origin_id,
                    "destination_id": passenger.destination_id,
                }
            )

    def ai_dispatcher(self):
        # initial immediate evaluation
        yield self.env.timeout(0)
        while True:
            self._dispatch_buses()
            yield self.env.timeout(DISPATCH_INTERVAL)

    def _dispatch_buses(self):
        current_time = self.env.now
        forecast_time = SIM_START_DATE + pd.to_timedelta(current_time + 3600, unit="s")

        for cluster_id in range(10):
            model = self.prophet_models.get(cluster_id)
            if model is None:
                continue

            future = pd.DataFrame({"ds": [forecast_time]})
            forecast = model.predict(future)["yhat"].iloc[0]

            queue_size = sum(
                len(self.stop_queues[stop_id])
                for stop_id in self.cluster_to_stops.get(cluster_id, [])
            )

            demand_metric = max(0.0, forecast) + queue_size
            buses_needed = math.ceil(demand_metric / BUS_CAPACITY)
            active = self.active_buses[cluster_id]
            additional = max(0, buses_needed - active)

            for _ in range(additional):
                stop_id = self._select_busiest_stop(cluster_id)
                if stop_id is None:
                    break
                self.active_buses[cluster_id] += 1
                self.env.process(self.bus_process(stop_id, cluster_id))

    def _select_busiest_stop(self, cluster_id):
        """Select the stop with the longest queue in the cluster."""
        busiest_stop = None
        max_queue = 0
        cluster_stops = self.cluster_to_stops.get(cluster_id, [])
        
        if not cluster_stops:
            return None
            
        for stop_id in cluster_stops:
            queue_len = len(self.stop_queues[stop_id])
            if queue_len > max_queue:
                max_queue = queue_len
                busiest_stop = stop_id
        
        # If no queue, return first stop in cluster (so bus can wait there)
        if busiest_stop is None and cluster_stops:
            return cluster_stops[0]
            
        return busiest_stop

    def bus_process(self, stop_id, cluster_id):
        """Bus process that serves passengers from the busiest stop in cluster."""
        # Get the busiest stop in the cluster (might be different from dispatch stop)
        busiest_stop = self._select_busiest_stop(cluster_id)
        if busiest_stop is None:
            # No passengers in cluster, wait a bit then return
            yield self.env.timeout(5 * 60)
            self.active_buses[cluster_id] = max(0, self.active_buses[cluster_id] - 1)
            return
        
        queue = self.stop_queues[busiest_stop]
        boarded = []

        # Board passengers up to capacity
        while queue and len(boarded) < BUS_CAPACITY:
            passenger = queue.popleft()
            wait_time = self.env.now - passenger["arrival_time"]
            # Only record positive wait times
            if wait_time >= 0:
                self.wait_times.append(wait_time)
            self.passengers_served += 1
            boarded.append(passenger)

        if boarded:
            # Calculate trip distance (average distance per passenger)
            bus_distance = 0.0
            for passenger in boarded:
                origin_coord = self.stop_coordinates.get(passenger["origin_id"])
                destination_coord = self.stop_coordinates.get(
                    passenger["destination_id"]
                )
                if origin_coord and destination_coord:
                    bus_distance += haversine_km(origin_coord, destination_coord)
            
            # Average distance per passenger, then multiply by number of passengers
            if len(boarded) > 0:
                avg_distance = bus_distance / len(boarded)
                # Bus travels to serve all passengers (simplified: average route)
                bus_distance = avg_distance * len(boarded)

            trip_duration = max(
                10 * 60,  # Minimum 10 minutes
                min(60 * 60, (bus_distance / max(0.1, AVG_SPEED_KMPH)) * 3600),  # Max 1 hour
            )
            self.total_km += bus_distance
            yield self.env.timeout(trip_duration)
        else:
            # No passengers, wait a bit then return
            yield self.env.timeout(5 * 60)

        self.active_buses[cluster_id] = max(0, self.active_buses[cluster_id] - 1)

    def run(self):
        total_passengers = len(self.passengers)
        print(f"--- Running Dynamic (AI-Driven) Simulation for {total_passengers:,} passengers ---")
        
        self.env.process(self.passenger_generator())
        self.env.process(self.ai_dispatcher())
        
        # Run simulation for full day + extra time for buses to finish
        # Also add time for all passengers to arrive (max request_time)
        max_request_time = self.passengers['request_time'].max() if len(self.passengers) > 0 else SIM_DURATION
        simulation_end = max(SIM_DURATION, max_request_time) + 3 * 60 * 60  # 3 hours buffer
        
        self.env.run(until=simulation_end)

        return self.get_results()

    def get_results(self):
        """Returns results as a dictionary (for notebook use)."""
        remaining = sum(len(q) for q in self.stop_queues.values())
        average_wait_minutes = (
            (np.mean(self.wait_times) / 60) if self.wait_times else 0.0
        )
        total_cost = self.total_km * 116.26
        total_passengers = len(self.passengers)
        passengers_served = total_passengers - remaining

        return {
            'average_wait_minutes': average_wait_minutes,
            'total_cost': total_cost,
            'total_km': self.total_km,
            'passengers_served': passengers_served,
            'passengers_failed': remaining,
            'cost_per_passenger': total_cost / passengers_served if passengers_served > 0 else 0
        }

    def save_results(self, results):
        """Save results to JSON file for notebook loading."""
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Add metadata
        output = {
            'simulation_type': 'dynamic',
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
        print("\n=== Dynamic Simulation Summary ===")
        print(f"Average Wait Time (minutes): {results['average_wait_minutes']:.2f}")
        print(f"Total Cost (₹): {results['total_cost']:,.2f}")
        print(f"Total KMs Driven: {results['total_km']:,.2f}")
        print(f"Passengers Served: {results['passengers_served']:,}")
        print(f"Passengers Failed: {results['passengers_failed']:,}")
        print(f"Cost per Passenger (₹): {results['cost_per_passenger']:.2f}")
        
        # Save to file
        self.save_results(results)


def main(sample_size=None):
    sim = DynamicSimulation(sample_size=sample_size)
    results = sim.run()
    sim.print_results()
    return results


if __name__ == "__main__":
    np.random.seed(42)
    main()

