import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    Enum as SAEnum, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class UserRole(str, enum.Enum):
    SUPERADMIN = "superadmin"
    DIRECTOR = "director"
    RECEPTION = "reception"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"


# 10 ta fan
class Subject(str, enum.Enum):
    PROGRAMMING = "programming"
    ENGLISH = "english"
    MATH = "math"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    HISTORY = "history"
    RUSSIAN = "russian"
    ARABIC = "arabic"
    DESIGN = "design"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.STUDENT)
    subject = Column(SAEnum(Subject), nullable=True)  # O'qituvchi fani
    subject_level = Column(String(50), nullable=True)  # Fan darajasi (masalan: html_css, ielts, beginner)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    face_encoding = Column(Text, nullable=True)  # JSON-encoded array of floats
    face_image = Column(Text, nullable=True)  # Base64 rasm

    # Telegram
    telegram_id = Column(String(50), unique=True, nullable=True)

    # Kim yaratdi
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", remote_side=[id], foreign_keys=[created_by])
    group_applications = relationship("GroupApplication", back_populates="student")
