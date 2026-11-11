from tests.helpers import html, login, register


def test_login_success_redirects_to_index(client):
    register(client)

    response = login(client)

    assert 'Мои карточки'.encode() in response.data


def test_login_wrong_password_shows_error(client):
    register(client)

    response = login(client, password='wrongpass')

    assert 'Неверный логин или пароль'.encode() in response.data


def test_protected_route_requires_login(client):
    """Без авторизации / должен редиректить на логин."""

    response = client.get('/')

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_logout(client):
    register(client)
    login(client)

    response = client.post('/logout/', follow_redirects=True)

    assert 'Добро пожаловать'.encode() in response.data

    response = client.get('/')

    assert response.status_code == 302


def test_logout_get_is_not_allowed(client):
    register(client)
    login(client)

    response = client.get('/logout/')

    assert response.status_code == 405
    # сессия при этом не сброшена
    assert client.get('/').status_code == 200


def test_logout_requires_csrf_token(app, client):
    register(client)
    login(client)
    app.config['WTF_CSRF_ENABLED'] = True

    response = client.post('/logout/')

    assert response.status_code == 400


def test_header_has_logout_form_not_link(client):
    register(client)
    response = login(client)
    html = response.data.decode('utf-8')

    assert 'action="/logout/"' in html
    assert 'href="/logout/"' not in html


def test_login_required_message_is_in_russian(client):
    page = html(client.get('/', follow_redirects=True))

    assert 'Войдите, чтобы открыть эту страницу.' in page
    assert 'Please log in' not in page


def test_login_page_after_redirect_ignores_next_parameter(client):
    """Параметр next не даёт открытого перенаправления: вход ведёт только на главную."""
    register(client)

    response = client.post(
        '/login/?next=https://evil.example/',
        data={'username': 'alice', 'password': 'secret123'},
    )

    assert response.status_code == 302
    assert 'evil.example' not in response.headers['Location']
