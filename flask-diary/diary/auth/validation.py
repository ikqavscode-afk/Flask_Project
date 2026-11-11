"""Проверка данных регистрации: логин и пароль."""

import re

USERNAME_MIN, USERNAME_MAX = 3, 50
PASSWORD_MIN, PASSWORD_MAX = 8, 128
# буквы (в том числе кириллица), цифры, точка, дефис, подчёркивание
_USERNAME_RE = re.compile(r"^[\w.-]+$")


def validate_username(raw):
    """Возвращает (очищенный_логин, ошибка_или_None)."""
    username = (raw or "").strip()
    if not USERNAME_MIN <= len(username) <= USERNAME_MAX:
        return username, f"Логин: от {USERNAME_MIN} до {USERNAME_MAX} символов"
    if not _USERNAME_RE.match(username):
        return username, ("Логин может содержать только буквы, цифры, точку, дефис и подчёркивание")
    return username, None


def validate_password(raw):
    """Возвращает ошибку или None. Пробелы по краям пароля допустимы."""
    if raw is None or not raw.strip():
        return "Пароль не может состоять из пробелов"
    if not PASSWORD_MIN <= len(raw) <= PASSWORD_MAX:
        return f"Пароль: от {PASSWORD_MIN} до {PASSWORD_MAX} символов"
    return None
