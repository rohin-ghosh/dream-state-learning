#!/bin/bash
# Always-on helper VM ("nvl-ai"; alias in gpu/hosts.env as NVL_HOST) — hosts the self-check daemon, the message courier
# and Astra runs so nothing depends on the laptop being awake. Key auth; no secrets stored.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; source "$HERE/hosts.env" 2>/dev/null || { echo "gpu/hosts.env missing (see hosts.env.example)" >&2; exit 2; }
NODE="${NVL_HOST:?NVL_HOST not set in gpu/hosts.env}"
exec ssh -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 "$NODE" "$@"
