import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from prophet import Prophet

PASSENGER_PATH = Path("data/raw/passenger_demand.csv")
CLUSTERS_PATH = Path("data/raw/stop_clusters.csv")
OUTPUT_DIR = Path("models_artifacts/forecast_models")
NUM_CLUSTERS = 10
NUM_DAYS = 90
BASE_DATE = pd.Timestamp("2024-08-01")


def load_data():
    passengers = pd.read_csv(PASSENGER_PATH)
    clusters = pd.read_csv(CLUSTERS_PATH)
    passengers["origin_id"] = passengers["origin_id"].astype(str)
    clusters["stop_id"] = clusters["stop_id"].astype(str)
    merged = passengers.merge(
        clusters,
        left_on="origin_id",
        right_on="stop_id",
        how="left",
        validate="many_to_one",
    )
    if merged["cluster"].isna().any():
        raise ValueError("Some passengers do not map to a cluster. Check stop_clusters.csv.")
    merged["hour"] = (merged["request_time"] // 3600).astype(int)
    return merged


def build_historical_timeseries(passengers):
    baseline = (
        passengers.groupby(["cluster", "hour"])
        .size()
        .reset_index(name="count")
    )

    history_frames = []
    for day_idx in range(NUM_DAYS):
        current_date = BASE_DATE + pd.Timedelta(days=day_idx)
        weekend_factor = 1.3 if current_date.weekday() in (5, 6) else 1.0
        daily = baseline.copy()
        noise = np.random.normal(1.0, 0.05, len(daily))
        daily["y"] = (
            daily["count"] * weekend_factor * noise
        ).clip(lower=0).round().astype(int)
        daily["ds"] = current_date + pd.to_timedelta(daily["hour"], unit="h")
        history_frames.append(daily[["cluster", "ds", "y"]])

    history = pd.concat(history_frames, ignore_index=True)
    return history


def build_holidays_df():
    holidays = pd.DataFrame(
        {
            "holiday": ["Diwali", "Republic_Day", "Independence_Day"],
            "ds": [
                pd.Timestamp("2024-10-31"),
                pd.Timestamp("2024-01-26"),
                pd.Timestamp("2024-08-15"),
            ],
            "lower_window": 0,
            "upper_window": 0,
        }
    )
    return holidays


def train_prophet_models(history, holidays):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for cluster_id in range(NUM_CLUSTERS):
        cluster_history = (
            history[history["cluster"] == cluster_id][["ds", "y"]]
            .sort_values("ds")
            .reset_index(drop=True)
        )

        if cluster_history.empty:
            print(f"No history for cluster {cluster_id}, skipping.")
            continue

        model = Prophet(
            holidays=holidays,
            daily_seasonality=True,
            weekly_seasonality=True,
        )
        model.fit(cluster_history)

        output_path = OUTPUT_DIR / f"prophet_model_cluster_{cluster_id}.pkl"
        with open(output_path, "wb") as fp:
            pickle.dump(model, fp)
        print(f"Saved model for cluster {cluster_id} to {output_path}")


def main():
    passengers = load_data()
    history = build_historical_timeseries(passengers)
    holidays = build_holidays_df()
    train_prophet_models(history, holidays)


if __name__ == "__main__":
    np.random.seed(42)
    main()