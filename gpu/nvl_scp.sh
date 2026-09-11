#!/bin/bash
# scp to/from the always-on helper VM. Usage: gpu/nvl_scp.sh LOCAL... NODE:REMOTE  (or NODE:REMOTE LOCAL)
# The literal word NODE is replaced by NVL_HOST from gpu/hosts.env (never committed).
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; source "$HERE/hosts.env" 2>/dev/null || { echo "gpu/hosts.env missing (see hosts.env.example)" >&2; exit 2; }
H="${NVL_HOST:?NVL_HOST not set in gpu/hosts.env}"
args=(); for a in "$@"; do args+=("${a/#NODE:/$H:}"); done
exec scp -o BatchMode=yes -o ConnectTimeout=15 "${args[@]}"
