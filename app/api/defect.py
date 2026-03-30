from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from db.dependency import get_db
from models.defect import Defect
from models.vessel import Vessel
from models.vendor_assignment import VendorAssignment
from models.equipment import Equipment
from models.defect_history import DefectHistory

from schemas.defect import DefectCreate, DefectResponse, DefectStatusUpdate
from schemas.defect_history import DefectHistoryResponse
from core.auth import required_roles, get_current_user

from services.history_logger import log_history

router = APIRouter(
    prefix="/defects",
    tags=["Defects"]
)


@router.post("/", response_model=DefectResponse)
def create_defect(
    defect_data: DefectCreate,
    db: Session = Depends(get_db),
    user=Depends(required_roles(["OverseeingTeam"]))
):
    vessel = db.query(Vessel).filter(
        Vessel.vessel_id == defect_data.vessel_id
    ).first()

    equipment = db.query(Equipment).filter(
        Equipment.equipment_id == defect_data.equipment_id
    ).first()

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    if equipment.vessel_id != defect_data.vessel_id:
        raise HTTPException(
            status_code=400, detail="Equipment does not belong to vessel")

    if not vessel:
        raise HTTPException(404, "Vessel not found")

    if vessel.organisation != user.organisation:
        raise HTTPException(403, detail="Not allowed for this vessel")

    new_defect = Defect(
        vessel_id=defect_data.vessel_id,
        equipment_id=defect_data.equipment_id,
        description=defect_data.description,
        status="OPEN",
        created_at=date.today()
    )

    db.add(new_defect)
    db.flush()

    log_history(
        db=db,
        defect_id=new_defect.defect_id,
        user_id=user.user_id,
        action="CREATED"
    )

    db.commit()
    db.refresh(new_defect)

    return new_defect


@router.get("/", response_model=list[DefectResponse])
def get_defects(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    role = user.role.role_name

    query = db.query(Defect)

    if role == "OverseeingTeam":
        query = query.join(Vessel).filter(
            Vessel.organisation == user.organisation
        )

    if role == "Vendor":
        query = query.join(VendorAssignment).filter(
            VendorAssignment.vendor_id == user.user_id
        )

    return query.all()


@router.get("/{defect_id}", response_model=DefectResponse)
def get_defect(
    defect_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    defect = db.query(Defect).filter(
        Defect.defect_id == defect_id
    ).first()

    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")

    role = user.role.role_name

    # ✅ Guarantee Dept → full access
    if role == "GuaranteeDept":
        return defect

    # ✅ Overseeing Team → org-based access
    if role == "OverseeingTeam":
        if defect.vessel.organisation != user.organisation:
            raise HTTPException(status_code=403, detail="Access denied")
        return defect

    # ✅ Vendor → only assigned defects
    if role == "Vendor":

        assignment = db.query(VendorAssignment).filter(
            VendorAssignment.defect_id == defect_id,
            VendorAssignment.vendor_id == user.user_id
        ).first()

        if not assignment:
            raise HTTPException(status_code=403, detail="Not your defect")

        return defect

    raise HTTPException(status_code=403, detail="Not allowed")


@router.patch("/{defect_id}/status")
def update_status(
    defect_id: int,
    data: DefectStatusUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    defect = db.query(Defect).filter(
        Defect.defect_id == defect_id
    ).first()

    if not defect:
        raise HTTPException(404)

    role = user.role.role_name
    new_status = data.status

    # 🔐 Role-based permission
    if new_status == "ASSIGNED" and role != "GuaranteeDept":
        raise HTTPException(403)

    if new_status in ["IN_PROGRESS", "RESOLVED"] and role != "Vendor":
        raise HTTPException(403)

    if new_status in ["ACCEPTED", "REJECTED", "CLOSED"] and role != "GuaranteeDept":
        raise HTTPException(403)

    old_status = defect.status
    defect.status = new_status
    db.flush()

    log_history(
        db=db,
        defect_id=defect.defect_id,
        user_id=user.user_id,
        action="STATUS_UPDATE",
        old_value=old_status,
        new_value=new_status
    )

    db.commit()

    return {"message": "Status updated"}


@router.get("/{defect_id}/history", response_model=list[DefectHistoryResponse])
def get_history(
    defect_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    defect = db.query(Defect).filter(
        Defect.defect_id == defect_id
    ).first()

    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")

    role = user.role.role_name

    # Guarantee Dept → full access
    if role == "GuaranteeDept":
        pass

    # Overseeing Team → org-based access
    elif role == "OverseeingTeam":
        if defect.vessel.organisation != user.organisation:
            raise HTTPException(status_code=403, detail="Access denied")

    # Vendor → only assigned defects
    elif role == "Vendor":
        assignment = db.query(VendorAssignment).filter(
            VendorAssignment.defect_id == defect_id,
            VendorAssignment.vendor_id == user.user_id
        ).first()

        if not assignment:
            raise HTTPException(status_code=403, detail="Not your defect")

    else:
        raise HTTPException(status_code=403, detail="Not allowed")

    history = db.query(DefectHistory).filter(
        DefectHistory.defect_id == defect_id
    ).order_by(DefectHistory.timestamp.desc()).all()

    return history
