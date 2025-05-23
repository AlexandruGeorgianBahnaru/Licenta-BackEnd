import jwt
import datetime
import utils.constants as constants


from jwt import ExpiredSignatureError, PyJWTError
from datetime import datetime, timedelta

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
