# Milestone 4 deployment progress (Azure)

The living record of what has actually been done on Azure for CodeAdapt, with the evidence
for each step. It holds **no secrets**: no passwords, keys, tokens, connection strings or
subscription identifiers. Plan: [azure-deployment-guide.md](azure-deployment-guide.md).

Each step is done by the owner, guided step by step: steps 1–8 in the Azure portal, later
steps with the Azure CLI in Cloud Shell and SSH (owner's choice, 2026-11-09 11:58). The
evidence is the owner's screenshot or pasted output, checked before the next step.
"Verified" below means that check, not an automated test.

## Subscription facts (read-only checks, 2026-11-09)

| Fact | Value |
| --- | --- |
| Offer | Azure for Students |
| Credit | ₹9,321 left of ₹9,523; expires 22/10/2027 |
| Region | Central India |
| Existing project | Relay, resource group `relay-rg` (VM B2ats v2, PostgreSQL B1ms, public IP, VNet 10.20.0.0/16): **never touched** |
| Relay's cost | about ₹390/month (public IP and DNS zone; VM, disk and database inside the free allowances) |
| Free allowances | 750 h/month each of B2pts v2 and B2ats v2 (B1s is not free here), 2 × P6 64 GiB disks, 5 GB Blob, PostgreSQL B1MS 750 h; no free public IP |
| Allowances Relay already uses | B2ats v2 hours, PostgreSQL B1MS hours, one P6 disk |
| vCPU quota (Central India) | total regional 2/6; Basv2 2/10; Bpsv2 0/10 (the plan reaches 6/6) |

## Decisions

| When | Decision |
| --- | --- |
| 2026-11-09 08:02 | Owner approved the plan: App VM B2pts v2 (free hours) and a runner VM B2ats v2 (paid), on only during sessions, in a separate `codeadapt-rg` and VNet. Expected cost for CodeAdapt about ₹520–540/month; with Relay about ₹910–930/month. |
| 2026-11-09 11:40 | Owner merged the deployment-files pull request (#5, `main` 8125461) and made the four GHCR packages public. |
| 2026-11-09 11:57 | Owner approved the App VM and its public IP (about ₹310/month). |
| 2026-11-09 12:34 | Owner approved opening SSH to any address for about 5 minutes to find the real source address (Jio IPv6/NAT64), then locking it again. |
| 2026-11-09 12:44 | Owner approved go-live: NSG 80/443 from Internet, stack started. |
| 2026-11-09 13:05 | Owner approved the runner VM (about ₹210/month disk + about ₹1 per running hour; temporary install IP about ₹0.40/hour). |

## Steps

| # | Date (IST) | Step | Cost | Result |
| --- | --- | --- | --- | --- |
| 1 | 2026-11-09 | Read-only checks: credit, Relay resources and costs, free services, quotas | ₹0 | Verified (facts above) |
| 2 | 2026-11-09 | Budget `codeadapt-relay-monthly`: ₹1,200/month on the billing scope; alerts at 50, 80 and 100 % actual and 90 % forecast | ₹0 | Verified |
| 3 | 2026-11-09 | Resource group `codeadapt-rg`, Central India, tag `project=codeadapt` | ₹0 | Verified |
| 4 | 2026-11-09 | VNet `codeadapt-vnet` 10.30.0.0/16; subnets `app` 10.30.1.0/24 and `runner` 10.30.2.0/24 (private; Bastion, Firewall and DDoS plan off) | ₹0 | Verified |
| 5 | 2026-11-09 | NSGs `codeadapt-app-nsg` and `codeadapt-runner-nsg` (a misspelt first copy was deleted and recreated) | ₹0 | Verified |
| 6 | 2026-11-09 | App NSG inbound: 100 TCP 22 from the owner's address; 200 TCP 5432 from 10.30.2.0/24; 300 deny everything else from 10.30.2.0/24. Ports 80/443 deliberately not open until go-live | ₹0 | Verified |
| 7 | 2026-11-09 | Runner NSG inbound: 100 TCP 22 from 10.30.1.0/24; 300 deny VirtualNetwork. Outbound: 100 TCP 5432 to 10.30.1.0/24; 300 deny Internet; 310 deny VirtualNetwork. The portal's warnings on inbound 300 (Azure Load Balancer, VNet) are expected: the runner sits behind no load balancer | ₹0 | Verified |
| 8 | 2026-11-09 | NSGs associated: `app` → codeadapt-app-nsg, `runner` → codeadapt-runner-nsg | ₹0 | Verified |
| 9 | 2026-11-09 | `release-images` run on `main` 8125461 green; IMAGE_TAG `sha-812546187529`; four packages public (anonymous pull returns 200) | ₹0 | Verified |
| 10 | 2026-11-09 | Public IP `codeadapt-app-ip` (Standard, static), DNS name `codeadapt-pilot.centralindia.cloudapp.azure.com`; NIC `codeadapt-app-nic` 10.30.1.4 static, no NIC NSG; new SSH key `codeadapt-key` (ed25519, not Relay's) | ~₹310/month | Verified |
| 11 | 2026-11-09 | `codeadapt-app-vm` Standard_B2pts_v2, Ubuntu 24.04 Arm64, Premium SSD; security type Standard (**B2pts v2 does not support Trusted launch**; the first attempt failed and created nothing); boot diagnostics on | free hours | Verified |
| 12 | 2026-11-09 | App VM setup: updates, unattended upgrades, 1 GiB swap, Docker 29.9.3 + Compose v5.7.0, checkout at 8125461, host firewall service (`ROLE=app`), api + proxy pulled by digest (arm64, built from 812546187529) | ₹0 | Verified |
| 13 | 2026-11-09 | Database TLS certificates made; `ca.key` copied to the owner's laptop and shredded on the VM (only `ca.crt`, `server.crt`, `server.key` 640 root:70 remain); `app.env` chmod 600, three 64-character hex passwords, no placeholder | ₹0 | Verified |
| 14 | 2026-11-09 | `PermitRootLogin no` (`/etc/ssh/sshd_config.d/10-codeadapt.conf`); `verify-host.sh app`: all checks passed | ₹0 | Verified |
| 15 | 2026-11-09 | Go-live: NSG `Allow-HTTP` 110 and `Allow-HTTPS` 120 from Internet; stack up with `--no-build`. Checks: valid certificate (curl without `-k`), HSTS, CSP, X-Frame-Options DENY, nosniff; `/api/v1/ready` → ready; http → 308 https; `codeadapt-admin status` ok, schema 0006; `verify-host.sh app` all passed incl. 443 listening and PostgreSQL on 10.30.1.4 only; a failed login is recorded in `audit_events.client` with the caller's public address, not the proxy's 172.30.0.10 | ₹0 | Verified |
| 16 | 2026-11-09 | Runner: NIC `codeadapt-runner-nic` 10.30.2.4 static; `codeadapt-runner-vm` Standard_B2ats_v2, Ubuntu 24.04 x64, Standard SSD 32 GiB, security type Standard, **no public IP**, auto-shutdown 23:00 IST, boot diagnostics | ~₹210/month + ~₹1/h | Verified |
| 17 | 2026-11-09 | Installation window (temporary IP + NSG `Allow-install-tmp`), then closed: updates, 1 GiB swap, Docker, checkout at 8125461, host firewall (`ROLE=runner`), `bzip2` (missing from Azure's image), gVisor release-20261005.0 (checksum OK, registered as `runsc`), worker + sandbox pulled by digest (amd64, built from 812546187529). Rule and temporary IP deleted afterwards | ~₹0.40/h while open | Verified |
| 18 | 2026-11-09 | `ca.crt` copied to the runner (same SHA-256 on both VMs); `runner.env` chmod 600 root, worker password copied VM to VM without display (64 characters), `SANDBOX_MAX_CONCURRENCY=1`, `IMAGE_TAG=sha-812546187529` | ₹0 | Verified |
| 19 | 2026-11-09 | gVisor L3 steps 1, 2 and 4 on the runner: kernel 7.0.0-1017-azure x86_64, runsc release-20261005.0 registered; a sandbox container under `--runtime runsc` prints gVisor's own boot log ("Starting gVisor...") | ₹0 | Verified |
| 20 | 2026-11-09 | gVisor L3 step 3: with `CODEADAPT_SANDBOX_RUNTIME` empty, the production worker exits 1 with "production requires CODEADAPT_SANDBOX_RUNTIME=runsc (gVisor)" before touching any job | ₹0 | Verified |
| 21 | 2026-11-09 | `PermitRootLogin no` on the runner; `verify-host.sh runner`: all checks passed (host and container egress blocked, outside DNS blocked, metadata blocked, database port reachable, no public IP, not in maintenance mode) | ₹0 | Verified |

Notes from these steps:

- `verify-host.sh` failed "root login" on both VMs because `sshd -T` prints
  `prohibit-password` as `without-password`; the script now accepts both, and both VMs set
  `PermitRootLogin no` anyway.
- The owner's mobile connection changes its public IPv4 every few minutes, so SSH is done
  from Azure Cloud Shell, whose address is fixed while the session lasts; the SSH rule is
  set to that address (`/32`) and updated when Cloud Shell restarts. The runner is reached
  through the App VM (`ProxyJump`).

## Not done yet (in order)

- [x] Steps A–C and the runner host (Step D up to `verify-host.sh runner`): see steps 9–21.
- [ ] gVisor level L3 steps 5 (sandbox suite on the host), 6 and 7 (end-to-end with
      `container_runtime: runsc`). Until all pass, gVisor is **not** fully verified on the host.
- [ ] Runner worker started, warm-up, end-to-end submission (runbook §2 steps 8–9).
- [ ] Database TLS on the hosts, backups and restore drill, monitoring (runbook §2–§4).
- [ ] Gate C (ethics, real students). Not started; no real student may be enrolled before it.
