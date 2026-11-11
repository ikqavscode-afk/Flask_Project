"""Консольный интерфейс магазина."""
import copy
from pathlib import Path

from .cart import Cart
from .models import Catalog, Product
from .sorting import SortAlgorithms
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

    def show_catalog(self):
        print("\n======================== КАТАЛОГ ТОВАРОВ ========================")
        print("=================================================================")
        for i, p in enumerate(self.catalog.get_list()):
            print(f"{i+1}. {p}")
        print("=================================================================\n")

    def add_product_to_catalog(self):
        name = input("Название: ").strip()
        category = input("Категория: ").strip()
        if not name or not category:
            print("❌ Название и категория обязательны.")
            return
        try:
            price = float(input("Цена, руб.: ").replace(",", "."))
            weight = float(input("Вес, кг: ").replace(",", "."))
        except ValueError:
            print("❌ Цена и вес должны быть числами.")
            return
        if price < 0 or weight < 0:
            print("❌ Цена и вес не могут быть отрицательными.")
            return
        description = input("Описание (можно пропустить): ").strip()
        self.catalog.add_product(Product(name, category, price, weight, description))
        self._save_catalog()
        print("✅ Товар добавлен в каталог.")

    def remove_product_from_catalog(self):
        self.show_catalog()
        try:
            idx = int(input("Введите номер товара для удаления из каталога: ")) - 1
        except ValueError:
            print("❌ Введите число.")
            return
        if 0 <= idx < len(self.catalog):
            self.catalog.remove_product(idx)
            self._save_catalog()
            print("✅ Товар удалён из каталога.")
        else:
            print("❌ Неверный номер.")

    def add_to_cart(self):
        self.show_catalog()
        try:
            idx = int(input("Введите номер товара для добавления: ")) - 1
            if 0 <= idx < len(self.catalog):
                self.cart.add_item(copy.deepcopy(self.catalog.get_list()[idx]))
                print("✅ Товар добавлен в корзину.")
            else:
                print("❌ Неверный номер.")
        except ValueError:
            print("❌ Введите число.")

    def remove_from_cart(self):
        self.cart.display()
        if not self.cart.get_items():
            return
        try:
            idx = int(input("Введите номер товара для удаления: ")) - 1
            if self.cart.remove_item(idx):
                print("✅ Товар удалён.")
            else:
                print("❌ Неверный номер.")
        except ValueError:
            print("❌ Введите число.")

    def sort_cart(self):
        if not self.cart.get_items():
            print("Корзина пуста, нечего сортировать.")
            return

        print("\n--- Выбор сортировки ---")
        print("Критерии: 1 - цена, 2 - вес, 3 - категория")
        crit_choice = input("Ваш выбор (1-3): ")
        criteria_map = {"1": "price", "2": "weight", "3": "category"}
        criteria = criteria_map.get(crit_choice, "price")

        print("Алгоритмы: 1 - Пузырёк, 2 - Вставками, 3 - Быстрая, 4 - Слиянием")
        alg_choice = input("Ваш выбор (1-4): ")
        alg_map = {
            "1": SortAlgorithms.bubble_sort,
            "2": SortAlgorithms.insertion_sort,
            "3": SortAlgorithms.quick_sort,
            "4": SortAlgorithms.merge_sort,
        }
        sort_func = alg_map.get(alg_choice, SortAlgorithms.bubble_sort)

        order = input("Порядок: 1 - по возрастанию, 2 - по убыванию: ")
        reverse = (order == "2")

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

    def run(self):
        while True:
            print("\n" + "="*40)
            print("********** СИМУЛЯТОР МАГАЗИНА **********")
            print("="*40)
            print("1. Показать каталог")
            print("2. Добавить товар в корзину")
            print("3. Удалить товар из корзины")
            print("4. Показать корзину")
            print("5. Сортировать корзину")
            print("6. Итоговая стоимость")
            print("7. Добавить товар в каталог")
            print("8. Удалить товар из каталога")
            print("0. ВЫХОД")
            print("-" * 40)
            choice = input("ВЫБЕРЕТЕ ДЕЙСТВИЕ: ")

            if choice == "1":
                self.show_catalog()
            elif choice == "2":
                self.add_to_cart()
            elif choice == "3":
                self.remove_from_cart()
            elif choice == "4":
                self.cart.display()
            elif choice == "5":
                self.sort_cart()
            elif choice == "6":
                self.show_total()
            elif choice == "7":
                self.add_product_to_catalog()
            elif choice == "8":
                self.remove_product_from_catalog()
            elif choice == "0":
                print("До свидания!")
                break
            else:
                print("❌ Неверный ввод.")
