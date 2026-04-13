"""Сид демо-данных: предметы + по одному репетитору на каждый предмет.

Запуск:
    docker exec ai_tutor_backend python -m scripts.seed_tutors

Идемпотентно — повторный запуск не создаст дубли (проверка по email и name).
"""

import asyncio
import random
from decimal import Decimal

from faker import Faker
from sqlalchemy import select

from app.database import async_session
from app.models.subject import Subject
from app.models.tutor import TutorProfile
from app.models.user import User, UserRole
from app.services.auth_service import hash_password


SUBJECTS = [
    ("Математика", "math", "Алгебра, геометрия, подготовка к ЕГЭ/ОГЭ", "calculator"),
    ("Русский язык", "russian", "Орфография, пунктуация, сочинения", "book"),
    ("Физика", "physics", "Механика, термодинамика, электричество", "atom"),
    ("Химия", "chemistry", "Органика, неорганика, задачи по химии", "flask"),
    ("Биология", "biology", "Ботаника, зоология, анатомия, генетика", "leaf"),
    ("История", "history", "История России и мира, подготовка к ЕГЭ", "landmark"),
    ("Обществознание", "social", "Право, экономика, политология", "users"),
    ("Английский язык", "english", "Грамматика, разговорный, IELTS/TOEFL", "globe"),
    ("Информатика", "informatics", "Программирование, алгоритмы, ЕГЭ по информатике", "code"),
    ("География", "geography", "Физическая и экономическая география", "map"),
    ("Литература", "literature", "Русская и зарубежная литература, анализ", "feather"),
]


def _education() -> str:
    universities = ["МГУ", "МФТИ", "СПбГУ", "ВШЭ", "МГПУ", "РГПУ им. Герцена", "НГУ"]
    faculties = ["филологический", "физико-математический", "исторический", "биологический", "химический"]
    return f"{random.choice(universities)}, {random.choice(faculties)} факультет"


async def seed_subjects(db, fake: Faker) -> dict[str, Subject]:
    """Создать предметы, если их ещё нет. Возвращает {name: Subject}."""
    existing = {s.name: s for s in (await db.execute(select(Subject))).scalars().all()}
    created = 0
    for name, slug, description, icon in SUBJECTS:
        if name in existing:
            continue
        subject = Subject(name=name, slug=slug, description=description, icon=icon)
        db.add(subject)
        existing[name] = subject
        created += 1
    if created:
        await db.commit()
        for s in existing.values():
            if s.id is None:
                await db.refresh(s)
    print(f"[subjects] уже было: {len(existing) - created}, создано: {created}")
    return existing


async def seed_tutors(db, fake: Faker) -> None:
    """По одному репетитору на каждый предмет. Идемпотентно по email."""
    created = 0
    skipped = 0
    for subject_name, slug, *_ in SUBJECTS:
        email = f"tutor.{slug}@ai-tutor.local"
        existing_user = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if existing_user:
            skipped += 1
            continue

        first_name = fake.first_name()
        last_name = fake.last_name()
        user = User(
            email=email,
            password_hash=hash_password("TutorDemo1"),
            first_name=first_name,
            last_name=last_name,
            role=UserRole.tutor,
            avatar_url=f"https://i.pravatar.cc/300?u={slug}",
        )
        db.add(user)
        await db.flush()

        profile = TutorProfile(
            user_id=user.id,
            subjects=[subject_name],
            price_per_hour=Decimal(random.choice([800, 1000, 1200, 1500, 1800, 2000])),
            experience_years=random.randint(2, 15),
            bio=(
                f"Преподаю {subject_name.lower()} уже несколько лет. "
                f"{fake.paragraph(nb_sentences=2)}"
            ),
            education=_education(),
            rating=Decimal(str(round(random.uniform(4.3, 5.0), 2))),
            reviews_count=random.randint(5, 80),
            is_verified=True,
        )
        db.add(profile)
        created += 1

    await db.commit()
    print(f"[tutors] уже было: {skipped}, создано: {created}")


async def main() -> None:
    fake = Faker("ru_RU")
    Faker.seed(42)
    random.seed(42)

    async with async_session() as db:
        await seed_subjects(db, fake)
        await seed_tutors(db, fake)
    print("Готово.")


if __name__ == "__main__":
    asyncio.run(main())
