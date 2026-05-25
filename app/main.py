# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request, status
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.api_router import api_router
from app.db.database import engine, Base

# ─── Import barcha modellar (jadval yaratish uchun) ──────────
from app.models import user, course, finance, task, attendance, bonus, lesson, material  # noqa

# ─── FastAPI ilovasi ─────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Markaz Platformasi API

O'quv markazi boshqaruv tizimining to'liq backend API interfeysi.

### Rollar:
- **SuperAdmin** 👑 — Platforma boshqaruvi
- **Director** 🏫 — Markaz boshqaruvi, o'qituvchilar, kurslar, moliya
- **Reception** 📋 — Talabalar, guruhga yozish, to'lovlar
- **Teacher** 📚 — Davomat, baholash, dars jadvali, materiallar
- **Student** 🎓 — Profil, guruhlar, baholar, to'lovlar
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ─── Startup: jadvallarni yaratish ───────────────────────────
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    
    from seed import seed as run_seed
    try:
        run_seed()
        print("✅ Seed funksiyasi muvaffaqiyatli ishga tushdi")
    except Exception as e:
        print(f"❌ Seed funksiyasida xato: {e}")

# ─── CORS Middleware ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Server xatosi yuz berdi"},
    )


# ─── API Routes ───────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


# ─── Frontend statik fayllar ─────────────────────────────────
import os
_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend")
_frontend_dir = os.path.normpath(_frontend_dir)
if os.path.isdir(_frontend_dir):
    app.mount("/frontend", StaticFiles(directory=_frontend_dir, html=True), name="frontend")


# ─── Root endpoint ───────────────────────────────────────────
@app.get("/", tags=["Root"], summary="API holat tekshiruvi")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "ishlamoqda ✅",
        "docs": "/docs",
        "frontend": "/frontend/index.html",
    }


@app.get("/health", tags=["Root"], summary="Health check")
def health_check():
    return {"status": "ok"}
