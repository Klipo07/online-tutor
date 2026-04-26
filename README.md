# AI Tutor — Онлайн-репетитор с персональным ИИ-тьютором

**Мобильное приложение для подготовки к ЕГЭ/ОГЭ и саморазвития** с встроенным AI-тьютором, маркетплейсом живых репетиторов и системой персонального прогресса.

> Дипломный проект — полноценное коммерческое приложение на React Native + FastAPI.

---

## Реализованные возможности

### Персональный AI-тьютор
- Чат-репетитор по любому школьному предмету (Gemini / GPT-4o / Claude)
- Подстройка AI под выбранный предмет — системный промпт меняется автоматически
- Режим Сократа — наводящие вопросы вместо прямых ответов
- Проверка домашних заданий через AI с разбором ошибок
- Генерация тестов по теме и уровню сложности
- Контекст диалога — AI помнит о чём вы говорили

### Маркетплейс репетиторов
- Каталог репетиторов с фильтрами по предмету, цене, рейтингу
- Профили с рейтингом, отзывами, предметами
- Онлайн-бронирование занятий с выбором слотов на 14 дней вперёд
- Внешняя ссылка на видеозанятие (Zoom / Google Meet / Jitsi) — тьютор присылает `meeting_link`, ученик открывает в браузере (`PUT /sessions/{id}/meeting-link`)
- Сидинг демо-данных — по репетитору на каждый предмет

### Тесты и подготовка к экзаменам
- **Банк из 2271 реального задания** ОГЭ/ЕГЭ по 11 предметам (импорт со sdamgia.ru через `scripts/import_sdamgia.py`)
  - Английский 341, География 231, Биология 208, Информатика 191, Литература 30, Математика 367, Обществознание 148, Русский 185, Физика 237, Химия 208, История 126
  - **478 заданий с PNG-чертежами** (графики, геометрия, физические схемы) — SVG → PNG конвертация через cairosvg при импорте
- Источник заданий — Решу ЕГЭ (`source_url` сохраняется, в UI бейдж «📘 Реальное задание ФИПИ»)
- Каскадные фильтры: формат → предмет → (для математики ЕГЭ — профильная/базовая) → номер задания → сложность → количество вопросов
- Реалистичные max-номера заданий по справочнику ФИПИ — `app/constants/task_numbers.py` (математика-профиль 19, математика-база 21, русский 27, химия 34 и т.д.) через `GET /tests/task-range`
- Таймер прохождения, фидбек по сложности (Легко / В самый раз / Сложно), разбор ответов с AI после сдачи
- **AI-генерация одиночного теста** на лету (`POST /tests/ai-generate`) с few-shot из банка, валидация номера задания против справочника ФИПИ
- **AI-адаптивный подбор** (`POST /tests/recommend`): по последним 10 фидбекам — много `too_easy` → `hard`, много `too_hard` → `easy`, иначе `medium`; fallback на medium/any если пусто
- В manual-режиме mobile сначала пробует банк (реальное задание), AI — только если в банке пусто
- Поддержка двух типов вопросов: `multiple_choice` (выбор) и `input` (ввод числа/строки) — для sdamgia. Толерантное сравнение: trim, lowercase, запятая→точка, числовое сравнение
- **Конвертация LaTeX → unicode** на backend: `$x^2$` → `x²`, `\sqrt{16}` → `√16`, `\frac{1}{2}` → `1/2`, `\pi` → `π`
- **Санитайзер AI-ответа** (`_sanitize_llm_json`): убирает markdown-фенсы и экранирует невалидные JSON-escape (`\sqrt`, `\frac`, `\beta` ломали `json.loads`); дедупликация дублей в `options`

### Прогресс и аналитика
- Персональная статистика (streak, часы обучения, средний балл, пройденные тесты)
- Прогресс-бары по предметам
- Автоматическое определение слабых тем
- AI-рекомендации что повторить
- История прохождения тестов

### Главный экран (Duolingo-стиль)
- Streak дней подряд
- Дневная цель с прогресс-баром
- AI-тренер дня (рекомендация слабой темы)
- Карточка предстоящего занятия с обратным отсчётом
- Быстрый тест-разминка
- Лента активности

### Авторизация и профиль
- JWT авторизация (регистрация, вход, refresh-токены)
- Разделение имени/фамилии
- Валидация пароля с индикатором силы
- Настройки профиля (bio, имя, фамилия, телефон, дата рождения)
- Экран помощи / FAQ / онбординг

