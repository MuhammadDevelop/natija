from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_teacher_or_above
from app.models.user import User, UserRole
from app.models.attendance import Attendance
from app.schemas.attendance import AttendanceCreate, AttendanceResponse
from app.schemas.lesson import LessonCreate, LessonResponse
from app.schemas.task import TaskCreate, TaskResponse, StudentTaskGrade, StudentTaskResponse
from app.schemas.bonus import BonusCreate, BonusResponse
from app.schemas.material import MaterialCreate, MaterialResponse

from app.services.teacher_service import teacher_service
from app.services.course_service import group_service, course_service
from app.core.exceptions import PermissionDeniedException, NotFoundException

router = APIRouter()


# ─── Xavfsizlik va Data Ownership Tekshiruvi ───────────────────
def verify_group_access(db: Session, group_id: int, current_user: User):
    """O'qituvchi faqat o'ziga biriktirilgan guruhlarni boshqara oladi."""
    group = group_service.get_by_id(db, group_id)
    if current_user.role == UserRole.TEACHER:
        if not group.course or group.course.teacher_id != current_user.id:
            raise PermissionDeniedException("Ruxsat yo'q. Ushbu guruh sizga biriktirilmagan")
    return group


def verify_course_access(db: Session, course_id: int, current_user: User):
    """O'qituvchi faqat o'ziga biriktirilgan kurs materiallarini boshqara oladi."""
    course = course_service.get_by_id(db, course_id)
    if current_user.role == UserRole.TEACHER:
        if course.teacher_id != current_user.id:
            raise PermissionDeniedException("Ruxsat yo'q. Ushbu kurs sizga biriktirilmagan")
    return course


from app.schemas.course import CourseResponse

@router.get("/my-courses", response_model=List[CourseResponse], summary="O'qituvchining kurslari")
def my_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """O'qituvchiga biriktirilgan kurslar ro'yxati."""
    courses = course_service.get_all(db)
    if current_user.role == UserRole.TEACHER:
        return [c for c in courses if c.teacher_id == current_user.id]
    return courses

# ─── Guruhlar (Groups) ────────────────────────────────────────
@router.get("/my-groups", response_model=List[dict], summary="O'qituvchining faol guruhlari")
def my_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """Tizimdagi o'qituvchiga tegishli barcha guruhlar ro'yxati."""
    groups = group_service.get_all(db)
    
    # Agar foydalanuvchi o'qituvchi bo'lsa, faqat o'ziga tegishli guruhlarni filter qilamiz
    if current_user.role == UserRole.TEACHER:
        my_list = [g for g in groups if g.course and g.course.teacher_id == current_user.id]
    else:
        my_list = groups

    result = []
    for g in my_list:
        result.append({
            "id": g.id,
            "name": g.name,
            "schedule": g.schedule,
            "max_students": g.max_students,
            "start_date": g.start_date,
            "end_date": g.end_date,
            "course_id": g.course_id,
            "course_name": g.course.name if g.course else None,
        })
    return result


