import builtins

from shop.cli import ShopApp


def feed_inputs(monkeypatch, answers):
    iterator = iter(answers)
    monkeypatch.setattr(builtins, "input", lambda _="": next(iterator))


def test_app_starts_with_filled_catalog():
    app = ShopApp()

    assert len(app.catalog) == 7
    assert len(app.cart) == 0


def test_add_to_cart_valid_number(monkeypatch):
    app = ShopApp()
    feed_inputs(monkeypatch, ["1"])

    app.add_to_cart()

    assert len(app.cart) == 1
    assert app.cart.get_items()[0].name == "Ноутбук"


def test_add_to_cart_copies_product(monkeypatch):
    app = ShopApp()
    feed_inputs(monkeypatch, ["1"])

    app.add_to_cart()

    assert app.cart.get_items()[0] is not app.catalog.get_list()[0]


def test_add_to_cart_invalid_number(monkeypatch, capsys):
    app = ShopApp()
    feed_inputs(monkeypatch, ["999"])

    app.add_to_cart()

    assert len(app.cart) == 0
    assert "Неверный номер" in capsys.readouterr().out


def test_add_to_cart_not_a_number(monkeypatch, capsys):
    app = ShopApp()
    feed_inputs(monkeypatch, ["abc"])

    app.add_to_cart()

    assert len(app.cart) == 0
    assert "Введите число" in capsys.readouterr().out


def test_remove_from_cart(monkeypatch):
    app = ShopApp()
    feed_inputs(monkeypatch, ["2", "1"])
    app.add_to_cart()

    app.remove_from_cart()

    assert len(app.cart) == 0


def test_sort_cart_by_price_descending(monkeypatch):
    app = ShopApp()
    # добавляем Хлеб (80), Ноутбук (75000), Мышь (1500)
    feed_inputs(monkeypatch, ["4", "1", "2"])
    app.add_to_cart()
    app.add_to_cart()
    app.add_to_cart()

    # критерий 1 (цена), алгоритм 4 (слиянием), порядок 2 (убывание), без шагов
    feed_inputs(monkeypatch, ["1", "4", "2", "n"])
    app.sort_cart()

    prices = [item.price for item in app.cart.get_items()]
    assert prices == sorted(prices, reverse=True)


def test_sort_empty_cart_does_nothing(capsys):
    app = ShopApp()

    app.sort_cart()

    assert "нечего сортировать" in capsys.readouterr().out


def test_run_exits_on_zero(monkeypatch, capsys):
    feed_inputs(monkeypatch, ["0"])

    ShopApp().run()

    assert "До свидания" in capsys.readouterr().out


def test_run_rejects_unknown_choice(monkeypatch, capsys):
    feed_inputs(monkeypatch, ["42", "0"])

    ShopApp().run()

    assert "Неверный ввод" in capsys.readouterr().out
