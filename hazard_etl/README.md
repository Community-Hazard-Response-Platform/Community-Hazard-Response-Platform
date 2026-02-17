# ETL - Hazard Response Platform

## Objectives

This ETL package extracts, transforms, and loads geographic data for a community hazard response platform.

The ETL process:

* **Extracts** administrative boundaries from CAOP (Portugal) and facilities from OpenStreetMap
* **Transforms** the data to EPSG:3857 (Web Mercator) for web mapping compatibility  
* **Loads** the transformed data into a PostGIS database

## Data Sources

* **CAOP**: Portuguese administrative boundaries from Direção-Geral do Território
* **OpenStreetMap**: Emergency facilities via Overpass API (hospitals, fire stations, police, etc.)

## Structure

```
.
├── config/
│   └── config.yml          # Configuration file
├── data/
│   ├── original/           # Downloaded raw data
│   ├── processed/          # Transformed data
│   └── static/             # Static reference data
├── etl/
│   ├── __init__.py
│   ├── config.py           # Config reader
│   ├── db.py               # Database operations
│   ├── ds.py               # Data source operations
│   └── logs.py             # Logging utilities
├── main.py                 # Main ETL runner
└── requirements.txt
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure database in `config/config.yml`

3. Ensure PostgreSQL with PostGIS is running

## Usage

Run the complete ETL pipeline:
```bash
python main.py
```

Or specify a config file:
```bash
python main.py --config_file config/my_config.yml
```

## Process Flow

1. **Extraction**
   - Downloads CAOP administrative boundaries (ZIP)
   - Extracts municipalities data
   - Queries OSM Overpass API for facilities

2. **Transformation**  
   - Converts to EPSG:3857 coordinate system
   - Cleans and standardizes column names
   - Parses OSM tags for useful attributes

3. **Load**
   - Inserts municipalities into database
   - Inserts facilities into database
   - Uses batch inserts for efficiency

## Output

The ETL loads two main tables:

* `municipalities` - Administrative boundaries
* `facilities` - Emergency and healthcare facilities

All geometries are in EPSG:3857 for web mapping compatibility.
