#!/usr/bin/env bash
# Talk to Astra (the orchestrator running in Codex on the helper VM, tmux session "astra2") from the laptop, as Rohin.
#
#   bash gpu/talk_astra.sh "<message>"             # deliver as a marked Rohin message (interrupts Astra's current turn), then wait for the reply
#   bash gpu/talk_astra.sh "<message>" --no-wait   # deliver only
#   bash gpu/talk_astra.sh --file notes.txt        # deliver the contents of a file (long messages, pasted email)
#   bash gpu/talk_astra.sh --watch [N]             # print the last N lines of Astra's pane (default 40) — read what it is doing / its reply
#   bash gpu/talk_astra.sh --attach                # attach read-only to Astra's tmux pane (detach with Ctrl-b then d)
#   bash gpu/talk_astra.sh --resume                # send /goal resume if the goal shows paused and Astra is idle
#   WAIT_MIN=20 bash gpu/talk_astra.sh "..."       # wait longer than the default 10 minutes for the reply
#   DRY_RUN=1 bash gpu/talk_astra.sh "..."         # show what would be sent, send nothing
#
# Mechanics: the message is written to a file on the VM (also kept in ~/courier/ as a receipt), pasted into the Codex composer
# with tmux, and submitted with Enter (Codex needs a settle time and sometimes a second Enter after a large paste).
# If Astra is mid-turn the turn is interrupted first (Escape) — Rohin's messages go through immediately by his standing rule.
# Nothing else is touched. Output is redacted of internal hostnames, IPs and keys. Works with macOS bash 3.2.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -x gpu/nvl_ssh.sh ] || { echo "missing gpu/nvl_ssh.sh" >&2; exit 2; }
redact() { LC_ALL=C sed -E 's/[a-z0-9.-]+\.nvidia\.com/[host]/g; s/[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[ip]/g; s/sk-[A-Za-z0-9_-]+/[key]/g'
}
SESSION=astra2
WAIT_MIN="${WAIT_MIN:-10}"

usage() { sed -n '2,13p' "$0"; exit 0; }
[ $# -ge 1 ] || usage

case "$1" in
  --watch)
    N="${2:-40}"
    bash gpu/nvl_ssh.sh "tmux capture-pane -p -t $SESSION | grep -v '^\s*$' | tail -n $N | cut -c1-220" | redact
    exit 0 ;;
  --attach)
    HERE="$(cd gpu && pwd)"; source "$HERE/hosts.env" 2>/dev/null || { echo "gpu/hosts.env missing" >&2; exit 2; }
    echo "attaching read-only to Astra's pane; detach with Ctrl-b then d"
    exec ssh -t -o ConnectTimeout=15 "${NVL_HOST:?}" "tmux attach -r -t $SESSION" ;;
  --resume)
    bash gpu/nvl_ssh.sh "P=\$(tmux capture-pane -p -t $SESSION); if echo \"\$P\" | grep -q 'esc to interrupt'; then echo 'Astra is mid-turn; not paused'; elif echo \"\$P\" | grep -q 'Goal paused'; then tmux send-keys -t $SESSION -l '/goal resume'; sleep 1; tmux send-keys -t $SESSION Enter; echo 'sent /goal resume'; else echo 'goal not paused'; fi" | redact
    exit 0 ;;
  --file)
    [ -f "${2:-}" ] || { echo "file not found: ${2:-}" >&2; exit 2; }
    text="$(cat "$2")"; shift 2 ;;
  -h|--help) usage ;;
  *)
    text="$1"; shift ;;
esac
wait=1; [ "${1:-}" = "--no-wait" ] && wait=0

NOW=$(date -u +%H:%MZ); PDT=$(TZ=America/Los_Angeles date +%H:%M); STAMP=$(date -u +%Y%m%dT%H%M%SZ)
msg="[ROHIN — direct message, ${NOW} (${PDT} PDT); rulings and orders in this message take effect immediately] ${text}"
b64=$(printf '%s' "$msg" | base64 | tr -d '\n')

remote="set -e
echo $b64 | base64 -d > /tmp/rohin_direct.txt
mkdir -p ~/courier && cp /tmp/rohin_direct.txt ~/courier/rohin_direct_${STAMP}.txt
P=\$(tmux capture-pane -p -t $SESSION)
if echo \"\$P\" | grep -q 'to scroll\|edit prev'; then tmux send-keys -t $SESSION q; sleep 1; fi
if tmux capture-pane -p -t $SESSION | grep -q 'esc to interrupt'; then tmux send-keys -t $SESSION Escape; sleep 3; echo 'interrupted the running turn'; fi
if tmux capture-pane -p -t $SESSION | grep -q 'Queued follow-up'; then tmux send-keys -t $SESSION S-Left; sleep 1.5; fi
tmux load-buffer /tmp/rohin_direct.txt; tmux paste-buffer -t $SESSION; sleep 8
tmux send-keys -t $SESSION Enter; sleep 10
for i in 1 2 3; do
  if tmux capture-pane -p -t $SESSION | grep -q 'Pasted Content\|take effect immediately\]'; then sleep 15; tmux send-keys -t $SESSION Enter; sleep 8; fi
done
if tmux capture-pane -p -t $SESSION | grep -q 'take effect immediately\]'; then echo 'WARNING: message may still be sitting in the composer; run --watch and press Enter with --resume-style send-keys if needed'; else echo \"DELIVERED \$(date -u +%H:%M:%SZ) (receipt ~/courier/rohin_direct_${STAMP}.txt)\"; fi"

if [ "${DRY_RUN:-0}" = "1" ]; then echo "would send to tmux $SESSION on the VM:"; echo "$msg"; exit 0; fi
echo ">> Rohin -> Astra: $text"
bash gpu/nvl_ssh.sh "$remote" | redact
[ $wait = 1 ] || exit 0

echo "... waiting for Astra to finish its turn (up to ${WAIT_MIN} min; Ctrl-C to stop waiting — the message is already delivered)"
deadline=$(( $(date +%s) + WAIT_MIN*60 )); tick=0
while [ $(date +%s) -lt $deadline ]; do
  sleep 20; tick=$((tick+1))
  P=$(bash gpu/nvl_ssh.sh "tmux capture-pane -p -t $SESSION" 2>/dev/null || true)
  if echo "$P" | grep -q 'esc to interrupt'; then
    [ $((tick % 3)) = 0 ] && echo "... Astra working: $(echo "$P" | grep -o '([0-9hms ]* • esc to interrupt)' | tail -1)"
    continue
  fi
  echo "<< Astra's pane (turn finished):"; echo "$P" | grep -v '^\s*$' | tail -n 45 | cut -c1-220 | redact
  exit 0
done
echo "!! Astra is still mid-turn after ${WAIT_MIN} min; read later with: bash gpu/talk_astra.sh --watch 60"
