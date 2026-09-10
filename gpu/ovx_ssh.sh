#!/bin/bash
# 8xA40 worker node #2 (lease to ~2026-09-21). Key auth; no secrets stored.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; source "$HERE/hosts.env" 2>/dev/null || { echo "gpu/hosts.env missing (see hosts.env.example)" >&2; exit 2; }
NODE="$OVX_NODE"
exec ssh -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 "$NODE" "$@"
