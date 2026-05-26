"""Render deployment uchun wrapper — app.main dan import qiladi.
Startup paytida seed ham ishga tushadi.
"""
from app.main import app  # noqa: F401
from app.db.database import engine, Base, SessionLocal
from app.models.user import User, UserRole, Subject
from app.core.security import get_password_hash


def auto_seed():
    """Agar DB bo'sh bo'lsa, default foydalanuvchilarni yaratadi."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(User).first()
        if existing:
            return  # allaqachon ma'lumot bor

        users = [
            User(full_name="Super Admin", phone="+998901001001",
                 hashed_password=get_password_hash("admin2024"),
                 role=UserRole.SUPERADMIN, is_active=True),
            User(full_name="Abdulloh Karimov", phone="+998931050116",
                 hashed_password=get_password_hash("bossjim"),
                 role=UserRole.DIRECTOR, is_active=True),
            User(full_name="Nilufar Rashidova", phone="+998942002002",
                 hashed_password=get_password_hash("qabul123"),
                 role=UserRole.RECEPTION, is_active=True),
            User(full_name="Sherzod Alimov", phone="+998953003003",
                 hashed_password=get_password_hash("ustoz123"),
                 role=UserRole.TEACHER, subject=Subject.PROGRAMMING, is_active=True),
            User(full_name="Gulnora Mirzayeva", phone="+998953003004",
                 hashed_password=get_password_hash("english1"),
                 role=UserRole.TEACHER, subject=Subject.ENGLISH, is_active=True),
            User(full_name="Behruz Sobirov", phone="+998900000005",
                 hashed_password=get_password_hash("talaba1"),
                 role=UserRole.STUDENT, is_active=True),
            User(full_name="Sardor Xolmatov", phone="+998900000006",
                 hashed_password=get_password_hash("talaba2"),
                 role=UserRole.STUDENT, is_active=True),
            User(full_name="Malika Nazarova", phone="+998900000007",
                 hashed_password=get_password_hash("talaba3"),
                 role=UserRole.STUDENT, is_active=True),
        ]
        db.add_all(users)
        db.commit()
        print("Auto-seed: 8 ta foydalanuvchi yaratildi")
    except Exception as e:
        db.rollback()
        print(f"Auto-seed xatosi: {e}")
    finally:
        db.close()


# Startup da auto-seed
auto_seed()
