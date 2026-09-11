#!/bin/bash
# gpu/queue_install.sh [NODE_ID] -- run ON a node: create ~/queue/{pending,running,done,failed,rejected,logs}, record
# the node id (1 = 8xA40 node reached by gpu/a40_ssh.sh, 2 = OVX node reached by gpu/ovx_ssh.sh; needed for
# NODE_ONLY= jobs -- both nodes report the same GPU model so it cannot be auto-detected), and start
# gpu/queue_runner.sh under `nohup setsid` if no runner is alive. Prints the runner pid. Idempotent.
#   from the laptop:  bash gpu/a40_ssh.sh 'cd ~/dream-state && bash gpu/queue_install.sh 1'
#                     bash gpu/ovx_ssh.sh 'cd ~/dream-state && bash gpu/queue_install.sh 2'
# Env: QUEUE_DIR (~/queue)  QUEUE_INTERVAL (60 s, passed to the runner)  QUEUE_RESERVE_PATTERNS (see runner header)
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUEUE_DIR="${QUEUE_DIR:-$HOME/queue}"
mkdir -p "$QUEUE_DIR"/{pending,running,done,failed,rejected,logs}
if [ -n "${1:-}" ]; then
  [[ "$1" =~ ^[12]$ ]] || { echo "queue_install: NODE_ID must be 1 or 2" >&2; exit 2; }
  echo "$1" > "$QUEUE_DIR/node_id"
fi
node=$(cat "$QUEUE_DIR/node_id" 2>/dev/null)
[ -n "$node" ] || echo "queue_install: WARNING no node id (pass 1 or 2); NODE_ONLY= jobs will be held" >&2
command -v nvidia-smi >/dev/null 2>&1 || echo "queue_install: WARNING nvidia-smi not on PATH; the runner will see no free GPUs" >&2
command -v setsid >/dev/null 2>&1 || echo "queue_install: WARNING setsid not found; using plain nohup" >&2

pid=$(cat "$QUEUE_DIR/runner.pid" 2>/dev/null)
if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && ps -p "$pid" -o command= 2>/dev/null | grep -q queue_runner; then
  echo "queue runner already running: pid=$pid node=${node:-unknown} queue=$QUEUE_DIR"
  exit 0
fi
if command -v setsid >/dev/null 2>&1; then
  nohup setsid bash "$HERE/queue_runner.sh" >> "$QUEUE_DIR/runner.out" 2>&1 < /dev/null &
else
  nohup bash "$HERE/queue_runner.sh" >> "$QUEUE_DIR/runner.out" 2>&1 < /dev/null &
fi
for i in 1 2 3 4 5 6 7 8 9 10; do
  pid=$(cat "$QUEUE_DIR/runner.pid" 2>/dev/null)
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && break
  sleep 0.5
done
if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
  echo "queue runner started: pid=$pid node=${node:-unknown} queue=$QUEUE_DIR log=$QUEUE_DIR/runner.log"
else
  echo "queue_install: runner did not start; see $QUEUE_DIR/runner.out" >&2; tail -5 "$QUEUE_DIR/runner.out" 2>/dev/null >&2; exit 1
fi
