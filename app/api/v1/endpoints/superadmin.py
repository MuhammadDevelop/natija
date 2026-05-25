from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.api.deps import get_superadmin
from app.models.user import User, UserRole
from app.models.course import Course, Group
from app.models.finance import Payment, PaymentStatus
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserDetail
from app.services.user_service import user_service
from app.core.exceptions import PermissionDeniedException

router = APIRouter()


# ─── Platforma Statistikasi ──────────────────────────────────
@router.get("/stats", summary="Platforma umumiy statistikasi")
def platform_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_superadmin),
):
    """SuperAdmin uchun butun platforma bo'yicha statistika."""
    directors = db.query(User).filter(User.role == UserRole.DIRECTOR).count()
    teachers = db.query(User).filter(User.role == UserRole.TEACHER).count()
    students = db.query(User).filter(User.role == UserRole.STUDENT).count()
    reception = db.query(User).filter(User.role == UserRole.RECEPTION).count()
    courses = db.query(Course).count()
    groups = db.query(Group).count()

    total_income = db.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatus.PAID
    ).scalar() or 0

    active_users = db.query(User).filter(
        User.is_active == True,
        User.role != UserRole.SUPERADMIN
    ).count()

    blocked_users = db.query(User).filter(
        User.is_active == False
    ).count()

    return {
        "users": {
            "directors": directors,
            "teachers": teachers,
            "students": students,
            "reception": reception,
            "active": active_users,
            "blocked": blocked_users,
        },
        "courses": courses,
        "groups": groups,
        "total_income_all_time": float(total_income),
    }


# ─── Direktorlar CRUD ─────────────────────────────────────────
@router.get(
    "/directors",
    response_model=List[UserResponse],
    summary="Barcha direktorlar ro'yxati",
)
def list_directors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_superadmin),
):
    """Tizimda ro'yxatdan o'tgan barcha direktorlar."""
    return user_service.get_all(db, role=UserRole.DIRECTOR)


@router.post(
    "/directors",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi direktor yaratish",
)
def create_director(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_superadmin),
):
    """
    SuperAdmin tomonidan yangi direktor hisobi yaratiladi.
    Faqat DIRECTOR roli biriktirilishi mumkin.
    """
    # Xavfsizlik: faqat DIRECTOR roli yaratilishi mumkin
    if user_in.role not in (UserRole.DIRECTOR, None):
        raise PermissionDeniedException(
            "SuperAdmin faqat DIRECTOR roli yarata oladi"
        )
    user_in.role = UserRole.DIRECTOR
    return user_service.create(db, user_in, created_by=current_user.id)


@router.get(
    "/directors/{director_id}",
    response_model=UserDetail,
    summary="Direktor ma'lumotlari",
)
def get_director(
    director_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_superadmin),
):
    director = user_service.get_by_id(db, director_id)
    if director.role != UserRole.DIRECTOR:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Direktor topilmadi")
    return director


@router.put(
    "/directors/{director_id}",
    response_model=UserResponse,
    summary="Direktorn ma'lumotlarini yangilash",
)
def update_director(
    director_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_superadmin),
):
    director = user_service.get_by_id(db, director_id)
    if director.role != UserRole.DIRECTOR:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Direktor topilmadi")
    return user_service.update(db, director_id, user_in)


@router.delete(
    "/directors/{director_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Direktorn o'chirish",
)
def delete_director(
    director_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_superadmin),
):
    director = user_service.get_by_id(db, director_id)
    if director.role != UserRole.DIRECTOR:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Direktor topilmadi")
    user_service.delete(db, director_id)


@router.patch(
    "/directors/{director_id}/toggle-active",
    response_model=UserResponse,
    summary="Direktorn bloklash / faollashtirish",
)
def toggle_director_active(
    director_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_superadmin),
):
    """Direktorn hisobini bloklash yoki faollashtirish."""
    director = user_service.get_by_id(db, director_id)
    if director.role != UserRole.DIRECTOR:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Direktor topilmadi")
    return user_service.toggle_active(db, director_id)


# ─── Barcha foydalanuvchilarni ko'rish ───────────────────────
@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="Barcha foydalanuvchilar (rol bo'yicha filter)",
)
def list_all_users(
    role: UserRole = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_superadmin),
):
    """SuperAdmin barcha rollar bo'yicha foydalanuvchilarni ko'rishi mumkin."""
    return user_service.get_all(db, role=role)
