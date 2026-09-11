#!/bin/bash
# tests/test_queue_runner.sh -- CPU-only test of gpu/queue_runner.sh scheduling logic. Runs on the Mac (bash 3.2, no
# setsid, no /proc): a fake `nvidia-smi` is put on PATH, GPUs come from QUEUE_FAKE_FREE_GPUS, and the runner is
# driven one pass at a time with QUEUE_LOOP_ONCE=1. Jobs are `echo`/`sleep`/`exit` one-liners. Nothing touches a node.
#   bash tests/test_queue_runner.sh
set -o pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER="$ROOT/gpu/queue_runner.sh"; ADD="$ROOT/gpu/queue_add.sh"; STATUS="$ROOT/gpu/queue_status.sh"
T=$(mktemp -d "${TMPDIR:-/tmp}/queue_test.XXXXXX"); T=$(cd "$T" && pwd)   # normalized (macOS TMPDIR ends in /)
PASS=0; FAIL=0; CLEANUP_PIDS=""
trap 'for p in $CLEANUP_PIDS; do kill "$p" 2>/dev/null; done; rm -rf "$T"' EXIT
ok()   { PASS=$((PASS+1)); echo "  ok   $*"; }
fail() { FAIL=$((FAIL+1)); echo "  FAIL $*"; }
check() { if eval "$1"; then ok "$2"; else fail "$2 -- [$1]"; fi; }

# fake nvidia-smi: 2 GPUs; FAKE_BUSY_UUIDS lists the uuids that have a compute process
mkdir -p "$T/bin" "$T/repo"
cat > "$T/bin/nvidia-smi" <<'EOF'
#!/bin/bash
case "$*" in
  *query-gpu=index,uuid*) printf '0, GPU-aaaa\n1, GPU-bbbb\n';;
  *query-compute-apps=gpu_uuid*) for u in ${FAKE_BUSY_UUIDS:-}; do echo "$u"; done;;
  *) exit 1;;
esac
EOF
chmod +x "$T/bin/nvidia-smi"
export PATH="$T/bin:$PATH"
export QUEUE_REPO="$T/repo" QUEUE_NODE=1 QUEUE_LOOP_ONCE=1 QUEUE_INTERVAL=1

