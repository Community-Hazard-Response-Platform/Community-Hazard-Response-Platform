from flask import Flask, redirect, request, jsonify, render_template, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from utils import format_geojson
import os
import bcrypt
import secrets
import smtplib
import yaml
from email.message import EmailMessage


def load_config(path="../config/config.yml"):
    """Loads the YAML configuration file.

    Args:
        path (str): path to the config file

    Returns:
        dict: configuration dictionary
    """
    with open(path) as f:
        return yaml.safe_load(f)


config = load_config()
db_cfg = config["database"]

DB_CONFIG = {
    "database": db_cfg["database"],
    "user":     db_cfg["username"],
    "password": db_cfg["password"],
    "host":     db_cfg["host"],
    "port":     db_cfg["port"]
}

db_pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    database=DB_CONFIG["database"],
    user=DB_CONFIG["user"],
    password=DB_CONFIG["password"],
    host=DB_CONFIG["host"],
    port=DB_CONFIG["port"],
    cursor_factory=RealDictCursor
)

template_path = os.path.join(os.path.dirname(__file__), "../frontend/templates")
static_path = os.path.join(os.path.dirname(__file__), "../frontend/static")
app = Flask(__name__, template_folder=template_path, static_folder=static_path)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-in-production")


def get_db_connection():
    """Gets a connection from the pool."""
    return db_pool.getconn()


def release_db_connection(conn):
    """Returns a connection to the pool."""
    db_pool.putconn(conn)


# ─── USERS ────────────────────────────────────────────────────────────────────

@app.route('/users', methods=['GET'])
def get_users():
    """Returns a list of all registered users (excluding sensitive fields).

    Returns:
        JSON list of user objects
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT user_id, username, email, firstname, surname, phone, is_verified, created_at
            FROM app_user
        """)
        users = cursor.fetchall()
    finally:
        cursor.close()
        release_db_connection(conn)
    return jsonify(users)


@app.route("/profile-page")
def profile_page():
    """Renders the profile page. Redirects to login if not authenticated."""
    if "user_id" not in session:
        return redirect("/")
    return render_template("profile_page.html")


@app.route("/profile", methods=["GET"])
def profile():
    """Returns the current user's profile data.

    Returns:
        JSON object with username, email, firstname, surname, phone
    """
    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT username, email, firstname, surname, phone
            FROM app_user
            WHERE user_id = %s
        """, (session["user_id"],))
        user = cursor.fetchone()
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify(user)


@app.route("/update-profile", methods=["POST"])
def update_profile():
    """Updates the current user's profile information.

    Form fields: username, email, firstname, surname, phone

    Returns:
        JSON with success flag or error message
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]
    username = request.form.get("username").strip()
    email = request.form.get("email").strip()
    firstname = request.form.get("firstname").strip()
    surname = request.form.get("surname").strip()
    phone = request.form.get("phone", "").strip() or None

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check username/email not already taken by another user
        cursor.execute("""
            SELECT user_id FROM app_user
            WHERE (username=%s OR email=%s) AND user_id != %s
        """, (username, email, user_id))
        existing = cursor.fetchone()
        if existing:
            return jsonify({"error": "Username or email already taken"}), 400

        cursor.execute("""
            UPDATE app_user
            SET username=%s, email=%s, firstname=%s, surname=%s, phone=%s
            WHERE user_id=%s
        """, (username, email, firstname, surname, phone, user_id))
        conn.commit()
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify({"success": True})


