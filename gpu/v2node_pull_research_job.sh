#!/bin/bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "usage: $0 RUN_ID" >&2
    exit 64
fi

RUN_ID="$1"
case "$RUN_ID" in
    *[!A-Za-z0-9._-]*|'') echo "invalid run id" >&2; exit 64 ;;
esac

source "$(dirname "$0")/hosts.env"; NODE="$V2_NODE"
DEST="$HOME/dream-state/gpu_artifacts_local/research_loop/$RUN_ID"
mkdir -p "$DEST/job"
rsync -a "$NODE:~/v2/jobs/$RUN_ID/" "$DEST/job/"
echo "$DEST"
