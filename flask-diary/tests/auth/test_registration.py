import diary.auth.views as auth_views
from diary.extensions import db
from diary.models import User
from tests.helpers import count_users, html, register


def test_register_page_opens(client):
    response = client.get('/register')

    assert response.status_code == 200
    assert 'Регистрация'.encode() in response.data


def test_register_creates_user_in_db(app, client):
    register(client)

    with app.app_context():
        user = db.session.query(User).filter_by(username='alice').first()

        assert user is not None


def test_register_duplicate_username_fails(client):
    register(client, username='alice')

    response = register(client, username='alice')

    assert 'уже существует'.encode() in response.data


def test_register_with_empty_fields_shows_error(client):
    response = client.post(
        '/register', data={'username': '', 'password': ''}, follow_redirects=True
    )

    assert 'Заполните все поля'.encode() in response.data


def test_password_is_stored_as_hash(app, client):
    register(client, password='secret123')

    user = db.session.query(User).filter_by(username='alice').one()

    assert user.password != 'secret123'
    assert 'secret123' not in user.password
    assert user.check_password('secret123')
    assert not user.check_password('другой-пароль')


def test_register_short_username_is_rejected(app, client):
    response = client.post('/register', data={'username': 'ab', 'password': 'secret123'})

    assert response.status_code == 400
    assert 'от 3 до 50' in html(response)
    assert count_users(app) == 0


def test_register_bad_characters_are_rejected(app, client):
    response = client.post('/register', data={'username': 'a b!', 'password': 'secret123'})

    assert response.status_code == 400
    assert count_users(app) == 0


def test_register_short_password_is_rejected(app, client):
    response = client.post('/register', data={'username': 'alice', 'password': '1234567'})

    assert response.status_code == 400
    assert 'от 8 до 128' in html(response)
    assert count_users(app) == 0


def test_register_whitespace_password_is_rejected(app, client):
    response = client.post('/register', data={'username': 'alice', 'password': '        '})

    assert response.status_code == 400
    assert count_users(app) == 0


def test_register_keeps_entered_username_on_error(client):
    response = client.post('/register', data={'username': 'ab', 'password': 'x'})

    assert 'value="ab"' in html(response)


def test_register_trims_username(app, client):
    register(client, username='  bobby  ')

    with app.app_context():
        assert db.session.query(User).filter_by(username='bobby').first() is not None


def test_register_page_shows_length_hints(client):
    page = html(client.get('/register'))

    assert 'maxlength="50"' in page
    assert 'minlength="8"' in page
    assert 'autocomplete="new-password"' in page


def test_register_form_limits_come_from_validation_constants(client, monkeypatch):
    monkeypatch.setattr(auth_views, 'USERNAME_MIN', 4)
    monkeypatch.setattr(auth_views, 'USERNAME_MAX', 21)
    monkeypatch.setattr(auth_views, 'PASSWORD_MIN', 11)
    monkeypatch.setattr(auth_views, 'PASSWORD_MAX', 77)

    page = html(client.get('/register'))

    for expected in ('minlength="4"', 'maxlength="21"', 'minlength="11"', 'maxlength="77"'):
        assert expected in page
    assert '4–21 символов' in page
    assert 'От 11 до 77 символов' in page
