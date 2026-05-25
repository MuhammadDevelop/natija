from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MaterialBase(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    link_url: Optional[str] = None


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    file_url: Optional[str] = None
    link_url: Optional[str] = None


class MaterialResponse(MaterialBase):
    id: int
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True
