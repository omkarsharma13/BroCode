import psycopg2
from psycopg2.extras import RealDictCursor

# --------------------
# Database connection
# --------------------
def get_connection():
    return psycopg2.connect(
        dbname="mini_uber",
        user="postgres",
        password="omkar13",  # update if needed
        host="localhost",
        port="5432"
    )

# --------------------
# Register Driver
# --------------------
def register_driver(conn, name, email, phone, vehicle_number):
    with conn.cursor() as cur:
        cur.execute("SELECT driver_id FROM drivers WHERE email = %s;", (email,))
        existing = cur.fetchone()
        if existing:
            print(f"✅ Driver already registered with id {existing[0]}")
            return existing[0]

        cur.execute(
            """
            INSERT INTO drivers (name, email, phone, vehicle_number)
            VALUES (%s, %s, %s, %s) RETURNING driver_id;
            """,
            (name, email, phone, vehicle_number)
        )
        driver_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ New driver registered with id {driver_id}")
        return driver_id

# --------------------
# View requested rides
# --------------------
def view_requested_rides(conn):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT rr.request_id, u.name AS user_name, rr.pickup_location, rr.dropoff_location, rr.status
            FROM ride_requests rr
            JOIN users u ON rr.user_id = u.user_id
            WHERE rr.status = 'pending'
            ORDER BY rr.request_time;
        """)
        rides = cur.fetchall()
        if not rides:
            print("No requested rides at the moment.")
            return []
        print("\n🚕 Pending Ride Requests:")
        for r in rides:
            print(f"[{r['request_id']}] {r['user_name']} - {r['pickup_location']} ➡ {r['dropoff_location']} (Status: {r['status']})")
        return rides

# --------------------
# Accept a ride
# --------------------
def accept_ride(conn, driver_id, request_id):
    with conn.cursor() as cur:
        # Update request status
        cur.execute("UPDATE ride_requests SET status = 'accepted' WHERE request_id = %s;", (request_id,))
        # Create a new ride entry
        cur.execute(
            """
            INSERT INTO rides (request_id, driver_id, user_id, pickup, destination, status)
            SELECT request_id, %s, user_id, pickup_location, dropoff_location, 'ongoing'
            FROM ride_requests WHERE request_id = %s
            RETURNING ride_id;
            """,
            (driver_id, request_id)
        )
        ride_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ Ride accepted successfully! Ride ID: {ride_id}")

# --------------------
# Complete a ride
# --------------------
def complete_ride(conn, driver_id, ride_id):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE rides SET status = 'completed', end_time = NOW() WHERE ride_id = %s AND driver_id = %s;",
            (ride_id, driver_id)
        )
        conn.commit()
        print(f"✅ Ride {ride_id} marked as completed!")

# --------------------
# Main Menu
# --------------------
def main():
    print("🚗 Welcome to Mini Uber - Driver Client")

    name = input("Enter your name: ")
    email = input("Enter your email: ")
    phone = input("Enter your phone number: ")
    vehicle_number = input("Enter your vehicle number: ")

    conn = get_connection()
    driver_id = register_driver(conn, name, email, phone, vehicle_number)

    while True:
        print("\n--- Driver Menu ---")
        print("1. View requested rides")
        print("2. Accept a ride")
        print("3. Complete a ride")
        print("4. Exit")
        choice = input("Enter choice: ")

        if choice == "1":
            view_requested_rides(conn)
        elif choice == "2":
            request_id = input("Enter Request ID to accept: ")
            accept_ride(conn, driver_id, request_id)
        elif choice == "3":
            ride_id = input("Enter Ride ID to complete: ")
            complete_ride(conn, driver_id, ride_id)
        elif choice == "4":
            print("👋 Exiting driver app.")
            break
        else:
            print("❌ Invalid choice. Try again.")

    conn.close()

if __name__ == "__main__":
    main()
