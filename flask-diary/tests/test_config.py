import pytest

from diary.settings import DEV_SECRET_KEY, get_secret_key, is_production

STRONG_KEY = "x" * 32


def test_development_uses_default_key_when_missing():
    assert get_secret_key({}) == DEV_SECRET_KEY


def test_development_prefers_explicit_key():
    assert get_secret_key({"SECRET_KEY": "my-own"}) == "my-own"


def test_production_accepts_strong_key():
    env = {"APP_ENV": "production", "SECRET_KEY": STRONG_KEY}

    assert get_secret_key(env) == STRONG_KEY


@pytest.mark.parametrize(
    "env",
    [
        {"APP_ENV": "production"},
        {"APP_ENV": "production", "SECRET_KEY": ""},
        {"APP_ENV": "production", "SECRET_KEY": DEV_SECRET_KEY},
        {"APP_ENV": "production", "SECRET_KEY": "short"},
        {"APP_ENV": "PRODUCTION", "SECRET_KEY": "short"},
    ],
    ids=["missing", "empty", "dev-default", "too-short", "case-insensitive-mode"],
)
def test_production_rejects_missing_or_weak_key(env):
    with pytest.raises(RuntimeError):
        get_secret_key(env)


@pytest.mark.parametrize(
    "env, expected",
    [({}, False), ({"APP_ENV": "development"}, False), ({"APP_ENV": "production"}, True)],
)
def test_is_production(env, expected):
    assert is_production(env) is expected


from diary.settings import security_settings  # noqa: E402


def test_cookie_flags_in_development():
    settings = security_settings({})

    assert settings["SESSION_COOKIE_HTTPONLY"] is True
    assert settings["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert "SESSION_COOKIE_SECURE" not in settings


def test_cookie_flags_in_production():
    settings = security_settings({"APP_ENV": "production"})

    assert settings["SESSION_COOKIE_SECURE"] is True
    assert settings["REMEMBER_COOKIE_SECURE"] is True
    assert settings["SESSION_COOKIE_HTTPONLY"] is True
    assert settings["SESSION_COOKIE_SAMESITE"] == "Lax"


from diary.settings import engine_options, normalize_database_url  # noqa: E402


@pytest.mark.parametrize(
    "url, expected",
    [
        ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        ("postgresql://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("sqlite:///diary.db", "sqlite:///diary.db"),
        ("sqlite:///:memory:", "sqlite:///:memory:"),
    ],
)
def test_normalize_database_url(url, expected):
    assert normalize_database_url(url) == expected


def test_engine_options_for_postgres_enable_pre_ping():
    assert engine_options("postgresql+psycopg://u:p@h/db") == {"pool_pre_ping": True}


def test_engine_options_for_sqlite_are_empty():
    assert engine_options("sqlite:///diary.db") == {}
