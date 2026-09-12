# Fixed fundamental teaching replications — Main handoff, 2026-09-12

**EDIT-STOP.** Code and CPU tests are complete. This contributor did not launch,
query, cancel, or run GPU work, inspect private model responses, use Git/network,
or change repository/other contributors' files. Main selected seeds 1/2 after
seed0 development; only Main may copy and launch this utility and account for
the original campaign budget. No LR/general sweep support is present.

## Exactly three owned files

- `/tmp/astra_fundamental_replication_20260912.py`
- `/tmp/test_astra_fundamental_replication_20260912.py`
- `/tmp/astra_fundamental_replication_handoff_20260912.md`

The implementation imports the existing native trainer/readout and vacancy and
supervision helpers; it does not implement training, generation, or scoring.
It does not execute/import the old pair script, only checks its bytes.

## Inputs pinned to node3 attempt1

The node3 seed0 plan itself is not accessible on this VM. Its exact digest was
obtained from the local teach/control **launch metadata**, not model results:

```text
seed0 plan: d5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e
pair script: 06d292311e0307b3121593cc2d34bb5c753480eb1537cced1c7fdbff913bd89a
seed0 OFF plan: e275ebf4f27f0a3b35fd87ac983843e9edcf73e1239bd01be60f4952f3845fc8
```

Runtime preparation fails unless the supplied original plan, its seal, old
launcher, model hashes, training source hashes, exported corpora, and original
OFF plan all match those pins. It also checks the current readout dependencies
against the seed0 OFF plan. The source files inspected locally match their
corresponding files in the seed0 `06c90d1b` source archive. Full validation of the
remote plan/material is intentionally deferred to Main's local node3 prepare.
There is no hash override flag, copying/rebasing a model path, or silent fallback.

## Recipe, material, and units

- Both seeds retain the seed0 full native `TrainConfig`, changing only `seed`.
  Explicit settings are LR 0.0003, rank 8, alpha 16, dropout 0.05, four epochs,
  batch size 4, grad accumulation 1, no packing, max length 512; all other native
  defaults must match the sealed seed0 config exactly. Seed0 seed must be 0.
- Native trainer seeds also control LoRA initialization, dropout RNG, and group
  shuffling; this is replication of the existing trainer-seed intervention, not
  a claim that only an optimizer's internal randomness changes.
- `teach.json` and `control.json` are copied **byte-for-byte** from seed0, never
  regenerated. Per-row matched native audits and hashes are retained. Each arm
  has 80 items, 4,517 input / 912 target tokens per corpus, 80 optimizer steps,
  18,068 input tokens seen / 3,648 target tokens seen across four epochs. Control
  label stays `COMPUTED`; no label selection is performed.
- Each native trainer process starts from the same frozen base with a fresh
  adapter output directory. No adapter input, resume path, SVD init, seed0
  adapter copy, or cross-arm adapter reuse is allowed by the generated recipe.
- Readout generation settings/cases stay unchanged: 48 fixed dev cases,
  temperature 0, generation seed 20260912, 64 output-token cap each. The other
  confirmation cases receive no requests. Only teach/control readouts are made;
  no OFF request is generated. OFF is an explicit plan-only same-base reference.
  Main must separately use the already-audited seed0 OFF result; this utility
  deliberately never reads OFF responses/reduction or seed0 model responses.
- No probe-wise independence/significance calculation or output-based selection
  occurs. The replication unit is the paired trainer seed, not each of the 48
  probes. These are two additional seed pairs on the same material/dev set, not
  new independent datasets or confirmation cases. The supplied seed0 all-red
  memory observation does not change the recipe or evidence selection.

## Fixed device mapping

| Seed | Teach | Control |
|---|---|---|
| 1 | GPU 0 | GPU 1 |
| 2 | GPU 2 | GPU 3 |

Fits and their later readouts use this same mapping. `--device` does not exist.
Each launch calls the original `check_free(device)` (GPU processes, own-user
reservations, queue checks) and saves its XML, then delegates to native
supervision. Main should check all four vacancies before the concurrent batch;
the utility rechecks the specific device immediately before each launch.

## Interface and artifacts

```text
prepare --seed0-root PATH --off-root PATH --pair-script PATH --out FRESH_BUNDLE
launch-fit --root BUNDLE/seed1|seed2 --arm teach|control --allow-gpu
verify-fit --root BUNDLE/seed1|seed2 --arm teach|control
prepare-readouts --root BUNDLE/seed1|seed2
launch-readout --root BUNDLE/seed1|seed2 --arm teach|control --allow-gpu
status --root BUNDLE/seed1|seed2
```

