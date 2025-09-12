import requests

BASE_URL = "http://127.0.0.1:8000"

def register_driver(name, phone):
    response = requests.post(
        f"{BASE_URL}/register_driver",
        params={"name": name, "phone": phone}
    )
    return response.json()

def accept_ride(ride_id, driver_id):
    response = requests.post(
        f"{BASE_URL}/accept_ride/{ride_id}",
        params={"driver_id": driver_id}
    )
    return response.json()

def complete_ride(ride_id, driver_id):
    response = requests.post(
        f"{BASE_URL}/complete_ride/{ride_id}",
        params={"driver_id": driver_id}
    )
    return response.json()

def driver_rides(driver_id):
    response = requests.get(f"{BASE_URL}/driver_rides/{driver_id}")
    return response.json()


# Example usage
if __name__ == "__main__":
    # Register a driver
    driver = register_driver("Ravi", "8887776666")
    print("Driver Registered:", driver)

    # Example: Accept a ride (replace ride_id=1 with actual ride_id from bookings)
    # accepted = accept_ride(1, driver["driver_id"])
    # print("Accepted Ride:", accepted)

    # Example: View driver rides
    rides = driver_rides(driver["driver_id"])
    print("Driver Rides:", rides)
