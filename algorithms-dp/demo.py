"""Демонстрация: python demo.py"""

from dp import (
    INF,
    count_coin_ways,
    count_partition,
    edit_distance,
    floyd_warshall,
    floyd_warshall_paths,
    knapsack,
    knapsack_with_items,
    lcs,
    lcs_length,
    min_coins,
    restore_path,
)


def title(text):
    print("*" * 50)
    print(text)
    print("*" * 50)


def show_matrix(matrix):
    for row in matrix:
        print([x if x != INF else "∞" for x in row])


title("01 Рюкзак")
weights = [2, 3, 4, 5]
values = [3, 4, 5, 6]
capacity = 5
best, items = knapsack_with_items(capacity, weights, values)
print(f"Веса: {weights}")
print(f"Стоимость: {values}")
print(f"Вместимость: {capacity}")
print(f"Максимальная стоимость: {knapsack(capacity, weights, values)}")
print(f"Взятые предметы (индексы): {items}")

title("02 LCS")
for s1, s2 in [("ABCDGH", "AEDFHR"), ("AGGTAB", "GXTXAYB")]:
    print(f"Стр1: {s1}")
    print(f"Стр2: {s2}")
    print(f"LCS: {lcs_length(s1, s2)} (подпоследовательность: {lcs(s1, s2)})")

title("03 Количество разбиений числа")
for n in [4, 5, 6, 10]:
    print(f"n = {n}: {count_partition(n)} разбиений")

title("04 Алгоритм Флойда–Уоршелла")
graph = [
    [0, 5, INF, 10],
    [INF, 0, 3, INF],
    [INF, INF, 0, 1],
    [INF, INF, INF, 0],
]
print("Исходная матрица")
show_matrix(graph)
print("Матрица кратчайших расстояний")
show_matrix(floyd_warshall(graph))
_, nxt = floyd_warshall_paths(graph)
print(f"Путь 0 -> 3: {restore_path(nxt, 0, 3)}")

title("05 Размен монет")
coins = [1, 2, 5]
print(f"Монеты: {coins}")
print(f"Минимум монет для 11: {min_coins(coins, 11)}")
print(f"Способов набрать 5: {count_coin_ways(coins, 5)}")
print(f"Минимум монет для 3 из [2]: {min_coins([2], 3)}")

title("06 Редакционное расстояние")
for a, b in [("kitten", "sitting"), ("flaw", "lawn")]:
    print(f"{a} -> {b}: {edit_distance(a, b)}")
