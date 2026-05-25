#!/bin/bash
# Render.com uchun ishga tushirish skripti

# 1. Ma'lumotlar bazasini yangilash (Alembic migrations)
echo "Ma'lumotlar bazasi migratsiyalarini ishga tushirish..."
alembic upgrade head

# 2. Asosiy API serverini ishga tushirish (Uvicorn bilan Gunicorn)
# Render o'zining PORT o'zgaruvchisini beradi, shuning uchun $PORT dan foydalanamiz
echo "FastAPI serverni ishga tushirish..."
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
