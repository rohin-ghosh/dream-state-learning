#!/bin/bash
# gpu/queue_status.sh -- one-screen status of the node-side GPU queue (run ON a node; QUEUE_DIR overrides ~/queue).
# Prints: runner pid/alive, node id, pending/running/done/failed/rejected counts, the running jobs (name gpu pid
# started), the pending jobs in launch order (with AFTER / NODE_ONLY), and the last 10 lines of runner.log.
QUEUE_DIR="${QUEUE_DIR:-$HOME/queue}"
count() { local n=0 f; for f in "$QUEUE_DIR/$1"/*.job; do [ -e "$f" ] && n=$((n+1)); done; echo "$n"; }
field() { sed -n "s/^$2=//p" "$1" | tail -1 | sed "s/^'\(.*\)'$/\1/"; }
strip_name() { local b; b=$(basename "$1" .job); echo "${b#[0-9][0-9][0-9][0-9]_}"; }
[ -d "$QUEUE_DIR" ] || { echo "no queue at $QUEUE_DIR (run gpu/queue_install.sh <node> first)"; exit 1; }

pid=$(cat "$QUEUE_DIR/runner.pid" 2>/dev/null)
if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then st="alive pid=$pid"; else st="NOT RUNNING${pid:+ (stale pid $pid)}"; fi
node=$(cat "$QUEUE_DIR/node_id" 2>/dev/null)
echo "runner: $st  node=${QUEUE_NODE:-${node:-unknown}}  queue=$QUEUE_DIR"
echo "pending=$(count pending) running=$(count running) done=$(count done) failed=$(count failed) rejected=$(count rejected)"

for f in "$QUEUE_DIR"/running/*.job; do
  [ -e "$f" ] || continue
  p=$(field "$f" PID); [ -n "$p" ] && kill -0 "$p" 2>/dev/null && a=alive || a=exited
  echo "  running  $(strip_name "$f")  gpu=$(field "$f" GPU)  pid=$p($a)  started=$(field "$f" STARTED)"
done
i=0
for f in "$QUEUE_DIR"/pending/*.job; do
  [ -e "$f" ] || continue
  i=$((i+1)); [ $i -gt 10 ] && { echo "  ... $(( $(count pending) - 10 )) more pending"; break; }
  extra=""; a=$(field "$f" AFTER); n=$(field "$f" NODE_ONLY); g=$(field "$f" NGPU)
  [ -n "$a" ] && extra="$extra after=$a"; [ -n "$n" ] && extra="$extra node=$n"; [ -n "$g" ] && [ "$g" != 1 ] && extra="$extra ngpu=$g"
  echo "  pending  $(strip_name "$f")$extra"
done
for f in "$QUEUE_DIR"/failed/*.job; do [ -e "$f" ] || continue; echo "  failed   $(strip_name "$f")  rc=$(field "$f" RC)  finished=$(field "$f" FINISHED)"; done | tail -5
for f in "$QUEUE_DIR"/rejected/*.job; do [ -e "$f" ] || continue; echo "  rejected $(strip_name "$f"): $(field "$f" REJECT_REASON)"; done | tail -3
echo "--- runner.log (last 10)"
tail -10 "$QUEUE_DIR/runner.log" 2>/dev/null || echo "(no runner.log yet)"
