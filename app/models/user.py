from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.base_class import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    password_hash = Column(String)
    email = Column(String(100), unique=True)
    organisation = Column(String(100), unique=True)

    role_id = Column(Integer, ForeignKey("role.role_id"))
    role = relationship("Role")
