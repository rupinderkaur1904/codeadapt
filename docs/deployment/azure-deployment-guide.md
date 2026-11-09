# Azure deployment guide (Milestone 4)

Status: **prepared, not yet executed beyond the free network foundation.** Every paid step
below needs the owner's explicit approval, with its cost shown, at the moment it is done.
What has actually been done, with evidence, is recorded in
[m4-deployment-progress.md](m4-deployment-progress.md). The general procedure stays
[production-runbook.md](production-runbook.md); this guide is its Azure-specific form.

## Ground rules

- **Relay (resource group `relay-rg`) is never touched**: not its VM, database, VNet, NSG,
  public IP, DNS zone, keys or secrets. When a portal form pre-selects `relay-vnet`,
  `relay-nsg` or `relay-rg`, change it.
- Everything for CodeAdapt goes in `codeadapt-rg`, Central India, tag `project=codeadapt`.
- No secret goes into GitHub, a screenshot, a chat message or a log. Passwords are made on
  the VM with `openssl rand -base64 32` and stay in `chmod 600` files there.
- The VMs never build images. CI builds them (`release-images` workflow) and the VMs pull
  them by digest with `deploy/pull-images.sh`.
- Never click "Upgrade" to pay-as-you-go.

## Architecture (approved 2026-11-09)

```
Internet ──443/80 (opened at go-live)──> codeadapt-app-ip (public IP, ~₹310/month)
                                             │
codeadapt-vnet 10.30.0.0/16 (not peered with relay-vnet)
├── subnet app 10.30.1.0/24, NSG codeadapt-app-nsg
│     codeadapt-app-vm  B2pts v2 (Arm64, 2 vCPU, 1 GiB, free hours)  10.30.1.4
│       Caddy (TLS) → API → PostgreSQL 16 (TLS, private address only)
└── subnet runner 10.30.2.0/24, NSG codeadapt-runner-nsg
      codeadapt-runner-vm  B2ats v2 (x86-64, 2 vCPU, 1 GiB, paid, on only for sessions)
        10.30.2.4, no public IP; worker + Docker + gVisor; egress: database port only
```

The runner must be x86-64: the fingerprints were measured there.

## Step A. Release images (Claude, in GitHub; free)

1. The owner merges the deployment-files pull request after review.
2. The `release-images` workflow runs on `main`. Its run summary shows a block
   `release-images.env`, with one digest per image and the commit it was built from.
3. **Owner decision:** GHCR packages start private. Either make the four packages
   `codeadapt-api`, `codeadapt-proxy`, `codeadapt-worker` and `codeadapt-sandbox` public
   (GitHub → your profile → Packages → package → Package settings → Change visibility),
   which is the recommended option because the repository is already public and the
   images hold no secret, or keep them private and log in on each VM with a read-only
   token (one more secret per VM to protect).

## Step B. App VM (paid: public IP ~₹310/month; VM and 64 GiB P6 disk free)

Portal → Virtual machines → Create → Azure virtual machine.

