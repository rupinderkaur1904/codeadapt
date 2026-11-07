# Production runbook (Option C: App VM + Runner VM)

Status: **prepared, never executed.** Every step below needs owner Gate A (architecture
and provider) and Gate B (provisioning and exposure) to be recorded first. Nothing in this
repository has been deployed. Real students also need Gate C (docs/pilot/).

Conventions:

- commands run from a checkout of the approved release tag on each VM;
- `app` means `docker compose -f deploy/compose.app.yaml --env-file deploy/app.env`;
- `runner` means `docker compose -f deploy/compose.runner.yaml --env-file deploy/runner.env`.

## 0. Before provisioning

- [ ] Gate A recorded: option, provider, region, budget ceiling and domain.
- [ ] A release tag on `main` with all CI checks green. The PR was merged by the owner.
- [ ] `sha256sum -c --quiet docs/reviews/milestone-3/research-freeze.sha256` is silent on
      that tag, or any change has an approved ADR.

## 0a. Pinned base images (R6)

Every image pulled from a registry is pinned to an immutable SHA-256 digest (owner
decision R6, Gate B). The tag stays next to the digest for readability, but Docker uses
only the digest, so a re-pushed tag cannot change a build. Each digest is a multi-platform
index: it covers both x86-64 (the runner) and Arm64 (an Arm app VM). The test
`tests/unit/test_deploy_files.py` fails if an image is unpinned or missing from this table.

| Image | Used in | Pinned reference | Recorded |
| --- | --- | --- | --- |
| Python | API and worker images | `python:3.13-slim@sha256:09a17cad02668ae61ece136b4fd36ac3849e14f670ebedb637ea3e15580525bc` | 2026-11-07 |
| Docker CLI | worker image | `docker:29-cli@sha256:2357639ad1ea7d0194134bf3292622fd4e562483966ed674e5d7c945b5f3b28d` | 2026-11-07 |
| Node | web build stage | `node:22-alpine@sha256:0e1754758c2df4cfa3e68d59e2e1b7374bb7fd9ea6328eaaacf15cc934af8202` | 2026-11-07 |
| Caddy | reverse proxy image | `caddy:2.8.4-alpine@sha256:af32e97399febea808609119bb21544d0265c58a02836576e32a2d082c262c17` | 2026-11-07 |
| PostgreSQL | database (app Compose file) | `postgres:16.4-alpine@sha256:5660c2cbfea50c7a9127d17dc4e48543eedd3d7a41a595a2dfa572471e37e64c` | 2026-11-07 |
| GCC | sandbox image (research-frozen, pinned since Milestone 1) | `gcc:14.2.0@sha256:b99b86a28812b1e6453a231a947dc43d76fe192788a12f344a9b568bf9f5d24c` | earlier |

**Updating a pin** (for security fixes): look up the new digest
(`docker buildx imagetools inspect <image>:<tag>`), change the file and this table in one
pull request, and let CI rebuild the production images. Never change the GCC pin: it is
part of the research freeze.

## 1. App VM

1. A Linux VM with automatic security updates turned on. Allow SSH only by key, from the
   operator's address only.
2. Firewall:
   - 80 and 443 from anywhere;
   - 5432 only from the Runner VM's private address;
   - nothing else.
3. Install the Docker Engine and Compose plugin from the vendor's repository.
4. DNS: an A/AAAA record for `SITE_HOST` pointing at this VM. Caddy needs it in order to
   obtain the certificate.
5. Create the settings file:
   - `cp deploy/app.env.example deploy/app.env && chmod 600 deploy/app.env`;
   - fill in every value, generating each password with `openssl rand -base64 32`;
   - set `DB_PRIVATE_BIND` to this VM's **private** address.
6. Start: `app up -d --build`. This runs `migrate`, then `db-setup` (roles and grants),
   then `api` and `proxy`.
7. Verify. Record each output in `docs/deployment/host-verification-<date>.md`.
   - `curl -sI https://$SITE_HOST/` shows a valid certificate (no `-k`), and the headers
     include HSTS, CSP, `X-Frame-Options` and `X-Content-Type-Options`.
   - `curl -s https://$SITE_HOST/api/v1/ready` returns `{"status":"ready"}`.
   - `curl -sI http://$SITE_HOST/` returns a 308 redirect to `https://`.
   - `app exec api codeadapt-admin status` reports `"ok": true`.
   - The forwarded client address is correct: one failed login from a known address
     appears in `audit_events.client` as that address, not as the proxy's `172.30.0.10`.

## 2. Runner VM

1. A separate Linux VM on the same private network, with no public inbound ports and SSH
   by key from the operator only.
