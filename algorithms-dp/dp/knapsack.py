"""Задача о рюкзаке 0/1."""


def _check(capacity, weights, values):
    if len(weights) != len(values):
        raise ValueError("weights и values должны быть одной длины")
    if capacity < 0:
        raise ValueError("capacity не может быть отрицательной")


def knapsack(capacity, weights, values):
    """Максимальная стоимость предметов, помещающихся в рюкзак.

    Каждый предмет можно взять не более одного раза.
    Идея: dp[w] — лучшая стоимость при вместимости w. Вместимость
    перебирается от большей к меньшей, чтобы предмет не использовался дважды.

    Время O(n * capacity), память O(capacity).
    """
    _check(capacity, weights, values)
    dp = [0] * (capacity + 1)
    for weight, value in zip(weights, values, strict=True):
        for w in range(capacity, weight - 1, -1):
            dp[w] = max(dp[w], dp[w - weight] + value)
    return dp[capacity]


def knapsack_with_items(capacity, weights, values):
    """Возвращает (максимальная стоимость, индексы взятых предметов).

    Используется полная таблица dp[i][w] — лучшая стоимость для первых i
    предметов при вместимости w; ответ восстанавливается обратным ходом.

    Время O(n * capacity), память O(n * capacity).
    """
    _check(capacity, weights, values)
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        weight, value = weights[i - 1], values[i - 1]
        for w in range(capacity + 1):
            dp[i][w] = dp[i - 1][w]
            if w >= weight:
                dp[i][w] = max(dp[i][w], dp[i - 1][w - weight] + value)

    chosen = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            chosen.append(i - 1)
            w -= weights[i - 1]
    return dp[n][capacity], sorted(chosen)
