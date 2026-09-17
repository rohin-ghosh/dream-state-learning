#!/usr/bin/env bash
# Talk to a live dream-state child as Rohin, from the laptop.
#
#   bash gpu/talk.sh <child> "<message>"            # deliver and wait for the child's reply (up to 12 min)
#   bash gpu/talk.sh <child> "<message>" --no-wait  # deliver only
#   bash gpu/talk.sh --list                          # show the child names
#   DRY_RUN=1 bash gpu/talk.sh <child> "<message>"   # print the remote command, deliver nothing
#
# The message is written into the child's stream/inbox by the R127 console on the child's node
# (speaker "Rohin", schema R127_ATTRIBUTED_INBOX_V1). The child reads it at its next step; the
# runtime renders it as "Rohin: ..." in the child's context and masks it from training targets.
# Nothing else is touched: no process is started or stopped. Works with macOS bash 3.2.
set -euo pipefail
cd "$(dirname "$0")/.."

L=/localhome/local-rohing
lookup() {  # prints "node root"
  case "$1" in
    C1|C2|C3|C4|C5)   echo "ovx3 $L/orch_r153_community_$1_20260916_attempt1/life" ;;
    run1)             echo "ovx3 $L/orch_r125_continual_20260916_attempt1/run1" ;;
    pilot)            echo "ovx3 $L/orch_r127_pilot_20260916_attempt1/run1" ;;
    repo_reader)      echo "ovx3 $L/orch_r136_repo_reader_20260916_attempt1/recovery_r154_saved30_20260916_attempt2/run1" ;;
    classroom_brain|classroom_creative|classroom_support|teach_parenting|teach_perception|teach_replay)
                      echo "a100 $L/orch_r136_a100_$1_20260916_attempt1/run1" ;;
    frozen_base)      echo "a100 $L/orch_r139_a100_frozen_base_no_adapter_20260916_attempt1/run1" ;;
    frozen_rank8)     echo "a100 $L/orch_r139_a100_frozen_rank8_no_sleep_20260916_attempt1/run1" ;;
    brain_free)       echo "ovx2 $L/orch_r133_brain_free_20260916_attempt1/run1" ;;
    creative_reread)  echo "ovx2 $L/orch_r133_creative_reread_20260916_attempt1/run1" ;;
    brain_guided)     echo "ovx2 $L/orch_r133_node3_brain_guided_20260916_attempt1/run1" ;;
    creative_free)    echo "ovx2 $L/orch_r133_node3_creative_free_20260916_attempt1/run1" ;;
    creative_select)  echo "ovx2 $L/orch_r133_node3_creative_select_20260916_attempt1/run1" ;;
    support_free)     echo "ovx2 $L/orch_r133_support_free_20260916_attempt1/run1" ;;
    kernel0)          echo "a40r $L/orch_r132_kernel_child_20260916_attempt1/run1" ;;
    kernel_parented)  echo "a40r $L/orch_r136_kernel_parented_a40r4_20260916_attempt1/run1" ;;
    raw_parented)     echo "a40r $L/orch_r136_raw_parented_seed1_a40r3_20260916_attempt1/run1" ;;
    raw_unparented)   echo "a40r $L/orch_r136_raw_unparented_a40r1_20260916_attempt1/run1" ;;
    *) return 1 ;;
  esac
}
srcdir() {  # node-side checkout that contains gpu/orch_r127_pilot_console.py
  case "$1" in
    ovx3) echo "$L/orch_r153_sandbox_source_20260916t2245z" ;;
    ovx2) echo "$L/orch_r145_integration_20260916t1611z_b" ;;
    a40r) echo "$L/orch_r141_kernel_tools_v1" ;;
    *)    echo "" ;;   # found dynamically on the node
  esac
}
CHILDREN="C1 C2 C3 C4 C5 run1 pilot repo_reader classroom_brain classroom_creative classroom_support teach_parenting teach_perception teach_replay frozen_base frozen_rank8 brain_free creative_reread brain_guided creative_free creative_select support_free kernel0 kernel_parented raw_parented raw_unparented"

