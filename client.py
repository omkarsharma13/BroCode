import requests

BASE_URL = "http://127.0.0.1:8000"


def book_ride(user_id, pickup, destination):
    data = {"user_id": user_id, "pickup": pickup, "destination": destination}
    response = requests.post(f"{BASE_URL}/book_ride", json=data)
    return response.json()

def get_ride_status(ride_id):
    response = requests.get(f"{BASE_URL}/ride_status/{ride_id}")
    return response.json()

if __name__ == "__main__":
    booking_response = book_ride(1, "Bull Temple Road", "MG Road")
    print("Booking Response:", booking_response)

    ride_id = booking_response.get("ride_id")

    if ride_id:
        status_response = get_ride_status(ride_id)
        print("Ride Status:", status_response)
