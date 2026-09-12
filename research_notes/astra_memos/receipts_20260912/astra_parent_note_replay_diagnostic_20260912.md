# Source-replayed coached NOTE diagnostic — frozen handoff

2026-09-12 09:51 UTC. Source/tests complete and frozen for main validation.
No production input reads, Git, network, remote or GPU actions were performed.
Only the two newly assigned files were edited. No full wake rerun, training,
neutral-probe integration, old-source edit or generated-child-text repair.

## Files

- `organism_v6/parent_note_replay_diagnostic.py`
  SHA256 `8131dd06a1b82b63d7690bb8d1f626381e9136512ddd6909bd355d06dd52561f`
- `tests/test_parent_note_replay_diagnostic.py`
  SHA256 `b8440dbdc08801860fda927656a1a9325a29ed5665fcc03f41869cba7276477f`

No further edits planned absent a runtime repair assignment. Main owns review,
archive/deployment, reservations and actual execution. Pasteur owns separate
replay-write preparation; this diagnostic does not construct a corpus.

## Actual node3 CLI (documentation, not executed)

From the fresh deployed source checkout, with the appropriate environment Python:

```bash
CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  "$PY" -B -m organism_v6.parent_note_replay_diagnostic \
  --lesson-root "$P0_LESSON" --sham-root "$P0_SHAM" \
  --out "$FRESH_REPLAY_OUT" --log "$FRESH_EXTERNAL_LOG" --execute
```

All paths must be canonical physical paths. Output/log must not exist and their
parents must exist. The log is outside output, original inputs, source checkout
and model. Original producer paths referenced in P0 configs must remain readable
and unchanged. Same reserved GPU handles both arms with one frozen base load.

The controller checks the explicit single GPU selector/process table and sets
V6_MODEL/offline/spawn before launching a **fresh** worker interpreter. Thus
`model_backend.MODEL` is initialized correctly in the actual worker. It calls
the existing owned-session worker/cleanup boundary with a 3600-second timeout;
the worker also has a one-hour alarm around model load/generation and unwinds
on termination. Main retains responsibility for reservation management.

CPU revalidation after completion:

```bash
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  "$PY" -B -m organism_v6.parent_note_replay_diagnostic \
  --out "$FRESH_REPLAY_OUT" --validate
```

This loads only the local tokenizer, rechecks original/replay data and outputs
the recomputed descriptive result. It does not load model weights for inference.
For direct real API execution, set V6_MODEL before importing the backend; the
documented controller CLI handles this by starting the correctly configured worker.

## Stable API for Pasteur (main to relay)

```python
from organism_v6.parent_note_replay_diagnostic import validate_replay

checked = validate_replay(replay_out)
results = checked["results"]
records = checked["records"]
sources = checked["sources"]
```

Optional `tokenizer=` is for injected CPU fixtures or an already loaded matching
local tokenizer. Default loads the tokenizer locally from the bound model path.
Failures raise; no partial artifact is returned as validated material.

Return shape:

- `results`: fully recomputed, explicitly source-replay descriptive summary.
- `records`: 512 ordered records (lesson256, then sham256), each in original
  selected ACT physical order. Important keys: `arm`, `output_id`, `source_id`,
  `episode_id`, historical `execution_id`, exact `old_text`, exact new `text`,
  `output_sha256`, `tokens`, `output_retokenized_tokens`, and `judgment`.
- `judgment["judge_record"]`: unchanged content judge's full result.
- `judgment["delivered_text_echo"]`: complete coach/teacher text or sentence echo.
- `judgment["faithful"]`: content eligible AND no delivered-text echo, with
  historical source provenance validated by this entry point.
- `sources[arm]`: original root/config/inventory/pins/schedule/teacher and ordered
  `sources` list. Join each record's `source_id` to that list.
- Each source entry contains historical `source_act`, `act_line`, `act_sha256`,
  `old_note_line`, `old_note_sha256`, `old_text`, `old_judgment`, `original_prompt`,
  `original_seed`, `original_rendered_prompt`, `original_prompt_tokens`,
  `note_trace`, `wake_trace`, `replay_prompt`, episode/execution/source IDs.
- Trace bindings name original request/output indices, physical generation-file
  line indices and LF-inclusive raw row hashes. Raw ACT and old-NOTE hashes are
  also LF-inclusive. Original full source files remain authoritative.

For any later first64 writer preparation: keep this order, require `faithful`,
deduplicate with the existing policy normalization, bind exact raw new text/hash
and source ACT in a distinct replay-write map, and independently run existing
tokenizer child-mask preflight. Do not call the old `_formation_snapshot` on these
outputs or invent its expected protocol. This runner makes no training eligibility
certificate or automatic claim that any quantity of replay text should be fitted.

## Bounded behavior

