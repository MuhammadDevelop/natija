from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.api_router import api_router
from app.db.database import engine, Base

# ─── Import barcha modellar (jadval yaratish uchun) ──────────
from app.models import user, course, finance, task, attendance, bonus, lesson, material, group_application  # noqa

# ─── FastAPI ilovasi ─────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Markaz Platformasi API

O'quv markazi boshqaruv tizimining to'liq backend API interfeysi.

### Rollar:
- **SuperAdmin** — Platforma boshqaruvi
- **Director** — Markaz boshqaruvi
- **Reception** — Talabalar, to'lovlar
- **Teacher** — Davomat, baholash
- **Student** — Profil, baholar
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ─── Startup: jadvallarni yaratish + auto-seed ───────────────
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

    # Auto-seed: DB bo'sh bo'lsa default foydalanuvchilarni yaratish
    from app.db.database import SessionLocal
    from app.models.user import User, UserRole, Subject
    from app.core.security import get_password_hash

    db = SessionLocal()
    try:
        if not db.query(User).first():
            defaults = [
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
            db.add_all(defaults)
            db.commit()
            print("Auto-seed: 8 ta foydalanuvchi yaratildi")
    except Exception as e:
        db.rollback()
        print(f"Auto-seed xatosi: {e}")
    finally:
        db.close()

# ─── CORS Middleware ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://natija-ro6w.onrender.com",
        "*" # Ehtiyot bo'lish uchun, lekin frontend qayerdan ulansa shu domenni qo'shgan ma'qul
    ],
    allow_credentials=False, # Yoki True bo'lsa "*" ni olib tashlash kerak
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Xato ishlovchilar ───────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({"field": field, "message": error["msg"]})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Kiritilgan ma'lumotlar noto'g'ri", "errors": errors},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    import traceback
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Server xatosi yuz berdi", "error_msg": str(exc), "trace": traceback.format_exc()},
    )


# ─── API Routes ───────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


# ─── Root endpoint ───────────────────────────────────────────
@app.get("/", tags=["Root"], summary="API holat tekshiruvi")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "ishlamoqda",
        "docs": "/docs",
    }


@app.get("/health", tags=["Root"], summary="Health check")
def health_check():
    return {"status": "ok"}
