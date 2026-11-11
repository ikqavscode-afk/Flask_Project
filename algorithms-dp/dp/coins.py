"""Задачи о размене монет."""


def min_coins(coins, amount):
    """Наименьшее число монет для суммы amount или -1, если собрать нельзя.

    Монет каждого номинала неограниченно. dp[a] — минимум монет для суммы a.

    Время O(amount * len(coins)), память O(amount).
    """
    if amount < 0:
        raise ValueError("amount не может быть отрицательной")
    inf = amount + 1
    dp = [0] + [inf] * amount
    for a in range(1, amount + 1):
        for coin in coins:
            if 0 < coin <= a:
                dp[a] = min(dp[a], dp[a - coin] + 1)
    return dp[amount] if dp[amount] != inf else -1


def count_coin_ways(coins, amount):
    """Число различных наборов монет, дающих сумму amount.

    Наборы считаются без учёта порядка: 1+2 и 2+1 — один способ.
    Перебор номиналов во внешнем цикле гарантирует, что порядок не учитывается.

    Время O(amount * len(coins)), память O(amount).
    """
    if amount < 0:
        raise ValueError("amount не может быть отрицательной")
    dp = [1] + [0] * amount
    for coin in coins:
        if coin <= 0:
            continue
        for a in range(coin, amount + 1):
            dp[a] += dp[a - coin]
    return dp[amount]
