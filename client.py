# client.py
import psycopg2
from psycopg2 import OperationalError

# -------------------
# Database configuration
# -------------------
DB_USER = "postgres"
DB_PASSWORD = "your_postgres_password"  # <-- replace with your actual password
DB_HOST = "localhost"
DB_PORT = 5433  # your PostgreSQL port
DB_NAME = "mini_uber"

# -------------------
# Database connection
# -------------------
def create_connection():
    """Create a connection to the existing database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except OperationalError as e:
        print(f"❌ Could not connect to database. Error: {e}")
        return None

# -------------------
# Register a driver
# -------------------
def register_driver(driver_info):
    """Register a driver safely, handling duplicate emails."""
    conn = create_connection()
    if not conn:
        return {"error": "Database connection failed."}

    try:
        cursor = conn.cursor()

        # Check if driver already exists
        cursor.execute("SELECT id FROM drivers WHERE email = %s;", (driver_info["email"],))
        existing = cursor.fetchone()
        if existing:
            driver_id = existing[0]
            cursor.close()
            conn.close()
            return {"driver_id": driver_id, "status": "already registered"}

        # Insert new driver
        cursor.execute(
            "INSERT INTO drivers (name, email) VALUES (%s, %s) RETURNING id;",
            (driver_info["name"], driver_info["email"])
        )
        result = cursor.fetchone()
        driver_id = result[0] if result else None
        conn.commit()
        cursor.close()
        conn.close()

        if driver_id:
            return {"driver_id": driver_id, "status": "registered"}
        else:
            return {"error": "Failed to register driver."}

    except Exception as e:
        return {"error": str(e)}

# -------------------
# Assign driver to a client
# -------------------
def assign_driver(user_id, pickup, destination):
    """Assign an available driver to a client."""
    conn = create_connection()
    if not conn:
        return {"error": "Database connection failed."}

    try:
        cursor = conn.cursor()

        # Find an available driver (not currently assigned)
        cursor.execute("""
            SELECT id, name FROM drivers
            WHERE id NOT IN (
                SELECT driver_id FROM rides WHERE status = 'assigned'
            )
            LIMIT 1;
        """)
        driver = cursor.fetchone()

        if not driver:
            cursor.close()
            conn.close()
            return {"error": "No available drivers right now."}

        driver_id, driver_name = driver

        # Insert a new ride
        cursor.execute("""
            INSERT INTO rides (user_id, driver_id, pickup, destination, status)
            VALUES (%s, %s, %s, %s, %s) RETURNING ride_id;
        """, (user_id, driver_id, pickup, destination, 'assigned'))
        result = cursor.fetchone()
        ride_id = result[0] if result else None

        conn.commit()
        cursor.close()
        conn.close()

        if ride_id:
            return {
                "ride_id": ride_id,
                "driver_id": driver_id,
                "driver_name": driver_name,
                "user_id": user_id,
                "pickup": pickup,
                "destination": destination,
                "status": "assigned"
            }
        else:
            return {"error": "Failed to assign ride."}

    except Exception as e:
        return {"error": str(e)}

# -------------------
# Main execution
# -------------------
if __name__ == "__main__":
    # Step 1: Register a driver
    driver_data = {"name": "Omkar Sharma", "email": "omkar@example.com"}
    result = register_driver(driver_data)
    print("Driver Registered:", result)

    # Step 2: Assign a ride to a client
    ride = assign_driver(
        user_id=1, 
        pickup="MG Road", 
        destination="Airport"
    )
    print("Ride Assigned:", ride)
