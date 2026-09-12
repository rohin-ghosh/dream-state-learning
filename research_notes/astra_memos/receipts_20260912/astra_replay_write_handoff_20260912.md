# Coached-replay child-only preparation handoff — 2026-09-12

## Scope and status

Implemented NEW ONLY:

- `organism_v6/parent_note_replay_write.py`
- `tests/test_parent_note_replay_write.py`

No existing helper, protocol, coordination notebook or other agent's file was
edited. No Git commands, GPU inspection/use, replay execution, real-source
preparation, model inference, training, leases or launch actions were performed.
Only synthetic CPU fixture tests were executed. Main owns integration, actual
preparation, downstream provenance checks, scheduling, training and probes.

## Exact preparation CLI

From the repository root, main sets the variables below to its actual paths.
The real replay root and production output paths were not supplied to this
worker, so none are invented here. Use canonical absolute paths without
symlink components. All output parents must already exist; preparation root,
both adapters and both trainer logs must be absent and mutually nonoverlapping,
and must not overlap the replay, either original source root, or model root.
`PREP_PYTHON` must have the actual local tokenizer dependencies;
`TRAINER_PYTHON` identifies the existing downstream trainer environment.

```bash
"$PREP_PYTHON" -B -m organism_v6.parent_note_replay_write \
  --replay-out "$REPLAY_ROOT" \
  --out "$PREPARATION_ROOT" \
  --lesson-adapter-out "$LESSON_ADAPTER_OUT" \
  --sham-adapter-out "$SHAM_ADAPTER_OUT" \
  --lesson-trainer-log "$LESSON_TRAINER_LOG" \
  --sham-trainer-log "$SHAM_TRAINER_LOG" \
  --python "$TRAINER_PYTHON"
```

This command only prepares files and prints a JSON report. There is no execute,
GPU, fit, generation, retry or permissive eligibility option. Insufficiency is
an explicit `PAIRED_SKIP_INSUFFICIENT_MATERIAL` report, not an exception; main
must inspect the status rather than treating exit zero as fit authorization.
Invalid or changed evidence raises before publishing the preparation directory.

Python API:

```python
prepare_write(
    replay_out, output_dir,
    adapter_dirs={"lesson": lesson_adapter, "sham": sham_adapter},
    trainer_logs={"lesson": lesson_log, "sham": sham_log},
    python_executable=trainer_python,
)
```

## Consumer contract and provenance

- Calls the actual `parent_note_replay_diagnostic.validate_replay(root,
  tokenizer=tokenizer)` before selection and again before publishing; consumes
  its `results`, `records` and `sources`, without bypassing its source, raw
  generation, judgment, complete-teacher/coaching-echo or local-model checks.
- Also binds the replay inventory before/after preparation, compares parsed
  raw records to the validated records, and checks writer source bytes again.
- Selects first64 normalized-unique faithful texts per arm in the revalidator's
  physical source order. Duplicate source records are invalid; repeated faithful
  child text contributes only one unique record. Neither ranking nor editing
  the child body is allowed. `Situation ... / My measured action record:` is
  only the existing trainer wrapper, and is loss-masked by existing utilities.
- Requires both arms to have at least64 unique faithful records. Otherwise both
  arms have zero selected rows, empty source-map records, and no corpus,
  tokenizer-preflight artifact or trainer argv, even if the other arm is full.
- Uses the actual locally loaded tokenizer via existing `_load_tokenizer`,
  `tokenizer_preflight`, `child_record_prefix_length`, masks and label counts.
  No truncation; per-batch padded length must fit512; causal child-token and
  prefix/padding masking evidence must pass for both arms before any files.
- Does not call `_formation_snapshot`, invent original formation artifacts,
  construct a gate/admission/ancestry certificate, or assert clean/H1 evidence.
  Official base authentication remains UNRESOLVED / LOCAL_HASHES_ONLY; this is
  historical-source shared-coaching exploratory material, not new episodes.
  Original teacher-dose confounding and unequal actual token doses remain.

