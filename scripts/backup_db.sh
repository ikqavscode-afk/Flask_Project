#!/usr/bin/env bash
# Зашифрованная копия базы PostgreSQL и проверка, что из неё можно восстановить данные.
#
# Использование:
#   BACKUP_DATABASE_URL=<адрес базы> BACKUP_PASSPHRASE=<пароль> \
#   [RESTORE_CHECK_URL=<адрес пустой временной базы>] \
#   scripts/backup_db.sh <папка_для_копии>
#
# Дамп шифруется «на лету» (AES-256, PBKDF2): открытый файл с данными на диск не попадает.
# Если задан RESTORE_CHECK_URL, копия расшифровывается и восстанавливается во временную базу,
# а число строк в каждой таблице сравнивается с исходной базой.
# Код выхода 0: копия создана и проверена; иначе 1.
set -euo pipefail

out_dir="${1:?Укажите папку для копии}"
: "${BACKUP_DATABASE_URL:?Задайте адрес базы в переменной BACKUP_DATABASE_URL}"
: "${BACKUP_PASSPHRASE:?Задайте пароль копии в переменной BACKUP_PASSPHRASE}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$out_dir"
file="$out_dir/diary-$(date -u +%Y%m%dT%H%M%SZ).dump.enc"

echo "Создаю копию…"
pg_dump -Fc --no-owner --no-privileges "$BACKUP_DATABASE_URL" \
  | openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt -pass env:BACKUP_PASSPHRASE -out "$file"

size="$(wc -c < "$file" | tr -d ' ')"
if [ "$size" -lt 100 ]; then
  echo "ОШИБКА: файл копии подозрительно мал ($size байт)" >&2
  exit 1
fi
echo "Копия создана: $file ($size байт, зашифрована)"

if [ -z "${RESTORE_CHECK_URL:-}" ]; then
  echo "ПРЕДУПРЕЖДЕНИЕ: проверка восстановления не выполнялась (не задан RESTORE_CHECK_URL)"
  exit 0
fi

echo "Проверяю восстановление во временную базу…"
"$script_dir/restore_db.sh" "$file" "$RESTORE_CHECK_URL" >/dev/null

list_tables() {
  psql "$1" -Atc "select tablename from pg_tables where schemaname = 'public' order by 1"
}
count_rows() {
  psql "$1" -Atc "select count(*) from \"$2\""
}

source_tables="$(list_tables "$BACKUP_DATABASE_URL")"
restored_tables="$(list_tables "$RESTORE_CHECK_URL")"
if [ "$source_tables" != "$restored_tables" ]; then
  echo "ОШИБКА: наборы таблиц различаются между исходной базой и восстановленной копией" >&2
  exit 1
fi

for table in $source_tables; do
  source_count="$(count_rows "$BACKUP_DATABASE_URL" "$table")"
  restored_count="$(count_rows "$RESTORE_CHECK_URL" "$table")"
  echo "  $table: в базе $source_count, в копии $restored_count"
  if [ "$restored_count" -eq 0 ] && [ "$source_count" -gt 0 ]; then
    echo "ОШИБКА: таблица $table пуста в копии, хотя в базе есть данные" >&2
    exit 1
  fi
done

echo "Проверка восстановления пройдена: $file"