@app.route("/delete-account", methods=["POST"])
def delete_account():
    """Deletes the current user's account and clears the session.

    Returns:
        JSON with success flag or error message
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM app_user WHERE user_id=%s", (user_id,))
        conn.commit()
    finally:
        cursor.close()
        release_db_connection(conn)

    session.clear()
    return jsonify({"success": True})


def send_verification_email(email, token):
    """Sends an email verification link to the given address.

    Args:
        email (str): recipient email address
        token (str): verification token to include in the link
    """
    link = url_for("verify_account", token=token, _external=True)

    msg = EmailMessage()
    msg["Subject"] = "Verify your account"
    msg["From"] = config["email"]["address"]
    msg["To"] = email
    msg.set_content(f"Click to verify your account:\n{link}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(
            config["email"]["address"],
            config["email"]["password"]
        )
        smtp.send_message(msg)


@app.route("/verify/<token>")
def verify_account(token):
    """Verifies a user account using the token sent by email.

    Args:
        token (str): verification token from the URL

    Returns:
        Rendered success or error template
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id FROM app_user
        WHERE verification_token = %s
    """, (token,))

    user = cursor.fetchone()

    if not user:
        cursor.close()
        release_db_connection(conn)
        return render_template("verification_error.html")

    cursor.execute("""
        UPDATE app_user
        SET is_verified = TRUE,
            verification_token = NULL
        WHERE verification_token = %s
    """, (token,))

    conn.commit()
    cursor.close()
    release_db_connection(conn)

    return render_template("verification_success.html")


@app.route("/create-account", methods=["GET", "POST"])
def create_account():
    """Handles account registration.

    GET: renders the registration form
    POST: creates the user, sends verification email

    Returns:
        Rendered template
    """
    if request.method == "POST":

        username = request.form["username"].strip()
        email = request.form["email"].strip()
        firstname = request.form["firstname"].strip()
        surname = request.form["surname"].strip()
        password = request.form["password"].encode("utf-8")
        phone = request.form.get("phone", "").strip() or None

        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt()).decode("utf-8")

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            verification_token = secrets.token_urlsafe(32)

            cursor.execute("SELECT user_id FROM app_user WHERE username=%s OR email=%s", (username, email))
            existing_user = cursor.fetchone()
            if existing_user:
                return render_template("create_account.html", error="Username or email already exists")

            cursor.execute("""
                INSERT INTO app_user
                (username, email, hashed_password, firstname, surname, phone, verification_token, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                RETURNING user_id
            """, (username, email, hashed_password, firstname, surname, phone, verification_token))

            conn.commit()
            send_verification_email(email, verification_token)

        except Exception as e:
            return render_template("create_account.html", error=str(e))
        finally:
            cursor.close()
            release_db_connection(conn)

        return render_template("account_created.html")

    return render_template("create_account.html")


@app.route("/", methods=["GET", "POST"])
def login():
    """Handles user login.

    GET: renders the login form
    POST: authenticates the user and starts a session

    Returns:
        Rendered template
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT user_id, username, hashed_password, is_verified FROM app_user WHERE username=%s",
                (username,)
            )
            user = cursor.fetchone()
        finally:
            cursor.close()
            release_db_connection(conn)

        if not user:
            return render_template("login.html", error="Username and password do not match")

        if not user["is_verified"]:
            return render_template("login.html", error="Please verify your email first")

        if user and bcrypt.checkpw(password, user["hashed_password"].encode("utf-8")):
            # Store user identity in session
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            return render_template("dashboard.html", username=user["username"])
        else:
            return render_template("login.html", error="Username and password do not match")

    return render_template("login.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    """Handles password reset by email.

    GET: renders the reset form
    POST: validates and updates the password

    Returns:
        Rendered template
    """
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return render_template("reset_password.html", error="Passwords do not match")
        if len(password) < 8:
            return render_template("reset_password.html", error="Password must be at least 8 characters")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id FROM app_user WHERE email=%s", (email,))
            user = cursor.fetchone()
            if not user:
                return render_template("reset_password.html", error="No user found with this email")

            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            cursor.execute(
                "UPDATE app_user SET hashed_password=%s WHERE email=%s",
                (hashed, email)
            )
            conn.commit()
        finally:
            cursor.close()
            release_db_connection(conn)

        return render_template("reset_success.html")

    return render_template("reset_password.html")


@app.route("/dashboard")
def dashboard():
    """Renders the main dashboard. Redirects to login if not authenticated."""
    if "user_id" not in session:
        return redirect("/")
    return render_template("dashboard.html", username=session["username"])


@app.route("/logout")
def logout():
    """Clears the session and redirects to the login page."""
    session.clear()
    return redirect("/")


# ─── CATEGORIES ───────────────────────────────────────────────────────────────

@app.route('/categories', methods=['GET'])
def get_categories():
    """Returns all available need/offer categories.

    Returns:
        JSON list of {id, name_cat} objects
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT category_id, name_cat FROM category ORDER BY name_cat")
        categories = cursor.fetchall()
        result = [{"id": c["category_id"], "name_cat": c["name_cat"]} for c in categories]
    finally:
        cursor.close()
        release_db_connection(conn)
    return jsonify(result)


# ─── NEEDS ────────────────────────────────────────────────────────────────────
@app.route("/edit-need/<int:need_id>")
def edit_need_page(need_id):
    return render_template("edit_need.html", need_id=need_id)

@app.route("/edit-need/<int:need_id>", methods=["GET"])
def edit_need(need_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT need_id, title, descrip, urgency, category, ST_AsGeoJSON(geom) AS geom
        FROM need
        WHERE need_id = %s AND user_id = %s
    """, (need_id, session["user_id"]))
    row = cursor.fetchone()
    cursor.close()
    release_db_connection(conn)

    if not row:
        return "Need not found or you don't have permission", 404

    return render_template("edit_need.html", need=row)

@app.route("/edit-need/<int:need_id>", methods=["POST"])
def update_need(need_id):
    data = request.get_json()  
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE need
        SET title = %s,
            descrip = %s,
            urgency = %s,
            category = %s,
            address_point = %s,
            geom = ST_Transform(
            ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326),3857),
            updated_at = NOW()
        WHERE need_id = %s AND user_id = %s
    """, (
        data["title"],
        data["descrip"],
        data["urgency"],
        data["category"],
        data["address_point"],
        data["geom"],
        need_id,
        session["user_id"]
    ))
    conn.commit()
    cursor.close()
    release_db_connection(conn)
    return {"success": True}

@app.route('/needs', methods=['GET'])
def get_needs():
    """Returns all needs as a GeoJSON FeatureCollection.

    Returns:
        GeoJSON FeatureCollection with need properties and point geometry
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT n.need_id,
                n.title,
                n.descrip,
                n.address_point,
                n.user_id,
                s.code as status,
                u.code as urgency,
                c.name_cat as category,
                ST_AsGeoJSON(n.geom)::json as geom,
                a.status_ass as assignment_status
            FROM need n
            JOIN status_domain s ON n.status_id = s.status_id
            JOIN urgency_domain u ON n.urgency = u.urgency_id
            JOIN category c ON n.category = c.category_id
            LEFT JOIN assignments a ON a.need_id = n.need_id
                AND a.status_ass IN ('proposed', 'accepted')
        """)
        needs = cursor.fetchall()
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify(format_geojson(needs))


