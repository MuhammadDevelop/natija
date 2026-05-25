from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.task import TaskType


class TaskBase(BaseModel):
    group_id: int
    title: str
    description: Optional[str] = None
    type: TaskType = TaskType.HOMEWORK
    max_score: int = 100
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[TaskType] = None
    max_score: Optional[int] = None
    due_date: Optional[datetime] = None


class TaskResponse(TaskBase):
    id: int
    teacher_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class StudentTaskGrade(BaseModel):
    score: int
    feedback: Optional[str] = None


class StudentTaskResponse(BaseModel):
    id: int
    task_id: int
    student_id: int
    score: Optional[int] = None
    feedback: Optional[str] = None
    submitted_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None
    graded_by: Optional[int] = None

    class Config:
        from_attributes = True
