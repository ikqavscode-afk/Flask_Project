import pytest

from diary.auth.validation import validate_password, validate_username
from diary.cards.validation import validate_card
from diary.extensions import db
from diary.models import Card, User


# ---------- Логин ----------

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("alice", "alice"),
        ("  alice  ", "alice"),
        ("иван_1", "иван_1"),
        ("a.b-c_d", "a.b-c_d"),
        ("abc", "abc"),
        ("a" * 50, "a" * 50),
    ],
)
def test_username_valid(raw, expected):
    username, error = validate_username(raw)

    assert error is None
    assert username == expected


@pytest.mark.parametrize(
    "raw",
    ["ab", "a" * 51, "", None, "  ab  ", "bad name", "john!", "<script>", "a@b"],
)
def test_username_invalid(raw):
    _, error = validate_username(raw)

    assert error is not None


# ---------- Пароль ----------

@pytest.mark.parametrize("raw", ["12345678", "a" * 128, " pass word ", "Пароль-123"])
def test_password_valid(raw):
    assert validate_password(raw) is None


@pytest.mark.parametrize("raw", ["1234567", "a" * 129, "        ", "", None])
def test_password_invalid(raw):
    assert validate_password(raw) is not None


# ---------- Карточка ----------

def test_card_valid_is_trimmed():
    data, errors = validate_card("  Заголовок ", " под ", "  текст\n")

    assert errors == []
    assert data == {"title": "Заголовок", "subtitle": "под", "text": "текст"}


def test_card_subtitle_is_optional():
    data, errors = validate_card("T", None, "x")

    assert errors == []
    assert data["subtitle"] == ""


@pytest.mark.parametrize(
    "title, subtitle, text, fragment",
    [
        ("", "", "x", "Заголовок не может быть пустым"),
        ("   ", "", "x", "Заголовок не может быть пустым"),
        ("t" * 101, "", "x", "Заголовок не длиннее 100"),
        ("t", "s" * 101, "x", "Подзаголовок не длиннее 100"),
        ("t", "", "", "Текст не может быть пустым"),
        ("t", "", "   ", "Текст не может быть пустым"),
        ("t", "", "x" * 5001, "Текст не длиннее 5000"),
    ],
)
def test_card_invalid(title, subtitle, text, fragment):
    _, errors = validate_card(title, subtitle, text)

    assert any(fragment in e for e in errors)


def test_card_boundary_lengths_are_valid():
    _, errors = validate_card("t" * 100, "s" * 100, "x" * 5000)

    assert errors == []


def test_card_collects_all_errors():
    _, errors = validate_card("", "s" * 101, "")

    assert len(errors) == 3


# ---------- Через формы ----------

def register(client, username='alice', password='secret123'):
    return client.post(
        '/register',
        data={'username': username, 'password': password},
        follow_redirects=True,
    )


def login(client, username='alice', password='secret123'):
    return client.post(
        '/login/',
        data={'username': username, 'password': password},
        follow_redirects=True,
    )


def count_users(app):
    with app.app_context():
        return db.session.query(User).count()


def count_cards(app):
    with app.app_context():
        return db.session.query(Card).count()


def text_of(response):
    return response.data.decode('utf-8')


def test_register_short_username_is_rejected(app, client):
    response = client.post('/register', data={'username': 'ab', 'password': 'secret123'})

    assert response.status_code == 400
    assert 'от 3 до 50' in text_of(response)
    assert count_users(app) == 0


def test_register_bad_characters_are_rejected(app, client):
    response = client.post('/register', data={'username': 'a b!', 'password': 'secret123'})

    assert response.status_code == 400
    assert count_users(app) == 0


def test_register_short_password_is_rejected(app, client):
    response = client.post('/register', data={'username': 'alice', 'password': '1234567'})

    assert response.status_code == 400
    assert 'от 8 до 128' in text_of(response)
    assert count_users(app) == 0


def test_register_whitespace_password_is_rejected(app, client):
    response = client.post('/register', data={'username': 'alice', 'password': '        '})

    assert response.status_code == 400
    assert count_users(app) == 0


def test_register_keeps_entered_username_on_error(client):
    response = client.post('/register', data={'username': 'ab', 'password': 'x'})

    assert 'value="ab"' in text_of(response)


def test_register_trims_username(app, client):
    register(client, username='  bobby  ')

    with app.app_context():
        assert db.session.query(User).filter_by(username='bobby').first() is not None


def test_register_page_shows_length_hints(client):
    html = text_of(client.get('/register'))

    assert 'maxlength="50"' in html
    assert 'minlength="8"' in html
    assert 'autocomplete="new-password"' in html


def test_create_invalid_card_is_rejected_and_keeps_input(app, client):
    register(client)
    login(client)

    response = client.post(
        '/form_create',
        data={'title': 't' * 101, 'subtitle': 'моя подпись', 'text': 'мой текст'},
    )

    assert response.status_code == 400
    html = text_of(response)
    assert 'Заголовок не длиннее 100' in html
    assert 'моя подпись' in html
    assert 'мой текст' in html
    assert count_cards(app) == 0


def test_create_whitespace_only_fields_are_rejected(app, client):
    register(client)
    login(client)

    response = client.post(
        '/form_create', data={'title': '   ', 'subtitle': '', 'text': '   '}
    )

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
    assert 'Заголовок не длиннее 100' in text_of(response)
    with app.app_context():
        assert db.session.get(Card, 1).title == 'Исходный'


def test_edit_form_shows_current_values(client):
    register(client)
    login(client)
    client.post('/form_create', data={'title': 'Исходный', 'subtitle': 'под', 'text': 'текст'})

    html = text_of(client.get('/card/1/edit'))

    assert 'value="Исходный"' in html
    assert 'value="под"' in html
    assert 'maxlength="5000"' in html


def test_oversized_request_is_rejected(client):
    register(client)
    login(client)

    response = client.post(
        '/form_create',
        data={'title': 't', 'subtitle': '', 'text': 'x' * (70 * 1024)},
    )

    assert response.status_code == 413
