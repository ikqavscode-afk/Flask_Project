#!/usr/bin/env bash
# Проверка работоспособности сайта: GET <адрес>/health должен вернуть 200 и {"status":"ok"}.
#
# Использование: scripts/check_health.sh <адрес_без_слэша> [попыток=3] [пауза_секунд=20]
# Код выхода 0 — сайт работает, 1 — недоступен после всех попыток.
#
# Попыток несколько, потому что бесплатный сервис после простоя просыпается около минуты.
set -u

base_url="${1:?Укажите адрес сайта, например https://example.onrender.com}"
attempts="${2:-3}"
pause="${3:-20}"
timeout="${HEALTH_TIMEOUT:-90}"

body_file="$(mktemp)"

for attempt in $(seq 1 "$attempts"); do
  code="$(curl -s -o "$body_file" -w '%{http_code}' -m "$timeout" "${base_url%/}/health" || true)"
  if [ "$code" = "200" ] && grep -q '"status":"ok"' "$body_file"; then
    echo "OK: ${base_url%/}/health отвечает (попытка $attempt)"
    exit 0
  fi
  echo "Попытка $attempt из $attempts: код ${code:-нет ответа}"
  if [ "$attempt" -lt "$attempts" ]; then
    sleep "$pause"
  fi
done

echo "НЕДОСТУПЕН: ${base_url%/}/health не ответил корректно за $attempts попыток" >&2
exit 1
