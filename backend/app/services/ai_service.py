"""AI-сервис с абстрактным провайдером — OpenAI и Anthropic.

Переключение провайдера через переменную AI_PROVIDER в .env.
"""

from abc import ABC, abstractmethod

from app.config import settings


# Системный промпт для AI-тьютора
TUTOR_SYSTEM_PROMPT = """Ты — персональный AI-тьютор для школьников и студентов.

Правила:
1. Объясняй просто и понятно, учитывая уровень ученика.
2. Используй режим Сократа — задавай наводящие вопросы вместо прямых ответов.
3. Если ученик ошибся — не давай сразу правильный ответ, а помоги найти ошибку.
4. Приводи примеры из реальной жизни.
5. Отвечай на русском языке.
6. Если попросили решить задачу — объясняй ход решения пошагово.
7. Поддерживай и мотивируй ученика.

Предмет: {subject}
Тема: {topic}
"""


class BaseAIProvider(ABC):
    """Абстрактный базовый класс для AI-провайдеров."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        subject: str = "Общий",
        topic: str = "Свободная тема",
    ) -> str:
        """Отправить сообщения и получить ответ от AI."""
        ...

    def _build_system_prompt(self, subject: str, topic: str) -> str:
        """Сформировать системный промпт с предметом и темой."""
        return TUTOR_SYSTEM_PROMPT.format(subject=subject, topic=topic)


class OpenAIProvider(BaseAIProvider):
    """Провайдер OpenAI (GPT)."""

    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.AI_MODEL_OPENAI

    async def chat(
        self,
        messages: list[dict],
        subject: str = "Общий",
        topic: str = "Свободная тема",
    ) -> str:
        """Отправить запрос в OpenAI API."""
        system_prompt = self._build_system_prompt(subject, topic)
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=2048,
            temperature=0.7,
        )
        return response.choices[0].message.content


class AnthropicProvider(BaseAIProvider):
    """Провайдер Anthropic (Claude)."""

    def __init__(self):
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.AI_MODEL_ANTHROPIC

    async def chat(
        self,
        messages: list[dict],
        subject: str = "Общий",
        topic: str = "Свободная тема",
    ) -> str:
        """Отправить запрос в Anthropic API."""
        system_prompt = self._build_system_prompt(subject, topic)

        response = await self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=messages,
            max_tokens=2048,
        )
        return response.content[0].text


def get_ai_provider() -> BaseAIProvider:
    """Получить AI-провайдер на основе настроек."""
    if settings.AI_PROVIDER == "anthropic":
        return AnthropicProvider()
    return OpenAIProvider()
