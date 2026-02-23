import etl_module as e
import argparse
import zipfile
from pathlib import Path
import pandas as pd


DB_SCHEMA = "public"
TABLE_ADMIN_AREAS = "administrative_area"
TABLE_FACILITIES = "facility"
DOWNLOAD_DIR = "data/original"
PROCESSED_DIR = "data/processed"


def extraction(config: dict) -> None:
    """Runs extraction

    Args:
        config (dict): configuration dictionary
    """
    e.section("EXTRACTION")
    
    # Check for latest CAOP version on DGT website
    e.info("CHECKING LATEST CAOP VERSION")
    caop_url, caop_version = e.get_latest_caop_url()
    caop_fname = f"{DOWNLOAD_DIR}/caop.zip"
    e.info(f"DOWNLOADING {caop_version}")
    e.download_data(caop_url, caop_fname)

    e.info("EXTRACTING CAOP ZIP")
    with zipfile.ZipFile(caop_fname, 'r') as zip_ref:
        zip_ref.extractall(DOWNLOAD_DIR)

    e.info("CAOP COMPLETED")

    # Extract OSM facilities
    e.info("EXTRACTING OSM FACILITIES")
    overpass_url = config["osm"]["overpass_url"]

    all_facilities = []
    
    for category, facilities in config["osm"]["facility_tags"].items():
        for facility_type, tags in facilities.items():
            e.info(f"Extracting {facility_type}...")
            gdf = e.extract_osm_data(tags, overpass_url)
            if gdf is not None:
                gdf['facility_type'] = facility_type
                all_facilities.append(gdf)
                e.info(f"  -> Found {len(gdf)} {facility_type}")
            else:
                e.info(f"  -> No results for {facility_type}")

    if all_facilities:
        facilities_gdf = pd.concat(all_facilities, ignore_index=True)
        facilities_gdf = facilities_gdf.to_crs('EPSG:3857')
        e.write_geojson(facilities_gdf, f"{DOWNLOAD_DIR}/facilities_raw.geojson")
        e.info(f"Saved {len(facilities_gdf)} facilities total")

    e.info("EXTRACTION COMPLETED")


def transformation(config: dict) -> None:
    """Runs transformation

    Args:
        config (dict): configuration dictionary
    """
    e.section("TRANSFORMATION")
    
    # Always re-run transformation to ensure processed files are up to date
    processed = Path(PROCESSED_DIR)
    processed.mkdir(parents=True, exist_ok=True)
    
    # Transform CAOP to administrative_area table schema
    e.info("READING CAOP DATA")
    gpkg_file = list(Path(DOWNLOAD_DIR).glob("*.gpkg"))[0]
    
    # Municipalities - admin_level 6
    municipalities = e.read_gpkg(str(gpkg_file), layer='cont_municipios')
    municipalities = municipalities.to_crs('EPSG:3857')
    municipalities = municipalities[['municipio', 'geometry']].copy()
    municipalities.columns = ['name_area', 'geometry']
    municipalities['admin_level'] = 6

    # Parishes - admin_level 8
    parishes = e.read_gpkg(str(gpkg_file), layer='cont_freguesias')
    parishes = parishes.to_crs('EPSG:3857')
    parishes = parishes[['freguesia', 'geometry']].copy()
    parishes.columns = ['name_area', 'geometry']
    parishes['admin_level'] = 8

    # Combine
    import geopandas as gpd
    admin_areas = pd.concat([municipalities, parishes], ignore_index=True)
    admin_areas = gpd.GeoDataFrame(admin_areas, geometry='geometry', crs='EPSG:3857')
    admin_areas['geometry'] = admin_areas['geometry'].apply(
        lambda g: g if g.geom_type == 'MultiPolygon' else MultiPolygon([g])
    )

    e.info(f"{len(admin_areas)} administrative areas ready")
    e.write_geojson(admin_areas, f"{PROCESSED_DIR}/administrative_area.geojson")

    # Transform facilities
    e.info("READING FACILITIES DATA")
    facilities = e.read_gpkg(f"{DOWNLOAD_DIR}/facilities_raw.geojson")

    facilities = facilities[['osm_id', 'name', 'facility_type', 'geometry']].copy()
    facilities.columns = ['osm_id', 'name_fac', 'facility_type', 'geometry']

    e.info(f"{len(facilities)} facilities ready")
    e.write_geojson(facilities, f"{PROCESSED_DIR}/facility.geojson")

    e.info("TRANSFORMATION COMPLETED")


def load(config: dict, chunksize: int = 1000) -> None:
    """Runs load

    Args:
        config (dict): configuration dictionary
        chunksize (int): the number of rows to be inserted at one time
    """
    try:
        e.section("LOAD")

        db = e.DBController(
            host=config["database"]["host"],
            port=config["database"]["port"],
            database=config["database"]["database"],
            username=config["database"]["username"],
            password=config["database"]["password"]
        )

        e.info("CLEARING EXISTING DATA")
        db.truncate_tables(["facility", "administrative_area"])

        e.info("READING ADMINISTRATIVE AREAS")
        admin_areas = e.read_gpkg(f"{PROCESSED_DIR}/administrative_area.geojson")
        e.info(f"Loaded {len(admin_areas)} administrative areas")

        e.info("INSERTING ADMINISTRATIVE AREAS INTO DATABASE")
        db.insert_geodata(admin_areas, schema=DB_SCHEMA, table=TABLE_ADMIN_AREAS, srid=3857, chunksize=chunksize)
        e.info("ADMINISTRATIVE AREAS INSERTED")

        e.info("READING FACILITIES")
        facilities = e.read_gpkg(f"{PROCESSED_DIR}/facility.geojson")
        e.info(f"Loaded {len(facilities)} facilities")

        e.info("INSERTING FACILITIES INTO DATABASE")
        db.insert_geodata(facilities, schema=DB_SCHEMA, table=TABLE_FACILITIES, srid=3857, chunksize=chunksize)
        e.info("FACILITIES INSERTED")
    except Exception as err:
        e.die(f"LOAD: {err}")


def parse_args() -> str:
    """Reads command line arguments

    Returns:
        the name of the configuration file
    """
    parser = argparse.ArgumentParser(description="Hazard Response Platform ETL")
    parser.add_argument("--config_file", required=False, 
                       help="The configuration file", 
                       default="../config/config.yml")
    args = parser.parse_args()
    return args.config_file


def time_this_function(func, **kwargs) -> str:
    """Times function `func`

    Args:
        func (function): the function we want to time

    Returns:
        a string with the execution time
    """
    import time
    t0 = time.time()
    func(**kwargs)
    t1 = time.time()
    return f"'{func.__name__}' EXECUTED IN {t1-t0:.3f} SECONDS"


def main(config_file: str) -> None:
    """Main function for ETL

    Args:
        config_file (str): configuration file
    """
    config = e.read_config(config_file)
    
    msg = time_this_function(extraction, config=config)
    e.info(msg)
    
    msg = time_this_function(transformation, config=config)
    e.info(msg)
    
    msg = time_this_function(load, config=config, chunksize=1000)
    e.info(msg)


if __name__ == "__main__":
    config_file = parse_args()
    main(config_file)
