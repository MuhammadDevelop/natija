from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_reception_or_above
from app.models.user import User, UserRole
from app.models.course import Group, GroupStudent
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.course import GroupResponse
from app.schemas.finance import PaymentCreate, PaymentUpdate, PaymentResponse
from app.services.user_service import user_service
from app.services.course_service import group_service, finance_service
from app.core.exceptions import PermissionDeniedException, NotFoundException

router = APIRouter()


# ─── Talabalar boshqaruvi ─────────────────────────────────────
@router.get(
    "/students",
    response_model=List[UserResponse],
    summary="O'quvchilar ro'yxati",
)
def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    """Tizimda ro'yxatdan o'tgan barcha o'quvchilar."""
    return user_service.get_all(
        db, role=UserRole.STUDENT, skip=skip, limit=limit
    )


@router.post(
    "/students",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi o'quvchi ro'yxatdan o'tkazish",
)
def register_student(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    """
    Reception tomonidan yangi talaba ro'yxatga olinadi.
    Faqat STUDENT roli biriktirilishi mumkin.
    """
    user_in.role = UserRole.STUDENT
    return user_service.create(db, user_in, created_by=current_user.id)


@router.get(
    "/students/{student_id}",
    response_model=UserResponse,
    summary="O'quvchi ma'lumotlari",
)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    student = user_service.get_by_id(db, student_id)
    if student.role != UserRole.STUDENT:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    return student


@router.put(
    "/students/{student_id}",
    response_model=UserResponse,
    summary="O'quvchi ma'lumotlarini yangilash",
)
def update_student(
    student_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    student = user_service.get_by_id(db, student_id)
    if student.role != UserRole.STUDENT:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    return user_service.update(db, student_id, user_in)


@router.patch(
    "/students/{student_id}/toggle-active",
    response_model=UserResponse,
    summary="O'quvchi holatini o'zgartirish",
)
def toggle_student_active(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    student = user_service.get_by_id(db, student_id)
    if student.role != UserRole.STUDENT:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    return user_service.toggle_active(db, student_id)


# ─── Guruhga yozish ───────────────────────────────────────────
@router.post(
    "/students/{student_id}/enroll/{group_id}",
    status_code=status.HTTP_201_CREATED,
    summary="O'quvchini guruhga yozish",
)
def enroll_student(
    student_id: int,
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    """O'quvchini muayyan guruhga ro'yxatga olish."""
    student = user_service.get_by_id(db, student_id)
    if student.role != UserRole.STUDENT:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")

    group = group_service.get_by_id(db, group_id)

    # Guruh to'liq emasligini tekshirish
    student_count = group_service.get_student_count(db, group_id)
    if student_count >= group.max_students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Guruh to'liq ({student_count}/{group.max_students} o'rin)"
        )

    gs = group_service.add_student(db, group_id=group_id, student_id=student_id)
    return {
        "message": "O'quvchi guruhga muvaffaqiyatli qo'shildi",
        "student_id": student_id,
        "group_id": group_id,
        "group_name": group.name,
        "joined_at": gs.joined_at,
    }


@router.delete(
    "/students/{student_id}/unenroll/{group_id}",
    status_code=status.HTTP_200_OK,
    summary="O'quvchini guruhdan chiqarish",
)
def unenroll_student(
    student_id: int,
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    """O'quvchini guruhdan chiqarish (is_active = False)."""
    gs = db.query(GroupStudent).filter(
        GroupStudent.student_id == student_id,
        GroupStudent.group_id == group_id,
        GroupStudent.is_active == True,
    ).first()
    if not gs:
        raise HTTPException(
            status_code=404, detail="O'quvchi bu guruhda topilmadi"
        )
    gs.is_active = False
    db.commit()
    return {"message": "O'quvchi guruhdan muvaffaqiyatli chiqarildi"}


# ─── Guruhlar ro'yxati (bo'sh o'rinlar bilan) ────────────────
@router.get(
    "/groups",
    summary="Guruhlar ro'yxati (bo'sh o'rinlar bilan)",
)
def list_groups_with_availability(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    """Barcha guruhlar, har birida qancha bo'sh o'rin qolganligini ko'rish."""
    groups = group_service.get_all(db)
    result = []
    for g in groups:
        student_count = group_service.get_student_count(db, g.id)
        result.append({
            "id": g.id,
            "name": g.name,
            "schedule": g.schedule,
            "max_students": g.max_students,
            "enrolled_students": student_count,
            "available_spots": max(0, g.max_students - student_count),
            "is_full": student_count >= g.max_students,
            "is_active": g.is_active,
            "start_date": g.start_date,
            "end_date": g.end_date,
            "course_name": g.course.name if g.course else None,
            "teacher_name": (
                g.course.teacher.full_name
                if g.course and g.course.teacher
                else "Biriktirilmagan"
            ),
        })
    return result


# ─── To'lovlar boshqaruvi ─────────────────────────────────────
@router.get(
    "/payments",
    response_model=List[PaymentResponse],
    summary="To'lovlar ro'yxati",
)
def list_payments(
    student_id: Optional[int] = Query(None),
    month: Optional[str] = Query(None, description="YYYY-MM formatida"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    return finance_service.get_payments(
        db, student_id=student_id, month=month
    )


@router.post(
    "/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="To'lov qabul qilish",
)
def accept_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    """Reception tomonidan o'quvchi to'lovi qabul qilinadi."""
    # O'quvchi mavjudligini tekshirish
    student = user_service.get_by_id(db, payment_in.student_id)
    if student.role != UserRole.STUDENT:
        raise HTTPException(status_code=400, detail="Faqat o'quvchi uchun to'lov qabul qilinadi")
    return finance_service.create_payment(
        db, payment_in, received_by=current_user.id
    )


@router.put(
    "/payments/{payment_id}",
    response_model=PaymentResponse,
    summary="To'lovni yangilash",
)
def update_payment(
    payment_id: int,
    payment_in: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    return finance_service.update_payment(db, payment_id, payment_in)
