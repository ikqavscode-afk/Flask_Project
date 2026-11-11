from tests.helpers import create_card, login, register


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
