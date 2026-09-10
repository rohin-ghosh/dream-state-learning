#!/bin/bash
# scp to/from the 8xA40 node (lease to 2026-09-14). Usage: gpu/a40_scp.sh LOCAL... NODE:REMOTE  (or NODE:REMOTE LOCAL)
# Write the remote side as NODE:path — the literal word NODE is replaced by the address in gpu/hosts.env (never committed).
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; source "$HERE/hosts.env" 2>/dev/null || { echo "gpu/hosts.env missing (see hosts.env.example)" >&2; exit 2; }
args=(); for a in "$@"; do args+=("${a/#NODE:/$A40_NODE:}"); done
exec scp -o BatchMode=yes -o ConnectTimeout=15 "${args[@]}"
