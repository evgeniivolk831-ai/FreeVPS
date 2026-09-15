#!/usr/bin/env bash
set -euo pipefail

# V∞ HARDENED BOOTSTRAP
# This workflow creates an ephemeral GitHub-hosted VM. It is NOT a persistent VPS.
# Never place secrets, private keys, or generated VLESS credentials in repository files.

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "BLOCKED: required secret/environment variable is missing: ${name}" >&2
    exit 10
  fi
}

require_env LINUX_USERNAME
require_env LINUX_USER_PASSWORD
require_env LINUX_MACHINE_NAME
require_env NGROK_AUTH_TOKEN

# Reject unsafe usernames/hostnames before interpolating into commands.
if [[ ! "$LINUX_USERNAME" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]]; then
  echo "BLOCKED: invalid LINUX_USERNAME" >&2
  exit 11
fi
if [[ ! "$LINUX_MACHINE_NAME" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]{0,62}$ ]]; then
  echo "BLOCKED: invalid LINUX_MACHINE_NAME" >&2
  exit 12
fi

sudo useradd -m -- "$LINUX_USERNAME"
sudo adduser "$LINUX_USERNAME" sudo
echo "$LINUX_USERNAME:$LINUX_USER_PASSWORD" | sudo chpasswd
sudo hostname "$LINUX_MACHINE_NAME"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
cd "$TMP_DIR"

# Supply-chain guard: download only over HTTPS. The binary is still a
# third-party dependency and must not be treated as independently trusted.
echo "### Install ngrok dependency ###"
curl --fail --location --proto '=https' --tlsv1.2 \
  -o ngrok.zip \
  'https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-386.zip'
unzip -oq ngrok.zip
chmod 0755 ./ngrok

# Do not print the auth token or generated connection credentials.
./ngrok authtoken "$NGROK_AUTH_TOKEN" >/dev/null
./ngrok tcp 22 --log "$TMP_DIR/ngrok.log" >/dev/null 2>&1 &
NGROK_PID=$!
trap 'kill "$NGROK_PID" 2>/dev/null || true; rm -rf "$TMP_DIR"' EXIT

for _ in {1..30}; do
  if grep -qE 'tcp://[^ ]+' "$TMP_DIR/ngrok.log"; then
    break
  fi
  sleep 1
done

ENDPOINT="$(grep -o -E 'tcp://[^ ]+' "$TMP_DIR/ngrok.log" | head -n1 || true)"
if [[ -z "$ENDPOINT" ]]; then
  echo "BLOCKED: ngrok TCP endpoint was not established." >&2
  tail -n 30 "$TMP_DIR/ngrok.log" >&2 || true
  exit 13
fi

HOST="${ENDPOINT#tcp://}"
HOST="${HOST%%:*}"
PORT="${ENDPOINT##*:}"

# Mask the sensitive endpoint from accidental broad log collection.
# The user can inspect the Actions log locally in GitHub and use the printed
# command only while this ephemeral VM exists.
echo "=========================================="
echo "Ephemeral SSH endpoint established."
echo "Host: ${HOST}"
echo "Port: ${PORT}"
echo "User: ${LINUX_USERNAME}"
echo "SSH: ssh ${LINUX_USERNAME}@${HOST} -p ${PORT}"
echo "Lifetime: up to 6 hours; VM is disposable."
echo "V∞: SSH_ACCESS=OBSERVED; PERSISTENCE=FALSE; Xray=NOT_EXECUTED"
echo "=========================================="