if [ "${1:-}" = "--list" ] || [ $# -lt 2 ]; then
  echo "children (name -> node):"; for c in $CHILDREN; do set -- $(lookup $c); echo "  $c -> $1"; done; exit 0
fi
child="$1"; text="$2"; wait=1; [ "${3:-}" = "--no-wait" ] && wait=0
pair=$(lookup "$child") || { echo "unknown child '$child'; use --list" >&2; exit 2; }
node=${pair%% *}; root=${pair#* }; src=$(srcdir "$node")
[ -x "gpu/${node}_ssh.sh" ] || { echo "missing wrapper gpu/${node}_ssh.sh" >&2; exit 2; }
redact() { LC_ALL=C sed -E 's/[a-z0-9.-]+\.nvidia\.com/[host]/g; s/[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[ip]/g'; }

b64=$(printf '%s' "$text" | base64 | tr -d '\n')
remote="set -e; SRC='$src'; if [ -z \"\$SRC\" ] || [ ! -f \"\$SRC/gpu/orch_r127_pilot_console.py\" ]; then SRC=\$(dirname \$(dirname \$(find $L -maxdepth 3 -name orch_r127_pilot_console.py 2>/dev/null | head -1))); fi; cd \"\$SRC\"; T=\$(echo $b64 | base64 -d); python3 -B -m gpu.orch_r127_pilot_console parent --root '$root' --speaker Rohin --text \"\$T\" && echo DELIVERED_TO_INBOX \$(date -u +%H:%M:%SZ)"
if [ "${DRY_RUN:-0}" = "1" ]; then echo "node=$node root=$root"; echo "$remote"; exit 0; fi
echo ">> Rohin -> $child (node $node): $text"
bash "gpu/${node}_ssh.sh" "$remote" | redact
[ $wait = 1 ] || exit 0

py=$(cat <<'EOF'
import json,glob,sys,time
root=sys.argv[1]; needle=sys.argv[2]; deadline=time.time()+float(sys.argv[3])
def doc(r): return r.get("document", r) if isinstance(r,dict) else {}
def kind(r): return doc(r).get("kind") or r.get("kind") or "?"
def longest(d):
    best=""
    def w(x):
        nonlocal best
        if isinstance(x,str):
            if len(x)>len(best): best=x
        elif isinstance(x,dict):
            for v in x.values(): w(v)
        elif isinstance(x,list):
            for v in x: w(v)
    w(d); return best
def load():
    recs=[]
    for f in sorted(glob.glob(root+"/stream/records/*")):
        try:
            with open(f) as fh:
                for line in fh:
                    line=line.strip()
                    if line:
                        try: recs.append(json.loads(line))
                        except Exception: pass
        except Exception: pass
    return recs
while time.time()<deadline:
    recs=load()
    idx=[i for i,r in enumerate(recs) if kind(r) in ("INBOX","REQUEST") and needle in json.dumps(doc(r),ensure_ascii=False)]
    if idx:
        i=idx[0]
        for j in range(i+1,len(recs)):
            if kind(recs[j])=="RESPONSE":
                print("<< reply:\n"+longest(doc(recs[j]))); sys.exit(0)
        print("... delivered into the child's context; waiting for its reply", flush=True)
    else:
        print("... waiting for the child to read the inbox", flush=True)
    time.sleep(45)
print("!! no reply within the wait window (the child may be in a sleep/training phase); rerun later without a message to read new replies")
EOF
)
pyb64=$(printf '%s' "$py" | base64 | tr -d '\n')
needle=$(printf '%s' "$text" | cut -c1-60)
nb64=$(printf '%s' "$needle" | base64 | tr -d '\n')
bash "gpu/${node}_ssh.sh" "echo $pyb64 | base64 -d > /tmp/talk_wait_fable.py; python3 /tmp/talk_wait_fable.py '$root' \"\$(echo $nb64 | base64 -d)\" 720" | redact
