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
from flask import redirect, url_for

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Check token in headers OR query param
            token = request.headers.get("Authorization") or request.args.get("token")
            payload = verify_token(token)
            if not payload or payload.get("role") not in roles:
                # Redirect browser to login if token invalid/missing
                return redirect(url_for("admin.login_page"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ================= LOGIN =================
# ================= LOGIN =================
@admin_bp.route("/login", methods=["POST"])
def admin_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    admin = mongo.db.admins.find_one({"username": username})
    if not admin or not check_password_hash(admin["password_hash"], password):
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
    # Calculate total revenue from PAID fines
    total_revenue = 0
    paid_fines = mongo.db.fines.find({"status": "PAID"})
    for fine in paid_fines:
        total_revenue += fine.get("total_amount", 0)
    
    # Count unpaid fines
    unpaid_fines_count = mongo.db.fines.count_documents({"status": "UNPAID"})
    
    return jsonify({
        "total_vehicles": mongo.db.vehicles.count_documents({}),
        "total_fines": mongo.db.fines.count_documents({}),
        "unpaid_fines": unpaid_fines_count,
        "total_amount": total_revenue,
        "paid_fines": mongo.db.fines.count_documents({"status": "PAID"}),
        "pending_fines": unpaid_fines_count
    })

# ================= FINES =================
@admin_bp.route("/fines", methods=["GET"])
@role_required(["ADMIN", "SUPER_ADMIN", "OFFICER"])
def view_fines():
    fines = list(mongo.db.fines.find({}))
    
    # Convert ObjectId to string and add vehicle details
    for fine in fines:
        fine["_id"] = str(fine["_id"])
        # If vehicle details are missing, fetch from vehicles collection
        if not fine.get("vehicle_no"):
            vehicle = mongo.db.vehicles.find_one({"rfid_tag": fine.get("rfid_tag")})
            if vehicle:
                fine["vehicle_no"] = vehicle.get("vehicle_no", "N/A")
                fine["model_no"] = vehicle.get("model_no", "N/A")  # Add model_no
                fine["owner_name"] = vehicle.get("owner_name", "N/A")
                fine["mobile_number"] = vehicle.get("mobile_number", "N/A")
    
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

import secrets
from datetime import datetime

from twilio.rest import Client


# User login page (RFID + phone)
@admin_bp.route("/user/login-page", methods=["GET"])
def user_login_page():
    return render_template("user_login.html")  # renders templates/user_login.html

# Serve fine payment page
@admin_bp.route("/user/fine", methods=["GET"])
def fine_page():
    token = request.args.get("token")  # Get token from URL
    vehicle = mongo.db.vehicles.find_one({"access_token": token})

    if not vehicle:
        return redirect(url_for("admin.user_login_page"))  # redirect to user login if token invalid

    return render_template("fine.html", token=token)  # Serve fines HTML


def send_sms_via_twilio(mobile_number, message):
    """
    TEMPORARY: Hardcoded Twilio credentials (for testing only)
    """

    print("\n================ TWILIO DEBUG START ================")

    try:
        print("➡️ Raw mobile_number:", mobile_number)
        print("➡️ Type of mobile_number:", type(mobile_number))

        # 🔴 TEMPORARY HARDCODED VALUES
        account_sid = "AC6e105a79612959f9d2cfb7b2d3534984"
        auth_token = "4bbc75505cd8f7d5e0dc8f2415e7f534"
        twilio_number = "+13048026706"

        print("➡️ Account SID loaded:", account_sid[:6] + "****")
        print("➡️ Twilio number:", twilio_number)

        # ✅ Ensure mobile number is string
        mobile_number = str(mobile_number).strip()
        print("➡️ Mobile number after str():", mobile_number)

        # ✅ Ensure E.164 format
        if not mobile_number.startswith("+"):
            to_number = "+91" + mobile_number
        else:
            to_number = mobile_number

        print("➡️ Final TO number:", to_number)

        print("➡️ Creating Twilio client...")
        client = Client(account_sid, auth_token)

        print("➡️ Sending SMS...")
        msg = client.messages.create(
            body=message,
            from_=twilio_number,
            to=to_number
        )

        print("✅ SMS SENT SUCCESSFULLY")
        print("📨 Message SID:", msg.sid)
        print("================ TWILIO DEBUG END ================\n")

        return True

    except Exception as e:
        print("❌ TWILIO ERROR OCCURRED")
        print("❌ Error type:", type(e))
        print("❌ Error message:", str(e))
        print("================ TWILIO DEBUG END ================\n")
        return False



def impose_fine_internal(vehicle, request_host_url):
    now = datetime.now()
    rfid = vehicle["rfid_tag"]

    # Token handling
    access_token = vehicle.get("access_token")
    if not access_token:
        access_token = secrets.token_urlsafe(16)
        mongo.db.vehicles.update_one(
            {"_id": vehicle["_id"]},
            {"$set": {"access_token": access_token}}
        )

    violations = []
    total_amount = 0

    # Insurance check
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

    # PUC check
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

    # If no violations → no fine
    if not violations:
        return None

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

    user_link = f"{request_host_url}api/admin/user/fine?token={access_token}"

    # Send SMS
    if vehicle.get("mobile_number"):
        send_sms_via_twilio(
            vehicle["mobile_number"],
            f"Fine ₹{total_amount} issued for vehicle {vehicle['vehicle_no']}. Pay here: {user_link}"
        )

    return {
        "total_amount": total_amount,
        "violations": violations,
        "link": user_link
    }

@admin_bp.route("/impose-fine", methods=["POST"])
def impose_fine():
    rfid = request.json.get("rfid")
    if not rfid:
        return jsonify({"message": "RFID is required"}), 400

    vehicle = mongo.db.vehicles.find_one({"rfid_tag": rfid})
    if not vehicle:
        return jsonify({"message": "Vehicle not found"}), 404

    result = impose_fine_internal(vehicle, request.host_url)

    if not result:
        return jsonify({"message": "No violations found. No fine imposed."})

    return jsonify({
        "message": "Fine imposed successfully",
        "total_amount": result["total_amount"],
        "violations": result["violations"],
        "link": result["link"]
    })


@admin_bp.route("/check-expiry", methods=["POST"])
def check_expiry():
    value = request.json.get("rfid")
    if not value:
        return jsonify({"message": "RFID is required"}), 400

    vehicle = mongo.db.vehicles.find_one({"rfid_tag": value})
    if not vehicle:
        return jsonify({"message": "Vehicle not found"}), 404

    now = datetime.now()

    insurance_expired = None
    puc_expired = None

    try:
        insurance_expiry = datetime.fromisoformat(vehicle["insurance_expiry"])
        insurance_expired = insurance_expiry < now
    except:
        pass

    try:
        puc_expiry = datetime.fromisoformat(vehicle["puc_expiry"])
        puc_expired = puc_expiry < now
    except:
        pass

    # 🚨 AUTO IMPOSE FINE IF EXPIRED
    fine_result = impose_fine_internal(vehicle, request.host_url)

    response = {
        "vehicle_no": vehicle.get("vehicle_no"),
        "model_no": vehicle.get("model_no"),
        "owner_name": vehicle.get("owner_name"),
        "rfid_tag": vehicle.get("rfid_tag"),
        "insurance_expiry": vehicle.get("insurance_expiry"),
        "puc_expiry": vehicle.get("puc_expiry"),
        "insurance_expired": insurance_expired,
        "puc_expired": puc_expired,
        "fine_imposed": bool(fine_result),
        "fine_details": fine_result
    }

    return jsonify(response)



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
@role_required(["ADMIN", "SUPER_ADMIN"])
def dashboard_page():
    return render_template("dashboard.html")


# Serve login page
@admin_bp.route("/login-page", methods=["GET"])
def login_page():
    return render_template("login.html")


from werkzeug.security import generate_password_hash

# ================= CREATE ADMIN =================
@admin_bp.route("/create-admin", methods=["POST"])
def create_admin():
    """
    Create a new admin user.
    Expected JSON body:
    {
        "username": "admin1",
        "password": "yourpassword",
        "role": "ADMIN"  # or "SUPER_ADMIN"
    }
    """
    data = request.json
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "ADMIN")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    existing_admin = mongo.db.admins.find_one({"username": username})
    if existing_admin:
        return jsonify({"message": "Admin already exists"}), 400

    password_hash = generate_password_hash(password)

    mongo.db.admins.insert_one({
        "username": username,
        "password_hash": password_hash,
        "role": role
    })

    return jsonify({"message": f"Admin '{username}' created successfully"})


@admin_bp.route("/user/login", methods=["POST"])
def user_login():
    """
    User login using RFID and phone number.
    Expected JSON:
    {
        "rfid": "RFID_TAG",
        "mobile_number": "PHONE_NUMBER"
    }
    """
    data = request.json
    rfid = data.get("rfid")
    mobile_number = data.get("mobile_number")

    if not rfid or not mobile_number:
        return jsonify({"message": "RFID and mobile number are required"}), 400

    vehicle = mongo.db.vehicles.find_one({
        "rfid_tag": rfid,
        "mobile_number": mobile_number
    })

    if not vehicle:
        return jsonify({"message": "Invalid credentials"}), 401

    # Generate access token for user session
    token = vehicle.get("access_token")
    if not token:
        token = secrets.token_urlsafe(16)
        mongo.db.vehicles.update_one(
            {"_id": vehicle["_id"]},
            {"$set": {"access_token": token}}
        )

    # Redirect URL to fines page with token
    fines_url = f"{request.host_url}api/admin/user/fine?token={token}"
    return jsonify({"token": token, "redirect_url": fines_url})

# Home page (general)
@admin_bp.route("/", methods=["GET"])
def home_page():
    return render_template("home.html")

@admin_bp.route("/pay-fines", methods=["POST"])
def pay_fines():
    """
    Mark all unpaid fines for a vehicle as PAID.
    Expected JSON:
    {
        "token": "ACCESS_TOKEN",   # token from user link
        "payment_method": "upi"    # optional
    }
    """
    try:
        print("\n================ PAY-FINES LOG START ================")
        
        data = request.json
        print("➡️ Request JSON:", data)

        token = data.get("token")
        payment_method = data.get("payment_method", "upi")
        print(f"➡️ Token: {token}, Payment Method: {payment_method}")

        if not token:
            print("❌ Token missing in request")
            return jsonify({"message": "Token is required"}), 400

        # Find all unpaid fines for this token
        fines = list(mongo.db.fines.find({"token": token, "status": "UNPAID"}))
        print(f"➡️ Unpaid fines found: {len(fines)}")

        if not fines:
            print("❌ No unpaid fines found for this token")
            return jsonify({"message": "No unpaid fines found for this vehicle"}), 404

        # Calculate total paid amount
        total_paid = sum(fine.get("total_amount", 0) for fine in fines)
        print(f"➡️ Total amount to be paid: ₹{total_paid}")

        # Update all fines to PAID
        result = mongo.db.fines.update_many(
            {"token": token, "status": "UNPAID"},
            {"$set": {"status": "PAID", "paid_at": datetime.now(), "payment_method": payment_method}}
        )
        print(f"✅ Updated fines count: {result.modified_count}")

        # Optional: Send SMS confirmation
        vehicle = mongo.db.vehicles.find_one({"access_token": token})
        if vehicle:
            print(f"➡️ Vehicle found: {vehicle.get('vehicle_no')}, Mobile: {vehicle.get('mobile_number')}")
            if vehicle.get("mobile_number"):
                sms_result = send_sms_via_twilio(
                    vehicle["mobile_number"],
                    f"Payment of ₹{total_paid} for vehicle {vehicle['vehicle_no']} successful. All fines cleared!"
                )
                print(f"➡️ SMS sent: {sms_result}")
            else:
                print("⚠️ Vehicle has no mobile number, SMS not sent")
        else:
            print("⚠️ Vehicle not found for this token, SMS not sent")

        print("================ PAY-FINES LOG END ================\n")
        return jsonify({
            "message": "Payment successful",
            "total_paid": total_paid,
            "fines_cleared": len(fines)
        })

    except Exception as e:
        print("❌ ERROR in pay-fines:", str(e))
        return jsonify({"message": "An error occurred during payment"}), 500
