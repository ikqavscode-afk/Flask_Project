"""Слой сервисов аутентификации проверяется напрямую, без HTTP и шаблонов."""

from datetime import timedelta

import pytest

from diary.auth import services
from diary.extensions import db
from diary.models import LoginAttempt

IP = '10.0.0.1'


def fail(times, username='alice', ip=IP):
    for _ in range(times):
        services.record_failed_login(ip, username)


def test_create_user_hashes_password(app):
    user = services.create_user('alice', 'secret123')

    assert user.id is not None
    assert user.password != 'secret123'
    assert user.check_password('secret123')


def test_find_user_and_get_user(app):
    user = services.create_user('alice', 'secret123')

    assert services.find_user('alice').id == user.id
    assert services.find_user('нет такого') is None
    assert services.get_user(user.id).username == 'alice'
    assert services.get_user(99999) is None


def test_utcnow_is_naive_utc(app):
    now = services.utcnow()

    assert now.tzinfo is None


def test_no_limit_without_failed_attempts(app):
    assert services.login_retry_after(IP, 'alice') == 0


def test_limit_after_five_failures_for_the_same_pair(app):
    fail(5)

    retry_after = services.login_retry_after(IP, 'alice')

    assert 0 < retry_after <= app.config['LOGIN_WINDOW_SECONDS']


def test_four_failures_are_not_a_limit(app):
    fail(4)

    assert services.login_retry_after(IP, 'alice') == 0


def test_pair_limit_does_not_block_other_username_or_address(app):
    fail(5)

    assert services.login_retry_after(IP, 'bob') == 0
    assert services.login_retry_after('10.0.0.2', 'alice') == 0


def test_address_limit_blocks_any_username(app):
    for number in range(20):
        services.record_failed_login(IP, f'user{number}')

    assert services.login_retry_after(IP, 'совсем-новый') > 0


def test_username_is_case_and_space_insensitive(app):
    for name in ('Alice', ' ALICE ', 'alice', 'aLiCe', 'AlIcE'):
        services.record_failed_login(IP, name)

    assert services.login_retry_after(IP, 'alice') > 0


def test_clear_failed_logins_resets_only_the_pair(app):
    fail(5)

    services.clear_failed_logins(IP, 'alice')

    assert services.login_retry_after(IP, 'alice') == 0
    # счётчик адреса остаётся: записи по адресу не удаляются
    assert db.session.query(LoginAttempt).filter_by(key=f'ip:{IP}').count() == 5


def test_old_attempts_expire_and_are_pruned(app, monkeypatch):
    fail(5)
    later = services.utcnow() + timedelta(seconds=app.config['LOGIN_WINDOW_SECONDS'] + 1)
    monkeypatch.setattr(services, 'utcnow', lambda: later)

    assert services.login_retry_after(IP, 'alice') == 0

    services.record_failed_login(IP, 'alice')  # заодно удаляет устаревшее
    assert db.session.query(LoginAttempt).count() == 2


@pytest.mark.parametrize(
    ('limit_key', 'limit'), [('LOGIN_MAX_ATTEMPTS', 2), ('LOGIN_MAX_ATTEMPTS_PER_IP', 2)]
)
def test_limits_are_configurable(app, limit_key, limit):
    app.config[limit_key] = limit
    fail(limit)

    assert services.login_retry_after(IP, 'alice') > 0
