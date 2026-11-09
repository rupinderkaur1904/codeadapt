#!/usr/bin/env bash
# Read-only checks of a CodeAdapt VM (Milestone 4). Prints PASS / FAIL / SKIP per check and
# exits 1 if anything failed. Changes nothing, prints no secret, and is safe to re-run.
# Paste its full output into docs/deployment/m4-deployment-progress.md as evidence.
#
#   sudo deploy/host/verify-host.sh app
#   sudo deploy/host/verify-host.sh runner
#
# It covers the host (architecture, updates, SSH, Docker, firewall, egress, metadata). The
# application checks (TLS on the public name, database TLS, gVisor level L3, end-to-end) are
# the separate steps in docs/deployment/azure-deployment-guide.md and gvisor-verification.md.
set -uo pipefail

role=${1:-}
case "$role" in app | runner) ;; *) echo "usage: $0 <app|runner>" >&2; exit 2 ;; esac
[ "$(id -u)" = 0 ] || { echo "run as root (sudo)" >&2; exit 2; }

failures=0
pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; failures=$((failures + 1)); }
skip() { printf 'SKIP  %s\n' "$1"; }
check() { # check "<description>" <command...>
  local d=$1; shift
  if "$@" >/dev/null 2>&1; then pass "$d"; else fail "$d"; fi
}
setting() { grep -E "^$1=" /etc/codeadapt/firewall.env 2>/dev/null | tail -n 1 | cut -d= -f2-; }
# A TCP connection attempt with a short timeout, from the host.
tcp_open() { timeout 5 bash -c "exec 3<>/dev/tcp/$1/$2" 2>/dev/null; }

echo "CodeAdapt host verification: role=$role host=$(hostname) $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "kernel: $(uname -srm)"
echo "os: $(. /etc/os-release && echo "$PRETTY_NAME")"
echo "memory: $(free -m | awk '/^Mem:/ {print $2 " MiB"}'), swap: $(free -m | awk '/^Swap:/ {print $2 " MiB"}')"
echo "disk /: $(df -h / | awk 'NR==2 {print $4 " free of " $2}')"
echo

# ---------------------------------------------------------------- architecture
arch=$(uname -m)
if [ "$role" = runner ]; then
  [ "$arch" = x86_64 ] && pass "architecture x86_64 (fingerprints were measured on x86-64)" \
    || fail "architecture is $arch; the runner must be x86_64"
else
  [ "$arch" = aarch64 ] && pass "architecture aarch64 (B2pts v2)" \
    || skip "architecture is $arch (the plan is aarch64; x86_64 also works)"
fi

# ---------------------------------------------------------------- updates and SSH
check "unattended security upgrades enabled" \
  grep -Eq 'APT::Periodic::Unattended-Upgrade "1"' /etc/apt/apt.conf.d/20auto-upgrades
sshd_value() { sshd -T 2>/dev/null | awk -v k="$1" '$1 == k {print $2}'; }
[ "$(sshd_value passwordauthentication)" = no ] && pass "SSH password login disabled" \
  || fail "SSH password login is not disabled"
[ "$(sshd_value permitrootlogin)" = no ] || [ "$(sshd_value permitrootlogin)" = prohibit-password ] \
  && pass "SSH root password login refused" || fail "SSH root login allowed with a password"

# ---------------------------------------------------------------- Docker
check "Docker daemon running" docker info
check "Docker Compose plugin present" docker compose version
check "firewall boot service enabled" systemctl is-enabled codeadapt-firewall
check "firewall rules loaded (DOCKER-USER -> CODEADAPT-CONTAINERS)" \
  iptables -C DOCKER-USER -j CODEADAPT-CONTAINERS

# Probe from inside a container on the default bridge, the path a compromised container
# would take. Uses an image already on this host; nothing is pulled.
probe_image=""
for img in "codeadapt-worker" "codeadapt-api"; do
  probe_image=$(docker image ls --format '{{.Repository}}:{{.Tag}}' "$img" 2>/dev/null | head -n 1)
  [ -n "$probe_image" ] && break
