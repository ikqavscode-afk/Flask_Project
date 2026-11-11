import diary.cards.views as card_views
from diary.extensions import db
from diary.models import Card
from tests.helpers import count_cards, create_card, html, login, register


def test_edit_card_empty_title_is_rejected(client):
    register(client)
    login(client)
    create_card(client, title='Заголовок')

    response = client.post(
        '/card/1/edit', data={'title': '   ', 'subtitle': '', 'text': 't'}, follow_redirects=True
    )

    assert 'не может быть пустым'.encode() in response.data


def test_create_invalid_card_is_rejected_and_keeps_input(app, client):
    register(client)
    login(client)

    response = client.post(
        '/form_create',
        data={'title': 't' * 101, 'subtitle': 'моя подпись', 'text': 'мой текст'},
    )

    assert response.status_code == 400
    page = html(response)
    assert 'Заголовок не длиннее 100' in page
    assert 'моя подпись' in page
    assert 'мой текст' in page
    assert count_cards(app) == 0


def test_create_whitespace_only_fields_are_rejected(app, client):
    register(client)
    login(client)

    response = client.post('/form_create', data={'title': '   ', 'subtitle': '', 'text': '   '})

    assert response.status_code == 400
    assert count_cards(app) == 0


def test_create_trims_fields(app, client):
    register(client)
    login(client)

    client.post(
        '/form_create',
        data={'title': '  Тест  ', 'subtitle': '', 'text': '  текст  '},
    )

    with app.app_context():
        card = db.session.query(Card).one()
        assert card.title == 'Тест'
        assert card.text == 'текст'


def test_edit_invalid_data_keeps_original_card(app, client):
    register(client)
    login(client)
    client.post('/form_create', data={'title': 'Исходный', 'subtitle': '', 'text': 'текст'})

    response = client.post(
        '/card/1/edit', data={'title': 'н' * 101, 'subtitle': '', 'text': 'новый'}
    )

    assert response.status_code == 400
    assert 'Заголовок не длиннее 100' in html(response)
    with app.app_context():
        assert db.session.get(Card, 1).title == 'Исходный'


def test_edit_form_shows_current_values(client):
    register(client)
    login(client)
    client.post('/form_create', data={'title': 'Исходный', 'subtitle': 'под', 'text': 'текст'})

    page = html(client.get('/card/1/edit'))

    assert 'value="Исходный"' in page
    assert 'value="под"' in page
    assert 'maxlength="5000"' in page


def test_card_form_limits_come_from_validation_constants(client, monkeypatch):
    monkeypatch.setattr(card_views, 'TITLE_MAX', 7)
    monkeypatch.setattr(card_views, 'SUBTITLE_MAX', 8)
    monkeypatch.setattr(card_views, 'TEXT_MAX', 9)
    register(client)
    login(client)

    page = html(client.get('/form_create'))

    assert 'maxlength="7"' in page
    assert 'maxlength="8"' in page
    assert 'maxlength="9"' in page
