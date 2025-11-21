# user_client.py
import argparse
import os
import time
import requests

def ping_server(server):
    try:
        r = requests.get(f"{server}/ping", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

def register_user(server):
    print("👤 Register User")
    name = input("Name: ")
    email = input("Email: ")
    phone = input("Phone: ")
    r = requests.post(f"{server}/register_user", json={
        "name": name, "email": email, "phone": phone
    })
    r.raise_for_status()
    uid = r.json()["user_id"]
    print(f"✅ Registered user_id = {uid}")
    return uid

def upload_photo(server, path):
    if not os.path.exists(path):
        print("❌ File not found:", path)
        return None
    with open(path, "rb") as f:
        r = requests.post(f"{server}/upload_move_photo", files={"file": f})
    if r.status_code == 200:
        url = r.json().get("url")
        print("📸 Uploaded photo ->", url)
        return url
    print("❌ Upload failed:", r.text)
    return None

def request_move_flow(server, user_id):
    print("\n🚛 Uber Packers & Movers – Create a Move\n")
    pickup = input("Pickup address: ")
    drop = input("Drop address: ")
    items = input("Items (comma separated, e.g., sofa,bed,fridge): ")
    vehicle_type = input("Vehicle type [van/truck/tempo] (default van): ") or "van"
    helpers = int(input("Helpers needed [1]: ") or "1")
    packing = input("Packing required? (y/n) [n]: ").lower() == "y"
    insurance = input("Add insurance? (y/n) [n]: ").lower() == "y"

    # inventory list for better quote
    inventory = [
        {"name": it.strip(), "qty": 1}
        for it in items.split(",") if it.strip()
    ] or None

    photos = []
    if input("Add photos for better estimate? (y/n) [n]: ").lower() == "y":
        while True:
            path = input(" -> Photo path (Enter to stop): ").strip()
            if not path:
                break
            url = upload_photo(server, path)
            if url:
                photos.append(url)

    # get a quote first
    q = requests.post(f"{server}/quote_move", json={
        "vehicle_type": vehicle_type,
        "helpers_needed": helpers,
        "packing_required": packing,
        "inventory": inventory,
        "item_list": items,
    })
    q.raise_for_status()
    qd = q.json()
    print("\n💰 Estimated Cost:", qd.get("estimated_cost"))
    print("   Breakdown:", qd.get("quote_breakdown"))
    print("   Suggested package:", qd.get("recommended_package"))
    if input("Confirm booking? (y/n): ").lower() != "y":
        print("❌ Move cancelled.")
        return

    r = requests.post(f"{server}/request_move", json={
        "user_id": user_id,
        "pickup_address": pickup,
        "drop_address": drop,
        "item_list": items,
        "vehicle_type": vehicle_type,
        "helpers_needed": helpers,
        "packing_required": packing,
        "insurance_opted": insurance,
        "package_type": qd.get("recommended_package"),
        "photos": photos,
        "inventory": inventory,
        "quote_breakdown": qd.get("quote_breakdown"),
        "estimated_cost": qd.get("estimated_cost"),
    })
    r.raise_for_status()
    info = r.json()
    move_id = info["move_id"]
    print(f"\n✅ Move created with ID: {move_id}")
    if info.get("matched"):
        print(f"🎉 Mover assigned immediately (driver_id = {info.get('driver_id')})")
    else:
        print("⌛ No mover yet, we’ll watch the status...")

    # Poll status a bit
    for i in range(20):
        time.sleep(3)
        st = requests.get(f"{server}/move_status/{move_id}")
        if st.status_code != 200:
            break
        s = st.json()
        status = s.get("status")
        icon = {
            "requested": "📥",
            "assigned": "👷",
            "ongoing": "📦",
            "completed": "✅",
        }.get(status, "❓")
        print(f"{icon} Move status: {status}")
        if status in ("assigned", "ongoing", "completed"):
            if status == "completed":
                print("🔚 Move finished!")
            break
    return move_id

def show_move(server):
    mid = input("Enter move_id: ").strip()
    if not mid:
        return
    r = requests.get(f"{server}/move_status/{mid}")
    print("ℹ️ Move info:", r.status_code, r.text)

def give_feedback(server):
    mid = input("Enter move_id to rate: ").strip()
    if not mid:
        return
    rating = int(input("Rating (1–5): ") or "5")
    tags = input("Tags (comma separated, e.g., punctual,careful): ")
    comment = input("Comment: ")
    r = requests.post(f"{server}/move_feedback", json={
        "move_id": int(mid),
        "rating": rating,
        "tags": tags,
        "comment": comment,
    })
    print("📣 Feedback response:", r.status_code, r.text)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="http://localhost:8000")
    args = parser.parse_args()
    server = args.server

    if not ping_server(server):
        print("❌ Cannot reach server at", server)
        return

    user_id = None
    while True:
        print("\n=== User Menu ===")
        print("1) Register user")
        print("2) Request Uber Movers job")
        print("3) View move status")
        print("4) Rate a move")
        print("5) Exit")
        choice = input("Choice: ").strip()

        if choice == "1":
            user_id = register_user(server)
        elif choice == "2":
            if not user_id:
                existing = input("Already have user_id? Enter or press Enter to register: ")
                if existing:
                    user_id = int(existing)
                else:
                    user_id = register_user(server)
            request_move_flow(server, user_id)
        elif choice == "3":
            show_move(server)
        elif choice == "4":
            give_feedback(server)
        elif choice == "5":
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
