#!/bin/bash
# head_parent.sh — the Fable head parent (PARENTING_BATTLE_PLAN_v4 §6). Cron on the VM: 10,40 * * * * (reader owns :05/:35).
# Each run: skip if another headless Claude (reader / self-check / previous head parent) is running; wait for
# ~/courier/swarm/branches.json (branch → {node, root} posted after Astra launches the lanes); act only when at least
# one Fable branch has a NEW sleep/cycle marker since the last run; pre-fetch a ≤ 40 KB digest per node-5 branch
# read-only through the gpu/<node>_ssh.sh wrapper; run ONE `claude -p --effort max` call with head_parent.md +
# PARENTING_PRINCIPLES as the system prompt and the digests as the user message; validate the returned fields;
# rewrite ~/courier/swarm/prompts/F<n>.md + .fields.json (the broker re-reads them every call); append the exchange
# entry to research_loop/PARENTING_EXCHANGE.md and COORDINATION.md; commit -o those two files; push if fast-forward.
# Never touches Astra's clone, never types into Codex, never stops a branch. Logs: ~/courier/swarm/head_parent.log.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../courier_lib.sh"
SW="$COURIER_HOME/swarm"; mkdir -p "$SW/cycles" "$SW/prompts"
COURIER_LOG="$SW/head_parent.log"; PIDFILE="$SW/head_parent.pid"
CAP_S="${HEAD_PARENT_CAP_S:-1200}"; BUDGET_USD="${HEAD_PARENT_BUDGET_USD:-10}"
PRINC="$SW/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md"; export MAKE_PROMPTS_PLAN="$SW/PARENTING_BATTLE_PLAN_v4_2026-09-15.md"
[ -r "$PRINC" ] && [ -r "$MAKE_PROMPTS_PLAN" ] || { echo "$(date -u +%FT%TZ) missing plan/principles copies in $SW" >> "$SW/head_parent.log"; exit 0; }
BRANCHES="$SW/branches.json"; STATE="$SW/head_state.json"

if pid_alive "$PIDFILE"; then log "head parent already running"; exit 0; fi
for other in "$COURIER_HOME/selfcheck/selfcheck.pid" "$COURIER_HOME/result_reads/result_read.pid"; do
  if pid_alive "$other"; then log "another headless Claude is running ($other); skipping"; exit 0; fi
done
echo $$ > "$PIDFILE"; trap 'rm -f "$PIDFILE"' EXIT
if ! claude_ready; then log "claude not ready ($(claude_not_ready_reason))"; exit 0; fi
[ -r "$BRANCHES" ] || { log "waiting for $BRANCHES (branch roots not posted yet)"; exit 0; }
MEM_AVAIL_MB=$(free -m | awk '/Mem:/{print $7}'); [ "${MEM_AVAIL_MB:-0}" -ge 1500 ] || { log "RAM available ${MEM_AVAIL_MB} MB < 1500; skipping"; exit 0; }

