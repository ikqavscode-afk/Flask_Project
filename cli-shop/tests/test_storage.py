import json

import pytest

from shop.cli import ShopApp
from shop.models import Catalog, Product
from shop.storage import load_catalog, save_catalog
from tests.test_cli import feed_inputs


def make_catalog():
    catalog = Catalog()
    catalog.add_product(Product("Чай", "Продукты", 150.5, 0.1, "Зелёный"))
    catalog.add_product(Product("Книга", "Книги", 900, 0.4))
    return catalog


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "catalog.json"

    save_catalog(make_catalog(), path)
    loaded = load_catalog(path)

    assert [p.to_dict() for p in loaded.get_list()] == [
        p.to_dict() for p in make_catalog().get_list()
    ]


def test_save_creates_missing_folder_and_keeps_unicode(tmp_path):
    path = tmp_path / "nested" / "catalog.json"

    save_catalog(make_catalog(), path)

    assert "Чай" in path.read_text(encoding="utf-8")


def test_load_missing_file_returns_none(tmp_path):
    assert load_catalog(tmp_path / "нет.json") is None


@pytest.mark.parametrize("content", ["не json", '{"a": 1}', '[{"name": "x"}]'])
def test_load_invalid_file_raises_value_error(tmp_path, content):
    path = tmp_path / "bad.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError):
        load_catalog(path)


def test_app_uses_defaults_when_file_is_missing():
    assert len(ShopApp().catalog) == 7


def test_app_recovers_from_broken_file(tmp_path, capsys):
    path = tmp_path / "broken.json"
    path.write_text("{{{", encoding="utf-8")

    app = ShopApp(catalog_path=path)

    assert len(app.catalog) == 7
    assert "повреждён" in capsys.readouterr().out


def test_added_product_is_saved_and_restored(tmp_path, monkeypatch):
    path = tmp_path / "shop.json"
    app = ShopApp(catalog_path=path)
    feed_inputs(monkeypatch, ["Чай", "Продукты", "150,5", "0.1", "Зелёный"])

    app.add_product_to_catalog()
    restored = ShopApp(catalog_path=path)

    assert len(restored.catalog) == 8
    added = restored.catalog.find_by_name("чай")
    assert added.price == 150.5
    assert added.description == "Зелёный"


def test_removed_product_stays_removed(tmp_path, monkeypatch):
    path = tmp_path / "shop.json"
    app = ShopApp(catalog_path=path)
    feed_inputs(monkeypatch, ["1"])

    app.remove_product_from_catalog()

    assert len(ShopApp(catalog_path=path).catalog) == 6


@pytest.mark.parametrize(
    "answers, message",
    [
        (["", "Еда"], "обязательны"),
        (["Чай", "Еда", "abc", "1"], "числами"),
        (["Чай", "Еда", "-5", "1"], "отрицательными"),
    ],
)
def test_add_product_validation(tmp_path, monkeypatch, capsys, answers, message):
    path = tmp_path / "shop.json"
    app = ShopApp(catalog_path=path)
    feed_inputs(monkeypatch, answers)

    app.add_product_to_catalog()

    assert message in capsys.readouterr().out
    assert len(app.catalog) == 7
    assert not path.exists()


def test_remove_product_from_catalog_invalid_input(tmp_path, monkeypatch, capsys):
    app = ShopApp(catalog_path=tmp_path / "shop.json")
    feed_inputs(monkeypatch, ["999"])

    app.remove_product_from_catalog()

    assert "Неверный номер" in capsys.readouterr().out
    assert len(app.catalog) == 7
