"""Сервис видеозвонков — генерация Agora RTC токенов.

Реализация по спецификации Agora:
https://docs.agora.io/en/video-calling/develop/authentication-workflow

Токен строится на основе HMAC-SHA256 с APP_CERTIFICATE.
"""

import hashlib
import hmac
import struct
import time
import secrets
from collections import OrderedDict

from app.config import settings


# Типы привилегий Agora
PRIVILEGES = {
    "join_channel": 1,
    "publish_audio": 2,
    "publish_video": 3,
    "publish_data": 4,
}

# Версия токена
TOKEN_VERSION = "007"


def _pack_uint16(value: int) -> bytes:
    return struct.pack("<H", value)


def _pack_uint32(value: int) -> bytes:
    return struct.pack("<I", value)


def _pack_string(value: str) -> bytes:
    encoded = value.encode("utf-8")
    return _pack_uint16(len(encoded)) + encoded


def _pack_map(privileges: dict[int, int]) -> bytes:
    ordered = OrderedDict(sorted(privileges.items()))
    result = _pack_uint16(len(ordered))
    for key, value in ordered.items():
        result += _pack_uint16(key) + _pack_uint32(value)
    return result


def generate_agora_token(
    channel_name: str,
    uid: int,
    expire_seconds: int = 3600,
) -> str:
    """Генерация RTC-токена для Agora.

    Если AGORA_APP_CERTIFICATE не задан — возвращаем
    тестовый токен (для разработки без Agora).
    """
    app_id = settings.AGORA_APP_ID
    app_certificate = settings.AGORA_APP_CERTIFICATE

    # Режим разработки без Agora
    if not app_certificate:
        return f"test-token-{channel_name}-{uid}-{secrets.token_hex(8)}"

    current_time = int(time.time())
    expire_time = current_time + expire_seconds

    # Привилегии: полный доступ к каналу
    privileges = {
        PRIVILEGES["join_channel"]: expire_time,
        PRIVILEGES["publish_audio"]: expire_time,
        PRIVILEGES["publish_video"]: expire_time,
        PRIVILEGES["publish_data"]: expire_time,
    }

    # Собираем сообщение для подписи
    message = _pack_uint32(0)  # salt (не используем)
    message += _pack_uint32(current_time)
    message += _pack_uint32(expire_time)
    message += _pack_map(privileges)

    # Подпись HMAC-SHA256
    uid_str = str(uid)
    content = _pack_string(app_id)
    content += _pack_string(channel_name)
    content += _pack_string(uid_str)
    content += message

    signature = hmac.new(
        app_certificate.encode("utf-8"),
        content,
        hashlib.sha256,
    ).digest()

    # Формируем токен
    import base64
    token_content = _pack_string(app_id)
    token_content += _pack_string(channel_name)
    token_content += _pack_string(uid_str)
    token_content += _pack_uint16(len(signature)) + signature
    token_content += message

    token = TOKEN_VERSION + base64.b64encode(token_content).decode("utf-8")
    return token
