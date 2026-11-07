#!/usr/bin/env bash
# PostgreSQL TLS certificates from a small private CA (owner decision R5, Gate B).
#
#   deploy/db-tls/make-db-certs.sh <out-dir> <db-tls-name> [server-days]
#
# <db-tls-name> is the name the runner VM uses for the database, for example
# db.codeadapt.internal. It never has to be in public DNS: the runner maps it to the App
# VM's private address (extra_hosts in compose.runner.yaml). The server certificate is
# valid for that name and for "db" (the Compose service name the API uses).
#
# Writes into <out-dir>, which must not already hold certificates:
#   ca.crt      the CA certificate: copy to both VMs (public, mode 644)
#   ca.key      the CA private key: MOVE IT OFF THE VM after running this (mode 600)
#   server.crt  the database server certificate (mode 644)
#   server.key  its private key, group 70 = postgres in the Alpine image (mode 640)
#
# Clients verify both the CA and the host name (sslmode=verify-full), so a certificate
# from any other CA, or for any other name, is refused.
set -euo pipefail
umask 077

out=${1:?usage: make-db-certs.sh <out-dir> <db-tls-name> [server-days]}
name=${2:?usage: make-db-certs.sh <out-dir> <db-tls-name> [server-days]}
days=${3:-397}
if [[ ! $name =~ ^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$ ]]; then
  echo "make-db-certs: not a host name: $name" >&2
  exit 2
fi
mkdir -p "$out"
for f in ca.key ca.crt server.key server.crt; do
  if [[ -e $out/$f ]]; then
    echo "make-db-certs: $out/$f exists; refusing to overwrite" >&2
    exit 1
  fi
done

openssl req -x509 -new -nodes -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
  -keyout "$out/ca.key" -out "$out/ca.crt" -days 1095 -sha256 \
  -subj "/CN=CodeAdapt database CA" \
  -addext "basicConstraints=critical,CA:TRUE,pathlen:0" \
  -addext "keyUsage=critical,keyCertSign,cRLSign" 2>/dev/null

openssl req -new -nodes -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
  -keyout "$out/server.key" -out "$out/server.csr" -subj "/CN=$name" 2>/dev/null
cat > "$out/server.ext" <<EXT
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:$name,DNS:db
EXT
openssl x509 -req -in "$out/server.csr" -CA "$out/ca.crt" -CAkey "$out/ca.key" \
  -CAcreateserial -out "$out/server.crt" -days "$days" -sha256 \
  -extfile "$out/server.ext" 2>/dev/null
rm -f "$out/server.csr" "$out/server.ext" "$out/ca.srl"

openssl verify -CAfile "$out/ca.crt" "$out/server.crt" >/dev/null
chmod 644 "$out/ca.crt" "$out/server.crt"
chmod 600 "$out/ca.key"
chmod 640 "$out/server.key"
# PostgreSQL accepts a key owned by root and readable by its group; in the Alpine image
# the postgres group is 70. Needs root; skipped (with a note) otherwise.
if [[ $(id -u) == 0 ]]; then
  chown 0:70 "$out/server.key"
else
  echo "make-db-certs: run 'sudo chown 0:70 $out/server.key' before starting PostgreSQL" >&2
fi
echo "make-db-certs: wrote $out (server certificate for $name and db, $days days)"
echo "make-db-certs: now move $out/ca.key off this machine; it is needed only to renew"
