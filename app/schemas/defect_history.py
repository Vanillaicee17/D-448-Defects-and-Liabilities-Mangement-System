from pydantic import BaseModel
from datetime import datetime


class DefectHistoryResponse(BaseModel):
    history_id: int
    defect_id: int
    changed_by: int
    action: str
    old_value: str
    new_value: str
    timestamp: datetime

    class Config:
        from_attributes = True
