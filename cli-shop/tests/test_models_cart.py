import pytest

from shop.cart import Cart
from shop.models import Catalog, Product


@pytest.fixture
def apple():
    return Product("Яблоко", "Продукты", 50.0, 0.2, "Красное")


@pytest.fixture
def book():
    return Product("Книга", "Книги", 1200.0, 0.5)


def test_product_to_dict(apple):
    assert apple.to_dict() == {
        "name": "Яблоко",
        "category": "Продукты",
        "price": 50.0,
        "weight": 0.2,
        "description": "Красное",
    }


def test_catalog_add_and_len(apple, book):
    catalog = Catalog()
    catalog.add_product(apple)
    catalog.add_product(book)

    assert len(catalog) == 2
    assert catalog.get_list() == [apple, book]


def test_catalog_find_by_name_ignores_case(apple):
    catalog = Catalog()
    catalog.add_product(apple)

    assert catalog.find_by_name("яБлОкО") is apple
    assert catalog.find_by_name("нет такого") is None


def test_catalog_edit_product_changes_known_fields_only(apple):
    catalog = Catalog()
    catalog.add_product(apple)

    catalog.edit_product(0, price=75.0, unknown_field="x")

    assert apple.price == 75.0
    assert not hasattr(apple, "unknown_field")


def test_catalog_remove_product(apple, book):
    catalog = Catalog()
    catalog.add_product(apple)
    catalog.add_product(book)

    catalog.remove_product(0)

    assert catalog.get_list() == [book]


def test_empty_cart_totals_are_zero():
    cart = Cart()

    assert len(cart) == 0
    assert cart.total_price() == 0
    assert cart.total_weight() == 0


def test_cart_totals(apple, book):
    cart = Cart()
    cart.add_item(apple)
    cart.add_item(book)

    assert cart.total_price() == pytest.approx(1250.0)
    assert cart.total_weight() == pytest.approx(0.7)


@pytest.mark.parametrize(("index", "removed"), [(0, True), (1, True), (2, False), (-1, False)])
def test_cart_remove_item_by_index(apple, book, index, removed):
    cart = Cart()
    cart.add_item(apple)
    cart.add_item(book)

    assert cart.remove_item(index) is removed
    assert len(cart) == (1 if removed else 2)


def test_cart_clear(apple):
    cart = Cart()
    cart.add_item(apple)

    cart.clear()

    assert len(cart) == 0


def test_cart_display_empty(capsys):
    Cart().display()

    assert "Корзина пуста" in capsys.readouterr().out


def test_cart_display_shows_totals(apple, capsys):
    cart = Cart()
    cart.add_item(apple)

    cart.display()

    out = capsys.readouterr().out
    assert "Яблоко" in out
    assert "Итого: 50.00 руб." in out
