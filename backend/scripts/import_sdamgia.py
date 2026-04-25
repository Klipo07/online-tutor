"""Импорт банка заданий с Решу ЕГЭ (sdamgia.ru) в локальную БД.

Парсит каталог заданий по номеру (`pcat_num`), скачивает текст + не-формульные
картинки (графики/чертежи), сохраняет в `tests` с `created_by_ai=False`.
Формулы (`<img class="tex">`) оставляем как естественно-языковой `alt`-текст —
SVG не качаем, чтобы не плодить мелкие файлы.

Идемпотентно: повторный запуск не плодит дубли (проверка по `external_id`).

Запуск (внутри контейнера):
    docker exec ai_tutor_backend python -m scripts.import_sdamgia \\
        --subject math-ege --task 8 --limit 10

Поддерживаемые subject (subdomain sdamgia.ru):
    math-ege   — профильная математика ЕГЭ
    mathb-ege  — базовая математика ЕГЭ
    math-oge   — ОГЭ математика
    rus-ege    — русский язык ЕГЭ
    phys-ege   — физика ЕГЭ
    chem-ege   — химия ЕГЭ
    bio-ege    — биология ЕГЭ
    hist-ege   — история ЕГЭ
    soc-ege    — обществознание ЕГЭ
"""

import argparse
import asyncio
import logging
import re
from pathlib import Path
from typing import NamedTuple

import httpx
from bs4 import BeautifulSoup, Tag
from sqlalchemy import select

# Конвертация SVG → PNG для отображения в Expo Go (RN <Image> не умеет SVG)
try:
    import cairosvg

    _SVG_TO_PNG_AVAILABLE = True
except ImportError:
    _SVG_TO_PNG_AVAILABLE = False

from app.database import async_session
from app.models.subject import Subject
from app.models.test import Difficulty, ExamType, Test


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("import_sdamgia")


# Маппинг subdomain → (slug нашего предмета, exam_type)
SUBJECT_MAP: dict[str, tuple[str, ExamType]] = {
    "math-ege":  ("math",        ExamType.ege),
    "mathb-ege": ("math",        ExamType.ege),  # базовая
    "math-oge":  ("math",        ExamType.oge),
    "rus-ege":   ("russian",     ExamType.ege),
    "rus-oge":   ("russian",     ExamType.oge),
    "phys-ege":  ("physics",     ExamType.ege),
    "phys-oge":  ("physics",     ExamType.oge),
    "chem-ege":  ("chemistry",   ExamType.ege),
    "chem-oge":  ("chemistry",   ExamType.oge),
    "bio-ege":   ("biology",     ExamType.ege),
    "bio-oge":   ("biology",     ExamType.oge),
    "hist-ege":  ("history",     ExamType.ege),
    "hist-oge":  ("history",     ExamType.oge),
    "soc-ege":   ("social",      ExamType.ege),
    "soc-oge":   ("social",      ExamType.oge),
    "en-ege":    ("english",     ExamType.ege),
    "en-oge":    ("english",     ExamType.oge),
    "inf-ege":   ("informatics", ExamType.ege),
    "inf-oge":   ("informatics", ExamType.oge),
    "geo-ege":   ("geography",   ExamType.ege),
    "geo-oge":   ("geography",   ExamType.oge),
    "lit-ege":   ("literature",  ExamType.ege),
    "lit-oge":   ("literature",  ExamType.oge),
}

UPLOADS_DIR = Path("/app/uploads/sdamgia")
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


class ParsedTask(NamedTuple):
    external_id: str            # внутренний id sdamgia ("119976")
    task_type: int              # номер задания ЕГЭ ("Тип 8 № 119976" → 8)
    text: str                   # текст вопроса (без HTML, формулы заменены на alt-текст)
    answer: str                 # правильный ответ
    image_urls: list[str]       # абсолютные URL не-формульных картинок (графики)
    source_url: str


def _http_client(base: str) -> httpx.Client:
    return httpx.Client(
        base_url=base,
        headers={"User-Agent": USER_AGENT},
        timeout=30.0,
        follow_redirects=True,
    )


