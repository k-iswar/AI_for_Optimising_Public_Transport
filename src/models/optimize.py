import pandas as pd
import geopandas as gpd
import networkx as nx
from sqlalchemy import create_engine
from shapely.geometry import LineString
import time

def build_transit_graph(DB_CONNECTION_STRING):
    """
    Builds a multi-modal transit graph (walking + transit) from PostGIS data.
    
    Nodes: stop_ids
    Edges:
    1. 'walk': Walking transfers between nearby stops.
    2. 'transit': Direct transit links between stops on the same trip.
    """
    print("Building transit graph...")
    engine = create_engine(DB_CONNECTION_STRING)
    
    # Load stops from the 'stops_geospatial' table, not the 'stops' table
    stops_gdf = gpd.read_postgis("SELECT * FROM stops_geospatial;", engine, geom_col='geometry')
    
    stops_gdf = stops_gdf.set_index('stop_id')
    print(f"Loaded {len(stops_gdf)} stops.")

    # Load stop times
    stop_times_df = pd.read_sql("SELECT trip_id, stop_id, stop_sequence, arrival_time FROM stop_times", engine)
    stop_times_df.sort_values(['trip_id', 'stop_sequence'], inplace=True)
    print(f"Loaded {len(stop_times_df)} stop_times.")

    G = nx.DiGraph()

    # 1. Add all stops as nodes
    for stop_id, data in stops_gdf.iterrows():
        G.add_node(stop_id, **data.to_dict())

    # 2. Add 'transit' edges
    print("Adding transit edges...")
    trip_groups = stop_times_df.groupby('trip_id')
    
    for trip_id, group in trip_groups:
        for i in range(len(group) - 1):
            start_stop = group.iloc[i]
            end_stop = group.iloc[i+1]
            
            start_id = start_stop['stop_id']
            end_id = end_stop['stop_id']
            
            try:
                # Assuming time is in 'HH:MM:SS' format, convert to seconds
                start_time = sum(x * int(t) for x, t in zip([3600, 60, 1], start_stop['arrival_time'].split(':')))
                end_time = sum(x * int(t) for x, t in zip([3600, 60, 1], end_stop['arrival_time'].split(':')))
                duration = max(60, end_time - start_time) # Ensure at least 60s travel time
            except Exception:
                duration = 300 # Default to 5 minutes if time parsing fails

            G.add_edge(start_id, end_id, weight=duration, type='transit', trip_id=trip_id)

    # 3. Add 'walk' edges (transfers)
    print("Adding walking transfer edges...")
    
    # Create a new GeoDataFrame for the join to avoid modifying the original
    stops_with_buffer = stops_gdf.copy()
    stops_with_buffer['geometry'] = stops_gdf.geometry.buffer(0.004) # Approx 400m
    
    # --- CHANGE 1: Reset index so 'stop_id' becomes a column ---
    # This makes the join explicitly create a 'stop_id_right' column
    stops_with_buffer = stops_with_buffer.reset_index() 
    
    possible_transfers = gpd.sjoin(stops_gdf, stops_with_buffer, how='left', predicate='within')
    
    for start_id, transfer_row in possible_transfers.iterrows():
        
        # --- CHANGE 2: Access 'stop_id_right' instead of 'index_right' ---
        end_id = transfer_row['stop_id_right']
        
        # --- CHANGE 3: Add a check for NaN (for stops with no transfers) ---
        if pd.isna(end_id):
            continue
            
        if start_id != end_id and not G.has_edge(start_id, end_id):
            # Add a 'walk' edge with weight based on distance
            # (Using a simple 5-minute walk time for any transfer)
            G.add_edge(start_id, end_id, weight=300, type='walk')

    print(f"Graph build complete. {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")
    return G

def find_optimal_route(graph, start_stop_id, end_stop_id):
    """
    Finds the shortest path in the graph using Dijkstra's algorithm.
    """
    try:
        path = nx.dijkstra_path(graph, source=start_stop_id, target=end_stop_id, weight='weight')
        return path
    except nx.NetworkXNoPath:
        return None