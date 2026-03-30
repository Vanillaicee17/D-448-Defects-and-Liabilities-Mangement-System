from sqlalchemy import Column, Integer, String, Date
from db.base_class import Base


class Vessel(Base):
    __tablename__ = "vessel"

    vessel_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    series_name = Column(String(100))
    shipyard_yard_number = Column(Integer)
    delivery_date = Column(Date)
    status = Column(String(100))
    date_till_guarantee_period = Column(Date)
    organisation = Column(String(100), nullable=False)
