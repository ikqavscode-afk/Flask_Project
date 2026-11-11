from diary.extensions import db


def test_health_ok(client):
    response = client.get('/health')

    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}


def test_health_does_not_require_login(client):
    assert client.get('/health').status_code == 200


def test_health_is_not_cached(client):
    response = client.get('/health')

    assert response.headers['Cache-Control'] == 'no-store'


def test_health_reports_database_failure(client, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError('секретные подробности: пароль базы и адрес')

    monkeypatch.setattr(db.session, 'execute', broken)

    response = client.get('/health')

    assert response.status_code == 503
    assert response.get_json() == {'status': 'error'}
    # внутренние детали ошибки наружу не попадают
    assert 'секретные' not in response.get_data(as_text=True)


def test_health_recovers_after_failure(client, monkeypatch):
    original = db.session.execute

    def broken(*args, **kwargs):
        raise RuntimeError('нет связи')

    monkeypatch.setattr(db.session, 'execute', broken)
    assert client.get('/health').status_code == 503

    monkeypatch.setattr(db.session, 'execute', original)
    assert client.get('/health').status_code == 200
