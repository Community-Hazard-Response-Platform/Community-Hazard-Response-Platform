# hazard_etl

ETL (Extract, Transform, Load) module for the Community Hazard Response Platform. This module is responsible for fetching, processing, and loading geospatial reference data into the PostgreSQL/PostGIS database. It imports two datasets: Portuguese administrative boundaries from CAOP (Carta Administrativa Oficial de Portugal) and emergency facilities from OpenStreetMap.

## Structure

```
hazard_etl/
├── main.py           # Entry point — orchestrates the full ETL pipeline
├── requirements.txt  # Python dependencies
├── config/
│   └── config.yml    # Configuration file (database, OSM settings)
├── data/
│   ├── original/     # Raw downloaded data (CAOP .gpkg, OSM GeoJSON)
│   └── processed/    # Transformed data ready for loading
└── etl/
    ├── __init__.py       # Package exports
    ├── config.py         # Configuration file reader
    ├── dbController.py   # Database connection and query abstraction
    ├── ds.py             # Data extraction and transformation 
    └── logs.py           # Logging and progress utilities
```

## Dependencies

Install the ETL required packages using conda:

```bash
conda env create -f etl_environment.yml
conda activate hazard_etl
```

## Configuration

Create a `config/config.yml` file with the following structure:

```yaml
database:
  host: localhost
  port: 5432
  database: hazard_response_db
  username: postgres
  password: your_password

osm:
  overpass_url: "https://overpass.kumi.systems/api/interpreter"
  facility_tags:
    emergency:
      hospital:
        - "amenity=hospital"
      fire_station:
        - "amenity=fire_station"
      police:
        - "amenity=police"
```

## Usage

Run the full ETL pipeline with a single command from the `hazard_etl/` directory:

```bash
python main.py
```

To specify a custom configuration file:

```bash
python main.py --config_file path/to/config.yml
```

## What It Does

### Extract
- Checks the DGT website for the latest CAOP version and downloads it if not already present
- Queries the Overpass API for emergency facilities in Portugal (hospitals, fire stations, police, etc.)
- Saves raw data to `data/original/`

### Transform
- Reads CAOP GeoPackage and extracts municipalities (admin level 6) and parishes (admin level 8)
- Reprojects all geometries to EPSG:3857
- Cleans facility data from OSM
- Saves processed data to `data/processed/`

### Load
- Clears existing reference data from the database before each run to avoid duplicates
- Inserts administrative areas and facilities into PostGIS tables using WKT geometry conversion
- All data is loaded into the `public` schema

## Notes

- CAOP data is only re-downloaded when a new version is available
- OSM data is always re-extracted to ensure facilities are up to date
- Only the reference layers (`administrative_area`, `facility`) are managed by the ETL, user-generated data (needs, offers, assignments) is managed through the API
