"""Роутер AI-тьютора — чат, проверка ДЗ, генерация тестов."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage, AIProvider, MessageRole
from app.models.subject import Subject
from app.models.test import Test, TestAttempt, Difficulty
from app.schemas.ai import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryMessage,
    ChatHistoryResponse,
    HomeworkRequest,
    HomeworkResponse,
    GenerateTestRequest,
    GenerateTestResponse,
    SubmitTestRequest,
    SubmitTestResponse,
)
from app.services.ai_service import get_ai_provider
from app.services.progress_service import get_recommendations, update_progress_after_test

router = APIRouter()


@router.post("/chat", response_model=ChatMessageResponse)
async def chat(
    data: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отправить сообщение AI-тьютору.

    Если session_id не указан — создаётся новая сессия чата.
    AI помнит контекст диалога в рамках сессии.
    """
    provider = get_ai_provider()
    existing_session = None

    # Получить существующую сессию и историю
    if data.session_id:
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(
                ChatSession.id == data.session_id,
                ChatSession.user_id == current_user.id,
            )
        )
        existing_session = result.scalar_one_or_none()
        if not existing_session:
            raise HTTPException(status_code=404, detail="Сессия чата не найдена")

    # Собираем историю сообщений для контекста
    history = []
    if existing_session:
        history = [
            {"role": msg.role.value, "content": msg.content}
            for msg in existing_session.messages
        ]
    history.append({"role": "user", "content": data.message})

    # Получаем ответ от AI (до операций с БД)
    try:
        ai_response = await provider.chat(
            messages=history,
            subject=data.subject,
            topic=data.topic,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ошибка AI-провайдера: {str(e)}")

    # Создаём сессию если новая
    if not existing_session:
        provider_name = provider.__class__.__name__.replace("Provider", "").lower()
        existing_session = ChatSession(
            user_id=current_user.id,
            subject_id=None,
            topic=data.topic,
            provider=AIProvider(provider_name),
        )
        db.add(existing_session)
        await db.flush()

    # Сохраняем сообщение пользователя
    user_msg = ChatMessage(
        session_id=existing_session.id,
        role=MessageRole.user,
        content=data.message,
    )
    db.add(user_msg)

    # Сохраняем ответ AI
    assistant_msg = ChatMessage(
        session_id=existing_session.id,
        role=MessageRole.assistant,
        content=ai_response,
    )
    db.add(assistant_msg)
    await db.commit()

    return ChatMessageResponse(
        session_id=existing_session.id,
        content=ai_response,
    )


@router.get("/chat/history", response_model=list[ChatHistoryResponse])
async def chat_history(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить список сессий чата с историей сообщений."""
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .limit(limit)
    )
    sessions = result.scalars().all()

    return [
        ChatHistoryResponse(
            session_id=s.id,
            subject=None,
            topic=s.topic,
            messages=[
                ChatHistoryMessage(
                    role=m.role.value,
                    content=m.content,
                    created_at=m.created_at,
                )
                for m in s.messages
            ],
        )
        for s in sessions
    ]


@router.post("/homework", response_model=HomeworkResponse)
async def check_homework(
    data: HomeworkRequest,
    current_user: User = Depends(get_current_user),
):
    """Проверка домашнего задания через AI.

    AI анализирует задачу и ответ ученика, указывает ошибки
    и объясняет правильное решение.
    """
    provider = get_ai_provider()

    prompt = (
        f"Проверь домашнее задание ученика.\n\n"
        f"Предмет: {data.subject}\n"
        f"Задача: {data.task_text}\n"
        f"Ответ ученика: {data.student_answer}\n\n"
        f"Ответь в формате:\n"
        f"1. Правильно или нет (true/false)\n"
        f"2. Оценка от 0 до 100\n"
        f"3. Подробный разбор ошибок\n"
        f"4. Правильное решение с пояснением"
    )

    messages = [{"role": "user", "content": prompt}]
    try:
        response = await provider.chat(messages, subject=data.subject)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ошибка AI-провайдера: {str(e)}")

    # Возвращаем ответ AI как feedback (парсинг формата — упрощённый)
    return HomeworkResponse(
        is_correct="правильно" in response.lower()[:100],
        score=75,
        feedback=response,
        correct_solution="См. разбор выше",
    )


@router.post("/generate-test", response_model=GenerateTestResponse)
async def generate_test(
    data: GenerateTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Генерация теста по теме через AI с few-shot-примерами из банка."""
    provider = get_ai_provider()

    # Подтягиваем 2 похожих реальных задания из банка — few-shot-примеры
    # для AI, чтобы структура и стиль совпадали с ФИПИ-образцами
    examples_query = (
        select(Test)
        .join(Subject, Subject.id == Test.subject_id)
        .where(
            Subject.name == data.subject,
            Test.difficulty == Difficulty(data.difficulty),
        )
        .limit(2)
    )
    examples_res = await db.execute(examples_query)
    example_tests = list(examples_res.scalars().all())

    examples_block = ""
    if example_tests:
        sample_questions = []
        for t in example_tests:
            qs = t.questions if isinstance(t.questions, list) else []
            sample_questions.extend(qs[:1])
        if sample_questions:
            examples_block = (
                "Примеры заданий такого же формата (используй как образец стиля и сложности):\n"
                f"{json.dumps(sample_questions, ensure_ascii=False, indent=2)}\n\n"
            )

    prompt = (
        f"Сгенерируй тест из {data.num_questions} вопросов.\n\n"
        f"Предмет: {data.subject}\n"
        f"Тема: {data.topic}\n"
        f"Сложность: {data.difficulty}\n\n"
        f"{examples_block}"
        f"Формат ответа — JSON массив:\n"
        f'[{{"question": "текст вопроса", "options": ["A", "B", "C", "D"], '
        f'"correct": "A", "type": "multiple_choice"}}]\n\n'
        f"Только JSON, без пояснений."
    )

    messages = [{"role": "user", "content": prompt}]
    try:
        response = await provider.chat(messages, subject=data.subject, topic=data.topic)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ошибка AI-провайдера: {str(e)}")

    # Парсим ответ AI (упрощённо — в MVP)
    try:
        # Пытаемся извлечь JSON из ответа
        start = response.find("[")
        end = response.rfind("]") + 1
        questions_raw = json.loads(response[start:end])
    except (json.JSONDecodeError, ValueError):
        questions_raw = [
            {"question": response, "options": [], "type": "open"}
        ]

    # Сохраняем тест в БД
    test = Test(
        subject_id=1,
        topic=data.topic,
        difficulty=Difficulty(data.difficulty),
        questions=questions_raw,
        created_by_ai=True,
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)

    questions = [
        {"id": i + 1, "question": q.get("question", ""), "options": q.get("options"), "type": q.get("type", "multiple_choice")}
        for i, q in enumerate(questions_raw)
    ]

    return GenerateTestResponse(
        test_id=test.id,
        subject=data.subject,
        topic=data.topic,
        difficulty=data.difficulty,
        questions=questions,
    )


@router.post("/submit-test", response_model=SubmitTestResponse)
async def submit_test(
    data: SubmitTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Сдать тест и получить разбор ошибок от AI."""
    result = await db.execute(select(Test).where(Test.id == data.test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")

    # Проверяем ответы
    questions = test.questions
    correct = 0
    details = []
    for i, q in enumerate(questions):
        q_id = str(i + 1)
        user_answer = data.answers.get(q_id, "")
        is_correct = user_answer.lower() == q.get("correct", "").lower()
        if is_correct:
            correct += 1
        details.append({
            "question": q.get("question", ""),
            "your_answer": user_answer,
            "correct_answer": q.get("correct", ""),
            "is_correct": is_correct,
        })

    total = len(questions)
    percentage = round(correct / total * 100) if total > 0 else 0

    # Сохраняем попытку
    attempt = TestAttempt(
        user_id=current_user.id,
        test_id=test.id,
        answers=data.answers,
        score=percentage,
        time_spent_seconds=data.time_spent_seconds,
        feedback_from_ai=f"Правильных ответов: {correct} из {total}",
    )
    db.add(attempt)
    await db.commit()

    # Обновляем прогресс ученика
    await update_progress_after_test(db, current_user.id, test, percentage)

    return SubmitTestResponse(
        score=correct,
        total=total,
        percentage=percentage,
        feedback=f"Вы ответили правильно на {correct} из {total} вопросов ({percentage}%)",
        details=details,
    )


@router.get("/recommendations")
async def ai_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Персональные рекомендации на основе прогресса и истории."""
    recommendations = await get_recommendations(db, current_user.id)
    return {
        "user_id": current_user.id,
        "recommendations": recommendations,
    }
