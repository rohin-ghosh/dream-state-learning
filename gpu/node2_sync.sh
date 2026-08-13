#!/bin/bash
# Push the working tree to node 2 (repo is private; no tokens on nodes).
exec rsync -a --delete \
    --exclude='.git' --exclude='gpu_artifacts_local' --exclude='gpu_artifacts' \
    "$HOME/dream-state/" local-rohing@10.117.10.11:~/dream-state-learning/
