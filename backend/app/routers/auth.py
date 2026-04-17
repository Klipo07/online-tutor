"""Роутер авторизации — регистрация, вход, обновление токена, выход, верификация email."""

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.tutor import TutorProfile
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterTutor,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    create_tutor_user,
    create_user,
    decode_token,
    get_user_by_email,
    get_user_by_id,
    verify_password,
)
from app.services.email_service import (
    generate_verification_token,
    hash_token,
    send_verification_email,
    token_expiry,
)

router = APIRouter()


async def _issue_verification_token(db: AsyncSession, user: User) -> str:
    """Сгенерировать новый токен верификации, записать в БД, вернуть raw-значение."""
    raw, hashed = generate_verification_token()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    user.email_verify_token_hash = hashed
    user.email_verify_token_expires_at = token_expiry()
    user.last_verification_sent_at = now
    await db.commit()
    return raw


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Регистрация нового пользователя.

    Единый эндпоинт для всех ролей. Pydantic discriminated union по `role`
    валидирует поля: для `role=tutor` обязательны subjects/price/experience.
    Сразу после регистрации отправляется письмо с подтверждением email.
    """
    # Проверяем, что email не занят
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )

    # Ветвление по типу регистрации
    if isinstance(data, RegisterTutor):
        user = await create_tutor_user(
            db,
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            subjects=data.subjects,
            price_per_hour=data.price_per_hour,
            experience_years=data.experience_years,
            bio=data.bio,
            education=data.education,
        )
    else:
        user = await create_user(
            db,
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            role=data.role,
        )

    # Генерируем и сохраняем токен верификации, письмо уходит в фоне
    raw_token = await _issue_verification_token(db, user)
    background_tasks.add_task(
        send_verification_email, user.email, user.first_name, raw_token
    )

    # Генерируем токены авторизации
    tokens = TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Вход в систему, возврат JWT-токенов."""
    user = await get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    tokens = TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Обновление access-токена по refresh-токену."""
    payload = decode_token(data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh-токен",
        )

    user_id = int(payload["sub"])
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/logout")
async def logout():
    """Выход из системы.

    На клиенте нужно удалить токены из хранилища.
    При необходимости можно добавить blacklist токенов в Redis.
    """
    return {"message": "Выход выполнен успешно"}


@router.post("/send-verification", status_code=status.HTTP_202_ACCEPTED)
async def send_verification(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Повторная отправка письма верификации.

    Защита от спама: cooldown `EMAIL_VERIFY_COOLDOWN_SECONDS` (по умолчанию 60с).
    Если email уже подтверждён — 409.
    """
    if current_user.email_verified_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email уже подтверждён",
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    last_sent = current_user.last_verification_sent_at
    if last_sent is not None:
        elapsed = (now - last_sent).total_seconds()
        cooldown = settings.EMAIL_VERIFY_COOLDOWN_SECONDS
        if elapsed < cooldown:
            retry_after = int(cooldown - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Письмо уже отправлено. Повтор возможен через {retry_after} сек.",
                headers={"Retry-After": str(retry_after)},
            )

    raw_token = await _issue_verification_token(db, current_user)
    background_tasks.add_task(
        send_verification_email, current_user.email, current_user.first_name, raw_token
    )
    return {
        "message": "Письмо отправлено",
        "cooldown_seconds": settings.EMAIL_VERIFY_COOLDOWN_SECONDS,
    }


@router.get("/verify-email")
async def verify_email(
    token: str = Query(..., min_length=10, max_length=200),
    db: AsyncSession = Depends(get_db),
):
    """Подтверждение email по токену из письма.

    Если пользователь — репетитор, после подтверждения автоматически
    ставим `TutorProfile.is_verified = true` → попадает в маркетплейс.
    """
    hashed = hash_token(token)
    result = await db.execute(
        select(User).where(User.email_verify_token_hash == hashed)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Токен недействителен или уже использован",
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if user.email_verify_token_expires_at is None or user.email_verify_token_expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Срок действия ссылки истёк. Запросите новое письмо.",
        )

    # Помечаем email подтверждённым, очищаем токен
    user.email_verified_at = now
    user.email_verify_token_hash = None
    user.email_verify_token_expires_at = None

    # Если репетитор — автоматически становится verified в маркетплейсе
    profile_res = await db.execute(
        select(TutorProfile).where(TutorProfile.user_id == user.id)
    )
    profile = profile_res.scalar_one_or_none()
    if profile is not None and not profile.is_verified:
        profile.is_verified = True

    await db.commit()
    return {
        "message": "Email подтверждён",
        "user_id": user.id,
        "email": user.email,
        "tutor_verified": profile.is_verified if profile else None,
    }
