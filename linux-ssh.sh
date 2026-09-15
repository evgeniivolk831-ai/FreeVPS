#!/usr/bin/env bash
set -euo pipefail

# V∞ HARDENED EPHEMERAL VLESS/REALITY BOOTSTRAP
# The GitHub-hosted VM is disposable and is NOT a persistent VPS.
# Secrets and generated private material never enter the repository.

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

if [[ ! "$LINUX_USERNAME" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]]; then
  echo "BLOCKED: invalid LINUX_USERNAME" >&2
  exit 11
fi
if [[ ! "$LINUX_MACHINE_NAME" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]{0,62}$ ]]; then
  echo "BLOCKED: invalid LINUX_MACHINE_NAME" >&2
  exit 12
fi

# Keep a normal sudo-capable user available for diagnostics if SSH is ever
# exposed by a separate tunnel. The VPN itself uses unprivileged TCP 8443.
sudo useradd -m -- "$LINUX_USERNAME"
sudo adduser "$LINUX_USERNAME" sudo
echo "$LINUX_USERNAME:$LINUX_USER_PASSWORD" | sudo chpasswd
sudo hostname "$LINUX_MACHINE_NAME"

TMP_DIR="$(mktemp -d)"
cleanup() {
  if [[ -n "${NGROK_PID:-}" ]]; then kill "$NGROK_PID" 2>/dev/null || true; fi
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT
cd "$TMP_DIR"

# -----------------------------
# 1. ngrok raw TCP tunnel
# -----------------------------
# The original project downloaded a 32-bit ngrok binary. GitHub's current
# Ubuntu runner is amd64, so use the amd64 build explicitly.
echo "### Install ngrok dependency ###"
curl --fail --location --proto '=https' --tlsv1.2 \
  -o ngrok.zip \
  'https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip'
unzip -oq ngrok.zip
chmod 0755 ./ngrok
./ngrok authtoken "$NGROK_AUTH_TOKEN" >/dev/null

# -----------------------------
# 2. Xray-core from official installer
# -----------------------------
# Download the installer to a file first; do not pipe a remote script to root.
echo "### Install Xray-core ###"
INSTALLER="$TMP_DIR/install-release.sh"
curl --fail --location --proto '=https' --tlsv1.2 \
  -o "$INSTALLER" \
  'https://raw.githubusercontent.com/XTLS/Xray-install/main/install-release.sh'
chmod 0755 "$INSTALLER"
sudo bash "$INSTALLER" install --without-geodata

XRAY=/usr/local/bin/xray
if [[ ! -x "$XRAY" ]]; then
  echo "BLOCKED: Xray binary was not installed." >&2
  exit 20
fi

# -----------------------------
# 3. Generate ephemeral credentials
# -----------------------------
UUID="$($XRAY uuid)"
KEYS="$($XRAY x25519)"
PRIVATE_KEY="$(printf '%s\n' "$KEYS" | awk -F': ' '/^(Private key|PrivateKey):/{print $2; exit}')"
PUBLIC_KEY="$(printf '%s\n' "$KEYS" | awk -F': ' '/^(Public key|Password):/{print $2; exit}')"
SHORT_ID="$(openssl rand -hex 8)"

if [[ -z "$UUID" || -z "$PRIVATE_KEY" || -z "$PUBLIC_KEY" || ! "$SHORT_ID" =~ ^[0-9a-f]{16}$ ]]; then
  echo "BLOCKED: credential generation failed." >&2
  exit 21
fi

# -----------------------------
# 4. VLESS + REALITY + Vision
# -----------------------------
# Cloudflare is used only as the REALITY TLS target. It is NOT the VPN server.
# The endpoint exposed to the client is the ephemeral ngrok TCP address.
cat > /usr/local/etc/xray/config.json <<EOF
{
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "listen": "0.0.0.0",
      "port": 8443,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "$UUID",
            "flow": "xtls-rprx-vision"
          }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "raw",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "target": "www.cloudflare.com:443",
          "xver": 0,
          "serverNames": ["www.cloudflare.com"],
          "privateKey": "$PRIVATE_KEY",
          "shortIds": ["$SHORT_ID"]
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "tag": "direct"
    },
    {
      "protocol": "blackhole",
      "tag": "block"
    }
  ]
}
EOF

chmod 600 /usr/local/etc/xray/config.json
chown root:root /usr/local/etc/xray/config.json

# Validate before activation: fail closed if configuration is invalid.
if ! "$XRAY" run -test -config /usr/local/etc/xray/config.json; then
  echo "BLOCKED: Xray configuration validation failed." >&2
  exit 22
fi

sudo systemctl restart xray
sleep 2
if ! sudo systemctl is-active --quiet xray; then
  echo "BLOCKED: Xray service is not active." >&2
  sudo journalctl -u xray --no-pager -n 40 >&2 || true
  exit 23
fi

if ! (command -v ss >/dev/null && ss -lnt | grep -q ':8443 '); then
  echo "BLOCKED: Xray is not listening on TCP 8443." >&2
  exit 24
fi

# -----------------------------
# 5. Expose ONLY the Xray port through ngrok
# -----------------------------
./ngrok tcp 8443 --log "$TMP_DIR/ngrok.log" >/dev/null 2>&1 &
NGROK_PID=$!

for _ in {1..45}; do
  if grep -qE 'tcp://[^ ]+' "$TMP_DIR/ngrok.log"; then
    break
  fi
  sleep 1
done

ENDPOINT="$(grep -o -E 'tcp://[^ ]+' "$TMP_DIR/ngrok.log" | head -n1 || true)"
if [[ -z "$ENDPOINT" ]]; then
  echo "BLOCKED: ngrok TCP endpoint was not established." >&2
  tail -n 40 "$TMP_DIR/ngrok.log" >&2 || true
  exit 25
fi

HOST="${ENDPOINT#tcp://}"
HOST="${HOST%%:*}"
PORT="${ENDPOINT##*:}"

# Client URI contains only the UUID/public key/short ID. The server private
# key remains on the ephemeral VM and is never printed or committed.
URI="vless://${UUID}@${HOST}:${PORT}?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.cloudflare.com&fp=chrome&pbk=${PUBLIC_KEY}&sid=${SHORT_ID}&type=tcp&headerType=none#V-INFINITY-Ephemeral"

# -----------------------------
# 6. Final fail-closed evidence
# -----------------------------
echo "=========================================="
echo "V∞ EPHEMERAL XRAY RESULT"
echo "=========================================="
echo "Xray: ACTIVE"
echo "Protocol: VLESS + REALITY + XTLS Vision"
echo "Transport: raw TCP"
echo "Local listener: 8443"
echo "Tunnel: ngrok TCP"
echo "Endpoint: ${HOST}:${PORT}"
echo "Lifetime: up to 6 hours; VM is disposable"
echo ""
echo "ANDROID VLESS URI:"
echo "$URI"
echo ""
echo "V∞ STATES:"
echo "SSH_ACCESS=NOT_REQUIRED"
echo "XRAY_CONFIG=OBSERVED"
echo "XRAY_SERVICE=OBSERVED"
echo "LISTENER_8443=OBSERVED"
echo "PUBLIC_ENDPOINT=OBSERVED"
echo "INDEPENDENT_CLIENT_CONNECTIVITY=NOT_EXECUTED"
echo "PERSISTENCE=FALSE"
echo "=========================================="

# Keep the VM alive while the workflow is active.
sleep 6h
