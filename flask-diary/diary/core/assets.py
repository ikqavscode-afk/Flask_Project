"""Кэширование статических файлов.

К адресу каждого статического файла автоматически добавляется параметр ``v`` с отпечатком
содержимого (``/static/css/index.css?v=3fa9c1d2e4``). Такой адрес меняется вместе с файлом,
поэтому его можно кэшировать на год: после обновления сайта браузер сразу возьмёт новую версию.
Шаблоны менять не нужно: параметр добавляет ``url_for``.

Картинки, на которые ссылается CSS (``url('../img/...')``), адреса без версии и кэшируются на сутки;
при замене такого файла давайте ему новое имя.
"""

import hashlib
from functools import lru_cache
from pathlib import Path

from flask import current_app, request

LONG_CACHE = 'public, max-age=31536000, immutable'
SHORT_CACHE = 'public, max-age=86400'
DIGEST_LENGTH = 10


@lru_cache(maxsize=256)
def _digest(path, mtime_ns, size):
    """Отпечаток файла; mtime и размер в аргументах сбрасывают кэш при изменении файла."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:DIGEST_LENGTH]


def static_version(app, filename):
    """Отпечаток файла из папки статики либо None (нет файла или путь выходит за папку)."""
    root = Path(app.static_folder).resolve()
    path = (root / filename).resolve()
    if root not in path.parents or not path.is_file():
        return None
    stat = path.stat()
    return _digest(str(path), stat.st_mtime_ns, stat.st_size)


def add_static_version(endpoint, values):
    """Хук url_for: дописывает ?v=<отпечаток> к адресам статики."""
    if endpoint == 'static' and 'v' not in values and 'filename' in values:
        version = static_version(current_app, values['filename'])
        if version:
            values['v'] = version


def set_static_cache_headers(response):
    if request.endpoint == 'static' and response.status_code in (200, 304):
        response.headers['Cache-Control'] = LONG_CACHE if 'v' in request.args else SHORT_CACHE
    return response


def register_asset_caching(app):
    app.url_defaults(add_static_version)
    app.after_request(set_static_cache_headers)
