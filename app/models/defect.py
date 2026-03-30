from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from db.base_class import Base


class Defect(Base):
    __tablename__ = "defect"

    defect_id = Column(Integer, primary_key=True, index=True)

    vessel_id = Column(Integer, ForeignKey("vessel.vessel_id"))
    equipment_id = Column(Integer, ForeignKey("equipment.equipment_id"))

    description = Column(String(255))
    status = Column(String(30))
    created_at = Column(Date)
    cost_to_shipyard = Column(Integer)
    date_of_liquidation = Column(Date)

    vessel = relationship("Vessel")
    equipment = relationship("Equipment")