- `prepare` is CPU-only, with no tokenizer/model construction. It creates both
  fresh `seed1/` and `seed2/` roots, each with `plan.json`, `plan.sha256.json`,
  unchanged `teach.json` and `control.json`. Only after both complete does it
  write bundle `preparation.json`. A partial bundle is not launchable.
- Each seed plan is the original seed0 plan with only `config.seed` changed,
  plus `replication` metadata: seed/pair, original roots and hashes, the current
  script/dependency hashes, interpreter, fresh-adapter invariant, and OFF binding
  scope. Original model/lease/source/corpus/audit/selection metadata stays intact.
- `launch-fit` is synchronous: it creates `fit_ARM/`, records `gpu.xml` and
  `allocation.json`, invokes one `base.supervise` native trainer, then verifies
  the result. Main may run the four CLI controllers concurrently. Each child
  worker gets its own device from `base.supervise`; the controllers must NOT
  inherit `CUDA_VISIBLE_DEVICES`, or vacancy checks will correctly reject them.
- `verify-fit` checks the worker command/device/timeout and complete cleanup,
  `DONE`, one nonempty adapter weight file, full manifest recipe, 80 steps,
  four epochs, finite final loss, no skipped/nonfinite/split/truncated data,
  token counts, and saved LoRA settings. It writes `fit_ARM/verified.json` once.
  Reverification is read-only after that seal and rejects changed adapter files.
  It does not print/select based on training losses.
- `prepare-readouts` requires both sealed fits of that seed. It invokes the
  existing native **CPU tokenizer** preparation for `readouts/teach` and
  `readouts/control` and writes `readout_preparation.json` only after both pass.
- `launch-readout` revalidates source/corpus/fit/plan links, checks vacancy, saves
  `readouts/ARM/launch/{gpu.xml,allocation.json}`, then calls `readout.run` once.
  It does not itself reduce/read model responses. Main runs the native reducer.
- `status` reads plans/fit verification/supervision metadata, not readout text
  or scores. `SUPERVISED_COMPLETE_NATIVE_REDUCTION_REQUIRED` is not a scientific
  result or a successful native token audit. Incomplete/failed evidence reports
  `NOT_TERMINALLY_VERIFIED_DO_NOT_RELAUNCH`; it does not guess a live PID or cancel.
- Existing or partial output/stage paths are terminal for relaunch. No deletion,
  overwrite, auto-resume, retry, cleanup of other jobs, or launcher daemon exists.
  Failed readout preparation cannot resume within that partially populated seed
  root through this utility; Main must preserve and explicitly resolve artifacts.

## Bounds and campaign budget — Main owns the global check

The original campaign remains **90 aggregate A40-minutes = 5,400 GPU-seconds**.
Main reported approximately 476 seconds already spent, leaving approximately
4,924 seconds before subsequent work. Concurrent time is summed over GPUs, not
counted once as wall time. The nominal four-fit/four-readout forecast at about
two minutes each is 960 additional aggregate seconds; this is a forecast only.

Native supervision caps each worker at **600 seconds**, possibly shortened for
lease/reservation headroom, with existing cleanup reserves and verified release.
The inherited original lease is not extended; launch requires >1,800 seconds
remaining. Base supervision also applies its existing per-root 1,800-second
accounting; it is **not** a cross-seed campaign ledger. Readouts have their own
native roots. Even 8 x 600 + prior 476 = 5,276 seconds excludes cleanup, so the
worker ceilings alone do not prove that the 5,400-second campaign cap is safe.

Main must check residual budget before the four-fit batch and again before any
readout batch or later diagnostic, allowing for actual cleanup/reserved time.
Sum each distinct `supervision.json`'s `reserved_seconds` once; do not double-count
verified receipts. This utility does not adjust budgets, preapprove future work,
launch an unrequested diagnostic, or cancel jobs to manage a global budget.

## Exact node3 commands — for Main only, NOT executed here

Use the already-pinned readout source snapshot that also contains the unchanged
trainer. Copy the three owned files before preparing; modifying the script or
switching interpreter/source after preparation invalidates its pins.

```bash
PY=/localhome/local-rohing/v2/venv/bin/python
SOURCE=/localhome/local-rohing/astra_sources/a9a7c67919b5f5ec8b121a463f2ea49a5c967757
SCRIPT=/tmp/astra_fundamental_replication_20260912.py
SEED0=/localhome/local-rohing/astra_diagnostics/astra_fundamental_teaching_20260912_attempt1
BUNDLE=/localhome/local-rohing/astra_diagnostics/astra_fundamental_replications_20260912_attempt1
export PYTHONPATH="$SOURCE" PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1
unset CUDA_VISIBLE_DEVICES

"$PY" -B /tmp/test_astra_fundamental_replication_20260912.py
"$PY" -B "$SCRIPT" prepare --seed0-root "$SEED0" --off-root "$SEED0/readouts/OFF" \
  --pair-script /tmp/astra_fundamental_pair_20260912.py --out "$BUNDLE"
```

