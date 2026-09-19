# R139 implementation sidecar: R134/R137 missing continual controls

## Design recorded before implementation — 2026-09-16

Scope: only `gpu/orch_r139_continual_controls.py`, its fixture-only CPU tests,
and this note. This implements the already authorized R134 controls; it changes
no thesis, base, held registry, isolation, parent blindness, live child or shared
native/journal/stream file. No GPU launch, retirement, lease action or commit is
performed by this sidecar. Sagan `01a0a99f-4dd0-7b82-b062-d13be60e2c79` owns
integration/admission and actual A100 operations. Main retains console/kernel
recovery. `send_input` is not exposed in this session; this note and the final
handoff are the available in-repository coordination surface, not a claim of
delivered agent messaging.

### Interface and scientific interpretation

Export `validate_plan(plan)`, `run(plan_path)`, and
`run_readout(plan_path, manifest_path, output_path)`. CLI `--validate-only`
performs CPU validation, `--readout-manifest ... --output ...` is exclusively
the separate readout worker; ordinary `--plan ...` is the operator entrypoint.
There is no resume, training, sleeping, GPU allocation or retirement API.

The PLAN uses schema `R139_CONTINUAL_CONTROLS_V1` and preserves the native R127
startup binding, system/birth bytes, seed, decoder, context/presentation,
segment budget, GPU identity and wall/lease binding. Native training schedule
fields remain reference metadata, not executed operations. A distinct control
configuration identifies `frozen_rank8_no_sleep` or `frozen_base_no_adapter`,
explicit zero learning/optimizer steps, no sleep and no sleep compaction.
An attributed runtime notice corrects any inherited learning/sleep language in
the matched startup. The notice is a documented prompt difference, not hidden
as exact prompt identity with a learning child. Ordinary oldest-context eviction
remains identical. Parent messages use the same TRAIN mailbox and attribution;
there is no benchmark-to-parent route.

Frozen rank-8 supports two explicitly different initializations: genuinely
seed-initialized native rank-8 (never described as pretrained), or a pinned real
pretrained adapter directory with file hashes and expected tensor-state hash.
A missing adapter is a hard failure, never silently replaced by random weights
or a base model. The base control has no adapter object or adapter artifact.
Reuse the frozen Engine's actual tensor base-fingerprint verification; do not
substitute a constant hash as evidence. Preserve native RNG ordering: seed
Python/Torch/CUDA before seeded LoRA initialization, then reset those generators
to the explicit PLAN seed before continuous sampling. Pretrained and base modes
also explicitly reset all three before sampling. Record the exact recipe,
initialization kind, dependency source hashes and runtime versions.

### Checkpoints, cadence and isolation

Create one immutable frozen-model identity manifest and, only for a real LoRA,
one actual adapter serialization. These are model artifacts, NOT sleep or
optimizer checkpoints. No optimizer is constructed; no optimizer/RNG checkpoint,
sleep receipt, training exposure, compaction generation or fictitious update is
emitted. The reused stream's `sleep_due` property is deliberately ignored, with
sleep frontier/receipts left at zero/empty. Generation, journal reservations,
raw responses, context accounting and mailbox ingestion remain native.

Read out initially and every explicitly recorded N ordinary committed segments
(N=2 for the native per-sleep frontier). The PLAN also records the reference
sleep's extra presleep generations (0 for no-distillation, 1 otherwise).
These are **generation-frontier-equivalent scheduled readouts**, not equal wall
time/token exposure or simulated sleep. No claim of a matched programme twin
without an actual matching parent programme/seed. A bounded smoke limit counts
scheduled readouts, not sleeps. Each readout is a fresh subprocess with only
PLAN/frozen model, no stream/inbox/history or optimizer; resident weights offload
and resident Python/CPU/CUDA RNG are saved/restored in memory. Failed readouts
stay explicit and are never replayed implicitly.

Reuse the unchanged held-policy registry/messages/capture functions only inside
the worker, with its existing fixed readout decoder/cap. Adapter readouts have
actual ON/OFF arms; base readouts have OFF only, never a fake ON pair or invented
adapter checkpoint. Policy's legacy `checkpoint_sha256` capture field binds
the frozen tensor-state identity (base fingerprint for base-only); the wrapper
labels this meaning explicitly. Results stay under separate node-local readouts
and are never copied into the TRAIN journal or returned to a parent.

### Acceptance and operator gate

