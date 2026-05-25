# Tizimlashtirilgan Markazlar Backend — Director Moduli

Bu loyiha FastAPI va PostgreSQL asosida qurilgan o'quv markazlarini boshqarish tizimining faqat **Director moduli** uchun ishlab chiqilgan backend qismidir.

## Xususiyatlari
- **Auth (Autentifikatsiya)**: Telegram OTP orqali kirish va JWT token orqali xavfsiz seanslar.
- **Director Moduli**:
  - Umumiy dashboard statistikasi (o'qituvchilar, o'quvchilar, kurslar, guruhlar soni va moliyaviy oylik hisobot).
  - O'qituvchilar (Teacher) CRUD operatsiyalari va faolligini boshqarish.
  - Kurslar (Course) va Guruhlar (Group) boshqaruvi.
  - Moliya bo'limi: Oylik moliyaviy hisobotlar, o'quvchilar to'lovlari (payments) va o'qituvchilar oyliklari/bonus/jarimalari (salaries) ustida amallar.

## Ishga tushirish (Local)

1. Virtual muhit yaratish va kerakli kutubxonalarni o'rnatish:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows uchun: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. `.env` faylida o'zingizning sozlamalaringizni yozing:
   - `DATABASE_URL` (PostgreSQL ulanish manzili)
   - `SECRET_KEY` (JWT yaratish uchun maxfiy kalit)

3. Migratsiyalarni amalga oshirish:
   ```bash
   python run_alembic.py
   ```

4. Serverni ishga tushirish:
   ```bash
   uvicorn app.main:app --reload
   ```

Tizim ishga tushgach, API hujjatlarini `http://127.0.0.1:8000/docs` manzilida ko'rishingiz mumkin.
