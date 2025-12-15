import jwt
from datetime import datetime, timedelta
from flask import current_app

def generate_token(admin):
    """
    Generate JWT token for admin user.
    """
    payload = {
        "id": str(admin["_id"]),
        "role": admin["role"],
        "exp": datetime.utcnow() + timedelta(hours=8)
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def verify_token(token):
    """
    Verify JWT token and return payload if valid, else None.
    """
    try:
        return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token
