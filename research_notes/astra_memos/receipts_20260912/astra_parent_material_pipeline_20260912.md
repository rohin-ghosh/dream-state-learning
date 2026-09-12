# Parented material write/probe pipeline — frozen handoff

2026-09-12 09:10 UTC. Bounded exploratory implementation; no substrate qualification,
clean ancestry/admission, official-base authentication, or H1 success claim.
Main owns Git, GPU reservations, deployment and actual execution. No Git,
network, remote or GPU actions were performed by this worker.

## Owned files — ready for main validation

- `organism_v6/parent_material_pipeline.py`
  SHA256 `c084f774e212b401ed662547e585f5f41fd8247b247d25a4f7a73dc714e08071`
- `tests/test_parent_material_pipeline.py`
  SHA256 `4ca992c300fa05fc210b93cd501d43fa588f5429158d3635a7a038748f2015b1`
- This report. No existing source/test/helper files edited.

Source/tests are frozen; no further edits planned absent a new assignment.

## Actual execution route

1. Explicit `prepare` reads both **completed** formation directories, verifies
   lesson/sham roles and shared model pins/schedule using the existing writer
   helper. It does not wait for or poll active formations.
2. Calls the real `prepare_write` independently for both arms. Both must have
   READY / exactly 64 selected records. Otherwise records
   `PAIRED_SKIP_INSUFFICIENT_MATERIAL`: neither fit nor probe runs, even if the
   other arm was READY. No threshold lowering, substitution or retry.
3. Records the panel and limits prospectively, plus original producer/preparation
   source binding. Prepared writer commands remain unchanged.
4. Explicit `execute --allow-gpu` runs the real standalone trainer via
   `subprocess.Popen(argv, shell=False, start_new_session=True)` once per arm.
   It is not a simulated training path: the production default invokes
   `python -B -m organism_v6.train_adapter` with the actual prepared corpus.
   Rank 8, epochs 3, LR 1e-4, seed 6102; all four optional gate/lineage arguments
   are omitted. 64 examples / 48 steps; differing actual child-token budgets
   remain visible in `train_meta.json` and aggregation.
5. Requires actual DONE, no EMPTY_CORPUS, every `metadata_equals` value, finite
   final loss, adapter config and nonempty adapter weights; records actual
   hashes of every adapter-directory file. Rechecks these after probing.
6. Calls existing `run_reasoning_neutral.run_pair` **in the pipeline process**
   with the per-arm environment, not as a subprocess controller whose separately
   sessioned workers would escape an outer process-group timeout. The existing
   runner launches each actual ON/OFF condition in its own fresh subprocess,
   invokes the existing evaluator, closes its backend and cleans its owned group.
7. Revalidates original receipts and actual result/manifest artifacts through
   existing custody helpers, then aggregates metadata and the four actual probe
   results. No H1 test, success cutoff, parenting-effect estimate or admission.

Execution is sequential: lesson fit, sham fit, lesson OFF/ON, sham OFF/ON.
The two explicitly supplied device selectors may be the same reserved device;
no concurrent use occurs. Caller owns initial reservation and later release.

## Tiny parent-removal panel

First two IDs in ledger order for each of the two configured gate families:

- `rg/n_queens/2000001`, `rg/n_queens/2000002`
- `rg/tower_of_hanoi/2000001`, `rg/tower_of_hanoi/2000002`

Rejects overlap with the actual configured canary set. Both arms and both
conditions use seed 6103, scratchpad seed-salt 6103, 3 ticks, wake cap 400,
scratchpad cap 100, total generation-reservation budget 20000, max 4 episodes,
max model length 16384. Panel is explicitly exploratory, not declared unused.

Training text is only the existing helper's source-joined child-only corpus
with unchanged Situation wrapper. Parent lesson/sham deliveries and raw
formation ledgers are **not passed** to the trainer or probe as text.
The neutral evaluator gets only model/adapter, the fixed panel and fixed
budgets; its existing parent-free birth prompt and non-retrieving ledger apply.
Original pair root plus preparation/adapter roots are protected against output
overlap. The existing API's `lineage_roots` argument is used for path exclusion
only (pair/source directories); this does not create a lineage artifact/claim.

## Main commands (examples, NOT executed)

Use the final deployed source checkout and its desired Python interpreter for
**both** preparation and execution. Supply canonical physical paths. PIPELINE_OUT
must be fresh, outside PAIR_ROOT, model and source checkout, with existing parent.

