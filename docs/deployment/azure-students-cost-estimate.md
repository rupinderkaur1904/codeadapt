# Option C on Azure for Students: cost estimate for a 20–50 student pilot

- **Asked by:** the owner, 2026-11-07. Gate A chose Option C (two servers: one for the
  application and database, one isolated server for sandboxed C++ execution). The owner
  has no budget for AWS and asked for Azure for Students instead, in an India region if
  possible.
- **Status:** estimate only. **Nothing has been provisioned.** The owner confirms the
  budget, region and domain before anything is created.
- **How the figures were found:** Microsoft's public pages on Azure for Students and the
  Azure free services, plus published pay-as-you-go prices, read on 2026-11-07. The Azure
  price API could not be reached from this environment, so every price below is an
  **approximate list price to confirm in the Azure pricing calculator** before
  provisioning. Items marked *(verify)* came from secondary sources or could change.

## 1. Summary

| | Plan 1: free sizes only | Plan 2: larger runner, used only during sessions |
| --- | --- | --- |
| App + database server | B2pts v2 (Arm, 2 vCPU, 1 GiB) — free | same |
| Sandbox runner | B2ats v2 (x86, 2 vCPU, 1 GiB) — free | B2s (x86, 2 vCPU, 4 GiB), switched off between sessions |
| Expected monthly cost | **about $0**, at most about $12 if disks and IP addresses are not covered | **about $3–15**, depending on hours used |
| Paid from | nothing, or the $100 credit | the $100 credit |
| Main risk | 1 GiB of memory is tight; must be tested on the host | someone must start and stop the runner around sessions |

**Recommendation:** start with Plan 1. Run the host acceptance tests from the runbook
(warm-up, then a burst of submissions). Move the runner to Plan 2 only if the 1 GiB
runner fails those tests. Either way, the $100 credit covers the pilot, and **no card
payment is needed**, because the student subscription stops resources instead of
charging a card (section 5).

## 2. What Azure for Students gives

- **$100 credit** for 12 months, with no credit card. It can be renewed each year while
  the owner is still a student.
