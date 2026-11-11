"""Консольный интерфейс магазина."""

import copy
from pathlib import Path

from .cart import Cart
from .models import Catalog, Product
from .sorting import ALGORITHMS, CRITERIA, SortAlgorithms
from .storage import load_catalog, save_catalog

DEFAULT_CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "catalog.json"


class ShopApp:
    def __init__(self, catalog_path=None):
        self.catalog_path = Path(catalog_path or DEFAULT_CATALOG_PATH)
        self.cart = Cart()
        self.catalog = self._load_or_create_catalog()

    def _load_or_create_catalog(self):
        """Берём каталог из файла, а если его нет или он повреждён, начальный."""
        try:
            catalog = load_catalog(self.catalog_path)
        except ValueError:
            print("⚠️ Файл каталога повреждён, загружен стандартный каталог.")
            catalog = None
        if catalog is None:
            catalog = Catalog()
            self._fill_default_catalog(catalog)
        return catalog

    def _save_catalog(self):
        save_catalog(self.catalog, self.catalog_path)

    @staticmethod
    def _fill_default_catalog(catalog):
        """Наполняем каталог начальными товарами"""
        products = [
            Product("Ноутбук", "Электроника", 75000, 2.5, "Игровой ноутбук"),
            Product("Мышь", "Электроника", 1500, 0.2, "Беспроводная"),
            Product("Книга 'Python'", "Книги", 1200, 0.5, "Учебник"),
            Product("Хлеб", "Продукты", 80, 0.4, "Белый"),
            Product("Молоко", "Продукты", 120, 1.0, "3.2%"),
            Product("Футболка", "Одежда", 2000, 0.3, "Хлопок"),
            Product("Кроссовки", "Одежда", 5500, 0.8, "Беговые"),
        ]
        for p in products:
            catalog.add_product(p)

    @staticmethod
    def _ask_index(prompt, size):
        """Спрашивает номер (с 1) и возвращает индекс с 0 либо None, сообщив об ошибке."""
        try:
            idx = int(input(prompt)) - 1
        except ValueError:
            print("❌ Введите число.")
            return None
        if not 0 <= idx < size:
            print("❌ Неверный номер.")
            return None
        return idx

    def show_catalog(self):
        print("\n======================== КАТАЛОГ ТОВАРОВ ========================")
        print("=================================================================")
        for i, p in enumerate(self.catalog.get_list()):
            print(f"{i + 1}. {p}")
        print("=================================================================\n")

    @staticmethod
    def _read_product():
        """Запрашивает данные товара; при ошибке ввода печатает причину и возвращает None."""
        name = input("Название: ").strip()
        category = input("Категория: ").strip()
        if not name or not category:
            print("❌ Название и категория обязательны.")
            return None
        try:
            price = float(input("Цена, руб.: ").replace(",", "."))
            weight = float(input("Вес, кг: ").replace(",", "."))
        except ValueError:
            print("❌ Цена и вес должны быть числами.")
            return None
        if price < 0 or weight < 0:
            print("❌ Цена и вес не могут быть отрицательными.")
            return None
        description = input("Описание (можно пропустить): ").strip()
        return Product(name, category, price, weight, description)

    def add_product_to_catalog(self):
        product = self._read_product()
        if product is None:
            return
        self.catalog.add_product(product)
        self._save_catalog()
        print("✅ Товар добавлен в каталог.")

    def remove_product_from_catalog(self):
        self.show_catalog()
        idx = self._ask_index("Введите номер товара для удаления из каталога: ", len(self.catalog))
        if idx is None:
            return
        self.catalog.remove_product(idx)
        self._save_catalog()
        print("✅ Товар удалён из каталога.")

    def add_to_cart(self):
        self.show_catalog()
        idx = self._ask_index("Введите номер товара для добавления: ", len(self.catalog))
        if idx is None:
            return
        self.cart.add_item(copy.deepcopy(self.catalog.get_list()[idx]))
        print("✅ Товар добавлен в корзину.")

    def remove_from_cart(self):
        self.cart.display()
        if not self.cart.get_items():
            return
        idx = self._ask_index("Введите номер товара для удаления: ", len(self.cart))
        if idx is None:
            return
        self.cart.remove_item(idx)
        print("✅ Товар удалён.")

    @staticmethod
    def _choose(title, options):
        """Печатает «title: 1 - …, 2 - …» и возвращает выбранный вариант.

        Для неверного ввода берётся первый вариант (как и раньше).
        """
        labels = ", ".join(f"{number} - {label}" for number, (label, *_) in enumerate(options, 1))
        print(f"{title}: {labels}")
        choice = input(f"Ваш выбор (1-{len(options)}): ")
        numbers = {str(number): option for number, option in enumerate(options, 1)}
        return numbers.get(choice, options[0])

    def sort_cart(self):
        if not self.cart.get_items():
            print("Корзина пуста, нечего сортировать.")
            return

        print("\n--- Выбор сортировки ---")
        _, criteria, _ = self._choose("Критерии", CRITERIA)
        _, sort_func = self._choose("Алгоритмы", ALGORITHMS)

        order = input("Порядок: 1 - по возрастанию, 2 - по убыванию: ")
        reverse = order == "2"

        show_steps = input("Показывать шаги? (y/n): ").lower() == "y"

        key_func = SortAlgorithms._key_func(criteria)

        print("\n--- Сортировка ---")
        sorted_items = sort_func(self.cart.get_items(), key_func, reverse, show_steps)
        self.cart.items = sorted_items

        print("\n✅ Корзина отсортирована.")
        self.cart.display()

    def show_total(self):
        self.cart.display()
        print(f"💰 Общая стоимость: {self.cart.total_price():.2f} руб.")
        print(f"⚖️ Общий вес: {self.cart.total_weight():.2f} кг")

    def _menu(self):
        """Пункты главного меню: номер, подпись, действие (порядок задаёт отображение)."""
        return {
            "1": ("Показать каталог", self.show_catalog),
            "2": ("Добавить товар в корзину", self.add_to_cart),
            "3": ("Удалить товар из корзины", self.remove_from_cart),
            "4": ("Показать корзину", self.cart.display),
            "5": ("Сортировать корзину", self.sort_cart),
            "6": ("Итоговая стоимость", self.show_total),
            "7": ("Добавить товар в каталог", self.add_product_to_catalog),
            "8": ("Удалить товар из каталога", self.remove_product_from_catalog),
        }

    def run(self):
        menu = self._menu()
        while True:
            print("\n" + "=" * 40)
            print("********** СИМУЛЯТОР МАГАЗИНА **********")
            print("=" * 40)
            for number, (label, _) in menu.items():
                print(f"{number}. {label}")
            print("0. ВЫХОД")
            print("-" * 40)
            choice = input("ВЫБЕРЕТЕ ДЕЙСТВИЕ: ")

            if choice == "0":
                print("До свидания!")
                break
            if choice in menu:
                menu[choice][1]()
            else:
                print("❌ Неверный ввод.")
