# server_matcher.py
# Auto-match pending ride requests to available drivers
# Run on port 8001

import time
import requests

ORCHESTRATOR = "http://127.0.0.1:8080"

def auto_match():
    print("⚙️  Matcher service started (polling every 5 seconds)...")
    while True:
        try:
            # 1️⃣ Get pending ride requests
            pending = requests.get(f"{ORCHESTRATOR}/pending_requests", timeout=5).json()
            # 2️⃣ Get available drivers
            drivers = requests.get(f"{ORCHESTRATOR}/available_drivers", timeout=5).json()

            if pending and drivers:
                for ride, driver in zip(pending, drivers):
                    print(f"🧩 Assigning Request {ride['request_id']} to Driver {driver['driver_id']}...")
                    res = requests.post(
                        f"{ORCHESTRATOR}/assign",
                        json={"request_id": ride["request_id"], "driver_id": driver["driver_id"]},
                        timeout=5
                    )
                    print("✅ Response:", res.text)
            else:
                print("⏳ Waiting... no pending requests or available drivers.")
        except Exception as e:
            print("❌ Error:", e)
        time.sleep(5)

if __name__ == "__main__":
    auto_match()
