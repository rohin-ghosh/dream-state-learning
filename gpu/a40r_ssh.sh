#!/bin/bash
# 8xA40 worker node #3, new lease to 2026-09-19 (host in gitignored gpu/hosts.env). Key auth; no secrets stored.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; source "$HERE/hosts.env" 2>/dev/null || { echo "gpu/hosts.env missing (see hosts.env.example)" >&2; exit 2; }
NODE="$A40R_NODE"
exec ssh -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 "$NODE" "$@"
