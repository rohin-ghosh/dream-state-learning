#!/bin/bash
# Push working tree to the v2 node (no .git, no artifacts, no venv).
exec rsync -a --delete \
    --exclude='.git' --exclude='.venv' --exclude='gpu_artifacts_local' \
    --exclude='alchemy/v2_out' --exclude='alchemy/smoke_out' \
    "$HOME/dream-state/" local-rohing@10.57.206.238:~/dream-state/
