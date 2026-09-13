# Single-seed actual-record memory runner — EDITSTOP

2026-09-13. Runnable implementation; native CPU preparation and GPU execution
remain Main-only and have NOT run here. Only this handoff, the new runner and
its matching tests were written. No old source, adapter, archive, live root,
repository, held answer, protocol or Git state was changed. No monitoring of
the separate high-seed2 access run occurred. Its supplied launch timestamp
1789288756.624 is September13,2026 08:39:16.624UTC.

## API and implementation status

Single pair, one original learner, no batch framework:

```text
prepare --root ROOT --spec-path SPEC --spec-sha256 SHA --allow-native
controller --root ROOT --plan-sha256 SHA --allow-gpu
collect --root ROOT --plan-sha256 SHA --completion-sha256 SHA --out OUT
worker --root ROOT --plan-sha256 SHA --stage STAGE --allow-gpu
```

Functions with the same argument names are available for injection/tests.
Internal fixed stages are WRITE_fit, WRITE_readout, LR0_fit, LR0_readout.
Each stage is a fresh subprocess/process group. Main runs3separate specs with
seed=fit_seed=0/1/2. The same original perception adapter is used in both
`trainer.run_training(..., init_adapter=original_adapter)` calls; LR0 never
initializes from WRITE. Both load a fresh frozen official base and use fresh
optimizers. No source/record conversation enters cold inference.

Protocol is pinned to
`research_notes/astra_memos/ASTRA_ACTUAL_RECORD_MEMORY_PROTOCOL_2026-09-13.md`,
SHA256 `c056a0fb6c97d1ba93b4d2a0fa07cb70f806cfa64fef2df1769d78e80334a716`.
Main may stage identical bytes at a native path. This runner does not change
the protocol in response to the separate HF access result.

## Reused boundaries; no original recollection

`bind_inputs` loads pinned formation runner3c03304e and calls its existing
`verify` and `validate_completed`. It checks original completion inventory,
all four formation state captures, original learner adapter/collection/source
bindings, and v2 core. It does NOT call formation.collect, even once. Already
collected formation-report and collection files have DISTINCT enforced pins:

- Formation plan: `039f8cc66ecae40ed9cbee649011b34e4e4654fec68f5e7d51a37f5a5a5374bd`.
- Completion: `51b09f9a553cfe561ae8613e299a6d4926d8df3286265498927573b41dae1274`.
- **collection.json**: `77260fe6d540beb65cd4f9717a76fc827cb3e441a23663077f72dbdbd7a70a4c`.
- **formation_report.json**: `9d04155a0103377e41f80ad25b7b1b4ed9cd2ffd014503e74b27a0992b4c81f1`.

The original one-shot collection claim is read and checked, never replaced.
Projector2c5538f5 then reaudits and projects the selected learner's actual
capture. All eligible rows stay in original order, including repeated records;
no indexing, balancing, deduplication, repair or target reserialization occurs.
The projector defines exact and paraphrase cues; only exact cues are trained.
Its raw targets and source references remain unchanged in dataset.json.

The pinned Level1 `training_item` supplies exact native full-assistant/EOS
boundary and label checks; normalized item's view label is explicitly changed
from authored_Level1 to `source_withdrawn_real_record`. It changes no prompt,
target, token or label. New8-pass/batch1 accounting reuses the frozen trainer's
encoder, epoch_order and collate, enforcing no truncation/splitting/packing.
Inherited `skill_target` token-category name is metadata, not an authored-target
claim; those tokens are the exact actual child record bytes. Context, template
tail and padding stay masked. PAD/EOS must be distinct. MAX_LEN1024;192output
tokens for every memory and original retention call, inherited greedy settings.

WRITE uses LR1e-4, LR0 uses0.0; configs differ only in LR. Both preserve rank8,
alpha16, dropout.05 and original projection modules,8epochs, batch1, same learner
fit seed, full passes and fresh optimizer. `_warm_parent` prechecks the original
adapter in native CPU prepare; trainer's existing full-state warm-start checks
and frozen-base/trainable-LoRA checks run during fit. Serialized resulting
tensors are checked against the recorded final state; parent tensors converted
to the initialized/saved dtype must match initialized state. Global initial,
final and delta L2 norms plus changed-element count are recorded. LR0 must
remain equal; WRITE must have finite actual parameter change or fail.

