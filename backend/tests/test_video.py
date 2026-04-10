"""Тесты видеозвонков — генерация токенов."""

import pytest

from app.services.video_service import generate_agora_token


class TestVideoService:
    """Тесты сервиса видеозвонков."""

    def test_generate_test_token(self):
        """Генерация тестового токена (без AGORA_APP_CERTIFICATE)."""
        token = generate_agora_token(channel_name="test-channel", uid=42)
        assert isinstance(token, str)
        assert "test-channel" in token
        assert "42" in token

    def test_generate_different_tokens(self):
        """Разные вызовы генерируют разные токены."""
        token1 = generate_agora_token(channel_name="ch1", uid=1)
        token2 = generate_agora_token(channel_name="ch2", uid=2)
        assert token1 != token2

    def test_generate_token_with_custom_expire(self):
        """Генерация токена с кастомным временем жизни."""
        token = generate_agora_token(
            channel_name="test", uid=1, expire_seconds=7200,
        )
        assert isinstance(token, str)
        assert len(token) > 0
