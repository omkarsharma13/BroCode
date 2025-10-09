import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname="mini_uber",
        user="omkar",             # ✅ change from "postgres" to "omkar"
        password="yourpassword",  # 🔑 replace with omkar's password
        host="localhost",
        port="5433"
    )


def register_driver(conn, name, email, phone, vehicle_number):
    cur = conn.cursor()
    cur.execute("SELECT driver_id FROM drivers WHERE email = %s;", (email,))
    existing = cur.fetchone()
    if existing:
        driver_id = existing[0]
        print(f"✅ Driver already registered with id {driver_id}")
    else:
        cur.execute(
            "INSERT INTO drivers (name, email, phone, vehicle_number) VALUES (%s, %s, %s, %s) RETURNING driver_id;",
            (name, email, phone, vehicle_number)
        )
        driver_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ New driver registered with id {driver_id}")
    cur.close()
    return driver_id

def view_requested_rides(conn):
    cur = conn.cursor()
    cur.execute("SELECT ride_id, user_id, pickup, destination FROM rides WHERE status = 'requested';")
    rides = cur.fetchall()
    cur.close()
    return rides

def accept_ride(conn, driver_id, ride_id):
    cur = conn.cursor()
    cur.execute(
        "UPDATE rides SET driver_id = %s, status = 'ongoing' WHERE ride_id = %s AND status = 'requested' RETURNING ride_id;",
        (driver_id, ride_id)
    )
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    if updated:
        print(f"🚖 Driver {driver_id} accepted ride {ride_id}")
    else:
        print(f"⚠️ Ride {ride_id} is no longer available")

def complete_ride(conn, ride_id):
    cur = conn.cursor()
    cur.execute(
        "UPDATE rides SET status = 'completed', completed_at = NOW() WHERE ride_id = %s AND status = 'ongoing' RETURNING ride_id;",
        (ride_id,)
    )
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    if updated:
        print(f"🏁 Ride {ride_id} marked as completed")
    else:
        print(f"⚠️ Ride {ride_id} was not ongoing")

def main():
    conn = get_connection()

    print("🚗 Welcome to Mini Uber - Driver Client")
    name = input("Enter your name: ")
    email = input("Enter your email: ")
    phone = input("Enter your phone number: ")
    vehicle_number = input("Enter your vehicle number: ")

    driver_id = register_driver(conn, name, email, phone, vehicle_number)

    while True:
        print("\n--- Driver Menu ---")
        print("1. View requested rides")
        print("2. Accept a ride")
        print("3. Complete a ride")
        print("4. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            rides = view_requested_rides(conn)
            if rides:
                print("\nRequested Rides:")
                for r in rides:
                    print(f"Ride {r[0]} | User {r[1]} | {r[2]} → {r[3]}")
            else:
                print("No requested rides at the moment.")

        elif choice == "2":
            ride_id = int(input("Enter Ride ID to accept: "))
            accept_ride(conn, driver_id, ride_id)

        elif choice == "3":
            ride_id = int(input("Enter Ride ID to complete: "))
            complete_ride(conn, ride_id)

        elif choice == "4":
            break
        else:
            print("Invalid choice. Try again.")

    conn.close()

if __name__ == "__main__":
    main()