## Workload, reporting and limits

For N admitted records: each arm has8Noptimizer steps and2N+60generation calls.
Main's frozen actual counts14/8/8 imply paired224/128/128steps and176/152/152calls.
Across the three pairs:480steps and480calls. Max per pair256steps/184calls.
LR0 steps are optimizer invocations with zero LR, not parameter changes.
Rows/repeated records are not independent learners. Empty valid admission is
NO_WRITE with no fit/readout; no fake adapter or empty-data learning result.

Each arm cold-loads its result into inherited formation.Native/vLLM and gets
exact then paraphrase memory cues, original48held then12canary prompts. Original
retention row IDs/messages/native tokens are checked against archived Level1
calls; its dataset and scorer are replayed unchanged. No target or source
metadata is rendered as a prompt. This is actual generated readback, not the
separate HF teacher-forced candidate likelihood diagnostic.

Collection scores only after both arms are complete/released. Memory scorer is
projector.score_readback against original execution, with stop required. Report
keeps production eligibility, typed content, field correctness, canonical
format, exact raw-target bytes and format counts separate. Primary exact cue,
paraphrase transfer and authored held/canary retention are not pooled. Reports
contain per-arm numerators/eligible denominators plus16possible memory slots,
WRITE/LR0 both/neither/first-only/second-only counts, and original-post versus
current retention item lists (retained/regressed/gained). Original retention
scores are hash checked and replayed, not rewritten. Raw responses, native
request/response hashes, token costs, generation times, loss/fit manifests,
parameter norms and training/context/supervised/padded token totals are kept.

Controller3600seconds and collection180seconds include verification. Native CPU
prepare has a separate180second cap. No automatic retries. Source verification
is not exempt from these caps. Runtime requires a six-hour lease finish margin
and a freshly bound node boot identity. Before each worker and after owned
cleanup, the unchanged public helper performs its30second all-process XML
vacancy/release check, with exact GPU UUID/index. Cleanup reserve40seconds;
controller preserves partial outputs on failure and kills only its identity-
bound child group. Parent checkpoints remain disjoint and immutable.

Main still owns the fresh node2 queue/environment-reservation check and exclusive
allocation before launch, using its existing launcher. XML vacancy is not an
atomic scheduler reservation. No historical GPU assignment is treated as a
current reservation. The controller itself requires CUDA_VISIBLE_DEVICES empty;
it gives only the assigned UUID to each worker. Native preparation/collection
do not reserve a GPU. Main must supply missing current GPU index/UUID, boot ID,
lease end, fresh roots and protocol path; none is guessed or autodiscovered here.

## Spec template and exact native commands

Create a fresh Main-owned spec for each seed; JSON below uses descriptive
placeholders for the current allocation, not valid defaults. Native dependency
paths from the original formation plan must remain available byte-identically;
its verify forbids silently relocating/rebinding a completed plan. No new
training/source snapshot or source edits are needed on the original node2.

```json
{
  "runner_sha256": "7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e",
  "memory": {"path": "/tmp/astra_real_record_memory_core_20260913.py", "sha256": "2c5538f5b63cbb4e592f40822561b4d62595ab3c9d7d193f084b91f9a064e8ef"},
  "formation_runtime": {"path": "/tmp/astra_level1_real_record_run_20260913.py", "sha256": "3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e"},
  "formation": {
    "root": "/localhome/local-rohing/astra_diagnostics/level1_real_record_20260913_attempt2",
    "plan_sha256": "039f8cc66ecae40ed9cbee649011b34e4e4654fec68f5e7d51a37f5a5a5374bd",
    "completion_sha256": "51b09f9a553cfe561ae8613e299a6d4926d8df3286265498927573b41dae1274",
    "collection": {"path": "/localhome/local-rohing/astra_diagnostics/level1_real_record_20260913_attempt2_collected/collection.json", "sha256": "77260fe6d540beb65cd4f9717a76fc827cb3e441a23663077f72dbdbd7a70a4c"}
  },
  "protocol": {"path": "ABSOLUTE_NATIVE_PATH_TO_MAIN_PROTOCOL", "sha256": "c056a0fb6c97d1ba93b4d2a0fa07cb70f806cfa64fef2df1769d78e80334a716"},
  "seed": 0,
  "fit_seed": 0,
  "gpu_index": "REPLACE_WITH_INTEGER",
  "gpu_uuid": "GPU-REPLACE_FROM_FRESH_INVENTORY",
  "expected_boot_id": "REPLACE_FROM_FRESH_NODE2_INVENTORY",
  "lease_end": "REPLACE_WITH_NUMERIC_UNIX_LEASE_END"
}
```

