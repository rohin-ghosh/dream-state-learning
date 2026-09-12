# Two-habit runner — EDIT-STOP

Validation cut: 2026-09-12T19:31:45Z. Ready for **Main's seed0/root0 pilot first**.
Do not start roots1/2 until Main reviews the root0 pilot and separately allocates
them. This runner handles one seed only; it never automatically dispatches
another seed. **No launch performed. EDIT-STOP.**

## Owned files / SHA256

| File | SHA256 |
|---|---|
| `/tmp/astra_two_habit_runner_20260912.py` | `d8983514e081be49c931f422143aeeee695498d9dc6547ac14e43d46034a2f60` |
| `/tmp/test_astra_two_habit_runner_20260912.py` | `9bd0ffefb72fd2edc23e60e510f56d544f61d278c776487f228ad2126fcffdd8` |

The third authored file is this handoff. No repository/manuscript/live-helper
edits, Git, network, GPU probes, actual worker launches, generation, or fits.
CPU tests use temporary fixtures; existing module globals remain unchanged.

## Fixed execution contract

- One fresh sealed plan per parent seed0/1/2 and one explicit Main GPU parameter.
  Device, seed, deadline, actual lease end, budget note and logging note are sealed
  in preparation. Run cannot override device/seed/deadline/lease arguments and
  requires both `--allow-gpu` and matching inherited `CUDA_VISIBLE_DEVICES`.
- Sequential arms: `input_before`, then `input_after`. **Both initialize from
  exactly the same original H adapter**, not the first arm's result. No optimizer
  state resumes. Continuation optimizer seed matches the original parent seed.
- Fixed LR1e-4, rank8/alpha16/dropout.05, four epochs, batch4/accumulation1, all
  original projections, no packing, one EOS, max512. Native trainer CLI parsing
  matches the exported recipe. `--overflow truncate` is explicit; **ANY context
  drop, target drop, truncated item or split item fails verification**.
- Each fit must finish80 steps/80 microbatches with finite loss, no skipped rows,
  exactly80 original examples, exact audited token totals and four-epoch token
  presentations. Warm-start provenance must show fresh AdamW, zero initial
  optimizer state, one adapter, frozen base, exact original parent files, matching
  seed,80 parent steps and160 cumulative steps. Existing fading state helpers
  compare original source, initialized and saved parameter inventories.
- Per seed: two fits,160 updates,640 row presentations, **96 new readout calls**,
 48 reused H-baseline calls and6144 output-cap tokens, not token usage. Across all
  three seeds, if later selected by Main: six fits,480 updates,1920 presentations,
 288 new calls and18432 output-cap tokens.

## Symmetric strict scoring — latest watcher requirement included

The existing exporter and old readout are untouched. The runner calls the
exporter's pure sourced scorer, then directly recognizes both orders in the
**unchanged raw response**; it does not reorder lines or repair output.

- `input_before_order`: exactly INPUT→PREDICT→ACT, three nonblank valid numeric
  lines, one of each label, source-correct operands in their displayed order.
- `input_after_order`: the identical requirements for PREDICT→ACT→INPUT.
- `input_before_success` / `input_after_success`: the corresponding strict
  source-correct order **plus correct PREDICT, correct ACT, and PREDICT before ACT**.
- Each arm reports `own_order_success`, `opposite_order_count`,
  `opposite_order_rejected`, and `own_success_and_opposite_rejection`. Opposition
  rejection uses the opposite **order**, not merely whether its answer is right.
- Invalid output can reject both orders. It is **not success**: the combined
  own-success-and-rejection metric and `invalid_for_both_orders` expose this.
- Arithmetic `no_tag_spill` requires exactly the three valid, unique protocol
  lines with no prose/fences/extra tags. Memory reports explicit case-insensitive
  INPUT/PREDICT/ACT tag-spill counts, invalid answers and ordinary memory accuracy.
