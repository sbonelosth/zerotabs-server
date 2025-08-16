from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, UTC
import jwt, os, random, string
from passlib.context import CryptContext
from couchbase.options import QueryOptions
from couchbase.exceptions import DocumentNotFoundException
from utils.jwt_helper import create_access_token, decode_token
from fastapi.security import OAuth2PasswordBearer

from utils.couchbase_client import CouchbaseClient
from utils.mail_service import MailService

router = APIRouter(prefix="/auth", tags=["Auth"])

SECRET_KEY = os.getenv("JWT_SECRET", "supersecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

scope = os.getenv("COUCHBASE_SCOPE", "appdata")
collection_name = "users"
db = CouchbaseClient().get_collection(scope, collection_name)


# =====================
# Schemas
# =====================

class SignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str

class VerifyRequest(BaseModel):
    email: EmailStr
    code: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


# =====================
# Helpers
# =====================

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# =====================
# Routes
# =====================

@router.post("/signup")
def signup(req: SignupRequest):
    user_id = f"user::{req.email}"
    try:
        existing = db.get(user_id)
        raise HTTPException(status_code=400, detail="User already exists")
    except DocumentNotFoundException:
        # Good! user doesn't exist, continue creating
        pass

    otp = generate_otp()
    user_doc = {
        "user_id": user_id,
        "full_name": req.full_name,
        "email": req.email,
        "phone": req.phone,
        "password": hash_password(req.password),  # ✅ now hashed
        "kyc_verified": False,
        "verified": False,
        "otp": otp,
        "refresh_token": None,
        "created_at": datetime.utcnow().isoformat()
    }

    db.upsert(user_id, user_doc)

    # TODO: send OTP email instead of returning
    # ✅ Send OTP via email
    subject = "Your ZeroTabs OTP Verification Code"
    body = f"""
    <h2>Welcome to ZeroTabs 🎉</h2>
    <p>Your One-Time Password (OTP) is:</p>
    <h1 style="color:#4CAF50;">{otp}</h1>
    <p>This code will expire in 10 minutes. Please don’t share it.</p>
    """

    MailService.send_email(req.email, subject, body)
    return {"message": "User registered, verify email with OTP", "otp": otp}


@router.post("/verify")
def verify(req: VerifyRequest):
    user_id = f"user::{req.email}"
    try:
        result = db.get(user_id)
        user = result.content_as[dict]
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("otp") != req.code:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    user["verified"] = True
    user["otp"] = None
    db.upsert(user_id, user)
    return {"message": "Email verified successfully"}


@router.post("/login")
def login(req: LoginRequest):
    user_id = f"user::{req.email}"
    try:
        result = db.get(user_id)
        user = result.content_as[dict]
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.get("verified"):
        raise HTTPException(status_code=403, detail="User not verified")

    if not verify_password(req.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_token({"sub": user_id}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_token({"sub": user_id}, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    # update stored refresh token
    user["refresh_token"] = refresh_token
    db.upsert(user_id, user)

    # build safe user payload
    safe_user = {
        "user_id": user["user_id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "phone": user.get("phone"),
        "verified": user.get("verified", False),
        "kyc_verified": user.get("kyc_verified", False),
        "created_at": user.get("created_at"),
    }

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": safe_user
    }


@router.post("/refresh")
def refresh(req: TokenRefreshRequest):
    try:
        payload = jwt.decode(req.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    try:
        result = db.get(user_id)
        user = result.content_as[dict]
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("refresh_token") != req.refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token mismatch")

    new_access_token = create_token({"sub": user_id}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest):
    query = f"SELECT META().id, u.* FROM `{db._bucket.name}`.`{scope}`.`{collection_name}` u WHERE u.email = $1"
    rows = list(db._scope.bucket.cluster.query(query, QueryOptions(positional_parameters=[data.email])))

    if not rows:
        raise HTTPException(status_code=404, detail="User not found")

    user_doc = rows[0]
    user_id = user_doc["id"]

    otp = str(random.randint(100000, 999999))
    expiry = (datetime.now(UTC) + timedelta(minutes=10)).isoformat()

    user_doc["reset_otp"] = otp
    user_doc["reset_otp_expiry"] = expiry
    db.upsert(user_id, user_doc)

    # send OTP
    MailService.send_email(
        data.email,
        "Your Password Reset OTP",
        f"Use this OTP to reset your password: {otp}\nThis code expires in 10 minutes."
    )

    return {"message": "OTP sent to your email"}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest):
    query = f"SELECT META().id, u.* FROM `{db._bucket.name}`.`{scope}`.`{collection_name}` u WHERE u.email = $1"
    rows = list(db._scope.bucket.cluster.query(query, QueryOptions(positional_parameters=[data.email])))

    if not rows:
        raise HTTPException(status_code=404, detail="User not found")

    user_doc = rows[0]
    user_id = user_doc["id"]

    stored_otp = user_doc.get("reset_otp")
    expiry = user_doc.get("reset_otp_expiry")

    if not stored_otp or not expiry:
        raise HTTPException(status_code=400, detail="No OTP found, request a new one")

    if datetime.now(UTC) > datetime.fromisoformat(expiry):
        raise HTTPException(status_code=400, detail="OTP expired")

    if data.otp != stored_otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # ✅ hash the new password before saving
    user_doc["password"] = hash_password(data.new_password)
    user_doc.pop("reset_otp", None)
    user_doc.pop("reset_otp_expiry", None)
    db.upsert(user_id, user_doc)

    return {"message": "Password reset successful"}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

class RefreshRequest(BaseModel):
    refresh_token: str

# Get current user info
@router.get("/me")
def get_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        result = db.get(user_id)
        user = result.content_as[dict]
        user.pop("password", None)
        user.pop("otp", None)
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Refresh token endpoint
@router.post("/refresh")
def refresh(req: RefreshRequest):
    try:
        payload = decode_token(req.refresh_token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        result = db.get(user_id)
        user = result.content_as[dict]
        if user.get("refresh_token") != req.refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token mismatch")

        new_access_token = create_access_token(
            {"sub": user_id}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return {"access_token": new_access_token, "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")