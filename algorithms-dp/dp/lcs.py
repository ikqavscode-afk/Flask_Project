"""Наибольшая общая подпоследовательность (LCS)."""


def _table(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp


def lcs_length(s1, s2):
    """Длина наибольшей общей подпоследовательности.

    Идея: dp[i][j] — длина LCS префиксов s1[:i] и s2[:j]. При совпадении
    символов берём диагональ + 1, иначе максимум из соседних ячеек.

    Время O(m * n), память O(m * n).
    """
    return _table(s1, s2)[len(s1)][len(s2)]


def lcs(s1, s2):
    """Сама наибольшая общая подпоследовательность (одна из возможных).

    Строится обратным ходом по таблице из `lcs_length`.

    Время O(m * n), память O(m * n).
    """
    dp = _table(s1, s2)
    i, j = len(s1), len(s2)
    result = []
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            result.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return "".join(reversed(result))
