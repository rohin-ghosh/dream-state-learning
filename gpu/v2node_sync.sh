#!/bin/bash
source "$(dirname "$0")/hosts.env"
# Push working tree to the v2 node (no .git, no artifacts, no venv).
exec rsync -a --delete \
    --exclude='.git' --exclude='.venv' --exclude='gpu_artifacts_local' \
    --exclude='alchemy/v2_out' --exclude='alchemy/smoke_out' \
    "$HOME/dream-state/" "$V2_NODE":~/dream-state/
