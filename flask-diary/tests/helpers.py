"""Общие помощники тестов: регистрация, вход, создание карточки."""

from diary.extensions import db
from diary.models import Card, User

DEFAULT_PASSWORD = 'secret123'


def register(client, username='alice', password=DEFAULT_PASSWORD):
    return client.post(
        '/register',
        data={'username': username, 'password': password},
        follow_redirects=True,
    )


def login(client, username='alice', password=DEFAULT_PASSWORD):
    return client.post(
        '/login/',
        data={'username': username, 'password': password},
        follow_redirects=True,
    )


def register_and_login(client, username='alice', password=DEFAULT_PASSWORD):
    register(client, username, password)
    return login(client, username, password)


def create_card(client, title='Моя заметка', subtitle='подзаголовок', text='текст'):
    return client.post(
        '/form_create',
        data={'title': title, 'subtitle': subtitle, 'text': text},
        follow_redirects=True,
    )


def html(response):
    return response.get_data(as_text=True)


def count_users(app):
    with app.app_context():
        return db.session.query(User).count()


def count_cards(app):
    with app.app_context():
        return db.session.query(Card).count()
