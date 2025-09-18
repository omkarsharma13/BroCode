import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
def get_connection():
    return psycopg2.connect(
        dbname="mini_uber",
        user="postgres",         # change if needed
        password="omkar13",  # 🔑 update with your password
        host="localhost",
        port="5433"
    )

# --------------------
# User functions
# --------------------
def register_user(name, email, phone):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, email, phone) VALUES (%s, %s, %s) RETURNING user_id;",
        (name, email, phone)
    )
    result = cur.fetchone()
    if result is None:
        conn.rollback()
        cur.close()
        conn.close()
        return {"error": "User registration failed"}
    user_id = result[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"user_id": user_id, "status": "registered"}

# --------------------
# Driver functions
# --------------------
def register_driver(name, email, phone, vehicle_number):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO drivers (name, email, phone, vehicle_number) VALUES (%s, %s, %s, %s) RETURNING driver_id;",
        (name, email, phone, vehicle_number)
    )
    result = cur.fetchone()
    if result is None:
        conn.rollback()
        cur.close()
        conn.close()
        return {"error": "Driver registration failed"}
    driver_id = result[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"driver_id": driver_id, "status": "registered"}

# --------------------
# Ride functions
# --------------------
def request_ride(user_id, pickup, destination):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO rides (user_id, pickup, destination) VALUES (%s, %s, %s) RETURNING ride_id;",
        (user_id, pickup, destination)
    )
    result = cur.fetchone()
    if result is None:
        conn.rollback()
        cur.close()
        conn.close()
        return {"error": "Ride request failed"}
    ride_id = result[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"ride_id": ride_id, "status": "requested"}

def assign_driver(ride_id):
    conn = get_connection()
    cur = conn.cursor()

    # pick first available driver
    cur.execute("SELECT driver_id FROM drivers WHERE status = 'available' LIMIT 1;")
    driver = cur.fetchone()

    if not driver:
        cur.close()
        conn.close()
        return {"error": "No drivers available"}

    driver_id = driver[0]

    # update ride
    cur.execute("UPDATE rides SET driver_id = %s, status = 'ongoing' WHERE ride_id = %s;",
                (driver_id, ride_id))
    # update driver status
    cur.execute("UPDATE drivers SET status = 'busy' WHERE driver_id = %s;", (driver_id,))

    conn.commit()
    cur.close()
    conn.close()
    return {"ride_id": ride_id, "driver_id": driver_id, "status": "ongoing"}
def driver_rides(driver_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ride_id, user_id, pickup, destination, status, requested_at, completed_at
        FROM rides
        WHERE driver_id = %s;
    """, (driver_id,))
    rides = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return rides
