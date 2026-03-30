from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.dependency import get_db
from models.vendor import Vendor
from schemas.vendor import VendorCreate, VendorUpdate, VendorResponse
from core.auth import required_roles

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.post("/", response_model=VendorResponse)
def create_vendor(
    data: VendorCreate,
    db: Session = Depends(get_db),
    user=Depends(required_roles(["Admin", "GuaranteeDept"]))
):
    # ✅ email unique
    existing_email = db.query(Vendor).filter(
        Vendor.email == data.email).first()
    if existing_email:
        raise HTTPException(400, "Email already exists")

    # ✅ phone unique
    existing_phone = db.query(Vendor).filter(
        Vendor.phone == data.phone).first()
    if existing_phone:
        raise HTTPException(400, "Phone already exists")

    vendor = Vendor(
        name=data.name,
        email=data.email,
        phone=data.phone,
        address=data.address
    )

    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    return vendor


@router.get("/", response_model=list[VendorResponse])
def get_vendors(
    db: Session = Depends(get_db),
    user=Depends(required_roles(["Admin", "GuaranteeDept", "OverseeingTeam"])),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100)
):
    return db.query(Vendor).offset(skip).limit(limit).all()


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(required_roles(["Admin", "GuaranteeDept", "OverseeingTeam"]))
):
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()

    if not vendor:
        raise HTTPException(404, "Vendor not found")

    return vendor


@router.patch("/{vendor_id}")
def update_vendor(
    vendor_id: int,
    data: VendorUpdate,
    db: Session = Depends(get_db),
    user=Depends(required_roles(["Admin", "GuaranteeDept"]))
):
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()

    if not vendor:
        raise HTTPException(404, "Vendor not found")

    # ✅ email uniqueness
    if data.email:
        existing = db.query(Vendor).filter(Vendor.email == data.email).first()
        if existing and existing.vendor_id != vendor_id:
            raise HTTPException(400, "Email already exists")
        vendor.email = data.email

    # ✅ phone uniqueness
    if data.phone:
        existing = db.query(Vendor).filter(Vendor.phone == data.phone).first()
        if existing and existing.vendor_id != vendor_id:
            raise HTTPException(400, "Phone already exists")
        vendor.phone = data.phone

    if data.name:
        vendor.name = data.name

    if data.address:
        vendor.address = data.address

    db.commit()
    db.refresh(vendor)

    return {"message": "Vendor updated successfully"}


@router.delete("/{vendor_id}")
def delete_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(required_roles(["Admin"]))
):
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()

    if not vendor:
        raise HTTPException(404, "Vendor not found")

    db.delete(vendor)
    db.commit()

    return {"message": "Vendor deleted successfully"}
