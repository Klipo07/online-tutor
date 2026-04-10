# API Документация — AI Tutor

## Обзор

REST API на FastAPI с автоматической Swagger-документацией.

**Swagger UI:** http://localhost:8000/docs
**ReDoc:** http://localhost:8000/redoc

## Аутентификация

API использует JWT Bearer-токены. Для доступа к защищённым эндпоинтам нужно передать заголовок:

```
Authorization: Bearer <access_token>
```

### Получение токена

```bash
# Регистрация
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "Иван Иванов",
    "role": "student"
  }'

# Вход
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

Ответ содержит `access_token` (30 мин) и `refresh_token` (30 дней).

### Обновление токена

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

## Роли пользователей

| Роль | Возможности |
|------|------------|
| `student` | AI-чат, тесты, бронирование, отзывы |
| `tutor` | Профиль репетитора, занятия, видеозвонки |
| `parent` | Просмотр прогресса ребёнка (в планах) |
| `admin` | Управление платформой (в планах) |

## Примеры запросов

### AI-чат

```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Объясни теорему Пифагора",
    "subject": "Математика",
    "topic": "Геометрия"
  }'
```

### Генерация теста

```bash
curl -X POST http://localhost:8000/api/v1/ai/generate-test \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Физика",
    "topic": "Механика",
    "difficulty": "medium",
    "num_questions": 5
  }'
```

### Бронирование занятия

```bash
curl -X POST http://localhost:8000/api/v1/sessions/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tutor_id": 1,
    "subject_id": 1,
    "scheduled_at": "2026-04-15T15:00:00",
    "duration_minutes": 60
  }'
```

## Коды ответов

| Код | Описание |
|-----|---------|
| 200 | Успех |
| 201 | Создано |
| 400 | Ошибка валидации / бизнес-логики |
| 401 | Не авторизован |
| 403 | Доступ запрещён |
| 404 | Не найдено |
| 409 | Конфликт (дубликат email) |
| 422 | Ошибка валидации данных |
| 502 | Ошибка AI-провайдера |
