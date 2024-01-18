import streamlit as st
import requests
import boto3
import pandas as pd
import geopandas as gpd
import numpy as np
import zipfile
import os
import io
import tempfile
import pyproj
from shapely.geometry import LineString, Point

#keys
consim_token = st.secrets["qissa_api"]['consim_token']
consim_url = st.secrets["qissa_api"]['consim_url']
footheat_token = st.secrets["qissa_api"]['footheat_token']
footheat_url = st.secrets["qissa_api"]['footheat_url']

bucket_key = st.secrets["client_bucket"]['BUCKET_idkey']
bucket_secret = st.secrets["client_bucket"]['BUCKET_secretkey']
bucket_url = st.secrets["client_bucket"]['BUCKET_url']
bucket_name = st.secrets["client_bucket"]['BUCKET_name']

@st.cache_data(max_entries=1)
def consim_call(params: dict):
    payload = params    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {consim_token}"
    }
    response = requests.post(consim_url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        st.warning(f"API-call error: {response.status_code}, {response.text}")
        return None

@st.cache_data(max_entries=1)
def footheat_call(params: dict):
    payload = params    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {footheat_token}"
    }
    response = requests.post(footheat_url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        st.warning(f"API-call error: {response.status_code}, {response.text}")
        return None
    

def get_demo_file(demo_name, folder="demo_plans", bucket_name=bucket_name):
    zip_file_name = f"{folder}/{demo_name}.zip"
    s3 = boto3.client('s3', endpoint_url=f'https://{bucket_url}',
                            aws_access_key_id=bucket_key,
                            aws_secret_access_key=bucket_secret)
    zip_file_data = s3.get_object(Bucket=bucket_name, Key=zip_file_name)['Body'].read()
    # Creating a file-like object from the zip data
    zip_file = io.BytesIO(zip_file_data)
    return zip_file


def extract_shapefiles_and_filenames_from_zip(file, geom_type):
    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)
        
        potential_files = []
        for filename in os.listdir(tmp_dir):
            if filename.endswith(".shp"):
                shapefile_path = os.path.join(tmp_dir, filename)
                data = gpd.read_file(shapefile_path)

                # Convert columns with numeric strings to numeric values
                for col in data.columns:
                    if data[col].dtype == object:  # Check if column type is object, often indicating strings
                        data[col] = pd.to_numeric(data[col], errors='ignore')  # Convert to numeric if possible
                
                # Collect files with the expected geometry type
                if any(data.geometry.geom_type == geom_type):
                    potential_files.append((data, filename))
                
        # Process the right file, if found
        for data, filename in potential_files:
            # Check if the CRS is missing in the GeoDataFrame
            if data.crs is None:
                prj_file_path = os.path.splitext(shapefile_path)[0] + ".prj"
                if os.path.exists(prj_file_path):
                    with open(prj_file_path, 'r') as prj_file:
                        prj_text = prj_file.read().strip()
                    crs = pyproj.CRS.from_string(prj_text)
                    data.crs = crs
            
            # Check if CRS is not EPSG:4326, then convert to EPSG:4326
            if data.crs != 'EPSG:4326':
                data = data.to_crs('EPSG:4326')
            
            return data, filename
    
    return None, None


def prepare_network_json(buildings_gdf, network_gdf, reso=50, volume_col='volume', search_radius=50):

    #helper for api serialization
    def convert_numpy_to_python(item):
        if isinstance(item, np.integer):
            return int(item)
        elif isinstance(item, np.floating):
            return float(item)
        elif isinstance(item, np.ndarray):
            return item.tolist()
        elif isinstance(item, list):
            return [convert_numpy_to_python(subitem) for subitem in item]
        elif isinstance(item, dict):
            return {key: convert_numpy_to_python(val) for key, val in item.items()}
        else:
            return item
        
    # Densify network geometry function
    def densify_geometry(line, dist=reso):
        if isinstance(line, LineString) and line.length > 0:
            num_segments = max(1, int(line.length // dist))
            return [LineString([line.interpolate(dist * i), line.interpolate(min(dist * (i + 1), line.length))]) for i in range(num_segments)]
        return []

    # Filter out non-LineString geometries and empty geometries from network_gdf and convert crs to projected
    projected_crs = network_gdf.estimate_utm_crs()
    network_gdf = network_gdf[network_gdf.geometry.type == 'LineString'].to_crs(projected_crs)
    network_gdf = network_gdf[network_gdf.geometry.length > 0].to_crs(projected_crs)

    # Apply densify_geometry
    densified_lines = network_gdf.geometry.apply(lambda x: densify_geometry(x)).explode().reset_index(drop=True)

    # Check for non-LineString geometries
    if not all(isinstance(item, LineString) for item in densified_lines):
        invalid_items = [type(item) for item in densified_lines if not isinstance(item, LineString)]
        raise ValueError(f"Densification resulted in non-LineString geometries: {invalid_items}")

    # Convert the densified linestring segments into points
    points = [Point(coord) for line in densified_lines for coord in line.coords]

    # Create GeoDataFrame for points in the projected CRS
    points_gdf = gpd.GeoDataFrame(geometry=points, crs=projected_crs)

    # Convert buildings_gdf to the same projected CRS
    buildings_gdf_projected = buildings_gdf.to_crs(projected_crs)

    # Find all buildings within search_radius of each network point in projected CRS
    aggregated_volumes = {}
    for idx, point in enumerate(points_gdf.geometry):
        point_buffer = point.buffer(search_radius)
        nearby_buildings = buildings_gdf_projected[buildings_gdf_projected.intersects(point_buffer)]
        total_volume = nearby_buildings[volume_col].sum()
        aggregated_volumes[idx] = total_volume
    
    # Convert points_gdf back to EPSG:4326 for JSON output
    points_gdf = points_gdf.to_crs("EPSG:4326")

    # Prepare network points data with aggregated volumes and coordinates
    network_points = [{'id': int(i), 'volume': aggregated_volumes.get(i, 0), 'coords': [float(coord) for coord in points_gdf.iloc[i].geometry.coords[0]]} for i in range(len(points_gdf))]

    # Prepare network edges data
    network_edges = [{'start_id': int(i), 'end_id': int(i+1)} for i in range(len(points_gdf) - 1)]

    # Compile final JSON
    network_json = {
        "points": network_points,
        "edges": network_edges
    }
    
    # Convert all NumPy data types to native Python types for JSON serialization
    network_json = convert_numpy_to_python(network_json)

    return network_json