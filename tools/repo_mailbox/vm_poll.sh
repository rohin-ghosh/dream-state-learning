#!/usr/bin/env bash
# VM-side repo mailbox poller. Pulls messages from mailbox/to_vm, talks to
# Astra's tmux session, writes replies to mailbox/from_vm, commits, and pushes.
set -euo pipefail

repo="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "vm_poll: run inside the VM repo checkout" >&2
  exit 1
}
cd "$repo"

interval="${REPO_MAILBOX_INTERVAL:-20}"
wait_seconds="${REPO_MAILBOX_WAIT_SECONDS:-900}"
session="${REPO_MAILBOX_SESSION:-astra2}"
remote="${REPO_MAILBOX_REMOTE:-origin}"
branch="${REPO_MAILBOX_BRANCH:-$(git symbolic-ref --short HEAD 2>/dev/null || echo main)}"
pidfile="${REPO_MAILBOX_PIDFILE:-$HOME/.repo_mailbox_vm.pid}"
logfile="${REPO_MAILBOX_LOG:-$HOME/repo_mailbox_vm.log}"
once=0
[ "${1:-}" = "--once" ] && once=1

to_dir="mailbox/to_vm"
from_dir="mailbox/from_vm"
run_dir="${TMPDIR:-/tmp}/repo_mailbox_vm"
mkdir -p "$to_dir" "$from_dir" "$run_dir"

log() {
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$logfile"
}

redact() {
  LC_ALL=C sed -E \
    -e 's/[a-zA-Z0-9._-]+\.nvidia\.com/[host]/g' \
    -e 's/[0-9]{1,3}(\.[0-9]{1,3}){3}/[ip]/g' \
    -e 's/sk-[A-Za-z0-9_-]+/[key]/g' \
    -e 's/(COLOSSUS_TOKEN=)[^[:space:]]+/\1[redacted]/g'
}

