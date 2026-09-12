# Fresh behavioral reread — EDIT-STOP, 2026-09-12

Implemented only `organism_v6/fresh_behavior_panel.py` and
`tests/test_fresh_behavior_panel.py` in the shared checkout via apply_patch.
Historical runner, reducer, constants and other agents' files were not edited.
No commit, native panel generation, remote check, GPU query or launch performed.
Main owns the next commit/native preparation. No approval framework was added.

## Implementation and tests

- `prepare`: fixed 1900070–1900099 candidate order, first 16 accepted; excludes
  all 32 training + 16 old-canary solution/puzzle arrays, prior-exposure IDs and
  within-panel duplicate solutions. Regenerates old entries for identity checks;
  independently checks unique 4x4 completion and native reference acceptance.
- Shortage preserves candidate audit + failure and produces no executable specs.
  Malformed/nonunique generator output fails preparation instead of being rerolled.
- Actual six adapter weight pins, entire original adapter/model/tokenizer
  inventories, historical material hashes and probe-source snapshots are checked.
  Native reasoning_gym 0.1.25 + exact generator hash and vLLM 0.27.1 required.
  Dependency hashes/versions are recorded, not claimed as historical authentication.
- Native first prompts and tokenizer IDs are hashed. Native canonical post-outcome
  prompt is token-checked, with additional action/wrapper allowance. This is not
  a proof for every possible sampled action; actual first prompt bytes/seeds,
  backend identity and generation caps are checked during reduction.
- Six paired OFF/ON specs, no fits. Useful then corrupt within each seed;
  seeds may run concurrently on three independently reserved compatible GPUs.
- `reduce`: requires all twelve completed/custodied conditions and cleanup;
  reuses historical first-ACT functions, not old panel constants. Missing/invalid/
  unmeasured first ACT is zero, later ACT cannot rescue; missing artifact/run fails.
  Reports paired gains per seed, direct ON contrasts, secondary means/action
  counts, OFF-vector agreement and explicit exploratory/overtuning/optimizer-seed
  versus independent-data limitations. No general G2/clean-lineage qualification.

Final CPU command, from checkout root:
```bash
PYTHONPATH="$PWD/tests:$PWD" python3 -B -m unittest \
  tests.test_fresh_behavior_panel tests.test_mini_sudoku_behavior_analysis \
  tests.test_run_reasoning_neutral tests.test_neutral_pair_custody -q
```
**93 tests passed, 6.962 seconds**, including 17 new helper tests. All fixtures
synthetic; no native candidates/model were generated. Earlier wider invocation
without `tests` on PYTHONPATH had import errors; corrected invocation passes.
CLI `--help` also passed. No whitespace errors found by diff check; the two
new files are untracked pending Main's commit.

Helper SHA256: `e2cb9924a9470eb03321ee5a6dca026bfd720ab87e8cdc7ef13fa160808974cb`.
Tests SHA256: `50a81e5eef0ce6e788e8e9b498bdc6aafdbc9efac14c7e85ed1d119432bf8a16`.

## Exact future commands — Main only, not executed

Use Main's committed/deployed source containing the helper, **not the old
source directory that lacks it**. `MAIN_SOURCE_ROOT` is the one intentionally
unresolved value until Main commits/deploys. Old actual adapter roots and model
are defaults embedded in the helper and are not recreated.

```bash
SOURCE="${MAIN_SOURCE_ROOT:?Set committed deployed node3 source directory}"
PYTHON=/localhome/local-rohing/v2/venv/bin/python
FRESH=/localhome/local-rohing/astra_diagnostics/astra_fresh_behavior_panel_20260912_attempt1
env -C "$SOURCE" CUDA_VISIBLE_DEVICES= PYTHONPATH="$SOURCE" \
  PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  "$PYTHON" -B -m organism_v6.fresh_behavior_panel prepare \
  --source-root "$SOURCE" --out-new "$FRESH"
```

If Main has additional known-exposed IDs, append
`--prior-exposure-json /absolute/path/to/frozen_ids.json` (a JSON string list)
**before generation**. Historical exclusions are automatic. Never reuse an
existing root, even after failure. Freeze `manifest.json` and six spec digests
before GPU. Stop for pin/source drift or fewer than 16 accepted items; no refit,
range expansion, automatic retry, or silent source modification.

Define this function in each Main-owned worker shell after setting SOURCE,
PYTHON and FRESH as above. It uses the unchanged runner, never `--condition`:

```bash
probe_seed() (
  set -eu
  SEED="$1"
  DEVICE="$2"
  case "$SEED" in 0|1|2) ;; *) exit 2 ;; esac
  for ARM in useful corrupt; do
    SPEC="$FRESH/specs/seed${SEED}_${ARM}.json"
    SPEC_SHA256=$(cat "$SPEC.sha256")
    env -C "$SOURCE" CUDA_VISIBLE_DEVICES="$DEVICE" PYTHONPATH="$SOURCE" \
      PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 VLLM_WORKER_MULTIPROC_METHOD=spawn \
      HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
      "$PYTHON" -B -m organism_v6.run_reasoning_neutral \
      --spec "$SPEC" --spec-sha256 "$SPEC_SHA256" --allow-gpu
  done
)
```

Main may run these three calls **in separate shells concurrently**, only with
three distinct separately reserved GPUs, or run them sequentially. No device
is assigned by this handoff and RuleGame's reservation is not touched:

```bash
probe_seed 0 "${GPU_SEED0:?Main-reserved device for seed0}"
probe_seed 1 "${GPU_SEED1:?Main-reserved device for seed1}"
probe_seed 2 "${GPU_SEED2:?Main-reserved device for seed2}"
```

Each pair owns its fresh processes and cleanup. A failing useful pair prevents
that shell's corrupt pair; preserve artifacts and let Main reconcile rather
than rerunning or killing unrelated processes. Completed weak/negative scores
do not stop the prescribed comparison.

After all six pairs complete, reduce on the prepared host with the same pinned
generator/dependencies still available:

```bash
env -C "$SOURCE" CUDA_VISIBLE_DEVICES= PYTHONPATH="$SOURCE" \
  PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
  "$PYTHON" -B -m organism_v6.fresh_behavior_panel reduce \
  --prepared-root "$FRESH" --output-new "$FRESH/first_act_report.json"
```

Budget unchanged: 6 OFF + 6 ON = 192 episode cells on 16 shared puzzles;
~96,000 output-token reservation if one ACT each, total configured ceiling
460,800, 900 seconds per condition. Prior estimate 35–50 aggregate A40-minutes
(parallel execution reduces wall time, not aggregate device cost). No new
rank/dose training, leases or claim confirmation authorized by this helper.

**EDIT-STOP. Main reviews/commits, then runs native preparation.**
