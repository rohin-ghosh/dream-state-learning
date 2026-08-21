#!/bin/bash
# v2 lease node (4u4g-gen-0310, 4xH100-NVL). Key auth; no secrets stored.
NODE="local-rohing@10.57.206.238"
exec ssh -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 "$NODE" "$@"