- The former before-only `joint`, separate form-A/form-B, prediction correctness,
  ACT success and original correct-adherence metrics remain available. **Do not
  use the legacy before-only `joint` as the after arm's primary success metric.**
- No extra reminders or examples enter prompts. Same fixed48dev cases, decode
  temperature0/seed20260912/max64; the remaining64 stay unrequested. Reduction
  requires all48 actual captures before scoring. No missing-output zeros, partial
  panel rescue, output repair, new readout framework, or outcome-dependent tuning.

## Provenance / reused baseline

Seed0 uses original `fit_teach/result.json`; seeds1/2 use their original
`fit_teach/verified.json`. Hardcoded plan/fit/readout-plan SHA256 pins and H capture
manifest/reduction pins were checked against the available local SEQ098/099
capsules for all three seeds. Preparation checks the actual original adapter
tree, source training hash, model files, native inputs, capture completeness,
raw-output token decoding, cleanup, and baseline reduction/raw-text parity.

The reused baseline is **each seed's original H readout**, rescored symmetrically
without modifying its files. It is not a new OFF readout; existing OFF evidence
is not regenerated or rewritten by this controller. Historical readout source
hashes are preserved; new readout plans bind current source hashes while retaining
the exact original cases, requests and native inputs.

Material verification requires the actual `NATIVE_TOKEN_MATCHED_NO_FIT_NO_LAUNCH`
export, current exporter source pins, source/model file pins, exact artifact
membership, both80-row corpora, full inventories/panels and a matching native
token/mask/order audit. No arbitrary padding or dose substitution. Source,
model/tokenizer, parent, baseline and material hashes are rechecked during the
controller. The two new adapters remain distinct and cannot mutate H.

Main reports the actual Qwen exporter PASS on node3 at:
`~/astra_diagnostics/astra_fundamental_two_habit_20260912_attempt1/material`, with
source snapshot label `d1e70002d12052f6b7357d42cf5997aa915e16f7`.
That is **Main's native evidence**; this runner was not native-prepared or
GPU-executed here. Source hashes, not a Git lookup, are authoritative.

## Time / cleanup / no retry

- Outer **1200 seconds per seed**, including run-controller CPU checks, hashing,
  fit/readout gaps and cleanup. The CLI clock starts before argument parsing and
  helper binding. Work alarm fires140 seconds before the effective deadline.
- Effective deadline is the earliest of controller start+1200, Main's sealed
  absolute deadline, and actual lease end minus10 seconds. Existing supervised
  workers retain their600-second upper bound and140-second cleanup reserve,
  further constrained by that effective deadline. No existing globals are changed.
- Offline CPU preparation is separately timed in the plan and is not claimed
  as part of the subsequent GPU reservation. Main's external ledger still owns
  queue/startup/reservation boundaries outside this script.
- Terminal receipt records full controller `reserved_seconds`, summed
  `worker_reserved_seconds`, receipt count/accounting completeness, cleanup and
  deadline status. Worker time cannot exceed full controller time. Missing or
  corrupt worker receipts produce **unknown/null worker total**, not zero.
- Success needs both completed arms, four successful supervised workers, verified
  owned-group and GPU absence, valid timing/accounting, and deadline compliance.
  Failure keeps partial files/results and writes `FAILED_PARTIAL_NO_RETRY`.
  Existing run roots cannot retry or resume. No monetary-rate arithmetic.
- Main must check full vacancy before spawning the controller. The script does
  not certify Main performed that check; existing supervision verifies GPU
  process absence around its own workers.

## Existing pinned helper dependencies

No helper edits. These files must be present on the node (paths are overridable
but bytes are pinned):

| Helper | SHA256 |
|---|---|
| `/tmp/astra_fading_replication_20260912.py` | `bc17821dc352757e7e18c74fddac451faee7b1ebae494b77ed61c4afceacb5e1` |
| `/tmp/astra_fading_sentinel_20260912.py` | `7b0686de7b66fcad27a665c0b30054a893af3ee33d053c26fae903fc1ed8af20` |

