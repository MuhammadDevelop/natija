from typing import Optional, List
from datetime import datetime
from decimal import Decimal
# pyrefly: ignore [missing-import]
from pydantic import BaseModel


# ─── Course Schemas ──────────────────────────────────────────
class CourseBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal = Decimal("0")
    duration_months: int = 3
    is_active: bool = True


class CourseCreate(CourseBase):
    teacher_id: Optional[int] = None


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    duration_months: Optional[int] = None
    is_active: Optional[bool] = None
    teacher_id: Optional[int] = None


class CourseResponse(CourseBase):
    id: int
    teacher_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Group Schemas ───────────────────────────────────────────
class GroupBase(BaseModel):
    name: str
    schedule: Optional[str] = None
    max_students: int = 20
    is_active: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ReceptionGroupCreate(BaseModel):
    name: str
    subject: str
    teacher_id: int
    days: List[str]
    start_time: str
    end_time: str
    max_students: int = 20


class GroupCreate(GroupBase):
    course_id: int


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    schedule: Optional[str] = None
    max_students: Optional[int] = None
    is_active: Optional[bool] = None


class GroupResponse(GroupBase):
    id: int
    course_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class GroupWithStudents(GroupResponse):
    student_count: int = 0
