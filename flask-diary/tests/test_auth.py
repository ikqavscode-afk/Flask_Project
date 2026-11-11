from diary.extensions import db
from diary.models import User


def register(client, username='alice', password='secret123'):
    return client.post(
        '/register', data={'username': username, 'password': password}, follow_redirects=True
    )


def login(client, username='alice', password='secret123'):
    return client.post(
        '/login/', data={'username': username, 'password': password}, follow_redirects=True
    )


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


def create_card(client, title='Моя заметка'):
    return client.post(
        '/form_create',
        data={'title': title, 'subtitle': 'sub', 'text': 'text'},
        follow_redirects=True,
    )


def test_user_sees_only_own_cards(client):
    register(client, username='alice')
    login(client, username='alice')
    create_card(client, title='Секрет Алисы')
    client.post('/logout/')

    register(client, username='bob')
    response = login(client, username='bob')

    assert 'Секрет Алисы'.encode() not in response.data


def test_user_cannot_open_foreign_card(client):
    register(client, username='alice')
    login(client, username='alice')
    create_card(client)
    client.post('/logout/')

    register(client, username='bob')
    login(client, username='bob')

    assert client.get('/card/1').status_code == 404


def test_edit_card_updates_data(client):
    register(client)
    login(client)
    create_card(client, title='Старый заголовок')

    response = client.post(
        '/card/1/edit',
        data={'title': 'Новый заголовок', 'subtitle': 's', 'text': 't'},
        follow_redirects=True,
    )

    assert 'Новый заголовок'.encode() in response.data
    assert 'Старый заголовок'.encode() not in response.data


def test_edit_card_empty_title_is_rejected(client):
    register(client)
    login(client)
    create_card(client, title='Заголовок')

    response = client.post(
        '/card/1/edit', data={'title': '   ', 'subtitle': '', 'text': 't'}, follow_redirects=True
    )

    assert 'не может быть пустым'.encode() in response.data


def test_delete_card_removes_it(client):
    register(client)
    login(client)
    create_card(client, title='Удаляемая')

    response = client.post('/card/1/delete', follow_redirects=True)

    assert 'Карточка удалена'.encode() in response.data
    assert client.get('/card/1').status_code == 404


def test_user_cannot_edit_or_delete_foreign_card(client):
    register(client, username='alice')
    login(client, username='alice')
    create_card(client)
    client.post('/logout/')

    register(client, username='bob')
    login(client, username='bob')

    assert client.post('/card/1/edit', data={'title': 'x'}).status_code == 404
    assert client.post('/card/1/delete').status_code == 404


def test_search_finds_matching_cards_only(client):
    register(client)
    login(client)
    create_card(client, title='Python заметки')
    create_card(client, title='Рецепт борща')

    response = client.get('/?q=python')

    assert 'Python заметки'.encode() in response.data
    assert 'Рецепт борща'.encode() not in response.data


def test_search_without_results_shows_message(client):
    register(client)
    login(client)
    create_card(client, title='Что-то')

    response = client.get('/?q=несуществующее')

    assert 'ничего не найдено'.encode() in response.data


def test_pagination_splits_cards_between_pages(client):
    register(client)
    login(client)
    for i in range(8):
        create_card(client, title=f'Карточка {i}')

    page1 = client.get('/')
    page2 = client.get('/?page=2')

    assert 'Страница 1 из 2'.encode() in page1.data
    assert 'Карточка 7'.encode() in page1.data
    assert 'Карточка 0'.encode() not in page1.data
    assert 'Карточка 0'.encode() in page2.data


def test_post_without_csrf_token_is_rejected(app, client):
    app.config['WTF_CSRF_ENABLED'] = True

    response = client.post('/register', data={'username': 'mallory', 'password': 'secret123'})

    assert response.status_code == 400


def test_register_with_empty_fields_shows_error(client):
    response = client.post(
        '/register', data={'username': '', 'password': ''}, follow_redirects=True
    )

    assert 'Заполните все поля'.encode() in response.data


def test_header_menu_links_directly_to_create_form(client):
    register(client)
    page = login(client).get_data(as_text=True)

    assert 'href="/form_create"' in page


def test_create_form_page_opens(client):
    register(client)
    login(client)

    response = client.get('/form_create')

    assert response.status_code == 200
    assert 'Создание карточки'.encode() in response.data


def session_cookie_header(response):
    cookies = [c for c in response.headers.getlist('Set-Cookie') if c.startswith('session=')]
    assert cookies, 'cookie сессии не установлена'
    return cookies[0]


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


def test_password_is_stored_as_hash(app, client):
    register(client, password='secret123')

    user = db.session.query(User).filter_by(username='alice').one()

    assert user.password != 'secret123'
    assert 'secret123' not in user.password
    assert user.check_password('secret123')
    assert not user.check_password('другой-пароль')