@app.route('/needs', methods=['POST'])
def create_need():
    """Creates a new need for the current logged-in user.

    JSON body: title, descrip, category, urgency, latitude, longitude, address_point

    Returns:
        JSON with need_id and confirmation message, 201 on success
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    body = request.get_json()
    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO need (
            user_id, title, descrip, category, urgency, geom, address_point
        )
        VALUES (
            %s, %s, %s, %s, %s,
            ST_Transform(
                ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                3857
            ),
            %s
        )
        RETURNING need_id
    """

    values = (
        user_id,
        body.get("title"),
        body.get("descrip"),
        body.get("category"),
        body.get("urgency"),
        body.get("longitude"),
        body.get("latitude"),
        body.get("address_point")
    )

    try:
        cursor.execute(query, values)
        need_id = cursor.fetchone()["need_id"]
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Failed to create need"}), 500
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify({"message": f"Need {need_id} created"}), 201


@app.route('/create-need', methods=['GET'])
def create_need_page():
    """Renders the create need form."""
    return render_template("create_need.html")


@app.route('/needs/uncovered', methods=['GET'])
def get_uncovered_needs():
    """Returns active needs that have no matching active offer within a given radius.

    A need is considered uncovered if there is no active offer sharing its
    category within the search radius. Ordered by urgency (critical first).

    Query params:
        radius (int): search radius in metres (default: 2000)

    Returns:
        GeoJSON FeatureCollection of uncovered needs with urgency and category,
        plus meta counts for critical and high urgency items
    """
    radius = request.args.get('radius', 2000, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                n.need_id,
                n.title,
                n.descrip,
                n.address_point,
                c.name_cat  AS category,
                u.code      AS urgency,
                u.urgency_id,
                ST_AsGeoJSON(n.geom)::json AS geom
            FROM need n
            JOIN category c       ON n.category  = c.category_id
            JOIN urgency_domain u ON n.urgency    = u.urgency_id
            WHERE n.status_id = (SELECT status_id FROM status_domain WHERE code = 'active')
              AND NOT EXISTS (
                SELECT 1
                FROM offer o
                WHERE o.category  = n.category
                  AND o.status_id = (SELECT status_id FROM status_domain WHERE code = 'active')
                  AND ST_DWithin(ST_Transform(o.geom, 4326)::geography, ST_Transform(n.geom, 4326)::geography, %(radius)s)              )
            ORDER BY u.urgency_id ASC
        """, {"radius": radius})

        rows = cursor.fetchall()

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        release_db_connection(conn)

    features = [
        {
            "type": "Feature",
            "geometry": row["geom"],
            "properties": {
                "need_id":       row["need_id"],
                "title":         row["title"],
                "descrip":       row["descrip"],
                "address_point": row["address_point"],
                "category":      row["category"],
                "urgency":       row["urgency"]
            }
        }
        for row in rows
    ]

    return jsonify({
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "radius_m":        radius,
            "total_uncovered": len(features),
            "critical_count":  sum(1 for f in features if f["properties"]["urgency"] == "critical"),
            "high_count":      sum(1 for f in features if f["properties"]["urgency"] == "high")
        }
    })


@app.route('/needs/<int:need_id>/nearby-offers', methods=['GET'])
def get_nearby_offers(need_id):
    """Returns offers related to a specific need, split by proximity.

    Fetches all active offers sharing the same category as the given need.
    Each offer is tagged as 'nearby' if within the specified radius, or
    'related' if outside it. Results are ordered by distance ascending.

    Args:
        need_id (int): the ID of the need (from URL)

    Query params:
        radius (int): search radius in metres (default: 2000)

    Returns:
        GeoJSON FeatureCollection with a 'proximity' property on each feature
        ('nearby' or 'related'), plus distance in metres and the need's
        geometry and radius for drawing the circle on the map
    """
    radius = request.args.get('radius', 2000, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT need_id FROM need WHERE need_id = %s", (need_id,))
        if cursor.fetchone() is None:
            return jsonify({"error": f"Need {need_id} not found"}), 404

        # Fetch need geometry separately so it's always available even with no offers
        cursor.execute("SELECT ST_AsGeoJSON(geom)::json AS geom FROM need WHERE need_id = %s", (need_id,))
        need_geom = cursor.fetchone()["geom"]

        cursor.execute("""
            SELECT
                o.offer_id,
                o.title,
                o.descrip,
                o.address_point,
                c.name_cat AS category,
                ST_AsGeoJSON(o.geom)::json AS geom,
                ROUND(ST_Distance(ST_Transform(o.geom, 4326)::geography, ST_Transform(n.geom, 4326)::geography)::numeric, 1) AS distance_m,
                CASE
                    WHEN ST_DWithin(ST_Transform(o.geom, 4326)::geography, ST_Transform(n.geom, 4326)::geography, %(radius)s) THEN 'nearby'
                    ELSE 'related'
                END AS proximity,
                ST_AsGeoJSON(n.geom)::json AS need_geom
            FROM offer o
            JOIN need n ON n.need_id = %(need_id)s
            JOIN category c ON o.category = c.category_id
            WHERE o.status_id = (SELECT status_id FROM status_domain WHERE code = 'active')
              AND o.category = n.category
            ORDER BY distance_m ASC
        """, {"need_id": need_id, "radius": radius})

        rows = cursor.fetchall()

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        release_db_connection(conn)

    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "geometry": row["geom"],
            "properties": {
                "offer_id":      row["offer_id"],
                "title":         row["title"],
                "descrip":       row["descrip"],
                "address_point": row["address_point"],
                "category":      row["category"],
                "distance_m":    float(row["distance_m"]),
                "proximity":     row["proximity"]
            }
        })

    return jsonify({
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "need_id":       need_id,
            "radius_m":      radius,
            "need_geom":     need_geom,
            "nearby_count":  sum(1 for f in features if f["properties"]["proximity"] == "nearby"),
            "related_count": sum(1 for f in features if f["properties"]["proximity"] == "related")
        }
    })


@app.route('/needs/<int:need_id>/nearest-facilities', methods=['GET'])
def get_nearest_facilities(need_id):
    """Returns the nearest facilities to a given need, filtered by need category.

    Args:
        need_id (int): the ID of the need (from URL)

    Query params:
        type (str): optional facility type filter
        limit (int): max number of facilities to return (default: 5)
        need_category (str): need category to map to relevant facility types

    Returns:
        GeoJSON FeatureCollection of nearest facilities ordered by distance ascending
    """
    facility_type = request.args.get('type', None)
    limit = request.args.get('limit', 5, type=int)
    need_category = request.args.get('need_category', None)

    CATEGORY_FACILITY_MAP = {
        'medical':      ['hospital', 'clinic', 'pharmacy', 'ambulance_station'],
        'shelter':      ['shelter', 'community_centre', 'sports_centre', 'school'],
        'food':         ['food_bank', 'community_centre'],
        'transport':    ['hospital', 'clinic'],
        'eldercare':    ['hospital', 'clinic', 'pharmacy'],
        'mental_health':['hospital', 'clinic', 'community_centre'],
        'childcare':    ['school', 'community_centre'],
        'pets':         ['veterinary'],
        'safety':       ['police', 'fire_station', 'emergency_service'],
        'hygiene':      ['pharmacy', 'community_centre'],
        'clothing':     ['community_centre', 'shelter'],
        'repairs':      ['community_centre'],
        'education':    ['school', 'university'],
        'tech':         ['community_centre', 'university'],
        'legal':        ['community_centre'],
        'logistics':    ['community_centre'],
        'translation':  ['community_centre'],
        'social':       ['community_centre'],
        'donation':     ['community_centre'],
        'other':        ['community_centre'],
    }

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT need_id FROM need WHERE need_id = %s", (need_id,))
        if cursor.fetchone() is None:
            return jsonify({"error": f"Need {need_id} not found"}), 404

        if need_category and need_category in CATEGORY_FACILITY_MAP:
            relevant_types = tuple(CATEGORY_FACILITY_MAP[need_category])
            cursor.execute("""
                SELECT
                    f.facility_id,
                    f.name_fac,
                    f.facility_type,
                    ST_AsGeoJSON(f.geom)::json AS geom,
                    ROUND(ST_Distance(ST_Transform(f.geom, 4326)::geography, ST_Transform(n.geom, 4326)::geography)::numeric, 1) AS distance_m
                FROM facility f
                JOIN need n ON n.need_id = %(need_id)s
                WHERE f.facility_type IN %(relevant_types)s
                ORDER BY distance_m ASC
                LIMIT %(limit)s
            """, {"need_id": need_id, "relevant_types": relevant_types, "limit": limit})
        else:
            type_filter = "AND f.facility_type = %(facility_type)s" if facility_type else ""
            cursor.execute(f"""
                SELECT
                    f.facility_id,
                    f.name_fac,
                    f.facility_type,
                    ST_AsGeoJSON(f.geom)::json AS geom,
                    ROUND(ST_Distance(ST_Transform(f.geom, 4326)::geography, ST_Transform(n.geom, 4326)::geography)::numeric, 1) AS distance_m
                FROM facility f
                JOIN need n ON n.need_id = %(need_id)s
                WHERE 1=1 {type_filter}
                ORDER BY distance_m ASC
                LIMIT %(limit)s
            """, {"need_id": need_id, "facility_type": facility_type, "limit": limit})

        rows = cursor.fetchall()

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        release_db_connection(conn)

    features = [
        {
            "type": "Feature",
            "geometry": row["geom"],
            "properties": {
                "facility_id":   row["facility_id"],
                "name_fac":      row["name_fac"],
                "facility_type": row["facility_type"],
                "distance_m":    float(row["distance_m"])
            }
        }
        for row in rows
    ]

    return jsonify({
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "need_id":              need_id,
            "facility_type_filter": facility_type,
            "count":                len(features)
        }
    })


@app.route('/needs/<id>', methods=['DELETE'])
def delete_need(id):
    """Deletes a need by ID.

    Args:
        id (int): need ID from URL

    Returns:
        JSON confirmation message
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM need WHERE need_id = %s", (id,))
        conn.commit()
    except Exception:
        return jsonify({"error": f"Failed to delete need {id}"}), 500
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify({"message": f"Need {id} deleted"})


@app.route("/my-needs")
def my_needs():
    """Returns the current user's needs as a list of GeoJSON features.

    Returns:
        JSON object with a features list
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
                    SELECT need_id, user_id, ST_AsGeoJSON(geom) AS geom, title, descrip
                    FROM need
                    WHERE user_id=%s
                """, (user_id,))
        features = [
            {
                "id": row["need_id"],          
                "user_id": row["user_id"],
                "geom": row["geom"],
                "title": row["title"],
                "descrip": row["descrip"]
            } 
            for row in cursor.fetchall()
        ]
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify({"features": features})


