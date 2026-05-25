from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import Token, LoginRequest, RegisterRequest, SUBJECT_LABELS
from app.services.user_service import auth_service, user_service
from app.core.exceptions import CredentialsException, ConflictException
from app.models.user import User, UserRole, Subject
from app.core.security import get_password_hash

router = APIRouter()


@router.post("/login", response_model=Token, summary="Tizimga kirish")
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Telefon raqami va parol orqali tizimga kiradi."""
    user = auth_service.authenticate_user(db, login_data.phone, login_data.password)
    if not user:
        raise CredentialsException()

    if not user.is_active:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Foydalanuvchi bloklangan")

    token = auth_service.create_token_for_user(user)
    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        full_name=user.full_name,
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED, summary="O'quvchi ro'yxatdan o'tish")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """O'quvchi o'zi ro'yxatdan o'tadi (student roli avtomatik)."""
    existing = db.query(User).filter(User.phone == data.phone.strip()).first()
    if existing:
        raise ConflictException("Bu telefon raqami allaqachon ro'yxatdan o'tgan")

    user = User(
        full_name=data.full_name.strip(),
        phone=data.phone.strip(),
        hashed_password=get_password_hash(data.password),
        role=UserRole.STUDENT,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth_service.create_token_for_user(user)
    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        full_name=user.full_name,
    )


@router.get("/subjects", summary="Fanlar ro'yxati")
def get_subjects():
    """Barcha fanlar ro'yxatini qaytaradi."""
    return [{"value": k, "label": v} for k, v in SUBJECT_LABELS.items()]


@router.get("/setup-superadmin", summary="Vaqtincha: SuperAdmin yaratish")
def setup_superadmin(db: Session = Depends(get_db)):
    """Render uchun vaqtincha admin yaratish yo'li"""
    existing = db.query(User).filter(User.role == UserRole.SUPERADMIN).first()
    if existing:
        return {"status": "SuperAdmin allaqachon mavjud"}
    
    superadmin = User(
        full_name="Super Admin",
        phone="+998901234567",
        hashed_password=get_password_hash("Admin@2024"),
        role=UserRole.SUPERADMIN,
        is_active=True,
    )
    db.add(superadmin)
    db.commit()
    return {"status": "SuperAdmin muvaffaqiyatli yaratildi!"}

@router.get("/reset-db", summary="Bazada hamma narsani tozalab qayta yaratish")
def reset_database():
    """Jadvallarni o'chirib qayta yaratadi. Agar xato bersa (masalan, eski DB tufayli), shuni ishlating."""
    try:
        from app.db.database import engine, Base
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # 8 ta default user yaratish
        from app.db.database import SessionLocal
        db = SessionLocal()
        defaults = [
            User(full_name="Super Admin", phone="+998900000001",
                 hashed_password=get_password_hash("admin123"),
                 role=UserRole.SUPERADMIN, is_active=True),
            User(full_name="Abdulloh Karimov", phone="+998900000002",
                 hashed_password=get_password_hash("admin123"),
                 role=UserRole.DIRECTOR, is_active=True),
            User(full_name="Nilufar Rashidova", phone="+998900000003",
                 hashed_password=get_password_hash("admin123"),
                 role=UserRole.RECEPTION, is_active=True),
            User(full_name="Sherzod Alimov", phone="+998900000004",
                 hashed_password=get_password_hash("admin123"),
                 role=UserRole.TEACHER, subject=Subject.PROGRAMMING, is_active=True),
            User(full_name="Gulnora Mirzayeva", phone="+998900000010",
                 hashed_password=get_password_hash("admin123"),
                 role=UserRole.TEACHER, subject=Subject.ENGLISH, is_active=True),
            User(full_name="Behruz Sobirov", phone="+998900000005",
                 hashed_password=get_password_hash("admin123"),
                 role=UserRole.STUDENT, is_active=True),
            User(full_name="Sardor Xolmatov", phone="+998900000006",
                 hashed_password=get_password_hash("admin123"),
                 role=UserRole.STUDENT, is_active=True),
            User(full_name="Malika Nazarova", phone="+998900000007",
                 hashed_password=get_password_hash("admin123"),
                 role=UserRole.STUDENT, is_active=True),
        ]
        db.add_all(defaults)
        db.commit()
        db.close()
        return {"status": "Database tozalandi va 8 ta user yaratildi!"}
    except Exception as e:
        return {"error": str(e)}
