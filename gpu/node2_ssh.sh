#!/bin/bash
# Node 2 (ipp1-1735) command wrapper — key auth, no secrets stored.
exec ssh -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 \
    local-rohing@10.117.10.11 "$@"
