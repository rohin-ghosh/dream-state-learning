#!/usr/bin/env bash
# Queue a repo-mailbox message for the VM poller.
#
# Usage:
#   bash tools/repo_mailbox/send_message.sh [--commit] [--push] "message"
#   bash tools/repo_mailbox/send_message.sh -f message.md --commit --push
#   bash tools/repo_mailbox/send_message.sh --action watch --commit --push
#   echo message | bash tools/repo_mailbox/send_message.sh - --commit --push
set -euo pipefail

usage() {
  sed -n '2,12p' "$0" >&2
  exit 2
}

repo="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "send_message: run inside a git checkout" >&2
  exit 1
}
cd "$repo"

action="send"
interrupt="true"
do_commit=0
do_push=0
file=""
stdin_mode=0
args=()

while [ $# -gt 0 ]; do
  case "$1" in
    --action)
      [ $# -ge 2 ] || usage
      action="$2"; shift 2 ;;
    --no-interrupt)
      interrupt="false"; shift ;;
    --commit)
      do_commit=1; shift ;;
    --push)
      do_commit=1; do_push=1; shift ;;
    -f|--file)
      [ $# -ge 2 ] || usage
      file="$2"; shift 2 ;;
    -)
      stdin_mode=1; shift ;;
    -h|--help)
      usage ;;
    --)
      shift; while [ $# -gt 0 ]; do args+=("$1"); shift; done ;;
    -*)
      usage ;;
    *)
      args+=("$1"); shift ;;
  esac
done

case "$action" in
  send|watch|resume|status) ;;
  *) echo "send_message: unsupported action '$action'" >&2; exit 2 ;;
esac

tmp_body="$(mktemp "${TMPDIR:-/tmp}/repo-mailbox-body.XXXXXX")"
trap 'rm -f "$tmp_body"' EXIT

if [ -n "$file" ]; then
  [ -r "$file" ] || { echo "send_message: cannot read $file" >&2; exit 1; }
  cp "$file" "$tmp_body"
elif [ "$stdin_mode" = 1 ]; then
  cat > "$tmp_body"
elif [ ${#args[@]} -gt 0 ]; then
  printf '%s\n' "${args[*]}" > "$tmp_body"
elif [ "$action" = "send" ]; then
  usage
else
  : > "$tmp_body"
fi

if [ "$action" = "send" ] && [ ! -s "$tmp_body" ]; then
  echo "send_message: empty send body" >&2
  exit 1
fi

mkdir -p mailbox/to_vm mailbox/from_vm
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
host="$(hostname 2>/dev/null | tr -cd 'A-Za-z0-9_.-' | cut -c1-40)"
[ -n "$host" ] || host="unknown-host"
suffix="$(printf '%04x' $(( RANDOM % 65536 )))"
id="${stamp}-${host}-${suffix}"
dest="mailbox/to_vm/${id}.md"
tmp="${dest}.tmp"
created="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

{
  echo "---"
  echo "schema: DREAM_REPO_MAILBOX_V1"
  echo "id: $id"
  echo "created_utc: $created"
  echo "from: operator"
  echo "target: astra2"
  echo "action: $action"
  echo "interrupt: $interrupt"
  echo "---"
  cat "$tmp_body"
} > "$tmp"
mv -f "$tmp" "$dest"

echo "$dest"

if [ "$do_commit" = 1 ]; then
  git add "$dest"
  git commit -m "mailbox: $action $id"
fi

if [ "$do_push" = 1 ]; then
  git push
fi