## Artifacts

Root files:

- `write_prep.json`: paired status, arm reports, boundaries, retry policy.
- `replay_inputs.json`: replay and original-source inventories/manifest hashes,
  source roots, coach hash and recorded replay implementation hashes.
- `local_base_pins.json`: actual validated local model byte pins, not authentication.
- `source_hashes.json`: preparing helper, existing writer and trainer source hashes.
- `artifact_hashes.json`: SHA256 for every other emitted file, using relative
  paths including `lesson/...` and `sham/...`. This is a preparation manifest,
  NOT an original-formation manifest or a replay artifact inventory.

Each of `lesson/` and `sham/` always gets `write_prep.json` and `source_map.json`.
When BOTH READY, each additionally gets `corpus.json`,
`tokenizer_preflight.json`, and `training_command.json`.
Maps bind replay raw-line hashes, source-map hashes, original ACT/old-NOTE
line hashes, original wake/NOTE trace links, output/source/episode/execution
identifiers, unchanged child-text hashes, corpus-item hashes and selection order.
All file bytes and completed preparation directories are made read-only.
Actual adapter and trainer log paths are not created.

Each generated argv targets the existing standalone `organism_v6.train_adapter`
with exactly rank8, epochs3, lr1e-4, seed6102 and a fresh per-arm adapter path.
Expected metadata records64 examples/48 steps plus actual tokenizer-derived
token counts, corpus digest and `child_body_only` targeting. Commands include
offline model environment, cwd and exclusive external-log instructions, but no
device assignment or launch. They contain no clean-gate arguments or receipts.

Before any downstream execution, main must revalidate replay/original sources,
local model, implementation and every preparation digest, confirm BOTH READY
and all adapter/log paths still fresh, and apply its actual reservation rules.
After fitting, inspect actual DONE/EMPTY_CORPUS, finite loss, matching
`metadata_equals`, adapter hashes and separately owned parent-free probes.
Standalone completion is not a learning, lineage or H1 result.

## CPU test evidence

Exact successful command, run from repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  python3 -B -m unittest discover -s tests -p test_parent_note_replay_write.py -v
```

Result: **13 tests passed in67.436s**.
Captured log: `/tmp/astra_replay_write_cpu_20260912.log`.

Tests use existing synthetic historical-source fixtures, manually assembled
synthetic replay artifacts, and a mocked offset/chat tokenizer. No replay run
or trainer is invoked; those entrypoints and `_formation_snapshot` are patched
to fail if called. Actual replay revalidation and actual tokenizer mask/count
utilities remain unmocked. Coverage includes:

- READY exact64/source-order selection, unchanged whitespace/body/raw input bytes,
  source links, file/corpus digests, fixed recipe/argv and loss masks;
- actual complete coach, coaching-sentence and delivered-teacher exclusions;
- paired skip for insufficient lesson or sham, including256 faithful but only63
  distinct child texts;
- missing replay rows and duplicate records even after manifest resealing;
- changed replay/original raw bytes, missing original ACT, source mutation during
  tokenizer preflight;
- real overlength and missing-loss-mask failures in first or second arm, with no
  one-arm publication;
- fresh adapter/output protection and CLI paired-skip behavior.

Environment notes: `python` is absent and system `python3` has no pytest, so no
dependencies were installed and stdlib unittest was used. There is an existing
`reasoning_gym_gym.py:99` unclosed-bootstrap ResourceWarning; it did not fail
tests and was not changed.

## Coordination limitation / message for main to relay

No direct agent-message tool is exposed in this worker session. An explicit
interface message addressed to
`Turing01a09483-1c83-7552-89bd-e9ea84285796` is saved at
`/tmp/astra_replay_write_interface_Turing_20260912.md`.
This is not a delivered-message receipt; main should relay it. The implementation
and tests use Turing's actual current `validate_replay` API and returned fields.
If Turing changes that interface or its fixture contract, rerun these tests and
coordinate with main rather than silently emulating an obsolete revalidator.
