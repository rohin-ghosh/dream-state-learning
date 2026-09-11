#!/bin/bash
# Queue a message for the Claude agent on the VM. The laptop agent calls this
# instead of doing any ssh: it just drops a file; courier_laptop.sh ships it and
# the reply later appears in ~/courier_in/<same name>.reply.md.
#
# Usage:  send_to_vm.sh 'message text'
#         send_to_vm.sh -f FILE            (file contents become the message)
#         echo text | send_to_vm.sh -      (read message from stdin)
# Env:    COURIER_OUT (default ~/courier_out)
# Prints the path of the queued message.
set -u
OUT="${COURIER_OUT:-$HOME/courier_out}"
mkdir -p "$OUT"

usage() { echo "usage: $0 'message text' | $0 -f FILE | ... | $0 -" >&2; exit 2; }
[ $# -ge 1 ] || usage

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
suffix="$(printf '%04x' $(( RANDOM % 65536 )))"
name="msg-${stamp}-${suffix}"
dest="$OUT/$name.md"
tmp="$dest.tmp"

case "$1" in
  -f)
    [ $# -eq 2 ] || usage
    [ -r "$2" ] || { echo "send_to_vm: cannot read $2" >&2; exit 1; }
    cp "$2" "$tmp" ;;
  -)
    cat > "$tmp" ;;
  -*)
    usage ;;
  *)
    printf '%s\n' "$*" > "$tmp" ;;
esac

if [ ! -s "$tmp" ]; then rm -f "$tmp"; echo "send_to_vm: empty message, nothing queued" >&2; exit 1; fi
mv -f "$tmp" "$dest"
echo "$dest"
