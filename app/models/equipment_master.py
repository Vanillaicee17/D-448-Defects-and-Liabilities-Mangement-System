from db.base_class import Base
from sqlalchemy import Column, Integer, String


class EquipmentMaster(Base):
    __tablename__ = "equipment_master"

    equipment_type_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    manufacturer = Column(String(100))
    model_no = Column(String(100))
