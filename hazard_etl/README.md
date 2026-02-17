# ETL - Hazard Response Platform

## Objectives

This ETL package extracts, transforms, and loads geographic data for a community hazard response platform.

The ETL process:

* **Extracts** administrative boundaries from CAOP (Portugal) and facilities from OpenStreetMap
* **Transforms** the data to EPSG:3857 (Web Mercator) for web mapping compatibility  
* **Loads** the transformed data into a PostGIS database

## Data Sources

* **CAOP**: Portuguese administrative boundaries from Direção-Geral do Território (auto-detects latest version)
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
│   ├── dbController.py     # Database operations
│   ├── ds.py               # Data source operations
│   └── logs.py             # Logging utilities
├── main.py                 # Main ETL runner
└── requirements.txt
```

## Setup

1. Create conda environment and install dependencies:
```bash
conda install -c conda-forge --file requirements.txt
```

2. Configure database in `config/config.yml`:
```yaml
database:
  host: "localhost"
  port: "5432"
  database: "hazard_response_db"
  username: "postgres"
  password: "your_password"
```

3. Create database schema:
```bash
psql -h localhost -U postgres -d hazard_response_db -f ../db/model.sql
```

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
   - Auto-detects and downloads latest CAOP version from DGT
   - Skips download if already cached locally
   - Queries OSM Overpass API for facilities

2. **Transformation**  
   - Converts to EPSG:3857 coordinate system
   - Cleans and standardizes column names
   - Prepares data for database schema

3. **Load**
   - Inserts administrative areas into `administrative_area` table
   - Inserts facilities into `facility` table
   - Uses PostGIS ST_GeomFromText for geometry

## Output

The ETL populates two main database tables:

* `administrative_area` - Municipal and parish boundaries (3,327 areas)
* `facility` - Emergency and healthcare facilities (~1,300+ facilities)

All geometries are in EPSG:3857 for web mapping compatibility.

## Configuration

Edit `config/config.yml` to customize:

- **Bounding box**: Default is Lisboa area for testing. Uncomment full Portugal bbox for complete data.
- **Facility types**: Add or remove OSM facility tags as needed
- **Database connection**: Update with your credentials

## Notes

- First run downloads CAOP (~50MB) and extracts facilities (5-10 min for Lisboa area)
- Subsequent runs skip CAOP download if same version exists
- Overpass API has rate limits - 5 second delay between requests
- For full Portugal extraction, expect 30-60 minutes runtime
