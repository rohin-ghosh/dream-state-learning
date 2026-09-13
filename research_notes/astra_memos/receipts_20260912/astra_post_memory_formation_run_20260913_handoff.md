# Post-memory WRITE/LR0 formation runner — EDITSTOP

September13,2026. CPU implementation/tests only. Main owns scientific decisions,
native preparation, allocations, launch and collection. Only the new runner,
matching tests and this handoff were edited. No repository/Git/network/native/GPU
operations, old-root writes, original collection, new training or core edits.

## Interface ready for Main

```text
prepare --root ROOT --spec-path SPEC --spec-sha256 SHA --allow-native
controller --root ROOT --plan-sha256 SHA --allow-gpu
collect --root ROOT --plan-sha256 SHA --completion-sha256 SHA --out OUT
worker --root ROOT --plan-sha256 SHA --state WRITE|LR0 --deadline-wall UNIX --allow-gpu
```

Worker is controller-internal; do not launch it separately. Functions with the
same argument names are also exposed. There is no new launcher or batch driver.
Prepare writes a fresh root and returns `POST_MEMORY_NATIVE_CPU_PREPARED_NOT_LAUNCHED`.
Controller returns `POST_MEMORY_FORMATION_COMPLETE_NOT_SCORED` plus completion SHA.
Collect returns `COLLECTED_POST_MEMORY_FORMATION_DIAGNOSTIC` plus scores SHA.

One seed per spec; native worker directory names are `WRITE` and `LR0`. Calls to
Parfit's core use `perception_seedN_WRITE` / `perception_seedN_LR0` explicitly.
All three seeds remain in the prospective comparison, including flat recall or
harm. Main's all-three engineering-valid prerequisite replaces the old design's
positive-recall/no-canary-loss gate. The single-seed runner validates its own
pair; it does not falsely attest cohort-wide native custody. Main has reported
all three COMPLETE/once-collected. No gain, retention or loss value is consulted
for eligibility. Source-root records and original scores remain unchanged.

## Closed specification (seed0 example)

Use actual numeric GPU index/lease and fresh UUID/boot identity instead of the
marked strings. The schema rejects bool seeds/index/lease, unknown keys, nonfinite
values, source drift, mismatched seeds, and unknown nodes. Only `node2` is accepted.
The provided source locations must exist unchanged on node2, with the same
interpreter and frozen dependency/source paths required by the original plan.

```json
{
  "runner_sha256": "c8ca3444c604aebbf5cd0b134f98a86cf79c3521332fff841e371a9986c41942",
  "core": {
    "path": "/tmp/astra_post_memory_formation_core_20260913.py",
    "sha256": "030c97c57a962a74a5b97bd66550096dedc2bab288d690b2c89808d2ec84474b"
  },
  "memory_runtime": {
    "path": "/tmp/astra_real_record_memory_run_20260913.py",
    "sha256": "7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e"
  },
  "memory": {
    "root": "/localhome/local-rohing/astra_diagnostics/real_record_memory_seed0_20260913_attempt1",
    "plan_sha256": "66fb0ae06fce25feb04c422add3062f8665be9bafaa72efdb348365fa82208c1",
    "completion_sha256": "08deffd0a0baa3bcad110884d250893f8470ae320afd13a3d71e20a651da4972",
    "collection": {
      "path": "/localhome/local-rohing/astra_diagnostics/real_record_memory_seed0_20260913_attempt1_collected/collection.json",
      "sha256": "fbbc8ddf580e2141c01a3b73477605e7e5a77bc8e638126475950ea1f105dfab"
    },
    "scores": {
      "path": "/localhome/local-rohing/astra_diagnostics/real_record_memory_seed0_20260913_attempt1_collected/scores.json",
      "sha256": "b56a0caa16259e29860efa284d283610ab9bfa9064c64f121fe7cc34266b72bf"
    }
  },
  "seed": 0,
  "node": "node2",
  "gpu_index": "REPLACE_WITH_INTEGER",
  "gpu_uuid": "GPU-REPLACE_WITH_FRESH_ALLOCATION",
  "expected_boot_id": "REPLACE_WITH_FRESH_NODE2_BOOT_UUID",
  "lease_end": "REPLACE_WITH_FINITE_UNIX_NUMBER"
}
```

For seeds1/2 replace seed and the native `seedN` root/collection path and pins:

