"""Проверка данных карточки."""

TITLE_MAX = 100
SUBTITLE_MAX = 100
TEXT_MAX = 5000


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
