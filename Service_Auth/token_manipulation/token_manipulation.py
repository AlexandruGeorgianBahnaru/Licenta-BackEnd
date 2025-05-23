import utils.constants as constants
import jwt

from datetime import datetime, timedelta
from jwt import PyJWTError, ExpiredSignatureError


def create_access_token(uid: str, email: str):
    try:
        expires_at = datetime.utcnow() + timedelta(minutes=constants.ACCESS_EXPIRE_MINUTES)
        created_at = datetime.utcnow()
        to_encode = {
            "uid": uid,
            "email": email,
            "expires_at": int(expires_at.timestamp()),
            "created_at": int(created_at.timestamp())
        }
        access_token = jwt.encode(to_encode, constants.SECRET_KEY, algorithm=constants.ENCRYPTATION_ALGORITHM)
        return {"success": True, "token": access_token, "expires_in": constants.ACCESS_EXPIRE_MINUTES}
    except PyJWTError as e:
        return {"success": False, "error": "jwt encoding failed"}

def verify_token_expiry(token: str):
    try:
        payload = jwt.decode(token, constants.SECRET_KEY, algorithms=[constants.ENCRYPTATION_ALGORITHM])
        uid = payload["uid"]
        email = payload["email"]
        exp = payload.get("expires_at")
        if exp is None:
            return "invalid_token", "", ""

        expiry_time = datetime.fromtimestamp(exp)
        if datetime.utcnow() > expiry_time:
            return "expired", "", ""
        return "valid", uid, email

    except ExpiredSignatureError:
        return "expired", "", ""
    except PyJWTError:
        return "invalid_token", "", ""

def get_email_from_token(token: str) -> str:
    try:
        payload = jwt.decode(token, constants.SECRET_KEY, algorithms=[constants.ENCRYPTATION_ALGORITHM])
        email = payload.get("email")
        if email is None:
            return "missing_email"
        return email
    except PyJWTError:
        return "invalid_token"

