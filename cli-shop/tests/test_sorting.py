import pytest

from shop import sorting
from shop.models import Product
from shop.sorting import CRITERIA, SortAlgorithms, precedes

# Алгоритмы берутся из реестра: новый алгоритм сразу попадает во все проверки ниже
ALGORITHMS = [function for _, function in sorting.ALGORITHMS]
ALGORITHM_IDS = [function.__name__ for function in ALGORITHMS]

PRODUCTS = [
    Product("Ноутбук", "Электроника", 75000, 2.5),
    Product("Мышь", "Электроника", 1500, 0.2),
    Product("Хлеб", "Продукты", 80, 0.4),
    Product("Книга", "Книги", 1200, 0.5),
    Product("Молоко", "Продукты", 120, 1.0),
]


@pytest.mark.parametrize("sort_func", ALGORITHMS, ids=ALGORITHM_IDS)
@pytest.mark.parametrize("criteria", ["price", "weight", "category", "name"])
@pytest.mark.parametrize("reverse", [False, True])
def test_sort_matches_builtin_sorted(sort_func, criteria, reverse):
    key = SortAlgorithms._key_func(criteria)

    result = sort_func(PRODUCTS, key, reverse)

    assert [key(p) for p in result] == [key(p) for p in sorted(PRODUCTS, key=key, reverse=reverse)]


@pytest.mark.parametrize("sort_func", ALGORITHMS, ids=ALGORITHM_IDS)
def test_sort_does_not_modify_input(sort_func):
    original = list(PRODUCTS)

    sort_func(PRODUCTS, SortAlgorithms._key_func("price"))

    assert original == PRODUCTS


@pytest.mark.parametrize("sort_func", ALGORITHMS, ids=ALGORITHM_IDS)
def test_sort_empty_and_single(sort_func):
    key = SortAlgorithms._key_func("price")

    assert sort_func([], key) == []
    assert sort_func(PRODUCTS[:1], key) == PRODUCTS[:1]


@pytest.mark.parametrize("sort_func", ALGORITHMS, ids=ALGORITHM_IDS)
def test_sort_keeps_all_items(sort_func):
    result = sort_func(PRODUCTS, SortAlgorithms._key_func("weight"))

    assert sorted(p.name for p in result) == sorted(p.name for p in PRODUCTS)


@pytest.mark.parametrize("sort_func", ALGORITHMS, ids=ALGORITHM_IDS)
def test_show_steps_prints_progress(sort_func, capsys):
    sort_func(PRODUCTS, SortAlgorithms._key_func("price"), show_steps=True)

    assert capsys.readouterr().out.strip() != ""


def test_unknown_criteria_falls_back_to_name():
    key = SortAlgorithms._key_func("что-то другое")

    assert key(PRODUCTS[0]) == "ноутбук"


# ---------- Реестры и общая функция сравнения ----------


def test_registry_lists_every_algorithm_once():
    labels = [label for label, _ in sorting.ALGORITHMS]

    assert len(labels) == len(set(labels))
    assert all(callable(function) for _, function in sorting.ALGORITHMS)
    assert len(ALGORITHMS) >= 4


def test_every_criterion_has_a_working_key():
    names = [name for _, name, _ in CRITERIA]

    assert len(names) == len(set(names))
    for name in names:
        key = SortAlgorithms._key_func(name)
        assert all(key(product) is not None for product in PRODUCTS)


@pytest.mark.parametrize(
    ("first", "second", "reverse", "expected"),
    [
        (1, 2, False, True),
        (2, 1, False, False),
        (1, 1, False, False),
        (2, 1, True, True),
        (1, 2, True, False),
        (1, 1, True, False),
    ],
)
def test_precedes_is_strict_and_respects_direction(first, second, reverse, expected):
    assert precedes(first, second, reverse) is expected
