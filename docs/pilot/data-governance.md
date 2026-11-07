# Pilot data governance (DRAFT, not approved)

> **Status: DRAFT for owner Gate C and for independent ethics and legal review.**
> - No ethics approval or exemption exists.
> - No participant has been recruited or contacted.
> - No real-student data has been collected.
> - Nothing here is legal advice. Items marked **[REVIEW]** need a qualified legal or
>   institutional reviewer before enrollment.

## 1. Roles

| Role | Who | Responsibility |
| --- | --- | --- |
| Data fiduciary and principal investigator | the project owner (an independent student researcher, **no supervisor**) | decides purposes and means; answers participants' requests; reports breaches |
| Operator | the owner | runs the system following `docs/deployment/production-runbook.md` |
| Processors | the hosting provider chosen at Gate A | hosts the VMs, database and backups under its terms. **[REVIEW]** whether a data processing agreement is needed |
| Ethics review body | **to be determined by the owner** | must give an approval or exemption decision in writing before enrollment |

## 2. What the system stores (checked against `backend/src/codeadapt/db/models.py`)

| Data | Where | Personal? | Why it is needed |
| --- | --- | --- | --- |
| Username | `users.username`, `audit_events.username` | **pseudonymous** if it follows §3 | login; linking a participant's attempts |
| Password hash (Argon2id) | `users.password_hash` | credential | login |
| Role and data class (`real`) | `users` | no | access control; keeps real data apart from synthetic data (ADR-008) |
| Session token hash, CSRF value, timestamps | `auth_sessions` | linked to the account | login sessions; purged after expiry (§6) |
| **Client IP address** | `audit_events.client` | **yes, personal data** | login throttling and security audit |
| Event kind, time, target | `audit_events` | linked to the account | security audit; records researcher access to learner data |
| **Submitted source code** and timestamps | `submissions` | linked to the account; may contain anything the student types, including names or comments | the core of the research: diagnosis and feedback |
| Program output (stdout/stderr) of the student's code on test inputs | `test_observations` | linked to the account | evidence for the diagnosis |
| Diagnoses, recommendations, follow-up verdicts | `diagnoses`, `recommendations`, `followup_evaluations` | linked to the account | feedback and research analysis |
| Application logs | container logs | method, path, status, duration, request id. **No** query strings, client addresses, source code or secrets (ADR-042) | operations |
| Backups | off-host dump files | everything above | recovery |

Not collected:

- real names;
- email addresses or phone numbers;
- student IDs or grades;
- demographics;
- device fingerprints;
- analytics or tracking cookies;
- third-party scripts.

The only cookie is the session cookie (HttpOnly, Secure, SameSite=Strict, Path=/api).

## 3. Pseudonymous accounts

- Accounts are created by the operator with codes such as `p017`, never with names.
- The key that links a code to a person (name, contact) exists only on the signed consent
  record and in one key file. The owner keeps that file offline, encrypted, and **never
  in the repository, the database, the hosting account or the project files**.
- Participants receive their code and an initial password privately, and are asked to
  change the password on first login (Account page).
- Participants are told not to put their name or other identifying text in their code.

## 4. Legal basis and Indian law **[REVIEW]**

The pilot would process digital personal data in India. The **Digital Personal Data
Protection Act, 2023 (DPDP Act)** and the **DPDP Rules** therefore need to be considered.
Several provisions of the Rules commence in phases, so a reviewer must confirm which
obligations are in force on the pilot date.

The points needing review:

1. **Consent (DPDP Act s.6).**
   - Consent must be free, specific, informed, unconditional and unambiguous, given by a
     clear affirmative action, and as easy to withdraw as to give.
   - The consent form (informed-consent.md) is drafted to that standard. It has a
     notice, a separate tick for each purpose and a withdrawal route.
   - **[REVIEW]** Is the notice content prescribed by the Rules covered, and in which
     languages must it be offered?
2. **Children (s.9).** Processing the data of anyone under 18 needs verifiable parental
   consent. **The pilot protocol limits participation to adults (18+), confirmed at
   consent.** **[REVIEW]** How should age be confirmed?
3. **Research exemption (s.17(2)(b)).** The Act exempts processing for research or
   statistical purposes where the data is **not used to take any decision specific to the
   data principal**.
   - CodeAdapt shows each student individual feedback and recommendations, so it is
     unclear that the exemption applies.
   - **This draft assumes it does not apply and relies on consent.** **[REVIEW]**
