import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "database": "mini_uber",
    "user": "postgres",             # use the DB owner you see in pgAdmin
    "password": "omkar13",  # the same password you set in pgAdmin
    "host": "localhost",
    "port": "5433"
}


def connect_db():
    # Pass only valid connection parameters to psycopg2.connect
    conn = psycopg2.connect(
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"]
    )
    return conn

def register_driver(name, email):
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO drivers (name, email) VALUES (%s, %s)
            ON CONFLICT (email) DO NOTHING
            RETURNING id;
        """, (name, email))
        driver_id = cur.fetchone()
        conn.commit()
        return {"driver_id": driver_id[0] if driver_id else None, "status": "registered"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()

def request_ride(user_id, pickup, destination):
    conn = connect_db()
    cur = conn.cursor()
    try:
        # Insert ride
        cur.execute("""
            INSERT INTO rides (user_id, pickup, destination, status)
            VALUES (%s, %s, %s, 'waiting') RETURNING ride_id;
        """, (user_id, pickup, destination))
        ride_row = cur.fetchone()
        if ride_row is None:
            return {"error": "Failed to create ride."}
        ride_id = ride_row[0]

        # Assign first available driver
        cur.execute("""
            SELECT id FROM drivers
            WHERE id NOT IN (SELECT driver_id FROM rides WHERE status IN ('assigned','ongoing'))
            LIMIT 1;
        """)
        driver = cur.fetchone()

        if driver:
            cur.execute("UPDATE rides SET driver_id=%s, status='assigned' WHERE ride_id=%s;",
                        (driver[0], ride_id))
            conn.commit()
            return {"ride_id": ride_id, "driver_id": driver[0], "status": "assigned"}
        else:
            conn.commit()
            return {"ride_id": ride_id, "status": "waiting"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()

def driver_rides(driver_id):
    conn = connect_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM rides WHERE driver_id=%s;", (driver_id,))
        return cur.fetchall()
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()
