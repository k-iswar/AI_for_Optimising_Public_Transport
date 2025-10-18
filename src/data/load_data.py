import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
from zipfile import ZipFile
import os

# --- Configuration ---
GTFS_ZIP_PATH = 'data/raw/in-maharashtra-msrtc-transit-gtfs-2336.zip'
DB_CONNECTION_STRING = 'postgresql://user:password@localhost:5432/gtfs_db'

def load_gtfs_to_postgis(gtfs_path, db_conn_str):
    """
    Loads GTFS data from a zip file into a PostGIS database.
    """
    engine = create_engine(db_conn_str)
    print("Database engine created.")

    # GTFS files to load
    files_to_load = [
        'agency.txt', 'routes.txt', 'trips.txt', 'calendar.txt',
        'calendar_dates.txt', 'stop_times.txt', 'stops.txt', 'shapes.txt'
    ]

    with ZipFile(gtfs_path) as myzip:
        for file in files_to_load:
            if file in myzip.namelist():
                table_name = os.path.splitext(file)[0]  # Get filename without extension
                print(f"Processing {file} -> table '{table_name}'...")

                with myzip.open(file) as f:
                    df = pd.read_csv(f)

                    # Handle spatial data for stops and shapes
                    if table_name == 'stops':
                        gdf = gpd.GeoDataFrame(
                            df,
                            geometry=gpd.points_from_xy(df.stop_lon, df.stop_lat),
                            crs="EPSG:4326"  # WGS84 CRS
                        )
                        gdf.to_postgis(table_name, engine, if_exists='replace', index=False)
                    elif table_name == 'shapes':
                        gdf = gpd.GeoDataFrame(
                            df,
                            geometry=gpd.points_from_xy(df.shape_pt_lon, df.shape_pt_lat),
                            crs="EPSG:4326"
                        )
                        gdf.to_postgis(table_name, engine, if_exists='replace', index=False)
                    else:
                        df.to_sql(table_name, engine, if_exists='replace', index=False)

                print(f"Successfully loaded {table_name} to PostGIS.")
            else:
                print(f"Warning: {file} not found in zip archive.")

if __name__ == '__main__':
    load_gtfs_to_postgis(GTFS_ZIP_PATH, DB_CONNECTION_STRING)

