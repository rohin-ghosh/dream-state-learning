#!/bin/bash
# gpu/queue_add.sh NAME 'CMD' [NGPU] -- enqueue a GPU job for gpu/queue_runner.sh on THIS machine (run it on the node,
# e.g. bash gpu/a40_ssh.sh 'cd ~/dream-state && bash gpu/queue_add.sh NAME '"'"'CMD'"'"''). Writes
# ~/queue/pending/<seq>_<NAME>.job (zero-padded sequence => lexical order == submission order) and prints the path.
#   CMD   runs as `cd ~/dream-state; export CUDA_VISIBLE_DEVICES=<g> GPU=<g> GPUS=<g>; CMD` with {gpu} -> <g>.
#         Quote it with single quotes so $HOME etc. expand on the node at run time, not now.
#   NGPU  GPUs needed (default 1); {gpu} then becomes the comma list, e.g. "2,3".
# Optional, via environment:  AFTER=<job NAME>  NODE_ONLY=<1|2>  MIN_FREE_MIN=<minutes>  QUEUE_DIR (~/queue)
# Refused here (exit 2), never written: CMD containing run_life_v2 / R6_ / R7_ / bootstrap (lives are launched by
# hand, never by automation); a NAME already pending or running; a NAME outside [A-Za-z0-9._-].
# Example:
#   bash gpu/queue_add.sh f_neg64_b1 'RUN=$HOME/v6_out/memory_dose_D32 F_CELLS=F_r16k16_neg64 F_BANKS=1 F_TOKEN_BUDGET=250000 FORCE=1 bash gpu/memory_dose_frames.sh {gpu} fits'
NAME="${1:?usage: queue_add.sh NAME 'CMD' [NGPU]}"; CMD="${2:?usage: queue_add.sh NAME 'CMD' [NGPU]}"; NGPU="${3:-1}"
QUEUE_DIR="${QUEUE_DIR:-$HOME/queue}"; PENDING="$QUEUE_DIR/pending"
mkdir -p "$PENDING" "$QUEUE_DIR/running" "$QUEUE_DIR/done" "$QUEUE_DIR/failed" "$QUEUE_DIR/rejected" "$QUEUE_DIR/logs"

[[ "$NAME" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "queue_add: NAME must match [A-Za-z0-9._-]+ (got '$NAME')" >&2; exit 2; }
[[ "$NGPU" =~ ^[1-9][0-9]*$ ]] || { echo "queue_add: NGPU must be a positive integer (got '$NGPU')" >&2; exit 2; }
[ -z "${AFTER:-}" ] || [[ "$AFTER" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "queue_add: AFTER must be a job NAME" >&2; exit 2; }
[ -z "${NODE_ONLY:-}" ] || [[ "$NODE_ONLY" =~ ^[123]$ ]] || { echo "queue_add: NODE_ONLY must be 1, 2 or 3" >&2; exit 2; }
[ -z "${MIN_FREE_MIN:-}" ] || [[ "$MIN_FREE_MIN" =~ ^[0-9]+$ ]] || { echo "queue_add: MIN_FREE_MIN must be an integer (minutes)" >&2; exit 2; }
lc=$(printf '%s' "$CMD" | tr 'A-Z' 'a-z')
for tok in run_life_v2 r6_ r7_ bootstrap; do
  case "$lc" in *"$tok"*) echo "queue_add: REFUSED -- CMD contains '$tok'; lives and bootstrapped children are never launched by automation" >&2; exit 2;; esac
done
for f in "$PENDING"/*_"$NAME".job "$PENDING/$NAME.job" "$QUEUE_DIR/running"/*_"$NAME".job "$QUEUE_DIR/running/$NAME.job"; do
  [ -e "$f" ] && { echo "queue_add: a job named '$NAME' is already pending or running ($f); pick another NAME" >&2; exit 2; }
done

# sequence: max of the counter file and every prefixed job file in any state, plus one
seq=0
[ -f "$QUEUE_DIR/seq" ] && seq=$(tr -dc '0-9' < "$QUEUE_DIR/seq")
for f in "$QUEUE_DIR"/{pending,running,done,failed,rejected}/[0-9][0-9][0-9][0-9]_*.job; do
  [ -e "$f" ] || continue
  b=$(basename "$f"); n=$((10#${b:0:4}))
  [ "$n" -gt "${seq:-0}" ] && seq=$n
done
seq=$(( ${seq:-0} + 1 )); printf '%d\n' "$seq" > "$QUEUE_DIR/seq"
out="$PENDING/$(printf '%04d' "$seq")_$NAME.job"

esc=$(printf '%s' "$CMD" | sed "s/'/'\\\\''/g")            # ' -> '\'' so the file sources back to the exact CMD
tmp="$out.tmp.$$"
{
  echo "# queued $(date -u '+%Y-%m-%dT%H:%M:%SZ') by queue_add.sh on this node"
  echo "NAME=$NAME"
  echo "CMD='$esc'"
  echo "NGPU=$NGPU"
  [ -n "${NODE_ONLY:-}" ] && echo "NODE_ONLY=$NODE_ONLY"
  [ -n "${AFTER:-}" ] && echo "AFTER=$AFTER"
  [ -n "${MIN_FREE_MIN:-}" ] && echo "MIN_FREE_MIN=$MIN_FREE_MIN"
  true
} > "$tmp" && mv "$tmp" "$out"                             # atomic: the runner never sees a half-written file
echo "$out"
