from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from utils import format_geojson   

DB_CONFIG = {
    "database": "solidarity_db",
    "user": "postgres",
    "password": "your_password",
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

app = Flask(__name__)

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


@app.route('/users', methods=['POST'])
def create_user():
    body = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO app_user (username, email, hashed_password, firstname, surname, phone)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING user_id
    """

    values = (
        body["username"],
        body["email"],
        body["hashed_password"],
        body["firstname"],
        body["surname"],
        body.get("phone")
    )

    try:
        cursor.execute(query, values)
        user_id = cursor.fetchone()["user_id"]
        conn.commit()
    except Exception:
        return jsonify({"error": "Failed to create user"}), 500
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify({"message": f"User {user_id} created"}), 201


# CATEGORY

@app.route('/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM category")
        categories = cursor.fetchall()
    finally:
        cursor.close()
        release_db_connection(conn)
    return jsonify(categories)


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
    body = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO need (user_id, title, descrip, category, urgency, geom, address_point)
        VALUES (
            %s, %s, %s, %s, %s,
            ST_SetSRID(ST_MakePoint(%s, %s), 3857),
            %s
        )
        RETURNING need_id
    """

    values = (
        body["user_id"],
        body["title"],
        body["descrip"],
        body["category"],
        body["urgency"],
        body["longitude"],
        body["latitude"],
        body.get("address_point")
    )

    try:
        cursor.execute(query, values)
        need_id = cursor.fetchone()["need_id"]
        conn.commit()
    except Exception:
        return jsonify({"error": "Failed to create need"}), 500
    finally:
        cursor.close()
        release_db_connection(conn)

    return jsonify({"message": f"Need {need_id} created"}), 201


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


if __name__ == '__main__':
    app.run(debug=True)
