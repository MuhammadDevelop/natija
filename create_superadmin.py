"""
SuperAdmin foydalanuvchini yaratish uchun bir martalik skript.
Foydalanish: python create_superadmin.py
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
import app.db.base  # Barcha modellarni yuklash uchun
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def create_superadmin():
    db = SessionLocal()
    try:
        # Avval mavjudligini tekshiramiz
        existing = db.query(User).filter(User.role == UserRole.SUPERADMIN).first()
        if existing:
            print(f"✅ SuperAdmin allaqachon mavjud: {existing.phone}")
            return

        superadmin = User(
            full_name="Super Admin",
            phone="+998931002010",
            hashed_password=get_password_hash("Admin@2024"),  # O'zgartiring!
            role=UserRole.SUPERADMIN,
            is_active=True,
        )
        db.add(superadmin)
        db.commit()
        db.refresh(superadmin)
        print("✅ SuperAdmin muvaffaqiyatli yaratildi!")
        print(f"   Telefon: {superadmin.phone}")
        print(f"   Parol: Admin@2024  ← DARHOL O'ZGARTIRING!")
    except Exception as e:
        db.rollback()
        print(f"❌ Xato: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_superadmin()
