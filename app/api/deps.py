from typing import Generator
# pyrefly: ignore [missing-import]
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.core.exceptions import CredentialsException, PermissionDeniedException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """JWT tokendan joriy foydalanuvchini oladi."""
    payload = decode_access_token(token)
    if not payload:
        raise CredentialsException()

    user_id: int = payload.get("sub")
    if user_id is None:
        raise CredentialsException()

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise CredentialsException()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Foydalanuvchi faol emas",
        )
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Faol foydalanuvchini qaytaradi."""
    return current_user


def require_role(*roles: UserRole):
    """Rol tekshiruvchi dependency factory."""
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise PermissionDeniedException(
                f"Bu amalni bajarish uchun {', '.join(r.value for r in roles)} roli kerak"
            )
        return current_user
    return checker


# ─── Rol-specific dependencies ───────────────────────────────
def get_superadmin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.SUPERADMIN:
        raise PermissionDeniedException("Faqat SuperAdmin uchun")
    return current_user


def get_director_or_above(current_user: User = Depends(get_current_user)) -> User:
    allowed = {UserRole.SUPERADMIN, UserRole.DIRECTOR}
    if current_user.role not in allowed:
        raise PermissionDeniedException("Faqat Director va yuqori rollar uchun")
    return current_user


def get_reception_or_above(current_user: User = Depends(get_current_user)) -> User:
    allowed = {UserRole.SUPERADMIN, UserRole.DIRECTOR, UserRole.RECEPTION}
    if current_user.role not in allowed:
        raise PermissionDeniedException("Ruxsat yo'q")
    return current_user


def get_teacher_or_above(current_user: User = Depends(get_current_user)) -> User:
    allowed = {UserRole.SUPERADMIN, UserRole.DIRECTOR, UserRole.RECEPTION, UserRole.TEACHER}
    if current_user.role not in allowed:
        raise PermissionDeniedException("Ruxsat yo'q")
    return current_user
