import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname="mini_uber",
        user="omkar",              # ✅ use the existing role
        password="yourpassword",   # 🔑 replace with omkar's password
        host="localhost",
        port="5433"
    )

def register_user(conn, name, email, phone):
    cur = conn.cursor()
    # Check if user already exists
    cur.execute("SELECT user_id FROM users WHERE email = %s;", (email,))
    existing = cur.fetchone()
    if existing:
        user_id = existing[0]
        print(f"✅ User already registered with id {user_id}")
    else:
        # Register new user
        cur.execute(
            "INSERT INTO users (name, email, phone) VALUES (%s, %s, %s) RETURNING user_id;",
            (name, email, phone)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ New user registered with id {user_id}")
    cur.close()
    return user_id

def request_ride(conn, user_id, pickup, destination):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO rides (user_id, pickup, destination) VALUES (%s, %s, %s) RETURNING ride_id;",
        (user_id, pickup, destination)
    )
    ride_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    print(f"🚖 Ride requested with id {ride_id}")
    return ride_id


def main():
    conn = get_connection()

    print("🚗 Welcome to Mini Uber - User Client")
    name = input("Enter your name: ")
    email = input("Enter your email: ")
    phone = input("Enter your phone number: ")

    # Register or fetch existing user
    user_id = register_user(conn, name, email, phone)

    pickup = input("Enter pickup location: ")
    destination = input("Enter destination: ")

    # Request ride
    request_ride(conn, user_id, pickup, destination)

    conn.close()

if __name__ == "__main__":
    main()
