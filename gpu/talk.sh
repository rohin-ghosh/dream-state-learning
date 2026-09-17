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
# Nothing else is touched: no process is started or stopped.
set -euo pipefail
cd "$(dirname "$0")/.."

declare -A NODE ROOT SRC
SRC[ovx3]=/localhome/local-rohing/orch_r153_sandbox_source_20260916t2245z
SRC[a100]=/localhome/local-rohing/orch_r153_sandbox_source_20260916t2245z   # overridden below if a local copy exists
SRC[ovx2]=/localhome/local-rohing/orch_r145_integration_20260916t1611z_b
SRC[a40r]=/localhome/local-rohing/orch_r141_kernel_tools_v1

# node 5
for c in C1 C2 C3 C4 C5; do NODE[$c]=ovx3; ROOT[$c]=/localhome/local-rohing/orch_r153_community_${c}_20260916_attempt1/life; done
NODE[run1]=ovx3;        ROOT[run1]=/localhome/local-rohing/orch_r125_continual_20260916_attempt1/run1
NODE[pilot]=ovx3;       ROOT[pilot]=/localhome/local-rohing/orch_r127_pilot_20260916_attempt1/run1
NODE[repo_reader]=ovx3; ROOT[repo_reader]=/localhome/local-rohing/orch_r136_repo_reader_20260916_attempt1/recovery_r154_saved30_20260916_attempt2/run1
# node 1
for c in classroom_brain classroom_creative classroom_support teach_parenting teach_perception teach_replay; do
  NODE[$c]=a100; ROOT[$c]=/localhome/local-rohing/orch_r136_a100_${c}_20260916_attempt1/run1; done
NODE[frozen_base]=a100;  ROOT[frozen_base]=/localhome/local-rohing/orch_r139_a100_frozen_base_no_adapter_20260916_attempt1/run1
NODE[frozen_rank8]=a100; ROOT[frozen_rank8]=/localhome/local-rohing/orch_r139_a100_frozen_rank8_no_sleep_20260916_attempt1/run1
# node 3
NODE[brain_free]=ovx2;      ROOT[brain_free]=/localhome/local-rohing/orch_r133_brain_free_20260916_attempt1/run1
NODE[creative_reread]=ovx2; ROOT[creative_reread]=/localhome/local-rohing/orch_r133_creative_reread_20260916_attempt1/run1
NODE[brain_guided]=ovx2;    ROOT[brain_guided]=/localhome/local-rohing/orch_r133_node3_brain_guided_20260916_attempt1/run1
NODE[creative_free]=ovx2;   ROOT[creative_free]=/localhome/local-rohing/orch_r133_node3_creative_free_20260916_attempt1/run1
NODE[creative_select]=ovx2; ROOT[creative_select]=/localhome/local-rohing/orch_r133_node3_creative_select_20260916_attempt1/run1
NODE[support_free]=ovx2;    ROOT[support_free]=/localhome/local-rohing/orch_r133_support_free_20260916_attempt1/run1
# node 4
NODE[kernel0]=a40r;          ROOT[kernel0]=/localhome/local-rohing/orch_r132_kernel_child_20260916_attempt1/run1
NODE[kernel_parented]=a40r;  ROOT[kernel_parented]=/localhome/local-rohing/orch_r136_kernel_parented_a40r4_20260916_attempt1/run1
NODE[raw_parented]=a40r;     ROOT[raw_parented]=/localhome/local-rohing/orch_r136_raw_parented_seed1_a40r3_20260916_attempt1/run1
NODE[raw_unparented]=a40r;   ROOT[raw_unparented]=/localhome/local-rohing/orch_r136_raw_unparented_a40r1_20260916_attempt1/run1

if [[ "${1:-}" == "--list" || $# -lt 2 ]]; then
  echo "children:"; for c in "${!NODE[@]}"; do echo "  $c (node ${NODE[$c]})"; done | sort; exit 0
fi
child="$1"; text="$2"; wait=1; [[ "${3:-}" == "--no-wait" ]] && wait=0
[[ -n "${NODE[$child]:-}" ]] || { echo "unknown child '$child'; use --list" >&2; exit 2; }
node=${NODE[$child]}; root=${ROOT[$child]}; src=${SRC[$node]}
[[ -x gpu/${node}_ssh.sh ]] || { echo "missing wrapper gpu/${node}_ssh.sh" >&2; exit 2; }

# base64 the text so quoting is exact end to end
b64=$(printf '%s' "$text" | base64 | tr -d '\n')
remote="set -e; SRC=$src; [ -f \$SRC/gpu/orch_r127_pilot_console.py ] || SRC=\$(dirname \$(dirname \$(find /localhome/local-rohing -maxdepth 3 -name orch_r127_pilot_console.py 2>/dev/null | head -1))); cd \$SRC; T=\$(echo $b64 | base64 -d); before=\$(ls $root/stream/records | wc -l); python3 -B -m gpu.orch_r127_pilot_console parent --root $root --speaker Rohin --text \"\$T\" && echo DELIVERED_TO_INBOX \$(date -u +%H:%M:%SZ)"
if [[ "${DRY_RUN:-0}" == "1" ]]; then echo "node=$node"; echo "$remote"; exit 0; fi
echo ">> Rohin -> $child (node $node): $text"
bash gpu/${node}_ssh.sh "$remote" | LC_ALL=C sed -E 's/[a-z0-9.-]+\.nvidia\.com/[host]/g; s/[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[ip]/g'
[[ $wait == 1 ]] || exit 0

# wait for the inbox to be read and the child's next reply; print it
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
                print("<< %s replied:\n%s" % (root.rsplit("/",2)[-2], longest(doc(recs[j])))); sys.exit(0)
        print("... delivered (rendered into context), waiting for the reply", flush=True)
    else:
        print("... waiting for the child to read the inbox", flush=True)
    time.sleep(45)
print("!! no reply within the wait window; the child may be asleep (training) — check again with: bash gpu/talk.sh %s --last" % root)
EOF
)
pyb64=$(printf '%s' "$py" | base64 | tr -d '\n')
needle=$(printf '%s' "$text" | cut -c1-60)
nb64=$(printf '%s' "$needle" | base64 | tr -d '\n')
bash gpu/${node}_ssh.sh "echo $pyb64 | base64 -d > /tmp/talk_wait_fable.py; python3 /tmp/talk_wait_fable.py $root \"\$(echo $nb64 | base64 -d)\" 720" | LC_ALL=C sed -E 's/[a-z0-9.-]+\.nvidia\.com/[host]/g; s/[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[ip]/g'
