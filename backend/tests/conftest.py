"""Конфигурация тестов — фикстуры для БД, клиента и аутентификации."""

import asyncio
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.models.subject import Subject, Topic
from app.models.tutor import TutorProfile
from app.services.auth_service import hash_password, create_access_token


# Тестовая БД — SQLite in-memory
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Общий event loop для всех тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Создание и очистка таблиц перед каждым тестом."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """Сессия БД для тестов."""
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """HTTP клиент для тестирования API."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Тестовый пользователь-ученик."""
    user = User(
        email="student@test.com",
        password_hash=hash_password("password123"),
        full_name="Иван Тестов",
        role=UserRole.student,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_tutor_user(db_session: AsyncSession) -> User:
    """Тестовый пользователь-репетитор."""
    user = User(
        email="tutor@test.com",
        password_hash=hash_password("password123"),
        full_name="Анна Репетиторова",
        role=UserRole.tutor,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_tutor_profile(db_session: AsyncSession, test_tutor_user: User) -> TutorProfile:
    """Тестовый профиль репетитора."""
    profile = TutorProfile(
        user_id=test_tutor_user.id,
        subjects=["Математика", "Физика"],
        price_per_hour=1500,
        experience_years=8,
        bio="Опытный преподаватель математики и физики",
        education="МГУ, мехмат",
        rating=4.8,
        reviews_count=0,
        is_verified=True,
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    return profile


@pytest_asyncio.fixture
async def test_subject(db_session: AsyncSession) -> Subject:
    """Тестовый предмет с темами."""
    subject = Subject(
        name="Математика",
        slug="math",
        description="Математика — царица наук",
        icon="📐",
    )
    db_session.add(subject)
    await db_session.flush()

    topics = [
        Topic(subject_id=subject.id, name="Квадратные уравнения", order=1),
        Topic(subject_id=subject.id, name="Производная", order=2),
        Topic(subject_id=subject.id, name="Интегралы", order=3),
    ]
    db_session.add_all(topics)
    await db_session.commit()
    await db_session.refresh(subject)
    return subject


@pytest_asyncio.fixture
def auth_headers(test_user: User) -> dict:
    """Заголовки авторизации для тестового пользователя."""
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def tutor_auth_headers(test_tutor_user: User) -> dict:
    """Заголовки авторизации для репетитора."""
    token = create_access_token(test_tutor_user.id)
    return {"Authorization": f"Bearer {token}"}
