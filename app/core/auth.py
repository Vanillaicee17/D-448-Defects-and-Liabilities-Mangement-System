from jose import jwt
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from db.dependency import get_db
from models.user import User

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt

import os
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGO = "HS256"
ACCESS_TOKEN_EXPIRE_MIN = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


security = HTTPBearer()


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)
    to_encode.update({"exp": expire, "type": "access"})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGO)


def create_refresh_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGO)


def get_new_access_token(refresh_token: str):
    payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGO])

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    new_access_token = create_access_token({
        "user_id": payload["user_id"],
        "role": payload["role"],
        "org": payload["org"]
    })

    return new_access_token


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),
                     db: Session = Depends(get_db)):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])

        if payload.get("type") != "access":
            raise HTTPException(401)
        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(status_code=401, detail="invalid token")

    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_data = db.query(User).filter(User.user_id == user_id).first()

    if not user_data:
        raise HTTPException(status_code=401, detail="User not found")

    return user_data


def required_roles(roles: list):
    def role_checker(user=Depends(get_current_user)):
        if user.role.role_name not in roles:
            raise HTTPException(status_code=403, detail="forbidden")

        return user

    return role_checker