### Управление занятиями
- Бронирование с проверкой свободных слотов
- Раздел «Мои занятия» — для ученика «с {tutor_name}», для тьютора «Ученик: {student_name}» (ветвление по роли, `SessionResponse` содержит оба имени)
- Фильтрация по статусу (предстоящие / прошедшие / отменённые)
- Отмена бронирования с правилом 24 часов (>24ч — без причины, <24ч — обязательная причина ≥5 символов)
- SELECT FOR UPDATE для защиты от гонок при отмене (PostgreSQL)
- После отмены слот снова доступен для новой записи

### Регистрация как репетитор
- Единый эндпоинт `/auth/register` с discriminated union (Pydantic v2)
- Для роли `tutor` — атомарное создание `User + TutorProfile` в одной транзакции
- Выбор предметов, цены за час, опыта, образования, bio
- По умолчанию `is_verified=true` (временно, до боевого SMTP) — репетитор сразу появляется в маркетплейсе
- Маркетплейс авто-рефрешится при возврате на таб (`useFocusEffect`), новые репетиторы видны без перезапуска

### Ролевой интерфейс репетитора
- Отдельный набор табов по роли: `chat`/`tests`/`tutors` скрыты у тьютора, вместо них — «Мои занятия» (`t-sessions`) и «Расписание» (`t-schedule`)
- Дашборд репетитора на главной — приветствие, карточка ближайшего занятия с обратным отсчётом, доход за месяц, рейтинг, мини-статистика (ученики / проведено / предстоящие), быстрые действия
- Экран «Мои занятия» тьютора — три фильтра (Предстоящие / Сегодня / История), статус-пилюли, клик по карточке → экран занятия
- Экран «Расписание» — per-day рабочие часы с toggle Рабочий/Выходной, ± степпер начала/конца (хранится в `TutorProfile.working_hours` JSONB, дефолт `пн-пт 9-21, сб 10-18, вс — выходной`)
- Экран «Предметы и цена» (`tutor-profile-edit`) — мультивыбор предметов из каталога, цена/опыт/образование, PATCH `/tutors/me/profile`
- Экран «Отзывы обо мне» (`tutor-reviews`) — лента через `/tutors/me/reviews`
- Меню профиля ветвится по роли: тьютор видит «Предметы и цена» + «Отзывы обо мне», ученик — «Мой прогресс»
- Свободные слоты (`GET /tutors/{id}/slots`) считаются **по `working_hours` репетитора**, а не по жёстко зашитым 9-18

### Верификация email
- После регистрации — письмо с ссылкой (Yandex SMTP, TTL 24ч)
- Токен хэшируется SHA-256 в БД, raw только в письме (при утечке БД не активируется)
- Отправка через FastAPI `BackgroundTasks` + `asyncio.to_thread` — event loop не блокируется
- Deep link `ai-tutor://verify?token=…` открывает mobile-экран и дергает `GET /auth/verify-email`
- Cooldown 60 секунд на повторную отправку, сервер отвечает 429 + `Retry-After`
- При подтверждении у репетитора автоматически `TutorProfile.is_verified=true` — попадает в маркетплейс
- Баннер «Email не подтверждён» на главной + экран `check-email` с таймером resend
- Rate-limit cooldown хранится в Redis (`INCR` + `EXPIRE`) — переживает рестарт backend'а, не сбрасывается при перезапуске контейнера

### Redis-кэширование
- `services/cache.py` — тонкая обёртка над `redis.asyncio`: `get/set/delete/delete_pattern/incr_with_ttl`, graceful fallback (если Redis недоступен — сервер работает напрямую с БД)
- Кэшируются: `GET /tutors/` (TTL 90с, инвалидация при PATCH профиля / новом отзыве), `GET /subjects/` и `/subjects/{id}/topics` (TTL 1ч), `GET /tests/task-numbers` и `/tests/subjects-with-tests` (TTL 10 мин)
- Инвалидация целых групп через `delete_pattern("tutors:list:*")` (Redis SCAN)
- Версионированный префикс `ai_tutor:v1:` — чтобы при ломающих изменениях формата обойтись без `FLUSHDB`

---

## Технологический стек

### Backend
| Технология | Назначение |
|-----------|-----------|
| Python 3.11 | Язык |
| FastAPI | REST API фреймворк |
| SQLAlchemy 2.0 (async) | ORM |
| PostgreSQL 16 | Основная БД |
| Redis 7 | Кэш маркетплейса / справочников + rate-limit cooldown верификации email |
| Alembic | Миграции БД (15 миграций) |
| Pydantic v2 | Валидация данных (ConfigDict, discriminated unions) |
| JWT (python-jose) | Аутентификация |
| YandexGPT | Основной AI-провайдер (`yandexgpt-lite/latest` через httpx) |
| Anthropic Claude | Опциональный fallback (lazy-import — пакет нужен только при `AI_PROVIDER=anthropic`) |
| cairosvg + libcairo2 | SVG → PNG конвертация при импорте sdamgia |
| beautifulsoup4 | HTML-парсер для импорта банка заданий |
| Pytest | Тестирование (99/99 зелёные — AI-подбор, LaTeX, кэш-инвалидация, бронирование) |
| Docker (multi-stage, ~425 MB) | Контейнеризация |

