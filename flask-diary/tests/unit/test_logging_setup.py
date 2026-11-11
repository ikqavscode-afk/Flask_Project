import pytest
from flask.logging import default_handler

from diary.logging_setup import configure_logging, get_log_level, safe_text


def test_safe_text_removes_control_characters():
    assert safe_text('a\nb\r\tc\x00d') == 'a b  c d'


def test_safe_text_truncates_long_values():
    result = safe_text('x' * 100, limit=10)

    assert result == 'x' * 10 + '…'


@pytest.mark.parametrize(
    ('env', 'expected'),
    [
        ({}, 'INFO'),
        ({'LOG_LEVEL': 'debug'}, 'DEBUG'),
        ({'LOG_LEVEL': 'ERROR'}, 'ERROR'),
        ({'LOG_LEVEL': 'болтовня'}, 'INFO'),
        ({'LOG_LEVEL': ''}, 'INFO'),
    ],
)
def test_get_log_level(env, expected):
    assert get_log_level(env) == expected


def test_flask_default_handler_is_removed(app):
    logger = configure_logging(app, 'INFO')

    assert default_handler not in logger.handlers
    assert len(logger.handlers) == 1


def test_configure_logging_does_not_duplicate_handlers(app):
    logger = configure_logging(app, 'INFO')
    before = len(logger.handlers)

    configure_logging(app, 'INFO')

    assert len(logger.handlers) == before
