from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BonusCreate(BaseModel):
    student_id: int
    points: int
    reason: Optional[str] = None


class BonusResponse(BaseModel):
    id: int
    student_id: int
    teacher_id: int
    points: int
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
