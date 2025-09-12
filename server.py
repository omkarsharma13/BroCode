from fastapi import FastAPI
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

# --- Database connection ---
def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="mini_uber",   # change to your DB name
        user="postgres",        # change if you use a different user
        password="yourpassword",  # change to your password
        port=5432
    )

# --- API Endpoints ---

@app.post("/register_driver")
def register_driver(name: str, phone: str):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            INSERT INTO drivers (name, phone, status)
            VALUES (%s, %s, 'available')
            RETURNING id, name, phone, status
            """,
            (name, phone),
        )
        driver = cur.fetchone()
        conn.commit()

        cur.close()
        conn.close()
        return {"message": "Driver registered successfully", "driver": driver}
    except Exception as e:
        return {"error": str(e)}

@app.post("/book_ride")
def book_ride(user_id: int, pickup: str, drop: str):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            INSERT INTO rides (user_id, pickup, drop, status)
            VALUES (%s, %s, %s, 'pending')
            RETURNING id, user_id, pickup, drop, status
            """,
            (user_id, pickup, drop),
        )
        ride = cur.fetchone()
        conn.commit()

        cur.close()
        conn.close()
        return {"message": "Ride booked successfully", "ride": ride}
    except Exception as e:
        return {"error": str(e)}

@app.get("/ride_status/{ride_id}")
def ride_status(ride_id: int):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM rides WHERE id = %s", (ride_id,))
        ride = cur.fetchone()

        cur.close()
        conn.close()

        if ride:
            return {"ride": ride}
        return {"error": "Ride not found"}
    except Exception as e:
        return {"error": str(e)}
