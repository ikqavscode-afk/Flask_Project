"""Корзина покупателя."""


class Cart:
    def __init__(self):
        self.items = []

    def add_item(self, product):
        self.items.append(product)

    def remove_item(self, index):
        if 0 <= index < len(self.items):
            del self.items[index]
            return True
        return False

    def clear(self):
        self.items.clear()

    def total_price(self):
        return sum(item.price for item in self.items)

    def total_weight(self):
        return sum(item.weight for item in self.items)

    def display(self):
        if not self.items:
            print("Корзина пуста.")
            return
        print("\n======================= СОДЕРЖИМОЕ КОРЗИНЫ ======================")
        print("=================================================================")
        for i, item in enumerate(self.items):
            print(f"{i + 1}. {item}")
        print("-----------------------------------------------------------------")
        print(f"Итого: {self.total_price():.2f} руб. | Вес: {self.total_weight():.2f} кг")
        print("=================================================================\n")

    def get_items(self):
        return self.items

    def __len__(self):
        return len(self.items)
