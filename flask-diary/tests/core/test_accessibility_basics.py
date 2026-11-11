"""Автоматическая проверка основ доступности HTML (то, что проверяет Lighthouse в первую очередь).

Это не замена Lighthouse и проверке с экранным диктором, но она ловит типичные ошибки разметки
на всех страницах сразу: язык, заголовки, подписи полей, повторяющиеся id, пустые кнопки и ссылки.
"""

from collections import Counter
from html.parser import HTMLParser

import pytest

from tests.helpers import create_card, html, register_and_login

VOID = {'meta', 'link', 'img', 'input', 'br', 'hr'}


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.elements = []  # (тег, атрибуты, текст внутри)
        self._stack = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        element = [tag, dict(attrs), '']
        self.elements.append(element)
        if tag not in VOID:
            self._stack.append(element)

    def handle_endtag(self, tag):
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                del self._stack[index:]
                break

    def handle_data(self, data):
        for element in self._stack:
            element[2] += data

    def tags(self, name):
        return [(attrs, text.strip()) for tag, attrs, text in self.elements if tag == name]

    def ids(self):
        return [attrs['id'] for _, attrs, _ in self.elements if 'id' in attrs]


def fetch(client, path):
    return Page(html(client.get(path)))


@pytest.fixture
def pages(client):
    """Страницы приложения: публичные, личные и страница ошибки."""
    register_and_login(client)
    create_card(client)
    paths = ['/home', '/', '/card/1', '/form_create', '/card/1/edit', '/нет-страницы']
    pages = {path: fetch(client, path) for path in paths}
    client.post('/logout/')
    pages['/login/'] = fetch(client, '/login/')
    pages['/register'] = fetch(client, '/register')
    return pages


def test_every_page_has_language_title_viewport_and_one_heading(pages):
    for path, page in pages.items():
        html_attrs = page.tags('html')[0][0]
        assert html_attrs.get('lang') == 'ru', path
        titles = page.tags('title')
        assert len(titles) == 1, path
        assert titles[0][1], f'{path}: пустой заголовок страницы'
        assert any(a.get('name') == 'viewport' for a, _ in page.tags('meta')), path
        assert len(page.tags('h1')) == 1, f'{path}: заголовков h1 должно быть ровно один'


def test_every_page_has_main_landmark_and_working_skip_link(pages):
    for path, page in pages.items():
        assert any(a.get('id') == 'content' for a, _ in page.tags('main')), path
        skip = [a for a, _ in page.tags('a') if 'skip-link' in a.get('class', '')]
        assert skip, f'{path}: нет ссылки «перейти к содержимому»'
        assert skip[0]['href'] == '#content'


def test_ids_are_unique(pages):
    for path, page in pages.items():
        duplicates = [i for i, n in Counter(page.ids()).items() if n > 1]
        assert not duplicates, f'{path}: повторяются id {duplicates}'


def test_every_field_has_a_label(pages):
    for path, page in pages.items():
        labelled = {a.get('for') for a, _ in page.tags('label')}
        for tag in ('input', 'textarea'):
            for attrs, _ in page.tags(tag):
                if attrs.get('type') in ('hidden', 'submit'):
                    continue
                has_label = attrs.get('id') in labelled or attrs.get('aria-label')
                assert has_label, f'{path}: поле {attrs.get("name")} без подписи'


def test_images_have_alt_text(pages):
    for path, page in pages.items():
        for attrs, _ in page.tags('img'):
            assert 'alt' in attrs, f'{path}: у картинки {attrs.get("src")} нет alt'


def test_buttons_and_links_have_names(pages):
    for path, page in pages.items():
        for attrs, text in page.tags('button'):
            assert text or attrs.get('aria-label'), f'{path}: кнопка без текста'
        for attrs, text in page.tags('a'):
            assert text or attrs.get('aria-label'), f'{path}: ссылка {attrs.get("href")} без текста'


def test_dialog_is_labelled_by_existing_elements(pages):
    page = pages['/card/1']
    dialogs = page.tags('dialog')
    ids = set(page.ids())

    assert dialogs
    for attrs, _ in dialogs:
        assert attrs['aria-labelledby'] in ids
        assert attrs['aria-describedby'] in ids


def test_login_and_register_fields_have_autocomplete(pages):
    for path in ('/login/', '/register'):
        for attrs, _ in pages[path].tags('input'):
            if attrs.get('type') in ('text', 'password'):
                assert attrs.get('autocomplete'), (
                    f'{path}: у поля {attrs.get("name")} нет autocomplete'
                )
