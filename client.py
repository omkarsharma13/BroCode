import requests

BASE_URL = "http://127.0.0.1:8000"

def register_driver(name, phone):
    response = requests.post(
        f"{BASE_URL}/register_driver",
        params={"name": name, "phone": phone}
    )
    return response.json()

def book_ride(user_id, pickup, drop):
    response = requests.post(
        f"{BASE_URL}/book_ride",
        params={"user_id": user_id, "pickup": pickup, "drop": drop}
    )
    return response.json()

def ride_status(ride_id):
    response = requests.get(f"{BASE_URL}/ride_status/{ride_id}")
    return response.json()

def driver_rides(driver_id):
    response = requests.get(f"{BASE_URL}/driver_rides/{driver_id}")
    return response.json()

# -------------------
# MAIN EXECUTION FLOW
# -------------------
if __name__ == "__main__":
    driver_response = register_driver("Ravi", "8887776666")
    print("Driver Registered:", driver_response)

    if "driver" in driver_response:
        driver_id = driver_response["driver"]["id"]

        # Step 2: Book a ride for user_id = 1
        ride_response = book_ride(1, "Delhi", "Gurgaon")
        print("Ride Booked:", ride_response)

        if "ride" in ride_response:
            ride_id = ride_response["ride"]["id"]

            # Step 3: Check ride status
            status = ride_status(ride_id)
            print("Ride Status:", status)

            # Step 4: Get rides assigned to driver
            rides = driver_rides(driver_id)
            print("Driver Rides:", rides)

    else:
        print("❌ Could not register driver. Error:", driver_response)
