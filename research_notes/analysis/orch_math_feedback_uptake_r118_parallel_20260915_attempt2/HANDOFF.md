# F2/A2 fresh-exec recovery: actual release, not a model launch

## Observed disposition

Both serial math residents failed before generation1 reload: exact JSON recipe
comparison rejected **only the ordering** of the same seven `target_modules`.
Their authentic failure/terminal records, six accepted TRAIN captures, closed
parent archives, carry and all reservations remain unchanged. The accepted
generation0 submissions were already trained. They must never be resubmitted.

| Branch | Released native | Consumed TRAIN cycle | Next NEW cycle | Native/parent charged | Old DEV/OPEN |
|---|---:|---:|---:|---:|---|
| F2 | 1073927 | 10 | 11 | 274 / 60 | NOT_ATTEMPTED / NOT_ATTEMPTED |
| A2 | 1073926 | 6 | 7 | 170 / 36 | NOT_ATTEMPTED / NOT_ATTEMPTED |

Canonical generation1 checkpoint:
`43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d`.
Actual mounted generation1 is **not yet claimed**. No fake DEV COMPLETE, old
PROGRESS replacement, collection replay, training replay or fresh baseline.

Actual `RELEASED.json`, normalized postcommit dispositions and recovery cursors
were written after proving both original natives/guards absent. No signals were
sent. Herschel's actual native `postcommit_evaluation_boundary` accepts both
envelopes. Original FINAL timers remain alive/unchanged pending coordinated
source custody; their planned retirement is not reported as already completed.

## Frozen executable implementation

Node source: `/localhome/local-rohing/orch_math_feedback_uptake_r118_parallel_source_20260915_v3`.
Services: `/localhome/local-rohing/orch_math_feedback_uptake_r118_parallel_20260915_attempt2/lane1`
and the same prefix with `/lane5`. Each has actual `RELEASED.json`,
`EXECUTABLE_READY.json`, `SOURCE_UPGRADE.json`, `OWNER_HANDOFF.json`, and
`FRESH_OWNER_PREPARED.json`. The prepared owner command is executable, but its
`runtime_staged=false` is intentional: Main's agreed all-eight activation is
not fabricated. `READY.json` contains the exact references and hashes.

The new executable guard performs strict privileged full-proc/UUID/CVD/FD
admission, starts identity-bound FINAL/cutoff timers and a real new native PID,
loads canonical weights, then calls `bootstrap_fresh_actor` and
`wait_fresh_collection_go` before new TRAIN. Math has no local optimizer;
F1 must restore its exact optimizer/RNG. Math's new gradient RNG is explicitly
session/rank-seeded, not represented as preserved old-peer RNG. Each subsequent
two-episode collection publishes its actual SAFE certificate through
`await_campaign_activation`, consolidates through the common hook, observes the
in-place broadcast and runs the original frozen fresh-process DEV evaluator.

191 tests pass locally and in the frozen node CPU runtime; neither initialized
CUDA. Tests include real CPU pidfd release with a foreign sentinel untouched,
PID/exec drift, source/version pins, no fake DEV, actual postcommit/charge/source
validation, rejection of true recipe changes, and bounded automatic SAFE
publication. Actual GPU execution/performance is not claimed.

v2 remains immutable. v3 adds automatic campaign publication, pre-staging owner
export, and an explicit unlaunched source overlay; all old PLAN/release files
remain unchanged. `SOURCE_BINDINGS.json` lists exact differences, including the
separately owned Herschel hook snapshot. No live source was hotpatched.

## Exact next commands (Main's coordinated boundary)

Run on node5 from the frozen **v3** source directory, before Main starts its
common locked dispatcher. For each `LANE` of `lane1` and `lane5`:

```sh
export CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1
SERVICE=/localhome/local-rohing/orch_math_feedback_uptake_r118_parallel_20260915_attempt2/$LANE
python3 -B -m gpu.orch_math_feedback_uptake_r118_parallel_lifecycle stage --service "$SERVICE" --authorization "$MAIN_LAUNCH_AUTH" --activation-directory "$MAIN_ACTIVATION_DIRECTORY" --campaign "$MAIN_CAMPAIGN_JSON"
python3 -B -m gpu.orch_math_feedback_uptake_r118_parallel_lifecycle owner-envelope --service "$SERVICE"
```

`MAIN_LAUNCH_AUTH` uses `R118_MATH_PARALLEL_FRESH_EXEC_AUTH_V1`: authorized,
common_handoff_coordinated, lifecycle_rebinding_authorized and all_eight_released
must be true; actions includes LAUNCH; root and original PLAN hash must match;
checkpoint is the generation1 hash above; activation_directory matches the
campaign; not_before/expiry stay before 16:55 UTC. RNG policy is
`DETERMINISTIC_NEW_STREAM_NOT_OLD_PEER_RNG`. The existing RELEASE-only
authorization is not a launch authorization. `stage` retires only exact owned
CPU FINAL timers, with pidfds and no old FINAL claims, before new custody.

Main's dispatcher uses each final `FRESH_OWNER.json` command:
`python -B -m gpu.orch_math_feedback_uptake_r118_parallel_native guard --service SERVICE`
with the exact Python path/cwd/environment already encoded in that file.
Do not independently run the native or replay the RELEASE command. Main remains
sole common CONFIG/session/campaign/dispatch writer. No additional review gate.

## Parent delivery and FINAL custody

Hubble owns F2. Its new terminal is `SERVICE/GUARD_TERMINAL.json`; publish
`SERVICE/BROKER_READY.json` only after the actual exclusive original queue lock:
`{runtime:{path,sha256}, terminal_path, actual_single_lane_lock_acquired:true}`.

A2 has a separate validated immutable VM broker runtime:
`/tmp/orch_math_feedback_uptake_r118_parallel_broker_source_20260915_attempt2`.
Its active config is `parent_claude/CONFIG.json` hash
`1a4caaa9cdef57cde755e3923f8965491e71f47387c3529c728ec15c1a4ca827`,
not the older historical root BROKER_CONFIG. It preserves the exact old policy
and transport source pins, config/GO, four HTTP slots, 1GiB memory floor, one
attempt, current claims and node-only archives. Ten broker CPU regressions pass;
actual provider delivery has not begun. The failed first CPU packaging attempt
is preserved separately; it omitted a historical test dependency and made no calls.

After native staging, create its metadata-only binding with original A2 root,
new service, active config hash, and actual RUNTIME/RELEASED references. Launch
from the immutable broker runtime:

```sh
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -m gpu.orch_math_feedback_uptake_r118_parallel_broker --config ASTRA_CONFIG.json --launch-receipt ASTRA_GO.json --prompt-root /data/home/rohing/courier/swarm/prompts --principles research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md --binding "$A2_PARALLEL_BINDING"
```

No guard/parent is launched by this handoff. Original 43-cycle/call ceilings and
16:59 native/17:02 hard bounds persist; common TRAIN retirement is 16:55 UTC.
The new FINAL custody reuses the SAME unused 8-call allocation, original sealed
IDs/decoder, sole Main selector and 17:00–17:20 window, with no parents/rows/OPEN.
Missing genuine release or canonical selection yields NOT_RUN, never duplication.

Stage only `STAGE_PATHS.txt`; Main owns Git. Raw evidence/checkpoints stay on nodes.
