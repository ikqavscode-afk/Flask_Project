"""Flask Diary: фабрика приложения.

Как добавить новый раздел: создайте пакет с блюпринтом (по образцу ``cards``)
и добавьте его в ``_blueprints()``. Подробности: docs/architecture.md.
"""

import mimetypes
import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .extensions import csrf, db, login_manager, migrate
from .logging_setup import configure_logging, get_log_level
from .settings import is_production, load_config

# В минимальных образах Docker нет системной таблицы типов файлов, и Python отдаёт .webp
# как application/octet-stream. Регистрируем тип явно, чтобы он не зависел от окружения.
mimetypes.add_type('image/webp', '.webp')


def _blueprints():
    # Импорт внутри функции: блюпринты импортируют расширения и модели,
    # и им не нужен пакет целиком на момент импорта.
    from .auth import bp as auth_bp
    from .cards import bp as cards_bp
    from .core import bp as core_bp

    return (core_bp, auth_bp, cards_bp)


def create_app(overrides=None):
    """Создаёт приложение. ``overrides`` — словарь настроек поверх окружения (для тестов)."""
    app = Flask(__name__)
    app.config.update(load_config())
    if overrides:
        app.config.update(overrides)

    configure_logging(app, get_log_level(os.environ))

    if is_production():
        # За прокси хостинга (HTTPS завершается на нём): доверяем заголовкам
        # X-Forwarded-For/Proto/Host от одного прокси. Настоящий адрес клиента
        # нужен для ограничения попыток входа.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    from . import models  # noqa: F401  (регистрирует модели для Alembic)
    from .core.errors import register_error_handlers
    from .core.security import register_security_headers

    for blueprint in _blueprints():
        app.register_blueprint(blueprint)
    register_error_handlers(app)
    register_security_headers(app)

    return app