### Mobile
| Технология | Назначение |
|-----------|-----------|
| React Native | Фреймворк |
| Expo (SDK 51+) | Сборка и деплой |
| TypeScript | Язык |
| Expo Router | Файловая навигация |
| Zustand | Стейт-менеджмент |
| Axios | HTTP-клиент |
| React.memo / useCallback | Оптимизация рендеров |
| expo-image | Кэшированные картинки (Avatar, чертежи заданий) с плавным `transition` |

---

## Структура проекта

```
online-tutor/
├── backend/
│   ├── app/
│   │   ├── main.py              # Точка входа FastAPI
│   │   ├── config.py            # Настройки из .env (Pydantic Settings)
│   │   ├── database.py          # Async SQLAlchemy
│   │   ├── dependencies.py      # JWT авторизация
│   │   ├── models/              # SQLAlchemy модели (9 таблиц)
│   │   ├── schemas/             # Pydantic v2 схемы
│   │   ├── routers/             # API эндпоинты (7 роутеров)
│   │   ├── services/            # Бизнес-логика (AI, auth, tutor, session, progress, cache, math_format, email)
│   │   └── constants/           # Справочники (task_numbers по предметам/форматам ФИПИ)
│   ├── alembic/                 # Миграции БД (17 миграций)
│   ├── scripts/                 # Сидинг (seed_tutors, seed_tests) + импорт sdamgia (import_sdamgia.py)
│   ├── tests/                   # Pytest тесты (99 зелёных)
│   ├── requirements.txt
│   └── Dockerfile               # Multi-stage build
│
├── mobile/
│   ├── app/
│   │   ├── (auth)/              # Вход / Регистрация (student или tutor, discriminated union)
│   │   ├── (tabs)/              # Главная, AI-чат, Тесты, Репетиторы, Профиль (ученик)
│   │   │                        # + t-sessions, t-schedule (тьютор — ролевое ветвление)
│   │   ├── session/[id].tsx     # Экран занятия — meeting_link на Zoom/Meet/Jitsi
│   │   ├── my-sessions.tsx      # Мои занятия + отмена (ученик)
│   │   ├── tutor-profile-edit.tsx # Предметы и цена (тьютор)
│   │   ├── tutor-reviews.tsx    # Отзывы обо мне (тьютор)
│   │   ├── settings.tsx         # Настройки профиля
│   │   ├── progress.tsx         # Прогресс (ученик)
│   │   ├── help.tsx             # Помощь / FAQ
│   │   ├── onboarding.tsx       # Онбординг
│   │   ├── check-email.tsx      # Экран после регистрации (resend + cooldown)
│   │   └── verify.tsx           # Deep link обработчик ai-tutor://verify
│   ├── components/              # Avatar, Card, Heatmap, CancelBookingModal, PasswordStrengthIndicator, EmailVerifyBanner, TutorDashboard
│   ├── services/api.ts          # HTTP клиент
│   ├── store/authStore.ts       # Zustand стор
│   └── constants/theme.ts       # Тема и цвета
│
├── docker-compose.yml
├── CLAUDE.md                    # Контекст для AI-разработки (только TODO)
└── README.md                    # Этот файл
```

---

## API эндпоинты

### Авторизация
```
POST   /api/v1/auth/register            — Регистрация (student/parent ИЛИ tutor — discriminated union)
POST   /api/v1/auth/login               — Вход (JWT)
POST   /api/v1/auth/refresh             — Обновление токена
POST   /api/v1/auth/logout              — Выход
POST   /api/v1/auth/send-verification   — Отправить/переотправить письмо (cooldown 60с)
GET    /api/v1/auth/verify-email?token= — Подтверждение email по токену из письма
```

### Пользователи
```
GET    /api/v1/users/me           — Профиль
PUT    /api/v1/users/me           — Обновление профиля
GET    /api/v1/users/me/progress  — Прогресс по предметам
GET    /api/v1/users/me/stats     — Общая статистика (streak, часы, средний балл)
GET    /api/v1/users/me/test-history — История тестов
```

