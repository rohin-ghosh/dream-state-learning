#!/bin/bash
# Offline tests for tools/courier: syntax of every script, send_to_vm.sh file
# creation/naming, and the heartbeat-staleness logic of backup_selfcheck.sh with
# a fake heartbeat and a fake `claude` (no network, no real claude).
# Run: bash tests/test_courier.sh        -> prints "N/M passed", exit 1 on failure.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
C="$REPO/tools/courier"
T="$(mktemp -d "${TMPDIR:-/tmp}/courier_test.XXXXXX")"
trap 'rm -rf "$T"' EXIT
pass=0; total=0
ok()   { total=$((total+1)); pass=$((pass+1)); echo "ok   - $1"; }
fail() { total=$((total+1)); echo "FAIL - $1"; }
check() { if eval "$2"; then ok "$1"; else fail "$1"; fi; }

# --- 1. every script is bash -n clean --------------------------------------------
for s in courier_lib.sh courier_vm.sh courier_laptop.sh send_to_vm.sh backup_selfcheck.sh courier_install_vm.sh sync_repo_to_vm.sh; do
  check "bash -n $s" "bash -n '$C/$s' 2>/dev/null"
done
check "SELFCHECK_PROMPT.md starts with the self-check header" \
  "head -c 60 '$C/SELFCHECK_PROMPT.md' | grep -q '^Self-check for the dream-state project'"

# --- 2. send_to_vm.sh ---------------------------------------------------------------
export COURIER_OUT="$T/courier_out"
p1="$(bash "$C/send_to_vm.sh" 'hello vm agent')"
check "send_to_vm text: prints path of created file" "[ -n '$p1' ] && [ -f '$p1' ]"
check "send_to_vm text: name matches msg-<UTC>-<hex>.md" \
  "basename '$p1' | grep -Eq '^msg-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{4}\.md$'"
check "send_to_vm text: content is the message" "[ \"\$(cat '$p1')\" = 'hello vm agent' ]"
check "send_to_vm text: no .tmp left behind" "! ls '$COURIER_OUT'/*.tmp >/dev/null 2>&1"
printf 'line one\nline two\n' > "$T/msg.txt"
p2="$(bash "$C/send_to_vm.sh" -f "$T/msg.txt")"
check "send_to_vm -f: file created with identical content" "[ -f '$p2' ] && cmp -s '$p2' '$T/msg.txt'"
check "send_to_vm -f: distinct name from first message" "[ '$p1' != '$p2' ]"
check "send_to_vm: two .md files queued" "[ \$(ls '$COURIER_OUT'/*.md | wc -l) -eq 2 ]"
check "send_to_vm -f missing file fails" "! bash '$C/send_to_vm.sh' -f '$T/nope.txt' >/dev/null 2>&1"
check "send_to_vm no args fails with usage" "! bash '$C/send_to_vm.sh' >/dev/null 2>&1"
p3="$(printf 'from stdin' | bash "$C/send_to_vm.sh" -)"
check "send_to_vm -: reads stdin" "[ \"\$(cat '$p3')\" = 'from stdin' ]"
unset COURIER_OUT

# --- 3. backup_selfcheck.sh staleness logic with fake claude -----------------------------
FAKEBIN="$T/fakebin"; mkdir -p "$FAKEBIN"
cat > "$FAKEBIN/claude" <<'EOF'
#!/bin/bash
if [ "${1:-}" = "--version" ]; then echo "0.0.0-fake (Claude Code)"; exit 0; fi
printf '%s\n' "$@" > "$FAKE_ARGS_FILE"
echo "FAKE CLAUDE RAN"
EOF
chmod +x "$FAKEBIN/claude"
export COURIER_HOME="$T/courier" COURIER_REPO="$T/repo" COURIER_CLAUDE_BIN="$FAKEBIN/claude"
export CLAUDE_CREDENTIALS_FILE="$T/fake_credentials.json" FAKE_ARGS_FILE="$T/claude_args.txt"
export SELFCHECK_CAP_S=20
unset CLAUDE_CODE_OAUTH_TOKEN ANTHROPIC_API_KEY
mkdir -p "$COURIER_HOME" "$COURIER_REPO"; echo '{}' > "$CLAUDE_CREDENTIALS_FILE"
SC="$C/backup_selfcheck.sh"
LOGF="$COURIER_HOME/selfcheck/selfcheck.log"

# 3a fresh heartbeat -> skip, claude not invoked
date -u +%s > "$COURIER_HOME/laptop_heartbeat"; rm -f "$FAKE_ARGS_FILE"
bash "$SC" >/dev/null 2>&1; rc=$?
check "fresh heartbeat: exit 0" "[ $rc -eq 0 ]"
check "fresh heartbeat: log says laptop alive, skipping" "grep -q 'laptop alive, skipping' '$LOGF'"
check "fresh heartbeat: fake claude NOT invoked" "[ ! -f '$FAKE_ARGS_FILE' ]"
check "fresh heartbeat: no selfcheck transcript written" "! ls '$COURIER_HOME'/selfcheck/*.md >/dev/null 2>&1"

# 3b heartbeat 44 min old -> still alive (boundary below 45)
echo $(( $(date -u +%s) - 44*60 )) > "$COURIER_HOME/laptop_heartbeat"
bash "$SC" >/dev/null 2>&1
check "44-min heartbeat: fake claude NOT invoked" "[ ! -f '$FAKE_ARGS_FILE' ]"

