from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_reception_or_above
from app.models.user import User, UserRole
from app.models.course import Group, GroupStudent
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.course import GroupResponse, CourseResponse, GroupCreate, CourseCreate
from app.schemas.finance import PaymentCreate, PaymentUpdate, PaymentResponse
from app.services.user_service import user_service
from app.services.course_service import group_service, finance_service, course_service
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

@router.get(
    "/teachers",
    response_model=List[UserResponse],
    summary="O'qituvchilar ro'yxati",
)
def list_teachers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    """Reception guruhga biriktirishi uchun o'qituvchilar ro'yxati."""
    return user_service.get_all(
        db, role=UserRole.TEACHER, skip=skip, limit=limit
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
    user = user_service.create(db, user_in, created_by=current_user.id)
    
    # Talabani avtomat guruhga yoki arizaga qo'shish
    if user_in.subject:
        from app.models.course import Group, Course, GroupStudent
        from app.models.group_application import GroupApplication
        from app.models.user import User as UserModel
        
        # O'sha fanga tegishli bo'sh joyi bor birinchi faol guruhni topamiz
        group = db.query(Group).join(Course).join(UserModel, Course.teacher_id == UserModel.id).filter(
            UserModel.subject == user_in.subject,
            Group.is_active == True
        ).first()

        if group:
            gs = GroupStudent(group_id=group.id, student_id=user.id)
            db.add(gs)
        else:
            app_record = GroupApplication(
                student_id=user.id,
                subject=user_in.subject,
                level=user_in.subject_level or "Boshlang'ich"
            )
            db.add(app_record)
        
        db.commit()

    return user


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
    max_students = group.max_students or 20
    if student_count >= max_students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Guruh to'liq ({student_count}/{max_students} o'rin)"
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


@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED, summary="Guruh yaratish")
def create_group(
    group_in: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    return group_service.create(db, group_in)


@router.get("/courses", response_model=List[CourseResponse], summary="Kurslar ro'yxati")
def list_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    return course_service.get_all(db)


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED, summary="Kurs yaratish")
def create_course(
    course_in: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    return course_service.create(db, course_in)



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


# ─── Guruh Tuzish (Soha va Daraja bo'yicha) ────────────────────
from app.schemas.group_application import GroupApplicationResponse, GroupCreateFromApplications
from app.services.group_application_service import group_application_service
from app.models.group_application import ApplicationStatus
from app.schemas.course import GroupResponse
from app.models.user import Subject

@router.get(
    "/applications",
    response_model=List[GroupApplicationResponse],
    summary="Barcha o'quvchi arizalari ro'yxati",
)
def list_student_applications(
    subject: Optional[Subject] = Query(None, description="Soha bo'yicha filter"),
    level: Optional[str] = Query(None, description="Daraja bo'yicha filter"),
    status: Optional[ApplicationStatus] = Query(ApplicationStatus.PENDING, description="Status bo'yicha filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    """
    Reception barcha talabalarning guruh tuzish arizalarini ko'radi va saralaydi.
    """
    return group_application_service.get_applications(
        db,
        subject=subject,
        level=level,
        status=status
    )


@router.post(
    "/applications/create-group",
    response_model=GroupResponse,
    summary="Tanlangan o'quvchi arizalaridan yangi guruh yaratish",
)
def reception_create_group_from_applications(
    group_in: GroupCreateFromApplications,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    """
    Reception tanlangan arizalar asosida guruh yaratadi va arizalarni tasdiqlaydi.
    """
    return group_application_service.create_group_from_applications(db, group_in)


# ─── Har Oyning 1-sanasida To'lovlarni Yangilash ──────────────
from datetime import datetime

@router.post(
    "/payments/renew-monthly",
    summary="Har oyning 1-sanasida faol o'quvchilar to'lovlarini yangilash",
)
def renew_monthly_payments(
    month: Optional[str] = Query(
        None, 
        description="To'lov yangilanadigan oy (YYYY-MM formatda, masalan: 2026-06). Agar kiritilmasa, joriy oy olinadi."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reception_or_above),
):
    """
    Har oyning 1-sanasida barcha faol guruhlardagi o'quvchilar uchun to'lov yozuvlarini (PENDING) avtomatik/yarim-avtomatik yaratadi.
    """
    if not month:
        month = datetime.utcnow().strftime("%Y-%m")
    
    result = finance_service.renew_monthly_payments(db, month)
    return {
        "status": "success",
        "message": f"{month} oyi uchun to'lovlar yangilandi",
        "details": result
    }

