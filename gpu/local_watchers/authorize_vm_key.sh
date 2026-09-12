#!/bin/bash
# authorize_vm_key.sh <prefix> — append the VM's public ssh key to a node's authorized_keys so the builder on the VM
# can reach the node through gpu/<prefix>_ssh.sh. Run from the laptop after a node is onboarded (nodes 1 and 2 already
# have it). Usage: bash gpu/local_watchers/authorize_vm_key.sh ovx2
set -u
PFX="${1:?prefix}"; HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUB=$(bash "$HERE/nvl_ssh.sh" 'cat ~/.ssh/id_ed25519.pub' 2>/dev/null | grep '^ssh-' | head -1)
[ -n "$PUB" ] || { echo "no VM public key"; exit 1; }
bash "$HERE/${PFX}_ssh.sh" "grep -qF '$PUB' ~/.ssh/authorized_keys 2>/dev/null || echo '$PUB' >> ~/.ssh/authorized_keys; echo vm_key_authorized_on_$PFX"