# 3c heartbeat 46 min old -> stale, claude invoked with the right flags, transcript written
echo $(( $(date -u +%s) - 46*60 )) > "$COURIER_HOME/laptop_heartbeat"
bash "$SC" >/dev/null 2>&1; rc=$?
check "stale heartbeat: exit 0" "[ $rc -eq 0 ]"
check "stale heartbeat: fake claude invoked" "[ -f '$FAKE_ARGS_FILE' ]"
check "stale heartbeat: passes --model claude-fable-5-1" "grep -qx 'claude-fable-5-1' '$FAKE_ARGS_FILE' && grep -qx -- '--model' '$FAKE_ARGS_FILE'"
check "stale heartbeat: passes --permission-mode acceptEdits" "grep -qx 'acceptEdits' '$FAKE_ARGS_FILE' && grep -qx -- '--permission-mode' '$FAKE_ARGS_FILE'"
check "stale heartbeat: prompt is SELFCHECK_PROMPT.md text" "grep -q '^Self-check for the dream-state project' '$FAKE_ARGS_FILE'"
tr_file="$(ls "$COURIER_HOME"/selfcheck/*.md 2>/dev/null | head -1)"
check "stale heartbeat: transcript <ts>.md written" "[ -n '$tr_file' ] && basename '$tr_file' | grep -Eq '^[0-9]{8}T[0-9]{6}Z\.md$'"
check "stale heartbeat: transcript contains claude output" "grep -q 'FAKE CLAUDE RAN' '$tr_file'"
check "stale heartbeat: transcript has exit footer" "grep -q 'backup_selfcheck: exit=0' '$tr_file'"
check "stale heartbeat: copy dropped in outbox as *.reply.md" "ls '$COURIER_HOME'/outbox/selfcheck-*-transcript.reply.md >/dev/null 2>&1"
check "stale heartbeat: log records stale age" "grep -q 'laptop heartbeat stale' '$LOGF'"

# 3d missing heartbeat -> treated as stale
rm -f "$COURIER_HOME/laptop_heartbeat" "$FAKE_ARGS_FILE"
bash "$SC" >/dev/null 2>&1
check "missing heartbeat: treated as stale (claude invoked)" "[ -f '$FAKE_ARGS_FILE' ]"
check "missing heartbeat: log says no laptop heartbeat file" "grep -q 'no laptop heartbeat file' '$LOGF'"

# 3e stale but claude not logged in -> skip with reason
echo $(( $(date -u +%s) - 3600 )) > "$COURIER_HOME/laptop_heartbeat"
rm -f "$FAKE_ARGS_FILE" "$CLAUDE_CREDENTIALS_FILE"
bash "$SC" >/dev/null 2>&1; rc=$?
check "stale + not logged in: exit 0, claude NOT invoked" "[ $rc -eq 0 ] && [ ! -f '$FAKE_ARGS_FILE' ]"
check "stale + not logged in: log says claude not ready" "grep -q 'claude not ready' '$LOGF'"

# 3f stale, logged in, but claude binary missing -> skip
echo '{}' > "$CLAUDE_CREDENTIALS_FILE"
COURIER_CLAUDE_BIN="$T/no_such_claude" bash "$SC" >/dev/null 2>&1; rc=$?
check "stale + no claude binary: exit 0, not invoked" "[ $rc -eq 0 ] && [ ! -f '$FAKE_ARGS_FILE' ]"

# 3g run cap: a claude that hangs is killed by the timeout wrapper
cat > "$FAKEBIN/claude" <<'EOF'
#!/bin/bash
if [ "${1:-}" = "--version" ]; then echo "0.0.0-fake"; exit 0; fi
sleep 30
EOF
SELFCHECK_CAP_S=2 bash "$SC" >/dev/null 2>&1; rc=$?
check "run cap: hung claude is timed out (non-zero exit reported)" "[ $rc -eq 3 ]"

# --- 4. courier_vm.sh --once with fake claude (no network) --------------------------------
cat > "$FAKEBIN/claude" <<'EOF'
#!/bin/bash
if [ "${1:-}" = "--version" ]; then echo "0.0.0-fake"; exit 0; fi
shift; echo "REPLY TO: $1"
EOF
mkdir -p "$COURIER_HOME/inbox"; printf 'ping from laptop' > "$COURIER_HOME/inbox/msg-test.md"
COURIER_SETTLE_S=0 bash "$C/courier_vm.sh" --once >/dev/null 2>&1
check "courier_vm --once: reply written as <name>.reply.md" "[ -f '$COURIER_HOME/outbox/msg-test.reply.md' ]"
check "courier_vm --once: reply contains claude output for the message" "grep -q 'REPLY TO: ping from laptop' '$COURIER_HOME/outbox/msg-test.reply.md'"
check "courier_vm --once: message moved to processed/" "[ -f '$COURIER_HOME/processed/msg-test.md' ] && [ ! -e '$COURIER_HOME/inbox/msg-test.md' ]"
check "courier_vm --once: pid file removed on exit" "[ ! -f '$COURIER_HOME/courier_vm.pid' ]"
rm -f "$CLAUDE_CREDENTIALS_FILE"; printf 'second' > "$COURIER_HOME/inbox/msg-nologin.md"
COURIER_SETTLE_S=0 bash "$C/courier_vm.sh" --once >/dev/null 2>&1
check "courier_vm --once, not logged in: reply explains claude not ready" "grep -q 'not logged in' '$COURIER_HOME/outbox/msg-nologin.reply.md'"

echo "$pass/$total passed"
[ "$pass" -eq "$total" ]
