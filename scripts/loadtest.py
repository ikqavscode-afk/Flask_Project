"""Простая нагрузочная проверка по HTTP (только стандартная библиотека).

Пример:
    python scripts/loadtest.py http://127.0.0.1:8000 --paths /health /home --users 20 --seconds 10

Показывает число запросов, запросов в секунду, ошибки по типам и задержки (p50, p95, p99).
Запускайте против тестового сервера (staging), а не против боевого.

Ограничение: если сервер закрывает соединение после каждого ответа (gunicorn с синхронными
процессами), каждый запрос занимает временный порт клиента, и на локальной машине они быстро
заканчиваются (ошибка «Can't assign requested address», errno 49 на macOS). Поэтому скорость
ограничена параметром --rate, а между адресами делается пауза --pause.
"""

import argparse
import collections
import http.client
import statistics
import threading
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

OK_STATUSES = range(200, 400)
TIMEOUT_SECONDS = 10


@dataclass
class Target:
    scheme: str
    host: str
    port: int
    path: str
    interval: float = 0.0  # пауза между запросами одного пользователя, с

    def connect(self):
        connection_class = (
            http.client.HTTPSConnection if self.scheme == "https" else http.client.HTTPConnection
        )
        return connection_class(self.host, self.port, timeout=TIMEOUT_SECONDS)


def make_target(base_url, path, interval=0.0):
    parts = urlsplit(base_url)
    port = parts.port or (443 if parts.scheme == "https" else 80)
    return Target(parts.scheme, parts.hostname, port, path, interval)


def worker(target, stop_at, results):
    """Шлёт запросы по одному соединению до окончания времени; ошибки записывает по типам."""
    connection = target.connect()
    next_start = time.monotonic()
    while time.monotonic() < stop_at:
        if target.interval:
            next_start += target.interval
            time.sleep(max(0.0, next_start - time.monotonic()))
        started = time.perf_counter()
        kind = None
        try:
            connection.request("GET", target.path)
            response = connection.getresponse()
            response.read()
            if response.status not in OK_STATUSES:
                kind = f"HTTP {response.status}"
        except (OSError, http.client.HTTPException) as error:
            kind = type(error).__name__
            connection.close()
            connection = target.connect()
        results.append((time.perf_counter() - started, kind))
    connection.close()


def percentile(sorted_values, fraction):
    return sorted_values[min(len(sorted_values) - 1, int(len(sorted_values) * fraction))]


def run(target, users, seconds):
    results = []
    stop_at = time.monotonic() + seconds
    threads = [
        threading.Thread(target=worker, args=(target, stop_at, results)) for _ in range(users)
    ]
    started = time.monotonic()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    elapsed = time.monotonic() - started

    latencies = sorted(duration * 1000 for duration, _ in results)
    error_kinds = collections.Counter(kind for _, kind in results if kind)
    return {
        "path": target.path,
        "requests": len(results),
        "rps": len(results) / elapsed,
        "errors": sum(error_kinds.values()),
        "error_kinds": dict(error_kinds),
        "p50": statistics.median(latencies) if latencies else 0,
        "p95": percentile(latencies, 0.95) if latencies else 0,
        "p99": percentile(latencies, 0.99) if latencies else 0,
    }


def format_row(r):
    return (
        f"{r['path']:<24}{r['requests']:>10}{r['rps']:>9.0f}{r['errors']:>8}"
        f"{r['p50']:>10.1f}{r['p95']:>10.1f}{r['p99']:>10.1f}"
    )


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("base_url")
    parser.add_argument("--paths", nargs="+", default=["/health"])
    parser.add_argument("--users", type=int, default=20, help="число одновременных пользователей")
    parser.add_argument("--seconds", type=int, default=10, help="длительность на каждый адрес")
    parser.add_argument(
        "--rate",
        type=int,
        default=0,
        help="предельное число запросов в секунду (0 = без ограничения)",
    )
    parser.add_argument(
        "--pause", type=int, default=0, help="пауза между адресами, с (даёт освободиться портам)"
    )
    args = parser.parse_args()

    header = (
        f"{'адрес':<24}{'запросов':>10}{'запр/с':>9}{'ошибок':>8}"
        f"{'p50, мс':>10}{'p95, мс':>10}{'p99, мс':>10}"
    )
    print(header)
    interval = args.users / args.rate if args.rate else 0.0
    for number, path in enumerate(args.paths):
        if number and args.pause:
            time.sleep(args.pause)
        row = run(make_target(args.base_url, path, interval), args.users, args.seconds)
        print(format_row(row))
        if row["error_kinds"]:
            print(f"  ошибки по типам: {row['error_kinds']}")


if __name__ == "__main__":
    main()
