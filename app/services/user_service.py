from typing import Optional, List
from datetime import timedelta
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.core.exceptions import NotFoundException, ConflictException, PermissionDeniedException


class AuthService:
    def authenticate_user(self, db: Session, phone: str, password: str) -> Optional[User]:
        """Telefon va parol orqali foydalanuvchini tekshiradi."""
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def create_token_for_user(self, user: User) -> str:
        """Foydalanuvchi uchun JWT token yaratadi."""
        token_data = {"sub": str(user.id), "role": user.role.value}
        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return access_token


class UserService:
    def get_by_id(self, db: Session, user_id: int) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException(f"Foydalanuvchi (id={user_id}) topilmadi")
        return user

    def get_by_phone(self, db: Session, phone: str) -> Optional[User]:
        return db.query(User).filter(User.phone == phone).first()

    def get_all(
        self,
        db: Session,
        role: Optional[UserRole] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        query = db.query(User)
        if role:
            query = query.filter(User.role == role)
        return query.offset(skip).limit(limit).all()

    def create(
        self,
        db: Session,
        user_in: UserCreate,
        created_by: Optional[int] = None,
    ) -> User:
        # Telefon raqami takrorlanishini tekshiramiz
        existing = self.get_by_phone(db, user_in.phone)
        if existing:
            raise ConflictException(f"Bu telefon raqami ({user_in.phone}) allaqachon ro'yxatdan o'tgan")

        user = User(
            full_name=user_in.full_name,
            phone=user_in.phone,
            hashed_password=get_password_hash(user_in.password),
            role=user_in.role,
            is_active=user_in.is_active,
            notes=user_in.notes,
            subject=user_in.subject,
            created_by=created_by,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update(self, db: Session, user_id: int, user_in: UserUpdate) -> User:
        user = self.get_by_id(db, user_id)
        update_data = user_in.model_dump(exclude_unset=True)

        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        for key, value in update_data.items():
            setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user

    def delete(self, db: Session, user_id: int) -> bool:
        user = self.get_by_id(db, user_id)
        db.delete(user)
        db.commit()
        return True

    def toggle_active(self, db: Session, user_id: int) -> User:
        user = self.get_by_id(db, user_id)
        user.is_active = not user.is_active
        db.commit()
        db.refresh(user)
        return user


auth_service = AuthService()
user_service = UserService()
