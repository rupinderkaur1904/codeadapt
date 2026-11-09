#!/usr/bin/env bash
# Install the PINNED gVisor release on the runner VM, checksum verified, exactly as the
# sandbox-gvisor CI job does (.github/workflows/ci.yml; a unit test keeps the two pins
# equal). Then register runsc with Docker and restart Docker.
#
#   sudo deploy/host/firewall.sh maintenance-on    # needs outbound 443 for the download
#   sudo deploy/host/install-gvisor.sh
#   sudo deploy/host/firewall.sh maintenance-off
set -euo pipefail

GVISOR_RELEASE="20261005"
GVISOR_SHA512="79869ae9a589355a46d46fdac068d9a954e741741ffe77c64e38c56ea955498c1cb04e9bce44e1cce5155333e6b76bee72347c6661bb7c78fd2fe3aad198c8fe"

[ "$(id -u)" = 0 ] || { echo "run as root" >&2; exit 1; }
[ "$(uname -m)" = x86_64 ] || { echo "the runner must be x86-64 (fingerprints were measured there)" >&2; exit 1; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cd "$work"
curl -fsSLO "https://storage.googleapis.com/gvisor/releases/release/${GVISOR_RELEASE}/x86_64/gvisor.tar.bz2"
echo "${GVISOR_SHA512}  gvisor.tar.bz2" | sha512sum -c -
mkdir gvisor && tar -xjf gvisor.tar.bz2 -C gvisor
install -m 755 gvisor/runsc gvisor/containerd-shim-runsc-v1 /usr/local/bin/
mkdir -p /usr/local/bin/gvisor-bin && install -m 755 gvisor/gvisor-bin/* /usr/local/bin/gvisor-bin/
/usr/local/bin/runsc install
systemctl restart docker
docker info --format '{{json .Runtimes}}' | grep -q runsc
echo "gVisor ${GVISOR_RELEASE} installed and registered with Docker as runsc."
echo "Next: docs/deployment/gvisor-verification.md level L3, then deploy/host/verify-host.sh runner."
