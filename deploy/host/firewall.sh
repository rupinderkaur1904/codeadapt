#!/usr/bin/env bash
# Host firewall for the CodeAdapt VMs (Milestone 4). Defence in depth BEHIND the Azure NSGs,
# never instead of them: Docker-published ports and container traffic bypass ufw, so the
# container rules go in Docker's DOCKER-USER chain.
#
#   sudo deploy/host/firewall.sh apply            # (re)build the rules; idempotent
#   sudo deploy/host/firewall.sh maintenance-on   # runner only: allow 80/443 out (installs)
#   sudo deploy/host/firewall.sh maintenance-off  # runner only: lock egress again
#   sudo deploy/host/firewall.sh show
#
# Settings come from /etc/codeadapt/firewall.env (no secrets; see firewall.env.example).
# Installed as a boot service by deploy/host/codeadapt-firewall.service.
#
# Runner VM: untrusted code runs here, so egress is closed.
#   containers (worker): may reach only DB_HOST:5432; everything else, including the Azure
#     metadata service 169.254.169.254, is dropped. Sandboxes run with --network none.
#   host: out only to the Azure platform address 168.63.129.16 (DNS, VM agent), the metadata
#     service for root (the Azure agent), DB_HOST:5432, and 80/443 in maintenance mode.
#     In: SSH from APP_SUBNET and the Azure platform address only.
# App VM:
#   containers: the published database port answers RUNNER_SUBNET only; no container may
#     reach the metadata service, or 168.63.129.16 except for DNS. The proxy keeps internet
#     access (Let's Encrypt).
#
# Recovery if SSH is lost: Azure portal -> the VM -> Help -> Serial console (or Run command):
#   iptables -D INPUT -j CODEADAPT-IN
set -euo pipefail

CONFIG=${CODEADAPT_FIREWALL_ENV:-/etc/codeadapt/firewall.env}
MAINT_FLAG=/run/codeadapt-firewall.maintenance
AZURE_PLATFORM=168.63.129.16
METADATA=169.254.169.254

die() { echo "firewall: $*" >&2; exit 1; }
[ "$(id -u)" = 0 ] || die "run as root"
[ -r "$CONFIG" ] || die "missing $CONFIG (copy deploy/host/firewall.env.example)"

setting() {
  local v
  v=$(grep -E "^$1=" "$CONFIG" | tail -n 1 | cut -d= -f2- || true)
  [ -n "$v" ] || die "$CONFIG has no $1"
  printf '%s' "$v"
}
cidr_ok() { [[ $1 =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}(/[0-9]{1,2})?$ ]] || die "not an IPv4 address/CIDR: $1"; }

ROLE=$(setting ROLE)
case "$ROLE" in app | runner) ;; *) die "ROLE must be app or runner" ;; esac

# A chain of our own, emptied and refilled, linked once from the parent chain.
chain() {
  local parent=$1 name=$2
  iptables -N "$name" 2>/dev/null || true
  iptables -F "$name"
  iptables -C "$parent" -j "$name" 2>/dev/null || iptables -I "$parent" 1 -j "$name"
}

docker_user() {
  # Docker creates DOCKER-USER when it starts; make sure it exists even before that.
  iptables -N DOCKER-USER 2>/dev/null || true
  chain DOCKER-USER CODEADAPT-CONTAINERS
}

apply_runner() {
  local db_host app_subnet
  db_host=$(setting DB_HOST); cidr_ok "$db_host"
  app_subnet=$(setting APP_SUBNET); cidr_ok "$app_subnet"

  docker_user
  local c=CODEADAPT-CONTAINERS
  iptables -A $c -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
  iptables -A $c -p tcp -d "$db_host" --dport 5432 -j RETURN
  iptables -A $c -j DROP

  chain OUTPUT CODEADAPT-OUT
  local o=CODEADAPT-OUT
  iptables -A $o -o lo -j RETURN
  iptables -A $o -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
  iptables -A $o -d $AZURE_PLATFORM -j RETURN
  iptables -A $o -d $METADATA -m owner --uid-owner 0 -j RETURN
  iptables -A $o -p tcp -d "$db_host" --dport 5432 -j RETURN
  if [ -e $MAINT_FLAG ]; then
    iptables -A $o -p tcp -m multiport --dports 80,443 -j RETURN
    echo "firewall: MAINTENANCE MODE - outbound 80/443 open; run maintenance-off when done"
  fi
  iptables -A $o -j REJECT

  chain INPUT CODEADAPT-IN
  local i=CODEADAPT-IN
  iptables -A $i -i lo -j RETURN
  iptables -A $i -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
  iptables -A $i -s $AZURE_PLATFORM -j RETURN
  iptables -A $i -p tcp -s "$app_subnet" --dport 22 -j RETURN
  iptables -A $i -p icmp -j RETURN
  iptables -A $i -j DROP
}

apply_app() {
  local private_ip runner_subnet
  private_ip=$(setting APP_PRIVATE_IP); cidr_ok "$private_ip"
  runner_subnet=$(setting RUNNER_SUBNET); cidr_ok "$runner_subnet"

  docker_user
  local c=CODEADAPT-CONTAINERS
  iptables -A $c -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
  # The published database port (bound to the private address) answers the runner only.
  iptables -A $c -p tcp -m conntrack --ctorigdst "$private_ip" --ctorigdstport 5432 -s "$runner_subnet" -j RETURN
  iptables -A $c -p tcp -m conntrack --ctorigdst "$private_ip" --ctorigdstport 5432 -j DROP
  # No container may read the VM's metadata (identity, network, custom data).
  iptables -A $c -d $METADATA -j DROP
  iptables -A $c -d $AZURE_PLATFORM -p udp --dport 53 -j RETURN
  iptables -A $c -d $AZURE_PLATFORM -p tcp --dport 53 -j RETURN
  iptables -A $c -d $AZURE_PLATFORM -j DROP
  iptables -A $c -j RETURN
}

show() {
  for t in CODEADAPT-CONTAINERS CODEADAPT-OUT CODEADAPT-IN; do
    iptables -S "$t" 2>/dev/null || true
  done
}

case "${1:-}" in
  apply)
    "apply_$ROLE"
    echo "firewall: $ROLE rules applied"
    ;;
  maintenance-on | maintenance-off)
    [ "$ROLE" = runner ] || die "maintenance mode is for the runner only"
    if [ "$1" = maintenance-on ]; then touch $MAINT_FLAG; else rm -f $MAINT_FLAG; fi
    apply_runner
    echo "firewall: runner rules applied (${1})"
    ;;
  show) show ;;
  *) echo "usage: $0 apply|maintenance-on|maintenance-off|show" >&2; exit 2 ;;
esac
