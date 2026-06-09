from typing import Any
import random
from fastapi import APIRouter, Depends
from app.api import deps
from app.models.user import User
from app.schemas.chat_ai import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/", response_model=ChatResponse, summary="AI Chat Assistant")
def chat_with_ai(
    data: ChatRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Sun'iy intellekt bilan yozishish uchun endpoint.
    """
    user_message = data.message.lower()
    
    # Hozircha oddiy mock javoblar qaytaradigan qilib turamiz, keyin OpenAI yoki boshqa AI ulanishi mumkin
    if "salom" in user_message:
        reply = "Assalomu alaykum! Sizga qanday yordam bera olaman?"
    elif "davomat" in user_message:
        reply = "Davomat bo'limiga o'tib, talabalar davomatini tekshirishingiz mumkin."
    elif "qanday" in user_message or "ahvol" in user_message:
        reply = "Rahmat, hammasi joyida! O'zingiz qandaysiz?"
    else:
        replies = [
            "Tushunmadim, iltimos boshqacha tushuntirib bering.",
            "Bu bo'yicha ma'lumot topa olmadim.",
            "Yaxshi savol! Lekin hozircha bunga aniq javobim yo'q.",
            "Men hali o'rganish jarayonidaman, savolingizga tez orada javob topishni o'rganaman."
        ]
        reply = random.choice(replies)
        
    return ChatResponse(reply=reply)