pid_alive() {
  [ -f "$1" ] || return 1
  pid="$(cat "$1" 2>/dev/null || true)"
  [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null
}

if pid_alive "$pidfile"; then
  echo "vm_poll already running (pid $(cat "$pidfile"))"
  exit 0
fi
echo $$ > "$pidfile"
trap 'rm -f "$pidfile"' EXIT

field() {
  key="$1"; file="$2"
  grep -m1 "^${key}:" "$file" 2>/dev/null | sed 's/^[^:]*:[[:space:]]*//; s/^"//; s/"$//'
}

body_file() {
  src="$1"; out="$2"
  awk '
    BEGIN { marks = 0; printing = 0 }
    /^---[[:space:]]*$/ {
      marks += 1
      if (marks == 2) { printing = 1; next }
      next
    }
    printing { print }
  ' "$src" > "$out"
  if [ ! -s "$out" ]; then
    cp "$src" "$out"
  fi
}

git_pull() {
  git pull --rebase --autostash "$remote" "$branch" >/dev/null 2>&1 || {
    log "WARN git pull failed"
    return 1
  }
}

commit_reply() {
  reply="$1"; id="$2"
  for attempt in 1 2 3; do
    git_pull || true
    git add "$reply"
    if GIT_AUTHOR_NAME="${GIT_AUTHOR_NAME:-repo-mailbox-vm}" \
       GIT_AUTHOR_EMAIL="${GIT_AUTHOR_EMAIL:-repo-mailbox-vm@local}" \
       GIT_COMMITTER_NAME="${GIT_COMMITTER_NAME:-repo-mailbox-vm}" \
       GIT_COMMITTER_EMAIL="${GIT_COMMITTER_EMAIL:-repo-mailbox-vm@local}" \
       git commit -m "mailbox reply: $id" >/dev/null 2>&1; then
      :
    else
      log "WARN git commit failed or no changes for $id"
      return 0
    fi
    if git push "$remote" "$branch" >/dev/null 2>&1; then
      log "pushed reply $id"
      return 0
    fi
    log "WARN git push failed for $id attempt=$attempt"
    sleep 5
  done
  log "ERROR could not push reply $id"
  return 1
}

pane_tail() {
  tmux capture-pane -p -t "$session" 2>&1 | grep -v '^[[:space:]]*$' | tail -n "${1:-80}" | cut -c1-220 | redact
}

write_reply() {
  reply="$1"; id="$2"; action="$3"; status="$4"; detail="$5"
  tmp="$reply.tmp"
  {
    echo "# Repo Mailbox Reply"
    echo
    echo "- id: $id"
    echo "- action: $action"
    echo "- status: $status"
    echo "- finished_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "- session: $session"
    [ -n "$detail" ] && echo "- detail: $detail"
    echo
    echo "## Astra Pane Tail"
    echo
    echo '```text'
    pane_tail 100
    echo '```'
  } > "$tmp"
  mv -f "$tmp" "$reply"
}

wait_for_idle() {
  deadline=$(( $(date +%s) + wait_seconds ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    if tmux capture-pane -p -t "$session" 2>/dev/null | grep -q 'esc to interrupt'; then
      sleep 20
    else
      return 0
    fi
  done
  return 1
}

deliver_send() {
  msg_file="$1"; interrupt="$2"; id="$3"
  direct="$run_dir/${id}.direct.txt"
  {
    now="$(date -u +%H:%MZ)"
    pdt="$(TZ=America/Los_Angeles date +%H:%M 2>/dev/null || date +%H:%M)"
    echo "[ROHIN -- repo mailbox, ${now} (${pdt} PDT); rulings and orders in this message take effect when read]"
    echo
    cat "$msg_file"
  } > "$direct"

  pane="$(tmux capture-pane -p -t "$session" 2>/dev/null || true)"
  if printf '%s\n' "$pane" | grep -q 'to scroll\|edit prev'; then
    tmux send-keys -t "$session" q
    sleep 1
  fi
  if [ "$interrupt" != "false" ] && tmux capture-pane -p -t "$session" | grep -q 'esc to interrupt'; then
    tmux send-keys -t "$session" Escape
    sleep 3
  fi
  if tmux capture-pane -p -t "$session" | grep -q 'Queued follow-up'; then
    tmux send-keys -t "$session" S-Left
    sleep 1
  fi

  tmux load-buffer "$direct"
  tmux paste-buffer -t "$session"
  sleep 8
  tmux send-keys -t "$session" Enter
  sleep 10
  for _ in 1 2 3; do
    if tmux capture-pane -p -t "$session" | grep -q 'Pasted Content\|take effect when read]'; then
      sleep 15
      tmux send-keys -t "$session" Enter
      sleep 8
    fi
  done
}

process_one() {
  file="$1"
  base="$(basename "$file" .md)"
  id="$(field id "$file")"
  [ -n "$id" ] || id="$base"
  reply="$from_dir/${id}.reply.md"
  [ -e "$reply" ] && return 0

  action="$(field action "$file")"
  [ -n "$action" ] || action="send"
  interrupt="$(field interrupt "$file")"
  [ -n "$interrupt" ] || interrupt="true"
  body="$run_dir/${id}.body.txt"
  body_file "$file" "$body"

  log "processing $id action=$action"

  if ! tmux has-session -t "$session" 2>/dev/null; then
    {
      echo "# Repo Mailbox Reply"
      echo
      echo "- id: $id"
      echo "- action: $action"
      echo "- status: error"
      echo "- finished_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "- detail: tmux session '$session' not found"
    } > "$reply"
    commit_reply "$reply" "$id"
    return 0
  fi

  case "$action" in
    send)
      deliver_send "$body" "$interrupt" "$id"
      if wait_for_idle; then
        write_reply "$reply" "$id" "$action" "finished" "Astra appeared idle before wait cap"
      else
        write_reply "$reply" "$id" "$action" "still-working" "wait cap reached; send action=watch later"
      fi ;;
    watch)
      write_reply "$reply" "$id" "$action" "ok" "captured pane tail only" ;;
    resume)
      if tmux capture-pane -p -t "$session" | grep -q 'esc to interrupt'; then
        write_reply "$reply" "$id" "$action" "busy" "Astra is mid-turn; not resumed"
      elif tmux capture-pane -p -t "$session" | grep -q 'Goal paused'; then
        tmux send-keys -t "$session" -l '/goal resume'
        sleep 1
        tmux send-keys -t "$session" Enter
        sleep 3
        write_reply "$reply" "$id" "$action" "sent" "sent /goal resume"
      else
        write_reply "$reply" "$id" "$action" "noop" "goal did not look paused"
      fi ;;
    status)
      tmp="$reply.tmp"
      {
        echo "# Repo Mailbox Reply"
        echo
        echo "- id: $id"
        echo "- action: status"
        echo "- status: ok"
        echo "- finished_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo
        echo "## Status"
        echo
        echo '```text'
        tmux ls 2>&1 | redact
        printf 'astra_watch_count='
        pgrep -fc '[a]stra_watch.sh' 2>/dev/null || true
        git log --oneline -1 2>/dev/null
        echo '```'
        echo
        echo "## Astra Pane Tail"
        echo
        echo '```text'
        pane_tail 80
        echo '```'
      } > "$tmp"
      mv -f "$tmp" "$reply" ;;
    *)
      {
        echo "# Repo Mailbox Reply"
        echo
        echo "- id: $id"
        echo "- action: $action"
        echo "- status: error"
        echo "- finished_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "- detail: unsupported action"
      } > "$reply" ;;
  esac

  commit_reply "$reply" "$id"
}

log "repo mailbox poller start pid=$$ repo=$repo branch=$branch session=$session"

while :; do
  git_pull || true
  for file in "$to_dir"/*.md; do
    [ -e "$file" ] || continue
    process_one "$file"
  done
  [ "$once" = 1 ] && break
  sleep "$interval"
done
