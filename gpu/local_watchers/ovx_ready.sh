#!/bin/bash
# Wait for <INTERNAL_HOST> to be provisioned (RESERVED + IP + sshable port).
C="$HOME/.venvs/colossus-cli/bin/colossus"
for ((i=0; i<60; i++)); do
  OUT=$("$C" bm resource list --search <INTERNAL_HOST> --json 2>/dev/null | python3 -c "
import json,sys
for r in json.load(sys.stdin):
    if r.get('name')=='<INTERNAL_HOST>':
        print(r.get('status'), r.get('ipAddress') or '-')" 2>/dev/null)
  echo "$(date '+%H:%M') $OUT"
  st=$(echo $OUT | awk '{print $1}'); ip=$(echo $OUT | awk '{print $2}')
  if [ "$st" = "RESERVED" ] && [ "$ip" != "-" ] && [ -n "$ip" ]; then
    if nc -z -w 5 "$ip" 22 2>/dev/null; then
      echo "OVX_READY $ip"
      exit 0
    fi
  fi
  sleep 120
done
echo "OVX_TIMEOUT"
