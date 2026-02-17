from .logs import die, info
import requests
import zipfile
import geopandas as gpd
import pandas as pd
import json
import time
import re
from pathlib import Path
from datetime import datetime


def get_latest_caop_url() -> tuple[str, str]:
    """Checks DGT website for the latest CAOP version available,
    searching backwards from current year until a valid version is found.

    Returns:
        tuple: (url, version_name) of the latest CAOP file
    """
    try:
        base_url = "https://geo2.dgterritorio.gov.pt/caop/"
        current_year = datetime.now().year

        # Search backwards up to 5 years
        for year in range(current_year, current_year - 5, -1):
            url = f"{base_url}CAOP_Continente_{year}_1-gpkg.zip"
            r = requests.head(url, allow_redirects=True, timeout=10)
            if r.status_code == 200:
                version = f"CAOP_Continente_{year}_1"
                info(f"Latest CAOP version found: {version}")
                return url, version
            info(f"CAOP {year} not available, trying {year - 1}...")

        die("Could not find a valid CAOP version in the last 5 years")
    except Exception as e:
        die(f"get_latest_caop_url: {e}")


def caop_already_downloaded(download_dir: str, version: str) -> bool:
    """Checks if this CAOP version is already downloaded and extracted

    Args:
        download_dir (str): the directory where data is stored
        version (str): the CAOP version name (e.g. 'CAOP_Continente_2024_1')

    Returns:
        bool: True if already downloaded
    """
    version_file = Path(download_dir) / f"{version}.version"
    gpkg_files = list(Path(download_dir).glob("*.gpkg"))

    if version_file.exists() and gpkg_files:
        info(f"CAOP {version} already downloaded - skipping")
        return True

    return False


def mark_caop_downloaded(download_dir: str, version: str) -> None:
    """Writes a version marker file after successful download

    Args:
        download_dir (str): the directory where data is stored
        version (str): the CAOP version name
    """
    version_file = Path(download_dir) / f"{version}.version"
    version_file.write_text(f"Downloaded: {datetime.now().isoformat()}")


def download_data(url: str, fname: str) -> None:
    """Downloads data from URL and stores it locally

    Args:
        url: URL with location of the original data
        fname (str): the name of the data file to save locally
    """
    try:
        info(f"Downloading from {url}")
        r = requests.get(url, stream=True, allow_redirects=True)
        r.raise_for_status()

        total_size = int(r.headers.get('content-length', 0))
        with open(fname, "wb") as f:
            if total_size:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            else:
                f.write(r.content)
        info(f"Downloaded to {fname}")
    except Exception as e:
        die(f"download_data: {e}")


def read_gpkg(fname: str, layer: str = None) -> gpd.GeoDataFrame:
    """Reads a GeoPackage into a GeoDataFrame

    Args:
        fname (str): the name of the GeoPackage file
        layer (str): the layer name to read

    Returns:
        gpd.GeoDataFrame: the geodataframe
    """
    try:
        gdf = gpd.read_file(fname, layer=layer)
    except Exception as e:
        die(f"read_gpkg: {e}")
    return gdf


def write_geojson(gdf: gpd.GeoDataFrame, fname: str) -> None:
    """Writes a GeoDataFrame to GeoJSON

    Args:
        gdf (gpd.GeoDataFrame): the geodataframe
        fname (str): the file name
    """
    try:
        gdf.to_file(fname, driver='GeoJSON')
    except Exception as e:
        die(f"write_geojson: {e}")


