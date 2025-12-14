import os

BASE_DIR = "iot-rfid-system"

folders = [
    "backend/app/routes",
    "backend/app/services",
    "backend/app/utils",
    "frontend/admin",
    "frontend/user",
    "frontend/css",
    "frontend/js",
]

files = {
    # ---------------- BACKEND ----------------
    "backend/run.py": """from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
""",

    "backend/app/__init__.py": """from flask import Flask
from .config import Config
from .extensions import mongo
from .routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mongo.init_app(app)
    register_routes(app)

    return app
""",

    "backend/app/config.py": """import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/iot_rfid")
""",

    "backend/app/extensions.py": """from flask_pymongo import PyMongo

mongo = PyMongo()
""",

    "backend/app/models.py": """from datetime import datetime
from bson import ObjectId

# MongoDB collections will be used directly via PyMongo
# This file is for structure reference only

class Vehicle:
    pass

class Fine:
    pass

class Admin:
    pass
""",

    # ---------------- ROUTES ----------------
    "backend/app/routes/__init__.py": """from .scan_routes import scan_bp
from .fine_routes import fine_bp
from .admin_routes import admin_bp
from .user_routes import user_bp

def register_routes(app):
    app.register_blueprint(scan_bp, url_prefix="/api/scan")
    app.register_blueprint(fine_bp, url_prefix="/api/fine")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(user_bp, url_prefix="/api/user")
""",

    "backend/app/routes/scan_routes.py": """from flask import Blueprint, request, jsonify
from app.extensions import mongo

scan_bp = Blueprint("scan", __name__)

@scan_bp.route("/", methods=["POST"])
def scan_vehicle():
    data = request.json
    rfid = data.get("rfid_tag")

    vehicle = mongo.db.vehicles.find_one({"rfid_tag": rfid})

    if not vehicle:
        return jsonify({"status": "NOT_FOUND"}), 404

    issues = []

    return jsonify({
        "status": "OK" if not issues else "VIOLATION",
        "issues": issues
    })
""",

    "backend/app/routes/fine_routes.py": """from flask import Blueprint, request, jsonify
from app.extensions import mongo
from datetime import datetime

fine_bp = Blueprint("fine", __name__)

@fine_bp.route("/", methods=["POST"])
def create_fine():
    data = request.json

    fine = {
        "vehicle_no": data.get("vehicle_no"),
        "rfid_tag": data.get("rfid_tag"),
        "issues": data.get("issues"),
        "amount": data.get("amount"),
        "status": "UNPAID",
        "created_at": datetime.utcnow()
    }

    mongo.db.fines.insert_one(fine)

    return jsonify({"message": "Fine issued successfully"})
""",

    "backend/app/routes/admin_routes.py": """from flask import Blueprint, request, jsonify
from app.extensions import mongo

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/add-vehicle", methods=["POST"])
def add_vehicle():
    mongo.db.vehicles.insert_one(request.json)
    return jsonify({"message": "Vehicle added"})
""",

    "backend/app/routes/user_routes.py": """from flask import Blueprint, request, jsonify
from app.extensions import mongo

user_bp = Blueprint("user", __name__)

@user_bp.route("/fine", methods=["POST"])
def view_fine():
    data = request.json
    fines = list(mongo.db.fines.find({"vehicle_no": data.get("vehicle_no")}))
    return jsonify(fines)
""",

    # ---------------- SERVICES ----------------
    "backend/app/services/twilio_service.py": """def send_sms(to, message):
    print(f"Sending SMS to {to}: {message}")
""",

    "backend/app/services/auth_service.py": """def verify_token(token):
    return True
""",

    # ---------------- UTILS ----------------
    "backend/app/utils/token_utils.py": """def extract_token(headers):
    return headers.get("Authorization")
""",

    "backend/app/utils/validators.py": """def validate_request(data, fields):
    return all(field in data for field in fields)
""",

    # ---------------- OTHER ----------------
    "backend/requirements.txt": """flask
flask-pymongo
python-dotenv
""",

    # ---------------- FRONTEND ----------------
    "frontend/admin/index.html": "<h1>Admin Login</h1>",
    "frontend/admin/dashboard.html": "<h1>Admin Dashboard</h1>",
    "frontend/admin/admin.js": "// Admin JS",

    "frontend/user/fine.html": "<h1>View Fine</h1>",
    "frontend/user/fine.js": "// User JS",

    "frontend/css/style.css": "body { font-family: Arial; }",
    "frontend/js/api.js": "// API helper",
}

def create_project():
    os.makedirs(BASE_DIR, exist_ok=True)

    for folder in folders:
        os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)

    for path, content in files.items():
        full_path = os.path.join(BASE_DIR, path)
        with open(full_path, "w") as f:
            f.write(content)

    print("✅ Flask project structure created successfully!")

if __name__ == "__main__":
    create_project()
