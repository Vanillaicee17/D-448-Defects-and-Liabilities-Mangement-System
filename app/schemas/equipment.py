from pydantic import BaseModel


# 🔹 Create equipment TYPE
class EquipmentTypeCreate(BaseModel):
    name: str
    manufacturer: str
    model_no: str


class EquipmentTypeResponse(BaseModel):
    equipment_type_id: int
    name: str
    manufacturer: str
    model_no: str

    class Config:
        from_attributes = True


# 🔹 Create equipment INSTANCE
class EquipmentCreate(BaseModel):
    vessel_id: int
    vendor_id: int
    equipment_type_id: int
    serial_no: str


class EquipmentResponse(BaseModel):
    equipment_id: int
    vessel_id: int
    vendor_id: int
    equipment_type_id: int
    serial_no: str

    class Config:
        from_attributes = True
