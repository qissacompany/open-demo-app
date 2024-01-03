import streamlit as st
import requests
import boto3
import pandas as pd
import geopandas as gpd
import zipfile
import os
import io
import tempfile
import pyproj

#keys
consim_token = st.secrets["qissa_api"]['consim_token']
consim_url = st.secrets["qissa_api"]['consim_url']

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