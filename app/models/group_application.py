import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum as SAEnum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.user import Subject


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    GROUPED = "grouped"
    REJECTED = "rejected"


class GroupApplication(Base):
    """Student application for a specific subject and level."""
    __tablename__ = "group_applications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(SAEnum(Subject), nullable=False)
    level = Column(String(50), nullable=False)  # masalan: beginner, intermediate, advanced, html_css, ielts
    status = Column(SAEnum(ApplicationStatus), default=ApplicationStatus.PENDING, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
