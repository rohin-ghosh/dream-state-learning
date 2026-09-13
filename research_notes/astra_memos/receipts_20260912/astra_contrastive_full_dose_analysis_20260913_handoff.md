# EDITSTOP — independent full-dose collected-output reducer

September 13, 2026. CPU implementation/fixtures only. Main has not supplied
completed outcomes to this sidecar; none were discovered, fetched or reduced.
No repository edits, launch, native/GPU/model/tokenizer/network/Git operations.

## Final owned files

- `/tmp/astra_contrastive_full_dose_analysis_20260913.py`
  SHA256 `ce020de47700c97b6208dbe2afea21f182ec85820b62b5f0aa5ea4208ca030f3`
- `/tmp/test_astra_contrastive_full_dose_analysis_20260913.py`
  SHA256 `d6cfbdfc68260c71bd8e7b2aa2254ddd2f6badee6242be22717dbe564d487e81`
- This handoff; its SHA256 is reported separately.

Frozen v2 runner was read only and remains
`ddd36b16e188a2c2bfa11e61e8fbed66fed67d93f81b1d4fa6384c04dd43c025`.
Original material, source files, runner and tests were not edited.

## Stable CLI / input contract

After Main has completed, once-collected and locally mirrored ALL THREE pairs:

```sh
timeout 180s python3 -B /tmp/astra_contrastive_full_dose_analysis_20260913.py \
  --manifest "$MANIFEST" --manifest-sha256 "$MANIFEST_SHA" \
  --out /tmp/astra_contrastive_full_dose_analysis_20260913_results.json
```

The example was NOT run on real outcomes. The CLI reads only explicit inputs
and writes one fresh `/tmp` JSON file exclusively; existing outputs, capture-root
outputs and paths resolving outside `/tmp` are rejected. The 180s outer timeout
is an invocation bound, not a claim of native throughput or an internal deadline.
No native preparation/collection command is invoked. No automatic retry.

Python API: `reduce_manifest(path, sha256) -> report`, with pure
`summarize(dataset, responses, material, corpus)` and `training_costs(prepared)`.
Exactly seeds0/1/2 are required; missing or duplicate seeds/roots are rejected,
not silently omitted or scored as zero. A missing arm/stage/row is a custody
failure. Validly captured length/error completions remain scoring failures.

Manifest has exactly these keys:

```json
{
  "runner": {"path": "/tmp/astra_contrastive_full_dose_run_20260913_v2.py", "sha256": "ddd36b16e188a2c2bfa11e61e8fbed66fed67d93f81b1d4fa6384c04dd43c025"},
  "protocol": {"path": "ABSOLUTE_LOCAL_PROTOCOL_COPY", "sha256": "e777b5be15e2a1cab447de3e72fb013bfac2a20a3d12d81574f95880ca60b0e6"},
  "material": {"path": "/tmp/astra_contrastive_perception_material_20260913.py", "sha256": "b3c7fa549fdade0866da51131f64fe067ad7cd3ce36187f67e4c56ac7fbe5c1d"},
  "public": {"path": "/tmp/astra_birth_skill_probe_run_20260913.py", "sha256": "59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c"},
  "source": "/tmp/astra_contrastive_source_20260913_attempt1",
  "source_files": {"COPY_EXACT_FOUR_FILE_MAP_FROM_PLAN": "REPLACE_THIS_PLACEHOLDER"},
  "historical_archive": {"path": "ABSOLUTE_LOCAL_ORIGINAL_ARCHIVE", "sha256": "c12c3ff8e7cd0a9261aa5118d85f5a93d5318245afd05d0d4ff3cacc96401f7d"},
  "pairs": [
    {"seed": 0, "root": "ABSOLUTE_LOCAL_COMPLETE_CAPTURE0", "plan_sha256": "MAIN_PIN0", "completion_sha256": "MAIN_COMPLETION0", "collection": {"path": "ABSOLUTE_COLLECTION0_JSON", "sha256": "MAIN_COLLECTION0"}, "scores": {"path": "ABSOLUTE_SCORES0_JSON", "sha256": "MAIN_SCORES0"}},
    {"seed": 1, "root": "ABSOLUTE_LOCAL_COMPLETE_CAPTURE1", "plan_sha256": "MAIN_PIN1", "completion_sha256": "MAIN_COMPLETION1", "collection": {"path": "ABSOLUTE_COLLECTION1_JSON", "sha256": "MAIN_COLLECTION1"}, "scores": {"path": "ABSOLUTE_SCORES1_JSON", "sha256": "MAIN_SCORES1"}},
    {"seed": 2, "root": "ABSOLUTE_LOCAL_COMPLETE_CAPTURE2", "plan_sha256": "MAIN_PIN2", "completion_sha256": "MAIN_COMPLETION2", "collection": {"path": "ABSOLUTE_COLLECTION2_JSON", "sha256": "MAIN_COLLECTION2"}, "scores": {"path": "ABSOLUTE_SCORES2_JSON", "sha256": "MAIN_SCORES2"}}
  ]
}
```

Replace placeholders; all file bindings are exactly `{path,sha256}` and paths
absolute. Manifest bytes are SHA-bound, with duplicate/nonfinite JSON rejected.
Do not change native capture bytes to relocate paths: `root` is the local mirror;
native adapter routes still resolve against the preserved `plan.root` string.
Three distinct local and original native roots/plans are required.

