from flask import Blueprint, request, jsonify
from app.extensions import mongo
from functools import wraps
from bson import ObjectId
from datetime import datetime, timedelta

from app.services.auth_service import verify_token, generate_token
from werkzeug.security import check_password_hash
from flask import render_template

import secrets

admin_bp = Blueprint("admin", __name__)

# # ================= ROLE DECORATOR =================
# def role_required(roles):
#     def decorator(f):
#         @wraps(f)
#         def wrapper(*args, **kwargs):
#             token = request.headers.get("Authorization")
#             payload = verify_token(token)
#             if not payload or payload["role"] not in roles:
#                 return jsonify({"message": "Unauthorized"}), 403
#             return f(*args, **kwargs)
#         return wrapper
#     return decorator
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):

            # 🔥 TEMP AUTH BYPASS (DEV MODE)
            return f(*args, **kwargs)

            # ===== RE-ENABLE LATER =====
            # token = request.headers.get("Authorization")
            # payload = verify_token(token)
            # if not payload or payload["role"] not in roles:
            #     return jsonify({"message": "Unauthorized"}), 403
            # return f(*args, **kwargs)

        return wrapper
    return decorator


# ================= LOGIN =================
@admin_bp.route("/login", methods=["POST"])
def admin_login():
    data = request.json
    admin = mongo.db.admins.find_one({"username": data["username"]})

    if not admin or not check_password_hash(admin["password_hash"], data["password"]):
        return jsonify({"message": "Invalid credentials"}), 401

    token = generate_token(admin)
    return jsonify({"token": token, "role": admin["role"]})


# ================= VEHICLE =================
@admin_bp.route("/add-vehicle", methods=["POST"])
@role_required(["ADMIN", "SUPER_ADMIN"])
def add_vehicle():
    mongo.db.vehicles.insert_one(request.json) 
    return jsonify({"message": "Vehicle added successfully"})


@admin_bp.route("/search-vehicle", methods=["POST"])
@role_required(["ADMIN", "SUPER_ADMIN", "OFFICER"])
def search_vehicle():
    value = request.json.get("value")
    vehicle = mongo.db.vehicles.find_one(
        {"$or": [{"vehicle_no": value}, {"rfid_tag": value}]}
    )
    if vehicle:
        vehicle["_id"] = str(vehicle["_id"])
    if not vehicle:
        return jsonify({"message": "Vehicle not found"}), 404
    return jsonify(vehicle)


@admin_bp.route("/update-vehicle/<id>", methods=["PUT"])
@role_required(["ADMIN", "SUPER_ADMIN"])
def update_vehicle(id):
    mongo.db.vehicles.update_one(
        {"_id": ObjectId(id)},
        {"$set": request.json}
    )
    return jsonify({"message": "Vehicle updated"})


@admin_bp.route("/delete-vehicle/<id>", methods=["DELETE"])
@role_required(["SUPER_ADMIN"])
def delete_vehicle(id):
    mongo.db.vehicles.delete_one({"_id": ObjectId(id)})
    return jsonify({"message": "Vehicle deleted"})


# ================= STATS =================
@admin_bp.route("/stats", methods=["GET"])
@role_required(["ADMIN", "SUPER_ADMIN"])
def stats():
    return jsonify({
        "total_vehicles": mongo.db.vehicles.count_documents({}),
        "total_fines": mongo.db.fines.count_documents({}),
        "unpaid_fines": mongo.db.fines.count_documents({"status": "UNPAID"})
    })


# ================= FINES =================
@admin_bp.route("/fines", methods=["GET"])
@role_required(["ADMIN", "SUPER_ADMIN", "OFFICER"])
def view_fines():
    fines = list(mongo.db.fines.find({}, {"_id": 0}))
    return jsonify(fines)


# ================= REPORTS =================
@admin_bp.route("/reports", methods=["GET"])
@role_required(["ADMIN", "SUPER_ADMIN"])
def monthly_report():
    pipeline = [
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$issued_at"},
                    "month": {"$month": "$issued_at"}
                },
                "total_fines": {"$sum": 1},
                "total_amount": {"$sum": "$amount"}
            }
        }
    ]
    return jsonify(list(mongo.db.fines.aggregate(pipeline)))


@admin_bp.route("/reports/date", methods=["POST"])
@role_required(["ADMIN", "SUPER_ADMIN"])
def date_report():
    date = datetime.fromisoformat(request.json["date"])
    fines = list(mongo.db.fines.find({
        "issued_at": {
            "$gte": date,
            "$lt": date + timedelta(days=1)
        }
    }, {"_id": 0}))
    return jsonify(fines)


from datetime import datetime
@admin_bp.route("/check-expiry", methods=["POST"])
# @role_required(["ADMIN", "SUPER_ADMIN", "OFFICER"])  # optional for dev
def check_expiry():
    value = request.json.get("rfid")
    if not value:
        return jsonify({"message": "RFID is required"}), 400

    vehicle = mongo.db.vehicles.find_one(
        {"rfid_tag": value},
        {"_id": 0}
    )

    if not vehicle:
        return jsonify({"message": "Vehicle not found"}), 404

    now = datetime.now()
    insurance_expired = False
    puc_expired = False

    try:
        insurance_expiry = datetime.fromisoformat(vehicle["insurance_expiry"])
        insurance_expired = insurance_expiry < now
    except Exception:
        insurance_expired = None  # invalid format

    try:
        puc_expiry = datetime.fromisoformat(vehicle["puc_expiry"])
        puc_expired = puc_expiry < now
    except Exception:
        puc_expired = None

    response = {
        "vehicle_no": vehicle.get("vehicle_no"),
        "model_no": vehicle.get("model_no"),  # <-- added
        "owner_name": vehicle.get("owner_name"),
        "rfid_tag": vehicle.get("rfid_tag"),
        "insurance_expiry": vehicle.get("insurance_expiry"),
        "puc_expiry": vehicle.get("puc_expiry"),
        "insurance_expired": insurance_expired,
        "puc_expired": puc_expired,
        "mobile_number": vehicle.get("mobile_number")
    }

    return jsonify(response)

