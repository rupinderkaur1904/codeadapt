# Incident response (pilot)

For a small pilot run by one operator, who is the owner. Keep it simple, write things
down as they happen, and protect students first.

## Severity

| Level | Examples | Response |
| --- | --- | --- |
| **SEV1** | learner data may have left the system (DB, backups or logs exposed; a compromised VM); a sandbox escape is suspected; one student can see another's data | act **immediately**: contain (below), stop the pilot session, follow the breach steps |
| **SEV2** | the site is down during a session; submissions are not processed (queue stuck); data loss needing a restore | restore service within the RTO (2 h); tell the students in the session |
| **SEV3** | a single failed job, an adaptation failure (`codeadapt-admin status`), a certificate renewal warning | fix within a working day |

## First 15 minutes (any severity)

1. Open an incident note: time, who noticed, what was seen. Copy exact error text and
   `X-Request-ID` values. Never paste passwords or tokens.
2. Check:
   - `/api/v1/ready`;
   - `codeadapt-admin status`;
   - `docker ps` on both VMs;
   - `app logs --since 30m api`;
   - `runner logs --since 30m worker`.
3. Decide the severity, and write it down.

## Containment

| Situation | Action |
| --- | --- |
| Suspected compromise of the **Runner VM** | `runner stop` (or power off the VM). Rotate the worker's DB password: set a new `WORKER_DB_PASSWORD` in `app.env` and run `app run --rm db-setup`. Keep the VM's disk for analysis; rebuild a new VM from the runbook. |
| Suspected compromise of the **App VM** or the database | Take the site offline (`app stop proxy`). Snapshot the disk. Rotate every database password and the accounts' passwords (`codeadapt-admin set-password` ends all sessions). Rebuild from the runbook and restore from a backup taken **before** the suspected time. |
| A student account is misused | `codeadapt-admin disable <user>`, which ends its sessions, then review `audit_events` for that account. |
| Queue stuck | `codeadapt-admin status`. If the worker is unhealthy, `runner restart worker`. If the sandbox is unavailable (`last_error` says so), check `docker info` and `runsc` on the runner. Jobs are requeued automatically. |
| Adaptation failures | Each one is a DONE job with an `adaptation failed:` marker. The student received a diagnosis but no new recommendation. Collect the error text from the logs (it is redacted) and fix it in a PR. Do not edit rows by hand. |
| Data loss or corruption | Follow backup-and-restore.md, "Recovering from data loss". Keep the damaged database. |

## Personal-data breach (SEV1)

Once real students take part, learner data is personal data. Under India's Digital
Personal Data Protection Act 2023 and its Rules, a personal-data breach must be reported to
the Data Protection Board and to the affected people. The deadlines and the exact form are
set by the Rules and **need confirmation by legal or institutional review**
(docs/pilot/data-governance.md). The institution's ethics committee also expects to be
told.

Until that review gives a precise procedure:

1. contain the breach;
2. preserve the evidence;
3. record what data, which students and which time window were involved;
4. inform the owner's institution and follow its instructions on notification, without
   delay.

## After the incident

Within a week, write a short blameless review covering:

- the timeline;
- the impact (students affected, data and time lost);
- the root cause;
- what worked and what did not;
- follow-up actions with owners.

File the follow-up actions as issues or PRs, and link the review from the operations log.
