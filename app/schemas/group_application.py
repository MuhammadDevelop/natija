from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.models.user import Subject, UserRole
from app.models.group_application import ApplicationStatus


class StudentShortInfo(BaseModel):
    id: int
    full_name: str
    phone: str

    class Config:
        from_attributes = True


class GroupApplicationBase(BaseModel):
    subject: Subject
    level: str
    notes: Optional[str] = None


class GroupApplicationCreate(GroupApplicationBase):
    pass


class GroupApplicationUpdateStatus(BaseModel):
    status: ApplicationStatus
    notes: Optional[str] = None


class GroupApplicationResponse(GroupApplicationBase):
    id: int
    student_id: int
    status: ApplicationStatus
    created_at: datetime
    student: Optional[StudentShortInfo] = None

    class Config:
        from_attributes = True


class GroupCreateFromApplications(BaseModel):
    name: str
    schedule: Optional[str] = None
    max_students: Optional[int] = 20
    application_ids: list[int]
    course_id: int
