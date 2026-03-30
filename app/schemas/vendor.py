from pydantic import BaseModel, EmailStr
from typing import Optional


class VendorCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address: str


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class VendorResponse(BaseModel):
    vendor_id: int
    name: str
    email: str
    phone: str
    address: str

    class Config:
        from_attributes = True
