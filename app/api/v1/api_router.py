from fastapi import APIRouter
from app.api.v1.endpoints import auth, director, teacher, superadmin, reception, student

api_router = APIRouter()

# Auth (hamma uchun)
api_router.include_router(auth.router, prefix="/auth", tags=["🔐 Auth"])

# SuperAdmin
api_router.include_router(superadmin.router, prefix="/superadmin", tags=["👑 SuperAdmin"])

# Director
api_router.include_router(director.router, prefix="/director", tags=["🏫 Director"])

# Reception (Qabul xodimi)
api_router.include_router(reception.router, prefix="/reception", tags=["📋 Reception"])

# Teacher (O'qituvchi)
api_router.include_router(teacher.router, prefix="/teacher", tags=["📚 Teacher"])

# Student (O'quvchi)
api_router.include_router(student.router, prefix="/student", tags=["🎓 Student"])

# Face ID (Davomat)
from app.api.v1.endpoints import face_id
api_router.include_router(face_id.router, prefix="/face-id", tags=["📷 Face ID"])

# AI Chat
from app.api.v1.endpoints import chat_ai
api_router.include_router(chat_ai.router, prefix="/chat", tags=["🤖 AI Chat"])
