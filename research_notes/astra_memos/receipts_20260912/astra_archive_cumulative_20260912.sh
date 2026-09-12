set -euo pipefail
root="$HOME/astra_diagnostics/astra_cumulative_20260912_attempt1"
archive=/tmp/astra_cumulative_terminal_20260912.tgz
test -f "$root/MAIN_TERMINAL_AUDIT.json"
test -f "$root/report.json"
test ! -e "$archive"
tar --exclude='*/adapter' -czf "$archive" -C "$HOME/astra_diagnostics" \
  astra_cumulative_20260912_attempt1 \
  astra_cumulative_20260912_attempt1_launch
tar -tzf "$archive" >/tmp/astra_cumulative_terminal_20260912.members
if grep -E '/adapter(/|$)|\.safetensors$' /tmp/astra_cumulative_terminal_20260912.members; then
  printf '%s\n' 'Unexpected weights in metadata-only capture; preserve and inspect.' >&2
  exit 1
fi
sha256sum "$archive"
wc -c "$archive"
