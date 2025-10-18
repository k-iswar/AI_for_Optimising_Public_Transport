import networkx as nx
import geopandas as gpd
from sqlalchemy import create_engine
import pandas as pd

def build_transit_graph(db_conn_str):
    """
    Builds a NetworkX graph from GTFS data.
    """
    engine = create_engine(db_conn_str)
    
    # Load stops as nodes
    stops_gdf = gpd.read_postgis("SELECT stop_id, geometry FROM stops;", engine, geom_col='geometry')
    
    G = nx.DiGraph()
    for _, row in stops_gdf.iterrows():
        G.add_node(row['stop_id'], pos=(row.geometry.x, row.geometry.y))
        
    # Load transit segments as edges
    # This query gets consecutive stops on the same trip and calculates travel time
    sql_edges = """
    WITH ranked_stops AS (
        SELECT
            trip_id,
            stop_id,
            EXTRACT(EPOCH FROM TO_TIMESTAMP(arrival_time, 'HH24:MI:SS')) as arrival_seconds,
            stop_sequence
        FROM stop_times
    )
    SELECT
        t1.stop_id as source,
        t2.stop_id as target,
        (t2.arrival_seconds - t1.arrival_seconds) as travel_time
    FROM ranked_stops t1
    JOIN ranked_stops t2 ON t1.trip_id = t2.trip_id AND t1.stop_sequence = t2.stop_sequence - 1
    WHERE (t2.arrival_seconds - t1.arrival_seconds) > 0;
    """
    edges_df = pd.read_sql(sql_edges, engine)
    
    # Add edges with travel time as weight
    for _, row in edges_df.iterrows():
        G.add_edge(row['source'], row['target'], weight=row['travel_time'])
        
    print(f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    return G

def find_optimal_route(graph, start_stop, end_stop):
    """
    Finds the shortest path between two stops using Dijkstra's algorithm.
    """
    try:
        path = nx.dijkstra_path(graph, source=start_stop, target=end_stop, weight='weight')
        length = nx.dijkstra_path_length(graph, source=start_stop, target=end_stop, weight='weight')
        print(f"Shortest path found with length (seconds): {length}")
        return path
    except nx.NetworkXNoPath:
        print("No path found between the specified stops.")
        return None

