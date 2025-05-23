import uuid
import hashlib
import mariadb
import utils.constants as constants

from pydantic import BaseModel
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from token_manipulation import token_manipulation as tc
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, Query

app = FastAPI()
security = HTTPBearer()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    "host": constants.HOST_NAME,
    "user": constants.USER,
    "password": constants.DB_PASSWORD,
    "database": constants.DATABASE_NAME,
}

class LoginRequest(BaseModel):
    user_email: str
    user_password: str

class SignUpRequest(BaseModel):
    user_first_name: str
    user_last_name: str
    user_email: str
    user_phone: str
    user_password: str

class UpdateUserModel(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: str
    password: str

def get_db_connection():
    return mariadb.connect(**DB_CONFIG)

@app.post("/login")
def login(login_request: LoginRequest):
    try:
        user_email = login_request.user_email
        user_password = login_request.user_password

        hashed_password = hashlib.md5(user_password.encode()).hexdigest()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT uid, first_name, last_name, email 
            FROM users 
            WHERE email = %s AND password_hash = %s"""

        cursor.execute(query, (user_email, hashed_password))
        found_user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not found_user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        uuid = found_user['uid']
        email = found_user['email']

        token = tc.create_access_token(uuid, email)
        if(token["success"] is False):
            raise HTTPException(status_code=500, detail=str(token["error"]))

        response_data = {
            "message": "Login successful",
            "access_token": token["token"],
            "expires_in": token["expires_in"]
        }
        return JSONResponse(content=response_data)

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/signup")
def signup(signup_request: SignUpRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query_find_user = """SELECT id FROM users WHERE email = %s OR phone = %s"""
        cursor.execute(query_find_user, (signup_request.user_email, signup_request.user_phone))

        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="User with this email or phone already exists")

        query_find_uids = """SELECT uid FROM users"""
        cursor.execute(query_find_uids)

        uids = {row[0] for row in cursor.fetchall()}
        new_uid = uuid.uuid4()
        while str(new_uid) in uids:
            new_uid = uuid.uuid4()

        hashed_password = hashlib.md5(signup_request.user_password.encode()).hexdigest()

        query_insert_new_user = """INSERT INTO users (uid, first_name, last_name, email, phone, password_hash) VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.execute(query_insert_new_user,(new_uid, signup_request.user_first_name, signup_request.user_last_name, signup_request.user_email, signup_request.user_phone, hashed_password))
        conn.commit()

        cursor.close()
        conn.close()
        return {"message": "User created successfully"}

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/getUserInfo")
def getUserInfo(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        print(token)
        expired, uid, email = tc.verify_token_expiry(token)
        print(expired + " " + email)
        if expired == 'expired':
            raise HTTPException(status_code=401, detail="Expired refresh token")
        if expired == 'invalid':
            raise HTTPException(status_code=403, detail="Invalid refresh token")

        #email = tc.get_email_from_token(token)
        if email in ["missing_email", "invalid_token"]:
            raise HTTPException(status_code=400, detail="Invalid token structure")

        conn = get_db_connection()
        cursor = conn.cursor()

        query_find_user = """
                   SELECT first_name, last_name, email, phone
                   FROM users
                   WHERE email = %s;
               """
        cursor.execute(query_find_user, (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"user": user}

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/updateUser")
def update_user(
    user_data: UpdateUserModel,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        token = credentials.credentials
        expired, uid, email = tc.verify_token_expiry(token)

        if expired == 'expired':
            raise HTTPException(status_code=401, detail="Expired token")
        if expired == 'invalid':
            raise HTTPException(status_code=403, detail="Invalid token")

        if email in ["missing_email", "invalid_token"]:
            raise HTTPException(status_code=400, detail="Invalid token structure")

        if email != user_data.email:
            raise HTTPException(status_code=403, detail="Cannot modify another user's data")

        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_password = hashlib.md5(user_data.password.encode()).hexdigest()
        update_query = ""

        if user_data.password != "":
            update_query = """
                UPDATE users
                SET first_name = %s,
                    last_name = %s,
                    phone = %s,
                    password_hash = %s
                WHERE email = %s;
                """
            cursor.execute(update_query, (
                user_data.first_name,
                user_data.last_name,
                user_data.phone,
                hashed_password,
                email
            ))
        else:
            update_query = """
                            UPDATE users
                            SET first_name = %s,
                                last_name = %s,
                                phone = %s
                            WHERE email = %s;
                        """
            cursor.execute(update_query, (
                user_data.first_name,
                user_data.last_name,
                user_data.phone,
                email
            ))
        conn.commit()

        cursor.close()
        conn.close()
        return {"message": "User updated successfully"}

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
