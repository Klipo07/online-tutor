"""Pydantic-схемы для предметов и тем."""

from pydantic import BaseModel


class TopicResponse(BaseModel):
    """Тема предмета."""
    id: int
    name: str
    order: int

    model_config = {"from_attributes": True}


class SubjectResponse(BaseModel):
    """Предмет."""
    id: int
    name: str
    slug: str
    description: str | None = None
    icon: str | None = None

    model_config = {"from_attributes": True}


class SubjectWithTopicsResponse(BaseModel):
    """Предмет с темами."""
    id: int
    name: str
    slug: str
    description: str | None = None
    icon: str | None = None
    topics: list[TopicResponse] = []

    model_config = {"from_attributes": True}