@router.get("/groups/{group_id}/students", summary="Guruhdagi o'quvchilar ro'yxati")
def group_students(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """Guruhdagi barcha faol o'quvchilar ro'yxati."""
    verify_group_access(db, group_id, current_user)
    
    group = group_service.get_by_id(db, group_id)
    students = []
    for gs in group.students:
        if gs.is_active:
            students.append({
                "student_id": gs.student.id,
                "full_name": gs.student.full_name,
                "phone": gs.student.phone,
                "joined_at": gs.joined_at,
            })
    return students


# ─── Davomat (Attendance) ──────────────────────────────────────
@router.post("/attendance", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED, summary="Davomat belgilash")
def mark_attendance(
    att_in: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """Talaba uchun davomat yozuvini kiritish."""
    verify_group_access(db, att_in.group_id, current_user)
    
    attendance = Attendance(
        date=att_in.date,
        status=att_in.status,
        notes=att_in.notes,
        student_id=att_in.student_id,
        group_id=att_in.group_id,
        marked_by=current_user.id,
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


@router.get("/attendance/group/{group_id}", response_model=List[AttendanceResponse], summary="Guruh davomat tarixi")
def group_attendance(
    group_id: int,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """Guruh davomatini filterlash va ko'rish."""
    verify_group_access(db, group_id, current_user)
    return teacher_service.get_group_attendance(db, group_id, date_from, date_to)


# ─── Dars Jadvali va Mavzular (Lessons) ────────────────────────
@router.post("/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED, summary="Dars va dars mavzusi qo'shish")
def create_lesson(
    lesson_in: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """Dars jadvaliga yangi dars/mavzu qo'shish."""
    verify_group_access(db, lesson_in.group_id, current_user)
    return teacher_service.create_lesson(db, lesson_in)


@router.get("/lessons/group/{group_id}", response_model=List[LessonResponse], summary="Guruh darslar ro'yxati")
def group_lessons(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """Guruhning barcha o'tilgan darslari/jadvali."""
    verify_group_access(db, group_id, current_user)
    return teacher_service.get_lessons_by_group(db, group_id)


# ─── Vazifalar va Baholash (Tasks & Grading) ───────────────────
@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, summary="Yangi vazifa (homework/test) yaratish")
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """Guruh uchun yangi vazifa yaratish (faol o'quvchilarga avtomat topshiriq biriktiriladi)."""
    verify_group_access(db, task_in.group_id, current_user)
    return teacher_service.create_task(db, task_in, teacher_id=current_user.id)


@router.get("/tasks/group/{group_id}", response_model=List[TaskResponse], summary="Guruh vazifalari ro'yxati")
def group_tasks(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """Guruh uchun berilgan vazifalar ro'yxati."""
    verify_group_access(db, group_id, current_user)
    return teacher_service.get_tasks_by_group(db, group_id)


@router.get("/tasks/{task_id}/student-tasks", response_model=List[StudentTaskResponse], summary="Vazifa bo'yicha talabalar javoblari")
def task_student_submissions(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """Vazifa bo'yicha baholash uchun talabalarning topshiriq yozuvlarini ko'rish."""
    task = db.query(db.query(Task).filter(Task.id == task_id).exists()).scalar()
    if not task:
        raise NotFoundException("Vazifa topilmadi")
    
    # Guruh huquqini tekshirish
    task_obj = db.query(Task).filter(Task.id == task_id).first()
    verify_group_access(db, task_obj.group_id, current_user)
    
    return teacher_service.get_student_tasks_by_task(db, task_id)


@router.post("/student-tasks/{student_task_id}/grade", response_model=StudentTaskResponse, summary="Vazifani baholash")
def grade_student_task(
    student_task_id: int,
    grade_in: StudentTaskGrade,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """Talabaning topshirgan vazifasiga ball qo'yish va fikr yozish."""
    # Vazifa guruhiga ruxsat borligini tekshiramiz
    st = db.query(StudentTask).filter(StudentTask.id == student_task_id).first()
    if not st:
        raise NotFoundException("Topshiriq topilmadi")
    
    verify_group_access(db, st.task.group_id, current_user)
    
    # Ball tekshiruvi (maximum balldan oshib ketmasligi kerak)
    if grade_in.score > st.task.max_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ball maksimun balldan ({st.task.max_score}) oshib ketmasligi kerak"
        )
        
    return teacher_service.grade_student_task(db, student_task_id, grade_in, graded_by=current_user.id)


# ─── Student Bonuslari (Gamification) ─────────────────────────
@router.post("/bonuses", response_model=BonusResponse, status_code=status.HTTP_201_CREATED, summary="Talabaga bonus ball berish")
def award_bonus(
    bonus_in: BonusCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """Talabaga darsdagi faolligi uchun bonus ball berish."""
    # Talaba o'qituvchining biror faol guruhida borligini tekshirish
    student_groups = db.query(GroupStudent).filter(
        GroupStudent.student_id == bonus_in.student_id,
        GroupStudent.is_active == True
    ).all()
    
    has_access = False
    for sg in student_groups:
        try:
            verify_group_access(db, sg.group_id, current_user)
            has_access = True
            break
        except PermissionDeniedException:
            continue
            
    if not has_access and current_user.role == UserRole.TEACHER:
        raise PermissionDeniedException("Ushbu o'quvchi sizning guruhlaringizda o'qimaydi")
        
    return teacher_service.add_student_bonus(db, bonus_in, teacher_id=current_user.id)


@router.get("/bonuses/student/{student_id}", response_model=List[BonusResponse], summary="Talabaning bonus ballari tarixi")
def student_bonuses(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """Talabaning shu paytgacha to'plagan bonus ballari tarixi."""
    return teacher_service.get_student_bonuses(db, student_id)


# ─── Kurs Materiallari (Course Materials) ──────────────────────
@router.post("/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED, summary="Kurs materiali qo'shish")
def create_material(
    material_in: MaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """Kurs uchun yangi material (havola, darslik) qo'shish."""
    verify_course_access(db, material_in.course_id, current_user)
    return teacher_service.create_material(db, material_in, created_by=current_user.id)


@router.get("/materials/course/{course_id}", response_model=List[MaterialResponse], summary="Kurs materiallari ro'yxati")
def course_materials(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """Kursga tegishli barcha materiallarni ko'rish."""
    verify_course_access(db, course_id, current_user)
    return teacher_service.get_materials_by_course(db, course_id)


# ─── Guruh Tuzish (Soha va Daraja bo'yicha) ────────────────────
from app.schemas.group_application import GroupApplicationResponse, GroupCreateFromApplications
from app.services.group_application_service import group_application_service
from app.models.group_application import ApplicationStatus
from app.schemas.course import GroupResponse

@router.get(
    "/applications",
    response_model=List[GroupApplicationResponse],
    summary="O'qituvchi sohasiga mos keluvchi o'quvchi arizalari",
)
def get_teacher_applications(
    level: Optional[str] = Query(None, description="Daraja bo'yicha filter"),
    status: Optional[ApplicationStatus] = Query(ApplicationStatus.PENDING, description="Status bo'yicha filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """
    O'qituvchi faqat o'z faniga mos keluvchi o'quvchilar yuborgan arizalarni ko'ra oladi.
    """
    if current_user.role == UserRole.TEACHER and not current_user.subject:
        return []  # Fani biriktirilmagan o'qituvchiga hech narsa ko'rsatilmaydi

    subject_filter = current_user.subject if current_user.role == UserRole.TEACHER else None

    return group_application_service.get_applications(
        db,
        subject=subject_filter,
        level=level,
        status=status
    )


@router.post(
    "/applications/create-group",
    response_model=GroupResponse,
    summary="Tanlangan o'quvchi arizalaridan yangi guruh yaratish",
)
def teacher_create_group_from_applications(
    group_in: GroupCreateFromApplications,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_or_above),
):
    """
    O'qituvchi o'ziga tegishli kurs bo'yicha tanlangan arizalarni birlashtirib yangi guruh yaratadi.
    """
    # Kursga ruxsatni tekshirish
    verify_course_access(db, group_in.course_id, current_user)

    # Arizalarni tekshirish (o'qituvchining faniga to'g'ri kelishini tekshirish)
    for app_id in group_in.application_ids:
        app = group_application_service.get_application_by_id(db, app_id)
        if current_user.role == UserRole.TEACHER and app.subject != current_user.subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ariza (id={app_id}) sizning faningizga mos kelmaydi"
            )

    return group_application_service.create_group_from_applications(db, group_in)

