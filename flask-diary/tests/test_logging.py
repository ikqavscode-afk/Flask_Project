import logging

import pytest

import diary.cards.views as card_views
from diary.logging_setup import configure_logging, get_log_level, safe_text

PASSWORD = 'очень-секретный-пароль-123'


@pytest.fixture
def logs(caplog, app):
    caplog.set_level(logging.INFO, logger=app.logger.name)
    return caplog


def register(client, username='alice', password=PASSWORD):
    return client.post(
        '/register',
        data={'username': username, 'password': password},
        follow_redirects=True,
    )


def login(client, username='alice', password=PASSWORD):
    return client.post(
        '/login/',
        data={'username': username, 'password': password},
        follow_redirects=True,
    )


def messages(logs):
    return [record.getMessage() for record in logs.records]


# ---------- События ----------

def test_register_and_login_are_logged(client, logs):
    register(client)
    login(client)

    text = '\n'.join(messages(logs))
    assert 'register ok user_id=1' in text
    assert 'login ok user_id=1' in text


def test_failed_login_is_logged_as_warning(client, logs):
    register(client)

    login(client, password='неверный-пароль')

    warnings = [r for r in logs.records if r.levelno == logging.WARNING]
    assert any('login failed' in r.getMessage() for r in warnings)


def test_logout_is_logged(client, logs):
    register(client)
    login(client)

    client.post('/logout/')

    assert any('logout user_id=1' in m for m in messages(logs))


def test_card_changes_are_logged_without_content(client, logs):
    register(client)
    login(client)

    client.post('/form_create', data={'title': 'Личный заголовок', 'subtitle': '', 'text': 'Личный текст'})
    client.post('/card/1/edit', data={'title': 'Новый заголовок', 'subtitle': '', 'text': 'Новый текст'})
    client.post('/card/1/delete')

    text = '\n'.join(messages(logs))
    assert 'card created id=1 user_id=1' in text
    assert 'card updated id=1 user_id=1' in text
    assert 'card deleted id=1 user_id=1' in text
    for private in ('Личный заголовок', 'Личный текст', 'Новый заголовок', 'Новый текст'):
        assert private not in text


# ---------- Что в журнал попадать не должно ----------

def test_passwords_never_appear_in_logs(client, logs):
    register(client)
    login(client)
    login(client, password='другой-неверный-пароль')
    client.post('/register', data={'username': 'bob', 'password': '1234'})  # слишком короткий

    text = '\n'.join(messages(logs))
    assert PASSWORD not in text
    assert 'другой-неверный-пароль' not in text
    assert '1234' not in text


def test_log_injection_via_username_is_neutralized(client, logs):
    client.post(
        '/login/',
        data={'username': 'evil\nINFO login ok user_id=1', 'password': 'x'},
    )

    failed = [m for m in messages(logs) if 'login failed' in m]
    assert failed
    assert all('\n' not in m for m in failed)


# ---------- Необработанные ошибки ----------

def test_unhandled_error_is_logged_with_traceback(app, client, monkeypatch, logs):
    register(client)
    login(client)
    monkeypatch.setitem(app.config, 'PROPAGATE_EXCEPTIONS', False)

    def boom(*args, **kwargs):
        raise RuntimeError('внутренний сбой')

    monkeypatch.setattr(card_views, 'validate_card', boom)

    response = client.post('/form_create', data={'title': 't', 'subtitle': '', 'text': 'x'})

    assert response.status_code == 500
    errors = [r for r in logs.records if r.levelno >= logging.ERROR]
    assert errors
    assert errors[0].exc_info is not None
    assert 'внутренний сбой' not in response.get_data(as_text=True)


# ---------- Вспомогательные функции ----------

def test_safe_text_removes_control_characters():
    assert safe_text('a\nb\r\tc\x00d') == 'a b  c d'


def test_safe_text_truncates_long_values():
    result = safe_text('x' * 100, limit=10)

    assert result == 'x' * 10 + '…'


@pytest.mark.parametrize(
    'env, expected',
    [({}, 'INFO'), ({'LOG_LEVEL': 'debug'}, 'DEBUG'), ({'LOG_LEVEL': 'ERROR'}, 'ERROR'),
     ({'LOG_LEVEL': 'болтовня'}, 'INFO'), ({'LOG_LEVEL': ''}, 'INFO')],
)
def test_get_log_level(env, expected):
    assert get_log_level(env) == expected


def test_flask_default_handler_is_removed(app):
    from flask.logging import default_handler

    logger = configure_logging(app, 'INFO')

    assert default_handler not in logger.handlers
    assert len(logger.handlers) == 1


def test_configure_logging_does_not_duplicate_handlers(app):
    logger = configure_logging(app, 'INFO')
    before = len(logger.handlers)

    configure_logging(app, 'INFO')

    assert len(logger.handlers) == before
