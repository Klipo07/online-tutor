"""Роутер предметов — список предметов и тем."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.subject import Subject, Topic
from app.schemas.subject import SubjectResponse, SubjectWithTopicsResponse, TopicResponse
from app.services import cache

router = APIRouter()

# Справочники меняются редко — можно держать долго
SUBJECTS_TTL = 3600
TOPICS_TTL = 3600


@router.get("/", response_model=list[SubjectResponse])
async def list_subjects(db: AsyncSession = Depends(get_db)):
    """Список всех предметов."""
    cached = await cache.get("subjects:list")
    if cached is not None:
        return cached

    result = await db.execute(select(Subject).order_by(Subject.name))
    subjects = result.scalars().all()
    payload = [SubjectResponse.model_validate(s).model_dump() for s in subjects]
    await cache.set("subjects:list", payload, ttl=SUBJECTS_TTL)
    return payload


@router.get("/{subject_id}", response_model=SubjectWithTopicsResponse)
async def get_subject(subject_id: int, db: AsyncSession = Depends(get_db)):
    """Предмет с его темами."""
    query = (
        select(Subject)
        .options(selectinload(Subject.topics))
        .where(Subject.id == subject_id)
    )
    result = await db.execute(query)
    subject = result.unique().scalar_one_or_none()

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Предмет не найден",
        )
    return subject


@router.get("/{subject_id}/topics", response_model=list[TopicResponse])
async def get_topics(subject_id: int, db: AsyncSession = Depends(get_db)):
    """Темы по предмету."""
    cache_key = f"subjects:{subject_id}:topics"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    # Проверяем что предмет существует
    subject = await db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Предмет не найден",
        )

    result = await db.execute(
        select(Topic)
        .where(Topic.subject_id == subject_id)
        .order_by(Topic.order)
    )
    topics = result.scalars().all()
    payload = [TopicResponse.model_validate(t).model_dump() for t in topics]
    await cache.set(cache_key, payload, ttl=TOPICS_TTL)
    return payload
