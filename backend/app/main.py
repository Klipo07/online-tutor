"""Точка входа FastAPI приложения AI Tutor."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, users, tutors, sessions, ai, subjects, video

app = FastAPI(
    title="AI Tutor API",
    description="API онлайн-репетитора с персональным ИИ-тьютором",
    version="1.0.0",
)

# Настройка CORS
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
app.include_router(video.router, prefix="/api/v1/video", tags=["Видеозвонки"])


@app.get("/", tags=["Здоровье"])
async def root():
    """Проверка работоспособности сервера."""
    return {"status": "ok", "message": "AI Tutor API работает"}
