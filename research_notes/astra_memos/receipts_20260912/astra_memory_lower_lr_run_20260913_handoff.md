# Single-seed lower-LR actual-record memory candidate — EDITSTOP

September 13, 2026. Main owns native prepare, placement, launch and collection.
Implementation and CPU tests complete. No native/model/GPU/network/Git actions
or old-source/repository modifications by this worker. No outcome-driven edits.

## Frozen delivery

- `/tmp/astra_memory_lower_lr_run_20260913.py`
  SHA256 `80467204aa7ccb4a1cbf4f8d85c7be4e7347263f98f4f7b8fef5739980fcf413`
- `/tmp/test_astra_memory_lower_lr_run_20260913.py`
  SHA256 `0c9351c6a0540aa6ea8e07d4b7c81446300981241709247a3d591f340da32406`
- This handoff's hash is reported externally, not self-embedded.

Scope/schema: `astra_memory_lower_lr_candidate_20260913_v1`.
The strict protocol binding is now
`122965224f6a72d1fb852a40dd24c02b78c733751337f37513712f0f3b45bbce`,
read from Main's
`research_notes/astra_memos/ASTRA_ACTUAL_MEMORY_RETENTION_REPAIR_2026-09-13.md`.
Spec must name a separately copied native protocol file with those exact bytes.
The earlier design is also source-bound at
`98df5e78c53921e7dae5c0210800c4ae4f1a068da69b50a1d3bebd1986c4b60c`;
it is provenance, not a substitute for Main's frozen protocol.

## API and behavior

No helper/controller framework required. The one executable exposes:

```text
prepare(root, spec_path, spec_sha256, allow_native=False)
verify(root, plan_sha256, native=False) -> (memory, plan, bound, historical_scores)
controller(root, plan_sha256, allow_gpu=False)
worker(root, plan_sha256, stage, allow_gpu=False)
collect(root, plan_sha256, completion_sha256, out)
```

`prepare` returns `NATIVE_CPU_PREPARED_NOT_LAUNCHED`, `plan_sha256`, `seed`,
`stages`, `updates`, `calls`. `controller` returns
`CANDIDATE_CAPTURE_COMPLETE_NOT_SCORED` and `completion_sha256`.
`collect` returns `COLLECTED_EXPLORATORY_CANDIDATE`, `out`, `scores_sha256`.

Only `WRITE_fit` and `WRITE_readout` are valid new stages. The single training
config is an exact copy of original `configs.WRITE` with only `lr` changed
from `1e-4` to `3e-5`. Its inherited note remains byte-identical too; the outer
scope/claim/protocol declare this candidate. The parent is the original
perception adapter, never its memory WRITE descendant. Same seed, fresh
optimizer, eight passes, batch1, rank8/alpha16/dropout.05, original frozen
base and LoRA target modules. Costs per seed0/1/2:112/64/64updates and
88/76/76calls;240new updates and240new calls total. No new LR0 work.

The pinned old runtime is imported without changing its globals:
`/tmp/astra_real_record_memory_run_20260913.py`, SHA256
`7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e`.
This exact default path must exist to bootstrap; `spec.runtime` is also checked.
Direct calls reuse its `encode_training`, `build_calls`, `fit_arm`,
`capture_readout`, `check_fit`, `route_for`, `score_calls`, `summarize`,
`identity`, `cleanup_owned`, `check_allocation`, budget and exclusive writers.
Only its original-root `verify`/`validate_completed` are used to authenticate
historical runs. No old worker, controller, run_stage or collector is called
with the new plan. The new lifecycle invokes this new executable's worker.

## Closed specification

Exactly these top-level keys (no optional extra keys):

