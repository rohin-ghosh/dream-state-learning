#!/bin/bash
# gpu/queue_runner.sh -- node-side GPU job queue runner. Runs ON a node under `nohup setsid`; the laptop is not
# in the loop (2026-09-11: the laptop slept nine hours and the laptop-driven scheduler stopped launching GPU work).
#
# WHAT IT DOES (one pass every QUEUE_INTERVAL=60 s)
#   1. Finalize: every job in ~/queue/running/ whose process has exited moves to ~/queue/done/ (exit code 0) or
#      ~/queue/failed/ (non-zero or unknown), with RC= and FINISHED= appended to the job file.
#   2. Discover free GPUs (see RULES).
#   3. Scan ~/queue/pending/*.job in lexical order (queue_add.sh gives files a zero-padded sequence prefix) and
#      launch each eligible job onto the next free GPU(s). A job that needs more GPUs than are free waits; smaller
#      jobs behind it may start first (backfill) -- use AFTER= when strict ordering matters.
#   4. Append one line to ~/queue/runner.log only when something changed (launch / finish / reject / free count).
#
# RULES BAKED IN (research_loop/COORDINATION.md; the daemon prompt)
#   * A GPU is FREE only if (a) `nvidia-smi --query-compute-apps` reports no process on it AND (b) no process on the
#     node matching QUEUE_RESERVE_PATTERNS (default: organism_v6.run_life_v2 lives) has CUDA_VISIBLE_DEVICES equal to
#     that index in /proc/<pid>/environ -- lives own their GPU even when momentarily at 0 MiB (engine restart,
#     sleep/compile phases) AND (c) no job this runner launched on it is still alive. A python life with no
#     CUDA_VISIBLE_DEVICES at all is assumed to sit on GPU 0 (CUDA default) and reserves it.
#   * The runner NEVER kills anything (the only signal it sends is `kill -0`, a liveness probe).
#   * The runner NEVER launches lives: a job whose CMD contains `run_life_v2`, `R6_`, `R7_` or `bootstrap` (any
#     case) is moved to ~/queue/rejected/ with REJECT_REASON= appended (Codex STOP: bootstrapped / parented clean
#     children are never launched by automation). Lives are launched by hand, by a human-supervised session.
#   * One job per GPU. A job declares NGPU (default 1); the runner sets CUDA_VISIBLE_DEVICES to the comma list of
#     the GPUs it got and also exports GPU=<first index> and GPUS=<comma list>; `{gpu}` (and `{gpus}`) in CMD are
#     replaced by the comma list (a single index when NGPU=1), because our runbooks take the GPU index as $1.
#   * Single instance per node via ~/queue/runner.pid (exit 1 if another runner is alive). On (re)start the runner
#     re-adopts ~/queue/running/ jobs whose pid is alive and finalizes the rest (exit code from logs/<NAME>.rc if the
#     job finished while the runner was down, else failed with RC=unknown).
#
# JOB FILE (small, bash-sourced; written by gpu/queue_add.sh)
#   NAME=f_neg64_b1                  # [A-Za-z0-9._-]+ ; log is ~/queue/logs/<NAME>.out, script ~/queue/logs/<NAME>.sh
#   CMD='... bash gpu/memory_dose_frames.sh {gpu} fits'   # runs as: cd ~/dream-state; export CUDA_VISIBLE_DEVICES=..; CMD
#   NGPU=1                           # GPUs needed (default 1)
#   NODE_ONLY=1                      # optional: run only on node 1|2 (node id: QUEUE_NODE env or ~/queue/node_id,
#                                    #           written by `bash gpu/queue_install.sh <node>`; unknown id => job waits)
#   AFTER=stage0_D32                 # optional: start only once ~/queue/done/*_<AFTER>.job (or <AFTER>.job) exists;
#                                    #           if that job FAILED the dependent waits forever (logged once)
#   MIN_FREE_MIN=30                  # optional: parsed and IGNORED for now (reserved for a lease-end guard)
#
# USAGE
#   install / start (on the node):   bash gpu/queue_install.sh <1|2>        # mkdirs, nohup setsid runner, prints pid
#   add a job (on the node):         bash gpu/queue_add.sh NAME 'CMD' [NGPU]  # AFTER= NODE_ONLY= MIN_FREE_MIN= via env
#   status (on the node):            bash gpu/queue_status.sh
#   from the laptop:                 bash gpu/a40_ssh.sh 'cd ~/dream-state && bash gpu/queue_status.sh'   (node 1)
#                                    bash gpu/ovx_ssh.sh 'cd ~/dream-state && bash gpu/queue_status.sh'   (node 2)
#   run the loop by hand:            bash gpu/queue_runner.sh              (QUEUE_LOOP_ONCE=1 for a single pass)
#
# EXAMPLE (car test, negatives cell, bank 1, on whichever GPU frees first)
#   bash gpu/queue_add.sh f_neg64_b1 'RUN=$HOME/v6_out/memory_dose_D32 F_CELLS=F_r16k16_neg64 F_BANKS=1 F_TOKEN_BUDGET=250000 FORCE=1 bash gpu/memory_dose_frames.sh {gpu} fits'
#   -> ~/queue/pending/0001_f_neg64_b1.job ; on launch the runner writes ~/queue/logs/f_neg64_b1.sh:
#        cd "$HOME/dream-state" || exit 97
#        export CUDA_VISIBLE_DEVICES=5 GPU=5 GPUS=5
#        RUN=$HOME/v6_out/memory_dose_D32 F_CELLS=F_r16k16_neg64 F_BANKS=1 F_TOKEN_BUDGET=250000 FORCE=1 bash gpu/memory_dose_frames.sh 5 fits
#      and runs it detached: nohup setsid bash -c '...' > ~/queue/logs/f_neg64_b1.out 2>&1 < /dev/null &
#
# ENV KNOBS  QUEUE_DIR (~/queue)  QUEUE_REPO (~/dream-state)  QUEUE_INTERVAL (60)  QUEUE_NODE (1|2)
#            QUEUE_RESERVE_PATTERNS ("run_life_v2"; space-separated pgrep -f patterns whose CUDA_VISIBLE_DEVICES reserve GPUs)
#            QUEUE_FAKE_FREE_GPUS ("0,1"; TESTING ONLY -- skips nvidia-smi and /proc, these indices are the whole node)
#            QUEUE_LOOP_ONCE (1 = one pass then exit)
# Plain bash (3.2+ so the test runs on a Mac; nodes have 5.2), nvidia-smi, pgrep, ps, tr, sed, awk. No python.
# No hostnames or IPs in this file: it runs on the node.

