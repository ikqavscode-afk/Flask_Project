from datetime import timedelta

import pytest

from diary.auth import services
from diary.extensions import db
from diary.models import LoginAttempt
from tests.helpers import register


def attempt(client, username='alice', password='неверный-пароль', ip='10.0.0.1'):
    return client.post(
        '/login/',
        data={'username': username, 'password': password},
        environ_base={'REMOTE_ADDR': ip},
    )


def fail_times(client, n, username='alice', ip='10.0.0.1'):
    for _ in range(n):
        attempt(client, username=username, ip=ip)


def count_attempts():
    return db.session.query(LoginAttempt).count()


def test_sixth_attempt_is_blocked_after_five_failures(client):
    register(client)
    fail_times(client, 5)

    response = attempt(client)

    assert response.status_code == 429
    assert 'Слишком много попыток входа' in response.get_data(as_text=True)
    assert int(response.headers['Retry-After']) > 0


def test_four_failures_do_not_block(client):
    register(client)
    fail_times(client, 4)

    response = attempt(client)

    assert response.status_code == 302  # обычный отказ с перенаправлением, не блокировка


def test_correct_password_is_also_blocked_during_lockout(client):
    register(client)
    fail_times(client, 5)

    response = attempt(client, password='secret123')

    assert response.status_code == 429


def test_block_does_not_lock_the_account_for_other_addresses(client):
    """Нельзя заблокировать чужой аккаунт, вводя неверные пароли со своего адреса."""
    register(client)
    fail_times(client, 5, ip='10.0.0.1')

    response = attempt(client, password='secret123', ip='10.0.0.2')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')  # вход выполнен


def test_other_usernames_from_same_address_are_not_blocked_by_pair_limit(client):
    register(client)
    fail_times(client, 5, username='alice')

    response = attempt(client, username='bob')

    assert response.status_code == 302


def test_ip_wide_limit_blocks_any_username(client):
    fail_times_users = [f'user{i}' for i in range(20)]
    for name in fail_times_users:
        attempt(client, username=name)

    response = attempt(client, username='совсем-новый-логин')

    assert response.status_code == 429


def test_unknown_usernames_are_counted_too(client):
    """Поведение не должно выдавать, существует ли такой пользователь."""
    fail_times(client, 5, username='нет-такого')

    assert attempt(client, username='нет-такого').status_code == 429


def test_block_looks_the_same_for_existing_and_missing_users(client):
    register(client)
    fail_times(client, 5, username='alice')
    fail_times(client, 5, username='ghost')

    existing = attempt(client, username='alice')
    missing = attempt(client, username='ghost')

    assert existing.status_code == missing.status_code == 429
    assert existing.get_data() == missing.get_data()


def test_successful_login_resets_the_counter(client):
    register(client)
    fail_times(client, 4)
    assert attempt(client, password='secret123').status_code == 302
    client.post('/logout/')

    fail_times(client, 4)  # без сброса это было бы уже 8 неудач

    assert attempt(client).status_code == 302  # пятая неудача после сброса, ещё не блокировка


def test_block_expires_after_the_window(app, client, monkeypatch):
    register(client)
    fail_times(client, 5)
    assert attempt(client).status_code == 429

    later = services.utcnow() + timedelta(seconds=app.config['LOGIN_WINDOW_SECONDS'] + 1)
    monkeypatch.setattr(services, 'utcnow', lambda: later)

    assert attempt(client, password='secret123').status_code == 302


def test_old_attempts_are_cleaned_up(app, client, monkeypatch):
    register(client)
    fail_times(client, 3)
    assert count_attempts() == 6  # по две записи на попытку (адрес и пара)

    later = services.utcnow() + timedelta(seconds=app.config['LOGIN_WINDOW_SECONDS'] + 1)
    monkeypatch.setattr(services, 'utcnow', lambda: later)
    attempt(client)

    assert count_attempts() == 2  # остались только записи последней попытки


def test_blocked_attempt_is_logged(app, client, caplog):
    register(client)
    fail_times(client, 5)

    with caplog.at_level('WARNING', logger=app.logger.name):
        attempt(client)

    assert any('login blocked' in r.getMessage() for r in caplog.records)


def test_blocked_page_never_shows_password(client):
    register(client)
    fail_times(client, 5)

    response = attempt(client, password='мой-секретный-пароль')

    assert 'мой-секретный-пароль' not in response.get_data(as_text=True)


def test_username_in_key_is_bounded_and_case_insensitive(app, client):
    register(client)
    for name in ('Alice', 'ALICE', 'alice', 'aLiCe', 'AlIcE'):
        attempt(client, username=name)

    assert attempt(client, username='alice').status_code == 429
    long_name = 'я' * 5000
    attempt(client, username=long_name)  # не должно падать из-за длины ключа
    with app.app_context():
        longest = max(len(row.key) for row in LoginAttempt.query.all())
    assert longest < 255


@pytest.mark.parametrize(('retry', 'minutes'), [(1, 1), (60, 1), (61, 2), (300, 5)])
def test_message_rounds_minutes_up(client, monkeypatch, retry, minutes):
    monkeypatch.setattr(services, 'login_retry_after', lambda ip, username: retry)

    response = attempt(client)

    assert f'Подождите {minutes} мин.' in response.get_data(as_text=True)
