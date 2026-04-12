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


class GeminiProvider(BaseAIProvider):
    """Провайдер Google Gemini через OpenAI-совместимый API."""

    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        self.model = settings.AI_MODEL_GEMINI

    async def chat(
        self,
        messages: list[dict],
        subject: str = "Общий",
        topic: str = "Свободная тема",
    ) -> str:
        """Отправить запрос в Google Gemini API."""
        system_prompt = self._build_system_prompt(subject, topic)
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=2048,
            temperature=0.7,
        )
        return response.choices[0].message.content


class OpenRouterProvider(BaseAIProvider):
    """Провайдер OpenRouter — агрегатор AI API через OpenAI-совместимый endpoint."""

    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = settings.AI_MODEL_OPENROUTER

    async def chat(
        self,
        messages: list[dict],
        subject: str = "Общий",
        topic: str = "Свободная тема",
    ) -> str:
        """Отправить запрос в OpenRouter API."""
        system_prompt = self._build_system_prompt(subject, topic)
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=2048,
            temperature=0.7,
        )
        return response.choices[0].message.content


class YandexProvider(BaseAIProvider):
    """Провайдер YandexGPT через REST API Yandex Cloud Foundation Models."""

    API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    def __init__(self):
        self.api_key = settings.YANDEX_API_KEY
        self.folder_id = settings.YANDEX_FOLDER_ID
        self.model = settings.AI_MODEL_YANDEX

    async def chat(
        self,
        messages: list[dict],
        subject: str = "Общий",
        topic: str = "Свободная тема",
    ) -> str:
        """Отправить запрос в YandexGPT API."""
        import httpx

        system_prompt = self._build_system_prompt(subject, topic)
        yandex_messages = [{"role": "system", "text": system_prompt}]
        for m in messages:
            yandex_messages.append({"role": m["role"], "text": m["content"]})

        payload = {
            "modelUri": f"gpt://{self.folder_id}/{self.model}",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": "2000",
            },
            "messages": yandex_messages,
        }
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "x-folder-id": self.folder_id,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        return data["result"]["alternatives"][0]["message"]["text"]


def get_ai_provider() -> BaseAIProvider:
    """Получить AI-провайдер на основе настроек."""
    if settings.AI_PROVIDER == "anthropic":
        return AnthropicProvider()
    if settings.AI_PROVIDER == "gemini":
        return GeminiProvider()
    if settings.AI_PROVIDER == "openrouter":
        return OpenRouterProvider()
    if settings.AI_PROVIDER == "yandex":
        return YandexProvider()
    return OpenAIProvider()
