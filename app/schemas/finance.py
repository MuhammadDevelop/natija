from typing import Optional
from datetime import datetime
from decimal import Decimal
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
from app.models.finance import PaymentStatus, PaymentType


# ─── Payment Schemas ─────────────────────────────────────────
class PaymentBase(BaseModel):
    amount: Decimal
    month: str  # "YYYY-MM" format
    status: PaymentStatus = PaymentStatus.PENDING
    payment_type: Optional[PaymentType] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    student_id: int
    course_id: Optional[int] = None


class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    payment_type: Optional[PaymentType] = None
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None


class PaymentResponse(PaymentBase):
    id: int
    student_id: int
    course_id: Optional[int] = None
    paid_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Salary Schemas ──────────────────────────────────────────
class SalaryBase(BaseModel):
    amount: Decimal
    month: str
    bonus: Decimal = Decimal("0")
    fine: Decimal = Decimal("0")
    notes: Optional[str] = None


class SalaryCreate(SalaryBase):
    teacher_id: int


class SalaryUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    bonus: Optional[Decimal] = None
    fine: Optional[Decimal] = None
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None


class SalaryResponse(SalaryBase):
    id: int
    teacher_id: int
    status: PaymentStatus
    paid_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Finance Summary ─────────────────────────────────────────
class FinanceSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    pending_payments: int
    overdue_payments: int
