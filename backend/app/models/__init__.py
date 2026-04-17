"""Все модели БД — импортируются здесь для Alembic и удобства."""

from app.models.user import User, UserRole
from app.models.subject import Subject, Topic
from app.models.tutor import TutorProfile
from app.models.chat import ChatSession, ChatMessage, AIProvider, MessageRole
from app.models.booking import BookingSession, BookingStatus, PaymentStatus
from app.models.test import Test, TestAttempt, Difficulty, TestFeedback, FeedbackRating
from app.models.progress import StudentProgress
from app.models.review import Review

__all__ = [
    "User", "UserRole",
    "Subject", "Topic",
    "TutorProfile",
    "ChatSession", "ChatMessage", "AIProvider", "MessageRole",
    "BookingSession", "BookingStatus", "PaymentStatus",
    "Test", "TestAttempt", "Difficulty", "TestFeedback", "FeedbackRating",
    "StudentProgress",
    "Review",
]
