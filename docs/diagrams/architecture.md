# Архитектура AI Tutor

## Общая схема

```
┌─────────────────────────────────────────────────────┐
│                 Mobile App (Expo)                    │
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐│
│  │  Auth    │ │ AI Chat  │ │  Tests   │ │ Tutors ││
│  │  Screens │ │  Screen  │ │  Screen  │ │ Market ││
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘│
│       │            │            │            │      │
│       └────────────┴────────────┴────────────┘      │
│                        │                             │
│              Axios HTTP Client                       │
│              (JWT auto-inject)                       │
└────────────────────────┬────────────────────────────┘
                         │ HTTPS
                         ▼
┌────────────────────────────────────────────────────┐
│                  Nginx (reverse proxy)              │
└────────────────────────┬───────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │              API Routers (v1)                 │  │
│  │  auth │ users │ ai │ tutors │ sessions │ video│  │
│  └───────────────────┬──────────────────────────┘  │
│                      │                              │
│  ┌───────────────────┴──────────────────────────┐  │
│  │              Services Layer                   │  │
│  │  auth │ ai_provider │ tutor │ session │ progress│ │
│  └──┬──────────┬──────────────────┬─────────────┘  │
│     │          │                  │                  │
│     ▼          ▼                  ▼                  │
│  ┌──────┐  ┌────────┐    ┌──────────────┐          │
│  │ JWT  │  │   AI   │    │  SQLAlchemy  │          │
│  │ Auth │  │Provider│    │  (async ORM) │          │
│  └──────┘  └───┬────┘    └──────┬───────┘          │
│                │                │                    │
└────────────────┼────────────────┼────────────────────┘
                 │                │
        ┌────────┴────┐    ┌─────┴──────┐
        │             │    │            │
   ┌────▼────┐ ┌──────▼┐  │PostgreSQL  │
   │ OpenAI  │ │Claude │  │   16       │
   │ GPT-4o  │ │Sonnet │  └────────────┘
   └─────────┘ └───────┘
```

## Схема базы данных

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│    users     │     │  tutor_profiles  │     │   reviews    │
├──────────────┤     ├──────────────────┤     ├──────────────┤
│ id           │◄───┐│ id               │◄────│ id           │
│ email        │    ││ user_id (FK)     │     │ tutor_id(FK) │
│ password_hash│    ││ subjects (JSON)  │     │ student_id   │
│ role (enum)  │    ││ price_per_hour   │     │ rating       │
│ full_name    │    ││ experience_years │     │ comment      │
│ avatar_url   │    ││ bio              │     │ created_at   │
│ birth_date   │    ││ education        │     └──────────────┘
│ is_active    │    ││ rating           │
│ created_at   │    ││ reviews_count    │
│ updated_at   │    ││ is_verified      │
└──┬───┬───┬───┘    │└──────┬───────────┘
   │   │   │        │       │
   │   │   │        │  ┌────▼───────────────┐
   │   │   │        │  │ booking_sessions   │
   │   │   │        │  ├────────────────────┤
   │   │   │        ├──│ student_id (FK)    │
   │   │   │        │  │ tutor_id (FK)      │
   │   │   │        │  │ subject_id (FK)    │
   │   │   │        │  │ scheduled_at       │
   │   │   │        │  │ duration_minutes   │
   │   │   │        │  │ status (enum)      │
   │   │   │        │  │ price              │
   │   │   │        │  │ payment_status     │
   │   │   │        │  │ agora_channel_name │
   │   │   │        │  └────────────────────┘
   │   │   │        │
   │   │   │    ┌───▼──────────────┐    ┌──────────────┐
   │   │   │    │  chat_sessions   │    │ chat_messages │
   │   │   │    ├──────────────────┤    ├──────────────┤
   │   │   ├───►│ user_id (FK)     │◄───│ session_id   │
   │   │   │    │ subject_id (FK)  │    │ role (enum)  │
   │   │   │    │ topic            │    │ content      │
   │   │   │    │ provider (enum)  │    │ tokens_used  │
   │   │   │    │ created_at       │    │ created_at   │
   │   │   │    └──────────────────┘    └──────────────┘
   │   │   │
   │   │  ┌▼───────────────────┐
   │   │  │ student_progress   │    ┌──────────────┐
   │   │  ├────────────────────┤    │   subjects   │
   │   │  │ user_id (FK)       │    ├──────────────┤
   │   │  │ subject_id (FK) ───┼───►│ id           │
   │   │  │ topic_id (FK)      │    │ name         │◄──┐
   │   │  │ score              │    │ slug         │   │
   │   │  │ weak_topics (JSON) │    │ description  │   │
   │   │  │ last_activity      │    │ icon         │   │
   │   │  └────────────────────┘    └──────────────┘   │
   │   │                                               │
   │   │  ┌────────────────┐    ┌──────────────────┐   │
   │   │  │ test_attempts  │    │     tests        │   │
   │   │  ├────────────────┤    ├──────────────────┤   │
   │   └─►│ user_id (FK)   │    │ id               │   │
   │      │ test_id (FK) ──┼───►│ subject_id (FK)──┼───┘
   │      │ answers (JSON) │    │ topic            │
   │      │ score          │    │ difficulty(enum) │
   │      │ time_spent     │    │ questions (JSON) │
   │      │ feedback       │    │ created_by_ai    │
   │      │ created_at     │    │ created_at       │
   │      └────────────────┘    └──────────────────┘
   │
   │      ┌──────────────┐
   │      │    topics    │
   │      ├──────────────┤
   └─────►│ subject_id   │
          │ name         │
          │ order        │
          └──────────────┘
```

## Поток AI-чата

```
Пользователь                    Backend                     AI Provider
    │                              │                            │
    │  POST /ai/chat              │                            │
    │  {message, session_id}      │                            │
    │─────────────────────────────►│                            │
    │                              │  Загрузка истории          │
    │                              │  из chat_messages          │
    │                              │                            │
    │                              │  Формирование промпта      │
    │                              │  (system + history + msg)  │
    │                              │                            │
    │                              │  API запрос                │
    │                              │────────────────────────────►│
    │                              │                            │
    │                              │◄────────────────────────────│
    │                              │  Ответ AI                  │
    │                              │                            │
    │                              │  Сохранение в БД           │
    │                              │  (user_msg + ai_msg)       │
    │                              │                            │
    │◄─────────────────────────────│                            │
    │  {session_id, content}      │                            │
    │                              │                            │
```

## Переключение AI-провайдера

```
.env: AI_PROVIDER=openai|anthropic
           │
           ▼
    get_ai_provider()
           │
     ┌─────┴──────┐
     │             │
     ▼             ▼
 OpenAI        Anthropic
 Provider      Provider
     │             │
     └──────┬──────┘
            │
     BaseAIProvider
     (абстрактный интерфейс)
```
