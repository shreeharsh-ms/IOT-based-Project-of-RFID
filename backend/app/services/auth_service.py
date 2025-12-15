import jwt
from datetime import datetime, timedelta
from flask import current_app

def generate_token(admin):
    payload = {
        "id": str(admin["_id"]),
        "role": admin["role"],
        "exp": datetime.utcnow() + timedelta(hours=8)
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def verify_token(token):
    try:
        return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except Exception:
        return None