Reused mechanisms: original native-input/capture audit, exclusive plan sealing,
fresh-path protection, CPU parameter-state inventory/checking, `base.supervise`,
the existing readout worker/reducer, and the exporter's pure scorer/native audit.

## Completed checks

From the repository/source checkout root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_two_habit_runner_20260912.py
# 32 tests, OK; no skips locally. Stdlib unittest: pytest is not required.

PYTHONDONTWRITEBYTECODE=1 /data/home/rohing/.cache/uv/archive-v0/gQNbv0KfvnaJ_g5l/bin/python -B -m pytest -q -p no:cacheprovider /tmp/test_astra_two_habit_runner_20260912.py tests/test_fundamental_two_habit_corpus.py
# Final bytes: 97 passed, 46 subtests passed in 13.14s; no skips.

PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/astra_two_habit_runner_20260912.py --help
# Exit0; help only, no bind/preparation/launch.
```

The standalone32-test run preceded only the case-insensitive memory tag-spill
flag refinement; the final combined run covers all32 runner tests on final bytes.
One test reads the local archived capsule paths. On a node without those local
archive copies it explicitly skips that single provenance test; the31 fixture
tests require no pytest installation. Actual preparation still requires and
validates the node's real original-parent evidence. No dependency was installed.

Coverage includes all three actual capsule pin sets, all six parsed fit commands,
shared-parent/non-chaining behavior, seeded fresh optimizer, exact native recipe,
source/model/material/parent drift, unchanged H baseline, missing captures,
no-drop validation, state mismatch, both strict orders and opposite rejection,
source operand copies, numerical correctness, memory tag spill, sealed device,
CPU-inclusive deadlines, cleanup/ledger failures and no retry.

## Main's root0 pilot procedure — not executed here

Use Main's existing native environment, with the source checkout installed on
node3 and the two pinned helpers available. Set explicit budget/logging notes
and Unix deadline/lease-end values; no defaults select these for Main.

```bash
PYTHONDONTWRITEBYTECODE=1 "$PYTHON" -B /tmp/astra_two_habit_runner_20260912.py prepare \
  --source-root "$SOURCE_ROOT" --runroot "$FRESH_ROOT0" \
  --materialroot "$HOME/astra_diagnostics/astra_fundamental_two_habit_20260912_attempt1/material" \
  --parentroot "$HOME/astra_diagnostics/astra_fundamental_teaching_20260912_attempt1" \
  --seed 0 --device "$MAIN_GPU" --deadline "$MAIN_DEADLINE" --lease-end "$LEASE_END" \
  --budget-note "$MAIN_BUDGET_NOTE" --logging-note "$MAIN_LOGGING_NOTE"
```

After Main's own checks/allocation, the explicit run interface is:

```bash
CUDA_VISIBLE_DEVICES="$MAIN_GPU" PYTHONDONTWRITEBYTECODE=1 "$PYTHON" -B \
  /tmp/astra_two_habit_runner_20260912.py run --source-root "$SOURCE_ROOT" \
  --runroot "$FRESH_ROOT0" --allow-gpu
```

This is an interface description, **not a launch performed or authorization
issued here**. Inspect `run/terminal.json` and each arm's `two-habit-scores.json`,
existing `readout/reduction.json`, native raw captures and fit/supervision
receipts. Root0 is the first pilot. Main—not an automatic scientific threshold
or a seed-dispatch loop—decides whether to prepare/run roots1/2 afterward.
Their parent roots, if later selected, are the original replication root's
`seed1` and `seed2` directories. Allocate each independently; no hardcoded GPU6/7
or automatic assumption that a released device remains free.

Scientific boundary: compatible authored conventions with rehearsal on a shared
exposed dev panel, not arithmetic improvement, reliable memory, parenting,
child-sleep efficacy, independent-probe replication, H1/H2 or a broader curriculum.

**EDIT-STOP. Main owns source publication, allocation, root0 launch and review.**