2. **Block egress** except TCP 5432 to the App VM's private address (and the package
   mirrors during installation only). Check that `curl https://example.com` fails.
3. Install Docker and the **pinned** gVisor release, with its checksum verified, exactly
   as the `sandbox-gvisor` CI job does. Then run `runsc install` and restart Docker.
4. Build the sandbox image: `docker build -t codeadapt-sandbox:gcc14.2-1 sandbox/`.
5. Create the settings file: `cp deploy/runner.env.example deploy/runner.env`, then
   `chmod 600`, and fill it in:
   - the worker password from `app.env`;
   - `DOCKER_SOCKET_GID=$(stat -c %g /var/run/docker.sock)`.
6. Run the gVisor host verification, `docs/deployment/gvisor-verification.md` level L3,
   all steps. **Stop here if any step fails.**
7. Start: `runner up -d --build`. The worker refuses to start without `runsc` (ADR-040).
8. Warm up: `runner run --rm worker codeadapt-worker --warm-up`. It should list every
   content version as valid.
9. End-to-end: submit the lower-bound reference solution with a test account
   (`--data-class dev`) and see "all tests passed".

## 3. Monitoring

- **External uptime check** (any provider, or a cron job on another machine): fetch
  `https://$SITE_HOST/api/v1/ready` every 5 minutes and alert unless it returns 200.
- **Queue and failure check** on the App VM:

  ```
  */5 * * * * cd /opt/codeadapt && docker compose -f deploy/compose.app.yaml --env-file deploy/app.env exec -T api codeadapt-admin status >> /var/log/codeadapt-status.log 2>&1 || <alert command>
  ```

  It exits 1 when any of these happens:
  - the oldest queued job is older than 5 minutes;
  - a worker is lost;
  - a job failed;
  - an adaptation failed;
  - the schema revision does not match.
- **Container health**: `docker ps` shows `healthy` for `api` and `worker`.
  `restart: unless-stopped` restarts a crashed container.
- **Logs**: `app logs api`, `runner logs worker` (JSON lines, redacted, ADR-042). Keep
  them for at most the retention period in the data governance draft.

## 4. Backups

```
# App VM, root crontab (docs/deployment/backup-and-restore.md)
15 2 * * *  PGHOST=<private> PGUSER=codeadapt_owner PGDATABASE=codeadapt BACKUP_DIR=/var/backups/codeadapt BACKUP_RETENTION_DAYS=<n> /opt/codeadapt/deploy/backup/pg-backup.sh
```

On session days, also run it hourly, and once before and once after the session. Copy
the dumps off the VM. Run the restore drill before the pilot and then monthly.

## 4b. Administration that needs the owner connection

The API's database role can add audit rows but cannot change or delete them, and cannot
write the schema revision (owner decision R7, `db/roles.py`). Commands that delete or
scrub audit rows therefore run as the schema owner, through the `admin` Compose service.
It is never started by `up`, and exits when the command ends:

```
alias admin='docker compose -f deploy/compose.app.yaml --env-file deploy/app.env --profile admin'
admin run --rm admin erase-learner p017            # dry run: shows what would go
admin run --rm admin erase-learner p017 --apply    # participant withdrawal (data governance §7)
admin run --rm admin purge-sessions --older-than-days 30 --apply   # monthly
```

Read-only commands (`status`, `db-fingerprint`, `list`) and account commands
(`create-user`, `disable`, `set-password`) still work through `app exec api
codeadapt-admin ...`.

## 5. Before each class session

1. `app exec api codeadapt-admin status` reports `"ok": true`.
2. `runner run --rm worker codeadapt-worker --warm-up` (it is quick when nothing has
   changed).
3. Take a backup.
4. Accounts: create them with `codeadapt-admin create-user`. Use `--data-class real` only
   after Gate C.

## 6. Upgrades

1. Back up.
2. `git fetch && git checkout <new tag>`.
3. `app up -d --build`. It migrates and re-applies grants, then restarts `api`.
4. `runner up -d --build`. The old worker gets SIGTERM, finishes its job, and the new one
   starts.
5. Check `/api/v1/ready` and `codeadapt-admin status`.

**Rollback:** check out the previous tag and run `up -d --build` again. If the new release
included a migration, restore the pre-upgrade dump into a new database as described in
backup-and-restore.md. Never downgrade a migration on the live database without first
taking a fresh backup.

## 7. Shutting down after the pilot

Follow the retention and deletion steps in `docs/pilot/data-governance.md`. Destroying the
VMs and deleting the backups are owner-approved, irreversible steps.
