import pytest

from diary.core.security import CONTENT_SECURITY_POLICY
from tests.helpers import register_and_login


@pytest.mark.parametrize('path', ['/home', '/login/', '/register', '/нет-такой-страницы'])
def test_security_headers_on_public_and_error_pages(client, path):
    response = client.get(path)

    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert response.headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'
    assert response.headers['Content-Security-Policy'] == CONTENT_SECURITY_POLICY
    assert 'camera=()' in response.headers['Permissions-Policy']
    assert response.headers['Cross-Origin-Opener-Policy'] == 'same-origin'


def test_security_headers_on_authenticated_page_and_redirect(client):
    redirect = client.get('/')  # без входа: перенаправление на страницу входа
    register_and_login(client)
    page = client.get('/')

    assert redirect.status_code == 302
    assert 'Content-Security-Policy' in redirect.headers
    assert page.status_code == 200
    assert 'Content-Security-Policy' in page.headers


def test_security_headers_on_static_files(client):
    response = client.get('/static/css/index.css')

    assert response.status_code == 200
    assert response.headers['X-Content-Type-Options'] == 'nosniff'


def test_csp_is_strict():
    policy = {part.split()[0]: part.split()[1:] for part in CONTENT_SECURITY_POLICY.split('; ')}

    assert policy['default-src'] == ["'self'"]
    assert policy['script-src'] == ["'self'"]
    assert policy['style-src'] == ["'self'"]
    assert policy['frame-ancestors'] == ["'none'"]
    assert policy['object-src'] == ["'none'"]
    assert policy['form-action'] == ["'self'"]
    assert 'unsafe-inline' not in CONTENT_SECURITY_POLICY
    assert 'unsafe-eval' not in CONTENT_SECURITY_POLICY


def test_hsts_only_over_https(client):
    insecure = client.get('/home')
    secure = client.get('/home', base_url='https://localhost')

    assert 'Strict-Transport-Security' not in insecure.headers
    assert secure.headers['Strict-Transport-Security'] == 'max-age=31536000'


def test_application_pages_are_not_cached(client):
    register_and_login(client)

    for path in ('/home', '/'):
        assert client.get(path).headers['Cache-Control'] == 'no-store'


def test_static_files_are_not_forced_to_no_store(client):
    response = client.get('/static/css/index.css')

    assert response.headers.get('Cache-Control') != 'no-store'
