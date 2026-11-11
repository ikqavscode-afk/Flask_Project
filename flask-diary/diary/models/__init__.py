"""Модели базы данных.

Каждая сущность лежит в своём файле. Новую модель нужно импортировать здесь,
иначе Alembic не увидит её при создании миграции.
"""
from .card import Card
from .login_attempt import LoginAttempt
from .user import User

__all__ = ["Card", "LoginAttempt", "User"]
