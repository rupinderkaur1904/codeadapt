#!/usr/bin/env bash
# Pull this release's images by digest onto a VM and give them the local names the Compose
# files use (Milestone 4: the 1 GiB VMs never build images).
#
#   sudo deploy/pull-images.sh app    release-images.env   # App VM: api + proxy
#   sudo deploy/pull-images.sh runner release-images.env   # Runner VM: worker + sandbox
#
# release-images.env comes from the `release-images` workflow run for the commit checked out
# here (run summary or artifact). It holds no secret. Each reference must be a GHCR digest;
# a tag alone is refused, so a re-pushed tag can never change what runs. The script also
# checks that every image was built from REVISION, and that REVISION is the commit checked
# out in this directory.
#
# Afterwards start Compose with --no-build and IMAGE_TAG set to the printed value.
set -euo pipefail

usage() { echo "usage: $0 <app|runner> <release-images.env>" >&2; exit 2; }
[ $# -eq 2 ] || usage
role=$1
manifest=$2
case "$role" in
  app) wanted="API PROXY" ;;
  runner) wanted="WORKER SANDBOX" ;;
  *) usage ;;
esac
[ -r "$manifest" ] || { echo "cannot read $manifest" >&2; exit 2; }

# Read KEY=VALUE lines only; never `source` a file that came from elsewhere.
value() {
  local v
  v=$(grep -E "^$1=" "$manifest" | tail -n 1 | cut -d= -f2-)
  [ -n "$v" ] || { echo "$manifest has no $1" >&2; exit 1; }
  printf '%s' "$v"
}

revision=$(value REVISION)
image_tag=$(value IMAGE_TAG)
[[ $revision =~ ^[0-9a-f]{40}$ ]] || { echo "REVISION is not a commit id" >&2; exit 1; }
[[ $image_tag =~ ^sha-[0-9a-f]{12}$ ]] || { echo "IMAGE_TAG is not sha-<12 hex>" >&2; exit 1; }

here=$(git -C "$(dirname "$0")/.." rev-parse HEAD 2>/dev/null || true)
if [ "$here" != "$revision" ]; then
  echo "This checkout is at ${here:-<not a git checkout>}, the images are for $revision." >&2
  echo "Check out the same commit first: git checkout $revision" >&2
  exit 1
fi

local_name() {
  case "$1" in
    API) echo "codeadapt-api:$image_tag" ;;
    PROXY) echo "codeadapt-proxy:$image_tag" ;;
    WORKER) echo "codeadapt-worker:$image_tag" ;;
    # The name the worker runs sandboxes with (execution/docker.py DEFAULT_IMAGE); the
    # image is built from the unchanged, research-frozen sandbox/Dockerfile.
    SANDBOX) echo "codeadapt-sandbox:gcc14.2-1" ;;
  esac
}

for key in $wanted; do
  ref=$(value "${key}_IMAGE")
  name=$(echo "$key" | tr '[:upper:]' '[:lower:]')
  if ! [[ $ref =~ ^ghcr\.io/[a-z0-9._-]+/codeadapt-${name}@sha256:[0-9a-f]{64}$ ]]; then
    echo "${key}_IMAGE must be ghcr.io/<owner>/codeadapt-${name}@sha256:<digest>: $ref" >&2
    exit 1
  fi
  echo "pulling $ref"
  docker pull --quiet "$ref" >/dev/null
  built_from=$(docker image inspect -f '{{ index .Config.Labels "org.opencontainers.image.revision" }}' "$ref")
  if [ "$built_from" != "$revision" ]; then
    echo "$ref was built from ${built_from:-<unknown>}, not $revision" >&2
    exit 1
  fi
  arch=$(docker image inspect -f '{{ .Architecture }}' "$ref")
  docker tag "$ref" "$(local_name "$key")"
  echo "  ok: $(local_name "$key") ($arch, built from ${revision:0:12})"
done

if [ "$role" = runner ]; then
  v=$(docker image inspect -f '{{ index .Config.Labels "org.codeadapt.sandbox.image-version" }}' codeadapt-sandbox:gcc14.2-1)
  [ "$v" = 1 ] || { echo "sandbox image-version label is '$v', expected 1" >&2; exit 1; }
fi

echo
echo "Done. Set IMAGE_TAG=$image_tag in deploy/${role}.env, then start with --no-build."
