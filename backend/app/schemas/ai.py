"""Pydantic-схемы для AI-тьютора."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageRequest(BaseModel):
    """Запрос — сообщение AI-тьютору."""
    message: str = Field(min_length=1, max_length=5000)
    session_id: int | None = None
    subject: str = "Общий"
    topic: str = "Свободная тема"


class ChatMessageResponse(BaseModel):
    """Ответ от AI-тьютора."""
    session_id: int
    role: str = "assistant"
    content: str


class ChatHistoryMessage(BaseModel):
    """Одно сообщение из истории чата."""
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseModel):
    """История чата."""
    session_id: int
    subject: str | None
    topic: str | None
    messages: list[ChatHistoryMessage]


class HomeworkRequest(BaseModel):
    """Запрос на проверку домашнего задания."""
    task_text: str = Field(min_length=1, max_length=10000, description="Текст задачи")
    student_answer: str = Field(min_length=1, max_length=10000, description="Ответ ученика")
    subject: str = "Математика"


class HomeworkResponse(BaseModel):
    """Результат проверки домашнего задания."""
    is_correct: bool
    score: int = Field(ge=0, le=100)
    feedback: str
    correct_solution: str


class GenerateTestRequest(BaseModel):
    """Запрос на генерацию теста."""
    subject: str
    topic: str
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    num_questions: int = Field(default=5, ge=1, le=20)


class TestQuestion(BaseModel):
    """Один вопрос теста."""
    id: int
    question: str
    options: list[str] | None = None
    type: str = "multiple_choice"


class GenerateTestResponse(BaseModel):
    """Сгенерированный тест."""
    test_id: int
    subject: str
    topic: str
    difficulty: str
    questions: list[TestQuestion]


class SubmitTestRequest(BaseModel):
    """Ответы на тест."""
    test_id: int
    answers: dict[str, str]


class SubmitTestResponse(BaseModel):
    """Результат проверки теста."""
    score: int
    total: int
    percentage: int
    feedback: str
    details: list[dict]
