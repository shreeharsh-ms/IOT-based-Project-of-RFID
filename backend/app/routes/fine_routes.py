from flask import Blueprint, request, jsonify
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
