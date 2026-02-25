# db

This module contains the full database schema for the Community Hazard Response Platform. It uses **PostgreSQL** with the **PostGIS** extension to support geospatial data and real-time coordination of emergency needs and volunteer responses.

## Structure

```
db/
├── model.sql           # Full schema — tables, indexes, triggers and functions
├── model_inserts.sql   # Seed data — users, categories, needs, offers and assignments
└── storm_inserts.sql   # Scenario data — Storm "Aura" (February 2026) across Portugal
```

## Requirements

- PostgreSQL 14+
- PostGIS extension

## Setup

### 1. Configure the database connection

The platform uses a shared config file at `config/config.yml`. A template is provided at `config/config.yml.example`. Copy it and fill in your credentials:

```bash
cp config/config.yml.example config/config.yml
```

Then edit `config/config.yml` with your PostgreSQL connection details:

```yaml
database:
  host: "localhost"
  port: "5432"
  database: "hazard_response_db"
  username: "your_username"
  password: "your_password"
```

> **Note:** `config/config.yml` is gitignored — your credentials will not be committed to version control.

### 2. Create the database

Using the values you set in `config.yml`, create the database in PostgreSQL:

```bash
psql -U your_username -h localhost -c "CREATE DATABASE hazard_response_db;"
```

### 3. Run the schema

```bash
psql -U your_username -h localhost -d hazard_response_db -f model.sql
```

This will create all tables, indexes, functions and triggers. The `status_domain` and `urgency_domain` tables are also populated with their allowed values at this step.

### 4. Load seed data (optional)

To populate the database with development/test data, run the seed scripts in order:

```bash
# Base data: 20 users, 20 categories, 46 needs, 25 offers, 13 assignments (Lisbon)
psql -U postgres -d hazard_response_db -f model_inserts.sql

# Storm scenario: adds needs, offers and assignments for Storm "Aura" across Portugal
# Requires model_inserts.sql to have been run first
psql -U postgres -d hazard_response_db -f storm_inserts.sql
```

> **Note:** `model_inserts.sql` uses `TRUNCATE ... RESTART IDENTITY CASCADE` — it resets all core tables before inserting. `storm_inserts.sql` does **not** truncate; it appends to existing data and assumes `user_id` 1–20 and the 20 categories from `model_inserts.sql` are present.

## Schema

![Database schema diagram](../docs/Community_Hazard_Response_Platform-2026-02-19_19-06.png)

The database contains **9 tables** divided into four groups:

### User Data
- **app_user** — registered platform users (residents, volunteers, emergency services). Stores credentials, contact info and email verification state.

### Domain Tables
- **category** — types of needs and offers (e.g. food, medical, transport, shelter, mental health). 20 categories are seeded by default.
- **status_domain** — predefined status values: `active`, `assigned`, `resolved`
- **urgency_domain** — predefined urgency levels: `critical`, `high`, `medium`, `low`

### Core Tables
- **need** — help requests submitted by users. Each need has a category, urgency level, PostGIS point geometry (EPSG:3857), a human-readable address, and a status managed automatically by triggers.
- **offer** — volunteer availability submitted by users. Mirrors the structure of `need` but without urgency. Status is also managed by triggers.
- **assignments** — matches between a need and an offer. Each need and offer can only appear in one assignment at a time (enforced by `UNIQUE` constraints). Supports statuses: `proposed`, `accepted`, `rejected`, `completed`.

### Reference Layers (populated by ETL)
- **administrative_area** — Portuguese administrative boundaries (municipalities and parishes) from CAOP, stored as PostGIS polygon geometries. Used to support spatial filtering (e.g. "needs in Lisbon").
- **facility** — Points of interest from OpenStreetMap, classified into three groups:
  - **Emergency:** hospitals, fire stations, police stations
  - **Healthcare:** clinics, pharmacies
  - **Shelter:** sports centres, community centres, schools, universities

## Spatial Data

All geometry columns use **EPSG:3857** (Web Mercator). GIST spatial indexes are created on all geometry columns to support efficient spatial queries such as:

- Finding needs within a given radius of a point
- Filtering needs and offers by administrative area
- Locating the nearest emergency facilities to a given need

Input coordinates are stored in **EPSG:4326** (WGS 84) and transformed to EPSG:3857 at insertion time using `ST_Transform(ST_SetSRID(...), 3857)`.

## Triggers

The schema includes four PostgreSQL triggers to enforce business logic automatically:

| Trigger | Table | Event | Behaviour |
|---|---|---|---|
| `update_need_updated_at` | `need` | `BEFORE UPDATE` | Stamps `updated_at` with the current timestamp |
| `update_offer_updated_at` | `offer` | `BEFORE UPDATE` | Stamps `updated_at` with the current timestamp |
| `trg_assignment_insert_sync_status` | `assignments` | `AFTER INSERT` | Sets the linked need and offer to `assigned` |
| `trg_assignment_update_completed` | `assignments` | `BEFORE UPDATE` | Sets the linked need and offer to `resolved` when the assignment reaches `completed`; also stamps `completed_at` if not already set |
| `trg_prevent_invalid_assignment` | `assignments` | `BEFORE INSERT` | Raises an exception if the need or offer is not in `active` status |

## Seed Data Overview

### `model_inserts.sql`
Populates the database with realistic development data set in Lisbon:

- **20 users** with Portuguese names and phone numbers
- **20 categories** covering a wide range of community needs
- **46 needs** spread across all urgency levels and Lisbon neighbourhoods
- **25 offers** covering all 20 categories
- **13 assignments** in a mix of statuses (`proposed`, `accepted`, `completed`)

### `storm_inserts.sql`
Adds a disaster-response scenario simulating Storm "Aura" (February 2026), affecting:

- **Setúbal, Barreiro, Alcochete, Montijo** (Setúbal district)
- **Portimão and Faro** (Algarve)
- **Amarante and Marco de Canaveses** (Tâmega/Douro)
- **Odivelas and Amadora** (Lisbon metropolitan area)

Includes **29 needs** (critical evacuations, medical emergencies, shelter, food) and **10 offers** (4x4 transport, nurse, psychologist, lawyer, cleanup team), with **10 assignments** reflecting an active emergency response.
