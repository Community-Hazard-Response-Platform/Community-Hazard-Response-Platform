# etl

ETL (Extract, Transform, Load) module for the Community Hazard Response Platform. It fetches, processes and loads geospatial reference data into the PostgreSQL/PostGIS database — specifically Portuguese administrative boundaries from CAOP and emergency facilities from OpenStreetMap.

> This module only manages the reference layers (`administrative_area` and `facility`). User-generated data (needs, offers, assignments) is managed through the API.

## Structure

```
etl/
├── run_etl.py              # Entry point — orchestrates the full ETL pipeline
├── etl_module/
│   ├── __init__.py         # Package exports and logger initialisation
│   ├── config.py           # Config file reader (YAML)
│   ├── dbController.py     # Database connection and query abstraction
│   ├── ds.py               # Data extraction and transformation logic
│   └── logs.py             # Logging and progress bar utilities
└── data/
    ├── original/           # Raw downloaded data (CAOP .zip/.gpkg, OSM GeoJSON)
    └── processed/          # Transformed GeoJSON files ready for loading
```

## Requirements

- Python 3.11
- Conda (see project root `environment.yml`)
- A running PostgreSQL/PostGIS instance with the schema already applied (see [`db/`](../db/README.md))

## Setup

### 1. Configure credentials

The ETL reads from the shared config file at `config/config.yml` in the project root. If you haven't set it up yet, copy the example and fill in your credentials from the **project root**:

```bash
# From the project root
cp config/config.yml.example config/config.yml
```

The ETL uses the `database` and `osm` sections of the config:

```yaml
database:
  host: "localhost"
  port: "5432"
  database: "hazard_response_db"
  username: "your_username"
  password: "your_password"

osm:
  overpass_url: "http://overpass-api.de/api/interpreter"
  facility_tags:
    emergency:
      hospitals: ["amenity=hospital"]
      fire_stations: ["amenity=fire_station"]
      police: ["amenity=police"]
    healthcare:
      clinics: ["amenity=clinic"]
      pharmacies: ["amenity=pharmacy"]
    shelter:
      schools: ["amenity=school"]
      universities: ["amenity=university"]
      community_centres: ["amenity=community_centre"]
      sports_centres: ["leisure=sports_centre"]
```

> `config/config.yml` is gitignored — your credentials will not be committed to version control.

### 2. Create the Conda environment

From the **project root**:

```bash
# From the project root
conda env create -f environment.yml
conda activate hazard_response_platform
```

## Usage

All commands should be run from the **project root** (not from inside `etl/`), since the pipeline resolves the config file path relative to the root.

Run the full pipeline with:

```bash
# From the project root
python etl/run_etl.py
```

By default it reads from `config/config.yml`. To use a different config file:

```bash
# From the project root
python etl/run_etl.py --config_file path/to/config.yml
```

## Pipeline

The pipeline runs three sequential stages. Execution time for each stage is logged on completion.

### 1. Extraction

- Checks the DGT website for the latest available CAOP version, searching backwards from the current year up to 5 years. Downloads the `.zip` file to `etl/data/original/`.
- Queries the Overpass API for each facility type defined under `osm.facility_tags` in the config. Each type is fetched individually and tagged accordingly. Results are merged and saved to `etl/data/original/facilities_raw.geojson`.
- OSM requests include a configurable delay between calls (default: 5 seconds) and retry logic with up to 6 attempts and exponential back-off to handle Overpass API timeouts.

### 2. Transformation

- Reads the CAOP GeoPackage and extracts two layers:
  - `cont_municipios` → municipalities (`admin_level = 6`)
  - `cont_freguesias` → parishes (`admin_level = 8`)
- Reprojects all geometries to **EPSG:3857** (Web Mercator) and ensures all polygons are `MultiPolygon` for schema compatibility.
- Cleans the raw OSM facilities GeoDataFrame, keeping only `osm_id`, `name_fac`, `facility_type` and `geometry`.
- Saves both outputs to `etl/data/processed/` as GeoJSON with UTF-8 encoding.

### 3. Load

- Connects to the database using the credentials from `config.yml`.
- Truncates the `facility` and `administrative_area` tables (with `RESTART IDENTITY CASCADE`) before each load to avoid duplicates.
- Inserts data in configurable chunks (default: 1 000 rows) using `ST_GeomFromText` with WKT geometry conversion. 
- Rolls back the transaction automatically on any error.

## Module Reference (`etl_module/`)

| File | Responsibility |
|---|---|
| `config.py` | Reads and parses `config.yml` using PyYAML. Calls `die()` on malformed YAML. |
| `dbController.py` | Wraps SQLAlchemy. Exposes `insert_geodata()`, `select_data()` and `truncate_tables()`. |
| `ds.py` | Handles all I/O: CAOP version discovery, file download, GeoPackage/GeoJSON read and write, and Overpass API queries. |
| `logs.py` | Provides `info()`, `die()`, `section()` and `progress_bar()`. `die()` logs the error and calls `sys.exit(1)`. |
| `__init__.py` | Exports all public functions and initialises the logger on import. |
