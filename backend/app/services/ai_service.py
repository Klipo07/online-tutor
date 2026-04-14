"""AI-сервис с абстрактным провайдером — Anthropic (Claude) и YandexGPT.

Переключение провайдера через переменную AI_PROVIDER в .env.
"""

from abc import ABC, abstractmethod

import httpx
from anthropic import AsyncAnthropic

from app.config import settings


# Базовые правила поведения — общие для всех предметов
BASE_RULES = """Ты — персональный AI-тьютор для школьников и студентов.

Правила:
1. Объясняй просто и понятно, учитывая уровень ученика.
2. Используй режим Сократа — задавай наводящие вопросы вместо прямых ответов.
3. Если ученик ошибся — не давай сразу правильный ответ, а помоги найти ошибку.
4. Приводи примеры из реальной жизни.
5. Отвечай на русском языке.
6. Если попросили решить задачу — объясняй ход решения пошагово.
7. Поддерживай и мотивируй ученика.
8. Если вопрос явно не по предмету — мягко верни к теме, предложи открыть другой раздел."""


# Специализированные подсказки по каждому предмету — дают AI сразу нужный контекст,
# что экономит токены и делает ответы точнее
SUBJECT_PROMPTS: dict[str, str] = {
    "Математика": (
        "Специализация: математика (алгебра, геометрия, тригонометрия, анализ, теория вероятностей). "
        "Используй LaTeX-подобную запись формул в тексте (например, x^2, sqrt(x), sin(a)). "
        "Разбирай задачи по шагам: условие → что дано → что найти → решение → проверка."
    ),
    "Русский язык": (
        "Специализация: русский язык (орфография, пунктуация, морфология, синтаксис, стилистика). "
        "Для каждого правила приводи формулировку + 2–3 примера + типичные исключения. "
        "Разбирая ошибку — указывай конкретное правило и его номер, если применимо."
    ),
    "Физика": (
        "Специализация: физика (механика, термодинамика, электричество, оптика, атомная физика). "
        "Записывай формулы явно, всегда указывай единицы измерения (СИ). "
        "Для задач: дано → СИ → формулы → вывод → численный ответ с единицами."
    ),
    "Химия": (
        "Специализация: химия (общая, неорганическая, органическая). "
        "Записывай химические уравнения с коэффициентами и стрелками (→, ↑, ↓). "
        "Для задач на растворы/моли — обязательно пиши, что такое M, n, m, V и как связаны."
    ),
    "Биология": (
        "Специализация: биология (ботаника, зоология, анатомия, генетика, экология). "
        "Используй терминологию, но каждый сложный термин поясняй в скобках. "
        "Для классификаций — давай иерархию (царство → тип → класс → ...)."
    ),
    "История": (
        "Специализация: история (всеобщая и отечественная). "
        "Всегда указывай даты/века. Для событий: причины → ход → итоги → значение. "
        "Упоминай ключевых деятелей с краткой ролью. Не путай факты — если не уверен, скажи."
    ),
    "Обществознание": (
        "Специализация: обществознание (экономика, право, политология, социология, философия). "
        "Определения давай строго по школьному/вузовскому курсу. "
        "Для ЕГЭ-заданий с развернутым ответом — опирайся на критерии ФИПИ."
    ),
    "Английский": (
        "Специализация: английский язык (грамматика, лексика, произношение, разговорная практика). "
        "Если ученик пишет по-английски с ошибкой — показывай исправление и объясняй на русском. "
        "Для грамматики — давай правило, формулу времени/конструкции и 2–3 примера."
    ),
    "Английский язык": (
        "Специализация: английский язык. Если ученик пишет по-английски с ошибкой — "
        "показывай исправление и объясняй на русском. Для грамматики — давай правило, "
        "формулу конструкции и 2–3 примера."
    ),
    "Информатика": (
        "Специализация: информатика (алгоритмы, программирование на Python/Pascal, системы счисления, "
        "логика, архитектура ПК, задачи ЕГЭ). "
        "Код оформляй в блоках, разбирай пошагово. Для задач на системы счисления — показывай перевод."
    ),
    "География": (
        "Специализация: география (физическая, экономическая, страноведение, картография). "
        "Привязывай ответы к конкретным регионам/странам. Для ЕГЭ — используй климатические пояса, "
        "тектонику плит, экономические районы РФ."
    ),
    "Литература": (
        "Специализация: литература (русская и зарубежная). "
        "Для анализа произведений — автор, эпоха, жанр, сюжет, герои, темы, проблематика, художественные средства. "
        "Цитируй точно, если не помнишь — говори, что нужно уточнить."
    ),
}


def _build_subject_prompt(subject: str, topic: str) -> str:
    """Сформировать системный промпт, заточенный под конкретный предмет.

    Если предмет в справочнике — добавляется специализированный блок, что даёт AI
    сразу нужный контекст (меньше токенов на уточнения, точнее ответы).
    """
    subject_clean = (subject or "").strip()
    specialization = SUBJECT_PROMPTS.get(subject_clean)

    parts = [BASE_RULES]
    if specialization:
        parts.append(f"\n{specialization}")
    else:
        parts.append(f"\nТекущий предмет: {subject_clean or 'общий'}.")

    if topic and topic.lower() not in ("свободная тема", ""):
        parts.append(f"\nТекущая тема: {topic}.")

    return "\n".join(parts)


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
        return _build_subject_prompt(subject, topic)


class AnthropicProvider(BaseAIProvider):
    """Провайдер Anthropic (Claude)."""

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.AI_MODEL_ANTHROPIC

    async def chat(
        self,
        messages: list[dict],
        subject: str = "Общий",
        topic: str = "Свободная тема",
    ) -> str:
        """Отправить запрос в Anthropic API."""
        response = await self.client.messages.create(
            model=self.model,
            system=self._build_system_prompt(subject, topic),
            messages=messages,
            max_tokens=2048,
        )
        return response.content[0].text


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
        yandex_messages = [
            {"role": "system", "text": self._build_system_prompt(subject, topic)}
        ]
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
    if settings.AI_PROVIDER == "yandex":
        return YandexProvider()
    return AnthropicProvider()
