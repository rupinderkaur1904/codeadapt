#!/usr/bin/env bash
# Restore a CodeAdapt dump into a NEW, empty database (M3.5). Never touches an existing
# database: switching the application to the restored copy is a separate, deliberate
# step (docs/deployment/backup-and-restore.md).
#
#   PGHOST=... PGUSER=codeadapt_owner deploy/backup/pg-restore.sh <dump> <new-database>
#
# Checks the dump's SHA-256 first when a .sha256 file sits next to it.
set -euo pipefail

dump=${1:?usage: pg-restore.sh <dump-file> <new-database-name>}
target=${2:?usage: pg-restore.sh <dump-file> <new-database-name>}
[[ "$target" =~ ^[a-z_][a-z0-9_]{0,62}$ ]] || { echo "unsafe database name: $target" >&2; exit 2; }

if [[ -f "$dump.sha256" ]]; then
  (cd "$(dirname "$dump")" && sha256sum --check --quiet "$(basename "$dump").sha256")
  echo "checksum ok"
fi

exists=$(psql --dbname=postgres --tuples-only --no-align \
  --command="SELECT 1 FROM pg_database WHERE datname = '$target'")
if [[ "$exists" == 1 ]]; then
  echo "database $target already exists; refusing to restore over it" >&2
  exit 3
fi

createdb "$target"
pg_restore --no-owner --no-privileges --exit-on-error --single-transaction \
  --dbname="$target" "$dump"
revision=$(psql --dbname="$target" --tuples-only --no-align \
  --command="SELECT version_num FROM alembic_version")
echo "restored into $target (schema revision $revision)"
echo "next: compare 'codeadapt-admin db-fingerprint' of the source and of $target,"
echo "      then run 'codeadapt-admin db-setup' against $target to re-apply role grants."
