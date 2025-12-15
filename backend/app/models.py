from datetime import datetime
from bson import ObjectId


# =====================================================
# VEHICLE MODEL
# =====================================================

class Vehicle:
    COLLECTION = "vehicles"

    def __init__(
        self,
        vehicle_no,
        model_no,                  # <-- new field
        rfid_tag,
        owner_name,
        insurance_expiry,
        puc_expiry,
        mobile_number,
        created_at=None,
        _id=None
    ):
        self.id = _id
        self.vehicle_no = vehicle_no
        self.model_no = model_no    # <-- store model number
        self.rfid_tag = rfid_tag
        self.owner_name = owner_name
        self.insurance_expiry = insurance_expiry
        self.puc_expiry = puc_expiry
        self.mobile_number = mobile_number
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            "vehicle_no": self.vehicle_no,
            "model_no": self.model_no,   # <-- include in dict
            "rfid_tag": self.rfid_tag,
            "owner_name": self.owner_name,
            "insurance_expiry": self.insurance_expiry,
            "puc_expiry": self.puc_expiry,
            "mobile_number": self.mobile_number,
            "created_at": self.created_at
        }

    @staticmethod
    def is_insurance_expired(vehicle):
        return vehicle["insurance_expiry"] < datetime.utcnow()

    @staticmethod
    def is_puc_expired(vehicle):
        return vehicle["puc_expiry"] < datetime.utcnow()


# =====================================================
# FINE MODEL
# =====================================================

class Fine:
    COLLECTION = "fines"

    def __init__(
        self,
        vehicle_no,
        rfid_tag,
        issues,
        amount,
        status="UNPAID",
        issued_at=None,
        _id=None
    ):
        self.id = _id
        self.vehicle_no = vehicle_no
        self.rfid_tag = rfid_tag
        self.issues = issues
        self.amount = amount
        self.status = status
        self.issued_at = issued_at or datetime.utcnow()

    def to_dict(self):
        return {
            "vehicle_no": self.vehicle_no,
            "rfid_tag": self.rfid_tag,
            "issues": self.issues,
            "amount": self.amount,
            "status": self.status,
            "issued_at": self.issued_at
        }


# =====================================================
# ADMIN MODEL
# =====================================================

class Admin:
    COLLECTION = "admins"

    def __init__(
        self,
        username,
        password_hash,
        role="ADMIN",
        created_at=None,
        _id=None
    ):
        self.id = _id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "role": self.role,
            "created_at": self.created_at
        }
