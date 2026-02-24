# api

Flask API for the Community Hazard Response Platform. It handles user authentication, session management, and all CRUD operations for needs, offers and assignments. All geospatial responses are returned as GeoJSON, and the API also serves the frontend templates and static files.

## Structure

```
api/
├── run_api.py      # Entry point — Flask app, all routes and database logic
├── requirements.txt
├── __init__.py
└── utils.py        # GeoJSON formatting helpers
```

## Requirements

- Python 3.11
- Conda environment from the project root (see [`environment.yml`](../environment.yml))
- A running PostgreSQL/PostGIS instance with the schema applied (see [`db/`](../db/README.md))
- A Gmail account with an [App Password](https://support.google.com/accounts/answer/185833) for email verification

## Setup

### 1. Configure credentials

The API reads from the shared config file at `config/config.yml` in the project root. It uses the `database` and `email` sections:

```yaml
database:
  host: "localhost"
  port: "5432"
  database: "hazard_response_db"
  username: "your_username"
  password: "your_password"

email:
  address: "your_email@gmail.com"
  password: "your_app_password"
```

> `config/config.yml` is gitignored — your credentials will not be committed to version control.

If `config/config.yml` is not found (e.g. when deployed to Render), the API falls back to the following environment variables:

| Variable | Description |
|---|---|
| `DB_HOST` | Database host |
| `DB_PORT` | Database port |
| `DB_NAME` | Database name |
| `DB_USER` | Database username |
| `DB_PASSWORD` | Database password |
| `EMAIL_ADDRESS` | Sender email address |
| `EMAIL_PASSWORD` | Gmail App Password |
| `FLASK_SECRET_KEY` | Secret key for session signing |

### 2. Activate the environment

```bash
# From the project root
conda activate hazard_response_platform
```

## Usage

Run the development server from the **project root**:

```bash
# From the project root
python api/run_api.py
```

The app will be available at `http://localhost:5000`.

## Connection Pool

The API uses a `psycopg2.pool.SimpleConnectionPool` with a minimum of 1 and a maximum of 10 connections. Every route acquires a connection from the pool and releases it in a `finally` block to ensure connections are always returned even if an error occurs.

## Endpoints

All JSON endpoints return `application/json`. Endpoints that return geospatial data use GeoJSON (either a `Feature` for single results or a `FeatureCollection` for lists).

---

### Authentication & Users

| Method | Path | Auth required | Description |
|---|---|---|---|
| `GET` | `/` | No | Renders the login page |
| `POST` | `/` | No | Authenticates user, starts session |
| `GET` | `/create-account` | No | Renders the registration form |
| `POST` | `/create-account` | No | Creates a new user and sends a verification email |
| `GET` | `/verify/<token>` | No | Verifies a user account via email token |
| `GET` | `/reset-password` | No | Renders the password reset form |
| `POST` | `/reset-password` | No | Updates the user's password |
| `GET` | `/logout` | No | Clears session and redirects to login |
| `GET` | `/dashboard` | Yes | Renders the main dashboard |
| `GET` | `/profile-page` | Yes | Renders the profile page |
| `GET` | `/profile` | Yes | Returns the current user's profile data |
| `POST` | `/update-profile` | Yes | Updates username, email, name and phone |
| `POST` | `/delete-account` | Yes | Deletes the current user's account |
| `GET` | `/users` | No | Returns all users (no sensitive fields) |

**Registration flow:** `POST /create-account` hashes the password with bcrypt, generates a secure token with `secrets.token_urlsafe(32)`, and sends a verification link by email. The account is only usable after clicking the link (`GET /verify/<token>`).

---

### Needs

| Method | Path | Auth required | Description |
|---|---|---|---|
| `GET` | `/needs` | No | Returns all needs as a GeoJSON FeatureCollection |
| `POST` | `/needs` | Yes | Creates a new need |
| `GET` | `/needs/<id>` | No | Returns a single need as a GeoJSON Feature |
| `DELETE` | `/needs/<id>` | No | Deletes a need |
| `GET` | `/create-need` | No | Renders the create need form |
| `GET` | `/edit-need/<id>` | Yes | Renders the edit need form |
| `POST` | `/edit-need/<id>` | Yes | Updates a need's fields and geometry |
| `GET` | `/my-needs` | Yes | Returns the current user's needs |
| `GET` | `/needs/uncovered` | No | Returns active needs with no nearby matching offer |
| `GET` | `/needs/<id>/nearby-offers` | No | Returns offers near a specific need, split by proximity |
| `GET` | `/needs/<id>/nearest-facilities` | No | Returns the nearest relevant facilities to a need |

**Notable endpoints:**

`GET /needs/uncovered?radius=<metres>` — returns active needs where no active offer of the same category exists within the given radius (default 2 000 m). Results are ordered by urgency (critical first) and include a `meta` object with `total_uncovered`, `critical_count` and `high_count`.

`GET /needs/<id>/nearby-offers?radius=<metres>` — returns all active offers matching the need's category. Each feature has a `proximity` property of `nearby` (within radius) or `related` (outside radius), plus `distance_m`. The `meta` object includes the need's geometry and radius for drawing a circle on the map.

`GET /needs/<id>/nearest-facilities?need_category=<cat>&limit=<n>` — returns the nearest facilities, automatically filtered to relevant types based on the need's category (e.g. `medical` → hospitals, clinics, pharmacies). Falls back to all facility types if no category mapping is found.

---

### Offers

| Method | Path | Auth required | Description |
|---|---|---|---|
| `GET` | `/offers` | No | Returns all active offers as a GeoJSON FeatureCollection |
| `GET` | `/offers/<id>` | Yes | Returns a single offer as a GeoJSON Feature |
| `POST` | `/create-offer` | Yes | Creates a new offer |
| `GET` | `/create-offer` | No | Renders the create offer form |
| `GET` | `/edit-offer/<id>` | Yes | Renders the edit offer form |
| `POST` | `/edit-offer/<id>` | Yes | Updates an offer's fields and geometry |
| `GET` | `/my-offers` | Yes | Returns the current user's offers |
| `GET` | `/my-offers-for-need/<need_id>` | Yes | Returns the user's active offers matching a need's category |

---

### Assignments

| Method | Path | Auth required | Description |
|---|---|---|---|
| `POST` | `/assignments` | Yes | Creates an assignment linking a need to an offer |
| `GET` | `/my-assignments` | Yes | Returns assignments involving the current user |
| `PUT` | `/assignments/<id>/complete` | No | Marks an assignment as completed |

**Assignment creation:** if `offer_id` is not provided in the request body, the API auto-matches by finding the user's active offer that shares the same category as the need. After creating the assignment, an email notification is sent to the other party (need owner or offer owner depending on who initiated).

---

### Reference Data

| Method | Path | Description |
|---|---|---|
| `GET` | `/categories` | Returns all categories |
| `GET` | `/urgency-levels` | Returns all urgency levels ordered by severity |
| `GET` | `/facilities` | Returns facilities as GeoJSON, optionally filtered by `?types=` |
| `GET` | `/facility-types` | Returns a list of distinct facility type strings |
| `GET` | `/admin-areas` | Searches administrative areas by name (autocomplete, max 10) |
| `GET` | `/admin-areas/stats` | Returns need/offer counts per area with a gap score |
| `GET` | `/search` | Filters needs, offers and facilities by area name and type |

**`GET /admin-areas/stats?admin_level=<6|8>`** — uses a spatial join (`ST_Within`) to count active needs and offers inside each administrative area polygon. Returns a `gap_score` (needs minus offers) per area useful for choropleth mapping, plus summary totals in `meta`.

**`GET /search?query=<area>&type=<needs|offers|facility|all>&facilityTypes=<type>`** — resolves the area name to a geometry with `ILIKE` and then uses `ST_Within` to filter all requested entity types spatially.

## Utils (`api/utils.py`)

Three helper functions for building GeoJSON responses from database rows:

- `format_geojson_feature(row)` — wraps a single row as a GeoJSON `Feature`
- `format_geojson_featurecollection(rows)` — wraps multiple rows as a `FeatureCollection`
- `format_geojson(rows)` — smart wrapper: returns an empty `FeatureCollection` for no results, a `Feature` for one result, and a `FeatureCollection` for multiple
