from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.attendance import Attendance
from app.models.lesson import Lesson
from app.models.task import Task, StudentTask
from app.models.bonus import StudentBonus
from app.models.material import CourseMaterial
from app.models.course import GroupStudent
from app.schemas.lesson import LessonCreate
from app.schemas.task import TaskCreate, StudentTaskGrade
from app.schemas.bonus import BonusCreate
from app.schemas.material import MaterialCreate
from app.core.exceptions import NotFoundException, PermissionDeniedException


class TeacherService:
    # ─── Davomat (Attendance) ──────────────────────────────────
    def get_group_attendance(
        self,
        db: Session,
        group_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Attendance]:
        query = db.query(Attendance).filter(Attendance.group_id == group_id)
        if date_from:
            query = query.filter(Attendance.date >= date_from)
        if date_to:
            query = query.filter(Attendance.date <= date_to)
        return query.order_by(Attendance.date.desc()).all()

    # ─── Dars Jadvali (Lesson Schedule) ─────────────────────────
    def create_lesson(self, db: Session, lesson_in: LessonCreate) -> Lesson:
        lesson = Lesson(**lesson_in.model_dump())
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        return lesson

    def get_lessons_by_group(self, db: Session, group_id: int) -> List[Lesson]:
        return db.query(Lesson).filter(Lesson.group_id == group_id).order_by(Lesson.date.desc()).all()

    # ─── Vazifalar va Baholash (Tasks & Grading) ────────────────
    def create_task(self, db: Session, task_in: TaskCreate, teacher_id: int) -> Task:
        task = Task(**task_in.model_dump(), teacher_id=teacher_id)
        db.add(task)
        db.commit()
        db.refresh(task)

        # Guruhdagi barcha faol talabalarga avtomat ravishda StudentTask yozuvi yaratiladi
        students = db.query(GroupStudent).filter(
            GroupStudent.group_id == task_in.group_id,
            GroupStudent.is_active == True
        ).all()

        for gs in students:
            st = StudentTask(
                task_id=task.id,
                student_id=gs.student_id
            )
            db.add(st)
        
        db.commit()
        db.refresh(task)
        return task

    def get_tasks_by_group(self, db: Session, group_id: int) -> List[Task]:
        return db.query(Task).filter(Task.group_id == group_id).order_by(Task.created_at.desc()).all()

    def get_student_tasks_by_task(self, db: Session, task_id: int) -> List[StudentTask]:
        return db.query(StudentTask).filter(StudentTask.task_id == task_id).all()

    def grade_student_task(
        self,
        db: Session,
        student_task_id: int,
        grade_in: StudentTaskGrade,
        graded_by: int
    ) -> StudentTask:
        st = db.query(StudentTask).filter(StudentTask.id == student_task_id).first()
        if not st:
            raise NotFoundException("Topshirilgan vazifa yozuvi topilmadi")

        st.score = grade_in.score
        st.feedback = grade_in.feedback
        st.graded_at = datetime.utcnow()
        st.graded_by = graded_by

        db.commit()
        db.refresh(st)
        return st

    # ─── Student Bonuslari (Gamification) ────────────────────────
    def add_student_bonus(self, db: Session, bonus_in: BonusCreate, teacher_id: int) -> StudentBonus:
        bonus = StudentBonus(**bonus_in.model_dump(), teacher_id=teacher_id)
        db.add(bonus)
        db.commit()
        db.refresh(bonus)
        return bonus

    def get_student_bonuses(self, db: Session, student_id: int) -> List[StudentBonus]:
        return db.query(StudentBonus).filter(StudentBonus.student_id == student_id).order_by(StudentBonus.created_at.desc()).all()

    # ─── Kurs Materiallari (Course Materials) ─────────────────────
    def create_material(self, db: Session, material_in: MaterialCreate, created_by: int) -> CourseMaterial:
        material = CourseMaterial(**material_in.model_dump(), created_by=created_by)
        db.add(material)
        db.commit()
        db.refresh(material)
        return material

    def get_materials_by_course(self, db: Session, course_id: int) -> List[CourseMaterial]:
        return db.query(CourseMaterial).filter(CourseMaterial.course_id == course_id).order_by(CourseMaterial.created_at.desc()).all()


teacher_service = TeacherService()
