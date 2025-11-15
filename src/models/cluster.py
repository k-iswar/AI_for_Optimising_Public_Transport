import os
from pathlib import Path

import geopandas as gpd
import pandas as pd
from joblib import dump
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy import create_engine

DB_CONNECTION_STRING = "postgresql://user:password@db:5432/gtfs_db"
N_CLUSTERS = 10
CLUSTERS_CSV = Path("data/raw/stop_clusters.csv")
MODEL_PATH = Path("models_artifacts/kmeans_model.pkl")


def load_stops(engine):
    query = "SELECT stop_id, stop_name, geometry FROM stops_geospatial;"
    return gpd.read_postgis(query, engine, geom_col="geometry")


def load_departure_counts(engine):
    query = """
        SELECT stop_id, COUNT(*) AS num_departures
        FROM stop_times
        GROUP BY stop_id
    """
    return pd.read_sql(query, engine)


def cluster_stops(db_conn_str=DB_CONNECTION_STRING, n_clusters=N_CLUSTERS):
    engine = create_engine(db_conn_str)

    stops_gdf = load_stops(engine)
    departures_df = load_departure_counts(engine)

    merged = stops_gdf.merge(departures_df, on="stop_id", how="left")
    merged["num_departures"] = merged["num_departures"].fillna(0)

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(merged[["num_departures"]])

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    merged["cluster"] = kmeans.fit_predict(scaled_features)

    CLUSTERS_CSV.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    merged[["stop_id", "cluster"]].to_csv(CLUSTERS_CSV, index=False)
    dump(kmeans, MODEL_PATH)

    print(f"Clustered {len(merged)} stops into {n_clusters} clusters.")
    print(f"Wrote assignments to {CLUSTERS_CSV} and model to {MODEL_PATH}.")

    return merged


if __name__ == "__main__":
    cluster_stops()