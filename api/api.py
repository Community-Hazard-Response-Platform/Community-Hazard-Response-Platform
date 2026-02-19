from flask import Flask, redirect, request, jsonify, render_template, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from utils import format_geojson   
import os
import bcrypt
import secrets
import smtplib
from email.message import EmailMessage

DB_CONFIG = {
    "database": "solidarity_db",
    "user": "postgres",
    "password": "belen2003",
    "host": "localhost",
    "port": "5432"
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

app.secret_key = "una_clave_super_secreta"

def get_db_connection():
    return db_pool.getconn()

def release_db_connection(conn):
    db_pool.putconn(conn)

# USERS

@app.route('/users', methods=['GET'])
def get_users():
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
    if "user_id" not in session:
        return redirect("/")
    
    return render_template("profile_page.html")

@app.route("/profile", methods=["GET"])
def profile():
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
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # borrar usuario
        cursor.execute("DELETE FROM app_user WHERE user_id=%s", (user_id,))
        conn.commit()
    finally:
        cursor.close()
        release_db_connection(conn)
    
    session.clear()
    return jsonify({"success": True})

def send_verification_email(email, token):
    link = url_for("verify_account", token=token, _external=True)

    msg = EmailMessage()
    msg["Subject"] = "Verify your account"
    msg["From"] = "jd0communityhazard@gmail.com"
    msg["To"] = email
    msg.set_content(f"Click to verify your account:\n{link}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(
            "jd0communityhazard@gmail.com",
            "mosxagtvaaomipzm"
        )
        smtp.send_message(msg)



@app.route("/verify/<token>")
def verify_account(token):

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
                (username, email, hashed_password, firstname, surname, phone, verification_token)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING user_id
            """, (username, email, hashed_password, firstname, surname, phone, verification_token))


            user_id = cursor.fetchone()["user_id"]
            conn.commit()

            send_verification_email(email, verification_token)


        except Exception as e:
            return render_template("create_account.html", error="Failed to create user")
        finally:
            cursor.close()
            release_db_connection(conn)

        return render_template("account_created.html")


    # GET → mostrar formulario de registro
    return render_template("create_account.html")


@app.route("/", methods=["GET", "POST"])
def login():
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
            
            # we save the session in order to extract only the info of that user in the future
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]

            return render_template("dashboard.html", username=user["username"])
        else:
            return render_template("login.html", error="Username and password do not match")

    # GET request 
    return render_template("login.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # sam epassword
        if password != confirm_password:
            return render_template("reset_password.html", error="Passwords do not match")
        if len(password) < 8:
            return render_template("reset_password.html", error="Password must be at least 8 characters")

        # user exists in database
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            email = request.form["email"].strip()  # si el input se llama email

            cursor.execute("SELECT user_id FROM app_user WHERE email=%s", (email,))
            user = cursor.fetchone()
            if not user:
                return render_template("reset_password.html", error="No user found with this email")

            # update password
            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            cursor.execute(
                "UPDATE app_user SET hashed_password=%s WHERE email=%s",
                (hashed, email)
            )
            conn.commit()
        finally:
            cursor.close()
            release_db_connection(conn)

        # redirect to success
        return render_template("reset_success.html")

    return render_template("reset_password.html")

# to protect the route of the user
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/")

    return render_template("dashboard.html", username=session["username"])

@app.route("/logout")
def logout():

    session.clear()  # to erase the current session
    return redirect("/")



# CATEGORY

@app.route('/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor()  # si estás usando DictCursor, esto ya devuelve diccionarios
    try:
        cursor.execute("SELECT category_id, name_cat FROM category ORDER BY name_cat")
        categories = cursor.fetchall()  # esto devuelve una lista de diccionarios
        # No necesitas reconstruirlos si ya son diccionarios
        result = [{"id": c["category_id"], "name_cat": c["name_cat"]} for c in categories]
    finally:
        cursor.close()
        release_db_connection(conn)
    return jsonify(result)



# NEEDS (GeoJSON)

@app.route('/needs', methods=['GET'])
def get_needs():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT n.need_id,
                   n.title,
                   n.descrip,
                   n.address_point,
                   s.code as status,
                   u.code as urgency,
                   c.name_cat as category,
                   ST_AsGeoJSON(n.geom)::json as geom
            FROM need n
            JOIN status_domain s ON n.status_id = s.status_id
            JOIN urgency_domain u ON n.urgency = u.urgency_id
            JOIN category c ON n.category = c.category_id
        """)
        needs = cursor.fetchall()
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify(format_geojson(needs)) 