| Tab | Field | Value |
| --- | --- | --- |
| Basics | Resource group | `codeadapt-rg` |
| | Name | `codeadapt-app-vm` |
| | Region | (Asia Pacific) Central India |
| | Availability options | No infrastructure redundancy required |
| | Security type | Trusted launch |
| | Image | Ubuntu Server 24.04 LTS, **Arm64** |
| | Size | **Standard_B2pts_v2** (shown as free-services eligible) |
| | Authentication | SSH public key, a **new** key pair named `codeadapt-key` (never Relay's) |
| | Username | `azureuser` |
| | Public inbound ports | **None** (the subnet NSG decides) |
| Disks | OS disk | Premium SSD, **64 GiB (P6)**, delete with VM |
| Networking | Virtual network | **codeadapt-vnet** (not relay-vnet) |
| | Subnet | `app` |
| | Public IP | Create new: `codeadapt-app-ip`, Standard, static |
| | NIC network security group | **None** (codeadapt-app-nsg is on the subnet) |
| | Delete public IP and NIC with VM | ticked |
| Management | Auto-shutdown | off (the website must stay up) |
| Monitoring | Boot diagnostics | Enable with managed storage account |
| Tags | project | `codeadapt` |

Keep the downloaded private key file safe; it is never uploaded anywhere.

After creation:

1. NIC → IP configurations → ipconfig1 → Assignment **Static**, address `10.30.1.4`.
2. Public IP `codeadapt-app-ip` → Configuration → DNS name label, e.g. `codeadapt-pilot`.
   The site name becomes `codeadapt-pilot.centralindia.cloudapp.azure.com` (free). A
   custom domain is optional and an owner decision.

## Step C. Set up the App VM

SSH from your laptop: `ssh -i codeadapt-key.pem azureuser@<app public IP>`.

```
# 1. Updates, and 1 GiB of swap (1 GiB RAM is tight for PostgreSQL + API + Caddy)
sudo apt-get update && sudo apt-get -y upgrade
cat /etc/apt/apt.conf.d/20auto-upgrades        # both lines should end in "1"
sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile
sudo swapon /swapfile && echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 2. Docker Engine + Compose plugin from Docker's own repository
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 3. The code, at the released commit
sudo git clone https://github.com/rupinderkaur1904/codeadapt.git /opt/codeadapt
cd /opt/codeadapt && sudo git checkout <REVISION from release-images.env>

# 4. Host firewall (container rules; see deploy/host/firewall.sh)
sudo mkdir -p /etc/codeadapt
sudo cp deploy/host/firewall.env.example /etc/codeadapt/firewall.env
sudo nano /etc/codeadapt/firewall.env            # ROLE=app, APP_PRIVATE_IP=10.30.1.4, RUNNER_SUBNET=10.30.2.0/24
sudo cp deploy/host/codeadapt-firewall.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now codeadapt-firewall

# 5. Images by digest
sudo nano /opt/codeadapt/release-images.env      # paste the block from the workflow run
sudo deploy/pull-images.sh app release-images.env

# 6. Database TLS (runbook §1 step 5), then settings
sudo deploy/db-tls/make-db-certs.sh /etc/codeadapt/db-tls db.codeadapt.internal
sudo cp deploy/app.env.example deploy/app.env && sudo chmod 600 deploy/app.env
sudo nano deploy/app.env     # SITE_HOST=<the DNS name>, DB_PRIVATE_BIND=10.30.1.4, IMAGE_TAG=<printed>,
                             # each password from: openssl rand -base64 32
```

Move `ca.key` off the VM (runbook §1 step 5) before going further.

Check the host: `sudo deploy/host/verify-host.sh app`. Every line should read PASS (443
shows SKIP until the stack runs). Paste the output into the progress record.

**Go-live gate (owner approval):** add the inbound NSG rules to `codeadapt-app-nsg`,
TCP 80 and TCP 443 from Internet (priorities 110 and 120). Then start the stack:

```
sudo docker compose -f deploy/compose.app.yaml --env-file deploy/app.env up -d --no-build
```

Then run the runbook §1 step 8 checks (valid certificate without `-k`, headers, readiness,
redirect, `codeadapt-admin status`, forwarded client address) and record the outputs.

## Step D. Runner VM (paid: ~₹210/month disk + ~₹1 per running hour; no public IP)

Same wizard as Step B, except:

| Field | Value |
| --- | --- |
| Name | `codeadapt-runner-vm` |
| Image | Ubuntu Server 24.04 LTS, **x64** |
| Size | **Standard_B2ats_v2** |
| SSH key | Use existing key `codeadapt-key` |
| OS disk | Standard SSD, 32 GiB |
| Subnet | `runner` |
| Public IP | **None** |
| Auto-shutdown | **On**, e.g. 23:00 IST, as a safety net |

NIC → IP configurations → Static `10.30.2.4`.

**Installation window (temporary internet access).** The runner has no route to the
internet, which is the point. To install packages once:

1. Create a temporary public IP `codeadapt-runner-tmp-ip` (Standard) and attach it to the
   runner's NIC (ipconfig1 → Associate public IP). About ₹0.40 per hour.
2. Add a temporary outbound rule to `codeadapt-runner-nsg`: `Allow-install-tmp`, priority
   250, destination Service Tag Internet, TCP 80,443, Allow.

SSH through the App VM (the runner accepts SSH from the app subnet only):
`ssh -i codeadapt-key.pem -J azureuser@<app public IP> azureuser@10.30.2.4`. If `-J` does not
pick up the key, add the key with `ssh-add` first.

```
sudo apt-get update && sudo apt-get -y upgrade
# Docker exactly as Step C.2, then:
sudo git clone https://github.com/rupinderkaur1904/codeadapt.git /opt/codeadapt
cd /opt/codeadapt && sudo git checkout <REVISION>
sudo mkdir -p /etc/codeadapt
sudo cp deploy/host/firewall.env.example /etc/codeadapt/firewall.env
sudo nano /etc/codeadapt/firewall.env            # ROLE=runner, DB_HOST=10.30.1.4, APP_SUBNET=10.30.1.0/24
sudo cp deploy/host/codeadapt-firewall.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo deploy/host/firewall.sh maintenance-on      # egress closed except 80/443
sudo systemctl enable --now codeadapt-firewall
sudo deploy/host/install-gvisor.sh
sudo nano release-images.env && sudo deploy/pull-images.sh runner release-images.env
sudo deploy/host/firewall.sh maintenance-off
```

Then close the window: delete the NSG rule `Allow-install-tmp`, dissociate and delete
`codeadapt-runner-tmp-ip`.

Copy `ca.crt` (public) from the App VM to `/etc/codeadapt/db-tls/ca.crt`, create
`deploy/runner.env` from the example (`chmod 600`; worker password from `app.env`,
`DB_HOST=10.30.1.4`, `DOCKER_SOCKET_GID=$(stat -c %g /var/run/docker.sock)`,
`SANDBOX_MAX_CONCURRENCY=1`, `IMAGE_TAG` as printed).

Checks, each output recorded:

1. `sudo deploy/host/verify-host.sh runner`: all PASS, including "no public IP" and
   "egress blocked".
2. gVisor level L3, [gvisor-verification.md](gvisor-verification.md), all steps. Step 5
   (the sandbox suite on the host) needs a second installation window. **Stop if any step
   fails.**
3. Start: `sudo docker compose -f deploy/compose.runner.yaml --env-file deploy/runner.env up -d --no-build`,
   then the warm-up, the end-to-end submission and the database TLS checks (runbook §2
   steps 8 to 10).

## Step E. Running sessions on a session-only runner

- **Before a session:** portal → `codeadapt-runner-vm` → Start. Wait about 2 minutes,
  then run the runbook §5 checklist.
- **After a session:** wait until `codeadapt-admin status` shows no queued job, then
  portal → Stop. The status must read **Stopped (deallocated)**; only then do compute
  charges stop (the disk is still charged).
- Submissions made while the runner is off stay queued and are evaluated when it starts.

## Security updates on the runner

The runner cannot reach the package mirrors outside an installation window. Open one
(Step D) about once a month and before the pilot, run `sudo apt-get update && sudo apt-get
-y upgrade`, then close it again and re-run `verify-host.sh runner`.