@app.route("/needs/<int:need_id>")
def need_details(need_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT n.need_id, n.title, n.descrip, n.urgency, n.category, n.user_id, n.address_point,
                   ST_AsGeoJSON(n.geom) AS geom
            FROM need n
            WHERE n.need_id = %s
        """, (need_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Need not found"}), 404

        geom = json.loads(row["geom"])  # Convertir string JSON a objeto
        return jsonify({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "need_id": row["need_id"],
                "title": row["title"],
                "descrip": row["descrip"],
                "urgency": row["urgency"],
                "category": row["category"],
                "user_id": row["user_id"],
                "address_point": row.get("address_point", "")
            }
        })
    finally:
        cursor.close()
        release_db_connection(conn)


# ─── OFFERS ───────────────────────────────────────────────────────────────────

@app.route("/edit-offer/<int:offer_id>", methods=["POST"])
def update_offer(offer_id):
    data = request.get_json()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE offer
        SET title = %s,
            descrip = %s,
            category = %s,
            address_point = %s,
            geom = ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), 3857),
            updated_at = NOW()
        WHERE offer_id = %s AND user_id = %s
    """, (
        data["title"],
        data["descrip"],
        data["category"],
        data["address_point"],
        data["geom"],
        offer_id,
        session["user_id"]
    ))

    conn.commit()
    cursor.close()
    release_db_connection(conn)

    return {"success": True}

