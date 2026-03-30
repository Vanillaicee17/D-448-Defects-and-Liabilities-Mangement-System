from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.dependency import get_db
from models.user import User
from models.role import Role
from schemas.user import UserCreate, UserResponse, UserUpdate
from core.security import hashing
from core.auth import required_roles

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/")
def register(user_data: UserCreate, db: Session = Depends(get_db), user=Depends(required_roles(["Admin"]))):
    existing_user = db.query(User).filter(
        User.email == user_data.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashing(user_data.password),
        role_id=user_data.role_id,
        organisation=user_data.organisation
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully"}


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int,
             db: Session = Depends(get_db),
             user=Depends(required_roles(["Admin"]))
             ):
    user_data = db.query(User).filter(User.user_id == user_id).first()

    return user_data


@router.patch("/{user_id}")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    user=Depends(required_roles(["Admin"]))
):
    db_user = db.query(User).filter(User.user_id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Email uniqueness check
    if user_data.email:
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing and existing.user_id != user_id:
            raise HTTPException(status_code=400, detail="Email already exists")

    # ✅ Role validation
    if user_data.role_id:
        role = db.query(Role).filter(Role.role_id == user_data.role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

    # ✅ Update fields dynamically
    if user_data.name:
        db_user.name = user_data.name

    if user_data.email:
        db_user.email = user_data.email

    if user_data.password:
        db_user.password_hash = hashing(user_data.password)

    if user_data.role_id:
        db_user.role_id = user_data.role_id

    if user_data.organisation:
        db_user.organisation = user_data.organisation

    db.commit()
    db.refresh(db_user)

    return {"message": "User updated successfully"}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(required_roles(["Admin"]))
):
    db_user = db.query(User).filter(User.user_id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if db_user.user_id == user.user_id:
        raise HTTPException(400, "Cannot delete yourself")

    db.delete(db_user)
    db.commit()

    return {"message": "User deleted successfully"}
