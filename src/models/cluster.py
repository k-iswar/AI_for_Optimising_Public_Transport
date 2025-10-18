import geopandas as gpd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy import create_engine

def cluster_stops(db_conn_str, n_clusters=10):
    """
    Performs K-Means clustering on transit stops.
    """
    engine = create_engine(db_conn_str)
    
    # Load stops data from PostGIS
    sql = "SELECT stop_id, stop_name, geometry FROM stops;"
    stops_gdf = gpd.read_postgis(sql, engine, geom_col='geometry', crs="EPSG:4326")
    
    # Feature Engineering: Use coordinates as features
    features = stops_gdf[['geometry']].copy()
    features['lon'] = features.geometry.x
    features['lat'] = features.geometry.y
    
    # Scale features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features[['lon', 'lat']])
    
    # K-Means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    stops_gdf['cluster'] = kmeans.fit_predict(scaled_features)
    
    print(f"Clustered {len(stops_gdf)} stops into {n_clusters} clusters.")
    
    # Optional: Save clustered data back to DB
    # stops_gdf[['stop_id', 'cluster']].to_sql('stop_clusters', engine, if_exists='replace', index=False)
    
    return stops_gdf