fresh() {  # new queue dir per test
  Q="$T/q$1"; export QUEUE_DIR="$Q"; mkdir -p "$Q"/{pending,running,done,failed,rejected,logs}
}
pass_once() { QUEUE_FAKE_FREE_GPUS="${1:-0,1}" bash "$RUNNER"; }
wait_rc() {  # NAME -> wait up to 10 s for the job's rc file
  local i=0; while [ $i -lt 100 ]; do [ -f "$Q/logs/$1.rc" ] && return 0; sleep 0.1; i=$((i+1)); done; return 1
}
in_dir() { local f; for f in "$Q/$1"/*_"$2".job; do [ -e "$f" ] && return 0; done; return 1; }
job_field() { local f; for f in "$Q/$1"/*_"$2".job; do [ -e "$f" ] && sed -n "s/^$3=//p" "$f" | tail -1; done; }

echo "[1] launch on a free GPU with {gpu} substituted; GPU/GPUS/CUDA_VISIBLE_DEVICES exported; done with rc=0"
fresh 1
p=$(bash "$ADD" hello 'echo "gpu={gpu} cvd=$CUDA_VISIBLE_DEVICES G=$GPU GS=$GPUS pwd=$(pwd)"')
check '[ "$p" = "$Q/pending/0001_hello.job" ]' "queue_add wrote $p"
pass_once "0,1"
check 'in_dir running hello || in_dir done hello' "job left pending/ after one pass"
check '[ "$(job_field running hello GPU)$(job_field done hello GPU)" = "0" ]' "GPU=0 recorded"
wait_rc hello || fail "hello never wrote its rc file"
pass_once "0,1"
check 'in_dir done hello' "moved to done/"
check '[ "$(job_field done hello RC)" = "0" ]' "RC=0 recorded"
check 'grep -q "gpu=0 cvd=0 G=0 GS=0 pwd=$T/repo" "$Q/logs/hello.out"' "{gpu} -> 0, env exported, cwd = repo: $(cat "$Q/logs/hello.out")"
check 'grep -q "launched hello gpu=0" "$Q/runner.log" && grep -q "done hello rc=0" "$Q/runner.log"' "runner.log has launch and done lines"

echo "[2] NGPU=2 waits until two GPUs are free; then gets CUDA_VISIBLE_DEVICES=0,1"
fresh 2
bash "$ADD" long1 'sleep 3' >/dev/null
bash "$ADD" two 'echo "cvd=$CUDA_VISIBLE_DEVICES gpu={gpu} G=$GPU GS=$GPUS"' 2 >/dev/null
pass_once "0,1"                      # long1 takes GPU 0; only GPU 1 free -> two must wait
check 'in_dir running long1' "long1 launched on a free GPU"
check 'in_dir pending two' "two (NGPU=2) still pending with one free GPU"
pass_once "0,1"
check 'in_dir pending two' "two still pending on the next pass (long1 holds GPU 0)"
wait_rc long1 || fail "long1 never finished"
pass_once "0,1"                      # long1 -> done, two -> launched on 0,1
check 'in_dir done long1' "long1 done"
check 'in_dir running two || in_dir done two' "two launched once both GPUs were free"
check '[ "$(job_field running two GPU)$(job_field done two GPU)" = "0,1" ]' "GPU=0,1 recorded"
wait_rc two || fail "two never finished"
check 'grep -q "cvd=0,1 gpu=0,1 G=0 GS=0,1" "$Q/logs/two.out"' "CUDA_VISIBLE_DEVICES=0,1 GPU=0 GPUS=0,1: $(cat "$Q/logs/two.out")"
fresh 2b
bash "$ADD" two_alone 'echo hi' 2 >/dev/null
pass_once "0"                        # a one-GPU node: NGPU=2 can never run -> rejected, not silently pending
check 'in_dir rejected two_alone' "NGPU=2 on a 1-GPU node is rejected: $(job_field rejected two_alone REJECT_REASON)"

echo "[3] jobs that would launch lives / bootstrapped children are rejected (queue_add and runner)"
fresh 3
bash "$ADD" life 'python -m organism_v6.run_life_v2 --life-dir x' >/dev/null 2>&1; rc=$?
check '[ $rc -ne 0 ]' "queue_add refuses run_life_v2 (exit $rc)"
check '! ls "$Q"/pending/*life* >/dev/null 2>&1' "queue_add wrote nothing"
for spec in "life2|python -m organism_v6.run_life_v2 --life-dir x" "r6|bash gpu/launch.sh R6_B_seed900" "r7|bash x.sh R7_thing" "boot|bash gpu/launch_Bootstrapped_life.sh"; do
  n="${spec%%|*}"; c="${spec#*|}"
  printf 'NAME=%s\nCMD=%q\nNGPU=1\n' "$n" "$c" > "$Q/pending/0009_$n.job"     # hand-written, bypassing queue_add
done
printf 'NAME=fine\nCMD="echo fine"\nNGPU=1\n' > "$Q/pending/0010_fine.job"
pass_once "0,1"
for n in life2 r6 r7 boot; do check "in_dir rejected $n" "$n rejected: $(job_field rejected $n REJECT_REASON | cut -c1-60)"; done
check 'in_dir running fine || in_dir done fine' "the harmless job in the same pass still launched"
check '[ "$(grep -c rejected "$Q/runner.log")" -ge 1 ]' "rejections logged"
wait_rc fine

echo "[4] AFTER= ordering: b waits for a's done marker even with a free GPU"
fresh 4
bash "$ADD" a 'sleep 1; echo a' >/dev/null
AFTER=a bash "$ADD" b 'echo b' >/dev/null
check 'grep -q "^AFTER=a$" "$Q/pending/0002_b.job"' "AFTER=a written into the job file"
pass_once "0,1"
check 'in_dir running a' "a launched"
check 'in_dir pending b' "b still pending while a runs (GPU 1 was free)"
wait_rc a || fail "a never finished"
pass_once "0,1"
check 'in_dir done a' "a done"
check 'in_dir running b || in_dir done b' "b launched in the pass that finalized a"
wait_rc b
fresh 4b
printf 'NAME=bad\nCMD="exit 5"\nNGPU=1\n' > "$Q/pending/0001_bad.job"
printf 'NAME=dep\nCMD="echo dep"\nNGPU=1\nAFTER=bad\n' > "$Q/pending/0002_dep.job"
pass_once "0,1"; wait_rc bad; pass_once "0,1"
check 'in_dir failed bad && in_dir pending dep' "a dependent of a FAILED job keeps waiting"
check 'grep -q "blocked dep: AFTER=bad is in failed/" "$Q/runner.log"' "blocked-by-failed logged"

echo "[5] exit codes: rc=0 -> done/, rc!=0 -> failed/, RC recorded; NODE_ONLY honoured; runner restart re-adopts"
fresh 5
bash "$ADD" good 'exit 0' >/dev/null
bash "$ADD" bad3 'echo boom >&2; exit 3' >/dev/null
NODE_ONLY=2 bash "$ADD" other_node 'echo never' >/dev/null
pass_once "0,1"; wait_rc good; wait_rc bad3; pass_once "0,1"
check 'in_dir done good && [ "$(job_field done good RC)" = "0" ]' "good -> done RC=0"
check 'in_dir failed bad3 && [ "$(job_field failed bad3 RC)" = "3" ]' "bad3 -> failed RC=3"
check 'grep -q boom "$Q/logs/bad3.out"' "stderr captured in logs/bad3.out"
check 'in_dir pending other_node' "NODE_ONLY=2 job held on node 1"
QUEUE_NODE=2 pass_once "0,1"
check 'in_dir running other_node || in_dir done other_node' "NODE_ONLY=2 job launched when the runner is node 2"
wait_rc other_node
bash "$ADD" slow 'sleep 2; exit 0' >/dev/null
pass_once "0,1"
check 'in_dir running slow' "slow running"
pass_once "0,1"                      # a fresh runner process must re-adopt the live job, not fail it
check 'in_dir running slow' "restarted runner re-adopted the live job"
check 'grep -q "adopting=1" "$Q/runner.log"' "adoption logged"
printf 'NAME=ghost\nCMD="true"\nNGPU=1\nPID=999999\nGPU=1\n' > "$Q/running/0099_ghost.job"   # dead pid, no rc file
pass_once "0,1"
check 'in_dir failed ghost && [ "$(job_field failed ghost RC)" = "unknown" ]' "dead pid without rc -> failed RC=unknown"
wait_rc slow; pass_once "0,1"
check 'in_dir done slow' "slow -> done after finishing"

echo "[6] a second runner instance exits while the first is alive"
fresh 6
QUEUE_LOOP_ONCE= QUEUE_FAKE_FREE_GPUS="0,1" bash "$RUNNER" & FIRST=$!
CLEANUP_PIDS="$CLEANUP_PIDS $FIRST"
i=0; while [ $i -lt 50 ] && [ ! -s "$Q/runner.pid" ]; do sleep 0.1; i=$((i+1)); done
check '[ "$(cat "$Q/runner.pid")" = "$FIRST" ]' "first runner wrote runner.pid=$FIRST"
QUEUE_FAKE_FREE_GPUS="0,1" bash "$RUNNER" 2> "$T/second.err"; rc=$?
check '[ $rc -eq 1 ]' "second instance exited with 1"
check 'grep -q "another runner is alive" "$T/second.err"' "second instance said why: $(cat "$T/second.err")"
check '[ "$(cat "$Q/runner.pid")" = "$FIRST" ]' "first runner's pid file untouched"
check 'kill -0 $FIRST' "first runner still alive"
kill "$FIRST"; wait "$FIRST" 2>/dev/null
echo 99999999 > "$Q/runner.pid"      # stale pid file: a new runner must start
pass_once "0,1"; rc=$?
check '[ $rc -eq 0 ]' "runner starts over a stale pid file"

echo "[7] real discovery path through nvidia-smi (fake binary): GPU 1 busy -> only GPU 0 free"
fresh 7
bash "$ADD" j1 'echo one' >/dev/null; bash "$ADD" j2 'echo two' >/dev/null
FAKE_BUSY_UUIDS="GPU-bbbb" QUEUE_FAKE_FREE_GPUS= bash "$RUNNER"
check 'in_dir running j1 || in_dir done j1' "j1 launched"
check '[ "$(job_field running j1 GPU)$(job_field done j1 GPU)" = "0" ]' "j1 got GPU 0 (uuid->index mapping)"
check 'in_dir pending j2' "j2 waits (GPU 1 has a compute process)"
check 'grep -q "smi=\[1\]" "$Q/runner.log"' "runner.log shows smi=[1]"
wait_rc j1
FAKE_BUSY_UUIDS="" QUEUE_FAKE_FREE_GPUS= bash "$RUNNER"
check 'in_dir running j2 || in_dir done j2' "j2 launched once GPU 1 freed"
wait_rc j2
bash "$STATUS" > "$T/status.txt"; rc=$?
check '[ $rc -eq 0 ] && grep -q "^pending=0 running=" "$T/status.txt" && grep -q "runner.log (last 10)" "$T/status.txt"' "queue_status runs: $(sed -n 2p "$T/status.txt")"

echo
echo "passed=$PASS failed=$FAIL"
[ $FAIL -eq 0 ]
