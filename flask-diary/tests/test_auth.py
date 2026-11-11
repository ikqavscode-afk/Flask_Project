from main import db, User


def register(client, username='alice', password='secret123'):
    return client.post(
        '/register',
        data={'username': username, 'password': password},
        follow_redirects=True
    )


def login(client, username='alice', password='secret123'):
    return client.post(
        '/login/',
        data={'username': username, 'password': password},
        follow_redirects=True
    )


def test_register_page_opens(client):
    response = client.get('/register')

    assert response.status_code == 200
    assert 'Регистрация'.encode('utf-8') in response.data


def test_register_creates_user_in_db(test_app, client):
    register(client)

    with test_app.app_context():
        user = db.session.query(User).filter_by(username='alice').first()

        assert user is not None


def test_register_duplicate_username_fails(client):
    register(client, username='alice')

    response = register(client, username='alice')

    assert 'уже существует'.encode('utf-8') in response.data


def test_login_success_redirects_to_index(client):
    register(client)

    response = login(client)

    assert 'Мои карточки'.encode('utf-8') in response.data


def test_login_wrong_password_shows_error(client):
    register(client)

    response = login(client, password='wrongpass')

    assert 'Неверный логин или пароль'.encode('utf-8') in response.data


def test_protected_route_requires_login(client):
    """Без авторизации / должен редиректить на логин."""

    response = client.get('/')

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_logout(client):
    register(client)
    login(client)

    response = client.get('/logout/', follow_redirects=True)

    assert 'Добро пожаловать'.encode('utf-8') in response.data

    response = client.get('/')

    assert response.status_code == 302
    

def create_card(client, title='Моя заметка'):
    return client.post(
        '/form_create',
        data={'title': title, 'subtitle': 'sub', 'text': 'text'},
        follow_redirects=True
    )


def test_user_sees_only_own_cards(client):
    register(client, username='alice')
    login(client, username='alice')
    create_card(client, title='Секрет Алисы')
    client.get('/logout/')

    register(client, username='bob')
    response = login(client, username='bob')

    assert 'Секрет Алисы'.encode('utf-8') not in response.data


def test_user_cannot_open_foreign_card(client):
    register(client, username='alice')
    login(client, username='alice')
    create_card(client)
    client.get('/logout/')

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
        follow_redirects=True
    )

    assert 'Новый заголовок'.encode('utf-8') in response.data
    assert 'Старый заголовок'.encode('utf-8') not in response.data


def test_edit_card_empty_title_is_rejected(client):
    register(client)
    login(client)
    create_card(client, title='Заголовок')

    response = client.post(
        '/card/1/edit',
        data={'title': '   ', 'subtitle': '', 'text': 't'},
        follow_redirects=True
    )

    assert 'не может быть пустым'.encode('utf-8') in response.data


def test_delete_card_removes_it(client):
    register(client)
    login(client)
    create_card(client, title='Удаляемая')

    response = client.post('/card/1/delete', follow_redirects=True)

    assert 'Карточка удалена'.encode('utf-8') in response.data
    assert client.get('/card/1').status_code == 404


def test_user_cannot_edit_or_delete_foreign_card(client):
    register(client, username='alice')
    login(client, username='alice')
    create_card(client)
    client.get('/logout/')

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

    assert 'Python заметки'.encode('utf-8') in response.data
    assert 'Рецепт борща'.encode('utf-8') not in response.data


def test_search_without_results_shows_message(client):
    register(client)
    login(client)
    create_card(client, title='Что-то')

    response = client.get('/?q=несуществующее')

    assert 'ничего не найдено'.encode('utf-8') in response.data


def test_pagination_splits_cards_between_pages(client):
    register(client)
    login(client)
    for i in range(8):
        create_card(client, title=f'Карточка {i}')

    page1 = client.get('/')
    page2 = client.get('/?page=2')

    assert 'Страница 1 из 2'.encode('utf-8') in page1.data
    assert 'Карточка 7'.encode('utf-8') in page1.data
    assert 'Карточка 0'.encode('utf-8') not in page1.data
    assert 'Карточка 0'.encode('utf-8') in page2.data


def test_post_without_csrf_token_is_rejected(test_app, client):
    test_app.config['WTF_CSRF_ENABLED'] = True

    response = client.post(
        '/register',
        data={'username': 'mallory', 'password': 'secret123'}
    )

    assert response.status_code == 400


def test_register_with_empty_fields_shows_error(client):
    response = client.post(
        '/register',
        data={'username': '', 'password': ''},
        follow_redirects=True
    )

    assert 'Заполните все поля'.encode('utf-8') in response.data


def test_create_redirects_to_form(client):
    register(client)
    login(client)

    response = client.get('/create')

    assert response.status_code == 302
    assert '/form_create' in response.headers['Location']


def test_create_form_page_opens(client):
    register(client)
    login(client)

    response = client.get('/form_create')

    assert response.status_code == 200
    assert 'Создание карточки'.encode('utf-8') in response.data


def session_cookie_header(response):
    cookies = [c for c in response.headers.getlist('Set-Cookie') if c.startswith('session=')]
    assert cookies, 'cookie сессии не установлена'
    return cookies[0]


def test_session_cookie_has_httponly_and_samesite(client):
    register(client)

    response = client.post(
        '/login/', data={'username': 'alice', 'password': 'secret123'}
    )

    header = session_cookie_header(response)
    assert 'HttpOnly' in header
    assert 'SameSite=Lax' in header


def test_session_cookie_is_secure_when_enabled(test_app, client, monkeypatch):
    monkeypatch.setitem(test_app.config, 'SESSION_COOKIE_SECURE', True)
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