Set ROOT, SPEC, SPEC_SHA, OUT explicitly to fresh Main-owned absolute paths and
the staged spec's exact digest. Use the original formation interpreter:

```sh
PY=/localhome/local-rohing/v2/venv/bin/python
RUN=/tmp/astra_real_record_memory_run_20260913.py
: "${ROOT:?fresh absolute memory root}" "${SPEC:?absolute spec}" "${SPEC_SHA:?exact spec SHA256}"
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  "$PY" -B "$RUN" prepare --root "$ROOT" --spec-path "$SPEC" \
  --spec-sha256 "$SPEC_SHA" --allow-native
```

Require `NATIVE_CPU_PREPARED_NOT_LAUNCHED`, WRITE_AVAILABLE and correct N/costs;
copy its returned plan_sha256 to PLAN_SHA. A failure is not permission to relax
any pin or increase the cap. Main's fresh reservation/queue checks precede:

```sh
: "${PLAN_SHA:?copy exact prepare result}"
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  "$PY" -B "$RUN" controller --root "$ROOT" --plan-sha256 "$PLAN_SHA" --allow-gpu
```

Only after `MEMORY_CAPTURE_COMPLETE_NOT_SCORED`, preserve the completion digest
as COMPLETE_SHA. A failed/partial root is not collectible. Collect this NEW
memory root once, never invoke the original formation collector:

```sh
: "${COMPLETE_SHA:?copy exact controller result}" "${OUT:?fresh external collection path}"
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  "$PY" -B "$RUN" collect --root "$ROOT" --plan-sha256 "$PLAN_SHA" \
  --completion-sha256 "$COMPLETE_SHA" --out "$OUT"
```

Each command emits machine-readable JSON status. Keep stdout/stderr and new
root/collection bytes. Python API can be used by Main's outer launcher without
additional controller helpers. No native command in this handoff ran here.

## CPU evidence and frozen files

13tests PASS in1.992seconds. Includes a full prepare→paired warm-start calls→
separate injected cold readouts→collection vertical slice, original-parent
equality, twice-collection rejection, exact raw target/EOS/context masks,
14/8/16/0row budgets, repeats, config LR-only difference, WRITE/LR0/nonfinite
failures, truncation, wrong outcome/unfinished/source-cue rejection, native
route/prefix drift, deadline-before-launch and owned-process identity rejection.
Pinned real projector/core/encoder are exercised with scripted child records
and a toy tokenizer. Native load/train/tensor-norm/process boundaries are mocked;
these tests do not certify actual native warm-start kernels or device readiness.

First10-test run had one TEST-ONLY normalized-span indexing error (list treated
as dict); the vertical slice already passed. Corrected that assertion, added
three boundary tests, final13-test run passed. CLI help, AST and whitespace
checks passed. Existing projector/formation/core pins rechecked unchanged.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s /tmp \
  -p test_astra_real_record_memory_run_20260913.py -v
```

- `/tmp/astra_real_record_memory_run_20260913.py`:
  `7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e`.
- `/tmp/test_astra_real_record_memory_run_20260913.py`:
  `059f2a3de919697b5587f7268965a0696928a7a1dc3a36fad4c6ca4b937114de`.
- `/tmp/astra_real_record_memory_run_20260913_handoff.md`: hash supplied separately.

EDITSTOP. Narrow real-event acquisition/persistence plus separate transfer and
authored retention only; no improved autonomous learning/internalization or
H1/H2 result is claimed. Main freezes and executes each single-seed pair.
