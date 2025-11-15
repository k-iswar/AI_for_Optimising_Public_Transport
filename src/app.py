import streamlit as st
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
import sys
import os
import pydeck as pdk
import requests  # <-- NEW IMPORT
import json      # <-- NEW IMPORT

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.optimize import build_transit_graph, find_optimal_route

# --- App Configuration ---
st.set_page_config(page_title="Public Transport Optimizer", layout="wide")
DB_CONNECTION_STRING = 'postgresql://user:password@db:5432/gtfs_db'  # Use service name 'db'

# --- ORS API KEY BLOCK IS REMOVED ---

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

# --- NEW: Function to get snapped route from OSRM ---
@st.cache_data
def get_snapped_route(coordinates_list, profile='driving'):
    """
    Gets a route polyline from the local OSRM service snapped to roads.
    """
    # Convert list of [lon, lat] pairs to OSRM's required string format
    # e.g., "77.1,28.6;77.2,28.7"
    coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates_list])
    
    # OSRM server URL (using the docker-compose service name)
    url = f"http://osrm-router:5000/route/v1/{profile}/{coords_str}?geometries=geojson"
    
    try:
        r = requests.get(url)
        r.raise_for_status()  # Raise an error for bad responses
        data = r.json()
        
        # Extract the detailed coordinates from the response
        snapped_coords = data['routes'][0]['geometry']['coordinates']
        return snapped_coords
        
    except requests.exceptions.RequestException as e:
        st.error(f"Could not get snapped route from OSRM: {e}")
    except (KeyError, IndexError):
        st.error("OSRM returned an unexpected response. Is the route valid?")
        
    # Fallback: just return the original (straight-line) coordinates
    return [c for c in coordinates_list] # Return a copy

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

    path = find_optimal_route(G, start_stop_id, end_stop_id)

    if path:
        st.success("Optimal Route Found!")

        path_df = stops[stops['stop_id'].isin(path)].copy()
        path_df['order'] = path_df['stop_id'].apply(lambda x: path.index(x))
        path_df = path_df.sort_values('order')

        st.subheader("Route Sequence:")
        st.dataframe(path_df[['stop_name', 'stop_id']])

        st.subheader("Route on Map:")

        stop_coordinates = path_df[['stop_lon', 'stop_lat']].values.tolist()

        # --- Get snapped coordinates from OSRM ---
        st.info("Fetching detailed route from local OSRM server...")
        snapped_coordinates = get_snapped_route(stop_coordinates)
        st.info("...Route loaded.")
        
        # --- (The rest of your file is unchanged) ---
        
        intermediate_df = path_df[(path_df['order'] != 0) & (path_df['order'] != path_df['order'].max())]

        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=intermediate_df.to_dict('records') if not intermediate_df.empty else [],
            get_position=["stop_lon", "stop_lat"],
            get_color=[200, 0, 0],
            get_radius=60,
            pickable=True,
            auto_highlight=True,
        )

        path_layer = pdk.Layer(
            "PathLayer",
            data=[{"path": snapped_coordinates, "name": "Route"}],
            get_path="path",
            get_color=[0, 176, 240],
            get_width=5,
            width_min_pixels=4,
            rounded=True,
        )

        arrow_data = []
        for i in range(len(snapped_coordinates) - 1):
            arrow_data.append({
                "start": snapped_coordinates[i],
                "end": snapped_coordinates[i + 1],
            })
        
        arrow_layer = pdk.Layer(
            "ArrowLayer",
            data=arrow_data,
            get_start_position="start",
            get_end_position="end",
            get_color=[0, 0, 255],
            get_width=7,
            get_height=10,
            width_min_pixels=1,
        )

        ICON_URL = "https://img.icons8.com/color/48/marker.png" 

        start_point_data = [{
            "coordinates": stop_coordinates[0],
            "stop_name": path_df.iloc[0]['stop_name'],
            "icon_data": {
                "url": ICON_URL, "width": 128, "height": 128, "anchorY": 128,
            }
        }]
        
        end_point_data = [{
            "coordinates": stop_coordinates[-1],
            "stop_name": path_df.iloc[-1]['stop_name'],
            "icon_data": {
                "url": ICON_URL, "width": 128, "height": 128, "anchorY": 128,
            }
        }]

        start_layer = pdk.Layer(
            "IconLayer",
            data=start_point_data,
            get_icon="icon_data",
            get_position="coordinates",
            get_size=4,
            size_scale=15,
            get_color=[0, 200, 0],
            pickable=True,
            auto_highlight=True,
        )

        end_layer = pdk.Layer(
            "IconLayer",
            data=end_point_data,
            get_icon="icon_data",
            get_position="coordinates",
            get_size=4,
            size_scale=15,
            get_color=[200, 0, 0],
            pickable=True,
            auto_highlight=True,
        )

        deck = pdk.Deck(
            layers=[scatter_layer, path_layer, arrow_layer, start_layer, end_layer],
            initial_view_state=pdk.ViewState(
                latitude=path_df['stop_lat'].mean(),
                longitude=path_df['stop_lon'].mean(),
                zoom=12,
                pitch=45,
            ),
            map_style='dark',
            tooltip={"html": "<b>Stop:</b> {stop_name}"}
        )

        st.pydeck_chart(deck)
    else:
        st.error("Could not find a route between the selected stops.")