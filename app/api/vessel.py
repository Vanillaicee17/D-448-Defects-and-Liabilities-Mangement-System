from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.dependency import get_db
from models.vessel import Vessel
from schemas.vessel import VesselCreate, VesselResponse

from core.auth import required_roles, get_current_user

router = APIRouter(
    prefix="/vessels",
    tags=["Vessels"]
)


@router.post("/", response_model=VesselResponse)
def create_vessel(
    vessel_data: VesselCreate,
    db: Session = Depends(get_db),
    user=Depends(required_roles(["GuaranteeDept"]))
):
    new_vessel = Vessel(
        series_name=vessel_data.series_name,
        shipyard_yard_number=vessel_data.shipyard_yard_number,
        delivery_date=vessel_data.delivery_date,
        status=vessel_data.status,
        date_till_guarantee_period=vessel_data.date_till_guarantee_period,
        organisation=vessel_data.organisation
    )

    db.add(new_vessel)
    db.commit()
    db.refresh(new_vessel)

    return new_vessel


@router.get("/", response_model=list[VesselResponse])
def get_vessels(
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    role = user.role.role_name

    if not user.organisation:
        raise HTTPException(400, "User has no organisation assigned")

    if role == "GuaranteeDept":
        return db.query(Vessel).all()

    if role == "OverseeingTeam":
        return db.query(Vessel).filter(
            Vessel.organisation == user.organisation
        ).all()

    raise HTTPException(status_code=403, detail="Not Allowed")


@router.get("/{vessel_id}", response_model=VesselResponse)
def get_vessel(
    vessel_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    vessel = db.query(Vessel).filter(
        Vessel.vessel_id == vessel_id
    ).first()

    if not vessel:
        raise HTTPException(status_code=404, detail=" Vessel not found")

    role = user.role.role_name
    if role == "GuaranteeDept":
        return vessel

    if role == "Overseeing Team":
        if vessel.organisation != user.organisation:
            raise HTTPException(status_code=403, detail="Access denied")

        return vessel

    raise HTTPException(status_code=403, detail="Not allowed")
