"""Настройка журнала приложения.

Журнал пишется в стандартный вывод (так его собирают хостинги и Docker).
В него не попадают пароли, токены и содержимое карточек.
"""

import logging
import re
import sys

from flask.logging import default_handler

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def get_log_level(env):
    """Уровень из LOG_LEVEL; при неверном значении INFO."""
    level = (env.get("LOG_LEVEL") or "INFO").upper()
    return level if level in VALID_LEVELS else "INFO"


def safe_text(value, limit=50):
    """Делает введённую пользователем строку безопасной для журнала.

    Убирает управляющие символы (защита от подделки строк журнала через
    переносы) и обрезает длинные значения.
    """
    text = _CONTROL_CHARS.sub(" ", str(value))
    return text if len(text) <= limit else text[:limit] + "…"


def configure_logging(app, level="INFO"):
    """Подключает вывод журнала приложения в stdout (без дублей при повторном вызове)."""
    logger = app.logger
    # Flask сам добавляет свой обработчик (stderr); оставляем только наш,
    # иначе каждая запись выводилась бы дважды.
    logger.removeHandler(default_handler)
    logger.handlers = [h for h in logger.handlers if not getattr(h, "_diary", False)]
    handler = logging.StreamHandler(sys.stdout)
    handler._diary = True
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
