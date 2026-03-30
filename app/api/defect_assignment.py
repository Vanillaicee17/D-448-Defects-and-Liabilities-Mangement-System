from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.dependency import get_db
from models.vendor_assignment import VendorAssignment
from models.defect import Defect
from models.user import User
from schemas.defect_assignment import AssignmentCreate, AssignmentResponse
from core.auth import required_roles, get_current_user
from services.history_logger import log_history


router = APIRouter(
    prefix="/assigments",
    tags=["Assignments"]
)


@router.post("/", response_model=AssignmentResponse)
def assign_vendor(
    data: AssignmentCreate,
    db: Session = Depends(get_db),
    user=Depends(required_roles(["GuaranteeDept"]))
):

    defect = db.query(Defect).filter(
        Defect.defect_id == data.defect_id
    ).first()

    if not defect:
        raise HTTPException(404, "Defect not found")

    if defect.status != "OPEN":
        raise HTTPException(400, "Vendor can only be assigned to OPEN defects")

    vendor = db.query(User).filter(
        User.user_id == data.vendor_id
    ).first()

    if not vendor:
        raise HTTPException(404, "Vendor not found")

    if vendor.role.role_name != "Vendor":
        raise HTTPException(400, "User is not a vendor")

    existing = db.query(VendorAssignment).filter(
        VendorAssignment.defect_id == data.defect_id
    ).first()

    if existing:
        raise HTTPException(400, "Vendor already assigned")

    assignment = VendorAssignment(
        defect_id=data.defect_id,
        vendor_id=data.vendor_id,
        assigned_by=user.user_id
    )

    db.add(assignment)

    old_status = defect.status
    defect.status = "ASSIGNED"
    db.flush()

    log_history(
        db=db,
        defect_id=defect.defect_id,
        user_id=user.user_id,
        action="VENDOR_ASSIGNED",
        new_value=f"Vendor {vendor.user_id}"
    )

    log_history(
        db=db,
        defect_id=defect.defect_id,
        user_id=user.user_id,
        action="STATUS_UPDATE",
        old_value=old_status,
        new_value="ASSIGNED"
    )

    db.commit()
    db.refresh(assignment)

    return assignment


@router.get("/", response_model=list[AssignmentResponse])
def get_assignments(
    db: Session = Depends(get_db),
    user=Depends(required_roles(["Guarantee Dept"]))
):
    return db.query(VendorAssignment).all()


@router.get("/vendor_assignment", response_model=list[AssignmentResponse])
def get_vendor_assignment(
    db: Session = Depends(get_db),
    user=Depends(required_roles(["Vendor"]))
):

    return db.query(VendorAssignment).filter(
        VendorAssignment.vendor_id == user.user_id
    ).all()
