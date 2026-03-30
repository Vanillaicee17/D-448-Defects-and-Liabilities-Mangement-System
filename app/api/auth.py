from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.dependency import get_db
from models.user import User
from schemas.user import UserCreate, UserLogin

from core.security import hashing, verify_pwd
from core.auth import create_access_token, create_refresh_token, get_new_access_token, get_current_user, required_roles


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

    if not verify_pwd(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid Credentials")

    payload = {
        "user_id": db_user.user_id,
        "role": db_user.role.role_name,
        "org": db_user.organisation
    }

    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
def change_token(refresh_token: str):
    new_access_token = get_new_access_token(refresh_token)

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
