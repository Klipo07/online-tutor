"""Настройки приложения — загружаются из .env файла."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Приложение
    APP_ENV: str = "development"
    DEBUG: bool = True
    SQL_ECHO: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8081"

    # База данных
    DATABASE_URL: str = "postgresql+asyncpg://ai_tutor:ai_tutor_pass@localhost/ai_tutor"

    # JWT аутентификация
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # AI провайдер — только Anthropic (Claude) и YandexGPT
    AI_PROVIDER: str = "anthropic"  # anthropic | yandex
    ANTHROPIC_API_KEY: str = ""
    AI_MODEL_ANTHROPIC: str = "claude-sonnet-4-5"
    YANDEX_API_KEY: str = ""
    YANDEX_FOLDER_ID: str = ""
    AI_MODEL_YANDEX: str = "yandexgpt-lite/latest"

    # Agora (видеозвонки)
    AGORA_APP_ID: str = ""
    AGORA_APP_CERTIFICATE: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


# Глобальный экземпляр настроек
settings = Settings()
