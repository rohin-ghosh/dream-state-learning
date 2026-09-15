#!/bin/bash
# scp to/from the OVX node. Usage: gpu/ovx_scp.sh LOCAL... NODE:REMOTE  (or NODE:REMOTE LOCAL)
# Write the remote side as NODE:path — the literal word NODE is replaced by the address in gpu/hosts.env (never committed).
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; source "$HERE/hosts.env" 2>/dev/null || { echo "gpu/hosts.env missing (see hosts.env.example)" >&2; exit 2; }
args=(); for a in "$@"; do args+=("${a/#NODE:/$A40R_NODE:}"); done
exec scp -o BatchMode=yes -o ConnectTimeout=15 "${args[@]}"
