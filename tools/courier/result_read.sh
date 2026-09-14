#!/bin/bash
# Independent result reader for the always-on VM (cron at :15 and :45, offset from backup_selfcheck.sh).
# Runs REGARDLESS of the laptop heartbeat: Rohin ruled (2026-09-14, message 63) that the reviewer does
# independent reads of every result-bearing SEQ and the builder never waits for them.
# Runs a headless Claude on RESULT_READ_PROMPT.md in ~/dream-state (cap 900 s by default), writes the
# transcript to ~/courier/result_reads/<UTC ts>.md, and lets the prompt itself commit the notebook entry
# with `git commit -o research_loop/COORDINATION.md` (never touching the builder's staged files).
# Single instance via ~/courier/result_reads/result_read.pid; skips while backup_selfcheck.sh is running.
# Log: ~/courier/result_reads/result_read.log.
#
# Env (tests): COURIER_HOME, COURIER_REPO, COURIER_CLAUDE_BIN, CLAUDE_CREDENTIALS_FILE, COURIER_MODEL,
#              RESULT_READ_CAP_S (default 900), RESULT_READ_PROMPT
# Exit codes: 0 ran or skipped cleanly; 3 run failed or timed out.
# shellcheck source=courier_lib.sh
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/courier_lib.sh"
set -u

RR_DIR="$COURIER_HOME/result_reads"
COURIER_LOG="$RR_DIR/result_read.log"
PIDFILE="$RR_DIR/result_read.pid"
CAP_S="${RESULT_READ_CAP_S:-900}"
PROMPT="${RESULT_READ_PROMPT:-$HERE/RESULT_READ_PROMPT.md}"
mkdir -p "$RR_DIR" "$COURIER_HOME/outbox"

if pid_alive "$PIDFILE"; then
  log "result read already running (pid $(cat "$PIDFILE")), skipping"; exit 0
fi
if pid_alive "$COURIER_HOME/selfcheck/selfcheck.pid"; then
  log "backup self-check running, skipping this slot"; exit 0
fi
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT

if ! claude_ready; then log "claude not ready ($(claude_not_ready_reason)), skipping"; exit 0; fi
[ -r "$PROMPT" ] || { log "prompt $PROMPT missing, skipping"; exit 0; }
[ -d "$COURIER_REPO" ] || { log "repo $COURIER_REPO missing, skipping"; exit 0; }

TS="$(date -u +%Y%m%dT%H%M%SZ)"
TRANSCRIPT="$RR_DIR/$TS.md"
log "starting result read (cap ${CAP_S}s, model $COURIER_MODEL) -> $TRANSCRIPT"
( cd "$COURIER_REPO" && run_with_timeout "$CAP_S" "$CLAUDE_BIN" -p "$(cat "$PROMPT")" \
    --model "$COURIER_MODEL" --permission-mode acceptEdits --output-format text ) \
    > "$TRANSCRIPT" 2>&1 < /dev/null
rc=$?
printf '\n\n---\n[result_read: exit=%s finished=%s]\n' "$rc" "$(utc_now)" >> "$TRANSCRIPT"
if [ "$rc" -eq 0 ]; then log "result read finished rc=0 -> $TRANSCRIPT"; exit 0; fi
log "result read FAILED/timed out rc=$rc -> $TRANSCRIPT"; exit 3
