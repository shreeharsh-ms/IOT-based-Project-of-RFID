from flask import Blueprint, request, jsonify
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