```json
{
  "runner_sha256": "80467204aa7ccb4a1cbf4f8d85c7be4e7347263f98f4f7b8fef5739980fcf413",
  "runtime": {
    "path": "/tmp/astra_real_record_memory_run_20260913.py",
    "sha256": "7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e"
  },
  "design": {
    "path": "/tmp/astra_memory_retention_repair_design_20260913.md",
    "sha256": "98df5e78c53921e7dae5c0210800c4ae4f1a068da69b50a1d3bebd1986c4b60c"
  },
  "protocol": {
    "path": "/tmp/astra_memory_lower_lr_20260913_attempt1/protocol.md",
    "sha256": "122965224f6a72d1fb852a40dd24c02b78c733751337f37513712f0f3b45bbce"
  },
  "history": {
    "root": "/localhome/local-rohing/astra_diagnostics/real_record_memory_seed0_20260913_attempt1",
    "plan_sha256": "66fb0ae06fce25feb04c422add3062f8665be9bafaa72efdb348365fa82208c1",
    "completion_sha256": "08deffd0a0baa3bcad110884d250893f8470ae320afd13a3d71e20a651da4972",
    "collection": {
      "path": "/localhome/local-rohing/astra_diagnostics/real_record_memory_seed0_20260913_attempt1_collected/collection.json",
      "sha256": "fbbc8ddf580e2141c01a3b73477605e7e5a77bc8e638126475950ea1f105dfab"
    },
    "scores_sha256": "b56a0caa16259e29860efa284d283610ab9bfa9064c64f121fe7cc34266b72bf"
  },
  "seed": 0,
  "fit_seed": 0,
  "gpu_index": 4,
  "gpu_uuid": "GPU-REPLACE-WITH-MAIN-CURRENT-ALLOCATION",
  "expected_boot_id": "REPLACE-WITH-CURRENT-36-CHAR-BOOT-ID",
  "lease_end": 0
}
```

This is a template, NOT an executable allocation: Main supplies the actual
UUID/current boot/lease and native copy paths. For seed1/2, use indices5/6 only
after Main's independent allocation checks, set seed=fit_seed, substitute the
corresponding original root/collection, and use `HISTORY_PINS[seed]` in tuple
order `(plan, completion, collection, scores)`. No history/root discovery or
remote query is performed here. Exact pins are independently hard-coded for
all three seeds. Local collection evidence was read from
`/tmp/astra_memory_collected_20260913_attempt1`.

History pins for seed1:

```text
plan       9886ef9f19869f69649ee894e15c1fb47dfc85e301ee728adfbefc4df2c9c52b
completion 56d19072b3f9474631c4b0d61ca23a21fde490ad80a9dd197f310ecd7023ff92
collection f0ac6662ccb6b6cb9477503fa7214578a1dade4e376e8b1e6c4395e2ae5c6268
scores     5fe7638aa86e718b36ea00f9a97b9e36acbed4b464c968737acbc86447c71979
```

History pins for seed2:

```text
plan       48f64f78aa6953baa72067602bf3043c0a8fb5531750f0433c6fdd8ef76dc5ea
completion e7ef9be2d572251e64c5973305fdcad0112d9569498c79c6646848049850987f
collection f0333bdd6854a27fc1a8825db852ec5976c3b50db667d9b762e2e489634d882a
scores     a0182417e86e85ab6a874c7e98d77fd5952e2bb036fe1a2e35d6e7289ecb0cef
```

## Native commands for Main only — not executed by author

Use the original native interpreter/dependencies, not a relocated local
archive. Historical verification deliberately requires original absolute
root paths, original collection claims and Python identity. The prepared
historical interpreter is `/localhome/local-rohing/v2/venv/bin/python`.

```bash
NATIVE_PY=/localhome/local-rohing/v2/venv/bin/python
RUNNER=/tmp/astra_memory_lower_lr_run_20260913.py
ROOT=/localhome/local-rohing/astra_diagnostics/real_record_memory_lower_lr_seed0_20260913_attempt1
SPEC=/tmp/astra_memory_lower_lr_20260913_attempt1/seed0.json
SPEC_SHA=$(sha256sum "$SPEC" | cut -d ' ' -f1)
env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 "$NATIVE_PY" -B "$RUNNER" prepare \
  --root "$ROOT" --spec-path "$SPEC" --spec-sha256 "$SPEC_SHA" --allow-native

PLAN_SHA=$(sha256sum "$ROOT/plan.json" | cut -d ' ' -f1)
env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 "$NATIVE_PY" -B "$RUNNER" controller \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA" --allow-gpu

COMPLETE_SHA=$(sha256sum "$ROOT/capture_complete.json" | cut -d ' ' -f1)
env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 "$NATIVE_PY" -B "$RUNNER" collect \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA" --completion-sha256 "$COMPLETE_SHA" \
  --out "${ROOT}_collected"
```

Main should freeze/check returned pins before launch and collect only after
successful completion; these commands are not an automatic retry chain.
Main's reservation holder remains responsible for occupancy custody while
the controller's CVD is empty. Worker CVD is the new spec GPU UUID. Fresh
vacancy, boot and lease checks use the new binding, not original GPU1/2/3
reservations. Each stage is a new session/process, cleanup uses PID/group/
start-ticks ownership and requires GPU release before a released receipt.
No foreign-process kills. The current post-memory-formation work is separate.

## New artifacts and verification

