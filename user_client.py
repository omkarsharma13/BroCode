import psycopg2
from psycopg2.extras import RealDictCursor

# --------------------
# Database connection
# --------------------
def get_connection():
    return psycopg2.connect(
        dbname="mini_uber",
        user="postgres",
        password="omkar13",  # change if needed
        host="localhost",
        port="5432"
    )

# --------------------
# User registration
# --------------------
def register_user(conn, name, email, phone):
    with conn.cursor() as cur:
        # Check if user already exists
        cur.execute("SELECT user_id FROM users WHERE email = %s;", (email,))
        result = cur.fetchone()
        if result:
            print(f"✅ User already registered with id {result[0]}")
            return result[0]

        # Otherwise register new user
        cur.execute(
            "INSERT INTO users (name, email, phone) VALUES (%s, %s, %s) RETURNING user_id;",
            (name, email, phone)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ New user registered with id {user_id}")
        return user_id

# --------------------
# Request ride
# --------------------
def request_ride(conn, user_id, pickup, destination):
    with conn.cursor() as cur:
        # Insert into ride_requests (not rides)
        cur.execute(
            """
            INSERT INTO ride_requests (user_id, pickup_location, dropoff_location, status)
            VALUES (%s, %s, %s, 'pending')
            RETURNING request_id;
            """,
            (user_id, pickup, destination)
        )
        request_id = cur.fetchone()[0]
        conn.commit()
        print(f"🚕 Ride request created successfully with request_id {request_id}")
        print("⏳ Waiting for a driver to accept your ride...")

# --------------------
# Check ride status
# --------------------
def check_ride_status(conn, user_id):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT rr.request_id, rr.status, r.driver_id, d.name AS driver_name
            FROM ride_requests rr
            LEFT JOIN rides r ON rr.request_id = r.request_id
            LEFT JOIN drivers d ON r.driver_id = d.driver_id
            WHERE rr.user_id = %s
            ORDER BY rr.request_time DESC LIMIT 1;
            """,
            (user_id,)
        )
        result = cur.fetchone()
        if result:
            print("\n🚗 Latest Ride Status:")
            print(f"Request ID: {result['request_id']}")
            print(f"Status: {result['status']}")
            if result["driver_name"]:
                print(f"Driver: {result['driver_name']} (ID: {result['driver_id']})")
        else:
            print("❌ No rides found for this user.")

# --------------------
# Main function
# --------------------
def main():
    print("🚗 Welcome to Mini Uber - User Client")

    name = input("Enter your name: ")
    email = input("Enter your email: ")
    phone = input("Enter your phone number: ")

    conn = get_connection()
    user_id = register_user(conn, name, email, phone)

    while True:
        print("\n--- User Menu ---")
        print("1. Request a ride")
        print("2. Check latest ride status")
        print("3. Exit")
        choice = input("Enter choice: ")

        if choice == "1":
            pickup = input("Enter pickup location: ")
            destination = input("Enter destination: ")
            request_ride(conn, user_id, pickup, destination)
        elif choice == "2":
            check_ride_status(conn, user_id)
        elif choice == "3":
            print("👋 Thank you for using Mini Uber!")
            break
        else:
            print("❌ Invalid choice. Try again.")

    conn.close()

if __name__ == "__main__":
    main()