TS="$(date -u +%Y%m%dT%H%M%SZ)"; CYC="$SW/cycles/$TS"; mkdir -p "$CYC"
# 1. digests (read-only, size-capped) and new-sleep detection
python3 - "$BRANCHES" "$STATE" "$CYC" "$COURIER_REPO" <<'PY'
import json, subprocess, sys, os, hashlib
branches, state_p, cyc, repo = sys.argv[1:5]
B = json.load(open(branches)); state = json.load(open(state_p)) if os.path.exists(state_p) else {}
new_any = False; digests = {}
for name, b in B.items():
    node, root = b['node'], b['root']
    cmd = f"""R={root}; latest=$(ls -td $R/cycle_* $R/*/cycle_* $R/cycle* $R/*/cycle* 2>/dev/null | head -1); nread=$(ls -d $R/readout_* $R/*/readout_* 2>/dev/null | wc -l); echo "LATEST ${{latest:-none}} readouts=$nread results=$(ls $R/parent_transcripts/*/RESULT.json $R/*/parent_transcripts/*/RESULT.json 2>/dev/null | wc -l)";
    for f in $(ls -t $R/STATUS.json $R/*/STATUS.json $R/PENDING_TRIPLE.json $R/*/PENDING_TRIPLE.json $R/readout_*/COMPLETE.json $R/*/readout_*/COMPLETE.json $R/readout_*/*MEASURE*.json $R/cycle_*/UPDATES.jsonl $R/parent_transcripts/*/RESULT.json $R/parent_transcripts/*/REQUEST.json $R/*/parent_transcripts/*/RESULT.json 2>/dev/null | head -10); do echo "=== $f"; head -c 1200 $f; echo; done"""
    try:
        out = subprocess.run(['bash', f'{repo}/gpu/{node}_ssh.sh', cmd], capture_output=True, text=True, timeout=120).stdout
    except Exception as e:
        out = f'DIGEST_ERROR {e}'
    out = out[:12000]
    marker = out.split('\n', 1)[0]
    digests[name] = out
    if name.startswith('F') and marker != state.get(name):
        new_any = True
    state[name] = marker
json.dump(digests, open(f'{cyc}/digests.json', 'w'))
json.dump(state, open(f'{cyc}/state_candidate.json', 'w'))
open(f'{cyc}/NEW_SLEEP', 'w').write('1' if new_any else '0')
PY
if [ "$(cat "$CYC/NEW_SLEEP")" != "1" ]; then log "no new Fable sleep/cycle since last run; no head-parent call"; exit 0; fi

# 2. build the user message (current fields + digests + Astra's last two exchange entries)
python3 - "$SW/prompts" "$CYC" "$COURIER_REPO/research_loop/PARENTING_EXCHANGE.md" <<'PY'
import json, sys, glob, os, re
prompts, cyc, exch = sys.argv[1:4]
fields = {}
for f in sorted(glob.glob(prompts + '/[FA][1-4].fields.json')):
    name = os.path.basename(f).split('.')[0]; fields[name] = json.load(open(f))['fields']
astra = []
if os.path.exists(exch):
    parts = re.split(r'\n(?=## \[)', open(exch).read())
    astra = [p for p in parts if p.startswith('## [Astra') or p.startswith('## [Main') or p.startswith('## [Builder')][-2:]
msg = {'current_fields': fields, 'digests': json.load(open(cyc + '/digests.json')), 'astra_last_two_exchange_entries': astra}
open(cyc + '/user.json', 'w').write(json.dumps(msg)[:900000])
PY
cat "$HERE/head_parent.md" > "$CYC/system.md"; echo >> "$CYC/system.md"; cat "$PRINC" >> "$CYC/system.md"
log "head parent call (cap ${CAP_S}s, budget ${BUDGET_USD} USD) -> $CYC"
# prompt via stdin and system prompt via file: the earlier argv form failed with "Argument list too long" (rc=126)
( cd "$COURIER_REPO" && run_with_timeout "$CAP_S" "$CLAUDE_BIN" -p --model claude-fable-5-1 --effort max --output-format json \
    --tools "" --no-session-persistence --max-turns 1 --max-budget-usd "$BUDGET_USD" \
    --system-prompt-file "$CYC/system.md" < "$CYC/user.json" ) > "$CYC/reply.json" 2> "$CYC/reply.err"
rc=$?; [ $rc -eq 0 ] || { log "head parent call failed rc=$rc ($(head -c 200 "$CYC/reply.err" | tr '\n' ' '))"; exit 3; }

