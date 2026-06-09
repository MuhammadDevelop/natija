import math
import json
from typing import Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User, UserRole
from app.models.attendance import Attendance, AttendanceStatus
from app.models.lesson import Lesson
from app.schemas.user import FaceRegistrationRequest
from app.schemas.attendance import FaceVerificationRequest, FaceVerificationResponse

router = APIRouter()

def calculate_squared_distance(enc1: List[float], enc2: List[float]) -> float:
    """Squared Euclidean distance (much faster as it skips sqrt)"""
    if len(enc1) != len(enc2):
        return float('inf')
    return sum((a - b) ** 2 for a, b in zip(enc1, enc2))

@router.post("/register/{student_id}", summary="Talaba uchun Face ID ro'yxatdan o'tkazish")
def register_face(
    student_id: int,
    data: FaceRegistrationRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Frontenddan olingan yuz parametrlari (encoding) ni saqlash.
    """
    if current_user.role not in [UserRole.SUPERADMIN, UserRole.DIRECTOR, UserRole.RECEPTION, UserRole.TEACHER] and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Ruxsat etilmagan")

    student = db.query(User).filter(User.id == student_id, User.role == UserRole.STUDENT).first()
    if not student:
        raise HTTPException(status_code=404, detail="Talaba topilmadi")

    student.face_encoding = json.dumps(data.encoding)
    if data.image_base64:
        student.face_image = data.image_base64
    db.commit()
    return {"message": "Yuz ma'lumotlari muvaffaqiyatli saqlandi"}


@router.post("/verify", response_model=FaceVerificationResponse, summary="Face ID orqali davomat qilish")
def verify_face(
    data: FaceVerificationRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Face ID yordamida guruhdagi talabani aniqlash va davomatini belgilash.
    """
    if current_user.role not in [UserRole.SUPERADMIN, UserRole.DIRECTOR, UserRole.RECEPTION, UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="Faqat xodimlar davomat qila oladi")

    # Tezlik uchun faqatgina aynan shu guruhdagi (group_id) talabalarni bazadan olamiz.
    from app.models.course import GroupStudent
    students = db.query(User).join(GroupStudent, User.id == GroupStudent.student_id).filter(
        GroupStudent.group_id == data.group_id,
        User.face_encoding.isnot(None)
    ).all()
    
    best_match = None
    # Original distance threshold is 0.6, so squared threshold is 0.36
    min_squared_distance = 0.36 
    
    for student in students:
        try:
            saved_encoding = json.loads(student.face_encoding)
            sq_distance = calculate_squared_distance(data.encoding, saved_encoding)
            if sq_distance < min_squared_distance:
                min_squared_distance = sq_distance
                best_match = student
        except Exception:
            continue

    if not best_match:
        return FaceVerificationResponse(matched=False)

    # Davomatni saqlash
    # Bugungi sanada shu guruh uchun dars bormi? Yoki to'g'ridan to'g'ri attendance yozamizmi?
    today = datetime.utcnow().date()
    
    attendance = db.query(Attendance).filter(
        Attendance.student_id == best_match.id,
        Attendance.group_id == data.group_id,
        # Soddalashtirilgan sana tekshiruvi (faqat bugun uchun)
    ).first() # TODO: Bugungi kunligini aniq filtr qilish kerak!
    
    # Keling sodda qilib yangi yozuv qo'shamiz (yoki borini yangilaymiz)
    if not attendance:
        attendance = Attendance(
            date=datetime.utcnow(),
            status=AttendanceStatus.PRESENT,
            student_id=best_match.id,
            group_id=data.group_id,
            marked_by=current_user.id,
            notes="Face ID orqali tasdiqlandi"
        )
        db.add(attendance)
        db.commit()
        db.refresh(attendance)

    return FaceVerificationResponse(
        matched=True,
        student_id=best_match.id,
        student_name=best_match.full_name,
        attendance_id=attendance.id
    )
