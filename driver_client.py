# driver_client.py
import argparse
import requests

def ping(server):
    try:
        r = requests.get(f"{server}/ping", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

def register_driver(server):
    print("🚗 Register Driver / Mover")
    name = input("Name: ")
    email = input("Email: ")
    phone = input("Phone: ")
    vehicle_number = input("Vehicle number: ")
    is_mover = input("Is this driver a Movers partner? (y/n) [n]: ").lower() == "y"
    vehicle_type = None
    if is_mover:
        vehicle_type = input("Vehicle type (van/truck/tempo) [van]: ") or "van"

    r = requests.post(f"{server}/register_driver", json={
        "name": name,
        "email": email,
        "phone": phone,
        "vehicle_number": vehicle_number,
        "is_mover": is_mover,
        "vehicle_type": vehicle_type,
    })
    r.raise_for_status()
    did = r.json()["driver_id"]
    print(f"✅ Registered driver_id = {did}")
    if is_mover:
        print("🎒 This driver can now receive Movers jobs!")
    return did

def view_pending_moves(server):
    r = requests.get(f"{server}/pending_moves")
    r.raise_for_status()
    moves = r.json()
    if not moves:
        print("😴 No pending moves right now.")
        return
    print("\n📋 Pending Moves:")
    for m in moves:
        print(
            f"  #{m['move_id']} | User {m['user_id']} | "
            f"{m['pickup']} → {m['drop']} | Est ₹{m.get('estimated_cost')}"
        )

def accept_move(server, driver_id):
    mid = input("Enter move_id to accept: ").strip()
    if not mid:
        return
    r = requests.post(f"{server}/assign_move", json={
        "move_id": int(mid),
        "driver_id": driver_id,
    })
    print("📦 Accept response:", r.status_code, r.text)

def start_move(server):
    mid = input("Enter move_id to mark as STARTED: ").strip()
    if not mid:
        return
    r = requests.post(f"{server}/start_move", json={"move_id": int(mid)})
    print("▶️  Start response:", r.status_code, r.text)

def complete_move(server):
    mid = input("Enter move_id to COMPLETE: ").strip()
    if not mid:
        return
    r = requests.post(f"{server}/complete_move", json={"move_id": int(mid)})
    print("✅ Complete response:", r.status_code, r.text)

def view_move(server):
    mid = input("Enter move_id to view: ").strip()
    if not mid:
        return
    r = requests.get(f"{server}/move_status/{mid}")
    print("ℹ️ Move info:", r.status_code, r.text)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="http://localhost:8000")
    args = parser.parse_args()
    server = args.server

    if not ping(server):
        print("❌ Cannot reach server at", server)
        return

    driver_id = register_driver(server)

    while True:
        print("\n=== Driver Menu ===")
        print("1) View pending moves")
        print("2) Accept move")
        print("3) Start move")
        print("4) Complete move")
        print("5) View move details")
        print("6) Exit")
        c = input("Choice: ").strip()

        if c == "1":
            view_pending_moves(server)
        elif c == "2":
            accept_move(server, driver_id)
        elif c == "3":
            start_move(server)
        elif c == "4":
            complete_move(server)
        elif c == "5":
            view_move(server)
        elif c == "6":
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