| Seed | Plan SHA256 | Completion SHA256 |
|---|---|---|
| 1 | `9886ef9f19869f69649ee894e15c1fb47dfc85e301ee728adfbefc4df2c9c52b` | `56d19072b3f9474631c4b0d61ca23a21fde490ad80a9dd197f310ecd7023ff92` |
| 2 | `48f64f78aa6953baa72067602bf3043c0a8fb5531750f0433c6fdd8ef76dc5ea` | `e7ef9be2d572251e64c5973305fdcad0112d9569498c79c6646848049850987f` |

| Seed | Collection SHA256 | Scores SHA256 |
|---|---|---|
| 1 | `f0ac6662ccb6b6cb9477503fa7214578a1dade4e376e8b1e6c4395e2ae5c6268` | `5fe7638aa86e718b36ea00f9a97b9e36acbed4b464c968737acbc86447c71979` |
| 2 | `f0333bdd6854a27fc1a8825db852ec5976c3b50db667d9b762e2e489634d882a` | `a0182417e86e85ab6a874c7e98d77fd5952e2bb036fe1a2e35d6e7289ecb0cef` |

Collection/scores SHA256s above were independently computed on the local mirrors:
`/tmp/astra_memory_collected_20260913_attempt1/real_record_memory_seedN_20260913_attempt1_collected/`.
Their metadata joins Main's supplied plan/completion pins; native/VM parity and
actual completion are Main's report, not a new native audit. Original score
outcomes were not re-reduced or used to change the schedule/interface.

## Native custody, bounds and outputs

`bind_inputs` calls frozen `memory.verify(..., native=...)`,
`memory.validate_completed` and `memory.route_for`. It binds the original
complete inventory, both adapter routes/files, exact collection/scores files,
their completion/plan/seed identities and the existing once-only claim. It
rejects failed/empty/incomplete pairs and lingering original worker groups or
controller PID. It NEVER calls memory/formation collectors, fit routines or
trainer kernels. Reused native formation module is
`/tmp/astra_level1_real_record_run_20260913.py`, SHA256
`3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e`.

Parfit's frozen core owns all schedule, prompts, real-world execution, record
judging, strata and scientific replay/reduction. Its core-contract and additional
prior-ID disjointness receipt are pinned in the new plan. Only core
`input_messages` enter rendering: no adapter routes, training records, scores or
source-proof metadata are added to model input. No new source/target rewriting,
parent calls, action-projection recovery or retry is introduced.

Prepare uses the original public native tokenizer/render helper for the eight
initial prompts, retains the exact input spec bytes (pretty JSON is permitted),
and binds model files/environment/chat-template/source/candidate files. Each
worker fresh-loads original `formation.Native`, independently rerenders initial
prompts and every actual sequential prompt, enforces unchanged vLLM engine and
seed0 sampling, checks max context without truncation, and checks original
native response/token/decoded-text/adapter-route/timing agreement.

- Two cold states, each16scheduled wakes plus at most16records: **≤64calls/pair**,
  ≤192across three pairs. Wake96/record192 output tokens; zero fits/updates.
- CPU native prepare180s; controller1800s total; state900s maximum including
  cleanup; new collection180s. Inherited all-process XML GPU check30s and owned
  cleanup reserve40s; six-hour lease finish margin. A query/verification failure
  does not relax the envelope. Native worker has an explicit finite deadline.
- Controller starts with empty CUDA visibility; only a fresh session worker
  receives the spec's GPU UUID. Boot/lease are rechecked, and the unchanged
  public `gpu_state` checker runs before each worker and after owned cleanup.
  Group termination uses frozen identity-checked `memory.cleanup_owned`.
- Request/response files are written before validation, preserving bad bytes.
  Ordinary invalid/unfinished child output remains a scored refusal, while
  infrastructure exceptions escape the core and abort the state. Backend close
  and controller-owned process cleanup remain distinct checks.

New root outputs:

```text
prepare_started.json, specification.json, initial_prompts.json, plan.json
controller_started.json
run/{WRITE,LR0}/launch.json, started.json, identity.json
run/{WRITE,LR0}/{00..31}.request.json / .response.json (actual count only)
run/{WRITE,LR0}/formation.json, closed.json, released.json, stdout.log, stderr.log
capture_complete.json OR failure receipts
```

`closed.json` pins every native request/response and capture/identity file with
actual prompt/output-token and timing totals. Completion pins both complete
state inventories. Validation reproduces core requests/executions/records and
joins each to the exact raw native response, routes, ordered nonoverlapping
process receipts and bounds; two distinct cold worker PIDs are required.

