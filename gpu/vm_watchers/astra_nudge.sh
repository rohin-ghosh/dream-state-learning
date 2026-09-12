#!/bin/bash
# astra_nudge.sh — VM-side continuity watcher for the builder (Astra in Codex, tmux session "astra").
#
# Rohin, 2026-09-12 06:20 UTC: "you can't be the one checking if Astra is idle when you might not be awake" — so this
# runs on the VM, not on Fable's laptop. Every INTERVAL seconds it reads the builder's Codex session log and, when
#   (a) the full launch prompt has been pasted (a user message contains the §15 header),
#   (b) the last Codex event is task_complete / turn_aborted, i.e. no turn is running, and
#   (c) that has been true for >= IDLE_MIN minutes and the last nudge was >= RENUDGE_MIN minutes ago,
# it types the launch prompt's continuation message into the tmux session, prefixed so the builder knows it is an
# automated nudge from the watcher and not a ruling from Rohin (notebook, [Fable] 06:15 UTC). No LLM, no tokens.
# Kill switch: touch ~/astra_nudge.off. Log: ~/astra_nudge.log. State: ~/astra_nudge.state (last nudge epoch).
# Usage: bash gpu/vm_watchers/astra_nudge.sh [INTERVAL_S=300] [IDLE_MIN=15] [RENUDGE_MIN=60] [--once] [--dry-run]
set -u
INTERVAL="${1:-300}"; IDLE_MIN="${2:-15}"; RENUDGE_MIN="${3:-60}"; ONCE=0; DRY=0
for a in "$@"; do [ "$a" = "--once" ] && ONCE=1; [ "$a" = "--dry-run" ] && DRY=1; done
LOG="$HOME/astra_nudge.log"; STATE="$HOME/astra_nudge.state"; OFF="$HOME/astra_nudge.off"; TMUX_TARGET="astra"
MSG='[Fable watcher — automated continuation, not Rohin] Resume the developmental-parenting research mission (launch prompt §11 loop, §15 standing authorization). Reconcile live jobs and durable state; do not restart completed work; choose the highest-value action on the critical path, execute it, inspect its evidence, update state, and keep every leased GPU busy. If you are waiting on Rohin for something, write it in research_loop/COORDINATION.md under a "[Builder → Rohin]" heading and continue with everything that is not blocked.'
log() { echo "$(date -u +%FT%TZ) $*" >> "$LOG"; }
echo $$ > "$HOME/astra_nudge.pid"
log "start interval=${INTERVAL}s idle_min=$IDLE_MIN renudge_min=$RENUDGE_MIN once=$ONCE dry=$DRY"
while :; do
  if [ -f "$OFF" ]; then log "kill switch present; idle tick"; [ "$ONCE" = 1 ] && exit 0; sleep "$INTERVAL"; continue; fi
  if ! tmux has-session -t "$TMUX_TARGET" 2>/dev/null; then log "no tmux session $TMUX_TARGET"; [ "$ONCE" = 1 ] && exit 0; sleep "$INTERVAL"; continue; fi
  verdict=$(python3 - "$IDLE_MIN" <<'EOF'
import glob, json, os, sys, time
idle_min = float(sys.argv[1])
files = sorted(glob.glob(os.path.expanduser("~/.codex/sessions/*/*/*/rollout-*.jsonl")), key=os.path.getmtime, reverse=True)
chosen = None
for f in files[:12]:
    try:
        with open(f) as fh:
            meta = json.loads(fh.readline())["payload"]
    except Exception:
        continue
    if meta.get("originator") == "codex-tui" and str(meta.get("cwd", "")).endswith("dream-state"):
        chosen = f; break
if not chosen:
    print("nofile"); sys.exit()
launched = False; last_ev = None; last_ts = None
with open(chosen) as fh:
    for line in fh:
        try: d = json.loads(line)
        except Exception: continue
        p = d.get("payload", {})
        if d.get("type") == "response_item" and p.get("type") == "message" and p.get("role") == "user" and not launched:
            txt = " ".join(c.get("text", "") for c in p.get("content", []) if isinstance(c, dict))
            if "### 15. Standing authorization" in txt or "BEGIN LAUNCH PROMPT" in txt: launched = True
        if d.get("type") == "event_msg":
            last_ev = p.get("type"); last_ts = d.get("timestamp")
if not last_ts:
    print("noevents"); sys.exit()
t = time.strptime(last_ts[:19], "%Y-%m-%dT%H:%M:%S"); age_min = (time.time() - (time.mktime(t) - time.timezone)) / 60.0
idle = last_ev in ("task_complete", "turn_aborted")
print(f"file={os.path.basename(chosen)} launched={int(launched)} idle={int(idle)} last={last_ev} age_min={age_min:.1f} ok={int(launched and idle and age_min >= idle_min)}")
EOF
)
  log "check: $verdict"
  if echo "$verdict" | grep -q "ok=1"; then
    last=$(cat "$STATE" 2>/dev/null || echo 0); now=$(date +%s)
    if [ $(( (now - last) / 60 )) -ge "$RENUDGE_MIN" ]; then
      if [ "$DRY" = 1 ]; then log "DRY-RUN: would nudge"; else
        tmux send-keys -t "$TMUX_TARGET" -l "$MSG" && sleep 1 && tmux send-keys -t "$TMUX_TARGET" Enter && echo "$now" > "$STATE" && log "NUDGED"
      fi
    else log "idle but last nudge $(( (now - last) / 60 )) min ago (< $RENUDGE_MIN); waiting"; fi
  fi
  [ "$ONCE" = 1 ] && exit 0
  sleep "$INTERVAL"
done
