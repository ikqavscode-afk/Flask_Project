"""Редакционное расстояние (расстояние Левенштейна)."""


def edit_distance(s1, s2):
    """Минимальное число вставок, удалений и замен символа, чтобы получить s2 из s1.

    dp[i][j] — расстояние между s1[:i] и s2[:j]. Хранится только две строки
    таблицы.

    Время O(m * n), память O(min(m, n)).
    """
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    previous = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1, start=1):
        current = [i]
        for j, c2 in enumerate(s2, start=1):
            current.append(
                min(
                    previous[j] + 1,  # удаление
                    current[j - 1] + 1,  # вставка
                    previous[j - 1] + (c1 != c2),  # замена
                )
            )
        previous = current
    return previous[-1]