CPU tests use fabricated plans, tokenizers, models, mailbox events and readout
policies only; do not load real held tasks/results. Cover mode/adapter validation,
explicit seed/RNG ordering, no optimizer construction, actual frozen identity,
generation continuation across scheduled boundaries, no sleep/compaction,
parent attribution, unchanged decoder/context, base-only fresh readout,
ON/OFF adapter readout, source/admission/gate drift and RNG restoration.
Operator must bind a passing CPU/provenance receipt to exact PLAN/source bytes,
log dated `[Builder]` CPU/provenance checks in `research_loop/COORDINATION.md`,
and perform their own node admission before launch. This sidecar cannot edit
that shared coordination file or claim remote CUDA validation. Independent
operator launch remains Sagan's decision; nothing here launches GPUs.

## Operator integration handoff — 2026-09-16 11:20 UTC

**Ready for independent operator integration, not a science-launch receipt.**
Only the three owned files were edited. No shared code/coordination edits,
GPU operations, commits, node inspection or live-child configuration changes.
No `send_input` capability became available; direct delivery to Sagan is still
for the supervising console to perform.

### Build a new control PLAN

`make_plan(reference_plan, *, mode, adapter=None, max_readouts=None)` returns a
validated JSON-serializable dict. `reference_plan` is a NEW operator-prepared
native-shaped allocation, not a mutable reference to a live child's PLAN.
Use a fresh node-local `root`, admitted GPU UUID/physical index and current
lease/wall; preserve the comparison's exact seed, decoder, segment/context
budgets, presentation version and pinned R127 startup bytes. `source_root`
must be the actual executing source snapshot, including the test file and all
`SOURCE_FILES`; rebind the startup path into that snapshot without changing its
bytes. Validate/retain the original matched-life PLAN separately: the helper's
`reference_plan_sha256` is the canonical JSON digest of the supplied NEW
allocation, not a claim to hash the original live PLAN's raw bytes.

```python
from gpu.orch_r139_continual_controls import make_plan

base = make_plan(new_base_allocation, mode='frozen_base_no_adapter')
rank8 = make_plan(new_rank8_allocation, mode='frozen_rank8_no_sleep',
                 adapter={'initialization': 'seeded_rank8'})
```

For genuinely pretrained LoRA, use instead:

```python
adapter = {
    'initialization': 'pretrained_rank8',
    'path': '/absolute/operator_verified_adapter_directory',
    'files': adapter_files('/absolute/operator_verified_adapter_directory'),
    'state_sha256': actual_adapter_tensor_state_sha256,
}
```

`adapter_files` validates the existing native rank-8 recipe and SHA256-binds all
regular directory files. The actual safetensors are parsed by frozen Engine;
the loaded tensor-state fingerprint must equal `state_sha256`. No directory,
weights or tensor hash is synthesized for a purported pretrained adapter.
The default seeded mode calls the native initializer itself, preserving rank8,
alpha16, dropout0.05, exact native target modules and initialization order.
This mode is explicitly **never-trained**, not pretrained.

The added control subdocument has this exact shape (seed shown as an example;
the helper copies the reference seed, including native default0):

```json
{
  "mode": "frozen_base_no_adapter",
  "adapter": null,
  "learning_steps": 0,
  "optimizer_steps": 0,
  "sleep_enabled": false,
  "compaction_at_sleep": false,
  "readout_schedule": {
    "initial": true,
    "every_segments": 2,
    "reference_presleep_extra_segments": 1,
    "basis": "ordinary_committed_segments",
    "max_readouts": null
  },
  "sampling_rng": {
    "seed": 0,
    "initialization": "native_before_lora_then_reset_before_generation",
    "generators": ["python", "torch_cpu", "torch_cuda_all"]
  }
}
```

`reference_presleep_extra_segments` is0 for a no-distillation reference and1
otherwise. `max_readouts=N` means N scheduled post-generation readouts **plus**
the initial readout; native `max_sleeps` remains inert reference metadata.
Frozen base does not execute a LoRA initialization despite the common RNG policy
name; its actual initialization is `adapter: null` with one pre-sampling reset.
No equal wall-time, total-token exposure or programme-effect claim is implied.

### CPU/provenance and launch interface

1. Stage the source snapshot, candidate PLAN/startup and real adapter if needed.
   Run `python -B -m gpu.orch_r139_continual_controls --plan PLAN.json
   --validate-only`. This is CPU validation only, never model loading or admission.
2. Run the fixture-only tests below against those exact source bytes; preserve
   stdout as an immutable test log. If any shared dependency changes, regenerate
   the inventory, rerun tests and issue a new bound gate rather than bypassing it.
