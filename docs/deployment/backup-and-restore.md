# Backup and restore (M3.5)

Status: the scripts exist and an **actual restore** has been tested on disposable
PostgreSQL 16 databases, in the cloud container and in CI. They have **not** been run on a
deployment host, because none exists. A backup only counts once it has been restored.

## What is backed up

The PostgreSQL database holds everything:

- accounts and password hashes;
- sessions;
- the audit log;
- submissions (student source code);
- runs, diagnoses, recommendations and follow-up evaluations;
- content-version snapshots.

The content files and the code live in Git and the images. The TLS certificates live in
the proxy's `caddydata` volume; Caddy re-issues them on its own if they are lost. The
database's private CA key is kept offline by the owner (runbook §1); if the server
certificate is lost, issue a new one from it, or run `make-db-certs.sh` again and copy the
new `ca.crt` to the runner.

The runner VM holds no data. It can be rebuilt from the runbook.

Dumps contain personal data once real students take part. They follow
`docs/pilot/data-governance.md`:

- encrypted at rest;
- access limited to the owner;
- stored off the App VM;
- deleted at the end of the retention period.

## Targets (proposed; the owner confirms them at Gate B)

| | Target | Basis |
| --- | --- | --- |
| **RPO** (data that may be lost) | at most 24 h normally; at most 1 h on days with a class session | a daily scheduled dump, plus hourly dumps while a session runs, plus one dump right before and right after each session |
| **RTO** (time to be serving again) | 2 h | restoring a pilot-sized database (thousands of submissions) takes minutes; the rest is checking and switching. The test database restores in under a second, which says nothing about real sizes, so measure at the first rehearsal on the host |

## Scripts

| Script | What it does | Safety |
| --- | --- | --- |
| `deploy/backup/pg-backup.sh` | `pg_dump --format=custom`, checks the file with `pg_restore --list`, writes a `.sha256`, and can prune this script's own files older than `BACKUP_RETENTION_DAYS` | files are mode 600 (`umask 077`); a dump is written as `.partial` and renamed only after it checks out |
| `deploy/backup/pg-restore.sh <dump> <new-db>` | verifies the checksum, creates **a new database**, restores it in a single transaction, and prints the schema revision | refuses to restore over an existing database (exit 3) and refuses unsafe names (exit 2); a corrupt dump fails before anything is created |
| `codeadapt-admin db-fingerprint` | JSON with the schema revision plus, for each table, the row count and a SHA-256 of the rows in primary-key order | digests only, never row contents |

## Taking a backup (App VM)

```
# the database port is published on the private address only (compose.app.yaml)
# TCP connections need verified TLS (R5): connect by the certificate's name.
export PGHOST=db.codeadapt.internal PGHOSTADDR=<private address>
export PGSSLMODE=verify-full PGSSLROOTCERT=/etc/codeadapt/db-tls/ca.crt
export PGUSER=codeadapt_owner PGDATABASE=codeadapt
export PGPASSWORD=...        # or a ~/.pgpass entry, mode 600
BACKUP_DIR=/var/backups/codeadapt BACKUP_RETENTION_DAYS=<from data governance> \
  deploy/backup/pg-backup.sh
```

Schedule it with cron or a systemd timer (examples in `production-runbook.md`). Then copy
each new dump and its `.sha256` off the VM, to storage the owner controls and with the
same access rules.

## Restore drill (do this before the pilot and then monthly)

1. Take a fingerprint of the live database:
   `CODEADAPT_DATABASE_URL=<owner url> codeadapt-admin db-fingerprint > before.json`.
2. Take a backup with `pg-backup.sh`.
3. Restore it into a new database:
   `deploy/backup/pg-restore.sh <dump> codeadapt_restore_<date>`.
4. Fingerprint the copy with the same command and the restored database's URL, saving it
   to `after.json`.
5. Compare: `diff before.json after.json` must print nothing. Writes that happened
   between steps 1 and 2 show up as differences, so run the drill when no class session
   is active.
6. Record the date, the dump size, the restore duration and the result in the
   operations log.
7. Drop the drill database. This is a delete, so do it by hand and check the name twice.

## Recovering from data loss

1. Stop the API and worker: `docker compose ... stop api` on the App VM and
   `docker compose ... stop worker` on the runner VM. The worker finishes its current job
   first.
2. Restore the newest good dump into a **new** database, as in step 3 of the drill.
3. Run `codeadapt-admin db-setup` against the new database to re-apply the grants.
   Roles are cluster-wide, so they already exist.
4. Point `DB_NAME` in `app.env` and `runner.env` at the new database, then start
   everything again.
5. Check `/api/v1/ready` and `codeadapt-admin status`. Write down what was lost, which is
   everything between the dump and the incident, and follow `incident-response.md`.

Keep the damaged database until the incident is closed. Never drop it as part of the
recovery.

## Verification evidence

- `backend/tests/unit/test_backup_restore.py` (PostgreSQL only):
  - populates users, sessions, audit events, submissions, jobs, runs and a diagnosis;
  - runs `pg-backup.sh`, restores with `pg-restore.sh` into a new database, and asserts
    that the two `db-fingerprint` outputs are equal;
  - checks that restoring over the copy is refused and that a corrupted dump creates
    nothing.
- It passed in the cloud container against PostgreSQL 16.15 (2026-11-07), and it runs in
  the `backend-postgres` CI job.
- `backend/tests/unit/test_migrations.py` walks every migration 0001→0006 up one step at
  a time, down to base, and back up to head, on both SQLite and PostgreSQL.
  `test_auth_parity.py` checks that 0005→0006→0005 keeps the rows.
