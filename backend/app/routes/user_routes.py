from flask import Blueprint, request, jsonify
from app.extensions import mongo

user_bp = Blueprint("user", __name__)

@user_bp.route("/fine", methods=["POST"])
def view_fine():
    data = request.json
    fines = list(mongo.db.fines.find({"vehicle_no": data.get("vehicle_no")}))
    return jsonify(fines)
