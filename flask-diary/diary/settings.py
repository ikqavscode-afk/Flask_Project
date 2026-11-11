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


def normalize_database_url(url):
    """Приводит адрес базы к виду, понятному SQLAlchemy с драйвером psycopg 3.

    Хостинги выдают адреса вида postgres:// или postgresql://, а SQLAlchemy 2
    не принимает первый вариант и для второго ожидает драйвер psycopg2.
    """
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def engine_options(url):
    """Параметры подключения: для PostgreSQL проверяем соединение перед использованием.

    Хостинги закрывают простаивающие соединения, без проверки следующий
    запрос мог бы завершиться ошибкой.
    """
    if url.startswith("postgresql"):
        return {"pool_pre_ping": True}
    return {}


# Значения по умолчанию, не зависящие от окружения
DEFAULTS = {
    "MAX_CONTENT_LENGTH": 64 * 1024,  # больше 64 КБ в запросе — ошибка 413
    "CARDS_PER_PAGE": 6,
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    # Ограничение попыток входа: после LOGIN_MAX_ATTEMPTS неудач с одного адреса
    # для одного логина (или LOGIN_MAX_ATTEMPTS_PER_IP неудач с одного адреса
    # для любых логинов) вход блокируется до конца окна LOGIN_WINDOW_SECONDS.
    "LOGIN_MAX_ATTEMPTS": 5,
    "LOGIN_MAX_ATTEMPTS_PER_IP": 20,
    "LOGIN_WINDOW_SECONDS": 300,
}


def load_config(env=None):
    """Собирает настройки приложения из значений по умолчанию и переменных окружения."""
    env = os.environ if env is None else env
    database_url = normalize_database_url(env.get("DATABASE_URL", "sqlite:///diary.db"))
    config = dict(DEFAULTS)
    config.update(security_settings(env))
    config.update(
        SECRET_KEY=get_secret_key(env),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_ENGINE_OPTIONS=engine_options(database_url),
    )
    return config
