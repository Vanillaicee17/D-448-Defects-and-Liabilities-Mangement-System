from sqlalchemy import Column, Integer, String
from db.base_class import Base


class Role(Base):
    __tablename__ = "role"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(100))
    description = Column(String(255))
