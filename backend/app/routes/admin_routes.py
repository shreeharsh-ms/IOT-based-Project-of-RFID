from flask import Blueprint, request, jsonify
from app.extensions import mongo

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/add-vehicle", methods=["POST"])
def add_vehicle():
    mongo.db.vehicles.insert_one(request.json)
    return jsonify({"message": "Vehicle added"})
