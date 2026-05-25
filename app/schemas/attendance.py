from typing import Optional, List
from datetime import datetime
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from app.models.attendance import AttendanceStatus


class AttendanceBase(BaseModel):
    date: datetime
    status: AttendanceStatus = AttendanceStatus.PRESENT
    notes: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    student_id: int
    group_id: int


class AttendanceBulkCreate(BaseModel):
    """Bir guruh uchun bir nechta davomat yozuvi."""
    group_id: int
    date: datetime
    records: List[dict]  # [{"student_id": 1, "status": "present"}]


class AttendanceUpdate(BaseModel):
    status: Optional[AttendanceStatus] = None
    notes: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    id: int
    student_id: int
    group_id: int
    marked_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceSummary(BaseModel):
    total: int
    present: int
    absent: int
    late: int
    excused: int
    percentage: float
