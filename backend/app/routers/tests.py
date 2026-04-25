"""Роутер тестов — банк заданий ОГЭ/ЕГЭ с фильтрами."""

import json
import logging
import re
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.task_numbers import get_max_task_number
from app.database import get_db
from app.dependencies import get_current_user
from app.models.subject import Subject
from app.models.test import Difficulty, ExamType, Test, TestFeedback, FeedbackRating
from app.models.user import User
from app.services import cache
from app.services.ai_service import get_ai_provider
from app.services.math_format import format_questions, latex_to_unicode

logger = logging.getLogger(__name__)

router = APIRouter()

# Справочники теста меняются редко (только при добавлении новых задач в банк)
TESTS_META_TTL = 600

# Валидные JSON escape-символы, которые мы НЕ хотим экранировать повторно.
# По RFC 8259 валидны и `\b`, `\f` — но в реальных текстах они не встречаются,
# зато конфликтуют с LaTeX-командами `\beta`, `\frac` и т.п. Поэтому их
# исключаем — пусть `\b`/`\f` от LLM экранируются как обычные backslash.
_VALID_JSON_ESCAPES = set('"\\/nrtu')


def _sanitize_llm_json(raw: str) -> str:
    """Чистим ответ LLM перед `json.loads`.

    LLM любят:
    1) обернуть JSON в ```...``` (markdown fence) — отрезаем фенсы
    2) писать LaTeX вроде `$\\sqrt{x}$`, что в JSON-строке делает `\\s`
       невалидным escape — экранируем такие backslash в `\\\\`.

    Работаем по подстроке от первой `[` до последней `]` — этого достаточно
    для нашего use-case (ответ всегда массив вопросов).
    """
    text = raw.strip()
    # Удаляем markdown-фенсы вида ```json ... ```
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)

    start = text.find("[")
    end = text.rfind("]") + 1
    if start < 0 or end <= start:
        raise ValueError("JSON-массив не найден в ответе")
    body = text[start:end]

    # Экранируем одиночные backslash, не являющиеся началом валидного JSON-escape.
    # Например, `\s`, `\f` (где \f это формфид — валиден, не трогаем),
    # `\p`, `\c` и т.п. в LaTeX-командах превращаем в `\\s`, `\\p`.
    def _fix(m: re.Match[str]) -> str:
        nxt = m.group(1)
        return f"\\\\{nxt}" if nxt not in _VALID_JSON_ESCAPES else m.group(0)

    body = re.sub(r"\\(.)", _fix, body)
    return body


class TestRecommendRequest(BaseModel):
    """Запрос на адаптивный подбор тестов."""
    subject_id: int
    exam_type: ExamType
    task_number: int | None = None
    limit: int = Field(5, ge=1, le=20)


class TestAiGenerateRequest(BaseModel):
    """Запрос на AI-генерацию одиночного теста.

    `math_variant` имеет смысл только для математики ЕГЭ ('profile' | 'base').
    Для остальных комбинаций предмета/формата параметр игнорируется.
    """
    subject_id: int
    exam_type: ExamType
    task_number: int | None = Field(default=None, ge=1, le=50)
    difficulty: Difficulty = Difficulty.medium
    num_questions: int = Field(default=5, ge=1, le=30)
    math_variant: Literal["profile", "base"] | None = None


async def _pick_difficulty_for_user(
    db: AsyncSession, user_id: int, subject_id: int
) -> Difficulty:
    """Подобрать стартовую сложность на основе последних фидбеков пользователя.

    Смотрим последние 10 оценок по данному предмету. Правило:
    - >=60% too_easy  → hard
    - >=60% too_hard  → easy
    - иначе           → medium
    Если фидбеков нет — medium (нейтральный старт).
    """
    q = (
        select(TestFeedback.rating)
        .join(Test, Test.id == TestFeedback.test_id)
        .where(TestFeedback.user_id == user_id, Test.subject_id == subject_id)
        .order_by(TestFeedback.created_at.desc())
        .limit(10)
    )
    result = await db.execute(q)
    ratings = [r[0] for r in result.all()]
    if not ratings:
        return Difficulty.medium

    total = len(ratings)
    too_easy = sum(1 for r in ratings if r == FeedbackRating.too_easy)
    too_hard = sum(1 for r in ratings if r == FeedbackRating.too_hard)

    if too_easy / total >= 0.6:
        return Difficulty.hard
    if too_hard / total >= 0.6:
        return Difficulty.easy
    return Difficulty.medium


class TestFeedbackRequest(BaseModel):
    """Фидбек после прохождения теста."""
    rating: FeedbackRating
    comment: str | None = Field(default=None, max_length=500)


