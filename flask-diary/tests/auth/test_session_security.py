from tests.helpers import register


def session_cookie_header(response):
    cookies = [c for c in response.headers.getlist('Set-Cookie') if c.startswith('session=')]
    assert cookies, 'cookie сессии не установлена'
    return cookies[0]


def test_post_without_csrf_token_is_rejected(app, client):
    app.config['WTF_CSRF_ENABLED'] = True

    response = client.post('/register', data={'username': 'mallory', 'password': 'secret123'})

    assert response.status_code == 400


def test_session_cookie_has_httponly_and_samesite(client):
    register(client)

    response = client.post('/login/', data={'username': 'alice', 'password': 'secret123'})

    header = session_cookie_header(response)
    assert 'HttpOnly' in header
    assert 'SameSite=Lax' in header


def test_session_cookie_is_secure_when_enabled(app, client, monkeypatch):
    monkeypatch.setitem(app.config, 'SESSION_COOKIE_SECURE', True)
    client.post(
        '/register',
        data={'username': 'alice', 'password': 'secret123'},
        base_url='https://localhost',
    )

    response = client.post(
        '/login/',
        data={'username': 'alice', 'password': 'secret123'},
        base_url='https://localhost',
    )

    assert 'Secure' in session_cookie_header(response)
