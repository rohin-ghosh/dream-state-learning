#!/bin/bash
# Thin wrapper: run a command on the lease node (key auth; no secrets stored).
# Usage: gpu/node_ssh.sh "command to run on node"
NODE="local-rohing@10.117.3.227"
exec ssh -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 "$NODE" "$@"
