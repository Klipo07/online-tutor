# AI Tutor — Онлайн-репетитор с персональным ИИ-тьютором

**Мобильное приложение для подготовки к ЕГЭ/ОГЭ и саморазвития** с встроенным AI-тьютором, маркетплейсом живых репетиторов и системой персонального прогресса.

> Дипломный проект — полноценное коммерческое приложение на React Native + FastAPI.

---

## Возможности

### Персональный AI-тьютор
- Чат-репетитор по любому школьному предмету (GPT-4o / Claude)
- Режим Сократа — наводящие вопросы вместо прямых ответов
- Проверка домашних заданий через AI с разбором ошибок
- Генерация тестов по теме и уровню сложности
- Контекст диалога — AI помнит о чём вы говорили

### Маркетплейс репетиторов
- Каталог верифицированных репетиторов с фильтрами
- Профили с рейтингом, отзывами, предметами
- Онлайн-бронирование занятий
- Видеозвонки через Agora RTC SDK

### Прогресс и аналитика
- Персональная статистика по всем предметам
- Визуализация прогресса с прогресс-барами
- Автоматическое определение слабых тем
- AI-рекомендации что повторить
- История прохождения тестов

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
| Alembic | Миграции БД |
| Pydantic v2 | Валидация данных |
| JWT (python-jose) | Аутентификация |
| OpenAI / Anthropic API | AI-провайдеры |
| Pytest | Тестирование |
| Docker | Контейнеризация |

### Mobile
| Технология | Назначение |
|-----------|-----------|
| React Native | Фреймворк |
| Expo (SDK 51+) | Сборка и деплой |
| TypeScript | Язык |
| Expo Router | Навигация |
| Zustand | Стейт-менеджмент |
| Axios | HTTP-клиент |
| Agora RTC SDK | Видеозвонки |

---

## Структура проекта

```
online-tutor/
├── backend/
│   ├── app/
│   │   ├── main.py              # Точка входа FastAPI
│   │   ├── config.py            # Настройки из .env
│   │   ├── database.py          # Async SQLAlchemy
│   │   ├── dependencies.py      # JWT авторизация
│   │   ├── models/              # SQLAlchemy модели (7 таблиц)
│   │   ├── schemas/             # Pydantic схемы
│   │   ├── routers/             # API эндпоинты
│   │   └── services/            # Бизнес-логика
│   ├── alembic/                 # Миграции БД
│   ├── tests/                   # Pytest тесты
│   ├── requirements.txt
│   └── Dockerfile
│
├── mobile/
│   ├── app/
│   │   ├── (auth)/              # Экраны входа/регистрации
│   │   ├── (tabs)/              # Основные вкладки
│   │   │   ├── index.tsx        # Главная / дашборд
│   │   │   ├── chat.tsx         # AI-чат
│   │   │   ├── tests.tsx        # Тесты
│   │   │   ├── tutors.tsx       # Маркетплейс репетиторов
│   │   │   └── profile.tsx      # Профиль и прогресс
│   │   └── session/[id].tsx     # Экран видеозанятия
│   ├── services/api.ts          # HTTP клиент
│   ├── store/authStore.ts       # Zustand стор
│   └── constants/theme.ts       # Тема и цвета
│
└── docker-compose.yml
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
GET    /api/v1/users/me/stats     — Общая статистика
GET    /api/v1/users/me/test-history — История тестов
```

### AI-тьютор
```
POST   /api/v1/ai/chat            — Сообщение AI
GET    /api/v1/ai/chat/history    — История чатов
POST   /api/v1/ai/homework        — Проверка ДЗ
POST   /api/v1/ai/generate-test   — Генерация теста
POST   /api/v1/ai/submit-test     — Сдать тест
GET    /api/v1/ai/recommendations  — Рекомендации
```

### Репетиторы
```
GET    /api/v1/tutors/             — Список (фильтры: предмет, цена, рейтинг)
GET    /api/v1/tutors/{id}         — Профиль репетитора
POST   /api/v1/tutors/{id}/review  — Оставить отзыв
GET    /api/v1/tutors/{id}/reviews — Список отзывов
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
POST   /api/v1/video/token          — Agora токен
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
# Отредактируйте .env — укажите API-ключи OpenAI/Anthropic
```

### 3. Запуск через Docker
```bash
docker-compose up -d
```
Сервер доступен: http://localhost:8000
Swagger UI: http://localhost:8000/docs

### 4. Запуск без Docker

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

### 5. Запуск тестов
```bash
cd backend
pip install -r requirements.txt
pytest -v
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

---

## AI-провайдер

Архитектура с абстрактным провайдером — переключение между OpenAI и Anthropic одной переменной:

```env
AI_PROVIDER=openai        # GPT-4o-mini
AI_PROVIDER=anthropic     # Claude Sonnet
```

Оба провайдера реализуют единый интерфейс `BaseAIProvider`, что позволяет добавлять новых провайдеров без изменения бизнес-логики.

---

## Тестирование

Покрытие тестами ключевых модулей:

| Модуль | Тестов | Что покрыто |
|--------|--------|------------|
| auth | 12 | Хеширование, JWT, регистрация, вход, refresh |
| users | 7 | Профиль, обновление, прогресс, статистика |
| tutors | 9 | Список, фильтры, профиль, отзывы |
| subjects | 6 | Предметы, темы, 404 |
| sessions | 6 | Бронирование, список, отмена, доступ |
| video | 3 | Генерация токенов |

```bash
pytest -v                    # все тесты
pytest tests/test_auth.py    # только авторизация
pytest -k "test_login"       # по имени
```

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
- Персональный AI-тьютор
- Проверку ДЗ через AI
- Генерацию тестов с разбором
- Аналитику прогресса

**AI Tutor** — это всё в одном приложении.

---

## Лицензия

Проект создан в рамках дипломной работы.
