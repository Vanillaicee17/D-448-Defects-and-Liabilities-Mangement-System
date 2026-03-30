from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    defect_id: int
    vendor_id: int


class AssignmentResponse(BaseModel):
    assignment_id: int
    defect_id: int
    vendor_id: int
    assigned_by: int

    class Config:
        from_attributes = True
