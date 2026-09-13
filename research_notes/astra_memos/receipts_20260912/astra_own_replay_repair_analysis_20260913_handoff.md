# Own-source replay repair reducer — pre-outcome freeze

September 13, 2026. CPU synthetic fixtures only. No outcome retrieval, root
discovery, model/tokenizer/tensor loading, native commands, collection, network,
Git, or repository edits. Main owns native receipt confirmation and reveal.

## Owned files and validation

- `/tmp/astra_own_replay_repair_analysis_20260913.py`
  SHA256 `ba039742485f8292e7caf9d728f0b5c9b1c3a0ca03a52ff39b8d4b14814a84cb`
- `/tmp/test_astra_own_replay_repair_analysis_20260913.py`
  SHA256 `0f626a1aa9806b7ef1b14fd33687a7d486f95f472ade99b231a5f7ed25a31eff`
- This new handoff; all earlier cores/runners/protocols/artifacts unchanged.

Final fixture suite: **14 tests PASS, 3.031 seconds**. CLI `--help` passes.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp python3 -m unittest -v test_astra_own_replay_repair_analysis_20260913
```

Tests cover complete three-pair 480-call/1632-update/six-fit accounting;
304/256/256 steps per arm; unequal memory exposure; r=0 retained as unavailable;
missing/duplicate seeds, stages, panels and LR0; exact native prefix/route/raw
joins; NaN/bool/unchanged tensor rejection; raw scorer disagreement; source
producer/raw rewrite and dose mismatches; itemwise losses not offset by gains;
8/7/5 floors; constant diagnostic recomputation; pin/JSON/write-once rejection.
The audited/cached memory scorer is checked against the frozen public
`score_readback` API on exact/paraphrase, valid/malformed/fenced/UTF-8 responses.
Synthetic capture hashes are patched only in the tests' private utilities
module; the production CLI retains the original pinned capture identities.

## Frozen API and exact manifest shape

Input schema: `astra_own_replay_repair_analysis_20260913_v1_inputs`.
Output schema: `astra_own_replay_repair_analysis_20260913_v1`.

`load_apis(module_dir, source_root, protocol_path)` loads pinned CPU scorers and
AST-extracts only `check_fit`/`validate_response`, not lifecycle implementations.
`load_bundle(entry)` reads one explicitly named complete local mirror and pinned
report pair. `reduce_seed(bundle, apis)` and `reduce_cohort(bundles, apis)` return
plain JSON-compatible dictionaries. CLI has no scorer/mock bypass switches.
`run(manifest_path, manifest_sha256, out, module_dir, source_root, protocol_path)`
reduces all three seeds, then creates fresh `analysis.json` and `analysis.md`;
returns both hashes. Existing output is rejected, including on retry.

Exact structure below is a **template**, not an actual evidence manifest; expand
the seed entry three times with unique integer seed 0/1/2 and Main-supplied pins.

```json
{
  "schema": "astra_own_replay_repair_analysis_20260913_v1_inputs",
  "seeds": [
    {
      "seed": 0,
      "root": "/absolute/local/complete/seed0_root",
      "plan_sha256": "REPLACE_WITH_FULL_PLAN_SHA256",
      "completion_sha256": "REPLACE_WITH_FULL_COMPLETION_SHA256",
      "scores": {
        "path": "/absolute/local/seed0_collected/scores.json",
        "sha256": "REPLACE_WITH_FULL_SCORES_SHA256"
      },
      "collection": {
        "path": "/absolute/local/seed0_collected/collection.json",
        "sha256": "REPLACE_WITH_FULL_COLLECTION_SHA256"
      }
    }
  ]
}
```

Use local mirror root in the manifest; **do not rewrite native paths inside
preserved plan/request/route/history JSON**. The reducer resolves relative
`plan.input_hashes`, `plan.snapshot_hashes`, and completion stage inventory
against only that explicit mirror. It never follows native absolute root,
adapter, model, or historical paths. Preserve the complete copied snapshots:
`memory/*`, `memory_history/*`, `lower_history/*`, `capture/*`, `sources/*`,
`spec.json`, plus mixture/calls/training JSON and all stage JSON receipts.
Keep historical HIGH/LR0 and LOWER scores already snapshotted by the runner;
do not substitute later descendants or reread a live source root.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /tmp/astra_own_replay_repair_analysis_20260913.py \
  --manifest /tmp/MAIN_SUPPLIED_INPUT_MANIFEST.json \
  --manifest-sha256 FULL_MANIFEST_SHA256 \
  --source-root /tmp/astra_level1_real_record_source_20260913_attempt1 \
  --protocol-path /data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_OWN_SOURCE_REPLAY_REPAIR_2026-09-13.md \
  --module-dir /tmp \
  --out /tmp/MAIN_CHOSEN_FRESH_REDUCTION_DIRECTORY
```

## CPU dependencies and evidence boundaries

Module directory must contain every `PINS` entry in the reducer, unchanged:
repair runner/core; actual-memory projector; v2 formation core; original
formation runtime (AST validator only); perception/reflection material;
original memory analyzer (typed validation/pairing utilities); own-source replay
core (CPU source inventory only, never its archive/build/native path).
Their full source pins are embedded. Frozen source root supplies the original
rulegame, parser, birth corpus and reflection definitions, checked by those
modules. Protocol pin:
`fb523ee6d96ef6186ae187c3c9b4482b25084fa49f292aae15a34affa87103c7`.

The formation source is audited/projected once per seed; unchanged production
record scoring is rerun for each memory result and each constant candidate.
Retention is rerun with the original pinned `score_row`, memoized only for
identical row/raw/finish tuples on the same rebuilt material. All stored scores
must agree exactly. Own observation replay is independently joined to the
fixed supported24 TRAIN selection and rescored by the original source judge;
both admitted and rejected raw responses are preserved and checked. Mixed
material cycling, unchanged targets, encoded masks/spans and per-kind costs
are independently reduced; no tokenizer roundtrip is claimed.

Archived native readout requests/responses are hash-joined to completion and
cell receipts, including literal messages, prompt IDs, route, finish and token
costs. Recorded fit manifests/tensor inventories/norms must show finite changes
and identical historical original initialization; no tensor payload is read or
recomputed. Main remains responsible for external receipt/claim/archive custody
and GPU release verification; this is not a new native replay or formal guard.

## Output interpretation

Per seed/arm: exact and paraphrase eligibility/content/strict/exact-target-byte
totals, held/canary content and strict totals, format/error breakdowns; per-item
REPLAY-minus-EXTRA_MEMORY and historical LOWER/HIGH/LR0 paired categories;
itemwise LR0-correct regressions; source row counts, per-kind token/presentation
dose, fits/norms/timing, generation costs and evaluator-only constant table.
Historical references explicitly remain noncontemporaneous with zero new cost.

Screen is exact eligible >=8/14,7/8,5/8 respectively **and zero losses on every
LR0-correct held/canary item**. Gains never offset losses. `r=0` remains
`REPLAY_UNAVAILABLE`, no fresh arm/screen/constant, and makes the all-three-pair
availability flag false; it is neither dropped nor counted as passing.
EXTRA_MEMORY matches steps, not memory exposure/tokens. Three learner pairs,
not independent presentations/episodes. No outcome-based selection, automatic
promotion, statistical equivalence, fresh confirmation, parenting or H1/H2 claim.

EDITSTOP
