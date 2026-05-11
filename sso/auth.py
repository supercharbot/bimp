from google.oauth2 import id_token
from google.auth.transport import requests
import os
from jose import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET = os.getenv("JWT_SECRET", "bimp-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24
ALLOWED_DOMAIN = "develo.net.au"


def verify_google_token(token):
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo.get("email", "")
        if not email.endswith(f"@{ALLOWED_DOMAIN}"):
            return None
        return {
            "email": email,
            "name": idinfo.get("name", ""),
            "picture": idinfo.get("picture", "")
        }
    except Exception:
        return None


def create_session_token(user_info, user_row):
    payload = {
        "email": user_info["email"],
        "name": user_info["name"],
        "user_id": str(user_row["user_id"]),
        "tenant_id": str(user_row["tenant_id"]),
        "role": user_row["role"],
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_session_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None