New collection uses sibling `ROOT.collection_claim.json`, exclusive and never
retried. It requires terminal completion, absent controller and worker scope,
unchanged inputs/captures and initial/final all-process GPU vacancy. Both states
must validate before the paired reducer. It writes external `scores.json` and
`collection.json`; any failure retains `collection_failure.json` and no accepted
collection. It does not reopen any original collection claim. Unknown state
files/extra calls and changed captures are rejected. Scores remain diagnostic:
`automatic_pass=false`, `scientific_pass=null`, `outcome_gate=null`.

## Main-only minimal preparation

Keep frozen dependencies and old roots byte-identical. Stage only the new
runner and already accepted core; use the interpreter required by the original
memory plan. The existing formation environment was
`/localhome/local-rohing/v2/venv/bin/python`; runtime enforces actual interpreter
path/hash, not this narrative. Main supplies fresh disjoint ROOT/SPEC/OUT paths.

```sh
PY=/localhome/local-rohing/v2/venv/bin/python
RUN=/tmp/astra_post_memory_formation_run_20260913.py
: "${ROOT:?fresh native root}" "${SPEC:?native spec}" "${SPEC_SHA:?exact spec SHA256}"
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  "$PY" -B "$RUN" prepare --root "$ROOT" --spec-path "$SPEC" \
  --spec-sha256 "$SPEC_SHA" --allow-native
```

After Main's existing fresh reservation/checker and review of prepare receipt,
use returned PLAN_SHA. Do not treat CPU readiness as allocation or launch.

```sh
: "${PLAN_SHA:?returned plan SHA256}"
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  "$PY" -B "$RUN" controller --root "$ROOT" --plan-sha256 "$PLAN_SHA" --allow-gpu
```

Only after the controller exits successfully and owned scope is absent, use its
COMPLETE_SHA and collect the NEW root once:

```sh
: "${COMPLETE_SHA:?returned completion SHA256}" "${OUT:?fresh external collection}"
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  "$PY" -B "$RUN" collect --root "$ROOT" --plan-sha256 "$PLAN_SHA" \
  --completion-sha256 "$COMPLETE_SHA" --out "$OUT"
```

No command in this native-preparation section ran here.

## CPU validation and final file pins

29runner tests PASS6.553s. Combined29runner +12unchanged core tests PASS6.225s.
The earlier23-test suite passed4.252s; an initial shell invocation had a1s
harness timeout before completion and was rerun with a120s bound. No native
work occurred. CLI top-level/prepare/worker help and AST/whitespace checks pass.

```sh
PYTHONDONTWRITEBYTECODE=1 timeout 120s python3 -B -m unittest discover \
  -s /tmp -p test_astra_post_memory_formation_run_20260913.py -q
PYTHONDONTWRITEBYTECODE=1 timeout 120s python3 -B -m unittest discover \
  -s /tmp -p 'test_astra_post_memory_formation*.py' -q
```

Coverage includes mocked prepare→two cold captures→replay→once-only collection;
original custody functions invoked; adverse scores accepted without gate; exact
source/spec/seed pins; fresh-path/symlink/retry refusal; partial/length/fenced
output; dynamic context caps and duplicate callbacks; native route/token/finite
time errors; adapter/raw-file/extra-call/reused-PID tampering; no native spawn on
failed vacancy; finite wait/UUID env/owned timeout cleanup; live controller,
failed state and failed collection never scored; no original collector/trainer
or duplicated scientific-core implementation.

- `/tmp/astra_post_memory_formation_run_20260913.py`:
  `c8ca3444c604aebbf5cd0b134f98a86cf79c3521332fff841e371a9986c41942`.
- `/tmp/test_astra_post_memory_formation_run_20260913.py`:
  `0dd9ce4006e298bdad6931d39ac818dbe32b121056d0dabe1f9ba1de734e3389`.
- `/tmp/astra_post_memory_formation_run_20260913_handoff.md`: hash separately.

Limitations: tokenizer/backend/launch/cleanup are toy or mocked in CPU tests;
no actual native preparation, device readiness, live kernel/loaded tensor or
GPU release certification. Collection verifies receipt/file custody, not an
independent model-origin proof. Training-overlap, novel-triple fidelity and
copying-example analysis are later analyzer work from preserved traces, not
new gates or duplicated core metrics. Typed source agreement is not reasoning
truth. Harm must remain visible; neither record formation nor recall alone
establishes improved process, autonomous learning or H1/H2.

EDITSTOP. Main retains all native and scientific authority.
