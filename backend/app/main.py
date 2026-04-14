"""Точка входа FastAPI приложения AI Tutor."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, users, tutors, sessions, ai, subjects, tests, video

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="AI Tutor API",
    description="API онлайн-репетитора с персональным ИИ-тьютором",
    version="1.0.0",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Авторизация"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Пользователи"])
app.include_router(tutors.router, prefix="/api/v1/tutors", tags=["Репетиторы"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Занятия"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI Тьютор"])
app.include_router(subjects.router, prefix="/api/v1/subjects", tags=["Предметы"])
app.include_router(tests.router, prefix="/api/v1/tests", tags=["Тесты"])
app.include_router(video.router, prefix="/api/v1/video", tags=["Видеозвонки"])

# Статика — аватарки и прочие загруженные файлы
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/", tags=["Здоровье"])
async def root():
    """Проверка работоспособности сервера."""
    return {"status": "ok", "message": "AI Tutor API работает"}
