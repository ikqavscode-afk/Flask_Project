import re

from flask import render_template_string

from tests.helpers import create_card, html, register_and_login


def open_card_page(client, title='Моя заметка'):
    register_and_login(client)
    create_card(client, title=title)
    return html(client.get('/card/1'))


def test_card_page_has_accessible_delete_dialog(client):
    page = open_card_page(client)

    assert '<dialog id="delete-card-dialog"' in page
    assert 'aria-labelledby="delete-card-dialog-title"' in page
    assert 'aria-describedby="delete-card-dialog-text"' in page
    assert 'data-confirm-dialog="delete-card-dialog"' in page
    assert 'Удалить карточку?' in page


def test_cancel_button_is_default_focus_and_precedes_delete(client):
    page = open_card_page(client)

    cancel = page.index('value="cancel"')
    confirm = page.index('value="confirm"')

    assert cancel < confirm
    assert 'value="cancel" autofocus' in page  # безопасный выбор по умолчанию


def test_dialog_form_points_to_existing_dialog(client):
    page = open_card_page(client)

    target = re.search(r'data-confirm-dialog="([^"]+)"', page).group(1)

    assert f'id="{target}"' in page


def test_card_title_in_dialog_is_escaped(client):
    page = open_card_page(client, title='<b>жирный</b>')
    dialog = page[page.index('<dialog') : page.index('</dialog>')]

    assert '<b>жирный</b>' not in dialog
    assert '&lt;b&gt;' in dialog


def test_long_card_title_is_truncated_in_dialog(client):
    page = open_card_page(client, title='А' * 100)
    dialog = page[page.index('<dialog') : page.index('</dialog>')]

    assert 'А' * 100 not in dialog
    # длина 60 включает многоточие: 57 символов + '...'
    assert 'А' * 57 + '...' in dialog


def test_card_page_has_no_browser_confirm_and_loads_script(client):
    page = open_card_page(client)

    assert 'confirm(' not in page
    assert 'js/confirm-dialog.js' in page
    assert re.search(r'<script src="[^"]*confirm-dialog\.js" defer></script>', page)


def test_dialog_script_is_served(client):
    response = client.get('/static/js/confirm-dialog.js')

    assert response.status_code == 200
    assert 'javascript' in response.content_type
    assert 'showModal' in response.get_data(as_text=True)


def test_delete_still_requires_post(client):
    register_and_login(client)
    create_card(client)

    assert client.get('/card/1/delete').status_code == 405


def test_component_renders_with_defaults_and_custom_labels(app):
    template = (
        '{% from "components/confirm_dialog.html" import confirm_dialog %}'
        '{{ confirm_dialog("d1", "Заголовок", "Пояснение") }}'
        '{{ confirm_dialog("d2", "Другой", "Текст", "Да", "Нет") }}'
    )

    with app.test_request_context():
        rendered = render_template_string(template)

    assert 'id="d1"' in rendered
    assert 'Подтвердить' in rendered
    assert 'Отмена' in rendered
    assert 'id="d2"' in rendered
    assert '>Да<' in rendered
    assert '>Нет<' in rendered


def test_dialog_css_keeps_centering_despite_global_margin_reset(client):
    """Глобальный сброс `* { margin: 0 }` убирает центрирование <dialog>: нужен margin: auto."""
    css = client.get('/static/css/index.css').get_data(as_text=True)
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)  # без комментариев

    block = re.search(r'\.dialog\s*\{([^}]*)\}', css).group(1)

    assert 'margin: auto' in block
