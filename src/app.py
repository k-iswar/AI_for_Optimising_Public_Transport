import streamlit as st
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.optimize import build_transit_graph, find_optimal_route

# --- App Configuration ---
st.set_page_config(page_title="Public Transport Optimizer", layout="wide")
DB_CONNECTION_STRING = 'postgresql://user:password@db:5432/gtfs_db'  # Use service name 'db'

# --- Caching Data Loading ---
@st.cache_resource
def load_data():
    """
    Loads graph and stops data, caching the result.
    """
    engine = create_engine(DB_CONNECTION_STRING)
    graph = build_transit_graph(DB_CONNECTION_STRING)
    stops_df = pd.read_sql("SELECT stop_id, stop_name, stop_lat, stop_lon FROM stops", engine)
    return graph, stops_df

st.title("AI-Powered Public Transport Route Optimizer")

# --- Load Data ---
try:
    G, stops = load_data()
except Exception as e:
    st.error(f"Failed to connect to the database and load data. Please ensure the database container is running. Error: {e}")
    st.stop()

# --- User Inputs ---
st.sidebar.header("Route Planner")
start_stop_name = st.sidebar.selectbox("Select Start Stop", options=stops['stop_name'].unique())
end_stop_name = st.sidebar.selectbox("Select End Stop", options=stops['stop_name'].unique())

if st.sidebar.button("Find Optimal Route"):
    start_stop_id = stops[stops['stop_name'] == start_stop_name]['stop_id'].iloc[0]
    end_stop_id = stops[stops['stop_name'] == end_stop_name]['stop_id'].iloc[0]

    st.write(f"Finding route from **{start_stop_name}** to **{end_stop_name}**...")

    # In a full implementation, you would load the ARIMA model,
    # get a forecast for the selected time, and update graph weights here.

    path = find_optimal_route(G, start_stop_id, end_stop_id)

    if path:
        st.success("Optimal Route Found!")

        # Prepare data for map visualization
        path_df = stops[stops['stop_id'].isin(path)].copy()
        path_df['order'] = path_df['stop_id'].apply(lambda x: path.index(x))
        path_df = path_df.sort_values('order')

        st.subheader("Route Sequence:")
        st.dataframe(path_df[['stop_name', 'stop_id']])

        st.subheader("Route on Map:")
        st.map(path_df, latitude='stop_lat', longitude='stop_lon', size=50)
    else:
        st.error("Could not find a route between the selected stops.")