# 3. validate + apply fields (STYLE/FOCUS/REFLECTION only), write exchange entries
python3 - "$SW/prompts" "$CYC" "$COURIER_REPO" "$TS" <<'PY'
import json, sys, os, hashlib, re, glob
prompts, cyc, repo, ts = sys.argv[1:5]
sys.path.insert(0, repo + '/tools/courier/swarm')
from make_prompts import apply_head_update, fixed_parent_template, render, verify_binding
raw = json.load(open(cyc + '/reply.json'))
text = raw.get('result') if isinstance(raw, dict) else raw
m = re.search(r'\{.*\}', text, flags=re.S); out = json.loads(m.group(0))
template = fixed_parent_template()
changed = []
for name, upd in out.get('branches', {}).items():
    if name in out.get('unchanged', []): continue
    if not re.fullmatch(r'[FA][1-4]', name): continue
    fp = f'{prompts}/{name}.fields.json'
    if not os.path.exists(fp): continue
    cur = json.load(open(fp))['fields']
    new = apply_head_update(cur, upd, template)
    bad = any(tok in new['FOCUS'] for tok in ('%', 'D&R', 'ratio', 'score', 'accuracy')) or re.search(r'\d', new['FOCUS'])
    if bad: new['FOCUS'] = cur['FOCUS']  # FOCUS never carries a measure or a number
    prompt = render(new, template); assert verify_binding(prompt, template), name
    open(f'{prompts}/{name}.md', 'wb').write(prompt.encode())
    json.dump({'schema': 'ORCH_R114_HEAD_FIELDS_V1', 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(), 'fields': new},
              open(fp, 'w'), indent=1, sort_keys=True)
    changed.append(f"{name}: STYLE='{new['STYLE']}' REFLECTION={new['REFLECTION']['mode']}/{new['REFLECTION']['max_new_tokens']} FOCUS='{new['FOCUS']}'")
entry = out.get('exchange_entry', '').strip()
hdr = f"\n\n## [Fable-VM swarm — head parent] {ts[:4]}-{ts[4:6]}-{ts[6:8]}T{ts[9:11]}:{ts[11:13]}Z\n"
body = entry + ("\n\nField changes: " + "; ".join(changed) if changed else "\n\nField changes: none") + f"\n\nDigest cycle: ~/courier/swarm/cycles/{ts} (VM-local; no raw transcripts in git)."
open(repo + '/research_loop/PARENTING_EXCHANGE.md', 'a').write(hdr + body + '\n')
open(repo + '/research_loop/COORDINATION.md', 'a').write(hdr.replace('head parent', 'head parent, mirrored from PARENTING_EXCHANGE') + body[:1500] + '\n')
print('applied', len(changed), 'field changes')
PY
rc=$?; [ $rc -eq 0 ] || { log "head fields rejected; prior cycle marker retained"; exit 3; }
cp "$CYC/state_candidate.json" "$STATE"
# 3b. sync the rewritten prompt files to node 5, where the Fable brokers run (message 117: Fable hosted on node 5)
source "$COURIER_REPO/gpu/hosts.env" 2>/dev/null; if [ -n "${OVX3_NODE:-}" ]; then
  rsync -a "$SW/prompts/" "$OVX3_NODE":~/courier_swarm/prompts/ 2>/dev/null && log "prompts synced to node 5" || log "prompt sync to node 5 FAILED"
fi
# 4. publish the exchange entry (this checkout only; never Astra's clone)
[ "${HEAD_PARENT_PUBLISH:-1}" = "1" ] || { log "field changes complete; publication delegated to orchestrator"; exit 0; }
cd "$COURIER_REPO" || exit 0
if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ] || [ -f .git/MERGE_HEAD ]; then log "git busy; entry left uncommitted"; exit 0; fi
git commit -q -o research_loop/PARENTING_EXCHANGE.md research_loop/COORDINATION.md -m "Fable-VM head parent $TS: exchange entry + field changes" && \
  { git push -q origin HEAD:refs/heads/vm-watcher 2>/dev/null && log "pushed to origin/vm-watcher (laptop watcher mirrors into main)" || log "commit local (push to vm-watcher failed)"; }
log "head parent cycle done -> $CYC"