def _image_url(rel_path: str) -> str:
    """Превращаем относительный путь image_paths в URL для фронта."""
    return f"/uploads/{rel_path.lstrip('/')}"


def _test_to_list_item(t: Test) -> dict:
    """Форматируем тест для списка — topic с конвертацией формул."""
    return {
        "id": t.id,
        "subject_id": t.subject_id,
        "topic": latex_to_unicode(t.topic),
        "exam_type": t.exam_type.value,
        "task_number": t.task_number,
        "difficulty": t.difficulty.value,
        "questions_count": len(t.questions) if isinstance(t.questions, list) else 0,
        "has_images": bool(t.image_paths),
        "from_bank": not t.created_by_ai,
        "created_at": t.created_at.isoformat(),
    }


@router.get("")
async def list_tests(
    subject_id: int | None = None,
    exam_type: ExamType | None = None,
    task_number: int | None = None,
    difficulty: Difficulty | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список тестов с фильтрами."""
    query = select(Test)
    if subject_id is not None:
        query = query.where(Test.subject_id == subject_id)
    if exam_type is not None:
        query = query.where(Test.exam_type == exam_type)
    if task_number is not None:
        query = query.where(Test.task_number == task_number)
    if difficulty is not None:
        query = query.where(Test.difficulty == difficulty)

    query = query.order_by(Test.id.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    tests = result.scalars().all()

    return [_test_to_list_item(t) for t in tests]


@router.post("/recommend")
async def recommend_tests(
    data: TestRecommendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Адаптивный подбор тестов под пользователя.

    Смотрим фидбеки (слишком легко / в самый раз / слишком сложно) по предмету,
    подбираем сложность и случайные тесты из банка. Если под подобранную сложность
    тестов нет — откатываемся к medium, потом к any.
    """
    picked = await _pick_difficulty_for_user(db, current_user.id, data.subject_id)

    async def _fetch(diff: Difficulty | None) -> list[Test]:
        q = select(Test).where(
            Test.subject_id == data.subject_id,
            Test.exam_type == data.exam_type,
        )
        if data.task_number is not None:
            q = q.where(Test.task_number == data.task_number)
        if diff is not None:
            q = q.where(Test.difficulty == diff)
        # func.random() работает на PostgreSQL и SQLite (random() alias)
        q = q.order_by(func.random()).limit(data.limit)
        res = await db.execute(q)
        return list(res.scalars().all())

    tests = await _fetch(picked)
    fallback_used = False
    if not tests and picked != Difficulty.medium:
        tests = await _fetch(Difficulty.medium)
        fallback_used = True
    if not tests:
        tests = await _fetch(None)
        fallback_used = True

    return {
        "difficulty": picked.value,
        "fallback_used": fallback_used,
        "tests": [_test_to_list_item(t) for t in tests],
    }


@router.post("/ai-generate")
async def ai_generate_test(
    data: TestAiGenerateRequest,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI-генерация одиночного теста в формате ОГЭ/ЕГЭ.

    Для manual-режима: пользователь выбрал предмет/номер задания/сложность,
    backend обращается к провайдеру, парсит JSON, сохраняет в `tests` с
    `created_by_ai=True`. Дальше работает обычный flow `/ai/submit-test` +
    `/tests/{id}/feedback` (id совпадает).

    Возвращает ту же форму, что и `GET /tests/{id}` — без поля correct.
    """
    subject = await db.get(Subject, data.subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Предмет не найден")

    # math_variant имеет смысл только для математики ЕГЭ
    is_math_ege = subject.slug == "math" and data.exam_type == ExamType.ege
    math_variant = data.math_variant if is_math_ege else None

    # Валидация номера задания против справочника ФИПИ
    if data.task_number is not None:
        max_n = get_max_task_number(subject.slug, data.exam_type.value, math_variant)
        if data.task_number > max_n:
            raise HTTPException(
                status_code=400,
                detail=f"Для {subject.name} в этом формате доступны задания 1..{max_n}",
            )

    # Подтягиваем до 2 реальных заданий из банка как few-shot — чтобы структура
    # и стиль совпадали с ФИПИ. Сначала пробуем точное совпадение
    # subject+exam_type+task_number, потом без task_number
    async def _fetch_examples(with_task_number: bool) -> list[Test]:
        q = select(Test).where(
            Test.subject_id == data.subject_id,
            Test.exam_type == data.exam_type,
        )
        if with_task_number and data.task_number is not None:
            q = q.where(Test.task_number == data.task_number)
        q = q.limit(2)
        r = await db.execute(q)
        return list(r.scalars().all())

    examples = await _fetch_examples(with_task_number=True)
    if not examples:
        examples = await _fetch_examples(with_task_number=False)

    examples_block = ""
    if examples:
        sample_questions: list = []
        for t in examples:
            qs = t.questions if isinstance(t.questions, list) else []
            if qs:
                sample_questions.append(qs[0])
        if sample_questions:
            examples_block = (
                "Примеры заданий такого же формата (стиль и уровень сложности):\n"
                f"{json.dumps(sample_questions, ensure_ascii=False, indent=2)}\n\n"
            )

    exam_label = {"ege": "ЕГЭ", "oge": "ОГЭ", "regular": "тренировочный"}[data.exam_type.value]
    # Для математики ЕГЭ — добавляем профильную/базовую к названию формата
    if is_math_ege and math_variant:
        variant_label = "профильная" if math_variant == "profile" else "базовая"
        exam_label = f"{exam_label} ({variant_label})"
    difficulty_label = {"easy": "лёгкий", "medium": "средний", "hard": "сложный"}[data.difficulty.value]
    task_label = f"задание №{data.task_number}" if data.task_number else "свободная тема"

    # Подчёркиваем ФИПИ-формат только для реальных экзаменов
    fipi_hint = (
        f"Это задания строго в формате ФИПИ для {exam_label} по предмету «{subject.name}». "
        if data.exam_type != ExamType.regular
        else ""
    )

    prompt = (
        f"Сгенерируй тест по предмету «{subject.name}» в формате {exam_label}, "
        f"{task_label}, уровень сложности — {difficulty_label}.\n"
        f"{fipi_hint}"
        f"Количество вопросов: {data.num_questions}.\n\n"
        f"{examples_block}"
        f"Формат ответа — СТРОГО JSON-массив без пояснений:\n"
        f'[{{"question": "текст вопроса", "options": ["A", "B", "C", "D"], '
        f'"correct": "A", "type": "multiple_choice", "explanation": "краткое пояснение"}}]\n\n'
        f"Требования:\n"
        f"- Формулы оборачивай в $...$ (LaTeX, например $x^2$, $\\sqrt{{9}}$).\n"
        f"- Варианты ответов различимы, ровно один правильный.\n"
        f"- На русском языке.\n"
        f"- Возвращай ЧИСТЫЙ JSON-массив без markdown-обёрток ```.\n"
        f"- В JSON-строках экранируй обратный слэш как \\\\ "
        f"(например, $\\\\sqrt{{9}}$, а не $\\sqrt{{9}}$)."
    )

    provider = get_ai_provider()
    try:
        response = await provider.chat(
            [{"role": "user", "content": prompt}],
            subject=subject.name,
            topic=task_label,
        )
    except Exception as e:
        logger.exception("AI provider failed in ai_generate_test")
        raise HTTPException(status_code=502, detail=f"Ошибка AI-провайдера: {e}")

    # Парсим JSON из ответа. LLM могут вернуть LaTeX с невалидными JSON-escape
    # (\sqrt, \pi, \frac) — `_sanitize_llm_json` чинит такие места.
    try:
        sanitized = _sanitize_llm_json(response)
        questions_raw = json.loads(sanitized)
        if not isinstance(questions_raw, list) or not questions_raw:
            raise ValueError("Пустой или невалидный массив вопросов")
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(
            "AI ai-generate parse failed: %s; response head: %s",
            e,
            response[:300],
        )
        raise HTTPException(
            status_code=502,
            detail="AI вернул невалидный формат — попробуйте ещё раз",
        )

    # AI иногда возвращает дубли в options ('предположить', 'предположить').
    # Дедуплицируем с сохранением порядка — иначе UI ругается на duplicate keys
    # и пользователь видит «два одинаковых варианта».
    for q in questions_raw:
        opts = q.get("options")
        if isinstance(opts, list):
            seen = set()
            uniq = []
            for o in opts:
                key = str(o).strip().lower()
                if key in seen:
                    continue
                seen.add(key)
                uniq.append(o)
            q["options"] = uniq

    # Сохраняем в БД — дальше обычный /ai/submit-test работает как с банковым тестом
    topic = f"{exam_label}, {task_label}"
    new_test = Test(
        subject_id=data.subject_id,
        topic=topic,
        exam_type=data.exam_type,
        task_number=data.task_number,
        difficulty=data.difficulty,
        questions=questions_raw,
        created_by_ai=True,
    )
    db.add(new_test)
    await db.commit()
    await db.refresh(new_test)

    # Формируем ответ в той же форме, что GET /tests/{id}
    raw_questions = []
    for i, q in enumerate(questions_raw):
        raw_questions.append({
            "id": i + 1,
            "question": q.get("question", ""),
            "options": q.get("options"),
            "type": q.get("type", "multiple_choice"),
        })
    questions = format_questions(raw_questions)

    return {
        "id": new_test.id,
        "subject_id": new_test.subject_id,
        "topic": latex_to_unicode(new_test.topic),
        "exam_type": new_test.exam_type.value,
        "task_number": new_test.task_number,
        "difficulty": new_test.difficulty.value,
        "questions": questions,
        "image_urls": [],
        "source_url": None,
        "from_bank": False,
    }


@router.get("/task-numbers")
async def list_task_numbers(
    subject_id: int,
    exam_type: ExamType,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список доступных номеров заданий для предмета и формата."""
    cache_key = f"tests:task-numbers:{subject_id}:{exam_type.value}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    query = (
        select(Test.task_number, func.count())
        .where(
            Test.subject_id == subject_id,
            Test.exam_type == exam_type,
            Test.task_number.is_not(None),
        )
        .group_by(Test.task_number)
        .order_by(Test.task_number)
    )
    result = await db.execute(query)
    payload = [{"task_number": n, "count": c} for n, c in result.all() if n is not None]
    await cache.set(cache_key, payload, ttl=TESTS_META_TTL)
    return payload


@router.get("/task-range")
async def get_task_range(
    subject_id: int,
    exam_type: ExamType,
    math_variant: Literal["profile", "base"] | None = None,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Максимальный номер задания ФИПИ для предмета и формата.

    Для математики ЕГЭ нужно передать `math_variant=profile|base`.
    Для остальных предметов параметр игнорируется.
    """
    subject = await db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Предмет не найден")

    max_n = get_max_task_number(subject.slug, exam_type.value, math_variant)
    return {
        "subject_id": subject_id,
        "subject_slug": subject.slug,
        "exam_type": exam_type.value,
        "math_variant": math_variant,
        "max_task_number": max_n,
    }


@router.get("/subjects-with-tests")
async def subjects_with_tests(
    exam_type: ExamType | None = None,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Предметы, по которым есть тесты (с подсчётом)."""
    # v2 — после добавления slug в payload (старый кэш без slug)
    cache_key = f"tests:subjects-with-tests:v2:{exam_type.value if exam_type else 'all'}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    query = (
        select(Subject.id, Subject.name, Subject.slug, func.count(Test.id))
        .join(Test, Test.subject_id == Subject.id)
    )
    if exam_type is not None:
        query = query.where(Test.exam_type == exam_type)
    query = query.group_by(Subject.id, Subject.name, Subject.slug).order_by(Subject.name)
    result = await db.execute(query)
    payload = [
        {"id": sid, "name": name, "slug": slug, "tests_count": cnt}
        for sid, name, slug, cnt in result.all()
    ]
    await cache.set(cache_key, payload, ttl=TESTS_META_TTL)
    return payload


@router.get("/{test_id}")
async def get_test(
    test_id: int,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить тест с вопросами (без правильных ответов)."""
    result = await db.execute(select(Test).where(Test.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")

    # Вопросы — без поля correct (его проверяем на submit).
    # Прогоняем через format_questions: LaTeX-маркеры → unicode (² √ π и т.п.)
    raw_questions = []
    for i, q in enumerate(test.questions or []):
        raw_questions.append(
            {
                "id": i + 1,
                "question": q.get("question", ""),
                "options": q.get("options"),
                "type": q.get("type", "multiple_choice"),
            }
        )
    questions = format_questions(raw_questions)

    image_urls = [_image_url(p) for p in (test.image_paths or [])]

    return {
        "id": test.id,
        "subject_id": test.subject_id,
        "topic": latex_to_unicode(test.topic),
        "exam_type": test.exam_type.value,
        "task_number": test.task_number,
        "difficulty": test.difficulty.value,
        "questions": questions,
        "image_urls": image_urls,
        "source_url": test.source_url,
        "from_bank": not test.created_by_ai,
    }


@router.post("/{test_id}/feedback", status_code=201)
async def submit_feedback(
    test_id: int,
    data: TestFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Оставить фидбек по тесту — лёгкий/нормальный/сложный.

    Используется для сбора сигналов об оценке сложности и будущей автокоррекции.
    """
    # Проверяем существование теста
    exists = await db.execute(select(Test.id).where(Test.id == test_id))
    if exists.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Тест не найден")

    feedback = TestFeedback(
        user_id=current_user.id,
        test_id=test_id,
        rating=data.rating,
        comment=(data.comment or "").strip() or None,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return {
        "id": feedback.id,
        "test_id": feedback.test_id,
        "rating": feedback.rating.value,
        "created_at": feedback.created_at.isoformat(),
    }
