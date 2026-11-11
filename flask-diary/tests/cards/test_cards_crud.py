from tests.helpers import create_card, login, register


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