### AI-тьютор
```
POST   /api/v1/ai/chat            — Сообщение AI (с учётом выбранного предмета)
GET    /api/v1/ai/chat/history    — История чатов
POST   /api/v1/ai/homework        — Проверка ДЗ
POST   /api/v1/ai/generate-test   — Генерация теста
POST   /api/v1/ai/submit-test     — Сдать тест с разбором
GET    /api/v1/ai/recommendations  — Персональные рекомендации
```

### Репетиторы
```
GET    /api/v1/tutors/             — Список (фильтры: предмет JSONB @>, цена, рейтинг; только verified)
GET    /api/v1/tutors/{id}         — Профиль репетитора
GET    /api/v1/tutors/{id}/slots   — Свободные слоты на 14 дней (по working_hours)
GET    /api/v1/tutors/{id}/reviews — Отзывы
POST   /api/v1/tutors/{id}/review  — Оставить отзыв
GET    /api/v1/tutors/me/schedule  — Моё расписание (рабочие часы по дням)
PUT    /api/v1/tutors/me/schedule  — Обновить расписание
PATCH  /api/v1/tutors/me/profile   — Обновить мой профиль (предметы, цена, опыт, образование)
GET    /api/v1/tutors/me/stats     — Статистика для дашборда (ученики, доход, рейтинг, ближайшее занятие)
GET    /api/v1/tutors/me/reviews   — Отзывы обо мне
```

### Занятия
```
POST   /api/v1/sessions/                  — Бронирование
GET    /api/v1/sessions/                  — Мои занятия
GET    /api/v1/sessions/{id}              — Детали
PUT    /api/v1/sessions/{id}/cancel       — Отмена (правило 24 часов, 409 если уже началось)
PUT    /api/v1/sessions/{id}/meeting-link — Тьютор сохраняет ссылку на Zoom/Meet/Jitsi
```

### Банк тестов
```
GET    /api/v1/tests                      — Список тестов (фильтры: subject_id, exam_type, task_number, difficulty)
POST   /api/v1/tests/recommend            — AI-адаптивный подбор: сложность по фидбекам + рандомная выборка
POST   /api/v1/tests/ai-generate          — Сгенерировать одиночный тест AI (по предмету/номеру/сложности/количеству вопросов)
GET    /api/v1/tests/task-range           — Max-номер задания по справочнику ФИПИ (для math-ege — math_variant=profile|base)
GET    /api/v1/tests/subjects-with-tests  — Предметы с количеством тестов (кэш 10 мин, поле slug в payload)
GET    /api/v1/tests/task-numbers         — Доступные номера заданий для предмета + формата (кэш 10 мин)
GET    /api/v1/tests/{id}                 — Тест с вопросами (без ответов, image_urls, source_url, from_bank, LaTeX → unicode)
POST   /api/v1/tests/{id}/feedback        — Фидбек по сложности (too_easy / ok / too_hard) — вход для `/recommend`
```

### Предметы
```
GET    /api/v1/subjects/            — Все предметы
GET    /api/v1/subjects/{id}        — Предмет с темами
GET    /api/v1/subjects/{id}/topics — Темы
```

---

## Быстрый старт

### 1. Клонирование
```bash
git clone https://github.com/Klipo07/online-tutor.git
cd online-tutor
```

### 2. Настройка окружения
```bash
cp .env.example .env
# Отредактируйте .env — укажите API-ключи AI-провайдера
```

### 3. Запуск через Docker
```bash
docker-compose up -d            # поднимет db + redis + backend
docker exec ai_tutor_backend alembic upgrade head  # Миграции (первый раз и после pull)
```
- Сервер: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Redis: `localhost:6379` (опционально — для кэша; если недоступен, backend работает без кэша)

### 4. Сидинг демо-данных
```bash
docker exec ai_tutor_backend python -m scripts.seed_tutors   # Репетиторы (по 1 на предмет)
docker exec ai_tutor_backend python -m scripts.seed_tests    # Базовые тесты (мини-набор)
```

### 4a. Импорт реальных заданий с Решу ЕГЭ (sdamgia.ru)
```bash
# Один предмет, один номер задания (5 заданий)
docker exec ai_tutor_backend python -m scripts.import_sdamgia \
    --subject math-ege --task 8 --limit 5

# Все номера одного предмета (по 5 на каждый номер)
docker exec ai_tutor_backend python -m scripts.import_sdamgia \
    --subject phys-ege --all-tasks --limit 5

# Все предметы из SUBJECT_MAP (полный охват)
docker exec ai_tutor_backend python -m scripts.import_sdamgia \
    --all-subjects --limit 5
```
Картинки (графики, чертежи) скачиваются в `uploads/sdamgia/<external_id>/` и
конвертируются из SVG в PNG через `cairosvg`. Идемпотентно по `external_id`.

