import pytest
from sqlalchemy.orm import Session

import diary.cards.views as card_views
from tests.helpers import html, login, register


def test_404_page_is_friendly(client):
    response = client.get('/такой-страницы-нет')

    assert response.status_code == 404
    page = html(response)
    assert 'Страница не найдена' in page
    assert 'На главную' in page
    assert '<title>404' in page


def test_404_page_does_not_reflect_the_address(client):
    response = client.get('/нет-такой?x=<script>alert(1)</script>')

    page = html(response)
    assert '<script>alert' not in page
    assert 'нет-такой' not in page


def test_404_for_foreign_or_missing_card(client):
    register(client)
    login(client)

    response = client.get('/card/999')

    assert response.status_code == 404
    assert 'Страница не найдена' in html(response)


def test_405_page(client):
    register(client)
    login(client)

    response = client.get('/logout/')

    assert response.status_code == 405
    assert 'Действие не поддерживается' in html(response)


def test_413_page(client):
    register(client)
    login(client)

    response = client.post(
        '/form_create', data={'title': 't', 'subtitle': '', 'text': 'x' * (70 * 1024)}
    )

    assert response.status_code == 413
    assert 'Слишком большой запрос' in html(response)


def test_csrf_failure_shows_session_expired_page(app, client):
    app.config['WTF_CSRF_ENABLED'] = True

    response = client.post('/register', data={'username': 'mallory', 'password': 'secret123'})

    assert response.status_code == 400
    assert 'Сессия устарела' in html(response)


def test_500_page_hides_error_details(app, client, monkeypatch):
    register(client)
    login(client)
    monkeypatch.setitem(app.config, 'PROPAGATE_EXCEPTIONS', False)

    def boom(*args, **kwargs):
        raise RuntimeError('секретная трассировка и пароль базы')

    monkeypatch.setattr(card_views, 'validate_card', boom)

    response = client.post('/form_create', data={'title': 't', 'subtitle': '', 'text': 'x'})

    assert response.status_code == 500
    page = html(response)
    assert 'Внутренняя ошибка сервера' in page
    assert 'секретная' not in page
    assert 'Traceback' not in page


def test_500_page_renders_even_when_database_is_down(app, client, monkeypatch):
    """Страница ошибки не обращается к базе, иначе при сбое базы упала бы и она."""
    register(client)
    login(client)
    monkeypatch.setitem(app.config, 'PROPAGATE_EXCEPTIONS', False)

    def db_down(*args, **kwargs):
        raise RuntimeError('база недоступна')

    # любой запрос к базе (в том числе из SQLAlchemy ORM) теперь падает
    monkeypatch.setattr(Session, 'execute', db_down)

    response = client.get('/')

    assert response.status_code == 500
    assert 'Внутренняя ошибка сервера' in html(response)


def test_error_page_has_accessibility_basics(client):
    page = html(client.get('/нет'))

    assert '<html lang="ru">' in page
    assert 'name="viewport"' in page
    assert '<h1>' in page
    assert 'id="content"' in page


def test_trailing_slash_redirect_still_works(client):
    """Перенаправления (3xx) не должны превращаться в страницу ошибки."""
    response = client.get('/login')

    assert response.status_code in (301, 308)
    assert response.headers['Location'].endswith('/login/')


@pytest.mark.parametrize('path', ['/health'])
def test_health_is_not_affected_by_error_pages(client, path):
    assert client.get(path).get_json() == {'status': 'ok'}