@app.route("/edit-offer/<int:offer_id>")
def edit_offer_page(offer_id):
    return render_template("edit_offer.html", offer_id=offer_id)

@app.route("/edit-offer/<int:offer_id>", methods=["GET"])
def edit_offer(offer_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            offer_id,
            title,
            descrip,
            category,
            address_point,
            ST_AsGeoJSON(ST_Transform(geom, 4326)) AS geom
        FROM offer
        WHERE offer_id = %s AND user_id = %s
    """, (offer_id, session["user_id"]))

    row = cursor.fetchone()

    cursor.close()
    release_db_connection(conn)

    if not row:
        return "Offer not found or you don't have permission", 404

    return render_template("edit_offer.html", offer=row)

@app.route("/offers/<int:offer_id>")
def get_offer(offer_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT json_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(geom)::json,
            'properties', json_build_object(
                'offer_id', offer_id,
                'title', title,
                'descrip', descrip,
                'category', category,
                'address_point', address_point
            )
        ) AS feature
        FROM offer
        WHERE offer_id = %s AND user_id = %s
    """, (offer_id, session["user_id"]))

    row = cursor.fetchone()

    cursor.close()
    release_db_connection(conn)

    if not row:
        return {"error": "Offer not found"}, 404

    return row["feature"]



@app.route('/offers', methods=['GET'])
def get_offers():
    """Returns all offers as a GeoJSON FeatureCollection.

    Returns:
        GeoJSON FeatureCollection with offer properties and point geometry
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
                    SELECT o.offer_id,
                        o.user_id,
                        o.title,
                        o.descrip,
                        o.address_point,
                        s.code as status,
                        c.name_cat as category,
                        ST_AsGeoJSON(o.geom)::json as geom
                    FROM offer o
                    JOIN status_domain s ON o.status_id = s.status_id
                    JOIN category c ON o.category = c.category_id
                    WHERE s.code = 'active'

                """)
        offers = cursor.fetchall()
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify(format_geojson(offers))


