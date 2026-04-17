"""Сервис авторизации — хеширование паролей, генерация JWT."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.tutor import TutorProfile
from app.models.user import User, UserRole

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Хешировать пароль."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверить пароль по хешу."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    """Создать access-токен."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Создать refresh-токен."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Декодировать и валидировать JWT-токен."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Найти пользователя по email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Найти пользователя по ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str,
    bio: str | None = None,
) -> User:
    """Создать нового пользователя (ученик/родитель)."""
    user = User(
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        role=UserRole(role),
        bio=bio,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_tutor_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    subjects: list[str],
    price_per_hour: float,
    experience_years: int,
    bio: str | None = None,
    education: str | None = None,
) -> User:
    """Создать репетитора: User + TutorProfile в одной транзакции.

    Профиль создаётся с is_verified=True, чтобы новые репетиторы сразу
    появлялись в маркетплейсе учеников. После настройки реального SMTP
    флаг можно вернуть в False и активировать через подтверждение email.
    """
    user = User(
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        role=UserRole.tutor,
        bio=bio,
    )
    db.add(user)
    await db.flush()

    profile = TutorProfile(
        user_id=user.id,
        subjects=subjects,
        price_per_hour=price_per_hour,
        experience_years=experience_years,
        education=education,
        is_verified=True,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)
    return user
