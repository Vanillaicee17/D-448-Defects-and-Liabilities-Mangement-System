from sqlalchemy import Column, Integer, String, Date
from db.base_class import Base


class Vendor(Base):
    __tablename__ = "vendor"

    vendor_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True)
    phone = Column(String(100), unique=True)
    address = Column(String(255))
    created_at = Column(Date)