4. **Purpose limitation and erasure (s.8(7)).** Data is erased when its purpose is served
   or consent is withdrawn, unless retention is legally required (see §6 and §7).
5. **Security safeguards and breach notice (s.8(5), 8(6)).**
   - The safeguards are ADR-029, ADR-040, ADR-041 and ADR-042: encryption in transit,
     least-privilege roles, access audit, backups.
   - Encryption in transit covers browsers to the proxy (TLS). The worker's connection to
     PostgreSQL crosses the private network between the two VMs and is **not yet
     encrypted**. **[REVIEW, Gate B]** Enable TLS on PostgreSQL and `sslmode=verify-full`
     on the worker before enrollment (milestone-3 PR review, finding R5).
   - Breaches are to be notified to the Data Protection Board and the affected
     participants, in the form and time set by the Rules. **[REVIEW]** The exact
     deadlines.
6. **Grievance redressal (s.8(10), s.13).** Participants contact the owner (§8). If the
   matter is not resolved, they may approach the Board.
7. **Cross-border transfer (s.16).** If the hosting region chosen at Gate A is outside
   India, check that it is not a restricted territory. **[REVIEW]** Preferring a region
   in India removes the question.
8. **Institutional rules.** If participants are students of an institution, its own
   research, IT and data policies may apply, and its permission may be needed to recruit
   on its premises or channels. **[REVIEW]**
9. **Ethics framework.** The relevant national guidelines for research with human
   participants in India, such as the ICMR National Ethical Guidelines where applicable,
   and the review body's own requirements. **[REVIEW]** Which body, and is this
   minimal-risk research?

## 5. Access control

| Who | Access |
| --- | --- |
| Participant | their own submissions, feedback and recommendations (ADR-040 authorization matrix) |
| Researcher role (the owner only) | research views. Every researcher view of a learner's data is written to `audit_events` |
| Database owner role | the owner only, for migrations and backups. Passwords are generated and stored only in the VM settings files (mode 600) |
| Worker role | job data only. It cannot read accounts, sessions or the audit log (ADR-042) |
| Nobody else | there are no other accounts. The hosting provider has infrastructure access under its terms |

## 6. Retention (proposed; the owner decides)

| Data | Retention | How |
| --- | --- | --- |
| Login sessions | deleted 30 days after expiry or revocation | `admin run --rm admin purge-sessions --older-than-days 30 --apply` (owner connection, runbook §4b), monthly |
| Application logs | 30 days | logging driver rotation (`max-size`/`max-file`), or the host's journald retention |
| Audit events | until the pilot data is deleted (they evidence access control) | deleted with the account (§7). The API's database role can add audit rows but cannot change or delete them (R7) |
| Pilot research data (submissions, runs, diagnoses, recommendations) | until analysis ends, at most **12 months** after the last session, unless the ethics review sets otherwise | then deleted, or irreversibly anonymised by removing usernames, IP addresses and free text; **[REVIEW]** whether source code can ever count as anonymous |
| Backups | rolling 30 days during the pilot; all deleted when the research data is deleted | `BACKUP_RETENTION_DAYS=30`; off-host copies deleted by hand |
| Code-to-person key and consent forms | as the ethics review requires; the key is destroyed when the data is deleted or anonymised | owner, offline |

## 7. Participant rights and withdrawal

- **Withdraw:** a participant can withdraw at any time without giving a reason, by
  telling the owner (§8). Their account is disabled at once
  (`codeadapt-admin disable`).
- **Erasure:** their data is deleted from the database within 14 days with
  `admin run --rm admin erase-learner <code> --apply` (as the schema owner, runbook §4b;
  the API's own database role cannot change or delete audit rows). Run it first without
  `--apply` to see what will go. Backups age out within the backup retention period.
  - The command deletes the account, its sessions, its submissions and everything derived
    from them (runs, outputs, diagnoses, recommendations, follow-ups), and every audit row
    carrying its name.
  - Researchers' access records are kept, because they evidence access control, but any
    that name the learner's code name or one of their submission ids get the target
    `(erased learner)`.
  - It leaves one audit row, `account_erased`, which holds the number of rows deleted but
    not the name.
  - It is tested in `backend/tests/unit/test_operations.py`. It is an operator tool and
    changes no research logic.
- **Access and correction:** on request, the owner exports the participant's own
  submissions and feedback.
- Data that has already gone into aggregate, anonymous results cannot be taken out of
  them. The consent form says so.

## 8. Contact

Owner contact details go into the participant documents at Gate C. They are deliberately
not written in this repository.
