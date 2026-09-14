#!/bin/bash
# Independent result reader for the always-on VM (cron, every 30 min, offset from backup_selfcheck.sh).
# Runs REGARDLESS of the laptop heartbeat: Rohin ruled (2026-09-14, message 63) that the reviewer does
# independent reads of every result-bearing SEQ and the builder never waits for them.
# Runs a headless Claude on RESULT_READ_PROMPT.md in ~/dream-state (cap 900 s by default), appends the
# transcript to ~/courier/result_reads/<UTC ts>.md, and lets the prompt itself commit the notebook entry.
# Single instance via ~/courier/result_reads/result_read.pid. Log: ~/courier/result_reads/result_read.log.
#
# Env (tests): COURIER_HOME, COURIER_REPO, COURIER_CLAUDE_BIN, CLAUDE_CREDENTIALS_FILE,
#              RESULT_READ_CAP_S (default 900), RESULT_READ_PROMPT
# Exit codes: 0 ran or skipped cleanly; 3 run failed or timed out.
# shellcheck source=courier_lib.sh
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/courier_lib.sh"

OUT="${COURIER_HOME:-$HOME/courier}/result_reads"
mkdir -p "$OUT"
LOG="$OUT/result_read.log"
PIDFILE="$OUT/result_read.pid"
CAP_S="${RESULT_READ_CAP_S:-900}"
PROMPT="${RESULT_READ_PROMPT:-$HERE/RESULT_READ_PROMPT.md}"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG"; }

# single instance
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE" 2>/dev/null)" 2>/dev/null; then
  log "previous result read still running (pid $(cat "$PIDFILE")), skipping"; exit 0
fi
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT

if ! claude_ready; then log "claude not ready ($(claude_not_ready_reason)), skipping"; exit 0; fi
[ -r "$PROMPT" ] || { log "prompt $PROMPT missing, skipping"; exit 0; }
[ -d "$COURIER_REPO" ] || { log "repo $COURIER_REPO missing, skipping"; exit 0; }

TS="$(date -u +%Y%m%dT%H%M%SZ)"
TRANSCRIPT="$OUT/$TS.md"
log "starting result read (cap ${CAP_S}s) -> $TRANSCRIPT"
( cd "$COURIER_REPO" && run_with_timeout "$CAP_S" "$CLAUDE_BIN" -p "$(cat "$PROMPT")" \
    --model "${COURIER_MODEL:-claude-fable-5-1}" --permission-mode acceptEdits --output-format text \
    > "$TRANSCRIPT" 2>&1 < /dev/null )
rc=$?
echo "" >> "$TRANSCRIPT"; echo "[result_read: exit=$rc finished=$(date -u +%Y-%m-%dT%H:%M:%SZ)]" >> "$TRANSCRIPT"
if [ "$rc" -eq 0 ]; then log "result read finished rc=0 -> $TRANSCRIPT"; exit 0; fi
log "result read FAILED/timed out rc=$rc -> $TRANSCRIPT"; exit 3
