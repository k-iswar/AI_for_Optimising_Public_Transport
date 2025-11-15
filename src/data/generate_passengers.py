import os
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

DB_CONNECTION_STRING = "postgresql://user:password@db:5432/gtfs_db"
OUTPUT_PATH = Path("data/raw/passenger_demand.csv")
TOTAL_PASSENGERS = 1_560_000


def fetch_stop_ids(engine):
    query = "SELECT stop_id FROM stops;"
    stops_df = pd.read_sql(query, engine)
    if stops_df.empty:
        raise ValueError("No stops found in database. Did you load GTFS data?")
    return stops_df["stop_id"].astype(str).values


def generate_request_times(size):
    categories = np.random.choice(
        ["morning", "evening", "offpeak"],
        size=size,
        p=[0.4, 0.4, 0.2],
    )

    request_times = np.zeros(size, dtype=int)

    def sample_times(mask, mean_hour, std_seconds):
        count = mask.sum()
        if count == 0:
            return
        samples = np.random.normal(mean_hour * 3600, std_seconds, count)
        samples = np.clip(samples, 0, 86_399)
        request_times[mask] = samples.astype(int)

    sample_times(categories == "morning", mean_hour=9, std_seconds=45 * 60)
    sample_times(categories == "evening", mean_hour=18, std_seconds=45 * 60)

    offpeak_mask = categories == "offpeak"
    count_offpeak = offpeak_mask.sum()
    if count_offpeak:
        request_times[offpeak_mask] = np.random.randint(
            0, 86_400, size=count_offpeak
        )

    return request_times


def generate_passengers(stop_ids):
    passenger_ids = np.arange(TOTAL_PASSENGERS, dtype=np.int64)
    origins = np.random.choice(stop_ids, size=TOTAL_PASSENGERS)
    destinations = np.random.choice(stop_ids, size=TOTAL_PASSENGERS)

    same_mask = origins == destinations
    while same_mask.any():
        destinations[same_mask] = np.random.choice(
            stop_ids, size=same_mask.sum()
        )
        same_mask = origins == destinations

    request_times = generate_request_times(TOTAL_PASSENGERS)

    df = pd.DataFrame(
        {
            "passenger_id": passenger_ids,
            "origin_id": origins,
            "destination_id": destinations,
            "request_time": request_times,
        }
    )
    return df


def main():
    engine = create_engine(DB_CONNECTION_STRING)
    stop_ids = fetch_stop_ids(engine)
    passengers_df = generate_passengers(stop_ids)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    passengers_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved passenger demand to {OUTPUT_PATH} ({len(passengers_df)} rows)")


if __name__ == "__main__":
    np.random.seed(42)
    main()

