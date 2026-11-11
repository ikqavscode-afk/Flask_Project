"""Алгоритмы сортировки: пузырьком, вставками, быстрая, слиянием."""


class SortAlgorithms:
    @staticmethod
    def _key_func(criteria):
        """Возвращает функцию ключа для сравнения"""
        if criteria == "price":
            return lambda p: p.price
        elif criteria == "weight":
            return lambda p: p.weight
        elif criteria == "category":
            return lambda p: p.category.lower()
        else:
            return lambda p: p.name.lower()

    # ---------- Пузырьковая ----------
    @staticmethod
    def bubble_sort(items, key_func, reverse=False, show_steps=False):
        arr = items[:]
        n = len(arr)
        for i in range(n):
            swapped = False
            for j in range(0, n - i - 1):
                a = key_func(arr[j])
                b = key_func(arr[j + 1])
                if (a > b) if not reverse else (a < b):
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    swapped = True
            if show_steps:
                print(f"  Шаг {i + 1}: {[p.name for p in arr]}")
            if not swapped:
                break
        return arr

    # ---------- Вставками ----------
    @staticmethod
    def insertion_sort(items, key_func, reverse=False, show_steps=False):
        arr = items[:]
        for i in range(1, len(arr)):
            key = arr[i]
            j = i - 1
            while j >= 0 and (
                (key_func(key) < key_func(arr[j]))
                if not reverse
                else (key_func(key) > key_func(arr[j]))
            ):
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key
            if show_steps:
                print(f"  Шаг {i}: {[p.name for p in arr]}")
        return arr

    # ---------- Быстрая ----------
    @staticmethod
    def quick_sort(items, key_func, reverse=False, show_steps=False):
        if len(items) <= 1:
            return items[:]
        pivot = items[0]
        left = []
        right = []
        for item in items[1:]:
            if (
                (key_func(item) < key_func(pivot))
                if not reverse
                else (key_func(item) > key_func(pivot))
            ):
                left.append(item)
            else:
                right.append(item)
        left_sorted = SortAlgorithms.quick_sort(left, key_func, reverse, show_steps)
        right_sorted = SortAlgorithms.quick_sort(right, key_func, reverse, show_steps)
        result = [*left_sorted, pivot, *right_sorted]
        if show_steps:
            print(f"  Разбиение: {[p.name for p in result]}")
        return result

    # ---------- Слиянием ----------
    @staticmethod
    def merge_sort(items, key_func, reverse=False, show_steps=False):
        if len(items) <= 1:
            return items[:]
        mid = len(items) // 2
        left = SortAlgorithms.merge_sort(items[:mid], key_func, reverse, show_steps)
        right = SortAlgorithms.merge_sort(items[mid:], key_func, reverse, show_steps)
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if (
                (key_func(left[i]) < key_func(right[j]))
                if not reverse
                else (key_func(left[i]) > key_func(right[j]))
            ):
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        if show_steps:
            print(f"  Слияние: {[p.name for p in result]}")
        return result
