from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from datetime import datetime, timezone
from db.base_class import Base


class DefectHistory(Base):
    __tablename__ = "defect_history"

    history_id = Column(Integer, primary_key=True, index=True)

    defect_id = Column(Integer, ForeignKey("defect.defect_id"))
    changed_by = Column(Integer, ForeignKey("users.user_id"))

    action = Column(String)
    old_value = Column(String)
    new_value = Column(String)

    timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc))