def extract_osm_data(bbox: tuple, tags: list, overpass_url: str, delay: int = 5) -> gpd.GeoDataFrame:
    """Extracts data from OpenStreetMap using Overpass API

    Args:
        bbox (tuple): bounding box (min_lat, min_lon, max_lat, max_lon)
        tags (list): list of OSM tags like ['amenity=hospital']
        overpass_url (str): Overpass API endpoint
        delay (int): delay between requests in seconds

    Returns:
        gpd.GeoDataFrame: geodataframe with OSM features
    """
    try:
        tag_string = ''.join([f'["{k}"="{v}"]' for tag in tags for k, v in [tag.split('=')]])

        query = f"""
        [out:json][timeout:180];
        (
          node{tag_string}({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          way{tag_string}({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        );
        out center;
        """

        for attempt in range(3):
            try:
                response = requests.post(overpass_url, data={'data': query}, timeout=180)
                response.raise_for_status()
                data = response.json()
                break
            except Exception as e:
                if attempt < 2:
                    wait = delay * (attempt + 1)
                    info(f"Overpass timeout, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise e

        if not data or 'elements' not in data:
            return None

        features = []
        for elem in data['elements']:
            if elem['type'] == 'node':
                lon, lat = elem['lon'], elem['lat']
            elif 'center' in elem:
                lon, lat = elem['center']['lon'], elem['center']['lat']
            else:
                continue

            tags_dict = elem.get('tags', {})
            features.append({
                'osm_id': elem['id'],
                'name': tags_dict.get('name', ''),
                'lon': lon,
                'lat': lat,
                'tags': json.dumps(tags_dict)
            })

        if not features:
            return None

        gdf = gpd.GeoDataFrame(
            features,
            geometry=gpd.points_from_xy([f['lon'] for f in features],
                                        [f['lat'] for f in features]),
            crs='EPSG:4326'
        )

        time.sleep(delay)
        return gdf

    except Exception as e:
        die(f"extract_osm_data: {e}")



def read_gpkg(fname: str, layer: str = None) -> gpd.GeoDataFrame:
    """Reads a GeoPackage into a GeoDataFrame

    Args:
        fname (str): the name of the GeoPackage file
        layer (str): the layer name to read

    Returns:
        gpd.GeoDataFrame: the geodataframe
    """
    try:
        gdf = gpd.read_file(fname, layer=layer)
    except Exception as e:
        die(f"read_gpkg: {e}")
    return gdf


def write_geojson(gdf: gpd.GeoDataFrame, fname: str) -> None:
    """Writes a GeoDataFrame to GeoJSON

    Args:
        gdf (gpd.GeoDataFrame): the geodataframe
        fname (str): the file name
    """
    try:
        gdf.to_file(fname, driver='GeoJSON')
    except Exception as e:
        die(f"write_geojson: {e}")


def extract_osm_data(bbox: tuple, tags: list, overpass_url: str, delay: int = 5) -> gpd.GeoDataFrame:
    """Extracts data from OpenStreetMap using Overpass API

    Args:
        bbox (tuple): bounding box (min_lat, min_lon, max_lat, max_lon)
        tags (list): list of OSM tags like ['amenity=hospital']
        overpass_url (str): Overpass API endpoint
        delay (int): delay between requests in seconds

    Returns:
        gpd.GeoDataFrame: geodataframe with OSM features
    """
    try:
        tag_string = ''.join([f'["{k}"="{v}"]' for tag in tags for k, v in [tag.split('=')]])
        
        query = f"""
        [out:json][timeout:180];
        (
          node{tag_string}({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          way{tag_string}({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        );
        out center;
        """
        
        for attempt in range(3):
            try:
                response = requests.post(overpass_url, data={'data': query}, timeout=180)
                response.raise_for_status()
                data = response.json()
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(delay * (attempt + 1))
                else:
                    raise e
        
        if not data or 'elements' not in data:
            return None
        
        features = []
        for elem in data['elements']:
            if elem['type'] == 'node':
                lon, lat = elem['lon'], elem['lat']
            elif 'center' in elem:
                lon, lat = elem['center']['lon'], elem['center']['lat']
            else:
                continue
            
            tags_dict = elem.get('tags', {})
            features.append({
                'osm_id': elem['id'],
                'name': tags_dict.get('name', ''),
                'lon': lon,
                'lat': lat,
                'tags': json.dumps(tags_dict)
            })
        
        if not features:
            return None
        
        gdf = gpd.GeoDataFrame(
            features,
            geometry=gpd.points_from_xy([f['lon'] for f in features], 
                                        [f['lat'] for f in features]),
            crs='EPSG:4326'
        )
        
        time.sleep(delay)
        return gdf
        
    except Exception as e:
        die(f"extract_osm_data: {e}")
