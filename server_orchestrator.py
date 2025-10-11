# server_orchestrator.py
# Orchestrator server (port 8000)
# Install dependencies: pip install flask psycopg2-binary

from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "mini_uber"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "omkar13"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}

app = Flask(__name__)

def get_conn():
    return psycopg2.connect(cursor_factory=RealDictCursor, **DB_CONFIG)

# Health
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "orchestrator"}), 200

# Create a ride request (called by user client)
# JSON: { "user_id": 1, "pickup": "HSR", "dropoff": "Airport" }
@app.route("/request_ride", methods=["POST"])
def request_ride():
    data = request.get_json(force=True)
    user_id = data.get("user_id")
    pickup = data.get("pickup")
    dropoff = data.get("dropoff")
    if not (user_id and pickup and dropoff):
        return jsonify({"error": "user_id, pickup and dropoff are required"}), 400

    sql = """
        INSERT INTO ride_requests (user_id, pickup_location, dropoff_location, status)
        VALUES (%s, %s, %s, 'pending') RETURNING request_id, request_time;
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, pickup, dropoff))
                row = cur.fetchone()
                return jsonify({"request_id": row["request_id"], "request_time": row["request_time"].isoformat()}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Driver updates availability and optionally location
# JSON: { "driver_id": 1, "is_available": true, "latitude": 12.9, "longitude": 77.6 }
@app.route("/driver_status", methods=["POST"])
def driver_status():
    data = request.get_json(force=True)
    driver_id = data.get("driver_id")
    is_available = data.get("is_available")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    if driver_id is None or is_available is None:
        return jsonify({"error": "driver_id and is_available are required"}), 400

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                # Update drivers.is_available
                cur.execute("UPDATE drivers SET is_available = %s WHERE driver_id = %s RETURNING driver_id;", (is_available, driver_id))
                if cur.rowcount == 0:
                    return jsonify({"error": "driver not found"}), 404

                # Insert or update driver_locations
                if latitude is not None and longitude is not None:
                    # upsert into driver_locations by driver_id (simple approach: insert new row)
                    cur.execute("""
                        INSERT INTO driver_locations (driver_id, latitude, longitude, last_updated)
                        VALUES (%s, %s, %s, NOW())
                    """, (driver_id, latitude, longitude))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# List pending ride requests (for matcher or admin)
@app.route("/pending_requests", methods=["GET"])
def pending_requests():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT rr.request_id, rr.user_id, u.name AS user_name,
                       rr.pickup_location, rr.dropoff_location, rr.request_time, rr.status
                FROM ride_requests rr
                JOIN users u ON rr.user_id = u.user_id
                WHERE rr.status = 'pending'
                ORDER BY rr.request_time ASC;
            """)
            rows = cur.fetchall()
            return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# List available drivers (for matcher)
@app.route("/available_drivers", methods=["GET"])
def available_drivers():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT d.driver_id, d.name, d.phone, dl.latitude, dl.longitude, d.created_at
                FROM drivers d
                LEFT JOIN lateral (
                    SELECT latitude, longitude FROM driver_locations dl2
                    WHERE dl2.driver_id = d.driver_id
                    ORDER BY dl2.last_updated DESC
                    LIMIT 1
                ) dl ON true
                WHERE d.is_available = true;
            """)
            rows = cur.fetchall()
            return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Assign a driver to a request (matcher calls this)
# JSON: { "request_id": 1, "driver_id": 2 }
@app.route("/assign", methods=["POST"])
def assign():
    data = request.get_json(force=True)
    request_id = data.get("request_id")
    driver_id = data.get("driver_id")
    if not (request_id and driver_id):
        return jsonify({"error": "request_id and driver_id required"}), 400

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                # Check request is pending
                cur.execute("SELECT * FROM ride_requests WHERE request_id = %s FOR UPDATE;", (request_id,))
                req = cur.fetchone()
                if not req:
                    return jsonify({"error": "request not found"}), 404
                if req["status"] != "pending":
                    return jsonify({"error": f"request not pending (status={req['status']})"}), 400

                # Check driver is available
                cur.execute("SELECT is_available FROM drivers WHERE driver_id = %s FOR UPDATE;", (driver_id,))
                drv = cur.fetchone()
                if not drv:
                    return jsonify({"error": "driver not found"}), 404
                if not drv["is_available"]:
                    return jsonify({"error": "driver not available"}), 400

                # Mark request accepted
                cur.execute("UPDATE ride_requests SET status = 'accepted' WHERE request_id = %s;", (request_id,))

                # Insert into rides copying details from ride_requests
                cur.execute("""
                    INSERT INTO rides (request_id, driver_id, user_id, pickup, destination, start_time, status)
                    SELECT request_id, %s, user_id, pickup_location, dropoff_location, NOW(), 'ongoing'
                    FROM ride_requests WHERE request_id = %s
                    RETURNING ride_id;
                """, (driver_id, request_id))
                ride_row = cur.fetchone()

                # Mark driver unavailable
                cur.execute("UPDATE drivers SET is_available = false WHERE driver_id = %s;", (driver_id,))

                conn.commit()
                return jsonify({
                    "ride_id": ride_row["ride_id"],
                    "request_id": request_id,
                    "driver_id": driver_id
                }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Optional: mark ride completed
# JSON: { "ride_id": 1, "driver_id": 2 }
@app.route("/complete", methods=["POST"])
def complete():
    data = request.get_json(force=True)
    ride_id = data.get("ride_id")
    driver_id = data.get("driver_id")
    if not (ride_id and driver_id):
        return jsonify({"error": "ride_id and driver_id required"}), 400

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE rides
                    SET status = 'completed', end_time = NOW()
                    WHERE ride_id = %s AND driver_id = %s
                    RETURNING ride_id;
                """, (ride_id, driver_id))
                r = cur.fetchone()
                if not r:
                    return jsonify({"error": "ride not found or driver mismatch"}), 404

                # mark driver available again
                cur.execute("UPDATE drivers SET is_available = true WHERE driver_id = %s;", (driver_id,))
                conn.commit()
                return jsonify({"ride_id": r["ride_id"], "status": "completed"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == "__main__":
    from waitress import serve
    print("🚀 Starting Orchestrator on http://127.0.0.1:8080")
    serve(app, host="127.0.0.1", port=8080)