QUEUE_DIR="${QUEUE_DIR:-$HOME/queue}"
REPO="${QUEUE_REPO:-$HOME/dream-state}"
INTERVAL="${QUEUE_INTERVAL:-60}"
RESERVE_PATTERNS="${QUEUE_RESERVE_PATTERNS:-run_life_v2}"
FORBIDDEN_TOKENS="run_life_v2 R6_ R7_ bootstrap"     # case-insensitive match on CMD
PENDING="$QUEUE_DIR/pending"; RUNNING="$QUEUE_DIR/running"; DONE="$QUEUE_DIR/done"
FAILED="$QUEUE_DIR/failed"; REJECTED="$QUEUE_DIR/rejected"; LOGS="$QUEUE_DIR/logs"
RUNNER_LOG="$QUEUE_DIR/runner.log"; PIDFILE="$QUEUE_DIR/runner.pid"
if command -v setsid >/dev/null 2>&1; then DETACH="nohup setsid"; else DETACH="nohup"; fi   # Mac (tests) has no setsid

now() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }
log() { printf '%s %s\n' "$(now)" "$*" >> "$RUNNER_LOG"; }
field() { sed -n "s/^$2=//p" "$1" | tail -1; }          # last value of KEY= in a job file (values we append are unquoted)
pid_alive() { [ -n "$1" ] && kill -0 "$1" 2>/dev/null; }
pid_cmd() { ps -p "$1" -o command= 2>/dev/null; }
count_files() { local n=0 f; for f in "$1"/*.job; do [ -e "$f" ] && n=$((n+1)); done; echo "$n"; }
node_id() {
  if [ -n "${QUEUE_NODE:-}" ]; then echo "$QUEUE_NODE"
  elif [ -f "$QUEUE_DIR/node_id" ]; then tr -d ' \n' < "$QUEUE_DIR/node_id"; fi
}
strip_name() { local b; b=$(basename "$1" .job); echo "${b#[0-9][0-9][0-9][0-9]_}"; }   # 0001_name.job -> name

# ---- single instance ------------------------------------------------------------------------------------------
acquire_pidfile() {
  local old
  if [ -f "$PIDFILE" ]; then
    old=$(tr -d ' \n' < "$PIDFILE")
    if [ -n "$old" ] && [ "$old" != "$$" ] && pid_alive "$old"; then
      case "$(pid_cmd "$old")" in
        *queue_runner*) echo "queue_runner: another runner is alive (pid $old, $PIDFILE); exiting" >&2; exit 1;;
      esac
    fi
  fi
  echo "$$" > "$PIDFILE"
  trap 'rm -f "$PIDFILE"' EXIT
}

# ---- job files -------------------------------------------------------------------------------------------------
read_job() {  # $1 = job file -> sets NAME CMD NGPU NODE_ONLY AFTER MIN_FREE_MIN ; returns 1 if it does not source
  local out i=0 line
  out=$( ( NAME=; CMD=; NGPU=1; NODE_ONLY=; AFTER=; MIN_FREE_MIN=
           . "$1" >/dev/null 2>&1 || exit 1
           printf '%q\n' "$NAME" "$CMD" "$NGPU" "$NODE_ONLY" "$AFTER" "$MIN_FREE_MIN" ) ) || return 1
  NAME=; CMD=; NGPU=1; NODE_ONLY=; AFTER=; MIN_FREE_MIN=
  while IFS= read -r line; do
    case $i in
      0) eval "NAME=$line";; 1) eval "CMD=$line";; 2) eval "NGPU=$line";;
      3) eval "NODE_ONLY=$line";; 4) eval "AFTER=$line";; 5) eval "MIN_FREE_MIN=$line";;
    esac
    i=$((i+1))
  done <<< "$out"
  [ -n "$NAME" ] || NAME=$(strip_name "$1")
  return 0
}

validate_job() {  # uses NAME CMD NGPU NODE_ONLY, TOTAL_GPUS -> echoes a reject reason or nothing
  local tok lc
  [[ "$NAME" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "bad NAME '$NAME' (allowed: A-Z a-z 0-9 . _ -)"; return; }
  [ -n "$CMD" ] || { echo "empty CMD"; return; }
  [[ "$NGPU" =~ ^[1-9][0-9]*$ ]] || { echo "NGPU must be a positive integer (got '$NGPU')"; return; }
  [ -z "$NODE_ONLY" ] || [[ "$NODE_ONLY" =~ ^[12]$ ]] || { echo "NODE_ONLY must be 1 or 2 (got '$NODE_ONLY')"; return; }
  lc=$(printf '%s' "$CMD" | tr 'A-Z' 'a-z')
  for tok in $FORBIDDEN_TOKENS; do
    case "$lc" in *"$(printf '%s' "$tok" | tr 'A-Z' 'a-z')"*)
      echo "CMD contains '$tok': the runner never launches lives or bootstrapped children (Codex STOP)"; return;;
    esac
  done
  if [ -n "$TOTAL_GPUS" ] && [ "$TOTAL_GPUS" -gt 0 ] && [ "$NGPU" -gt "$TOTAL_GPUS" ]; then
    echo "NGPU=$NGPU exceeds the $TOTAL_GPUS GPUs on this node"; return
  fi
}

reject_job() {  # file reason
  { echo "REJECTED=$(now)"; echo "REJECT_REASON=$2"; } >> "$1"
  mv "$1" "$REJECTED/"
  EVENTS="$EVENTS | rejected $(strip_name "$1"): $2"
}

after_done() {  # $1 = AFTER name -> 0 if its done marker exists
  local f
  [ -e "$DONE/$1.job" ] && return 0
  for f in "$DONE"/*_"$1".job; do [ -e "$f" ] && return 0; done
  return 1
}
after_failed() { local f; [ -e "$FAILED/$1.job" ] && return 0; for f in "$FAILED"/*_"$1".job; do [ -e "$f" ] && return 0; done; return 1; }

# ---- GPUs ------------------------------------------------------------------------------------------------------
list_minus() {  # "a b c" "b" -> "a c" (order kept)
  local x y keep out=""
  for x in $1; do keep=1; for y in $2; do [ "$x" = "$y" ] && keep=0; done; [ $keep = 1 ] && out="$out $x"; done
  echo "${out# }"
}

discover_gpus() {  # sets ALL_GPUS TOTAL_GPUS FREE_GPUS (space lists) and TAKEN_DESC
  local all="" busy="" reserved="" own="" idx_uuid u i p cvd tok comm g f
  if [ -n "${QUEUE_FAKE_FREE_GPUS:-}" ]; then
    all=$(printf '%s' "$QUEUE_FAKE_FREE_GPUS" | tr ',' ' ')
  else
    idx_uuid=$(nvidia-smi --query-gpu=index,uuid --format=csv,noheader 2>/dev/null) || idx_uuid=""
    if [ -z "$idx_uuid" ]; then
      ALL_GPUS=""; TOTAL_GPUS=0; FREE_GPUS=""; TAKEN_DESC="nvidia-smi unavailable"; return
    fi
    all=$(printf '%s\n' "$idx_uuid" | awk -F', *' '{print $1}' | tr '\n' ' ')
    # (a) compute processes reported by nvidia-smi (uuid -> index)
    for u in $(nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader 2>/dev/null | tr -d ' ' | sort -u); do
      i=$(printf '%s\n' "$idx_uuid" | awk -F', *' -v u="$u" '$2==u {print $1}')
      [ -n "$i" ] && busy="$busy $i"
    done
    # (b) lives (and anything else in QUEUE_RESERVE_PATTERNS) own the GPU named in their environment
    for tok in $RESERVE_PATTERNS; do
      for p in $(pgrep -f "$tok" 2>/dev/null); do
        [ "$p" = "$$" ] && continue
        [ -r "/proc/$p/environ" ] || continue
        cvd=$(tr '\0' '\n' < "/proc/$p/environ" 2>/dev/null | sed -n 's/^CUDA_VISIBLE_DEVICES=//p' | head -1)
        if [ -n "$cvd" ]; then
          for g in $(printf '%s' "$cvd" | tr ',' ' '); do
            if [[ "$g" =~ ^[0-9]+$ ]]; then reserved="$reserved $g"
            else i=$(printf '%s\n' "$idx_uuid" | awk -F', *' -v u="$g" '$2==u {print $1}'); [ -n "$i" ] && reserved="$reserved $i"; fi
          done
        else
          comm=$(cat "/proc/$p/comm" 2>/dev/null)
          case "$comm" in python*) reserved="$reserved 0";; esac   # a life with no CUDA_VISIBLE_DEVICES sits on GPU 0
        fi
      done
    done
  fi
  # (c) GPUs held by jobs this runner launched that are still in running/
  for f in "$RUNNING"/*.job; do
    [ -e "$f" ] || continue
    own="$own $(field "$f" GPU | tr ',' ' ')"
  done
  ALL_GPUS="${all% }"
  TOTAL_GPUS=$(set -- $ALL_GPUS; echo $#)
  FREE_GPUS=$(list_minus "$ALL_GPUS" "$busy $reserved $own")
  TAKEN_DESC="smi=[$(echo $busy | tr ' ' ',')] lives=[$(echo $reserved | tr ' ' ',')] own=[$(echo $own | tr ' ' ',')]"
}

# ---- launch / finalize -----------------------------------------------------------------------------------------
job_alive() {  # pid name -> 0 if the wrapper for this job is still running
  local cmd
  pid_alive "$1" || return 1
  cmd=$(pid_cmd "$1")
  [ -z "$cmd" ] && return 0                     # ps unavailable: trust kill -0
  case "$cmd" in *"logs/$2.sh"*) return 0;; *) return 1;; esac   # pid reused by something else => job is gone
}

launch_job() {  # file name cmd gpus(space list)
  local f="$1" name="$2" cmd="$3" gpus="$4" cvd first script out rcf pidf i pid bg
  cvd=$(printf '%s' "$gpus" | tr ' ' ','); first="${gpus%% *}"
  cmd="${cmd//\{gpu\}/$cvd}"; cmd="${cmd//\{gpus\}/$cvd}"
  script="$LOGS/$name.sh"; out="$LOGS/$name.out"; rcf="$LOGS/$name.rc"; pidf="$LOGS/$name.pid"
  [ -e "$out" ] && mv "$out" "$out.prev.$(date +%s)"
  rm -f "$rcf" "$pidf"
  {
    echo '#!/bin/bash'
    echo "# queue_runner job $name launched $(now) on GPU(s) $cvd"
    printf 'cd %q || exit 97\n' "$REPO"
    echo "export CUDA_VISIBLE_DEVICES=$cvd GPU=$first GPUS=$cvd"
    printf '%s\n' "$cmd"
  } > "$script"
  # The wrapper records its own pid (robust even if setsid forks) and its exit code (survives a runner restart).
  $DETACH bash -c 'echo $$ > "$3"; bash "$1"; rc=$?; echo $rc > "$2"; exit $rc' queue_job "$script" "$rcf" "$pidf" \
    > "$out" 2>&1 < /dev/null &
  bg=$!
  pid=""; i=0
  while [ $i -lt 50 ]; do pid=$(cat "$pidf" 2>/dev/null); [ -n "$pid" ] && break; sleep 0.1; i=$((i+1)); done
  [ -n "$pid" ] || pid=$bg
  { echo "PID=$pid"; echo "GPU=$cvd"; echo "STARTED=$(now)"; echo "SCRIPT=$script"; echo "OUT=$out"; } >> "$f"
  mv "$f" "$RUNNING/"
  EVENTS="$EVENTS | launched $name gpu=$cvd pid=$pid"
}

finalize_running() {
  local f name pid rcf rc
  for f in "$RUNNING"/*.job; do
    [ -e "$f" ] || continue
    if read_job "$f"; then name="$NAME"; else name=$(strip_name "$f"); fi
    pid=$(field "$f" PID); rcf="$LOGS/$name.rc"
    if [ -f "$rcf" ]; then rc=$(tr -d ' \n' < "$rcf")
    elif job_alive "$pid" "$name"; then continue
    else rc=""; fi
    { echo "FINISHED=$(now)"; echo "RC=${rc:-unknown}"; } >> "$f"
    if [ "$rc" = "0" ]; then mv "$f" "$DONE/"; EVENTS="$EVENTS | done $name rc=0"
    else mv "$f" "$FAILED/"; EVENTS="$EVENTS | FAILED $name rc=${rc:-unknown}"; fi
  done
}

# ---- one scheduling pass ---------------------------------------------------------------------------------------
WARNED=""   # AFTER-blocked-by-failed names already logged
pass() {
  local f name free n take g node reason
  EVENTS=""
  finalize_running
  discover_gpus
  free="$FREE_GPUS"; node=$(node_id)
  for f in "$PENDING"/*.job; do
    [ -e "$f" ] || continue
    if ! read_job "$f"; then reject_job "$f" "job file does not source as bash"; continue; fi
    reason=$(validate_job)
    if [ -n "$reason" ]; then reject_job "$f" "$reason"; continue; fi
    if [ -n "$NODE_ONLY" ] && [ "$NODE_ONLY" != "$node" ]; then continue; fi         # not this node (or node unknown)
    if [ -n "$AFTER" ] && ! after_done "$AFTER"; then
      if after_failed "$AFTER"; then case " $WARNED " in *" $NAME "*) ;; *) WARNED="$WARNED $NAME"; EVENTS="$EVENTS | blocked $NAME: AFTER=$AFTER is in failed/";; esac; fi
      continue
    fi
    n=$(set -- $free; echo $#)
    [ "$n" -ge "$NGPU" ] || continue                                                  # waits for enough GPUs
    take=""; for g in $free; do take="$take $g"; [ $(set -- $take; echo $#) -ge "$NGPU" ] && break; done
    take="${take# }"; free=$(list_minus "$free" "$take")
    launch_job "$f" "$NAME" "$CMD" "$take"
  done
  n=$(set -- $free; echo $#)
  if [ -n "$EVENTS" ] || [ "$n" != "$PREV_FREE" ]; then
    log "free=$n[$(echo $free | tr ' ' ',')] $TAKEN_DESC pending=$(count_files "$PENDING") running=$(count_files "$RUNNING")${EVENTS}"
  fi
  PREV_FREE="$n"
}

# ---- main ------------------------------------------------------------------------------------------------------
main() {
  local f n=0
  mkdir -p "$PENDING" "$RUNNING" "$DONE" "$FAILED" "$REJECTED" "$LOGS"
  acquire_pidfile
  for f in "$RUNNING"/*.job; do [ -e "$f" ] && n=$((n+1)); done
  log "runner start pid=$$ node=${QUEUE_NODE:-$(node_id)} interval=${INTERVAL}s repo=$REPO detach='$DETACH' adopting=$n running job(s)${QUEUE_FAKE_FREE_GPUS:+ FAKE_GPUS=$QUEUE_FAKE_FREE_GPUS}"
  PREV_FREE=""
  while :; do
    pass
    [ -n "${QUEUE_LOOP_ONCE:-}" ] && break
    sleep "$INTERVAL"
  done
}
main "$@"