3. Compute `plan_binding(plan)` (canonical digest excluding only `cpu_gate`).
   Sagan/operator adds a dated `[Builder]` CPU/provenance line containing that
   digest to shared `research_loop/COORDINATION.md`. This sidecar did not add it.
4. Write a gate receipt with these fields:

```python
{
    'schema': 'R139_CPU_PROVENANCE_GATE_V1',
    'status': 'PASS',
    'plan_binding': plan_binding(plan),
    'source_files': plan['source_files'],
    'tests_passed': True,
    'test_log_path': absolute_preserved_test_log,
    'test_log_sha256': sha256_of_exact_test_log,
    'coordination_line': exact_dated_builder_line,
}
```

Set `plan['cpu_gate']` to `{'path': absolute_gate_path, 'sha256': sha256_of_gate}`
and write the final PLAN once. The runtime verifies source inventory, gate bytes,
PLAN binding, test-log bytes and the exact existing Builder line before loading
a model. The source snapshot's coordination file must contain that line too.
The receipt is an operator attestation bound to evidence, not an independent
test-result verifier or proof of GPU availability.

5. After Sagan's independent node admission, the supported process entrypoint is
   `python -B -m gpu.orch_r139_continual_controls --plan /absolute/PLAN.json`, with
   `CUDA_VISIBLE_DEVICES` equal to the single admitted GPU UUID and
   `R125_ADMISSION_PLAN_SHA256` equal to the SHA256 of the final PLAN file bytes.
   Callable equivalent: `run(plan_path)`. The caller must be in the main thread,
   with no existing process interval timer: the callable installs its own hard
   wall alarm and refuses to overwrite another operator's alarm.

The worker command is generated internally as the same module with
`--readout-manifest ROOT/frozen_model/MANIFEST.json --output ROOT/readouts/control_NNNNNN`.
It enforces fresh CUDA state and loads neither stream nor mailbox. Existing
`gpu.orch_r125_continual_readout` cannot substitute here: its adapter/optimizer
COMMIT assumptions deliberately remain unchanged.

### Artifact and parent interface

- `ROOT/stream/`: existing `StreamJournal` layout, actual generation REQUEST /
  RESPONSE / COMMITTED records and unchanged TRAIN inbox schema. The attributed
  parent inbox works with Astra/Fable/Rohin and keeps parents distinct from child
  targets; fixture tests exercise the real mailbox and journal replay.
- `ROOT/frozen_model/MANIFEST.json`: actual verified frozen base/adapter identity,
  runtime versions, initialization, seed policy and zero updates. Only a real
  adapter creates `ROOT/frozen_model/adapter/`; no `checkpoints/`, optimizer or
  RNG checkpoint is created. Resident RNG preservation is in memory only.
- `ROOT/readouts/control_NNNNNN*`: separate dispatch/frontier receipts, raw
  call records, before/after identities and COMPLETE or FAILED. Base has32 OFF
  calls and `paired_scores: null`; rank8 has64 actual ON/OFF calls with the
  unchanged paired reducer. Failed inference/capture preserves available raw
  responses and produces no fake COMPLETE; no implicit replay.
- No readout result/score is added to TRAIN records or returned through mailbox
  APIs. Parent tooling may consume normal stream records but must not ingest
  the readout directory. No parent broker was launched or modified here.
- No resume implemented: an existing stream or frozen manifest refuses restart.
  An interrupted life remains preserved for operator disposition, not silently
  reseeded. No optimizer or fake sleep frontier is used to support recovery.

### Recorded CPU evidence

At **2026-09-16 11:20 UTC**:

```text
uv run --with pytest python -m pytest -q \
  tests/test_orch_r139_continual_controls.py \
  tests/test_orch_r125_continual_native.py \
  tests/test_orch_r125_stream_journal.py \
  tests/test_orch_r125_continual_stream.py \
  tests/test_orch_r125_plain_context.py
182 passed, 197 subtests passed in 23.32s
```

Control-only suite: **39 passed**. All control readout tests substitute a
fabricated32-task policy; no real held registry is evaluated by these tests.
GPU model loading, actual adapter serialization/reload, performance and real
held readout completion remain **unverified on CUDA** and belong to the operator.

Preserved local test log: `/tmp/orch_r139_continual_controls_cpu_20260916.log`.
SHA256: `cf6eb6a762838a76dffd5cf970ef24779b56f699dfc6e249ffb4c0b2f0ebb849`.

Source SHA256:
`da4df71623812697c34a2c4cac8746e097d4faf0374808f12dd500fd52cc9f50`.
Test SHA256:
`72c875c551277c76f87cc06b1723158a744d1791e9bfa5a41dcba2cf1e6c4cff`.
