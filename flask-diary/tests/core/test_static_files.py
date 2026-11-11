import pytest


@pytest.mark.parametrize(
    ('path', 'content_type'),
    [
        ('/static/css/index.css', 'text/css'),
        ('/static/js/confirm-dialog.js', 'javascript'),
        ('/static/img/logo.webp', 'image/webp'),
        ('/static/img/favicon.png', 'image/png'),
        ('/static/img/fon_1.webp', 'image/webp'),
    ],
)
def test_static_files_have_correct_content_type(client, path, content_type):
    """Тип файла не должен зависеть от системной таблицы типов (её нет в минимальных образах)."""
    response = client.get(path)

    assert response.status_code == 200
    assert content_type in response.content_type
