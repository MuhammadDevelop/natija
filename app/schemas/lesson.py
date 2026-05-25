from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LessonBase(BaseModel):
    group_id: int
    topic: str
    description: Optional[str] = None
    date: datetime


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    topic: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None


class LessonResponse(LessonBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