@app.route('/needs', methods=['POST'])
def create_need():

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
    return render_template("create_need.html")


@app.route('/needs/<id>', methods=['DELETE'])
def delete_need(id):
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


# OFFERS (GeoJSON)

@app.route('/offers', methods=['GET'])
def get_offers():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT o.offer_id,
                   o.title,
                   o.descrip,
                   o.address_point,
                   s.code as status,
                   c.name_cat as category,
                   ST_AsGeoJSON(o.geom)::json as geom
            FROM offer o
            JOIN status_domain s ON o.status_id = s.status_id
            JOIN category c ON o.category = c.category_id
        """)
        offers = cursor.fetchall()
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify(format_geojson(offers))  # 👈 FORMATO CORRECTO


# ASSIGNMENTS

@app.route('/assignments', methods=['POST'])
def create_assignment():
    body = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO assignments (need_id, offer_id, notes)
        VALUES (%s, %s, %s)
        RETURNING assignment_id
    """

    try:
        cursor.execute(query, (
            body["need_id"],
            body["offer_id"],
            body.get("notes")
        ))
        assignment_id = cursor.fetchone()["assignment_id"]
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify({"message": f"Assignment {assignment_id} created"}), 201


@app.route('/assignments/<id>/complete', methods=['PUT'])
def complete_assignment(id):
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


# FACILITIES
@app.route("/facility-types", methods=["GET"])
def get_facility_types():
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



# FOR THE SEARCH
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query", "").strip().lower()
    filter_type = request.args.get("type", "all")
    facility_types = request.args.getlist("facilityTypes")  # lista de types

    conn = get_db_connection()
    cursor = conn.cursor()
    results = {"needs": [], "offers": [], "facility": []}

    try:
        # Filter by admin area
        if query:
            cursor.execute("""
                SELECT geom 
                FROM admin_area
                WHERE LOWER(name) LIKE %s
            """, (f"%{query}%",))
            area = cursor.fetchone()
            if area:
                geom_filter = area["geom"]  
            else:
                geom_filter = None
        else:
            geom_filter = None

        # Needs
        if filter_type in ("needs", "all"):
            sql = "SELECT title, descrip, ST_AsGeoJSON(geom) AS geom FROM need"
            if geom_filter:
                sql += " WHERE ST_Within(geom, %s)"
                cursor.execute(sql, (geom_filter,))
            else:
                cursor.execute(sql)
            results["needs"] = cursor.fetchall()

        # Offers
        if filter_type in ("offers", "all"):
            sql = "SELECT descrip, ST_AsGeoJSON(geom) AS geom FROM offer"
            if geom_filter:
                sql += " WHERE ST_Within(geom, %s)"
                cursor.execute(sql, (geom_filter,))
            else:
                cursor.execute(sql)
            results["offers"] = cursor.fetchall()

        # Facility
        if filter_type in ("facility", "all"):
            if facility_types and "all" not in facility_types:
                types_clause = tuple(facility_types)
                sql = f"SELECT name, facility_type, ST_AsGeoJSON(geom) AS geom FROM facility WHERE facility_type IN %s"
                if geom_filter:
                    sql += " AND ST_Within(geom, %s)"
                    cursor.execute(sql, (types_clause, geom_filter))
                else:
                    cursor.execute(sql, (types_clause,))
            else:
                sql = "SELECT name, facility_type, ST_AsGeoJSON(geom) AS geom FROM facility"
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
