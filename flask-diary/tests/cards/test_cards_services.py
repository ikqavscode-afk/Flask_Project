"""Слой сервисов карточек проверяется напрямую, без HTTP и шаблонов."""

import pytest
from werkzeug.exceptions import NotFound

from diary.auth import services as auth_services
from diary.cards import services
from diary.extensions import db
from diary.models import Card


@pytest.fixture
def alice(app):
    return auth_services.create_user('alice', 'secret123')


@pytest.fixture
def bob(app):
    return auth_services.create_user('bob', 'secret123')


def data(title='Заголовок', subtitle='подзаголовок', text='текст'):
    return {'title': title, 'subtitle': subtitle, 'text': text}


def test_create_card_belongs_to_user(alice):
    card = services.create_card(alice.id, data(title='Первая'))

    assert card.id is not None
    assert card.user_id == alice.id
    assert (card.title, card.subtitle, card.text) == ('Первая', 'подзаголовок', 'текст')


def test_update_card_changes_all_fields(alice):
    card = services.create_card(alice.id, data())

    services.update_card(card, data(title='Новый', subtitle='', text='другое'))

    saved = db.session.get(Card, card.id)
    assert (saved.title, saved.subtitle, saved.text) == ('Новый', '', 'другое')


def test_delete_card_returns_id_and_removes_row(alice):
    card = services.create_card(alice.id, data())
    card_id = card.id

    assert services.delete_card(card) == card_id
    assert db.session.get(Card, card_id) is None


def test_get_user_card_returns_own_card(alice):
    card = services.create_card(alice.id, data())

    assert services.get_user_card_or_404(card.id, alice.id).id == card.id


def test_get_user_card_hides_foreign_and_missing_cards(alice, bob):
    card = services.create_card(alice.id, data())

    with pytest.raises(NotFound):
        services.get_user_card_or_404(card.id, bob.id)
    with pytest.raises(NotFound):
        services.get_user_card_or_404(99999, alice.id)


def test_search_returns_newest_first(alice):
    for title in ('первая', 'вторая', 'третья'):
        services.create_card(alice.id, data(title=title))

    page = services.search_cards(alice.id, '', page=1, per_page=10)

    assert [c.title for c in page.items] == ['третья', 'вторая', 'первая']


def test_search_is_case_insensitive_and_covers_all_text_fields(alice):
    services.create_card(alice.id, data(title='Python', subtitle='x', text='x'))
    services.create_card(alice.id, data(title='a', subtitle='Python', text='x'))
    services.create_card(alice.id, data(title='a', subtitle='x', text='про PYTHON'))
    services.create_card(alice.id, data(title='борщ', subtitle='x', text='x'))

    page = services.search_cards(alice.id, 'python', page=1, per_page=10)

    assert len(page.items) == 3


def test_search_only_sees_own_cards(alice, bob):
    services.create_card(alice.id, data(title='общее слово'))
    services.create_card(bob.id, data(title='общее слово'))

    page = services.search_cards(alice.id, 'общее', page=1, per_page=10)

    assert [c.user_id for c in page.items] == [alice.id]


def test_search_paginates(alice):
    for number in range(5):
        services.create_card(alice.id, data(title=f'карточка {number}'))

    first = services.search_cards(alice.id, '', page=1, per_page=2)
    last = services.search_cards(alice.id, '', page=3, per_page=2)

    assert (first.pages, first.total, len(first.items)) == (3, 5, 2)
    assert len(last.items) == 1


def test_search_page_out_of_range_is_empty_not_an_error(alice):
    services.create_card(alice.id, data())

    page = services.search_cards(alice.id, '', page=99, per_page=6)

    assert page.items == []
