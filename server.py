# server.py
import os
import json
from flask import Flask, request, jsonify, send_from_directory
import psycopg2
from psycopg2.extras import Json
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ---- DB config ----
DBNAME = os.getenv("DB_NAME", "mini_uber")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "omkar13")  # change this!
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))

def get_connection():
    return psycopg2.connect(
        dbname=DBNAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
    )

# ---- uploads for move photos (demo) ----
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


@app.route("/ping")
def ping():
    return {"status": "ok", "server": "mini-uber-orchestrator"}


# =========================
# BASIC USER & DRIVER APIS
# =========================

@app.route("/register_user", methods=["POST"])
def register_user():
    data = request.json or {}
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")

    if not (name and email):
        return jsonify({"error": "name and email required"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE email = %s;", (email,))
    row = cur.fetchone()
    if row:
        user_id = row[0]
    else:
        cur.execute(
            "INSERT INTO users (name, email, phone) VALUES (%s, %s, %s) RETURNING user_id;",
            (name, email, phone),
        )
        user_id = cur.fetchone()[0]
        conn.commit()

    cur.close()
    conn.close()
    return jsonify({"user_id": user_id})


@app.route("/register_driver", methods=["POST"])
def register_driver():
    data = request.json or {}
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    vehicle_number = data.get("vehicle_number")
    is_mover = bool(data.get("is_mover", False))
    vehicle_type = data.get("vehicle_type")  # van/truck/tempo

    if not (name and email and vehicle_number):
        return jsonify({"error": "name, email, vehicle_number required"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT driver_id FROM drivers WHERE email = %s;", (email,))
    row = cur.fetchone()
    if row:
        driver_id = row[0]
    else:
        cur.execute(
            """
            INSERT INTO drivers (name, email, phone, vehicle_number, status, is_mover, vehicle_type)
            VALUES (%s, %s, %s, %s, 'available', %s, %s)
            RETURNING driver_id;
            """,
            (name, email, phone, vehicle_number, is_mover, vehicle_type),
        )
        driver_id = cur.fetchone()[0]
        conn.commit()

    cur.close()
    conn.close()
    return jsonify({"driver_id": driver_id})


# ================
# RIDES (existing)
# ================

@app.route("/request_ride", methods=["POST"])
def request_ride():
    data = request.json or {}
    user_id = data.get("user_id")
    pickup = data.get("pickup")
    destination = data.get("destination")

    if not (user_id and pickup and destination):
        return jsonify({"error": "user_id, pickup, destination required"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO rides (user_id, pickup, destination, status, requested_at)
        VALUES (%s, %s, %s, 'requested', NOW())
        RETURNING ride_id;
        """,
        (user_id, pickup, destination),
    )
    ride_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ride_id": ride_id, "matched": False})


# ============================
# UBER PACKERS & MOVERS APIS
# ============================

@app.route("/quote_move", methods=["POST"])
def quote_move():
    """
    Simple 'AI-style' quote based on:
    - vehicle_type
    - helpers_needed
    - packing_required
    - number of items
    """
    data = request.json or {}
    vehicle_type = data.get("vehicle_type", "van")
    helpers = int(data.get("helpers_needed", 1))
    packing_required = bool(data.get("packing_required", False))

    # count items from inventory or plain list
    items = 0
    inventory = data.get("inventory")
    if isinstance(inventory, list):
        items = sum(i.get("qty", 1) for i in inventory)
    elif data.get("item_list"):
        items = len([x for x in data["item_list"].split(",") if x.strip()])

    base_by_vehicle = {"van": 1000, "truck": 1500, "tempo": 1300}
    base = base_by_vehicle.get(vehicle_type, 1200)
    per_helper = 250
    per_item = 50
    packing_fee = 300 if packing_required else 0

    estimated_cost = base + helpers * per_helper + items * per_item + packing_fee
    breakdown = {
        "base": base,
        "helpers": helpers * per_helper,
        "items": items * per_item,
        "packing": packing_fee,
    }

    return jsonify(
        {
            "estimated_cost": float(estimated_cost),
            "quote_breakdown": breakdown,
            "recommended_package": "premium" if packing_required else "basic",
        }
    )


@app.route("/request_move", methods=["POST"])
def request_move():
    print("\n================= /request_move CALLED =================")
    data = request.get_json()
    print("Incoming JSON:", data)

    try:
        user_id = data.get("user_id")
        pickup = data.get("pickup_address")
        drop = data.get("drop_address")
        items = data.get("item_list")
        vehicle_type = data.get("vehicle_type")
        helpers = data.get("helpers_needed")
        packing = data.get("packing_required")
        insurance = data.get("insurance_opted")
        package_type = data.get("package_type")
        photos = data.get("photos", [])
        estimated_cost = data.get("estimated_cost")

        # FULL DEBUG PRINT
        print("Parsed values:")
        print({
            "user_id": user_id,
            "pickup": pickup,
            "drop": drop,
            "items": items,
            "vehicle_type": vehicle_type,
            "helpers": helpers,
            "packing": packing,
            "insurance": insurance,
            "package_type": package_type,
            "photos": photos,
            "estimated_cost": estimated_cost
        })

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO moves (
                user_id, pickup_address, drop_address, item_list,
                vehicle_type, helpers_needed, packing_required,
                insurance_opted, package_type, photos,
                estimated_cost, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'requested')
            RETURNING move_id;
        """, (
            user_id,
            pickup,
            drop,
            items,
            vehicle_type,
            helpers,
            packing,
            insurance,
            package_type,
            json.dumps(photos),     # MUST be JSON
            estimated_cost
        ))

        move_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        print("✔ MOVE INSERTED SUCCESSFULLY → ID:", move_id)
        return jsonify({"move_id": move_id, "status": "requested"})

    except Exception as e:
        print("❌ ERROR in /request_move:", e)
        return jsonify({"error": str(e)}), 500



@app.route("/pending_moves", methods=["GET"])
def pending_moves():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT move_id, user_id, pickup_address, drop_address, item_list, estimated_cost
        FROM moves
        WHERE status = 'requested';
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    data = []
    for r in rows:
        data.append(
            {
                "move_id": r[0],
                "user_id": r[1],
                "pickup": r[2],
                "drop": r[3],
                "items": r[4],
                "estimated_cost": float(r[5]) if r[5] is not None else None,
            }
        )
    return jsonify(data)


@app.route("/assign_move", methods=["POST"])
def assign_move():
    data = request.json or {}
    move_id = data.get("move_id")
    driver_id = data.get("driver_id")
    if not (move_id and driver_id):
        return jsonify({"error": "move_id and driver_id required"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE moves
        SET driver_id = %s, status = 'assigned'
        WHERE move_id = %s AND status = 'requested'
        RETURNING move_id;
        """,
        (driver_id, move_id),
    )
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE drivers SET status = 'busy' WHERE driver_id = %s;", (driver_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"assigned": True})
    else:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify(
            {"assigned": False, "reason": "move not available or already assigned"}), 409


@app.route("/start_move", methods=["POST"])
def start_move():
    data = request.json or {}
    move_id = data.get("move_id")
    if not move_id:
        return jsonify({"error": "move_id required"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE moves SET status = 'ongoing' WHERE move_id = %s AND status = 'assigned' RETURNING move_id;",
        (move_id,),
    )
    row = cur.fetchone()
    if row:
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"started": True})
    else:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"started": False, "reason": "move not assigned"}), 409


@app.route("/complete_move", methods=["POST"])
def complete_move():
    data = request.json or {}
    move_id = data.get("move_id")
    if not move_id:
        return jsonify({"error": "move_id required"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT driver_id FROM moves WHERE move_id = %s;", (move_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return jsonify({"error": "move not found"}), 404

    driver_id = row[0]
    cur.execute(
        """
        UPDATE moves
        SET status = 'completed', completed_at = NOW()
        WHERE move_id = %s AND status IN ('assigned','ongoing')
        RETURNING move_id;
        """,
        (move_id,),
    )
    updated = cur.fetchone()
    if updated:
        if driver_id:
            cur.execute(
                "UPDATE drivers SET status = 'available' WHERE driver_id = %s;",
                (driver_id,),
            )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"completed": True})
    else:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"completed": False, "reason": "move not ongoing"}), 409


@app.route("/move_status/<int:move_id>")
def move_status(move_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT move_id, user_id, driver_id, pickup_address, drop_address,
               item_list, vehicle_type, helpers_needed, packing_required,
               package_type, photos, inventory, quote_breakdown,
               estimated_cost, status, requested_at, completed_at
        FROM moves
        WHERE move_id = %s;
        """,
        (move_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "move not found"}), 404

    keys = [
        "move_id", "user_id", "driver_id", "pickup_address", "drop_address",
        "item_list", "vehicle_type", "helpers_needed", "packing_required",
        "package_type", "photos", "inventory", "quote_breakdown",
        "estimated_cost", "status", "requested_at", "completed_at",
    ]
    result = dict(zip(keys, row))
    for k in ("photos", "inventory", "quote_breakdown"):
        if isinstance(result.get(k), str):
            try:
                result[k] = json.loads(result[k])
            except Exception:
                pass
    if isinstance(result.get("estimated_cost"), (int, float)):
        result["estimated_cost"] = float(result["estimated_cost"])
    return jsonify(result)


@app.route("/upload_move_photo", methods=["POST"])
def upload_move_photo():
    if "file" not in request.files:
        return jsonify({"error": "no file provided"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "empty filename"}), 400
    if not allowed_file(f.filename):
        return jsonify({"error": "invalid file type"}), 400
    filename = secure_filename(f.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)
    f.save(save_path)
    return jsonify({"url": f"/uploads/{filename}"})


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/move_feedback", methods=["POST"])
def move_feedback():
    data = request.json or {}
    move_id = data.get("move_id")
    rating = int(data.get("rating", 0))
    tags = data.get("tags")
    comment = data.get("comment")

    if not move_id or rating < 1 or rating > 5:
        return jsonify({"error": "move_id and rating (1–5) required"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO move_feedback (move_id, rating, tags, comment) VALUES (%s, %s, %s, %s);",
        (move_id, rating, tags, comment),
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"saved": True})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=8000, debug=True)