@app.route('/create-offer', methods=['POST'])
def create_offer():
    """Creates a new offer for the current logged-in user.

    JSON body: title, descrip, category, lat, lng, address_point

    Returns:
        JSON with offer_id and success flag, 201 on success
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO offer (
                user_id, title, descrip, category, geom, address_point, status_id
            )
            VALUES (
                %s, %s, %s, %s,
                ST_Transform(
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                    3857
                ),
                %s,
                (SELECT status_id FROM status_domain WHERE code = 'active')
            )
            RETURNING offer_id;
        """, (
            user_id,
            data.get('title'),
            data.get('descrip'),
            data.get('category'),
            data.get('lng'),
            data.get('lat'),
            data.get('address_point')
        ))

        new_offer_id = cursor.fetchone()['offer_id']
        conn.commit()

        return jsonify({
            "message": "Offer created successfully",
            "offer_id": new_offer_id,
            "success": True
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        release_db_connection(conn)


@app.route("/create-offer", methods=["GET"])
def create_offer_form():
    """Renders the create offer form."""
    return render_template("create_offer.html")


@app.route("/my-offers", methods=["GET"])
def my_offers():
    """Returns the current user's offers as a list of GeoJSON features.

    Returns:
        JSON object with a features list
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT offer_id, user_id, ST_AsGeoJSON(geom) AS geom, title, descrip
            FROM offer
            WHERE user_id = %s
        """, (user_id,))
        features = [
            {
                "id": row["offer_id"],          
                "user_id": row["user_id"],
                "geom": row["geom"],
                "title": row["title"],
                "descrip": row["descrip"]
            } 
            for row in cursor.fetchall()
        ]
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify({"features": features})


# ─── ASSIGNMENTS ──────────────────────────────────────────────────────────────

def send_assignment_email(to_email, accepter_email, item_type, title):
    """
    Sends notification when someone accepts a need or offer.

    Args:
        to_email (str): email of the owner of the need/offer
        accepter_email (str): email of the user who accepted
        item_type (str): "need" or "offer"
        title (str): title of the accepted item
    """

    msg = EmailMessage()
    msg["Subject"] = "Your item has been accepted!"
    msg["From"] = config["email"]["address"]
    msg["To"] = to_email

    msg.set_content(
        f"""
Good news!

Someone has accepted your {item_type} titled:

"{title}"

You can contact them at:
{accepter_email}

Community Hazard Response Platform
        """
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(
            config["email"]["address"],
            config["email"]["password"]
        )
        smtp.send_message(msg)

@app.route('/assignments', methods=['POST'])
def create_assignment():
    """Creates an assignment linking a need to an offer.
    
    If offer_id is provided in the body it uses that directly.
    Otherwise it auto-matches the user's active offer by category.

    Returns:
        JSON with assignment_id, 201 on success
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    body = request.get_json()
    need_id = body.get("need_id")
    offer_id = body.get("offer_id")
    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # If offer_id not provided, auto-find matching offer by category
        if not offer_id:
            cursor.execute("""
                SELECT o.offer_id FROM offer o
                JOIN need n ON n.need_id = %s
                WHERE o.user_id = %s
                  AND o.category = n.category
                  AND o.status_id = (SELECT status_id FROM status_domain WHERE code = 'active')
                LIMIT 1
            """, (need_id, user_id))
            offer = cursor.fetchone()
            if not offer:
                return jsonify({"error": "You have no active offer matching this need's category"}), 400
            offer_id = offer["offer_id"]

        # Check if need already has an active assignment
        cursor.execute("""
            SELECT assignment_id FROM assignments 
            WHERE need_id = %s 
            AND status_ass IN ('proposed', 'accepted')
        """, (need_id,))
        existing = cursor.fetchone()
        if existing:
            return jsonify({"error": "This need has already been assigned to a volunteer"}), 400

        cursor.execute("""
            INSERT INTO assignments (need_id, offer_id, notes)
            VALUES (%s, %s, %s)
            RETURNING assignment_id
        """, (need_id, offer_id, body.get("notes")))
        assignment_id = cursor.fetchone()["assignment_id"]

                # --- GET EMAILS AND TITLE FOR NOTIFICATION ---

        # Get title and owner email
        cursor.execute("""
            SELECT n.title AS need_title,
                o.title AS offer_title,
                n.user_id AS need_owner,
                o.user_id AS offer_owner
            FROM need n
            JOIN offer o ON o.offer_id = %s
            WHERE n.need_id = %s
        """, (offer_id, need_id))

        item = cursor.fetchone()

        # Email of the user who accepted
        cursor.execute("""
            SELECT email FROM app_user WHERE user_id = %s
        """, (user_id,))
        accepter_email = cursor.fetchone()["email"]

        # Determine who to notify
        if user_id == item["need_owner"]:
            # Need owner accepted an offer → notify offer owner
            cursor.execute("""
                SELECT email FROM app_user WHERE user_id = %s
            """, (item["offer_owner"],))
            to_email = cursor.fetchone()["email"]
            send_assignment_email(to_email, accepter_email, "offer", item["offer_title"])

        else:
            # Offer owner accepted a need → notify need owner
            cursor.execute("""
                SELECT email FROM app_user WHERE user_id = %s
            """, (item["need_owner"],))
            to_email = cursor.fetchone()["email"]
            send_assignment_email(to_email, accepter_email, "need", item["need_title"])
            
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify({"message": f"Assignment {assignment_id} created"}), 201


@app.route("/my-assignments")
def my_assignments():
    """Returns assignments involving the current user (as need owner or offer owner).

    Returns:
        JSON object with a features list containing geom, title, descrip
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                ST_AsGeoJSON(n.geom) AS geom,
                n.title,
                n.descrip
            FROM assignments a
            JOIN need n ON n.need_id = a.need_id
            JOIN offer o ON o.offer_id = a.offer_id
            WHERE n.user_id = %s OR o.user_id = %s
        """, (user_id, user_id))

        features = [
            {"geom": row["geom"], "title": row["title"], "descrip": row["descrip"]}
            for row in cursor.fetchall()
        ]
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify({"features": features})

@app.route("/assignments", methods=["POST"])
def create_assignment():

    data = request.json
    user_id = session["user_id"]

    need_id = data.get("need_id")
    offer_id = data.get("offer_id")

    if not need_id and not offer_id:
        return jsonify({"error": "No item to assign"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if need_id and not offer_id:
            # Accept a need → create a temporary offer based on the need
            cursor.execute("""
                INSERT INTO offer (user_id, title, descrip, category, geom, status_id)
                SELECT %s, title, descrip, category, geom, 
                       (SELECT status_id FROM status_domain WHERE code='active')
                FROM need
                WHERE need_id = %s
                RETURNING offer_id
            """, (user_id, need_id))
            offer_id = cursor.fetchone()["offer_id"]  

        elif offer_id and not need_id:
            # Accept an offer → create temporary need for the user
            cursor.execute("""
                INSERT INTO need (user_id, title, descrip, category, geom, status_id)
                SELECT %s, title, descrip, category, geom, 
                       (SELECT status_id FROM status_domain WHERE code='active')
                FROM offer
                WHERE offer_id = %s
                RETURNING need_id
            """, (user_id, offer_id))
            need_id = cursor.fetchone()["need_id"]  


        # --- CREATE ASSIGNMENT ---
        cursor.execute("""
            INSERT INTO assignments (need_id, offer_id, status_ass)
            VALUES (%s, %s, 'proposed')
            RETURNING assignment_id
        """, (need_id, offer_id))
        assignment_id = cursor.fetchone()["assignment_id"]

        # --- UPDATE STATUS OF NEED AND OFFER ---
        cursor.execute("""
            UPDATE need
            SET status_id = (SELECT status_id FROM status_domain WHERE code='assigned')
            WHERE need_id = %s
        """, (need_id,))
        cursor.execute("""
            UPDATE offer
            SET status_id = (SELECT status_id FROM status_domain WHERE code='assigned')
            WHERE offer_id = %s
        """, (offer_id,))

        conn.commit()

        return jsonify({"success": True, "assignment_id": assignment_id, "need_id": need_id, "offer_id": offer_id}), 201

    finally:
        cursor.close()
        release_db_connection(conn)




@app.route('/assignments/<id>/complete', methods=['PUT'])
def complete_assignment(id):
    """Marks an assignment as completed.

    Args:
        id (int): assignment ID from URL

    Returns:
        JSON confirmation message
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE assignments
            SET status_ass = 'completed'
            WHERE assignment_id = %s
        """, (id,))
        conn.commit()
    except Exception:
        return jsonify({"error": "Failed to complete assignment"}), 500
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify({"message": f"Assignment {id} completed"})


@app.route('/my-offers-for-need/<int:need_id>', methods=['GET'])
def my_offers_for_need(need_id):
    """Returns the current user's active offers that match a given need's category.

    Args:
        need_id (int): the need ID to match against

    Returns:
        JSON with list of matching offers
    """
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT o.offer_id, o.title FROM offer o
            JOIN need n ON n.need_id = %s
            WHERE o.user_id = %s
              AND o.category = n.category
              AND o.status_id = (SELECT status_id FROM status_domain WHERE code = 'active')
        """, (need_id, user_id))
        offers = cursor.fetchall()
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify({"offers": offers})


# ─── FACILITIES ───────────────────────────────────────────────────────────────

@app.route("/facility-types", methods=["GET"])
def get_facility_types():
    """Returns a list of distinct facility types present in the database.

    Returns:
        JSON list of facility type strings
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT facility_type FROM facility")
        types = [row["facility_type"] for row in cursor.fetchall()]
    finally:
        cursor.close()
        release_db_connection(conn)
    return jsonify(types)


@app.route('/facilities', methods=['GET'])
def get_facilities():
    """Returns all facilities as a GeoJSON FeatureCollection.

    Returns:
        GeoJSON FeatureCollection with facility properties and point geometry
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT f.osm_id,
                   f.name_fac,
                   f.facility_type,
                   ST_AsGeoJSON(f.geom)::json as geom
            FROM facility f
        """)
        facilities = cursor.fetchall()
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify(format_geojson(facilities))


# ─── URGENCY ──────────────────────────────────────────────────────────────────

@app.route('/urgency-levels', methods=['GET'])
def get_urgency_levels():
    """Returns all urgency levels ordered by severity.

    Returns:
        JSON list of {urgency_id, code, name} objects
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT urgency_id, code, name
            FROM urgency_domain
            ORDER BY urgency_id
        """)
        rows = cursor.fetchall()
        return jsonify(rows)
    finally:
        cursor.close()
        release_db_connection(conn)


# ─── ADMINISTRATIVE AREAS ─────────────────────────────────────────────────────

@app.route("/admin-areas", methods=["GET"])
def get_admin_areas():
    """Searches administrative areas by name (autocomplete).

    Query params:
        q (str): partial name to search for

    Returns:
        JSON list of {area_id, name_area} objects (max 10)
    """
    query = request.args.get("q", "")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT area_id, name_area
            FROM administrative_area
            WHERE name_area ILIKE %s
            ORDER BY name_area
            LIMIT 10
        """, (f"%{query}%",))
        areas = [{"area_id": row["area_id"], "name_area": row["name_area"]} for row in cursor.fetchall()]
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify(areas)


