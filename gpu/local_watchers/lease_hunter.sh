#!/bin/bash
# lease_hunter.sh — laptop-side loop: every INTERVAL seconds, list Colossus bare-metal nodes that are AVAILABLE,
# authorized-to-reserve, x86, with >= 8 GPUs of a usable type, and try to book each for DURATION (falling back to
# shorter durations on a policy refusal) until MAX_NEW new leases have been created. Logs every attempt.
# Rohin, 2026-09-12: "I want as many GPUs per lease" — so only 8-GPU nodes; T40 / A30 / T4 classes are excluded
# (too little memory for the 7B vLLM child + training).
# Usage: bash gpu/local_watchers/lease_hunter.sh [MAX_NEW=2] [INTERVAL=1200] [DURATION=8d]
# Stop: kill the PID in ~/dream-state-artifacts/lease_hunter.pid
set -u
MAX_NEW="${1:-2}"; INTERVAL="${2:-1200}"; DURATION="${3:-8d}"
C="$HOME/.venvs/colossus-cli/bin/colossus"
LOG="$HOME/dream-state-artifacts/lease_hunter.log"; PIDF="$HOME/dream-state-artifacts/lease_hunter.pid"
echo $$ > "$PIDF"
OK_TAGS='8XA40|8XA100|8XH100|8XH200|8XL40S|8XRTX-PRO-6000|8XA6000|8XL40'
JUST="Dream-state continual-learning experiments (ICLR 2027 deadline 09-25): parenting/developmental curriculum runs, 8-GPU node"
booked=0
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
log "lease_hunter start max_new=$MAX_NEW interval=${INTERVAL}s duration=$DURATION"
while [ "$booked" -lt "$MAX_NEW" ]; do
  cands=$("$C" bm resource list --authorized-to-reserve --partial-filters --filters status=AVAILABLE --all --json 2>/dev/null | python3 -c '
import json,sys,re
ok=re.compile(sys.argv[1])
d=json.load(sys.stdin); d=d if isinstance(d,list) else d.get("items",[])
for r in d:
    c=r.get("gpuCount"); tag=str(r.get("gpuTag") or "")
    if str(c).isdigit() and int(c)>=8 and ok.search(tag) and not r.get("leaseId"):
        print(r.get("name"), tag, r.get("poolName"))
' "$OK_TAGS" 2>/dev/null)
  if [ -z "$cands" ]; then log "no bookable 8-GPU node (free of pending leases) right now"; else
    while read -r name tag pool; do
      [ -z "$name" ] && continue
      for dur in "$DURATION" 5d 3d; do
        out=$("$C" bm lease create --search "$name" --os ubuntu-24.04-x86_64-standard-uefi --start-datetime now --duration "$dur" --provision-mode CLEAN --lease-justification "$JUST" 2>&1)
        if echo "$out" | grep -qi "error\|denied\|fail"; then log "REFUSED $name ($tag, $pool) $dur: $(echo "$out" | grep -i -m1 'error\|denied\|fail' | cut -c1-140)";
        else log "BOOKED $name ($tag, $pool) for $dur: $(echo "$out" | grep -i -m1 'lease id' | cut -c1-140) $(echo "$out" | grep -i -m1 'status by command' | cut -c1-120)"; booked=$((booked+1)); break; fi
      done
      [ "$booked" -ge "$MAX_NEW" ] && break
    done <<< "$cands"
  fi
  [ "$booked" -ge "$MAX_NEW" ] && break
  sleep "$INTERVAL"
done
log "lease_hunter done: booked=$booked"
rm -f "$PIDF"
