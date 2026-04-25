"""Справочник максимальных номеров заданий ФИПИ по предметам и форматам.

Числа взяты из демонстрационных вариантов ФИПИ (актуально на 2024-2025 учебный год).
Для математики ЕГЭ есть две версии — профильная и базовая, поэтому используем
дополнительный параметр math_variant ('profile' | 'base'). Для остальных
предметов math_variant игнорируется.

Для exam_type='regular' (тренировочные тесты) ограничения нет — возвращаем
условный максимум 30, чтобы фронт не показывал бесконечный список.

Использование:
    max_n = get_max_task_number(subject_slug='math', exam_type='ege', math_variant='profile')
"""

from typing import Literal

# Slug должен совпадать с Subject.slug (см. scripts/seed_tutors.py)
TASK_NUMBERS_REGULAR_DEFAULT = 30
TASK_NUMBERS_FALLBACK = 30

# {subject_slug: {exam_type: max_task_number}}
# Источник цифр — демоверсии ФИПИ 2024-2025. Если данных нет — берём fallback.
TASK_NUMBERS: dict[str, dict[str, int]] = {
    "math": {
        # Профильная математика — 19 заданий (1-12 короткий ответ, 13-19 развёрнутый)
        "ege_profile": 19,
        # Базовая математика — 21 задание
        "ege_base": 21,
        # ОГЭ по математике — 25 заданий (1-19 + 20-25 развёрнутые)
        "oge": 25,
    },
    "russian": {
        "ege": 27,
        "oge": 13,
    },
    "physics": {
        "ege": 26,
        "oge": 25,
    },
    "chemistry": {
        "ege": 34,
        "oge": 24,
    },
    "biology": {
        "ege": 28,
        "oge": 29,
    },
    "history": {
        "ege": 21,
        "oge": 24,
    },
    "social": {
        "ege": 25,
        "oge": 24,
    },
    "english": {
        "ege": 38,
        "oge": 36,
    },
    "informatics": {
        "ege": 27,
        "oge": 15,
    },
    "literature": {
        "ege": 12,
        "oge": 5,
    },
    "geography": {
        "ege": 29,
        "oge": 30,
    },
}


MathVariant = Literal["profile", "base"]


def get_max_task_number(
    subject_slug: str,
    exam_type: str,
    math_variant: MathVariant | None = None,
) -> int:
    """Вернуть максимальный номер задания для предмета и формата.

    Для exam_type='ege' и subject_slug='math' нужно явно передать math_variant
    ('profile' или 'base'). Если не передан — берём профильную как наиболее
    распространённую.

    Для exam_type='regular' возвращаем условный максимум, потому что
    тренировочные тесты не привязаны к КИМам ФИПИ.
    """
    if exam_type == "regular":
        return TASK_NUMBERS_REGULAR_DEFAULT

    subject_map = TASK_NUMBERS.get(subject_slug)
    if subject_map is None:
        return TASK_NUMBERS_FALLBACK

    # Математика ЕГЭ — отдельная логика для профиля/базы
    if subject_slug == "math" and exam_type == "ege":
        variant = math_variant or "profile"
        key = f"ege_{variant}"
        return subject_map.get(key, TASK_NUMBERS_FALLBACK)

    return subject_map.get(exam_type, TASK_NUMBERS_FALLBACK)