@app.route('/admin-areas/stats', methods=['GET'])
def get_admin_area_stats():
    """Returns active need and offer counts per administrative area.

    Uses a spatial join (ST_Within) to count how many active needs and offers
    fall inside each administrative area polygon. Includes a gap_score
    (needs minus offers) useful for choropleth mapping.

    Query params:
        admin_level (int): optional filter by admin level (6 = municipalities, 8 = parishes)

    Returns:
        GeoJSON FeatureCollection of area polygons with need_count, offer_count
        and gap_score properties, plus summary totals in meta
    """
    admin_level = request.args.get('admin_level', None, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        level_filter = "AND a.admin_level = %(admin_level)s" if admin_level else ""

        cursor.execute(f"""
            SELECT
                a.area_id,
                a.name_area,
                a.admin_level,
                ST_AsGeoJSON(ST_Transform(a.geom, 4326))::json AS geom,
                COUNT(DISTINCT n.need_id)  AS need_count,
                COUNT(DISTINCT o.offer_id) AS offer_count
            FROM administrative_area a
            LEFT JOIN need n
                ON ST_Within(n.geom, a.geom)
                AND n.status_id = (SELECT status_id FROM status_domain WHERE code = 'active')
            LEFT JOIN offer o
                ON ST_Within(o.geom, a.geom)
                AND o.status_id = (SELECT status_id FROM status_domain WHERE code = 'active')
            WHERE 1=1 {level_filter}
            GROUP BY a.area_id, a.name_area, a.admin_level, a.geom
            ORDER BY need_count DESC
        """, {"admin_level": admin_level})

        rows = cursor.fetchall()

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        release_db_connection(conn)

    features = [
        {
            "type": "Feature",
            "geometry": row["geom"],
            "properties": {
                "area_id":     row["area_id"],
                "name_area":   row["name_area"],
                "admin_level": row["admin_level"],
                "need_count":  row["need_count"],
                "offer_count": row["offer_count"],
                # Areas with high needs and low offers are highest priority
                "gap_score":   row["need_count"] - row["offer_count"]
            }
        }
        for row in rows
    ]

    return jsonify({
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "admin_level_filter":  admin_level,
            "total_areas":         len(features),
            "total_active_needs":  sum(f["properties"]["need_count"] for f in features),
            "total_active_offers": sum(f["properties"]["offer_count"] for f in features)
        }
    })


