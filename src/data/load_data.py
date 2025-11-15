import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
import zipfile
import os
import sys

# --- THIS IS THE FIXED LINE ---
# Connect to the 'db' service, not 'localhost'
DB_CONNECTION_STRING = 'postgresql://user:password@db:5432/gtfs_db'
# ------------------------------

# --- THIS IS THE OTHER FIXED LINE ---
# Point to the correct path inside the container
GTFS_ZIP_PATH = 'data/raw/delhi-bus.zip'
# ------------------------------------


def load_gtfs_to_postgis(zip_path, conn_string):
    """
    Reads all .txt files from a GTFS zip archive and loads them as tables
    into a PostGIS database.
    Also converts stops.txt to a geospatial table.
    """
    try:
        engine = create_engine(conn_string)
        print("Database engine created.")

        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Process all text files
            stops_df = None
            for file in zf.namelist():
                if file.endswith('.txt'):
                    table_name = file.replace('.txt', '').lower()
                    print(f"Processing {file} -> table '{table_name}'...")
                    
                    try:
                        df = pd.read_csv(zf.open(file))
                    except Exception as read_err:
                        print(f"  └─ Skipping {file}: could not read ({read_err})", file=sys.stderr)
                        continue
                    
                    # Clean column names (e.g., "stop_id " -> "stop_id")
                    df.columns = df.columns.str.strip()

                    try:
                        df.to_sql(table_name, engine, if_exists='replace', index=False)
                        print(f"Successfully loaded {table_name}.")
                    except Exception as load_err:
                        print(f"  └─ Skipping {table_name}: database load failed ({load_err})", file=sys.stderr)
                        continue

                    if file.lower() == 'stops.txt':
                        stops_df = df.copy()

            # Specifically process stops.txt for geospatial data
            if stops_df is not None:
                if {'stop_lat', 'stop_lon'}.issubset(stops_df.columns):
                    print("\nConverting 'stops' table to geospatial table 'stops_geospatial'...")
                    
                    gdf = gpd.GeoDataFrame(
                        stops_df, 
                        geometry=gpd.points_from_xy(stops_df.stop_lon, stops_df.stop_lat),
                        crs="EPSG:4326"  # Standard WGS84 lat/lon
                    )
                    
                    try:
                        print("Loading GeoDataFrame to PostGIS...")
                        gdf.to_postgis('stops_geospatial', engine, if_exists='replace', index=False)
                        print("Successfully created 'stops_geospatial' table.")
                    except Exception as geo_err:
                        print(f"Warning: Could not create 'stops_geospatial' ({geo_err})", file=sys.stderr)
                else:
                    print("Warning: 'stops.txt' missing 'stop_lat'/'stop_lon'; skipping geospatial table.", file=sys.stderr)
            else:
                print("Warning: 'stops.txt' not found; skipping geospatial conversion.", file=sys.stderr)

        print("\nAll GTFS data loaded successfully.")

    except zipfile.BadZipFile:
        print(f"Error: Could not read zip file at {zip_path}", file=sys.stderr)
    except FileNotFoundError:
        print(f"Error: Zip file not found at {zip_path}", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        raise e

if __name__ == "__main__":
    load_gtfs_to_postgis(GTFS_ZIP_PATH, DB_CONNECTION_STRING)