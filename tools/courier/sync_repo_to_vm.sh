#!/bin/bash
# Bring the VM's ~/dream-state checkout up to the laptop's HEAD without GitHub
# auth on the VM: ship a git bundle of the missing commits through gpu/nvl_scp.sh
# and hard-reset the VM checkout to the laptop HEAD (VM-side untracked and
# gitignored files, e.g. gpu/hosts.env and runtime state, are untouched).
# Run on the laptop from the repo:  bash tools/courier/sync_repo_to_vm.sh
# Once the VM has GitHub push/pull auth this is superseded by `git pull` there.
set -eu
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
SSH="bash $REPO/gpu/nvl_ssh.sh"
SCP="bash $REPO/gpu/nvl_scp.sh"
TMP="${TMPDIR:-/tmp}"

local_head="$(git -C "$REPO" rev-parse HEAD)"
vm_head="$($SSH 'git -C ~/dream-state rev-parse HEAD 2>/dev/null' || true)"
if [ -z "$vm_head" ]; then echo "VM has no ~/dream-state git checkout" >&2; exit 1; fi
if [ "$vm_head" = "$local_head" ]; then echo "VM already at laptop HEAD ${local_head:0:8}"; exit 0; fi

# The VM may have made local commits (backup self-check runs commit locally while
# it has no GitHub auth). Never destroy them: if the VM HEAD is not an ancestor of
# the laptop HEAD, pull the VM's commits into the laptop branch `vm-local` and stop;
# merge/cherry-pick them on the laptop, commit, then rerun this script.
if ! git -C "$REPO" merge-base --is-ancestor "$vm_head" "$local_head" 2>/dev/null; then
  if ! git -C "$REPO" cat-file -e "$vm_head" 2>/dev/null; then
    # Bundle the VM's commits since the last sync point (refs/laptop/last-sync,
    # set below on every successful sync; fallback: last 40 commits).
    $SSH 'mkdir -p ~/.tmp/ds_xfer && cd ~/dream-state && base=$(git rev-parse -q --verify refs/laptop/last-sync || git rev-parse -q --verify HEAD~40 || git rev-list --max-parents=0 HEAD | tail -1) && git bundle create ~/.tmp/ds_xfer/vm_local.bundle HEAD --not "$base" >/dev/null 2>&1' \
      || { echo "could not bundle VM-local commits" >&2; exit 1; }
    $SCP "NODE:.tmp/ds_xfer/vm_local.bundle" "$TMP/vm_local.bundle" >/dev/null
    git -C "$REPO" fetch -q "$TMP/vm_local.bundle" "HEAD:refs/heads/vm-local"
    rm -f "$TMP/vm_local.bundle"; $SSH 'rm -f ~/.tmp/ds_xfer/vm_local.bundle' >/dev/null
  else
    git -C "$REPO" branch -f vm-local "$vm_head" >/dev/null
  fi
  echo "VM has local commits not on the laptop (VM HEAD ${vm_head:0:8}); fetched into laptop branch 'vm-local'." >&2
  echo "Merge or cherry-pick them (git log main..vm-local), commit on the laptop, then rerun. No reset done." >&2
  exit 2
fi

# git bundle must record a ref name (a bare sha as range end is refused), so bundle to HEAD.
bundle="$TMP/ds_delta_${local_head:0:8}.bundle"
git -C "$REPO" bundle create "$bundle" "$vm_head..HEAD" 2>&1 | grep -v '^Enumerating\|^Counting\|^Compressing\|^Writing\|^Total' || true
[ -s "$bundle" ] || { echo "bundle creation failed" >&2; exit 1; }
$SSH 'mkdir -p ~/.tmp/ds_xfer' >/dev/null
$SCP "$bundle" "NODE:.tmp/ds_xfer/delta.bundle" >/dev/null
rm -f "$bundle"
$SSH "cd ~/dream-state && git fetch -q ~/.tmp/ds_xfer/delta.bundle HEAD && git reset -q --hard '$local_head' && git update-ref refs/laptop/last-sync '$local_head' && rm -f ~/.tmp/ds_xfer/delta.bundle && echo \"VM now at \$(git log --oneline -1 | cut -c1-80)\""
