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
import json
from email.message import EmailMessage

def load_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    config_path = os.path.join(project_root, "config", "config.yml")

    with open(config_path) as f:
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

            return render_template("dashboard.html", username=user["username"], user_id=session["user_id"])
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

    return render_template("dashboard.html", username=session["username"], user_id=session["user_id"])

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
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT n.need_id,
                   n.user_id,
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
            WHERE s.code = 'active'
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

@app.route("/my-needs")
def my_needs():
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

# OFFERS (GeoJSON)

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


@app.route("/my-offers", methods=["GET"])
def my_offers():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"features": []})

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



@app.route('/offers', methods=['GET'])
def get_offers():
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

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO offer (
                user_id,
                title,
                descrip,
                category,
                geom,
                address_point,
                status_id
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
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
    return render_template("create_offer.html")


# ASSIGNMENTS


@app.route("/my-assignments")
def my_assignments():
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Seleccionamos el geom del need asociado al assignment del usuario
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
            {
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


@app.route("/assignments", methods=["POST"])
def create_assignment():
    """
    Crear un assignment a partir de una necesidad o una oferta.
    - Si se acepta una necesidad, crea primero un offer temporal.
    - Si se acepta una oferta, crea primero una need temporal.
    """
    data = request.json
    user_id = session["user_id"]

    need_id = data.get("need_id")
    offer_id = data.get("offer_id")

    if not need_id and not offer_id:
        return jsonify({"error": "No item to assign"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # --- CREAR ITEMS TEMPORALES SI NO EXISTEN ---
        if need_id and not offer_id:
            # Aceptaste una necesidad → crear oferta temporal para ti
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
            # Aceptaste una oferta → crear necesidad temporal para ti
            cursor.execute("""
                INSERT INTO need (user_id, title, descrip, category, geom, status_id)
                SELECT %s, title, descrip, category, geom, 
                       (SELECT status_id FROM status_domain WHERE code='active')
                FROM offer
                WHERE offer_id = %s
                RETURNING need_id
            """, (user_id, offer_id))
            need_id = cursor.fetchone()["need_id"]  


        # --- CREAR ASSIGNMENT ---
        cursor.execute("""
            INSERT INTO assignments (need_id, offer_id, status_ass)
            VALUES (%s, %s, 'proposed')
            RETURNING assignment_id
        """, (need_id, offer_id))
        assignment_id = cursor.fetchone()["assignment_id"]

        # --- ACTUALIZAR STATUS DE NEED Y OFFER ---
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



def send_email(to_email, subject, body):
    msg = email.message.EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = "no-reply@community-platform.com"
    msg["To"] = to_email

    with smtplib.SMTP("localhost") as s:
        s.send_message(msg)




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

#URGENCY
@app.route('/urgency-levels', methods=['GET'])
def get_urgency_levels():
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
                FROM administrative_area
                WHERE LOWER(name_area) LIKE %s
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
            sql = "SELECT title, descrip, ST_AsGeoJSON(geom) AS geom FROM need AS n JOIN status_domain s ON n.status_id = s.status_id AND s.code = 'active'"
            if geom_filter:
                sql += " WHERE ST_Within(geom, %s)"
                cursor.execute(sql, (geom_filter,))
            else:
                cursor.execute(sql)
            results["needs"] = cursor.fetchall()

        # Offers
        if filter_type in ("offers", "all"):
            sql = "SELECT descrip, ST_AsGeoJSON(geom) AS geom FROM offer AS o JOIN status_domain s ON o.status_id = s.status_id AND s.code = 'active'"
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
                sql = f"SELECT name_fac, facility_type, ST_AsGeoJSON(geom) AS geom FROM facility WHERE facility_type IN %s"
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

@app.route("/admin-areas", methods=["GET"])
def get_admin_areas():
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




if __name__ == '__main__':
    app.run(debug=True)