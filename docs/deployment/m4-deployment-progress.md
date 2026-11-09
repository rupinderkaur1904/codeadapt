# Milestone 4 deployment progress (Azure)

The living record of what has actually been done on Azure for CodeAdapt, with the evidence
for each step. It holds **no secrets**: no passwords, keys, tokens, connection strings or
subscription identifiers. Plan: [azure-deployment-guide.md](azure-deployment-guide.md).

Each step is done by the owner in the Azure portal, guided step by step; the evidence is
the owner's screenshot, checked before the next step. "Verified" below means that check,
not an automated test.

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

## Not done yet (in order)

- [ ] Deployment-files pull request reviewed and merged by the owner; `release-images` run
      green on `main`; package visibility decided (guide, Step A).
- [ ] App VM and its public IP (guide, Step B). Paid: needs owner approval at that moment.
- [ ] App VM setup and `verify-host.sh app` output (Step C).
- [ ] Go-live gate: NSG 80/443, TLS on the real name (Step C). Owner approval.
- [ ] Runner VM, installation window, `verify-host.sh runner` output (Step D). Paid.
- [ ] gVisor level L3 on the runner. Until it passes, gVisor is **not** verified on a host.
- [ ] Database TLS on the hosts, backups and restore drill, monitoring (runbook §2–§4).
- [ ] Gate C (ethics, real students). Not started; no real student may be enrolled before it.