from datetime import datetime

import secrets
from datetime import datetime

# Twilio placeholder
def send_sms_via_twilio(mobile_number, message):
    print(f"[Twilio Placeholder] Sending SMS to {mobile_number}: {message}")
    # Later: integrate Twilio API here


# Serve fine payment page
@admin_bp.route("/user/fine", methods=["GET"])
def fine_page():
    # Optional: pass token as query param
    token = request.args.get("token")
    return render_template("fine.html", token=token)


@admin_bp.route("/impose-fine", methods=["POST"])
def impose_fine():
    data = request.json
    rfid = data.get("rfid")

    if not rfid:
        return jsonify({"message": "RFID is required"}), 400

    vehicle = mongo.db.vehicles.find_one({"rfid_tag": rfid})
    if not vehicle:
        return jsonify({"message": "Vehicle not found"}), 404

    now = datetime.now()

    # Token handling
    access_token = vehicle.get("access_token")
    if not access_token:
        access_token = secrets.token_urlsafe(16)
        mongo.db.vehicles.update_one(
            {"_id": vehicle["_id"]},
            {"$set": {"access_token": access_token}}
        )

    # Violations
    violations = []
    total_amount = 0

    # Insurance
    try:
        ins_expiry = datetime.fromisoformat(vehicle["insurance_expiry"])
        if ins_expiry < now:
            violations.append({
                "type": "Insurance Expired",
                "expired_on": vehicle["insurance_expiry"],
                "fine": 1000
            })
            total_amount += 1000
    except:
        pass

    # PUC
    try:
        puc_expiry = datetime.fromisoformat(vehicle["puc_expiry"])
        if puc_expiry < now:
            violations.append({
                "type": "PUC Expired",
                "expired_on": vehicle["puc_expiry"],
                "fine": 500
            })
            total_amount += 500
    except:
        pass

    # Default violation
    if not violations:
        violations.append({
            "type": "Traffic Rule Violation",
            "expired_on": None,
            "fine": 500
        })
        total_amount = 500

    fine_doc = {
        "vehicle_no": vehicle["vehicle_no"],
        "rfid_tag": rfid,
        "owner_name": vehicle["owner_name"],
        "mobile_number": vehicle.get("mobile_number"),
        "status": "UNPAID",
        "issued_at": now,
        "token": access_token,
        "violations": violations,
        "total_amount": total_amount
    }

    mongo.db.fines.insert_one(fine_doc)

    # ✅ Updated: Serve page via Flask route
    user_link = f"{request.host_url}api/admin/user/fine?token={access_token}"
    # request.host_url dynamically uses your Flask host (e.g., http://10.192.26.193:5000/)

    if vehicle.get("mobile_number"):
        send_sms_via_twilio(
            vehicle["mobile_number"],
            f"Fine ₹{total_amount} issued for vehicle {vehicle['vehicle_no']}. View & Pay: {user_link}"
        )

    return jsonify({"message": "Fine imposed successfully", "link": user_link})



@admin_bp.route("/fines/token/<token>", methods=["GET"])
def fines_by_token(token):
    fines = list(mongo.db.fines.find({"token": token}, {"_id": 0}))

    if not fines:
        return jsonify({"message": "Invalid or expired link"}), 404

    # Ensure every fine has violations array and total_amount
    for f in fines:
        if "violations" not in f:
            f["violations"] = [{"type": f.get("reason", "Traffic Rule Violation"),
                                "expired_on": None,
                                "fine": f.get("amount", 500)}]
        if "total_amount" not in f:
            f["total_amount"] = sum(v["fine"] for v in f["violations"])

    total_unpaid_amount = sum(f["total_amount"] for f in fines if f["status"] == "UNPAID")

    return jsonify({
        "fines": fines,
        "total_unpaid_amount": total_unpaid_amount
    })

@admin_bp.route("/vehicles", methods=["GET"])
@role_required(["ADMIN", "SUPER_ADMIN", "OFFICER"])
def get_all_vehicles():
    vehicles = list(mongo.db.vehicles.find({}))
    
    # Convert ObjectId to string
    for v in vehicles:
        v["_id"] = str(v["_id"])
    
    return jsonify({"vehicles": vehicles})



@admin_bp.route("/vehicle/<vehicle_id>", methods=["GET"])
def get_vehicle(vehicle_id):
    vehicle = mongo.db.vehicles.find_one({"_id": ObjectId(vehicle_id)})

    if not vehicle:
        return jsonify({"message": "Vehicle not found"}), 404

    vehicle["_id"] = str(vehicle["_id"])
    return jsonify(vehicle), 200



@admin_bp.route("/dashboard", methods=["GET"])
def dashboard_page():
    # Optional: pass data if needed
    return render_template("dashboard.html")
