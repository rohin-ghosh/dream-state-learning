#!/bin/bash
# GH200 worker node (lego-cg1-qct-034). Key auth; no secrets stored.
NODE="local-rohing@10.57.199.71"
exec ssh -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 "$NODE" "$@"
