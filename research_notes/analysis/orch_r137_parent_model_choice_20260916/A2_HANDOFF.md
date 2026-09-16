# R137 A2 request compatibility repair: final v3 handoff

September 16, 2026, 02:19:24 UTC. Final source and tests are bound in `A2_READY.json`. **Use v3 only.** v1 is preserved with failed copied-wrapper routing; v2 is preserved as superseded by v3's already-absent lock handling. No broker has been stopped or launched by this preparation.

## Exact scope

Only `render_parent_prompt()` and `build_system()` change in the frozen broker: optional NEXT_GUIDANCE UTF-8/type validation, applicable note insertion, note hash and head_waited metadata. Fixed template, original transport contract, provider, effort, output/call/budget limits, consumer, optimizer and checkpoint are unchanged. 177 other dependency files retain original hashes. Config changes only the broker source-pin hash.

Every check/serve/retire remote operation uses the existing authorized wrapper context `/tmp/orch_math_feedback_uptake_r121_astra_source_20260915_v1`, not the copied wrapper context without hosts.env. No credential file is copied or edited. New source, logs and packet bytes live under `/data/home/rohing/courier/runtime/r137_a2_request_repair_v3`; the future /tmp compatibility symlink points to that /data packet directory. Failed archival packets remain preserved, with no automatic replay.

Latest observed old broker: PID **3796147**, start_ticks **160688270**, command SHA256 `30b0bc1d83d0737853b8cd0a424753e5194aeb95540c084ad8b8990b6df8c1b6`. No socket/HTTP-slot FDs and no unfinished claims were observed; a polling subprocess existed, so this is **not an idle-retirement proof**. The `retire` command uses an exact pidfd, stops only this broker, rechecks identity plus no descendants/no HTTP socket or slot/no unfinished claim, and resumes it without terminating if the check fails. No child PID is signalled. After exact broker exit and settled-claim proof, an empty or already-absent runner lock is accepted; nonempty/invalid locks fail closed. No SIGKILL or child restart exists in this path.

## Future-only boundary

Prepared at Unix **1789525148.458752** (02:19:08 UTC): native=882, parent=100, optimizer_steps=14169; 100 historical requests; latest `R121_C000038_E1_experience`. Native root is `/localhome/local-rohing/orch_math_feedback_uptake_r124_readout_20260915_attempt1/A2`; original queue is `/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1/lane5/parent_queue`.

Serve takes a **fresh, stronger boundary after acquiring the exclusive original queue lock** and writes `runtime/START_BOUNDARY.json`. It excludes every then-existing request, all earlier native reservations (even if their queue file appears later), all claims/responses/partials/native dispositions, and reservations at or before that timestamp. No historical MISSING/refused request is resent. The prepared high-water is not permission to process backlog accumulated before launch.

## Tests and current staging

`python3 -B -m unittest discover -s tests -p test_orch_r137_math_request_repair.py -q`

**26 tests PASS, zero skipped.** This includes exact frozen-source AST-only delta, bound/stale/invalid notes, original reflection checks, future reservation/high-water/disposition exclusion, data confinement, unchanged wrapper context, pid reuse rejection, in-flight resume without termination, and already-absent lock acceptance. Actual staged `check` PASS with current head settings bound; zero provider calls. Retire/serve have NOT been executed.

Stage already exists; do not rerun prepare or overwrite it:

```bash
STAGE=/data/home/rohing/courier/runtime/r137_a2_request_repair_v3
MANIFEST=bb3ab4b49faf867c6c936922a6b5e0bcdd009bd5a697d70309db1ddd619cf713
SCRIPT="$STAGE/orch_r137_math_request_repair.py"
CUDA_VISIBLE_DEVICES='' python3 -B "$SCRIPT" check --stage "$STAGE" --manifest-sha256 "$MANIFEST"
```

## Main-only publication and handoff

After Main publishes the exact source/tests/receipts, set `PUBLISHED_COMMIT` to that actual commit and create a NEW launch receipt from the staged disabled template. The legacy authorization string is the unchanged transport protocol token, not a head-watcher action. The template remains disabled until Main explicitly creates this receipt.

```bash
set -e
: "${PUBLISHED_COMMIT:?set actual Main publication commit first}"
python3 -B - "$STAGE" "$MANIFEST" "$PUBLISHED_COMMIT" <<'PY'
import json, sys
from pathlib import Path
stage = Path(sys.argv[1])
document = json.loads((stage/'GO_TEMPLATE.json').read_text())
document['authorized'] = True
document['source_reference'] = 'Main publication '+sys.argv[3]+'; R137 A2 manifest '+sys.argv[2]
with (stage/'MAIN_GO.json').open('x') as output:
    json.dump(document, output, sort_keys=True, indent=2)
    output.write('\n')
PY
test -n "${NVIDIA_API_KEY:-}"
CUDA_VISIBLE_DEVICES='' python3 -B "$SCRIPT" retire --stage "$STAGE" --manifest-sha256 "$MANIFEST" --launch-receipt "$STAGE/MAIN_GO.json"
mkdir -p "$STAGE/runtime"
CUDA_VISIBLE_DEVICES='' nohup python3 -B "$SCRIPT" serve --stage "$STAGE" --manifest-sha256 "$MANIFEST" --launch-receipt "$STAGE/MAIN_GO.json" >"$STAGE/runtime/BROKER.log" 2>&1 < /dev/null &
```

If retirement reports in-flight activity, it resumes the exact old broker and exits nonzero. **Do not proceed to serve.** Main may retry the idle retirement check later without rewriting MAIN_GO, changing source or replaying requests. If it reports any other identity, lock, or provenance failure, stop and inspect rather than bypass it. Do not create another broker while the old one remains alive.

Successful process spawn alone is not delivery. Check `RETIREMENT.json`, `runtime/START_BOUNDARY.json`, `runtime/STARTED.json` and subsequent native consumer receipts. F1/F2/F4 consumer blocks and watcher-owned files remain untouched.
