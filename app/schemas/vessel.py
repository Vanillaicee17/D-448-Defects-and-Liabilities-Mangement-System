from pydantic import BaseModel, field_validator
from datetime import date


class VesselCreate(BaseModel):
    series_name: str
    shipyard_yard_number: int
    delivery_date: date
    status: str
    date_till_guarantee_period: date
    organisation: str

    @field_validator("date_till_guarantee_period")
    def validation_dates(cls, v, values):

        delivery_date = values.data.get("delivery_date")
        if delivery_date and v < delivery_date:
            raise ValueError("Guarantee period must be after delivery date")
        return v


class VesselResponse(VesselCreate):
    vessel_id: int

    class Config:
        from_attributes = True
