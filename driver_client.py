from server import register_driver, driver_rides

if __name__ == "__main__":
    print("🚗 Welcome to Mini Uber - Driver Client")
    name = input("Enter your name: ")
    email = input("Enter your email: ")

    driver = register_driver(name, email)
    print("✅ Driver Registered:", driver)

    if driver.get("driver_id"):
        rides = driver_rides(driver["driver_id"])
        print("📋 Your Rides:", rides)
