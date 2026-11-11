"""Настройки приложения, зависящие от окружения."""
import os

DEV_SECRET_KEY = "dev-secret-key"
MIN_SECRET_KEY_LENGTH = 16


def is_production(env=None):
    env = os.environ if env is None else env
    return env.get("APP_ENV", "development").lower() == "production"


def get_secret_key(env=None):
    """Возвращает SECRET_KEY.

    В режиме разработки при отсутствии ключа берётся значение по умолчанию.
    В режиме production (APP_ENV=production) ключ обязателен: он должен быть
    задан, не совпадать со значением для разработки и быть не короче
    MIN_SECRET_KEY_LENGTH символов, иначе выбрасывается RuntimeError.
    """
    env = os.environ if env is None else env
    key = env.get("SECRET_KEY")

    if not is_production(env):
        return key or DEV_SECRET_KEY

    if not key:
        raise RuntimeError(
            "SECRET_KEY не задан. В режиме production переменная обязательна."
        )
    if key == DEV_SECRET_KEY or len(key) < MIN_SECRET_KEY_LENGTH:
        raise RuntimeError(
            "SECRET_KEY слишком слабый: используйте случайную строку "
            f"не короче {MIN_SECRET_KEY_LENGTH} символов."
        )
    return key


def security_settings(env=None):
    """Настройки cookie сессии и «запомнить меня».

    HttpOnly и SameSite=Lax включены всегда. Secure (только по HTTPS)
    включается в режиме production, чтобы локальная работа по HTTP
    оставалась возможной.
    """
    settings = {
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "REMEMBER_COOKIE_HTTPONLY": True,
        "REMEMBER_COOKIE_SAMESITE": "Lax",
    }
    if is_production(env):
        settings["SESSION_COOKIE_SECURE"] = True
        settings["REMEMBER_COOKIE_SECURE"] = True
    return settings