```bash
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  "$PY" -B -m organism_v6.parent_material_pipeline prepare \
  --pair-root "$PAIR_ROOT" --lesson-out "$LESSON_FORMATION" \
  --sham-out "$SHAM_FORMATION" --out "$PIPELINE_OUT" \
  --lesson-device "$LESSON_GPU" --sham-device "$SHAM_GPU"

HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  "$PY" -B -m organism_v6.parent_material_pipeline execute \
  --out "$PIPELINE_OUT" --allow-gpu
```

Preparation can be run only after both COMPLETE formation outputs exist;
it deliberately fails on active/incomplete roots. Do not reuse partial roots.
No polling/daemon is built in. If prepared status is paired skip, `execute`
returns that skip without launching anything.

Files include immutable preparation directories, `pipeline.json`, the
prospective digest, `EXECUTION_STARTED.json`, external exclusive
`logs/{lesson,sham}_train.log`, per-process/cleanup records, actual adapters,
per-arm TRAIN_DONE observations, prechosen probe specs, neutral outputs under
`probes/{lesson,sham}/{off,on}`, and `results.json` only after complete validation.
Failures retain raw files and `PARTIAL.json` (or PREPARATION_FAILED); no retry or
overwrite. Partial metadata is labelled incomplete, never successful results.

## Lifecycle and ordinary hygiene

- Trainer timeout: 600 seconds each. Neutral worker timeout: existing 3600
  seconds each. Four sequential neutral workers; nominal maximum subprocess
  budgets sum to 15600 seconds (4h20m), plus hashing/cleanup overhead. Main owns
  any overall caller timeout. There is no whole-run GPU daemon or scheduler.
- Before each fit and around probe pairs, an actual all-process nvidia-smi XML
  query must report absence. Failed/empty/malformed queries are not availability;
  memory=0 is never consulted. The existing neutral runner checks between workers.
- Training cleanup kills/verifies only its new owned process group in finally.
  The existing neutral runner owns its fresh workers' cleanup. SIGTERM is
  translated into an exception to unwind those finally blocks; SIGINT also
  unwinds normally. SIGKILL/host loss cannot offer in-process cleanup guarantees.
- A failed stage cannot launch its next stage. Cleanup uncertainty is reported
  as reservation retained; the pipeline does not claim a successful release.
- Explicit V6_MODEL, single CUDA selector, trusted cwd/PYTHONPATH, no user site,
  spawn and offline env. Python-home/preload overrides and unrelated inherited
  environment are excluded. API execution is intended for the main thread/CLI,
  not simultaneous calls mutating process environment.
- Existing snapshot/custody checks are reused, not extended into C11.

## Relocation regression

The test creates a fresh source-only checkout (copy equivalent to source archive;
no Git command), retaining original completed formations at their old producer
paths. A separate CPU interpreter imports the new checkout, prepares from those
original formations via the existing relocation-aware helper, then exercises
actual neutral run_pair/run_probe/custody validation with synthetic backends.
Original formation manifest hashes are unchanged. Snapshot source root/bootstrap
and actual evaluator code paths all match the new checkout.

Preparing in one checkout then moving already-prepared pipeline state to a
different checkout is intentionally unsupported. Deploy first, then prepare;
original producer paths must remain readable and byte-identical.

## CPU validation

Focused command:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 PYTHONPATH=tests:. python3 -B -m unittest \
  test_parent_material_pipeline -v
```

**15 passed in 30.249s**. Log: `/tmp/astra_parent_material_pipeline_tests.log`.

Broader command:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 PYTHONPATH=tests:. python3 -B -m unittest \
  test_parent_material_pipeline test_parent_material_write \
  test_run_reasoning_neutral test_neutral_pair_custody -v
```

**93 passed in 46.606s**. Log: `/tmp/astra_parent_material_pipeline_combined.log`.
CLI `--help` also passed without model/GPU load.

Coverage: actual formation/summarizer/writer and evaluator/custody integration;
fresh checkout with old producers; fixed shell-free commands/environment;
paired skip; malformed metadata/nonfinite loss/missing weights; failed GPU
query/release; missing probe output; prior-arm adapter mutation; input drift;
output/log conflicts; explicit execution; real CPU timeout killing owned
descendants while leaving an unrelated process alive. Broader tests include
the neutral wrapper's real CPU failure/interrupt/descendant cleanup fixtures.

## Remaining limits, not hidden qualifications

- No real tokenizer model load, training, inference, GPU query or GPU execution
  was performed by this worker. Positive model/tokenizer/process fixtures are
  explicitly synthetic CPU doubles; real helper/evaluator logic executes.
- Actual run must still meet READY64/tokenization and real train metadata checks.
- Main's exploratory-write decision is not writer/substrate qualification; the
  output deliberately makes neither that claim nor an H1 conclusion.
- Local bytes establish identity only; official base provenance remains unresolved.
- Existing unrelated bootstrap ResourceWarning remains unchanged.
