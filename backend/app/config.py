"""Настройки приложения — загружаются из .env файла."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Приложение
    APP_ENV: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8081"

    # База данных
    DATABASE_URL: str = "postgresql+asyncpg://ai_tutor:ai_tutor_pass@localhost/ai_tutor"
    REDIS_URL: str = "redis://localhost:6379"

    # JWT аутентификация
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # AI провайдер
    AI_PROVIDER: str = "openai"  # openai | anthropic | gemini | openrouter | yandex
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    AI_MODEL_OPENAI: str = "gpt-4o-mini"
    AI_MODEL_ANTHROPIC: str = "claude-sonnet-4-5"
    GEMINI_API_KEY: str = ""
    AI_MODEL_GEMINI: str = "gemini-2.0-flash"
    OPENROUTER_API_KEY: str = ""
    AI_MODEL_OPENROUTER: str = "google/gemini-2.0-flash-exp:free"
    YANDEX_API_KEY: str = ""
    YANDEX_FOLDER_ID: str = ""
    AI_MODEL_YANDEX: str = "yandexgpt-lite/latest"

    # Agora (видеозвонки)
    AGORA_APP_ID: str = ""
    AGORA_APP_CERTIFICATE: str = ""

    # S3 хранилище
    S3_BUCKET: str = "ai-tutor-media"
    S3_ENDPOINT: str = "https://storage.yandexcloud.net"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Глобальный экземпляр настроек
settings = Settings()
