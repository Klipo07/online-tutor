"""Pydantic-схемы для репетиторов и отзывов."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TutorResponse(BaseModel):
    """Профиль репетитора в ответе."""
    id: int
    user_id: int
    full_name: str
    subjects: list[str] = []
    price_per_hour: float
    experience_years: int
    bio: str | None = None
    education: str | None = None
    rating: float
    reviews_count: int
    is_verified: bool
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TutorListResponse(BaseModel):
    """Список репетиторов с пагинацией."""
    tutors: list[TutorResponse]
    total: int
    page: int
    per_page: int


class ReviewCreate(BaseModel):
    """Запрос на создание отзыва."""
    rating: int = Field(ge=1, le=5, description="Оценка от 1 до 5")
    comment: str = Field(min_length=5, max_length=2000, description="Текст отзыва")


class ReviewResponse(BaseModel):
    """Отзыв в ответе."""
    id: int
    tutor_id: int
    student_id: int
    student_name: str
    rating: int
    comment: str

    model_config = ConfigDict(from_attributes=True)


# === Расписание репетитора ===

class TutorScheduleResponse(BaseModel):
    """Рабочие часы репетитора по дням недели.

    Значение каждого дня: `[start_hour, end_hour]` или `null` (выходной).
    """
    mon: list[int] | None = None
    tue: list[int] | None = None
    wed: list[int] | None = None
    thu: list[int] | None = None
    fri: list[int] | None = None
    sat: list[int] | None = None
    sun: list[int] | None = None


class TutorScheduleUpdate(BaseModel):
    """Запрос на обновление рабочих часов. Валидация: start<end, 0..24."""
    mon: list[int] | None = None
    tue: list[int] | None = None
    wed: list[int] | None = None
    thu: list[int] | None = None
    fri: list[int] | None = None
    sat: list[int] | None = None
    sun: list[int] | None = None

    @field_validator("mon", "tue", "wed", "thu", "fri", "sat", "sun")
    @classmethod
    def _check_hours(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return None
        if len(v) != 2:
            raise ValueError("Должно быть два значения — [start, end]")
        start, end = v
        if not (0 <= start < end <= 24):
            raise ValueError("Часы должны быть 0..24 и start < end")
        return [int(start), int(end)]


# === Профиль (tutor-specific редактирование) ===

class TutorProfileUpdate(BaseModel):
    """Редактирование tutor-специфичных полей текущего репетитора."""
    subjects: list[str] | None = Field(None, min_length=1, max_length=10)
    price_per_hour: float | None = Field(None, ge=0, le=100000)
    experience_years: int | None = Field(None, ge=0, le=70)
    education: str | None = Field(None, max_length=500)


# === Статистика для дашборда репетитора ===

class TutorStatsResponse(BaseModel):
    """Агрегированные показатели для дашборда репетитора."""
    students_count: int
    sessions_completed: int
    sessions_upcoming: int
    earnings_month: float
    rating: float
    reviews_count: int
    next_session_at: datetime | None = None
    next_session_student: str | None = None
    next_session_subject: str | None = None