The local mirrors must include complete stage inventories, adapter artifacts,
raw request/response files, prepare/controller receipts, plan/completion, training
encodings, costs, material, calls and `historical_OFF.json`. Scores alone are
insufficient for this contract. Main owns any copying/extraction/archive work;
this reducer does not extract archives or open original native roots implicitly.
The historical archive may have a different local pathname than its original
plan record; only that transport path is normalized after exact archive SHA
verification, with every other imported-history value checked unchanged.

## What is independent / what is shared

New independent logic verifies collection-to-score/plan/completion joins,
completed stage trees and closed file inventories, native recorded routes,
requests/row IDs, four distinct worker receipts and exact four-stage lifecycle.
It replays raw text through the frozen `material.score_row`, then independently
builds panel totals, paired wins/losses/both/neither, differences, itemwise canary
losses and the original screen. The entire reconstructed frozen-score object
must equal saved `material_scores`; no saved field/totals are accepted as truth
without raw replay. Saved per-item canaries and generation costs must also agree.

The original row scorer, frozen v2 historical archive importer, fit-manifest /
prepared-epoch validators and pure native response validator are shared, pinned
dependencies, not independently reimplemented scientific definitions. No runner
`verify`, `validate_completed`, `collect`, Native or process/GPU querying is called.
The historical importer reuses exact original OFF archive/plan/completion/score
pins, checks native prompt/base/template/route receipt joins and reads no new OFF.
Stage adapter files are rehashed, not numerically remeasured or model-loaded.

Historical OFF is explicitly `noncontemporaneous=true`, reused, 48 unique original
calls, zero incremental calls/updates. It is not multiplied into three control
replications. Every seed has 2 fresh fits / 672 updates / 2688 presentations /
96 new calls; full roster must total **6 fits / 2016 updates / 8064 presentations /
288 calls**. Each arm has exactly336updates/48calls. Source/target/epoch agreement
and all helper/protocol pins are bound to the frozen v2 plan.

## Metrics and limitations

Important inherited semantics: the original contrastive `strict_pass` uses the
public typed-JSON/source checker. **It accepts valid JSON whitespace/key order;
it is NOT canonical-byte equality.** Fences are not accepted. This differs from
later Level1 canonical-format interfaces; none of those parsers is substituted.

- `strict`: unchanged original row-scoring endpoint and original screen.
- `content`: all four typed, parsed source fields correct with stop completion;
  addition/copy retain their original exact-target rule. It can coincide with
  strict; no artificial distinction is manufactured.
- `exact_target_bytes`: separate descriptive raw-target equality, not a screen.
- Per-field correct/incorrect/unavailable counts; completion, syntax, schema,
  source and strict-failure categories with full per-row raw text and raw SHA.
  Failure categories may overlap; unavailable fields are not labeled incorrect.
- Per-seed CONTRASTIVE minus PLAIN and historical OFF, both content and strict,
  on each12-row panel and24-row held union, with paired item IDs and differences.
- Both arms' individual OFF-correct canary losses, not net gain/loss offsets.
- Context/supervised/padded training-token costs independently recalculated from
  the pinned112epoch schedules/encodings; output/prompt counts and generation time
  from native receipts. Fit duration/loss remain stored diagnostics; durations
  are not a concurrent makespan or proof of equal compute.

The original screen is reported per seed with unchanged thresholds, including
OFF ceiling and no contrastive canary losses. There is no selection rule, new
whole-roster success threshold, automatic pass, promotion, training or next-run
decision. `automatic_pass=false`, `scientific_pass=null`.

All panels are exposed exploratory DEV; D1/D2 share12sources, C-record is exposed,
and negate-earlier remains a perfect shortcut. Grouping plus instructions differ
and context costs differ. No fresh confirmation, source-attention mechanism,
child SLEEP, parenting, freeze, clean lineage, H1/H2/general G3 or working-loop
claim follows. Receipt consistency does not authenticate native hardware, prove
live process absence or independently re-encode native tokenizer/weight state.

## Tests and validation

`python3 -B /tmp/test_astra_contrastive_full_dose_analysis_20260913.py`
— **25 PASS, 10.617s**. CLI help, AST and trailing-whitespace checks also PASS.

Tests use actual frozen material/pure scoring and the pinned v2 CPU fixture
harness (`/tmp/test_astra_contrastive_full_dose_run_20260913_v2.py`, SHA
`b680d2123f496e405e203fe7a9859deb9b55a3ca177e3d5f766008695fd0333e`): toy tokenizer,
mocked fits/readouts, synthetic responses, temporary closed-capture directories.
No test reads the live full-dose roots or actual new full-dose outcomes.
Coverage includes missing arms/rows/seeds, changed captured bytes/field scores,
bool-vs-int schema errors, truncation completion, whitespace and fence semantics,
original screen equivalence, per-item harm in both canaries/arms, source/padding
cost replay, historical-OFF accounting, all-three budget, failure rejection,
nonfinite/duplicate JSON, output overwrite/path traversal, and forbidden native
lifecycle calls. The whole-roster aggregation test uses three synthetic summaries;
single-pair custody/raw replay is exercised with a complete synthetic capture.

Main may run this only after supplying completed pinned local evidence. No real
outcome report is created by this implementation task. **EDITSTOP.**
