"""Email-сервис — отправка писем через SMTP (Yandex Mail по умолчанию).

SMTP не настроен (пустой SMTP_USER) → отправка мягко пропускается, токен всё равно
сохраняется в БД (полезно в dev/test и пока пользователь не получил app-password).
"""

import asyncio
import hashlib
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

from app.config import settings


TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "emails" / "verify.html"


def generate_verification_token() -> tuple[str, str]:
    """Сгенерировать случайный токен + его SHA-256 хэш.

    В БД хранится только хэш — даже при утечке базы токены нельзя переиспользовать.
    """
    raw = secrets.token_urlsafe(48)
    hashed = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return raw, hashed


def hash_token(token: str) -> str:
    """Получить SHA-256 хэш токена (для поиска в БД)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_expiry() -> datetime:
    """Время истечения нового токена (naive UTC, как в БД)."""
    expires = datetime.now(timezone.utc) + timedelta(
        hours=settings.EMAIL_VERIFY_TTL_HOURS
    )
    return expires.replace(tzinfo=None)


def build_verify_url(token: str) -> str:
    """Собрать deep link для мобильного приложения."""
    return f"{settings.APP_DEEP_LINK_BASE}?token={token}"


def _render_html(first_name: str, verify_url: str) -> str:
    """Простой рендер шаблона — без Jinja2 для минимума зависимостей."""
    try:
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            f"<p>Здравствуйте, {first_name}!</p>"
            f'<p><a href="{verify_url}">Подтвердить email</a></p>'
        )
    return (
        template.replace("{{ first_name }}", first_name)
        .replace("{{ verify_url }}", verify_url)
        .replace("{{ ttl_hours }}", str(settings.EMAIL_VERIFY_TTL_HOURS))
    )


def _send_sync(to_email: str, subject: str, html_body: str) -> None:
    """Синхронная отправка через SMTP+SSL. Вызывается из потока."""
    msg = EmailMessage()
    from_name = settings.SMTP_FROM_NAME or "AI Tutor"
    from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content("Письмо содержит HTML. Откройте в почтовом клиенте с поддержкой HTML.")
    msg.add_alternative(html_body, subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(
        settings.SMTP_HOST, settings.SMTP_PORT, context=context, timeout=15
    ) as smtp:
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


async def send_verification_email(
    to_email: str, first_name: str, token: str
) -> bool:
    """Отправить письмо с ссылкой подтверждения.

    Возвращает True если попытка отправки была выполнена, False если SMTP
    не настроен (пустой SMTP_USER) — токен всё равно уже сохранён в БД,
    пользователь может получить его через debug-эндпоинт или логи.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        return False

    verify_url = build_verify_url(token)
    html = _render_html(first_name=first_name or "пользователь", verify_url=verify_url)
    subject = "Подтверждение email — AI Tutor"

    # smtplib блокирующий → выполняем в отдельном потоке, чтобы не тормозить event loop
    await asyncio.to_thread(_send_sync, to_email, subject, html)
    return True
