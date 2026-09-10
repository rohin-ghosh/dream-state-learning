#!/bin/bash
# One-time SSH key install for <INTERNAL_HOST> (8xA40, lease to ~Sep 21).
# Fetches the lease OS password via Colossus CLI at runtime (never stored).
set -u
LEASE_ID="a12bda56-10b2-4b69-abc4-401dcea654c7"
NODE_IP="<INTERNAL_IP>"
C="$HOME/.venvs/colossus-cli/bin/colossus"

CREDS=$("$C" bm lease list --lease-id "$LEASE_ID" --show-creds --json 2>/dev/null)
export NODE_USER=$(printf '%s' "$CREDS" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for it in (d if isinstance(d,list) else [d]):
    s=it.get('lease_secrets') or {}
    if s.get('local_accountname'): print(s['local_accountname']); break
")
export NODE_PASS=$(printf '%s' "$CREDS" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for it in (d if isinstance(d,list) else [d]):
    s=it.get('lease_secrets') or {}
    if s.get('local_accountpassword'): print(s['local_accountpassword']); break
")
unset CREDS
if [ -z "${NODE_USER:-}" ] || [ -z "${NODE_PASS:-}" ]; then
  echo "CRED_EXTRACT_FAILED (is the colossus CLI logged in?)"; exit 1
fi
echo "creds loaded for user: $NODE_USER (password not shown)"
export PUBKEY=$(cat "$HOME/.ssh/id_ed25519.pub")

expect <<EXP
set timeout 30
set user \$env(NODE_USER)
set pass \$env(NODE_PASS)
set pk \$env(PUBKEY)
spawn ssh -o StrictHostKeyChecking=accept-new \$user@$NODE_IP "mkdir -p ~/.ssh && chmod 700 ~/.ssh && printf '%s\n' \"\$pk\" > ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo KEY_OK"
expect {
    -re "(?i)password" { send "\$pass\r"; exp_continue }
    "KEY_OK" { exit 0 }
    timeout { exit 2 }
    eof { exit 3 }
}
EXP
rc=$?
unset NODE_PASS
[ $rc -ne 0 ] && { echo "KEY_INSTALL_FAILED rc=$rc"; exit $rc; }
ssh -o BatchMode=yes -o ConnectTimeout=10 "$NODE_USER@$NODE_IP" \
  "echo KEY_AUTH_OK; lspci | grep -ci nvidia"
