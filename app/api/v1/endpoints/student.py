from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.attendance import Attendance
from app.models.task import Task, StudentTask
from app.models.bonus import StudentBonus
from app.models.finance import Payment
from app.models.course import GroupStudent
from app.schemas.user import UserResponse, UserUpdate
from app.core.exceptions import PermissionDeniedException
from app.core.security import get_password_hash

router = APIRouter()


def require_student(current_user: User) -> User:
    """O'quvchi ekanligini tekshiradi."""
    if current_user.role != UserRole.STUDENT:
        raise PermissionDeniedException("Bu bo'lim faqat o'quvchilar uchun")
    return current_user


# ─── Profil ───────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse, summary="O'z profili")
def my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """O'quvchi o'z shaxsiy ma'lumotlarini ko'radi."""
    require_student(current_user)
    return current_user


@router.put("/me", response_model=UserResponse, summary="Profilni yangilash")
def update_profile(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """O'quvchi faqat o'z profilini (ism, parol) yangilay oladi."""
    require_student(current_user)

    # Ruxsat etilgan maydonlar: faqat full_name va password
    allowed = {}
    if user_in.full_name:
        allowed["full_name"] = user_in.full_name
    if user_in.password:
        if len(user_in.password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Parol kamida 6 ta belgidan iborat bo'lishi kerak"
            )
        allowed["hashed_password"] = get_password_hash(user_in.password)

    for key, value in allowed.items():
        setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)
    return current_user


# ─── Guruhlar ─────────────────────────────────────────────────
@router.get("/my-groups", summary="O'qiyotgan guruhlar")
def my_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """O'quvchi o'qiyotgan barcha faol guruhlar."""
    require_student(current_user)

    memberships = db.query(GroupStudent).filter(
        GroupStudent.student_id == current_user.id,
        GroupStudent.is_active == True,
    ).all()

    result = []
    for m in memberships:
        g = m.group
        result.append({
            "group_id": g.id,
            "group_name": g.name,
            "schedule": g.schedule,
            "start_date": g.start_date,
            "end_date": g.end_date,
            "course_name": g.course.name if g.course else None,
            "teacher_name": (
                g.course.teacher.full_name
                if g.course and g.course.teacher
                else "Belgilanmagan"
            ),
            "joined_at": m.joined_at,
        })
    return result


# ─── Davomat ──────────────────────────────────────────────────
@router.get("/attendance", summary="O'z davomat tarixi")
def my_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """O'quvchi o'zining davomat tarixini ko'radi."""
    require_student(current_user)

    records = db.query(Attendance).filter(
        Attendance.student_id == current_user.id
    ).order_by(Attendance.date.desc()).all()

    total = len(records)
    present = sum(1 for r in records if r.status == "present")
    absent = sum(1 for r in records if r.status == "absent")
    late = sum(1 for r in records if r.status == "late")

    return {
        "summary": {
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "attendance_rate": round(present / total * 100, 1) if total > 0 else 0,
        },
        "records": [
            {
                "id": r.id,
                "date": r.date,
                "status": r.status,
                "notes": r.notes,
                "group_id": r.group_id,
            }
            for r in records
        ],
    }


# ─── Vazifalar va Baholar ─────────────────────────────────────
@router.get("/tasks", summary="Menga berilgan vazifalar")
def my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """O'quvchi o'ziga berilgan barcha vazifalar va baholarni ko'radi."""
    require_student(current_user)

    student_tasks = db.query(StudentTask).filter(
        StudentTask.student_id == current_user.id
    ).all()

    result = []
    for st in student_tasks:
        task = st.task
        result.append({
            "student_task_id": st.id,
            "task_title": task.title if task else None,
            "task_type": task.task_type if task else None,
            "max_score": task.max_score if task else None,
            "deadline": task.deadline if task else None,
            "score": st.score,
            "feedback": st.feedback,
            "graded_at": st.graded_at,
            "is_graded": st.graded_at is not None,
            "group_id": task.group_id if task else None,
        })
    return result


@router.get("/grades/summary", summary="Baho xulosasi")
def grades_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """O'quvchi o'rtacha baho va umumiy statistikasini ko'radi."""
    require_student(current_user)

    graded_tasks = db.query(StudentTask).filter(
        StudentTask.student_id == current_user.id,
        StudentTask.score != None,
    ).all()

    if not graded_tasks:
        return {
            "total_tasks": 0,
            "graded_tasks": 0,
            "average_score": 0,
            "average_percent": 0,
        }

    total_score = sum(st.score for st in graded_tasks if st.score is not None)
    total_max = sum(
        st.task.max_score for st in graded_tasks
        if st.task and st.task.max_score
    )

    return {
        "total_tasks": db.query(StudentTask).filter(
            StudentTask.student_id == current_user.id
        ).count(),
        "graded_tasks": len(graded_tasks),
        "average_score": round(total_score / len(graded_tasks), 2),
        "average_percent": round(
            total_score / total_max * 100, 1
        ) if total_max > 0 else 0,
    }


# ─── Bonus Ballar ─────────────────────────────────────────────
@router.get("/bonuses", summary="Bonus ballarim")
def my_bonuses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """O'quvchi o'zining bonus ballar tarixini ko'radi."""
    require_student(current_user)

    bonuses = db.query(StudentBonus).filter(
        StudentBonus.student_id == current_user.id
    ).order_by(StudentBonus.created_at.desc()).all()

    total_points = sum(b.points for b in bonuses)

    return {
        "total_points": total_points,
        "bonuses": [
            {
                "id": b.id,
                "points": b.points,
                "reason": b.reason,
                "created_at": b.created_at,
            }
            for b in bonuses
        ],
    }


# ─── To'lovlar holati ─────────────────────────────────────────
@router.get("/payments", summary="To'lovlarim holati")
def my_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """O'quvchi o'zining to'lovlar tarixini va holatini ko'radi."""
    require_student(current_user)

    payments = db.query(Payment).filter(
        Payment.student_id == current_user.id
    ).order_by(Payment.created_at.desc()).all()

    return [
        {
            "id": p.id,
            "amount": float(p.amount),
            "month": p.month,
            "status": p.status,
            "payment_type": p.payment_type,
            "paid_at": p.paid_at,
            "notes": p.notes,
        }
        for p in payments
    ]
