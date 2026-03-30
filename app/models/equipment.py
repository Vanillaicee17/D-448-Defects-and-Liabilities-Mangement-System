from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.base_class import Base


class Equipment(Base):
    __tablename__ = "equipment"

    equipment_id = Column(Integer, primary_key=True, index=True)
    equipment_type_id = Column(
        Integer, ForeignKey("equipment_master.equipment_type_id"))

    vessel_id = Column(Integer, ForeignKey("vessel.vessel_id"))
    vendor_id = Column(Integer, ForeignKey("vendor.vendor_id"))
    serial_no = Column(String(100))

    vessel = relationship("Vessel")
    vendor = relationship("Vendor")
    equipment_type = relationship("EquipmentMaster")
