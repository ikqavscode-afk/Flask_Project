import random
from itertools import combinations

import pytest

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

# ---------- Рюкзак ----------


@pytest.mark.parametrize(
    ("capacity", "weights", "values", "expected"),
    [
        (5, [2, 3, 4, 5], [3, 4, 5, 6], 7),
        (50, [10, 20, 30], [60, 100, 120], 220),
        (0, [1, 2], [10, 20], 0),
        (10, [], [], 0),
        (3, [5, 6], [10, 20], 0),
    ],
)
def test_knapsack_known_values(capacity, weights, values, expected):
    assert knapsack(capacity, weights, values) == expected
    assert knapsack_with_items(capacity, weights, values)[0] == expected


def test_knapsack_items_are_valid():
    best, items = knapsack_with_items(50, [10, 20, 30], [60, 100, 120])

    assert items == [1, 2]
    assert sum([10, 20, 30][i] for i in items) <= 50
    assert sum([60, 100, 120][i] for i in items) == best


def test_knapsack_matches_brute_force_on_random_inputs():
    rng = random.Random(42)
    for _ in range(50):
        n = rng.randint(0, 8)
        weights = [rng.randint(1, 10) for _ in range(n)]
        values = [rng.randint(1, 20) for _ in range(n)]
        capacity = rng.randint(0, 25)

        brute = max(
            (
                sum(values[i] for i in subset)
                for r in range(n + 1)
                for subset in combinations(range(n), r)
                if sum(weights[i] for i in subset) <= capacity
            ),
            default=0,
        )

        assert knapsack(capacity, weights, values) == brute
        best, items = knapsack_with_items(capacity, weights, values)
        assert best == brute
        assert sum(weights[i] for i in items) <= capacity
        assert sum(values[i] for i in items) == best


def test_knapsack_validation():
    with pytest.raises(ValueError, match="одной длины"):
        knapsack(5, [1, 2], [1])
    with pytest.raises(ValueError, match="capacity не может быть отрицательной"):
        knapsack(-1, [1], [1])


# ---------- LCS ----------


@pytest.mark.parametrize(
    ("s1", "s2", "length", "sequence"),
    [
        ("ABCDGH", "AEDFHR", 3, "ADH"),
        ("AGGTAB", "GXTXAYB", 4, "GTAB"),
        ("", "abc", 0, ""),
        ("abc", "", 0, ""),
        ("abc", "abc", 3, "abc"),
        ("abc", "def", 0, ""),
    ],
)
def test_lcs_known_values(s1, s2, length, sequence):
    assert lcs_length(s1, s2) == length
    assert lcs(s1, s2) == sequence


def is_subsequence(small, big):
    it = iter(big)
    return all(ch in it for ch in small)


def test_lcs_result_is_common_subsequence_of_right_length():
    rng = random.Random(7)
    for _ in range(50):
        s1 = "".join(rng.choice("abc") for _ in range(rng.randint(0, 10)))
        s2 = "".join(rng.choice("abc") for _ in range(rng.randint(0, 10)))

        result = lcs(s1, s2)

        assert len(result) == lcs_length(s1, s2)
        assert is_subsequence(result, s1)
        assert is_subsequence(result, s2)


# ---------- Разбиения числа ----------


@pytest.mark.parametrize(
    ("n", "expected"),
    [(0, 1), (1, 1), (2, 2), (3, 3), (4, 5), (5, 7), (6, 11), (10, 42), (50, 204226)],
)
def test_count_partition(n, expected):
    assert count_partition(n) == expected


def test_count_partition_negative():
    with pytest.raises(ValueError, match="не может быть отрицательным"):
        count_partition(-1)


# ---------- Флойд–Уоршелл ----------

GRAPH = [
    [0, 5, INF, 10],
    [INF, 0, 3, INF],
    [INF, INF, 0, 1],
    [INF, INF, INF, 0],
]


def test_floyd_warshall_distances():
    dist = floyd_warshall(GRAPH)

    assert dist[0] == [0, 5, 8, 9]
    assert dist[1] == [INF, 0, 3, 4]
    assert dist[2] == [INF, INF, 0, 1]
    assert dist[3] == [INF, INF, INF, 0]


def test_floyd_warshall_does_not_modify_input():
    before = [row[:] for row in GRAPH]

    floyd_warshall(GRAPH)

    assert before == GRAPH


def test_restore_path():
    _, nxt = floyd_warshall_paths(GRAPH)

    assert restore_path(nxt, 0, 3) == [0, 1, 2, 3]
    assert restore_path(nxt, 1, 3) == [1, 2, 3]
    assert restore_path(nxt, 2, 2) == [2]
    assert restore_path(nxt, 3, 0) == []


def test_floyd_warshall_finds_shorter_indirect_route():
    graph = [[0, 1, 10], [INF, 0, 1], [INF, INF, 0]]

    dist, nxt = floyd_warshall_paths(graph)

    assert dist[0][2] == 2
    assert restore_path(nxt, 0, 2) == [0, 1, 2]


# ---------- Размен монет ----------


@pytest.mark.parametrize(
    ("coins", "amount", "expected"),
    [
        ([1, 2, 5], 11, 3),
        ([2], 3, -1),
        ([1], 0, 0),
        ([], 5, -1),
        ([3, 7], 7, 1),
        ([2, 5, 10], 6, 3),
    ],
)
def test_min_coins(coins, amount, expected):
    assert min_coins(coins, amount) == expected


@pytest.mark.parametrize(
    ("coins", "amount", "expected"),
    [
        ([1, 2, 5], 5, 4),
        ([2], 3, 0),
        ([1, 2, 3], 0, 1),
        ([], 0, 1),
        ([], 5, 0),
        ([2, 5, 3, 6], 10, 5),
    ],
)
def test_count_coin_ways(coins, amount, expected):
    assert count_coin_ways(coins, amount) == expected


def test_count_coin_ways_matches_partitions():
    """Разбиения n — это размен монетами 1..n."""
    for n in range(0, 15):
        assert count_coin_ways(list(range(1, n + 1)), n) == count_partition(n)


def test_count_coin_ways_ignores_non_positive_coins():
    assert count_coin_ways([0, -3, 2], 4) == 1


def test_coins_negative_amount():
    with pytest.raises(ValueError, match="amount не может быть отрицательной"):
        min_coins([1], -1)
    with pytest.raises(ValueError, match="amount не может быть отрицательной"):
        count_coin_ways([1], -1)


# ---------- Редакционное расстояние ----------


@pytest.mark.parametrize(
    ("s1", "s2", "expected"),
    [
        ("kitten", "sitting", 3),
        ("flaw", "lawn", 2),
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("same", "same", 0),
        ("a", "b", 1),
    ],
)
def test_edit_distance(s1, s2, expected):
    assert edit_distance(s1, s2) == expected


def test_edit_distance_is_symmetric_and_bounded():
    rng = random.Random(3)
    for _ in range(50):
        a = "".join(rng.choice("abc") for _ in range(rng.randint(0, 8)))
        b = "".join(rng.choice("abc") for _ in range(rng.randint(0, 8)))

        assert edit_distance(a, b) == edit_distance(b, a)
        assert edit_distance(a, b) <= max(len(a), len(b))
