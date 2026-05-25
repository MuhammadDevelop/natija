"""
Markaz Platformasi — Seed Script
Barcha rollar uchun default foydalanuvchilar va namuna ma'lumotlar yaratadi.
"""
import sys
import os

# backend papkasidan ishga tushadigan bo'lsa
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine, Base, SessionLocal
from app.models.user import User, UserRole, Subject
from app.models.course import Course, Group, GroupStudent
from app.models.finance import Payment, Salary, PaymentStatus, PaymentType
from app.models.task import Task, StudentTask, TaskType
from app.models.attendance import Attendance, AttendanceStatus
from app.models.bonus import StudentBonus
from app.models.lesson import Lesson
from app.models.material import CourseMaterial
from app.core.security import get_password_hash
from datetime import datetime, timedelta


def seed():
    # Eski jadvallarni o'chirish va yangi yaratish
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Allaqachon seeded bo'lsa skip qilamiz
        existing = db.query(User).filter(User.role == UserRole.SUPERADMIN).first()
        if existing:
            print("✅ Ma'lumotlar allaqachon mavjud. Seed o'tkazilmadi.")
            return

        print("🌱 Seed boshlanmoqda...")

        # ─── 1. Foydalanuvchilar ─────────────────────────────────
        superadmin = User(
            full_name="Super Admin",
            phone="+998900000001",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.SUPERADMIN,
            is_active=True,
        )
        director = User(
            full_name="Abdulloh Karimov",
            phone="+998900000002",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.DIRECTOR,
            is_active=True,
        )
        reception = User(
            full_name="Nilufar Rashidova",
            phone="+998900000003",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.RECEPTION,
            is_active=True,
        )
        teacher1 = User(
            full_name="Sherzod Alimov",
            phone="+998900000004",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.TEACHER,
            subject=Subject.PROGRAMMING,
            is_active=True,
        )
        teacher2 = User(
            full_name="Gulnora Mirzayeva",
            phone="+998900000010",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.TEACHER,
            subject=Subject.ENGLISH,
            is_active=True,
        )
        student1 = User(
            full_name="Behruz Sobirov",
            phone="+998900000005",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.STUDENT,
            is_active=True,
        )
        student2 = User(
            full_name="Sardor Xolmatov",
            phone="+998900000006",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.STUDENT,
            is_active=True,
        )
        student3 = User(
            full_name="Malika Nazarova",
            phone="+998900000007",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.STUDENT,
            is_active=True,
        )

        db.add_all([superadmin, director, reception, teacher1, teacher2, student1, student2, student3])
        db.commit()

        print(f"  👤 Foydalanuvchilar yaratildi ({8} ta)")

        # ─── 2. Kurslar ──────────────────────────────────────────
        course_python = Course(
            name="Python Backend",
            description="Python va FastAPI yordamida backend dasturlash",
            price=500000,
            duration_months=4,
            is_active=True,
            teacher_id=teacher1.id,
        )
        course_frontend = Course(
            name="Frontend Development",
            description="HTML, CSS, JavaScript va React",
            price=400000,
            duration_months=3,
            is_active=True,
            teacher_id=teacher2.id,
        )
        course_english = Course(
            name="English Language",
            description="IELTS va General English kurslari",
            price=350000,
            duration_months=6,
            is_active=True,
        )

        db.add_all([course_python, course_frontend, course_english])
        db.commit()

        print(f"  📚 Kurslar yaratildi ({3} ta)")

        # ─── 3. Guruhlar ─────────────────────────────────────────
        group_p15 = Group(
            name="P15 Python Boot Camp",
            schedule="Du-Cho-Ju 14:00-16:00",
            max_students=20,
            is_active=True,
            start_date=datetime(2026, 1, 15),
            course_id=course_python.id,
        )
        group_f8 = Group(
            name="F8 Frontend Intensive",
            schedule="Se-Pay 10:00-12:00",
            max_students=15,
            is_active=True,
            start_date=datetime(2026, 2, 1),
            course_id=course_frontend.id,
        )
        group_eng = Group(
            name="E3 IELTS Preparation",
            schedule="Du-Cho-Ju 18:00-20:00",
            max_students=12,
            is_active=True,
            start_date=datetime(2026, 3, 1),
            course_id=course_english.id,
        )

        db.add_all([group_p15, group_f8, group_eng])
        db.commit()

        print(f"  👥 Guruhlar yaratildi ({3} ta)")

        # ─── 4. Talabalarni guruhlarga yozish ─────────────────────
        enrollments = [
            GroupStudent(group_id=group_p15.id, student_id=student1.id, is_active=True),
            GroupStudent(group_id=group_p15.id, student_id=student2.id, is_active=True),
            GroupStudent(group_id=group_f8.id, student_id=student3.id, is_active=True),
            GroupStudent(group_id=group_f8.id, student_id=student1.id, is_active=True),
        ]
        db.add_all(enrollments)
        db.commit()

        print(f"  📋 Guruhga yozildi ({4} ta)")

        # ─── 5. To'lovlar ────────────────────────────────────────
        payments = [
            Payment(
                amount=500000, month="2026-05", status=PaymentStatus.PAID,
                payment_type=PaymentType.CARD, student_id=student1.id,
                course_id=course_python.id, received_by=reception.id,
                paid_at=datetime(2026, 5, 1),
            ),
            Payment(
                amount=400000, month="2026-05", status=PaymentStatus.PAID,
                payment_type=PaymentType.CASH, student_id=student3.id,
                course_id=course_frontend.id, received_by=reception.id,
                paid_at=datetime(2026, 5, 3),
            ),
            Payment(
                amount=500000, month="2026-06", status=PaymentStatus.PENDING,
                student_id=student1.id, course_id=course_python.id,
            ),
            Payment(
                amount=500000, month="2026-05", status=PaymentStatus.OVERDUE,
                student_id=student2.id, course_id=course_python.id,
            ),
        ]
        db.add_all(payments)
        db.commit()

        print(f"  💳 To'lovlar yaratildi ({4} ta)")

        # ─── 6. Oyliklar ─────────────────────────────────────────
        salaries = [
            Salary(
                amount=3000000, month="2026-05", status=PaymentStatus.PAID,
                bonus=200000, fine=0, teacher_id=teacher1.id,
                paid_at=datetime(2026, 5, 28),
            ),
            Salary(
                amount=2500000, month="2026-05", status=PaymentStatus.PENDING,
                teacher_id=teacher2.id,
            ),
        ]
        db.add_all(salaries)
        db.commit()

        print(f"  💰 Oyliklar yaratildi ({2} ta)")

        # ─── 7. Darslar ──────────────────────────────────────────
        lessons = [
            Lesson(
                group_id=group_p15.id, topic="FastAPI kirish",
                description="REST API va FastAPI asoslari",
                date=datetime(2026, 5, 20),
            ),
            Lesson(
                group_id=group_p15.id, topic="SQLAlchemy ORM",
                description="Ma'lumotlar bazasi bilan ishlash",
                date=datetime(2026, 5, 22),
            ),
            Lesson(
                group_id=group_f8.id, topic="React Components",
                description="Functional components va hooks",
                date=datetime(2026, 5, 21),
            ),
        ]
        db.add_all(lessons)
        db.commit()

        print(f"  📖 Darslar yaratildi ({3} ta)")

        # ─── 8. Vazifalar ─────────────────────────────────────────
        task1 = Task(
            group_id=group_p15.id, teacher_id=teacher1.id,
            title="FastAPI CRUD yaratish",
            description="Student modeliga CRUD endpointlar yozing",
            type=TaskType.HOMEWORK, max_score=100,
            due_date=datetime(2026, 5, 30),
        )
        task2 = Task(
            group_id=group_f8.id, teacher_id=teacher2.id,
            title="React Todo App",
            description="useState va useEffect ishlatib Todo ilovasi yarating",
            type=TaskType.HOMEWORK, max_score=100,
            due_date=datetime(2026, 6, 1),
        )
        db.add_all([task1, task2])
        db.commit()

        # Student task assignmentlari
        student_tasks = [
            StudentTask(task_id=task1.id, student_id=student1.id, score=85,
                        feedback="Yaxshi!", graded_at=datetime(2026, 5, 25),
                        graded_by=teacher1.id, submitted_at=datetime(2026, 5, 24)),
            StudentTask(task_id=task1.id, student_id=student2.id),
            StudentTask(task_id=task2.id, student_id=student3.id),
            StudentTask(task_id=task2.id, student_id=student1.id, score=92,
                        feedback="A'lo!", graded_at=datetime(2026, 5, 26),
                        graded_by=teacher2.id, submitted_at=datetime(2026, 5, 25)),
        ]
        db.add_all(student_tasks)
        db.commit()

        print(f"  📝 Vazifalar yaratildi ({2} ta, {4} ta topshiriq)")

        # ─── 9. Davomat ──────────────────────────────────────────
        attendance_records = [
            Attendance(date=datetime(2026, 5, 20), status=AttendanceStatus.PRESENT,
                       student_id=student1.id, group_id=group_p15.id, marked_by=teacher1.id),
            Attendance(date=datetime(2026, 5, 20), status=AttendanceStatus.PRESENT,
                       student_id=student2.id, group_id=group_p15.id, marked_by=teacher1.id),
            Attendance(date=datetime(2026, 5, 22), status=AttendanceStatus.PRESENT,
                       student_id=student1.id, group_id=group_p15.id, marked_by=teacher1.id),
            Attendance(date=datetime(2026, 5, 22), status=AttendanceStatus.ABSENT,
                       student_id=student2.id, group_id=group_p15.id, marked_by=teacher1.id),
            Attendance(date=datetime(2026, 5, 21), status=AttendanceStatus.PRESENT,
                       student_id=student3.id, group_id=group_f8.id, marked_by=teacher2.id),
            Attendance(date=datetime(2026, 5, 21), status=AttendanceStatus.LATE,
                       student_id=student1.id, group_id=group_f8.id, marked_by=teacher2.id),
        ]
        db.add_all(attendance_records)
        db.commit()

        print(f"  ✅ Davomat yozuvlari yaratildi ({6} ta)")

        # ─── 10. Bonuslar ────────────────────────────────────────
        bonuses = [
            StudentBonus(student_id=student1.id, teacher_id=teacher1.id,
                         points=10, reason="Darsda faol qatnashdi"),
            StudentBonus(student_id=student1.id, teacher_id=teacher2.id,
                         points=5, reason="Vazifani birinchi topshirdi"),
            StudentBonus(student_id=student3.id, teacher_id=teacher2.id,
                         points=8, reason="Guruhda eng yaxshi natija"),
        ]
        db.add_all(bonuses)
        db.commit()

        print(f"  ⭐ Bonuslar yaratildi ({3} ta)")

        # ─── 11. Kurs materiallari ───────────────────────────────
        materials = [
            CourseMaterial(
                course_id=course_python.id, title="FastAPI Documentation",
                description="Rasmiy qo'llanma",
                link_url="https://fastapi.tiangolo.com",
                created_by=teacher1.id,
            ),
            CourseMaterial(
                course_id=course_frontend.id, title="React Tutorial",
                description="Official React tutorial",
                link_url="https://react.dev/learn",
                created_by=teacher2.id,
            ),
        ]
        db.add_all(materials)
        db.commit()

        print(f"  📁 Materiallar yaratildi ({2} ta)")

        print()
        print("=" * 50)
        print("🎉 Seed muvaffaqiyatli yakunlandi!")
        print("=" * 50)
        print()
        print("📋 Login ma'lumotlari (barcha parollar: admin123):")
        print("─" * 50)
        print(f"  👑 SuperAdmin:  +998900000001")
        print(f"  🏫 Director:    +998900000002")
        print(f"  📋 Reception:   +998900000003")
        print(f"  📚 Teacher 1:   +998900000004")
        print(f"  📚 Teacher 2:   +998900000010")
        print(f"  🎓 Student 1:   +998900000005")
        print(f"  🎓 Student 2:   +998900000006")
        print(f"  🎓 Student 3:   +998900000007")
        print("─" * 50)

    except Exception as e:
        db.rollback()
        print(f"❌ Seed xatosi: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