done
container_can_reach() { # host port
  docker run --rm --network bridge --entrypoint python "$probe_image" -c \
    "import socket,sys; s=socket.socket(); s.settimeout(4); sys.exit(0 if s.connect_ex(('$1',$2))==0 else 1)" \
    >/dev/null 2>&1
}
if [ -n "$probe_image" ]; then
  container_can_reach 169.254.169.254 80 && fail "a container can reach the Azure metadata service" \
    || pass "containers cannot reach the Azure metadata service"
else
  skip "container metadata probe (no codeadapt image pulled yet)"
fi

# ---------------------------------------------------------------- role-specific
if [ "$role" = runner ]; then
  db_host=$(setting DB_HOST)
  docker info --format '{{json .Runtimes}}' 2>/dev/null | grep -q '"runsc"' \
    && pass "gVisor runsc registered with Docker" || fail "runsc is not registered with Docker"
  v=$(/usr/local/bin/runsc --version 2>/dev/null | awk '/^runsc version/ {print $3}')
  [ "$v" = release-20261005.0 ] && pass "runsc version $v (the CI pin)" \
    || fail "runsc version is '${v:-missing}', expected release-20261005.0"
  if docker image inspect codeadapt-sandbox:gcc14.2-1 >/dev/null 2>&1; then
    pass "sandbox image codeadapt-sandbox:gcc14.2-1 present"
  else
    fail "sandbox image missing (deploy/pull-images.sh runner ...)"
  fi
  if [ -e /run/codeadapt-firewall.maintenance ]; then
    fail "firewall is in MAINTENANCE mode (run firewall.sh maintenance-off)"
  else
    pass "firewall not in maintenance mode"
  fi
  tcp_open example.com 443 && fail "the host can reach the internet (example.com:443)" \
    || pass "host egress to the internet is blocked"
  tcp_open 1.1.1.1 53 && fail "the host can reach an outside DNS server" \
    || pass "host cannot reach outside DNS servers"
  if [ -n "$probe_image" ]; then
    container_can_reach 1.1.1.1 443 && fail "a container can reach the internet" \
      || pass "containers cannot reach the internet"
  fi
  if [ -n "$db_host" ]; then
    tcp_open "$db_host" 5432 && pass "database port $db_host:5432 reachable" \
      || fail "database port $db_host:5432 not reachable (App VM down, or a rule is wrong)"
  else
    fail "DB_HOST not set in /etc/codeadapt/firewall.env"
  fi
  # The runner must have no public address (metadata read by root on the host only).
  pub=$(curl -s -m 5 -H Metadata:true \
    "http://169.254.169.254/metadata/instance/network/interface/0/ipv4/ipAddress/0/publicIpAddress?api-version=2021-02-01&format=text" || true)
  [ -z "$pub" ] && pass "no public IP address on the runner" \
    || fail "the runner has a public IP address (remove it after installation)"
else
  private_ip=$(setting APP_PRIVATE_IP)
  listeners=$(ss -Hltn | awk '{print $4}')
  echo "$listeners" | grep -Eq '(^|:)443$' && pass "port 443 listening" || skip "port 443 not listening yet"
  if echo "$listeners" | grep -Eq '^(0\.0\.0\.0|\*|\[::\]):5432$'; then
    fail "PostgreSQL is published on all addresses; it must bind to the private address only"
  elif [ -n "$private_ip" ] && echo "$listeners" | grep -q "^$private_ip:5432$"; then
    pass "PostgreSQL published on the private address $private_ip only"
  else
    skip "PostgreSQL not published yet"
  fi
  extra=$(echo "$listeners" | grep -Ev '(:22|:80|:443|:5432|:53)$' | grep -Ev '^(127\.|\[::1\])' || true)
  [ -z "$extra" ] && pass "no unexpected listening ports" \
    || fail "unexpected listening ports: $(echo "$extra" | tr '\n' ' ')"
fi

echo
if [ "$failures" -eq 0 ]; then
  echo "RESULT: all checks passed ($role)"
else
  echo "RESULT: $failures check(s) FAILED ($role)"
  exit 1
fi
