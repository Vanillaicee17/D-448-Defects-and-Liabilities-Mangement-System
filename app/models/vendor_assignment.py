from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from db.base_class import Base


class VendorAssignment(Base):
    __tablename__ = "vendor_assignment"

    assignment_id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendor.vendor_id"))

    defect_id = Column(Integer, ForeignKey("defect.defect_id"))
    vessel_id = Column(Integer, ForeignKey("vessel.vessel_id"))
    assigned_by = Column(Integer, ForeignKey("users.user_id"))

    assignment_date = Column(Date)
    status = Column(String(100))

    defect = relationship("Defect")
    vessel = relationship("Vessel")
