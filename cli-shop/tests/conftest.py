import pytest

import shop.cli


@pytest.fixture(autouse=True)
def isolated_catalog_file(tmp_path, monkeypatch):
    """Тесты не должны читать или менять настоящий data/catalog.json."""
    monkeypatch.setattr(shop.cli, "DEFAULT_CATALOG_PATH", tmp_path / "catalog.json")
