#!/bin/bash
# Shared helpers for the message courier (sourced, not executed).
#
# The courier moves messages between the laptop Claude session and a headless
# Claude on the always-on helper VM, so neither agent does ssh itself:
#   laptop:  ~/courier_out/*.md  --push-->  VM ~/courier/inbox/
#   VM:      claude -p <inbox file>  -->  ~/courier/outbox/<name>.reply.md
#   laptop:  pulls ~/courier/outbox/*.reply.md  -->  ~/courier_in/
#
# Env overrides (all optional; the tests use them to run with no network):
#   COURIER_HOME             VM-side courier root      (default ~/courier)
#   COURIER_REPO             repo checkout to run in   (default ~/dream-state)
#   COURIER_CLAUDE_BIN       claude executable         (default: `claude` on PATH)
#   CLAUDE_CREDENTIALS_FILE  login marker              (default ~/.claude/.credentials.json)
#   COURIER_MODEL            model id                  (default claude-fable-5-1)

COURIER_HOME="${COURIER_HOME:-$HOME/courier}"
COURIER_REPO="${COURIER_REPO:-$HOME/dream-state}"
COURIER_MODEL="${COURIER_MODEL:-claude-fable-5-1}"
CLAUDE_BIN="${COURIER_CLAUDE_BIN:-claude}"
CLAUDE_CREDENTIALS_FILE="${CLAUDE_CREDENTIALS_FILE:-$HOME/.claude/.credentials.json}"

# Non-interactive shells (nohup, cron, `ssh host cmd`) do not load nvm or
# ~/.bashrc PATH additions, so make claude findable explicitly. Order: newest
# nvm node first (Claude Code >= 2.1.25x needs node >= 22 and the user's own
# `claude update` keeps that copy current), then ~/.npm-global (fallback copy).
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"
_nvm_latest="$(ls -d "$HOME"/.nvm/versions/node/v* 2>/dev/null | sort -V | tail -1)"
[ -n "$_nvm_latest" ] && [ -d "$_nvm_latest/bin" ] && export PATH="$_nvm_latest/bin:$PATH"
unset _nvm_latest

utc_now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
utc_stamp() { date -u +%Y%m%dT%H%M%SZ; }

# log MESSAGE...  -> appends a UTC-stamped line to $COURIER_LOG (if set) and stdout.
log() {
  local line
  line="$(utc_now) $*"
  echo "$line"
  [ -n "${COURIER_LOG:-}" ] && echo "$line" >> "$COURIER_LOG"
  return 0
}

# claude_ready -> 0 if the claude CLI runs and a login marker exists.
claude_ready() {
  command -v "$CLAUDE_BIN" >/dev/null 2>&1 || return 1
  "$CLAUDE_BIN" --version >/dev/null 2>&1 || return 1
  [ -f "$CLAUDE_CREDENTIALS_FILE" ] && return 0
  [ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] && return 0
  [ -n "${ANTHROPIC_API_KEY:-}" ] && return 0
  return 1
}

# claude_not_ready_reason -> one-line explanation for reply files / logs.
claude_not_ready_reason() {
  if ! command -v "$CLAUDE_BIN" >/dev/null 2>&1; then
    echo "claude CLI not found on PATH (${CLAUDE_BIN})"
  elif ! "$CLAUDE_BIN" --version >/dev/null 2>&1; then
    echo "claude CLI present but '--version' fails"
  else
    echo "claude installed but not logged in (no ${CLAUDE_CREDENTIALS_FILE} and no OAuth/API token in env)"
  fi
}

# run_with_timeout SECONDS CMD...  (GNU timeout, gtimeout, or a perl alarm fallback for macOS)
run_with_timeout() {
  local secs="$1"; shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "$secs" "$@"
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$secs" "$@"
  else
    perl -e 'alarm shift; exec @ARGV or die "exec failed: $!\n"' "$secs" "$@"
  fi
}

# file_age_s FILE -> seconds since last modification (Linux and macOS stat).
file_age_s() {
  local m
  m=$(stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null) || { echo 0; return 1; }
  echo $(( $(date +%s) - m ))
}

# pid_alive PIDFILE -> 0 if the pid recorded in PIDFILE is a live process.
pid_alive() {
  local pf="$1" pid
  [ -f "$pf" ] || return 1
  pid=$(cat "$pf" 2>/dev/null)
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}