# ─── SEARCH ───────────────────────────────────────────────────────────────────

@app.route("/search", methods=["GET"])
def search():
    """Filters needs, offers and facilities by administrative area and type.

    Query params:
        query (str): administrative area name to filter by
        type (str): one of 'needs', 'offers', 'facility', 'all'
        facilityTypes (list): facility types to include (repeatable param)

    Returns:
        JSON object with needs, offers and facility lists
    """
    query = request.args.get("query", "").strip().lower()
    filter_type = request.args.get("type", "all")
    facility_types = request.args.getlist("facilityTypes")

    conn = get_db_connection()
    cursor = conn.cursor()
    results = {"needs": [], "offers": [], "facility": []}

    try:
        # Resolve admin area name to geometry for spatial filtering
        if query:
            cursor.execute("""
                SELECT geom
                FROM administrative_area
                WHERE LOWER(name_area) LIKE %s
            """, (f"%{query}%",))
            area = cursor.fetchone()
            geom_filter = area["geom"] if area else None
        else:
            geom_filter = None

        # Needs
        if filter_type in ("needs", "all"):
            sql = """SELECT n.need_id, n.title, n.descrip, n.user_id, 
                    c.name_cat as category, ST_AsGeoJSON(n.geom) AS geom 
                    FROM need n JOIN category c ON n.category = c.category_id"""
            if geom_filter:
                sql += " WHERE ST_Within(geom, %s)"
                cursor.execute(sql, (geom_filter,))
            else:
                cursor.execute(sql)
            results["needs"] = cursor.fetchall()

        # Offers
        if filter_type in ("offers", "all"):
            sql = """SELECT o.offer_id, o.title, o.descrip, o.user_id,
                     ST_AsGeoJSON(o.geom) AS geom 
                     FROM offer o"""
            if geom_filter:
                sql += " WHERE ST_Within(geom, %s)"
                cursor.execute(sql, (geom_filter,))
            else:
                cursor.execute(sql)
            results["offers"] = cursor.fetchall()

        # Facilities (with optional type filter)
        if filter_type in ("facility", "all"):
            if facility_types and "all" not in facility_types:
                types_clause = tuple(facility_types)
                sql = "SELECT name_fac, facility_type, ST_AsGeoJSON(geom) AS geom FROM facility WHERE facility_type IN %s"
                if geom_filter:
                    sql += " AND ST_Within(geom, %s)"
                    cursor.execute(sql, (types_clause, geom_filter))
                else:
                    cursor.execute(sql, (types_clause,))
            else:
                sql = "SELECT name_fac, facility_type, ST_AsGeoJSON(geom) AS geom FROM facility"
                if geom_filter:
                    sql += " WHERE ST_Within(geom, %s)"
                    cursor.execute(sql, (geom_filter,))
                else:
                    cursor.execute(sql)
            results["facility"] = cursor.fetchall()

    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)
