from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Numeric, Text
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class Course(Base):
    """O'quv kursi."""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False, default=0)
    duration_months = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    teacher = relationship("User", foreign_keys=[teacher_id])
    groups = relationship("Group", back_populates="course")


class Group(Base):
    """Kurs guruhi."""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    schedule = Column(String(255), nullable=True)
    max_students = Column(Integer, default=20)
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    course = relationship("Course", back_populates="groups")
    students = relationship("GroupStudent", back_populates="group")
    attendances = relationship("Attendance", back_populates="group")


class GroupStudent(Base):
    """Guruh va talaba bog'lanishi."""
    __tablename__ = "group_students"

    id = Column(Integer, primary_key=True, index=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    group = relationship("Group", back_populates="students")
    student = relationship("User", foreign_keys=[student_id])
