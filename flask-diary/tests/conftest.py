import os

# Должно быть задано до импорта приложения: адрес БД читается при создании engine.
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

import pytest

from main import app, db


@pytest.fixture
def test_app():
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SECRET_KEY='test-secret-key'
    )

    with app.app_context():
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(test_app):
    return test_app.test_client()
