#!/usr/bin/env bash
# PostgreSQL backup for CodeAdapt (M3.5). Writes one custom-format dump plus a SHA-256
# file, then (optionally) prunes dumps older than BACKUP_RETENTION_DAYS in BACKUP_DIR.
#
# Connection comes from the standard libpq variables: PGHOST, PGPORT, PGUSER, PGPASSWORD
# (or ~/.pgpass), PGDATABASE. Run as the schema owner. Example on the App VM:
#
#   BACKUP_DIR=/var/backups/codeadapt PGHOST=127.0.0.1 PGUSER=codeadapt_owner \
#     PGDATABASE=codeadapt deploy/backup/pg-backup.sh
#
# A successful backup is NOT proof of recoverability: restore it (pg-restore.sh) on a
# schedule. Dumps contain learner data: keep BACKUP_DIR mode 700 and copy dumps off the
# host to storage with the same access rules (docs/pilot/data-governance.md).
set -euo pipefail
umask 077

: "${BACKUP_DIR:?set BACKUP_DIR}"
: "${PGDATABASE:?set PGDATABASE}"
mkdir -p "$BACKUP_DIR"

stamp=$(date -u +%Y%m%dT%H%M%SZ)
file="$BACKUP_DIR/codeadapt-$PGDATABASE-$stamp.dump"
tmp="$file.partial"

pg_dump --format=custom --no-owner --no-privileges --file="$tmp"
# The dump must be readable by pg_restore before it counts.
pg_restore --list "$tmp" > /dev/null
mv "$tmp" "$file"
(cd "$BACKUP_DIR" && sha256sum "$(basename "$file")" > "$(basename "$file").sha256")
echo "backup: $file ($(du -h "$file" | cut -f1))"

if [[ -n "${BACKUP_RETENTION_DAYS:-}" ]]; then
  # Only this script's own files, only in BACKUP_DIR, never recursive.
  find "$BACKUP_DIR" -maxdepth 1 -type f \
    \( -name 'codeadapt-*.dump' -o -name 'codeadapt-*.dump.sha256' \) \
    -mtime "+$BACKUP_RETENTION_DAYS" -print -delete
fi
