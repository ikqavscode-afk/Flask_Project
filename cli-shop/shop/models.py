"""Товар и каталог."""


class Product:
    def __init__(self, name, category, price, weight, description=""):
        self.name = name
        self.category = category
        self.price = price
        self.weight = weight
        self.description = description

    def __repr__(self):
        return (
            f"{self.name:<18} | "
            f"{self.category:<12} | "
            f"{self.price:>10.2f} руб. | "
            f"{self.weight:>5.2f} кг"
    )

    def to_dict(self):
        return {
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "weight": self.weight,
            "description": self.description
        }


class Catalog:
    """Каталог товаров (хранилище)"""
    def __init__(self):
        self.products = []

    def add_product(self, product):
        self.products.append(product)

    def edit_product(self, index, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.products[index], key):
                setattr(self.products[index], key, value)

    def remove_product(self, index):
        del self.products[index]

    def get_list(self):
        return self.products

    def find_by_name(self, name):
        for p in self.products:
            if p.name.lower() == name.lower():
                return p
        return None

    def __len__(self):
        return len(self.products)
