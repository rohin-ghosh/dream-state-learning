#!/bin/bash
# v2 lease node (4u4g-gen-0310, 4xH100-NVL). Key auth; no secrets stored.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; source "$HERE/hosts.env" 2>/dev/null || { echo "gpu/hosts.env missing (see hosts.env.example)" >&2; exit 2; }
NODE="$V2_NODE"
exec ssh -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 "$NODE" "$@"
