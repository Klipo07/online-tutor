"""Сид банка тестов — примеры заданий ОГЭ/ЕГЭ по предметам.

Запуск:
    docker exec ai_tutor_backend python -m scripts.seed_tests

Идемпотентно — проверка по (subject_id, exam_type, task_number, difficulty, topic).
Задания перефразированы и предназначены для демонстрации архитектуры банка —
не являются копией официальных КИМов ФИПИ.
"""

import asyncio

from sqlalchemy import select

from app.database import async_session
from app.models.subject import Subject
from app.models.test import Difficulty, ExamType, Test


# Структура: список кортежей
# (subject_slug_в_имени, exam_type, task_number, difficulty, topic, [questions])
# Каждый вопрос: {"question", "options" (или None), "correct", "type"}
SEEDS: list[tuple[str, ExamType, int, Difficulty, str, list[dict]]] = [
    # === МАТЕМАТИКА ЕГЭ ===
    ("Математика", ExamType.ege, 1, Difficulty.easy, "Простейшие уравнения", [
        {
            "question": "Решите уравнение 2x + 6 = 14. Введите значение x.",
            "options": ["3", "4", "5", "7"],
            "correct": "4",
            "type": "multiple_choice",
        },
        {
            "question": "Решите уравнение 5x - 3 = 12. Введите x.",
            "options": ["2", "3", "4", "5"],
            "correct": "3",
            "type": "multiple_choice",
        },
    ]),
    ("Математика", ExamType.ege, 4, Difficulty.medium, "Вероятность", [
        {
            "question": "В урне 5 белых и 3 чёрных шара. Какова вероятность вытащить белый?",
            "options": ["3/8", "5/8", "1/2", "2/3"],
            "correct": "5/8",
            "type": "multiple_choice",
        },
        {
            "question": "Подбросили монету 2 раза. Какова вероятность выпадения двух орлов?",
            "options": ["1/2", "1/3", "1/4", "3/4"],
            "correct": "1/4",
            "type": "multiple_choice",
        },
    ]),
    ("Математика", ExamType.ege, 7, Difficulty.hard, "Производная функции", [
        {
            "question": "Найдите производную функции f(x) = x³ + 2x.",
            "options": ["3x² + 2", "3x + 2", "x² + 2", "3x²"],
            "correct": "3x² + 2",
            "type": "multiple_choice",
        },
    ]),
    ("Математика", ExamType.oge, 1, Difficulty.easy, "Арифметика", [
        {
            "question": "Вычислите: 15 · 4 - 20.",
            "options": ["30", "40", "50", "60"],
            "correct": "40",
            "type": "multiple_choice",
        },
        {
            "question": "Сколько будет 7² + 24?",
            "options": ["63", "73", "83", "93"],
            "correct": "73",
            "type": "multiple_choice",
        },
    ]),

    # === РУССКИЙ ЯЗЫК ЕГЭ ===
    ("Русский язык", ExamType.ege, 4, Difficulty.medium, "Орфоэпия — ударения", [
        {
            "question": "В каком слове ударение поставлено верно?",
            "options": ["звОнит", "звонИт", "звонит", "ЗвОнит"],
            "correct": "звонИт",
            "type": "multiple_choice",
        },
        {
            "question": "Выберите слово с правильным ударением.",
            "options": ["тОрты", "тортЫ", "торты", "торТы"],
            "correct": "тОрты",
            "type": "multiple_choice",
        },
    ]),
    ("Русский язык", ExamType.ege, 8, Difficulty.hard, "Синтаксис — грамматические ошибки", [
        {
            "question": "В каком предложении НЕТ грамматической ошибки?",
            "options": [
                "Благодаря дождя урожай вырос.",
                "Благодаря дождю урожай вырос.",
                "Благодаря дождём урожай вырос.",
                "Благодаря дождём урожаи выросли.",
            ],
            "correct": "Благодаря дождю урожай вырос.",
            "type": "multiple_choice",
        },
    ]),
    ("Русский язык", ExamType.oge, 5, Difficulty.easy, "Правописание приставок", [
        {
            "question": "В каком слове пишется приставка ПРИ-?",
            "options": ["пр_открыть (дверь)", "пр_красный", "пр_мудрый", "пр_вышать"],
            "correct": "пр_открыть (дверь)",
            "type": "multiple_choice",
        },
    ]),

    # === ФИЗИКА ЕГЭ ===
    ("Физика", ExamType.ege, 1, Difficulty.easy, "Кинематика", [
        {
            "question": "Автомобиль проехал 60 км за 2 часа. Какова его средняя скорость?",
            "options": ["20 км/ч", "30 км/ч", "60 км/ч", "120 км/ч"],
            "correct": "30 км/ч",
            "type": "multiple_choice",
        },
    ]),
    ("Физика", ExamType.ege, 4, Difficulty.medium, "Второй закон Ньютона", [
        {
            "question": "На тело массой 2 кг действует сила 10 Н. Чему равно ускорение?",
            "options": ["2 м/с²", "5 м/с²", "10 м/с²", "20 м/с²"],
            "correct": "5 м/с²",
            "type": "multiple_choice",
        },
    ]),

    # === ИСТОРИЯ ЕГЭ ===
    ("История", ExamType.ege, 1, Difficulty.easy, "Древняя Русь", [
        {
            "question": "В каком году произошло Крещение Руси?",
            "options": ["862", "988", "1054", "1147"],
            "correct": "988",
            "type": "multiple_choice",
        },
        {
            "question": "Кто считается основателем Древнерусского государства по летописям?",
            "options": ["Олег", "Рюрик", "Игорь", "Владимир"],
            "correct": "Рюрик",
            "type": "multiple_choice",
        },
    ]),
    ("История", ExamType.ege, 10, Difficulty.medium, "Великая Отечественная война", [
        {
            "question": "В каком году началась Великая Отечественная война?",
            "options": ["1939", "1940", "1941", "1942"],
            "correct": "1941",
            "type": "multiple_choice",
        },
        {
            "question": "Сталинградская битва завершилась в…",
            "options": ["1942 году", "феврале 1943 года", "1944 году", "1945 году"],
            "correct": "феврале 1943 года",
            "type": "multiple_choice",
        },
    ]),

    # === ОБЩЕСТВОЗНАНИЕ ===
    ("Обществознание", ExamType.ege, 1, Difficulty.easy, "Основы экономики", [
        {
            "question": "Что относится к факторам производства?",
            "options": ["Прибыль", "Рента", "Труд", "Налог"],
            "correct": "Труд",
            "type": "multiple_choice",
        },
    ]),

    # === АНГЛИЙСКИЙ ===
    ("Английский язык", ExamType.ege, 1, Difficulty.easy, "Времена глаголов", [
        {
            "question": "Выберите правильную форму: 'She ___ to school every day.'",
            "options": ["go", "goes", "going", "gone"],
            "correct": "goes",
            "type": "multiple_choice",
        },
        {
            "question": "'I ___ my homework yesterday.'",
            "options": ["do", "did", "done", "doing"],
            "correct": "did",
            "type": "multiple_choice",
        },
    ]),
    ("Английский язык", ExamType.oge, 1, Difficulty.easy, "Артикли", [
        {
            "question": "Выберите артикль: 'This is ___ apple.'",
            "options": ["a", "an", "the", "—"],
            "correct": "an",
            "type": "multiple_choice",
        },
    ]),

    # === ИНФОРМАТИКА ЕГЭ ===
    ("Информатика", ExamType.ege, 1, Difficulty.easy, "Системы счисления", [
        {
            "question": "Переведите число 10 из десятичной системы в двоичную.",
            "options": ["1010", "1100", "1001", "1111"],
            "correct": "1010",
            "type": "multiple_choice",
        },
    ]),
    ("Информатика", ExamType.ege, 5, Difficulty.medium, "Алгоритмы", [
        {
            "question": "Какая сложность у линейного поиска в неотсортированном массиве?",
            "options": ["O(1)", "O(log n)", "O(n)", "O(n²)"],
            "correct": "O(n)",
            "type": "multiple_choice",
        },
    ]),

    # === ХИМИЯ ===
    ("Химия", ExamType.ege, 1, Difficulty.easy, "Строение атома", [
        {
            "question": "Сколько электронов у атома кислорода (O, №8)?",
            "options": ["6", "7", "8", "16"],
            "correct": "8",
            "type": "multiple_choice",
        },
    ]),

    # === БИОЛОГИЯ ===
    ("Биология", ExamType.ege, 1, Difficulty.easy, "Клеточное строение", [
        {
            "question": "Какой органоид отвечает за синтез белка в клетке?",
            "options": ["Митохондрия", "Рибосома", "Лизосома", "Ядро"],
            "correct": "Рибосома",
            "type": "multiple_choice",
        },
    ]),
]


