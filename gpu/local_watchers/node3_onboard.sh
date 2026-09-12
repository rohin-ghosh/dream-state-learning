#!/bin/bash
# node3_onboard.sh — laptop-side, unattended: wait for the new Colossus lease's node to finish CLEAN provisioning
# (RESERVED + IP + ssh port), install the laptop's ssh key using the lease credentials fetched at runtime from the
# Colossus CLI (never stored), append the host to gpu/hosts.env as $VAR (gitignored) on the laptop AND on the VM,
# and create gpu/<prefix>_ssh.sh / gpu/<prefix>_scp.sh wrappers. Then prints NODE_READY <ip>.
# Usage: bash gpu/local_watchers/node3_onboard.sh <resource-name> <lease-id> <VAR> <prefix>
#   e.g. bash gpu/local_watchers/node3_onboard.sh ipp2-ovx-p6-09 f1f1d208-f245-431e-88da-e17a06ee432d OVX2_NODE ovx2
set -u
NODE="${1:?resource name}"; LEASE_ID="${2:?lease id}"; VAR="${3:-OVX2_NODE}"; PFX="${4:-ovx2}"
C="$HOME/.venvs/colossus-cli/bin/colossus"; REPO="$HOME/dream-state"
LOG="$HOME/dream-state-artifacts/node3_onboard.log"
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
log "onboard start node=$NODE lease=$LEASE_ID var=$VAR"
ip=""
for ((i=0; i<90; i++)); do
  OUT=$("$C" bm resource list --search "$NODE" --json 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin); d=d if isinstance(d,list) else d.get('items',[])
for r in d:
    if r.get('name')=='$NODE': print(r.get('status'), r.get('ipAddress') or '-')" 2>/dev/null)
  st=$(echo "$OUT" | awk '{print $1}'); ip=$(echo "$OUT" | awk '{print $2}')
  log "poll $i: status=$st ip=$ip"
  if [ "$st" = "RESERVED" ] && [ -n "$ip" ] && [ "$ip" != "-" ] && nc -z -w 5 "$ip" 22 2>/dev/null; then break; fi
  ip=""; sleep 120
done
[ -n "$ip" ] || { log "TIMEOUT waiting for $NODE"; exit 2; }
# credentials at runtime only
CREDS=$("$C" bm lease list --lease-id "$LEASE_ID" --show-creds --json 2>/dev/null)
export NODE_USER=$(printf '%s' "$CREDS" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for it in (d if isinstance(d,list) else [d]):
    s=it.get('lease_secrets') or {}
    if s.get('local_accountname'): print(s['local_accountname']); break")
export NODE_PASS=$(printf '%s' "$CREDS" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for it in (d if isinstance(d,list) else [d]):
    s=it.get('lease_secrets') or {}
    if s.get('local_accountpassword'): print(s['local_accountpassword']); break")
unset CREDS
[ -n "${NODE_USER:-}" ] && [ -n "${NODE_PASS:-}" ] || { log "CRED_EXTRACT_FAILED"; exit 1; }
log "creds loaded for user $NODE_USER (password not logged)"
export PUBKEY=$(cat "$HOME/.ssh/id_ed25519.pub")
expect <<EXP
set timeout 40
set user \$env(NODE_USER)
set pass \$env(NODE_PASS)
set pk \$env(PUBKEY)
spawn ssh -o StrictHostKeyChecking=accept-new \$user@$ip "mkdir -p ~/.ssh && chmod 700 ~/.ssh && printf '%s\n' \"\$pk\" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo KEY_OK"
expect {
    -re "(?i)password" { send "\$pass\r"; exp_continue }
    "KEY_OK" { exit 0 }
    timeout { exit 2 }
    eof { exit 3 }
}
EXP
rc=$?; unset NODE_PASS
[ $rc -eq 0 ] || { log "KEY_INSTALL_FAILED rc=$rc"; exit $rc; }
ssh -o BatchMode=yes -o ConnectTimeout=10 "$NODE_USER@$ip" "echo KEY_AUTH_OK; lspci | grep -ci nvidia; nvidia-smi -L 2>/dev/null | wc -l" | tee -a "$LOG"
# hosts.env (laptop), wrappers, then the VM
grep -q "^$VAR=" "$REPO/gpu/hosts.env" && sed -i.bak "s|^$VAR=.*|$VAR=\"$NODE_USER@$ip\"|" "$REPO/gpu/hosts.env" || echo "$VAR=\"$NODE_USER@$ip\"" >> "$REPO/gpu/hosts.env"
sed "s/OVX_NODE/$VAR/g; s/8xA40 worker node #2 (lease to ~2026-09-21)/8xA40 worker node #3 $NODE (lease to 2026-09-19)/" "$REPO/gpu/ovx_ssh.sh" > "$REPO/gpu/${PFX}_ssh.sh"
sed "s/OVX_NODE/$VAR/g" "$REPO/gpu/ovx_scp.sh" > "$REPO/gpu/${PFX}_scp.sh"
chmod +x "$REPO/gpu/${PFX}_ssh.sh" "$REPO/gpu/${PFX}_scp.sh"
bash "$REPO/gpu/nvl_ssh.sh" "grep -q '^$VAR=' ~/dream-state/gpu/hosts.env && sed -i 's|^$VAR=.*|$VAR=\"$NODE_USER@$ip\"|' ~/dream-state/gpu/hosts.env || echo '$VAR=\"$NODE_USER@$ip\"' >> ~/dream-state/gpu/hosts.env; echo vm_hosts_ok" | tee -a "$LOG"
log "NODE_READY $NODE $ip user=$NODE_USER var=$VAR wrappers=gpu/${PFX}_ssh.sh gpu/${PFX}_scp.sh"
