"""Бизнес-логика аутентификации. Не зависит от запросов и шаблонов."""

import math
from datetime import UTC, datetime, timedelta

from flask import current_app

from ..extensions import db
from ..logging_setup import safe_text
from ..models import LoginAttempt, User


def utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


# ---------- пользователи ----------


def get_user(user_id):
    return db.session.get(User, user_id)


def find_user(username):
    return db.session.query(User).filter_by(username=username).first()


def create_user(username, password):
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


# ---------- ограничение попыток входа ----------


def _login_keys(ip, username):
    """Ключи счётчиков: общий по адресу и по паре «адрес + логин».

    Пара нужна, чтобы злоумышленник не мог заблокировать чужой аккаунт,
    вводя неверные пароли со своего адреса. Логин берётся из формы как есть
    (существует он или нет), поэтому по поведению нельзя узнать, есть ли
    такой пользователь.
    """
    name = safe_text((username or '').strip().lower(), limit=50)
    return f'ip:{ip}', f'ipuser:{ip}:{name}'


def login_retry_after(ip, username):
    """Через сколько секунд можно пробовать снова (0, если ограничения нет)."""
    config = current_app.config
    window = timedelta(seconds=config['LOGIN_WINDOW_SECONDS'])
    now = utcnow()
    ip_key, pair_key = _login_keys(ip, username)
    limits = (
        (ip_key, config['LOGIN_MAX_ATTEMPTS_PER_IP']),
        (pair_key, config['LOGIN_MAX_ATTEMPTS']),
    )
    retry_after = 0
    for key, limit in limits:
        times = [
            row[0]
            for row in db.session.query(LoginAttempt.created_at)
            .filter(LoginAttempt.key == key, LoginAttempt.created_at >= now - window)
            .order_by(LoginAttempt.created_at)
            .all()
        ]
        if len(times) >= limit:
            # разблокировка наступит, когда самая давняя из «лишних» попыток выйдет из окна
            unblock_at = times[len(times) - limit] + window
            retry_after = max(retry_after, math.ceil((unblock_at - now).total_seconds()))
    return max(retry_after, 0)


def record_failed_login(ip, username):
    now = utcnow()
    for key in _login_keys(ip, username):
        db.session.add(LoginAttempt(key=key, created_at=now))
    # заодно удаляем устаревшие записи
    window = timedelta(seconds=current_app.config['LOGIN_WINDOW_SECONDS'])
    LoginAttempt.query.filter(LoginAttempt.created_at < now - window).delete()
    db.session.commit()


def clear_failed_logins(ip, username):
    _, pair_key = _login_keys(ip, username)
    LoginAttempt.query.filter(LoginAttempt.key == pair_key).delete()
    db.session.commit()