async def seed():
    async with async_session() as db:
        # Кэш предметов по имени
        subjects_res = await db.execute(select(Subject))
        by_name = {s.name: s for s in subjects_res.scalars().all()}
        if not by_name:
            print("⚠️  Нет предметов в БД. Сначала запустите: python -m scripts.seed_tutors")
            return

        created = 0
        skipped = 0

        for subj_name, exam_type, task_number, difficulty, topic, questions in SEEDS:
            subject = by_name.get(subj_name)
            if not subject:
                print(f"⚠️  Предмет «{subj_name}» не найден — пропуск")
                continue

            # Проверка идемпотентности
            existing_res = await db.execute(
                select(Test).where(
                    Test.subject_id == subject.id,
                    Test.exam_type == exam_type,
                    Test.task_number == task_number,
                    Test.difficulty == difficulty,
                    Test.topic == topic,
                )
            )
            if existing_res.scalar_one_or_none():
                skipped += 1
                continue

            test = Test(
                subject_id=subject.id,
                topic=topic,
                difficulty=difficulty,
                exam_type=exam_type,
                task_number=task_number,
                questions=questions,
                created_by_ai=False,
            )
            db.add(test)
            created += 1

        await db.commit()
        print(f"✅ Создано: {created}, пропущено (уже были): {skipped}")


if __name__ == "__main__":
    asyncio.run(seed())
