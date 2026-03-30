from pydantic import BaseModel


class DefectCreate(BaseModel):
    vessel_id: int
    equipment_id: int
    description: str


class DefectStatusUpdate(BaseModel):
    status: str


class DefectResponse(BaseModel):
    vessel_id: int
    equipment_id: int
    description: str
    status: str

    class Config:
        from_attributes = True
