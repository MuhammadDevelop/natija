"""
SuperAdmin telefon raqamini yangilash.
Foydalanish: python update_admin_phone.py
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
import app.db.base
from app.models.user import User, UserRole


def update_phone():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == UserRole.SUPERADMIN).first()
        if not admin:
            print("❌ SuperAdmin topilmadi!")
            return

        old_phone = admin.phone
        admin.phone = "+998931002010"
        db.commit()
        print(f"✅ SuperAdmin telefon raqami yangilandi!")
        print(f"   Eski: {old_phone}")
        print(f"   Yangi: +998931002010")
    except Exception as e:
        db.rollback()
        print(f"❌ Xato: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    update_phone()
