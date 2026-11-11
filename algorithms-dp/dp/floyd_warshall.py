"""Алгоритм Флойда–Уоршелла: кратчайшие пути между всеми парами вершин."""

INF = float("inf")


def floyd_warshall(adj_matrix):
    """Матрица кратчайших расстояний между всеми парами вершин.

    adj_matrix[i][j] — вес ребра i -> j (INF, если ребра нет, 0 на диагонали).
    Исходная матрица не изменяется.

    Время O(V^3), память O(V^2).
    """
    return floyd_warshall_paths(adj_matrix)[0]


def floyd_warshall_paths(adj_matrix):
    """Возвращает (расстояния, следующие вершины) для восстановления путей.

    nxt[i][j] — вершина, в которую нужно пойти из i первой, чтобы добраться
    до j кратчайшим путём (None, если пути нет). Сам путь собирает
    `restore_path`.

    Время O(V^3), память O(V^2).
    """
    n = len(adj_matrix)
    dist = [row[:] for row in adj_matrix]
    nxt = [
        [j if i != j and dist[i][j] != INF else None for j in range(n)]
        for i in range(n)
    ]
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    nxt[i][j] = nxt[i][k]
    return dist, nxt


def restore_path(nxt, start, end):
    """Кратчайший путь start -> end списком вершин ([] если пути нет)."""
    if start == end:
        return [start]
    if nxt[start][end] is None:
        return []
    path = [start]
    while start != end:
        start = nxt[start][end]
        path.append(start)
    return path
