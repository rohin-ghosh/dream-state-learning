# Fundamental memory training-prompt diagnostic — 2026-09-12

Status: EDIT-STOP after CPU validation. Main owns allocation, launch, native
execution review, and all Git operations. This contributor performed no Git,
network, GPU/model execution, fitting, or changes to the existing corpus/readout.
No manuscript files were touched. Tests used temporary CPU-fixture directories.

## Only owned deliverables

- `organism_v6/fundamental_memory_diagnostic.py`
- `tests/test_fundamental_memory_diagnostic.py`
- `/tmp/astra_fundamental_memory_diagnostic_handoff_20260912.md`

Implementation SHA256:
`4befc61714b4bc9276a387e6934d7010ea1c609857d02080796952f3bd99768c`

Test SHA256:
`9d8f1f1977440d851bb29c305f3d998caa7a5093d41d16d278ea05d128f96bce`

## Diagnostic contract

The separate plan and reduction carry the exact label
`IN_SAMPLE_TRAINING_PROMPT_DIAGNOSTIC_NOT_HELDOUT`.

Selection is all `train-memory-000` through `train-memory-015`, in that order,
one per original device. Each context is copied from the deterministic committed
`fundamental_teaching_corpus.build_candidate()` training row, not an evaluation
paraphrase or a reconstructed answer-bearing lesson. Both teach/control rows
must agree with the source event's device and color. Original training record
IDs, source-event IDs and the full source record are preserved in plan metadata.
Duplicate/missing/extra memory cases, duplicate sources, changed targets,
changed device bindings, and altered original contexts fail selection.

The full model-visible user content is exactly:
`Which color does the log assign to device-NNN?`

There are 16 calls per state, call IDs `0000` through `0015`, with temperature
0.0, generation seed 20260912 and max_tokens 64. No reminders, answer facts,
examples, custom stop rules, confirmation cases, retries, or additional training
are added. `role=memory_diagnostic` and `arm=readout` are usage metadata only.
Requests and native inputs are identical for OFF and any selected adapter.
Run a separate fresh root for each state; the adapter path/identity distinguishes
states, not a caller-supplied scientific label.

The original fixed 48-case development endpoint is unchanged. This is an
in-sample diagnostic of training-prompt recall versus paraphrase performance,
not a new primary endpoint or heldout confirmation. It does not establish a
unique failure mechanism, internalization, parenting efficacy, or H1/H2.

## Reuse and fail-closed custody

The module directly reuses the existing readout's `capture`, `native_inputs`,
and `score_memory` functions. It uses the shared native backend, supervision,
native token/text audit, hashing, exclusive artifact writes and usage helpers.
Production code does not monkeypatch any prior readout globals. The new module
owns only its selection/plan, bounded worker entrypoint and reduction.

- `prepare(out, model, adapter, device, lease_end)` creates a fresh external
  output root and stores `plan.json` plus `plan.sha256.json`. Adapter is a local
  path or `None` for OFF. Model must be a local Qwen-configured directory;
  adapter weights/config must resolve through the existing identity helper.
  Output may not overlap the repository, model, or adapter.
- Source-code hashes, a full deterministic candidate hash, exact cases and
  requests, model and adapter file hashes, loader identity, native rendered
  prompts/token IDs, fixed limits and the diagnostic label are verified before
  execution and reduction. The source closure includes the prior readout,
  corpus, backend, supervisor and shared audit helpers.
- `run(root, allow_gpu=False)` refuses without explicit opt-in and delegates to
  the existing supervisor; a used/failed run root cannot be retried. Its worker
  verifies the device, command, live supervisor parent and owned PID/process
  group before constructing the backend. Parent loss, deadlines and lease
  expiry use the existing owned-group cleanup pattern.
- `reduce(root)` requires successful supervision and verified group/device
  cleanup, process/command/device bindings, a matching backend-ready PID,
  bounded monotonic call timing, backend cleanup and no failure marker. It
  verifies the capture manifest, exactly 16 request/response pairs, identity,
  raw request/response hashes, prepared inputs, native token/text reconstruction
  and the usage receipt. Missing/incomplete/duplicate requests or absent native
  fields fail; missing artifacts never become zero scores.
- A complete malformed model response may score invalid/incorrect. Raw text is
  retained in every scored row; the capture retains raw requests, responses,
  actual prompt/output token IDs, timestamps and hashes. Counts include total,
  correct, invalid and valid-answer frequencies, without subset selection.
