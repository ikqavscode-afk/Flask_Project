#!/usr/bin/env bash
# Восстановление зашифрованной копии базы (создана scripts/backup_db.sh) в указанную базу.
#
# Использование:
#   BACKUP_PASSPHRASE=<пароль_копии> scripts/restore_db.sh <файл.dump.enc> <адрес_целевой_базы>
#
# Целевая база должна быть ПУСТОЙ или тестовой: объекты с теми же именами будут пересозданы.
# Не направляйте скрипт на рабочую базу, не сверив содержимое копии (см. docs/deployment.md).
set -euo pipefail

file="${1:?Укажите файл копии (.dump.enc)}"
target_url="${2:?Укажите адрес целевой базы}"
: "${BACKUP_PASSPHRASE:?Задайте пароль копии в переменной BACKUP_PASSPHRASE}"

openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:BACKUP_PASSPHRASE -in "$file" \
  | pg_restore --no-owner --no-privileges --clean --if-exists -d "$target_url"
