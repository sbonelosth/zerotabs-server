import jwt
from datetime import datetime, timedelta, timezone
import os
from jwt import ExpiredSignatureError, InvalidTokenError

SECRET = os.getenv("JWT_SECRET", "supersecret")
ALGO = "HS256"

def create_access_token(data: dict, expires_minutes: int = 15):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    return jwt.encode(to_encode, SECRET, algorithm=ALGO)

def create_refresh_token(username: str, expires_days: int = 7):
    expire = datetime.now(timezone.utc) + timedelta(days=expires_days)
    payload = {
        "sub": username,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def decode_token(token: str):
    """
    Decodes any JWT (access or refresh).
    Raises exception if expired/invalid.
    """
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        return payload
    except ExpiredSignatureError:
        raise Exception("Token expired")
    except InvalidTokenError:
        raise Exception("Invalid token")

def verify_refresh_token(token: str):
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise Exception("Not a refresh token")
    return payload

def verify_access_token(token: str):
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise Exception("Not an access token")
    return payload
