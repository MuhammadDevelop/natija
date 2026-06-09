from typing import Optional
from datetime import datetime
from pydantic import BaseModel, field_validator
from app.models.user import UserRole, Subject


# ─── Token Schemas ───────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    full_name: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[UserRole] = None


# ─── Login Schemas ───────────────────────────────────────────
class LoginRequest(BaseModel):
    phone: str
    password: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Telefon raqami bo'sh bo'lishi mumkin emas")
        return cleaned


# ─── Register (Foydalanuvchi o'zi ro'yxatdan o'tadi) ──────────────
class RegisterRequest(BaseModel):
    full_name: str
    phone: str
    password: str
    role: Optional[UserRole] = UserRole.STUDENT
    subject: Optional[Subject] = None
    subject_level: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Telefon raqami bo'sh bo'lishi mumkin emas")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Parol kamida 6 ta belgidan iborat bo'lishi kerak")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        allowed = [UserRole.STUDENT, UserRole.DIRECTOR, UserRole.TEACHER, UserRole.RECEPTION]
        if v not in allowed:
            raise ValueError("Bu rol bilan ro'yxatdan o'tib bo'lmaydi")
        return v


# ─── User Base ───────────────────────────────────────────────
class UserBase(BaseModel):
    full_name: str
    phone: str
    role: UserRole
    is_active: bool = True
    notes: Optional[str] = None
    subject: Optional[Subject] = None
    subject_level: Optional[str] = None


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Parol kamida 6 ta belgidan iborat bo'lishi kerak")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    subject: Optional[Subject] = None
    subject_level: Optional[str] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    telegram_id: Optional[str] = None

    class Config:
        from_attributes = True


class UserDetail(UserResponse):
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FaceRegistrationRequest(BaseModel):
    encoding: list[float]  # 128-d yoki 512-d array
    image_base64: str      # Base64 rasm


# ─── Fanlar ro'yxati ─────────────────────────────────────────
SUBJECT_LABELS = {
    "programming": "Dasturlash",
    "english": "Ingliz tili",
    "math": "Matematika",
    "physics": "Fizika",
    "chemistry": "Kimyo",
    "biology": "Biologiya",
    "history": "Tarix",
    "russian": "Rus tili",
    "arabic": "Arab tili",
    "design": "Dizayn",
}