def _find_categories_for_task(catalog_html: str, task_num: int) -> list[int]:
    """Из HTML каталога вытаскиваем все category_id, относящиеся к номеру задания."""
    soup = BeautifulSoup(catalog_html, "html.parser")
    result: list[int] = []
    for span in soup.select("span.pcat_num"):
        try:
            num = int(span.get_text(strip=True))
        except ValueError:
            continue
        if num != task_num:
            continue
        # Ищем родительский cat_category, потом внутри него cat_children и data-id
        parent = span.find_parent(class_="cat_category")
        if parent is None:
            continue
        for child in parent.select(".cat_children .cat_category[data-id]"):
            try:
                result.append(int(child["data-id"]))
            except (ValueError, KeyError):
                continue
    return result


def _list_all_task_numbers(catalog_html: str) -> list[int]:
    """Все номера заданий, представленные в каталоге (`pcat_num`)."""
    soup = BeautifulSoup(catalog_html, "html.parser")
    nums: set[int] = set()
    for span in soup.select("span.pcat_num"):
        try:
            nums.add(int(span.get_text(strip=True)))
        except ValueError:
            continue
    return sorted(nums)


def _normalize_text(node: Tag) -> tuple[str, list[str]]:
    """Превращаем содержимое <div class="pbody"> в чистый текст.

    - <img class="tex"> → её `alt`-текст (формула в естественной форме).
    - <img src="/get_file?id=N"> → маркер `[рисунок N]`, URL отдельно в image_urls.
    - Остальные теги — игнорируются, остаётся внутренний текст.
    """
    image_urls: list[str] = []

    # Идём по всем <img>, мутируем дерево перед извлечением текста
    for img in node.find_all("img"):
        src = img.get("src", "")
        cls = img.get("class") or []
        # Формулы — у них alt с человекочитаемым текстом
        if "tex" in cls or "/formula/" in src:
            alt = img.get("alt", "").strip()
            img.replace_with(f" {alt} " if alt else "")
            continue
        # Не-формульные картинки (графики, чертежи)
        if src.startswith("/get_file") or "sdamgia.ru" in src:
            image_urls.append(src)
            img.replace_with(f"[рисунок {len(image_urls)}]")
            continue
        # Прочие — пропускаем
        img.decompose()

    # `get_text(' ')` склеивает с пробелом, чтобы не слипались слова
    text = node.get_text(" ", strip=True)
    # Нормализация мягких переносов и множественных пробелов
    text = text.replace("­", "").replace(" ", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text, image_urls


def _parse_task_block(maindiv: Tag, base_url: str) -> ParsedTask | None:
    """Распарсить один <div class="prob_maindiv">. None если что-то не то."""
    nums_span = maindiv.select_one(".prob_nums")
    if nums_span is None:
        return None
    nums_text = nums_span.get_text(" ", strip=True)
    # "Тип 8 № 119976"
    m = re.search(r"Тип\s+(\d+)\s*№\s*(\d+)", nums_text)
    if not m:
        return None
    task_type = int(m.group(1))
    external_id = m.group(2)

    body = maindiv.select_one(".pbody")
    if body is None:
        return None
    text, image_urls = _normalize_text(body)

    # Делаем картинки абсолютными
    abs_urls = []
    for u in image_urls:
        if u.startswith("/"):
            abs_urls.append(base_url.rstrip("/") + u)
        else:
            abs_urls.append(u)

    answer_div = maindiv.select_one(".answer")
    if answer_div is None:
        return None
    answer_raw = answer_div.get_text(" ", strip=True)
    # "Ответ: 20"
    answer = re.sub(r"^Ответ\s*:\s*", "", answer_raw).strip()
    if not answer:
        return None

    return ParsedTask(
        external_id=external_id,
        task_type=task_type,
        text=text,
        answer=answer,
        image_urls=abs_urls,
        source_url=f"{base_url.rstrip('/')}/problem?id={external_id}",
    )


def _download_images(
    client: httpx.Client, urls: list[str], external_id: str
) -> list[str]:
    """Скачивает картинки в uploads/sdamgia/<external_id>/. Возвращает относительные пути."""
    if not urls:
        return []
    target_dir = UPLOADS_DIR / external_id
    target_dir.mkdir(parents=True, exist_ok=True)

    rel_paths: list[str] = []
    for i, url in enumerate(urls, 1):
        try:
            r = client.get(url)
            r.raise_for_status()
            ctype = r.headers.get("content-type", "").split(";")[0].strip()

            # SVG → PNG конвертация (Expo Go RN <Image> не рендерит SVG)
            if ctype == "image/svg+xml" and _SVG_TO_PNG_AVAILABLE:
                png_path = target_dir / f"{i}.png"
                try:
                    cairosvg.svg2png(
                        bytestring=r.content,
                        write_to=str(png_path),
                        output_width=600,  # фикс ширины для нормального DPI на телефоне
                    )
                    rel_paths.append(f"sdamgia/{external_id}/{i}.png")
                    continue
                except Exception as e:
                    log.warning("SVG → PNG для %s упал: %s; сохраняю SVG", url, e)
                    svg_path = target_dir / f"{i}.svg"
                    svg_path.write_bytes(r.content)
                    rel_paths.append(f"sdamgia/{external_id}/{i}.svg")
                    continue

            ext = {
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "image/gif": ".gif",
                "image/svg+xml": ".svg",
                "image/webp": ".webp",
            }.get(ctype, ".png")
            fname = f"{i}{ext}"
            (target_dir / fname).write_bytes(r.content)
            rel_paths.append(f"sdamgia/{external_id}/{fname}")
        except Exception as e:
            log.warning("Не удалось скачать %s: %s", url, e)
    return rel_paths


async def _import_one(
    client: httpx.Client,
    db,
    subject: Subject,
    exam_type: ExamType,
    task_num: int,
    parsed: ParsedTask,
    diff: Difficulty,
) -> bool:
    """Сохранить одну задачу. True если создали, False если уже была."""
    existing = await db.execute(
        select(Test.id).where(Test.external_id == parsed.external_id)
    )
    if existing.scalar_one_or_none() is not None:
        return False

    rel_paths = _download_images(client, parsed.image_urls, parsed.external_id)

    test = Test(
        subject_id=subject.id,
        topic=f"Решу ЕГЭ № {parsed.external_id}",
        exam_type=exam_type,
        task_number=task_num,
        difficulty=diff,
        questions=[{
            "question": parsed.text,
            "options": None,
            "correct": parsed.answer,
            "type": "input",
        }],
        created_by_ai=False,
        source_url=parsed.source_url,
        external_id=parsed.external_id,
        image_paths=rel_paths if rel_paths else None,
    )
    db.add(test)
    await db.commit()
    return True


async def _import_for_task(
    client: httpx.Client, db, subject: Subject, exam_type: ExamType,
    base_url: str, task_num: int, limit: int, diff: Difficulty,
) -> tuple[int, int]:
    """Импорт limit задач для одного task_num. Возвращает (создано, пропущено)."""
    catalog_resp = client.get("/prob_catalog")
    catalog_resp.raise_for_status()
    cat_ids = _find_categories_for_task(catalog_resp.text, task_num)
    if not cat_ids:
        log.warning("В каталоге %s нет категорий для задания %d", base_url, task_num)
        return 0, 0
    log.info("Задание №%d → категории: %s", task_num, cat_ids)

    created = 0
    skipped = 0
    for cat_id in cat_ids:
        if created >= limit:
            break
        try:
            resp = client.get(
                "/test", params={"filter": "all", "category_id": cat_id}
            )
            resp.raise_for_status()
        except Exception as e:
            log.warning("  cat %d: ошибка запроса: %s", cat_id, e)
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        tasks = soup.select("div.prob_maindiv")
        for maindiv in tasks:
            if created >= limit:
                break
            parsed = _parse_task_block(maindiv, base_url)
            if parsed is None or parsed.task_type != task_num:
                continue
            try:
                is_new = await _import_one(
                    client, db, subject, exam_type, task_num, parsed, diff
                )
            except Exception as e:
                log.warning("  ext=%s: ошибка сохранения: %s", parsed.external_id, e)
                continue
            if is_new:
                created += 1
            else:
                skipped += 1
    return created, skipped


async def main(
    subdomain: str,
    task_num: int | None,
    limit: int,
    difficulty: str,
    all_tasks: bool,
) -> None:
    if subdomain not in SUBJECT_MAP:
        raise SystemExit(
            f"Неизвестный subject '{subdomain}'. Доступные: {sorted(SUBJECT_MAP)}"
        )
    subject_slug, exam_type = SUBJECT_MAP[subdomain]
    diff = Difficulty(difficulty)
    base_url = f"https://{subdomain}.sdamgia.ru"

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    async with async_session() as db:
        subject = (
            await db.execute(select(Subject).where(Subject.slug == subject_slug))
        ).scalar_one_or_none()
        if subject is None:
            raise SystemExit(
                f"Предмет '{subject_slug}' не найден в БД — запусти scripts/seed_tutors.py"
            )

        with _http_client(base_url) as client:
            log.info("Тяну каталог: %s/prob_catalog", base_url)

            if all_tasks:
                catalog_resp = client.get("/prob_catalog")
                catalog_resp.raise_for_status()
                task_nums = _list_all_task_numbers(catalog_resp.text)
                log.info("Все номера заданий в каталоге: %s", task_nums)
                total_created = 0
                total_skipped = 0
                for n in task_nums:
                    log.info("=== %s task=%d ===", subdomain, n)
                    c, s = await _import_for_task(
                        client, db, subject, exam_type, base_url, n, limit, diff
                    )
                    total_created += c
                    total_skipped += s
                log.info(
                    "[%s] ВСЕГО: создано %d, пропущено %d",
                    subdomain, total_created, total_skipped,
                )
            else:
                if task_num is None:
                    raise SystemExit("Нужен --task N или --all-tasks")
                created, skipped = await _import_for_task(
                    client, db, subject, exam_type, base_url, task_num, limit, diff
                )
                log.info("Готово: создано %d, пропущено (дубли) %d", created, skipped)


async def main_all_subjects(limit: int, difficulty: str) -> None:
    """Импорт всех subdomain'ов из SUBJECT_MAP, --all-tasks для каждого."""
    for sub in SUBJECT_MAP:
        log.info("======== %s ========", sub)
        try:
            await main(sub, None, limit, difficulty, all_tasks=True)
        except Exception as e:
            log.exception("Ошибка для %s: %s", sub, e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Импорт заданий с Решу ЕГЭ")
    parser.add_argument(
        "--subject", default=None,
        help="subdomain sdamgia (math-ege, math-oge, rus-ege и т.п.) или --all-subjects",
    )
    parser.add_argument(
        "--all-subjects", action="store_true",
        help="импорт по всем известным subdomain'ам (override --subject)",
    )
    parser.add_argument(
        "--task", type=int, default=None,
        help="конкретный номер задания (или используйте --all-tasks)",
    )
    parser.add_argument(
        "--all-tasks", action="store_true",
        help="импорт всех номеров заданий из каталога",
    )
    parser.add_argument(
        "--limit", type=int, default=10,
        help="макс. новых задач на каждый номер",
    )
    parser.add_argument(
        "--difficulty", default="medium", choices=["easy", "medium", "hard"],
        help="сложность по умолчанию",
    )
    args = parser.parse_args()
    if args.all_subjects:
        asyncio.run(main_all_subjects(args.limit, args.difficulty))
    else:
        if not args.subject:
            raise SystemExit("Нужен --subject SLUG или --all-subjects")
        asyncio.run(main(args.subject, args.task, args.limit, args.difficulty, args.all_tasks))