- **Free services for 12 months**, on top of the credit (Microsoft's free services list):
  - Linux VMs: **750 hours a month each** of B1s, B2pts v2 (Arm) and B2ats v2 (AMD).
    All three have only **1 GiB of memory**. 750 hours covers one VM running all month
    (about 730 hours), so two VMs of the **same** size do not both fit. Option C
    therefore uses two **different** free sizes.
  - Managed disks: **2 × 64 GB Premium SSD (P6)** *(verify)*.
  - Blob storage: **5 GB** locally redundant *(verify)*.
  - Azure Database for PostgreSQL Flexible Server: **750 hours of B1MS, 32 GB storage,
    32 GB backup** (used only in the variant in section 6).
  - Public IPv4 addresses: **1,500 hours a month** *(verify)*, enough for two addresses.
- **Outbound data:** the first 100 GB a month are free *(verify; some pages say 15 GB)*.
  A pilot of 50 students uses far less than 15 GB (section 3.4).
- **Limits that matter:**
  - Student subscriptions usually allow only some regions, set by an "Allowed resource
    deployment regions" policy. Central India or South India may not be on the list.
    The owner can see the list in the Azure portal under **Policy → Assignments**.
    Southeast Asia (Singapore) is the usual fallback.
  - A quota of about **6 vCPUs** per region, with no increase on this offer. Option C
    uses 4.
  - The 12-month free period starts when the subscription is created, not at
    provisioning.

## 3. Cost by item (per month)

### 3.1 Compute

| Server | Size | Why this size | Free? | List price if not free *(approx.)* |
| --- | --- | --- | --- | --- |
| App + database | **B2pts v2**, Arm64, 2 vCPU, 1 GiB | Python, PostgreSQL and Caddy all run on Arm. Using the Arm size leaves the free x86 size for the runner. | Yes, 750 h | about $6 |
| Sandbox runner | **B2ats v2**, x86-64, 2 vCPU, 1 GiB | The runner must be **x86-64**. Every fingerprint and evaluation result was measured on x86-64, and compiled C++ can behave differently on Arm. Running learners' code on Arm would quietly change what the frozen diagnosis sees. | Yes, 750 h | about $7 |
| Runner, Plan 2 | **B2s**, x86-64, 2 vCPU, 4 GiB | Room for compiles and gVisor without memory pressure | No | about **$0.045 an hour**, about $33 if left on all month |

B-series sizes are "burstable": they run at full speed for bursts and slower over long
periods. Class sessions are bursts, so this suits the pilot.

**Plan 2 in practice:** a stopped ("deallocated") VM costs nothing for compute, only for
its disk. Six two-hour sessions a month on B2s is about 12 hours, or about **$0.55**.
Even left on for a full working week before a deadline, it costs about $8.

**gVisor works on these VMs.** gVisor's default platform (systrap) does not need nested
virtualisation, so a normal Azure VM is enough. No special or dedicated host is needed.
gVisor on a real host is still **not verified** (gvisor-verification.md L3); the first
host session must do that.

### 3.2 Will 1 GiB be enough?

This is the main uncertainty of Plan 1. It can only be settled by testing on the host.

- **Runner:** the Docker daemon, containerd and the worker take roughly 300–400 MB. One
  sandboxed compile is limited to 256 MiB (`execution/docker.py`), plus gVisor's own
  overhead. The worker runs one job at a time, so this should fit, with a 2 GB swap file
  as a safety margin. A first-time fingerprint measurement takes longest; the runbook's
  `codeadapt-worker --warm-up` before each session handles that.
- **App + database:** PostgreSQL with `shared_buffers` at 128 MB, the API (about
  150 MB), Caddy (about 30 MB) and static web files. This should fit for 50 students,
  also with a 2 GB swap file.
- **Pass/fail test:** after warm-up, submit 50 attempts in a burst. Pass if no job fails
  for memory, no container is killed by the kernel, and the slowest result reaches the
  learner within the time the runbook sets. If it fails, move only the runner to Plan 2.

### 3.3 Storage and backups

| Item | Size | Free? | If not free *(approx.)* |
| --- | --- | --- | --- |
| App server disk | 64 GB Premium SSD (P6) | Yes *(verify)* | about $10, or $2–3 for a 32 GB Standard SSD |
| Runner disk | 64 GB Premium SSD (P6) | Yes *(verify)* | same |
| Off-server backups | Daily `pg-backup.sh` dumps to Blob storage. A dump for 50 students is a few MB; 30 days fit well under 1 GB. | Yes, 5 GB | under $0.10 |
| Disk snapshot before upgrades | 1 GB | Yes *(verify)* | under $0.10 |

If the free disks turn out not to apply, choosing **32 GB Standard SSD** disks keeps the
cost to about $5 for both.

### 3.4 Networking

| Item | Need | Free? | If not free *(approx.)* |
| --- | --- | --- | --- |
| Public IPv4, app server | For HTTPS (Caddy) | Yes, within 1,500 h *(verify)* | about $3.65 |
| Public IPv4, runner | Only for outbound updates and image pulls. **No inbound ports open**; it is reached over the private network from the app server. Azure no longer gives new networks free default outbound access, and the alternative, a NAT gateway, costs about $32 a month. | Yes, within 1,500 h *(verify)* | about $3.65 |
| Private network between the servers | One virtual network, two subnets | Free | — |
| Outbound data | 50 students × a few hundred page loads × under 1 MB is roughly 2–5 GB a month | Free up to 100 GB *(verify)* | about $0.09 per GB |
| Domain name | Optional, see section 4 | — | — |

### 3.5 Monitoring

| Item | Choice | Cost |
| --- | --- | --- |
| VM CPU, memory, disk metrics | Azure's built-in platform metrics | Free |
| Alerts | A few metric alerts (VM stopped, CPU, disk) by email | Free or a few cents each *(verify)* |
| Application health | The existing `/api/v1/ready`, the worker heartbeat check, and `codeadapt status` | Free |
| Uptime check from outside | Optional: a free external checker, or none | Free |
| Log Analytics or Application Insights | **Not used.** The app already logs to the server with redaction; sending logs to a cloud service would also send learner activity data off the server. | $0 |

## 4. Domain and HTTPS

- **Free option:** Azure gives a public IP address a DNS name such as
  `<name>.centralindia.cloudapp.azure.com`. Caddy can get a Let's Encrypt certificate for
  that name. This costs nothing and is enough for a pilot.
- **Own domain:** a `.in` or `.com` costs about ₹700–1,200 a year. The GitHub Student
  Developer Pack has also included a free first-year domain from some registrars
  *(verify the current offer)*. Azure credit cannot be spent on domains from other
  registrars.
- Either way, **TLS is not operational until it is checked on the host.**

## 5. What happens when the credit or the year runs out

- The student subscription has a **spending limit**. When the $100 is used up, or the
  12 months end, Azure **stops and disables** the resources. It does not charge a card,
  because there is none.
- If nothing is done, the data can be deleted after a grace period *(about 90 days;
  verify)*. For the pilot, the off-server backups and a final export (runbook) must be
  taken before then.
- The owner can see the remaining credit at **Microsoft Azure Sponsorships** or in the
  portal under **Cost Management**. A **budget alert at $25 and $50** costs nothing and
  is recommended.
- **Upgrading to pay-as-you-go** would need a card and would start real charges. That
  would need the owner's explicit approval.

## 6. Variant (needs the owner's approval): managed PostgreSQL instead of the database on the app server

Azure for Students also includes a free managed PostgreSQL server (B1MS, 32 GB) for
12 months. Moving the database there:

- frees memory on the 1 GiB app server;
- gives automatic backups and point-in-time restore;
- **requires TLS on database connections by default, which closes open review item R5**
  (the worker's database traffic is currently not encrypted).

However, it is **Option B, not the Option C the owner chose**. It also means:

- learner data is held by a managed service, which needs a line in data-governance.md;
- the database must be reached through private access (network integration), not a
  public endpoint;
- the deployment files would need a separate profile without the PostgreSQL container.

I recommend considering it, but it is the owner's decision.

## 7. Before provisioning (the owner's choices)

1. **Budget:** confirm that up to the $100 credit may be used. Plan 1 should cost about
   $0, and Plan 2 a few dollars a month.
2. **Region:** check the allowed regions in the portal. Prefer Central India, then South
   India, then Southeast Asia.
3. **Domain:** free `cloudapp.azure.com` name, or an own domain.
4. **Plan 1 or Plan 2** for the runner. The recommendation is to start with Plan 1 and
   test it.
5. **Variant in section 6:** yes or no.
6. **R5:** whichever database choice, encrypt the worker's database connection before
   enrollment.

Until then, nothing is created, and no money or credit is spent.
