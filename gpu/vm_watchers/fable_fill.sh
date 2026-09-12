#!/bin/bash
# fable_fill.sh — VM-side "subsidiary work" filler for idle GPUs (Rohin, 2026-09-12 ~08:20 UTC: "fill some of them …
# Astra has priority … stopped early with some interim result … make sure this isn't getting in the way of Astra's
# main runs").  Runs on the VM under `nohup setsid`; uses the node ssh wrappers and the node queues only.
#
# Each tick, for every node with a job list:
#   1. read the node's queue runner state: free GPUs (its own rule: no compute process, no life owning the GPU,
#      no runner job), pending jobs that are NOT ours, and our own pending+running jobs;
#   2. if the builder has ANY job pending, add nothing (its jobs must never queue behind ours);
#   3. otherwise enqueue at most (free - HEADROOM - ours_pending) jobs from the list, so HEADROOM GPUs per node
#      always stay free for the builder's immediate launches;
#   4. never within DEADLINE_MARGIN_H of the node's lease end; never kill anything; never touch a non-fable job.
# Job names carry the prefix fable_fill_ so the builder can delete pending ones (rm ~/queue/pending/*_fable_fill_*.job)
# or kill a running one (PID in ~/queue/running/<job>) whenever it needs the GPU. Results of jobs stopped early are
# INTERIM by definition and get no SEQ number (notebook, [Fable] 08:2x UTC).
# Lists: gpu/vm_watchers/fable_fill_node{1,2}.jobs (lines NAME|CMD; CMD uses {gpu} and ~ as queue_add.sh expects).
# State: ~/fable_fill/<node>.enqueued (names already submitted). Kill switch: ~/fable_fill.off. Log: ~/fable_fill.log.
# Usage: bash gpu/vm_watchers/fable_fill.sh [INTERVAL_S=600] [HEADROOM=2] [--once] [--dry-run]
set -u
INTERVAL="${1:-600}"; HEADROOM="${2:-2}"; ONCE=0; DRY=0
for a in "$@"; do [ "$a" = "--once" ] && ONCE=1; [ "$a" = "--dry-run" ] && DRY=1; done
REPO="$HOME/dream-state"; LOG="$HOME/fable_fill.log"; OFF="$HOME/fable_fill.off"; ST="$HOME/fable_fill"; mkdir -p "$ST"
DEADLINE_MARGIN_H=6
# node id -> ssh wrapper prefix, lease end (ISO with offset)
declare -A WRAP=( [1]=a40 [2]=ovx ); declare -A LEASE_END=( [1]="2026-09-14T16:14:00-07:00" [2]="2026-09-21T01:43:00-07:00" )
log() { echo "$(date -u +%FT%TZ) $*" >> "$LOG"; }
echo $$ > "$ST/pid"
log "start interval=${INTERVAL}s headroom=$HEADROOM once=$ONCE dry=$DRY"
while :; do
  if [ -f "$OFF" ]; then log "kill switch present; idle"; [ "$ONCE" = 1 ] && exit 0; sleep "$INTERVAL"; continue; fi
  for node in 1 2; do
    LIST="$REPO/gpu/vm_watchers/fable_fill_node${node}.jobs"; [ -f "$LIST" ] || continue
    ENQ="$ST/node${node}.enqueued"; touch "$ENQ"
    # remaining lease time
    end_epoch=$(date -d "${LEASE_END[$node]}" +%s 2>/dev/null || echo 0); now=$(date +%s)
    hours_left=$(( (end_epoch - now) / 3600 ))
    if [ "$hours_left" -lt "$DEADLINE_MARGIN_H" ]; then log "node$node: ${hours_left}h to lease end (< $DEADLINE_MARGIN_H); not adding"; continue; fi
    # node state in one ssh: free GPUs from the runner's last log line; pending non-fable; our pending+running
    state=$(timeout 60 bash "$REPO/gpu/${WRAP[$node]}_ssh.sh" 'f=$(tail -1 ~/queue/runner.log 2>/dev/null | grep -oE "free=[0-9]+" | cut -d= -f2); echo "free=${f:-?} builder_pending=$(ls ~/queue/pending 2>/dev/null | grep -vc fable_fill_) ours=$(ls ~/queue/pending ~/queue/running 2>/dev/null | grep -c fable_fill_) runner=$(pgrep -fc queue_runner.sh)"' 2>/dev/null)
    free=$(echo "$state" | grep -oE "free=[0-9]+" | cut -d= -f2); bp=$(echo "$state" | grep -oE "builder_pending=[0-9]+" | cut -d= -f2); ours=$(echo "$state" | grep -oE "ours=[0-9]+" | cut -d= -f2); runner=$(echo "$state" | grep -oE "runner=[0-9]+" | cut -d= -f2)
    if [ -z "$free" ] || [ -z "$bp" ]; then log "node$node: could not read state ($state)"; continue; fi
    if [ "${runner:-0}" -lt 1 ]; then log "node$node: queue runner not running; not adding"; continue; fi
    if [ "$bp" -gt 0 ]; then log "node$node: builder has $bp pending job(s); not adding (free=$free ours=$ours)"; continue; fi
    room=$(( free - HEADROOM - ours )); [ "$room" -lt 0 ] && room=0
    added=0
    while [ "$added" -lt "$room" ]; do
      line=$(grep -v '^\s*#' "$LIST" | grep -v '^\s*$' | while IFS='|' read -r name cmd; do grep -qx "$name" "$ENQ" || { echo "$name|$cmd"; break; }; done)
      [ -z "$line" ] && break
      name="${line%%|*}"; cmd="${line#*|}"
      if [ "$DRY" = 1 ]; then log "node$node DRY: would enqueue $name :: $cmd"; echo "$name" >> "$ENQ.dry"; added=$((added+1)); continue; fi
      out=$(timeout 60 bash "$REPO/gpu/${WRAP[$node]}_ssh.sh" "cd ~/dream-state && bash gpu/queue_add.sh $name '$cmd'" 2>&1 | tail -1)
      if echo "$out" | grep -q "pending/"; then echo "$name" >> "$ENQ"; log "node$node ENQUEUED $name (free=$free headroom=$HEADROOM ours_before=$ours) -> $out"; added=$((added+1)); ours=$((ours+1));
      else log "node$node enqueue FAILED for $name: $out"; echo "$name" >> "$ENQ"; fi
    done
    [ "$added" = 0 ] && log "node$node: free=$free ours=$ours builder_pending=$bp room=$room; nothing added"
  done
  [ "$ONCE" = 1 ] && exit 0
  sleep "$INTERVAL"
done
