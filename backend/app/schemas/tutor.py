"""Pydantic-схемы для репетиторов и отзывов."""

from pydantic import BaseModel, ConfigDict, Field


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