- Validates each original COMPLETE arm and its actual artifact inventory/hashes.
  Rehashes all four recorded frozen producer paths. The historical diagnostic
  may differ from the new consumer, but policy/batch/families bytes must match
  executing equivalents. No original manifest or receipt is rewritten.
- Selects first4 valid MEASURED ACTs per each original schedule, using physical
  ledger order; **requires exactly256 per arm** before backend creation. No
  output/score-value ranking, fallback, retry or extra source substitution.
- Old NOTE content rejection is explicitly independent of provenance: existing
  `_judge_source` must reach the appropriate content/echo verdict rather than
  fail earlier source checks, then `_generation_rejection`, actual trace matching
  and ledger-prefix checks separately validate that old generation.
- New prompt is exactly the stored original prompt with the fixed coach inserted
  immediately before the unchanged `\n\n` plus `outcome_block` suffix. Original
  per-request derived seed, temperature0.7 and max_tokens100 are retained.
- Runs 32 batches of8 per arm,64 batches total: maximum512 new note generations,
  no wake generations, episode drivers, scoring calls or world ACTs.
- Actual local tokenizer checks original rendering/count, logs new rendering,
  original/new token counts, exact rendered delta and standalone coaching tokens.
  Every prompt plus100 output allowance must fit16384; no silent truncation.
- Raw outputs are not stripped, rewritten, prefixed, repaired or replaced. Even
  an invalid-cardinality batch is retained as a raw batch return before failure.
- The original policy judge runs unchanged against historical action facts.
  Full coach/teacher paragraph and sentence echoes are conservatively excluded
  with the existing normalized literal matching mechanism. Teacher bytes remain
  canonical; the original203/158 semantic/dose confound is not removed.
- Revalidation rebuilds the historical source map, retokenizes exact prompts,
  matches every actual request/raw batch return to each record and recomputes
  output hashes, judgments and descriptive totals. It returns source-linked raw
  material, not original formation artifacts or new measurement scores.

## Artifacts

`config.json`, `lesson_sources.json`, `sham_sources.json`,
`token_preflight.json`, `generations.jsonl`, `records.jsonl`,
`results.json` on success, `failure.json` on failure, `artifact_hashes.json`.
Config binds exact coach bytes/hash, source/model pins and implementation hashes.
Full canonical teacher bytes live in each source map. Files/dir are read-only at
termination; existing output/log is rejected. Worker log/process/cleanup evidence
is external under the specified log prefix.

New `output_id` is a deterministic local trace identifier, not an invented engine
request ID. The existing backend exposes only decoded text; engine output IDs and
runtime token IDs are unavailable. Retokenized output counts are labelled as such.
Completed coaching presentation totals are in results; issued requests and raw
partial returns remain independently visible in the trace on failure.

## CPU tests

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 PYTHONPATH=tests:. python3 -B -m unittest \
  test_parent_note_replay_diagnostic -v
```

**12 passed in30.151s.** Log: `/tmp/astra_parent_note_replay_tests.log`.

Broader targeted command:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 PYTHONPATH=tests:. python3 -B -m unittest \
  test_parent_note_replay_diagnostic \
  test_run_reasoning_neutral.NeutralRunnerTests.test_real_cpu_worker_timeout_kills_owned_child \
  test_run_reasoning_neutral.NeutralRunnerTests.test_real_cpu_worker_failure_and_interrupt_are_cleaned \
  test_parent_material_write.ParentMaterialWriteTests.test_identical_producer_relocated_without_rewriting_formation -v
```

**15 passed in33.499s.** Log: `/tmp/astra_parent_note_replay_combined.log`.
CLI help also passes without model load.

Coverage includes actual synthetic original formation/receipt/source joins with
zero eligible old notes; exact fixed first4 selection and same derived seeds;
no new childhood/world calls; canonical suffix;512 actual fake-backend outputs;
teacher/coach sentence echo; unmodified raw prefixes/newlines and default judge;
source and wake corruption; old producer byte identity without pretending new
diagnostic equals old;256 requirement; malformed batch raw retention/no retry;
context preflight/no truncation; resealed record tampering; explicit opt-in;
output conflict; one-hour fresh-worker dispatch; source immutability and CPU
revalidation. Existing worker tests exercise real CPU descendant cleanup.

No actual GPU, native model or real tokenizer inference fixture was run. Synthetic
tokenizers/backends are clearly labelled in tests; no faithful real material is
claimed. An initial sentence-echo regression found line-prefix splitting needed
correction; final tests pass with complete per-line sentences excluded. Existing
bootstrap ResourceWarning remains untouched.

## Remaining limits

No downstream corpus/trainer/probe integration is implemented here (Pasteur owns
future replay-write work). Artifact hashes/read-only modes are ordinary custody,
not adversarial filesystem immutability. Old roots and recorded source files must
remain accessible. Real source prompt length/model/kernel behavior still require
main's deployment preflight. One-hour process timeout is an upper bound, not a
promise about wall time; source validation and prefill may dominate.
