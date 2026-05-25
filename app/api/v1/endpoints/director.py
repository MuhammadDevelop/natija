from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_director_or_above, get_current_user
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserDetail
from app.schemas.course import CourseCreate, CourseUpdate, CourseResponse, GroupCreate, GroupUpdate, GroupResponse
from app.schemas.finance import (
    PaymentCreate, PaymentUpdate, PaymentResponse,
    SalaryCreate, SalaryUpdate, SalaryResponse, FinanceSummary
)
from app.services.user_service import user_service
from app.services.course_service import course_service, group_service, finance_service
from app.core.exceptions import PermissionDeniedException

router = APIRouter()


# ─── Dashboard Statistika ─────────────────────────────────────
@router.get("/dashboard", summary="Director bosh sahifasi statistikasi")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    """Director uchun umumiy statistika."""
    teachers = user_service.get_all(db, role=UserRole.TEACHER)
    students = user_service.get_all(db, role=UserRole.STUDENT)
    courses = course_service.get_all(db)
    groups = group_service.get_all(db)

    from datetime import datetime
    current_month = datetime.utcnow().strftime("%Y-%m")
    finance_summary = finance_service.get_monthly_summary(db, current_month)

    return {
        "teachers_count": len(teachers),
        "students_count": len(students),
        "courses_count": len(courses),
        "groups_count": len(groups),
        "finance": finance_summary,
    }


# ─── Teacher CRUD ─────────────────────────────────────────────
@router.get("/teachers", response_model=List[UserResponse], summary="O'qituvchilar ro'yxati")
def list_teachers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return user_service.get_all(db, role=UserRole.TEACHER, skip=skip, limit=limit)


@router.post("/teachers", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="O'qituvchi qo'shish")
def create_teacher(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    # Faqat TEACHER roli qo'shilishi mumkin
    user_in.role = UserRole.TEACHER
    return user_service.create(db, user_in, created_by=current_user.id)


@router.get("/teachers/{teacher_id}", response_model=UserDetail, summary="O'qituvchi ma'lumotlari")
def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    teacher = user_service.get_by_id(db, teacher_id)
    if teacher.role != UserRole.TEACHER:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="O'qituvchi topilmadi")
    return teacher


@router.put("/teachers/{teacher_id}", response_model=UserResponse, summary="O'qituvchini yangilash")
def update_teacher(
    teacher_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return user_service.update(db, teacher_id, user_in)


@router.delete("/teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT, summary="O'qituvchini o'chirish")
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    user_service.delete(db, teacher_id)


@router.patch("/teachers/{teacher_id}/toggle-active", response_model=UserResponse, summary="Faollikni o'zgartirish")
def toggle_teacher_active(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return user_service.toggle_active(db, teacher_id)


# ─── Kurs boshqaruvi ─────────────────────────────────────────
@router.get("/courses", response_model=List[CourseResponse], summary="Kurslar ro'yxati")
def list_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return course_service.get_all(db)


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED, summary="Kurs yaratish")
def create_course(
    course_in: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return course_service.create(db, course_in)


@router.put("/courses/{course_id}", response_model=CourseResponse, summary="Kursni yangilash")
def update_course(
    course_id: int,
    course_in: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return course_service.update(db, course_id, course_in)


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Kursni o'chirish")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    course_service.delete(db, course_id)


# ─── Guruh boshqaruvi ─────────────────────────────────────────
@router.get("/groups", response_model=List[GroupResponse], summary="Guruhlar ro'yxati")
def list_groups(
    course_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return group_service.get_all(db, course_id=course_id)


@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED, summary="Guruh yaratish")
def create_group(
    group_in: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return group_service.create(db, group_in)


@router.put("/groups/{group_id}", response_model=GroupResponse, summary="Guruhni yangilash")
def update_group(
    group_id: int,
    group_in: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return group_service.update(db, group_id, group_in)


# ─── Moliyaviy boshqaruv ──────────────────────────────────────
@router.get("/finance/summary", response_model=FinanceSummary, summary="Oylik moliyaviy hisobot")
def finance_summary(
    month: str = Query(..., description="YYYY-MM formatida, masalan: 2024-05"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return finance_service.get_monthly_summary(db, month)


@router.get("/finance/payments", response_model=List[PaymentResponse], summary="To'lovlar ro'yxati")
def list_payments(
    student_id: Optional[int] = Query(None),
    month: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return finance_service.get_payments(db, student_id=student_id, month=month)


@router.post("/finance/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED, summary="To'lov qo'shish")
def create_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return finance_service.create_payment(db, payment_in, received_by=current_user.id)


@router.put("/finance/payments/{payment_id}", response_model=PaymentResponse, summary="To'lovni yangilash")
def update_payment(
    payment_id: int,
    payment_in: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return finance_service.update_payment(db, payment_id, payment_in)


@router.get("/finance/salaries", response_model=List[SalaryResponse], summary="Oyliklar ro'yxati")
def list_salaries(
    teacher_id: Optional[int] = Query(None),
    month: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return finance_service.get_salaries(db, teacher_id=teacher_id, month=month)


@router.post("/finance/salaries", response_model=SalaryResponse, status_code=status.HTTP_201_CREATED, summary="Oylik tayinlash")
def create_salary(
    salary_in: SalaryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return finance_service.create_salary(db, salary_in)


@router.put("/finance/salaries/{salary_id}", response_model=SalaryResponse, summary="Oylikni yangilash (bonus/jarima)")
def update_salary(
    salary_id: int,
    salary_in: SalaryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_director_or_above),
):
    return finance_service.update_salary(db, salary_id, salary_in)
