from tests.helpers import login, register


def test_oversized_request_is_rejected(client):
    register(client)
    login(client)

    response = client.post(
        '/form_create',
        data={'title': 't', 'subtitle': '', 'text': 'x' * (70 * 1024)},
    )

    assert response.status_code == 413
