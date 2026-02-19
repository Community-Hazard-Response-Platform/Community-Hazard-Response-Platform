# db

This module contains the database schema for the Community Hazard Response Platform. It uses PostgreSQL with the PostGIS extension to support geospatial data and real-time coordination of emergency needs and volunteer responses.

## Structure

```
db/
└── model.sql   # Full database schema — tables, indexes, triggers and functions
```

## Requirements

- PostgreSQL 14+
- PostGIS extension

## Setup

Connect to your PostgreSQL instance and create the database:

```sql
CREATE DATABASE hazard_response_db;
```

Then connect to it and run the schema:

```bash
psql -U postgres -d hazard_response_db -f model.sql
```

## Schema

![Database schema diagram](../docs/Community_Hazard_Response_Platform-2026-02-19_19-06.png)

The database contains 8 tables divided into three groups:

### User Data
- **app_user** — registered users of the platform (residents, volunteers, emergency services)

### Domain Tables
- **category** — types of needs and offers (e.g. food, medical, transport)
- **status_domain** — predefined status values: `active`, `assigned`, `resolved`
- **urgency_domain** — predefined urgency levels: `critical`, `high`, `medium`, `low`

### Core Tables
- **need** — help requests submitted by users, with a PostGIS point geometry for location
- **offer** — volunteer availability submitted by users, with a PostGIS point geometry for location
- **assignments** — matches between a need and an offer

### Reference Layers (populated by ETL)
- **administrative_area** — Portuguese municipalities and parishes from CAOP, with PostGIS polygon geometry
- **facility** — facilities from OpenStreetMap divided into emergency (hospitals, fire stations and police), healthcare (clinics and pharmacies) and shelter (sports centres, community centres, schools and universities) with PostGIS point geometry

## Spatial Data

All geometry columns use **EPSG:3857** (Web Mercator). Spatial indexes (GIST) are created on all geometry columns to support efficient spatial queries such as:
- Finding needs within a given radius
- Filtering offers by administrative area
- Locating nearby emergency facilities

## Triggers

The schema includes four PostgreSQL triggers to automate business logic:

- **update_need_updated_at** — automatically updates `updated_at` timestamp on need changes
- **update_offer_updated_at** — automatically updates `updated_at` timestamp on offer changes
- **trg_assignment_insert_sync_status** — sets need and offer status to `assigned` when a new assignment is created
- **trg_assignment_update_completed** — sets need and offer status to `resolved` when an assignment is marked as completed
- **trg_prevent_invalid_assignment** — prevents assigning needs or offers that are not in `active` status
