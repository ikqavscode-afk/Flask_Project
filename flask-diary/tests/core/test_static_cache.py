import re
from pathlib import Path

import pytest

from diary.core import assets
from diary.core.assets import LONG_CACHE, SHORT_CACHE, static_version
from tests.helpers import html

STATIC = Path(__file__).resolve().parents[2] / 'diary' / 'static'


def test_html_links_to_static_files_carry_a_version(client):
    page = html(client.get('/login/'))

    for path in ('css/index.css', 'js/confirm-dialog.js', 'img/logo.webp', 'img/favicon.png'):
        assert re.search(rf'/static/{re.escape(path)}\?v=[0-9a-f]{{10}}"', page), path


def test_versioned_static_request_is_cached_for_a_year(client):
    version = static_version(client.application, 'css/index.css')

    response = client.get(f'/static/css/index.css?v={version}')

    assert response.status_code == 200
    assert response.headers['Cache-Control'] == LONG_CACHE
    assert 'immutable' in LONG_CACHE


def test_unversioned_static_request_is_cached_for_a_day(client):
    response = client.get('/static/img/fon_1.webp')

    assert response.status_code == 200
    assert response.headers['Cache-Control'] == SHORT_CACHE


def test_not_modified_response_keeps_cache_header(client):
    first = client.get('/static/css/index.css')

    second = client.get('/static/css/index.css', headers={'If-None-Match': first.headers['ETag']})

    assert second.status_code == 304
    assert second.headers['Cache-Control'] == SHORT_CACHE


def test_application_pages_are_still_not_cached(client):
    assert client.get('/home').headers['Cache-Control'] == 'no-store'


def test_version_changes_with_file_content(app, tmp_path, monkeypatch):
    (tmp_path / 'a.css').write_text('body{color:red}', encoding='utf-8')
    monkeypatch.setattr(type(app), 'static_folder', property(lambda self: str(tmp_path)))
    before = static_version(app, 'a.css')
    assert before == static_version(app, 'a.css')  # стабилен, пока файл не менялся

    (tmp_path / 'a.css').write_text('body{color:blue}', encoding='utf-8')

    assert static_version(app, 'a.css') != before


@pytest.mark.parametrize(
    'filename', ['нет-такого.css', '../../etc/passwd', '../__init__.py', 'css']
)
def test_no_version_for_missing_or_escaping_paths(app, filename):
    assert static_version(app, filename) is None


def test_digest_function_is_cached_per_file_state():
    assert assets._digest.cache_info().maxsize == 256


def test_every_url_in_css_points_to_an_existing_file():
    css = (STATIC / 'css' / 'index.css').read_text(encoding='utf-8')
    urls = re.findall(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", css)

    assert urls, 'в CSS не найдено ни одной ссылки url(...)'
    for url in urls:
        assert (STATIC / 'css' / url).resolve().is_file(), url


def test_css_uses_webp_backgrounds_not_jpeg():
    css = (STATIC / 'css' / 'index.css').read_text(encoding='utf-8')

    assert 'fon_1.webp' in css
    assert 'fon_2.webp' in css
    assert '.jpg' not in css


def test_images_stay_small():
    """Защита от случайного добавления тяжёлых картинок: каждая не больше 100 КБ."""
    for image in (STATIC / 'img').iterdir():
        assert image.stat().st_size <= 100_000, f'{image.name}: {image.stat().st_size} байт'