After Main's residual-budget decision and full vacancy reconciliation:

```bash
"$PY" -B -c 'from gpu.astra_mini_sudoku_diagnostic import check_free; [print(device, check_free(device)[0]) for device in ("0", "1", "2", "3")]'

"$PY" -B "$SCRIPT" launch-fit --root "$BUNDLE/seed1" --arm teach --allow-gpu & seed1_teach=$!
"$PY" -B "$SCRIPT" launch-fit --root "$BUNDLE/seed1" --arm control --allow-gpu & seed1_control=$!
"$PY" -B "$SCRIPT" launch-fit --root "$BUNDLE/seed2" --arm teach --allow-gpu & seed2_teach=$!
"$PY" -B "$SCRIPT" launch-fit --root "$BUNDLE/seed2" --arm control --allow-gpu & seed2_control=$!
fit_failed=0
for controller in "$seed1_teach" "$seed1_control" "$seed2_teach" "$seed2_control"; do
  wait "$controller" || fit_failed=1
done
test "$fit_failed" -eq 0
```

Keep Main's controlling session alive. Treat any failed wait or unverified
release as a hard stop, not permission to repeat a launch. CPU verification and
native tokenizer preparation after the fits:

```bash
for seed in 1 2; do
  "$PY" -B "$SCRIPT" verify-fit --root "$BUNDLE/seed$seed" --arm teach
  "$PY" -B "$SCRIPT" verify-fit --root "$BUNDLE/seed$seed" --arm control
  "$PY" -B "$SCRIPT" status --root "$BUNDLE/seed$seed"
  "$PY" -B "$SCRIPT" prepare-readouts --root "$BUNDLE/seed$seed"
done
```

Only after Main checks the remaining aggregate budget and full vacancy again,
launch each desired arm with this exact interface (sequential example; Main can
background/wait all four using the same pattern as fits):

```bash
"$PY" -B "$SCRIPT" launch-readout --root "$BUNDLE/seed1" --arm teach --allow-gpu
"$PY" -B "$SCRIPT" launch-readout --root "$BUNDLE/seed1" --arm control --allow-gpu
"$PY" -B "$SCRIPT" launch-readout --root "$BUNDLE/seed2" --arm teach --allow-gpu
"$PY" -B "$SCRIPT" launch-readout --root "$BUNDLE/seed2" --arm control --allow-gpu

for seed in 1 2; do
  for arm in teach control; do
    "$PY" -B -m organism_v6.fundamental_teaching_readout reduce \
      --root "$BUNDLE/seed$seed/readouts/$arm"
  done
done
```

Native reduction independently requires all 48 raw responses, actual input and
output token audits, source/identity pins, and complete cleanup. Missing evidence
is not a zero. No new OFF reduction is needed from this utility; reuse Main's
existing independently audited seed0 OFF result explicitly.

## Local validation and limitations

Executed locally:

```bash
PYTHONPATH=/data/home/rohing/dream-state PYTHONDONTWRITEBYTECODE=1 \
  python3 -B /tmp/test_astra_fundamental_replication_20260912.py
PYTHONPATH=/data/home/rohing/dream-state PYTHONDONTWRITEBYTECODE=1 \
  python3 -B /tmp/astra_fundamental_replication_20260912.py --help
```

**20 CPU tests pass.** Tests cover exact plan transformation, both seed roots,
byte equality, source/model/corpus/OFF drift, fixed recipe/tokens/cases, four
distinct adapter destinations, four-GPU mapping, effective native CLI config,
explicit opt-in, mocked one-shot supervision/vacancy, failure preservation,
fit seals, two-arm-only readouts, partial-state refusal, and lease limits.
Native tokenizer preparation in tests uses an explicit CPU fixture; GPU helpers,
supervisors, and readout execution are guarded/mocked. Real original plan/model/
tokenizer and remote execution have not been tested by this contributor.

There is no aggregate scheduler, campaign policy framework, automatic rerun,
adaptive seed/LR choice, added evaluation case, confirmation readout, statistical
test, or outcome-dependent arm alteration. Main owns interpretation, budget,
remote source compatibility, OFF reuse, launch decisions, and any later diagnostic.

**EDIT-STOP — ready for Main; no launch authority exercised.**