### 5. Запуск без Docker

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

**Mobile:**
```bash
cd mobile
npm install
npx expo start
```

### 6. Перезапуск backend
```bash
docker-compose restart backend                 # Изменён код Python
docker-compose up -d --force-recreate backend  # Изменён .env
docker-compose up -d --build backend           # Изменён requirements.txt
```

### 7. Тесты
```bash
cd backend
pytest -v                    # Все тесты (99 — все зелёные)
pytest tests/test_auth.py    # Только авторизация
pytest tests/test_tests.py   # AI-подбор + LaTeX
pytest -k "test_login"       # По имени
```

---

## База данных

10 таблиц с полной связностью:

```
users ─────────────── tutor_profiles ──── reviews
  │                        │
  ├── chat_sessions        ├── booking_sessions (+ cancellation fields)
  │     └── chat_messages  │
  │                        │
  ├── student_progress     │
  ├── test_attempts ────── tests ──── test_feedbacks
  │
  └── subjects ──── topics
```

17 Alembic-миграций: initial tables, reviews, exam type/task number, performance indexes, split full name, drop tokens_used, cleanup AIProvider enum, add user bio, drop tutor_profile bio, tutor subjects GIN index (JSONB), booking cancellation fields, test feedback table, email verification fields, tutor working_hours JSONB, backfill is_verified=true, **add meeting_link** (отказ от Agora), **add test source_url/external_id/image_paths** (импорт sdamgia), **drop agora_channel_name** (cleanup).

---

## AI-провайдер

Архитектура с абстрактным провайдером — переключение одной переменной:

```env
AI_PROVIDER=yandex       # YandexGPT Lite (основной, через httpx)
AI_PROVIDER=anthropic    # Claude Sonnet 4.5 (опционально — нужен `pip install anthropic`)
```

Все провайдеры реализуют единый интерфейс `BaseAIProvider`. Anthropic SDK
импортируется лениво (только при выборе провайдера) — не входит в
`requirements.txt` по умолчанию, чтобы не раздувать образ.

AI автоматически подстраивается под выбранный предмет — системный промпт генерируется динамически.

---

## Предметы (v1.0)

- Математика (база + профиль)
- Русский язык
- Физика, Химия, Биология
- История, Обществознание
- Английский язык
- Информатика
- География, Литература

---

## Тестирование

99 тестов покрывают ключевые модули — **все зелёные** (Redis-кэш сбрасывается между тестами в `conftest.py`):

| Модуль | Тестов | Что покрыто |
|--------|--------|------------|
| auth | 31 | Хеширование, JWT, регистрация student/tutor (discriminated union), вход, refresh, верификация email (token, expiry, auto-promote tutor, cooldown 429) |
| sessions | 10 | Бронирование, список, отмена (24ч-правило, double-cancel, release slot), доступ |
| tutors | 11 | Список, фильтры по предмету (JSONB), профиль, отзывы, слоты |
| users | 7 | Профиль, обновление, прогресс, статистика |
| subjects | 6 | Предметы, темы, 404 |
| math_format | 20 | LaTeX → unicode: степени, корни, дроби, греческие, операторы, format_questions |
| tests (recommend) | 9 | Адаптивный подбор: no-feedback → medium, too_easy → hard, too_hard → easy, fallback, изоляция по предметам, LaTeX в `/tests/{id}` |
| cache_invalidation | 5 | PATCH профиля / schedule / review сбрасывают кэш маркетплейса |

---

## Целевая аудитория

| Сегмент | Возраст | Задачи |
|---------|---------|--------|
| Школьники | 13-17 | ЕГЭ/ОГЭ, подтягивание предметов |
| Студенты | 18-22 | Сессия, углубление знаний |
| Взрослые | 22-35 | Саморазвитие |
| Родители | 30-45 | Контроль прогресса ребёнка |

---

## Конкурентное преимущество

Ни один из существующих сервисов (Profi.ru, Skyeng, Умскул) не объединяет:
- Маркетплейс живых репетиторов
- Персональный AI-тьютор (YandexGPT / Claude)
- Проверку ДЗ через AI
- **Реальный банк заданий ФИПИ (2271 задание из Решу ЕГЭ) + AI-генерация по запросу**
- Аналитику прогресса и streak-систему

**AI Tutor** — это всё в одном приложении.

---

## Лицензия

Проект создан в рамках дипломной работы.
