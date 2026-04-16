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
- Экран видеозанятия (подготовлен под Agora RTC SDK)
- Сидинг демо-данных — по репетитору на каждый предмет

### Тесты и подготовка к экзаменам
- Банк тестов ОГЭ/ЕГЭ по всем предметам
- Каскадные фильтры: формат экзамена → предмет → номер задания → сложность
- Таймер прохождения
- Разбор ответов с AI-пояснением после сдачи
- AI-генерация похожих заданий

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
- Раздел «Мои занятия» (предстоящие / прошедшие)
- Фильтрация по статусу

---

## Технологический стек

### Backend
| Технология | Назначение |
|-----------|-----------|
| Python 3.11 | Язык |
| FastAPI | REST API фреймворк |
| SQLAlchemy 2.0 (async) | ORM |
| PostgreSQL 16 | Основная БД |
| Redis 7 | Кэш и очереди |
| Alembic | Миграции БД (9 миграций) |
| Pydantic v2 | Валидация данных (ConfigDict) |
| JWT (python-jose) | Аутентификация |
| Google Gemini API | Основной AI-провайдер (через OpenAI SDK) |
| OpenAI / Anthropic API | Альтернативные AI-провайдеры |
| Pytest | Тестирование (43+ тестов) |
| Docker (multi-stage) | Контейнеризация |

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
│   │   └── services/            # Бизнес-логика (AI, auth, tutor, session, video, progress)
│   ├── alembic/                 # Миграции БД (9 миграций)
│   ├── scripts/                 # Сидинг данных (seed_tutors, seed_tests)
│   ├── tests/                   # Pytest тесты (43+)
│   ├── requirements.txt
│   └── Dockerfile               # Multi-stage build
│
├── mobile/
│   ├── app/
│   │   ├── (auth)/              # Вход / Регистрация
│   │   ├── (tabs)/              # Главная, AI-чат, Тесты, Репетиторы, Профиль
│   │   ├── session/[id].tsx     # Экран видеозанятия
│   │   ├── my-sessions.tsx      # Мои занятия
│   │   ├── settings.tsx         # Настройки профиля
│   │   ├── progress.tsx         # Прогресс
│   │   ├── help.tsx             # Помощь / FAQ
│   │   └── onboarding.tsx       # Онбординг
│   ├── components/              # Avatar, Card, Heatmap, PasswordStrengthIndicator
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
POST   /api/v1/auth/register     — Регистрация
POST   /api/v1/auth/login        — Вход (JWT)
POST   /api/v1/auth/refresh      — Обновление токена
POST   /api/v1/auth/logout       — Выход
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
GET    /api/v1/tutors/             — Список (фильтры: предмет, цена, рейтинг)
GET    /api/v1/tutors/{id}         — Профиль репетитора
GET    /api/v1/tutors/{id}/slots   — Свободные слоты на 14 дней
GET    /api/v1/tutors/{id}/reviews — Отзывы
POST   /api/v1/tutors/{id}/review  — Оставить отзыв
```

### Занятия
```
POST   /api/v1/sessions/           — Бронирование
GET    /api/v1/sessions/           — Мои занятия
GET    /api/v1/sessions/{id}       — Детали
PUT    /api/v1/sessions/{id}/cancel — Отмена
```

### Видеозвонки
```
POST   /api/v1/video/token          — Agora RTC токен
POST   /api/v1/video/recording/start — Начать запись
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
docker-compose up -d
docker exec ai_tutor_backend alembic upgrade head  # Миграции (первый раз)
```
- Сервер: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

### 4. Сидинг демо-данных
```bash
docker exec ai_tutor_backend python -m scripts.seed_tutors   # Репетиторы
docker exec ai_tutor_backend python -m scripts.seed_tests    # Тесты ОГЭ/ЕГЭ
```

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
pytest -v                    # Все тесты (43+)
pytest tests/test_auth.py    # Только авторизация
pytest -k "test_login"       # По имени
```

---

## База данных

9 таблиц с полной связностью:

```
users ─────────────── tutor_profiles ──── reviews
  │                        │
  ├── chat_sessions        ├── booking_sessions
  │     └── chat_messages  │
  │                        │
  ├── student_progress     │
  ├── test_attempts ────── tests
  │
  └── subjects ──── topics
```

9 Alembic-миграций: initial tables, reviews, exam type/task number, performance indexes, split full name, drop tokens_used, cleanup AIProvider enum, add user bio.

---

## AI-провайдер

Архитектура с абстрактным провайдером — переключение одной переменной:

```env
AI_PROVIDER=gemini       # Gemini 2.0 Flash (основной, бесплатный)
AI_PROVIDER=openai       # GPT-4o-mini
AI_PROVIDER=anthropic    # Claude Sonnet
```

Все провайдеры реализуют единый интерфейс `BaseAIProvider`. Gemini работает через OpenAI-совместимый endpoint (используется AsyncOpenAI клиент).

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

43+ тестов покрывают ключевые модули:

| Модуль | Тестов | Что покрыто |
|--------|--------|------------|
| auth | 12 | Хеширование, JWT, регистрация, вход, refresh |
| users | 7 | Профиль, обновление, прогресс, статистика |
| tutors | 9 | Список, фильтры, профиль, отзывы, слоты |
| subjects | 6 | Предметы, темы, 404 |
| sessions | 6 | Бронирование, список, отмена, доступ |
| video | 3 | Генерация токенов |

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
- Персональный AI-тьютор (Gemini / GPT / Claude)
- Проверку ДЗ через AI
- Генерацию тестов ОГЭ/ЕГЭ с разбором
- Аналитику прогресса и streak-систему

**AI Tutor** — это всё в одном приложении.

---

## Лицензия

Проект создан в рамках дипломной работы.