- Reduction records plan/capture/process/supervision digests, source/corpus
  hashes, model/adapter identities, actual native token counts, generation
  seconds and supervised reserved seconds. The 1024-token output ceiling is a
  cap, not usage. Monetary cost is unknown; no billing rate is inferred.

Preparation requires more than 750 seconds remaining (600-second worker bound,
140-second cleanup reserve, 10-second lease margin). `lease_end` is Unix seconds.
Run/reduce use the same Python interpreter and root path for exact command
custody. The supervisor window includes its owned cleanup, but not CPU
preparation, Main's audit, or Main's full allocation/queue reservation.

## Main-only execution examples — not executed here

Use a frozen source snapshot and local model/adapter files. These are templates;
Main selects the device, fresh root, adapter and real lease end. Prepare and
reduce load only the local tokenizer for native audits, not model weights.

```bash
python3 -B -m organism_v6.fundamental_memory_diagnostic prepare \
  --out "$FRESH_ROOT" --model "$LOCAL_MODEL" --adapter "$SELECTED_ADAPTER" \
  --device "$DEVICE" --lease-end "$LEASE_END_UNIX"
python3 -B -m organism_v6.fundamental_memory_diagnostic run \
  --root "$FRESH_ROOT" --allow-gpu
python3 -B -m organism_v6.fundamental_memory_diagnostic reduce \
  --root "$FRESH_ROOT"
```

For OFF, omit `--adapter` during preparation; use another fresh root. Main must
retain a reservation on any unverified cleanup/failure; this handoff does not
allocate or release devices.

## Exact CPU validation commands and results

From `/data/home/rohing/dream-state`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_fundamental_memory_diagnostic.py' -v
```

PASS: **28 tests**, 1.845 seconds. Pure selection/scoring and local fixture
prepare/capture/reduce tests; native backend and real supervision are blocked
or mocked. Worker signal checks mock signals/processes; no actual GPU worker is
started. Successful fixture scores (including 4/16 for literal red) are scripted
test expectations, not newly measured model outcomes.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_fundamental_*.py' -v
```

PASS: **61 tests**, 3.365 seconds, including the 28 new tests plus the 33 existing
fundamental corpus/readout tests. The counts are overlapping, not 89 distinct
tests. No full repository suite was run.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m organism_v6.fundamental_memory_diagnostic --help
sha256sum organism_v6/fundamental_teaching_readout.py organism_v6/fundamental_teaching_corpus.py tests/test_fundamental_teaching_readout.py tests/test_fundamental_teaching_corpus.py
```

PASS: CLI exposes only prepare/run/reduce/internal worker. Four baseline hashes
match their pre-edit values:

```text
d6eebc6e70f5a76fcde6c530aeacc273ae5f29a8d9a67ffe5948f04842684bb6  organism_v6/fundamental_teaching_readout.py
44b1a61e10695e1e65ca3ee2e6c151eba45df1512ea3fc108402e96226ddaa13  organism_v6/fundamental_teaching_corpus.py
9950b74a6f31c1e5034355da67a6f57b462b503332a32144703ebf821172d052  tests/test_fundamental_teaching_readout.py
4db6fd41c64b5c9f43018f188d7eb9c36f416f9b73066812bc5dc8b0b678824a  tests/test_fundamental_teaching_corpus.py
```

Additional CPU-only inline assertions passed: parse both new Python files with
`ast.parse`; compare those four baseline hashes; check 16 distinct devices and
requests, all decode settings, original context equality, unchanged 48-case
selection, and shared capture/scorer function identity. No bytecode was written.

Deterministic full-candidate hash:
`178844a86d5bcb5a1576247abf7bbb44eb6d67645334d60e033d8e1b118e9544`

Selected diagnostic-case hash:
`f9804de169f21d61dcfd8e2e0fd84c7bcb6270f8d0d7a869b57437f435c69ea5`

## Exact limitations / next owner action

No native tokenizer audit against the real model, vLLM load, GPU supervision,
adapter readout, fit, scientific outcome or independent review was performed by
this contributor. CPU fixture passes validate implementation behavior only.
Hash/custody checks bind local loader inputs and recorded artifacts; they do
not independently authenticate the base's origin, prove the adapter's training
history, or protect against an actor replacing an entire artifact chain. Main
must use the intended fit adapters and corpus/source snapshot and perform the
real native execution/review. The original development endpoint remains fixed.

EDIT-STOP: deliverables are ready for Main's allocation and scoped review.
