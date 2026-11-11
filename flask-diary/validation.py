"""Проверка данных, введённых пользователем."""
import re

USERNAME_MIN, USERNAME_MAX = 3, 50
PASSWORD_MIN, PASSWORD_MAX = 8, 128
TITLE_MAX = 100
SUBTITLE_MAX = 100
TEXT_MAX = 5000

# буквы (в том числе кириллица), цифры, точка, дефис, подчёркивание
_USERNAME_RE = re.compile(r"^[\w.-]+$")


def validate_username(raw):
    """Возвращает (очищенный_логин, ошибка_или_None)."""
    username = (raw or "").strip()
    if not USERNAME_MIN <= len(username) <= USERNAME_MAX:
        return username, f"Логин: от {USERNAME_MIN} до {USERNAME_MAX} символов"
    if not _USERNAME_RE.match(username):
        return username, (
            "Логин может содержать только буквы, цифры, "
            "точку, дефис и подчёркивание"
        )
    return username, None


def validate_password(raw):
    """Возвращает ошибку или None. Пробелы по краям пароля допустимы."""
    if raw is None or not raw.strip():
        return "Пароль не может состоять из пробелов"
    if not PASSWORD_MIN <= len(raw) <= PASSWORD_MAX:
        return f"Пароль: от {PASSWORD_MIN} до {PASSWORD_MAX} символов"
    return None


def validate_card(title, subtitle, text):
    """Возвращает (очищенные_данные, список_ошибок)."""
    data = {
        "title": (title or "").strip(),
        "subtitle": (subtitle or "").strip(),
        "text": (text or "").strip(),
    }
    errors = []

    if not data["title"]:
        errors.append("Заголовок не может быть пустым")
    elif len(data["title"]) > TITLE_MAX:
        errors.append(f"Заголовок не длиннее {TITLE_MAX} символов")

    if len(data["subtitle"]) > SUBTITLE_MAX:
        errors.append(f"Подзаголовок не длиннее {SUBTITLE_MAX} символов")

    if not data["text"]:
        errors.append("Текст не может быть пустым")
    elif len(data["text"]) > TEXT_MAX:
        errors.append(f"Текст не длиннее {TEXT_MAX} символов")

    return data, errors
