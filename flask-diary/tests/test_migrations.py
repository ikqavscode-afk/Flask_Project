from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from flask_migrate import downgrade, upgrade
from sqlalchemy import inspect, text

from main import app, db

MIGRATIONS_DIR = str(Path(__file__).resolve().parent.parent / "migrations")


def _reset():
    db.session.remove()
    db.drop_all()
    db.session.execute(text("DROP TABLE IF EXISTS alembic_version"))
    db.session.commit()


@pytest.fixture
def empty_db():
    """Пустая база: схему создаёт только миграция."""
    with app.app_context():
        _reset()
        yield
        _reset()


def table_names():
    return set(inspect(db.engine).get_table_names())


def test_upgrade_creates_schema(empty_db):
    upgrade(directory=MIGRATIONS_DIR)

    assert {"users", "card", "alembic_version"} <= table_names()


def test_migrations_match_models(empty_db):
    """Если изменить модель и забыть миграцию, тест упадёт."""
    upgrade(directory=MIGRATIONS_DIR)

    with db.engine.connect() as connection:
        context = MigrationContext.configure(connection)
        differences = compare_metadata(context, db.metadata)

    assert differences == []


def test_downgrade_removes_schema(empty_db):
    upgrade(directory=MIGRATIONS_DIR)

    downgrade(directory=MIGRATIONS_DIR, revision="base")

    assert "users" not in table_names()
    assert "card" not in table_names()


def test_upgrade_is_repeatable(empty_db):
    upgrade(directory=MIGRATIONS_DIR)
    upgrade(directory=MIGRATIONS_DIR)

    assert {"users", "card"} <= table_names()
