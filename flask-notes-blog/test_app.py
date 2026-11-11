import pytest

from app import User, app, db


@pytest.fixture
def client():
    """Настраивает тестовое окружение: отдельная БД в памяти для каждого теста."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_home_page_has_register_and_login_buttons(client):
    """Пункт 2: страница /home открывается и содержит обе кнопки."""
    response = client.get("/home")
    html = response.data.decode("utf-8")

    assert response.status_code == 200
    assert "Регистрация" in html
    assert "Логин" in html


def test_register_creates_user_and_redirects_to_login(client):
    """Пункт 3: регистрация создаёт пользователя и перекидывает на /login с сообщением об успехе."""
    response = client.post(
        "/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "secret123",
        },
        follow_redirects=True,
    )
    html = response.data.decode("utf-8")

    assert response.status_code == 200
    assert response.request.path == "/login"
    assert "успешно" in html.lower()

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user is not None
        assert user.email == "test@example.com"


def test_login_success_redirects_to_index_with_greeting(client):
    """Пункт 4: успешный логин перекидывает на главную с приветствием."""
    client.post(
        "/register",
        data={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "mypassword",
        },
        follow_redirects=True,
    )

    response = client.post(
        "/login",
        data={"username": "loginuser", "password": "mypassword"},
        follow_redirects=True,
    )
    html = response.data.decode("utf-8")

    assert response.status_code == 200
    assert response.request.path == "/"
    assert "Добро пожаловать" in html


def test_login_wrong_password_stays_on_login_with_error(client):
    """Пункт 5: неверный пароль — ошибка и остаёмся на /login."""
    client.post(
        "/register",
        data={
            "username": "wronguser",
            "email": "wrong@example.com",
            "password": "correctpass",
        },
        follow_redirects=True,
    )

    response = client.post(
        "/login",
        data={"username": "wronguser", "password": "incorrectpass"},
        follow_redirects=True,
    )
    html = response.data.decode("utf-8")

    assert response.status_code == 200
    assert response.request.path == "/login"
    assert "Неверный логин или пароль" in html


def test_password_is_hashed_in_db(client):
    """Пункт 6: пароль в БД хранится захэшированным, а не в открытом виде."""
    client.post(
        "/register",
        data={
            "username": "hashuser",
            "email": "hash@example.com",
            "password": "plainpassword",
        },
        follow_redirects=True,
    )

    with app.app_context():
        user = User.query.filter_by(username="hashuser").first()
        assert user is not None
        assert user.password != "plainpassword"
        assert user.check_password("plainpassword")


def test_token_is_generated_on_login(client):
    """Шаг 08: при успешном логине в сессию кладётся токен."""
    client.post(
        "/register",
        data={
            "username": "tokenuser",
            "email": "token@example.com",
            "password": "tokenpass",
        },
        follow_redirects=True,
    )
    client.post(
        "/login",
        data={"username": "tokenuser", "password": "tokenpass"},
        follow_redirects=True,
    )

    with client.session_transaction() as sess:
        assert "token" in sess
        assert sess["token"] is not None


def register_and_login(client, username, email):
    client.post(
        "/register",
        data={"username": username, "email": email, "password": "pass12345"},
        follow_redirects=True,
    )
    return client.post(
        "/login",
        data={"username": username, "password": "pass12345"},
        follow_redirects=True,
    )


def add_note(client, title):
    return client.post(
        "/notes",
        data={"title": title, "subtitle": "sub", "text": "text"},
        follow_redirects=True,
    )


def test_notes_require_login(client):
    """Без входа /notes перенаправляет на /login."""
    response = client.get("/notes")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_notes_post_requires_login(client):
    """Без входа нельзя создать заметку."""
    response = client.post("/notes", data={"title": "t", "subtitle": "", "text": "x"})

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_user_can_create_and_see_own_note(client):
    register_and_login(client, "alice", "alice@example.com")

    response = add_note(client, "Моя заметка")

    assert "Моя заметка".encode() in response.data


def test_user_does_not_see_foreign_notes(client):
    register_and_login(client, "alice", "alice@example.com")
    add_note(client, "Секрет Алисы")
    client.get("/logout")

    register_and_login(client, "bob", "bob@example.com")
    response = client.get("/notes")

    assert "Секрет Алисы".encode() not in response.data


def test_logout_closes_access_to_notes(client):
    register_and_login(client, "alice", "alice@example.com")
    client.get("/logout")

    response = client.get("/notes")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