The fresh root contains exact byte copies of `dataset.json`, `capture.json`,
`retention.json`, `training.json`, `calls.json`, plus `spec.json`. Original
plan/completion/collection/scores are copied under explicitly historical
`history/` paths, never under new LR0 stages. Plans carry hashes for all
copies, frozen source/spec/protocol, original parent/model/config inventories
and the sole LR delta. Preparation re-encodes training and rebuilds calls
and requires exact equality before writing a plan. Fit/readout independently
repeat the frozen native encoder/prefix checks. Context remains masked, exact
raw target plus EOS supervised, no truncation or target normalization.

Verification re-derives the entire candidate plan from the authenticated
original; changed init adapters, configs, inputs, outputs or allocations fail.
Original completion and once-collection claim are read-only authenticated.
Original score cells join each stored raw response by ID/hash/raw/finish.
New fit initialization/source tensors must match BOTH historical arms;
old LR0 initialized=final and base-frozen/fresh-optimizer invariants retain
the original checks. Same native inference model/template/settings/token
prefixes/caps are inherited. No requirement is imposed on model outcomes.

New receipt: `capture_complete.json` binds only the two new stage inventories,
new calls/updates, elapsed seconds, and `scored=false`. New collector creates
only its own sibling `.collection_claim.json`, never calls original collect,
and writes new `scores.json` + `collection.json`. A claim is consumed even
when scoring fails; failures are preserved with no automatic rerun. Same
source directories and old roots remain required for verification; snapshots
do not authorize relocation or replacement of original custody.

New report:
- `cells.WRITE`: new raw/finish/score/cost cells only.
- `historical_cells.HIGH` and `.LR0`: untouched stored cells.
- `reused_endpoints`: explicit noncontemporaneous flags and zero incremental
  calls/updates for each historical endpoint.
- `comparisons.candidate_vs_historical_LR0` and
  `.candidate_vs_historical_HIGH`: unchanged `summarize` outputs.
  Its fixed reducer slots are WRITE=the candidate and LR0=the NAMED historical
  endpoint. In the HIGH comparison, the internal slot named LR0 holds HIGH;
  `comparison_labels` explicitly explains this, not a new LR0 stage.
  Reducer generation costs retain historical observation costs; only
  top-level `incremental_cost` denotes new expenditure.
- Separate field/content/production/canonical/exact-byte endpoints, paired
  row losses/gains, fixed memory possible denominator16, actual denominators
  14/8/8, held48/canary12, fit manifest, norms and masked-token accounting.
- `strict_exploratory_repair_screen`: exact `production_eligible` count at
  least8/7/5 AND no loss of ANY LR0-correct held or canary item. Gains cannot
  offset lost items. `met` is descriptive only, not execution, retry,
  selection or qualification authorization. `automatic_pass=false`,
  `scientific_pass=null` remain even if the screen is met.

## CPU checks and limits

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 60s python3 -B -m unittest discover \
  -s /tmp -p 'test_astra_memory_lower_lr_run_20260913.py' -q
```

Final run: **22 tests PASS,0.302s**; CLI `--help` also passed. Tests exercise
LR-only delta/three-seed budgets, byte-copy/mask/prompt replay, original-parent
enforcement, seed/source/protocol pins, original raw joins, duplicate/missing
rows, warm-inventory mismatch, no forged LR0 receipts, worker dispatch,
failed precheck/no spawn, owned cleanup, simultaneous timeout/cleanup failure
preservation, candidate-only controller costs, collector one-shot/failure,
historical labels/costs, and strict itemwise screen. Native boundaries are
mocked, not executed; the old13tests were not duplicated. Source hashes were
rechecked unchanged after tests. Main's native CPU prepare is still required.

Controller alarm3600s covers verification, stages and completion checks;
stage wait reserves the inherited cleanup interval. Prepare/collector alarms
are180s including verification. Failure to establish ownership or release
preserves failures, emits no successful release/completion, and needs Main's
reconciliation. This is inherited simple lifecycle hygiene, not a formal C11
guard or proof against every OS failure. No native identity or timing was
validated on this CPU host. No new fits/readbacks occurred here.

The scientific comparison is one prespecified lower LR from the same original
parent and same experience, not new experience or a new learner replication.
Historical endpoints are noncontemporaneous. The old held panel is now an
inspected exploratory repair panel; partial tradeoffs are not full repair,
and even a full screen does not establish general retention/learning/H1/H2.
No changed corpus, targets, scoring thresholds, hidden teacher rewriting,
automatic dose escalation, fresh-test or thesis promotion.
