from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.dependency import get_db
from models.equipment import Equipment
from models.equipment_master import EquipmentMaster
from models.vessel import Vessel
from models.vendor import Vendor

from schemas.equipment import (
    EquipmentCreate,
    EquipmentResponse,
    EquipmentTypeCreate,
    EquipmentTypeResponse
)

from core.auth import required_roles

router = APIRouter(prefix="/equipment", tags=["Equipment"])


@router.post("/types", response_model=EquipmentTypeResponse)
def create_equipment_type(
    data: EquipmentTypeCreate,
    db: Session = Depends(get_db),
    user=Depends(required_roles(["Admin", "GuaranteeDept"]))
):
    new_type = EquipmentMaster(
        name=data.name,
        manufacturer=data.manufacturer,
        model_no=data.model_no
    )

    db.add(new_type)
    db.commit()
    db.refresh(new_type)

    return new_type


@router.get("/types", response_model=list[EquipmentTypeResponse])
def get_equipment_types(
    db: Session = Depends(get_db),
    user=Depends(required_roles(["Admin", "GuaranteeDept", "OverseeingTeam"]))
):
    return db.query(EquipmentMaster).all()


@router.post("/", response_model=EquipmentResponse)
def create_equipment(
    data: EquipmentCreate,
    db: Session = Depends(get_db),
    user=Depends(required_roles(["GuaranteeDept"]))
):
    # ✅ Validate vessel
    vessel = db.query(Vessel).filter(
        Vessel.vessel_id == data.vessel_id
    ).first()

    if not vessel:
        raise HTTPException(404, "Vessel not found")

    # ✅ Validate vendor
    vendor = db.query(Vendor).filter(
        Vendor.vendor_id == data.vendor_id
    ).first()

    if not vendor:
        raise HTTPException(404, "Vendor not found")

    # ✅ Validate equipment type
    eq_type = db.query(EquipmentMaster).filter(
        EquipmentMaster.equipment_type_id == data.equipment_type_id
    ).first()

    if not eq_type:
        raise HTTPException(404, "Equipment type not found")

    new_equipment = Equipment(
        vessel_id=data.vessel_id,
        vendor_id=data.vendor_id,
        equipment_type_id=data.equipment_type_id,
        serial_no=data.serial_no
    )

    db.add(new_equipment)
    db.commit()
    db.refresh(new_equipment)

    return new_equipment


@router.get("/", response_model=list[EquipmentResponse])
def get_equipment(
    db: Session = Depends(get_db),
    user=Depends(required_roles(["GuaranteeDept", "OverseeingTeam"]))
):
    return db.query(Equipment).all()


@router.get("/vessel/{vessel_id}", response_model=list[EquipmentResponse])
def get_equipment_by_vessel(
    vessel_id: int,
    db: Session = Depends(get_db),
    user=Depends(required_roles(["GuaranteeDept", "OverseeingTeam"]))
):
    return db.query(Equipment).filter(
        Equipment.vessel_id == vessel_id
    ).all()
