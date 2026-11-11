"""Общие фикстуры тестов.

По умолчанию тесты идут на SQLite в памяти; для проверки на PostgreSQL
задайте TEST_DATABASE_URL (например, в CI). Каждый тест получает своё
приложение, созданное фабрикой, поэтому тесты не влияют друг на друга.
"""
import os

import pytest

from diary import create_app
from diary.extensions import db
from diary.settings import engine_options, normalize_database_url

TEST_DATABASE_URL = normalize_database_url(
    os.environ.get('TEST_DATABASE_URL', 'sqlite:///:memory:')
)


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URL,
        'SQLALCHEMY_ENGINE_OPTIONS': engine_options(TEST_DATABASE_URL),
    })

    with app.app_context():
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()
        db.engine.dispose()  # закрываем соединение этого приложения


@pytest.fixture
def client(app):
    return app.test_client()
