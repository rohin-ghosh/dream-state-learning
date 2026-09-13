# Post-memory raw analysis handoff — 2026-09-13

EDITSTOP. Only new local analysis/test/result files changed. No native calls, GPU/model/tokenizer loads, launches, monitoring, collection, Git or repository edits. Frozen helpers were loaded only for CPU replay; runner collect/verify were not imported or called.

## Findings

- All six native captures and three original admission banks replay exactly. Pinned post archive, score/plan/completion/collection joins, completed upstream adapter inventories, exact requests/responses, execution-source hashes, declared routes, prefix-token receipts and cost totals agree. This is local evidence replay, not independent native/model verification.
- WRITE production/content 8/16 each versus LR0 7/16, 6/16, 4/16. Each arm executed eight example-present slots and no example-absent slots; 24 calls/arm, 48/pair, zero new fits/updates. Canonical strict WRITE/LR0: seed0 4/4, seed1 0/0, seed2 0/0 (counts out of 16).
- Every absent-example wake stopped normally and emitted `ACT: TRY` followed by **space-separated integers without commas**. All 48 failures are the production parser's `ACT needs exactly three integers or six literal T/F labels`; not missing ACT, length termination or absent predictions. Raw variants are preserved in JSON and Markdown. No repaired outputs were scored.
- LR0 rejected records (1/2/4 by seed) have correct executed triple and observed outcome but replace an explicit Boolean prior with `null` and relation with `unavailable`. Production reports `prediction mismatch`; independently scored predicted/relation fields fail. WRITE gets all four fields correct in all eight reached records per seed. These are content errors, not merely canonical-format penalties.
- WRITE exact old-target byte matches: **7/8, 3/8, 0/8**; typed complete-target matches also **7/8, 3/8, 0/8**. LR0 exact matches 4/8, 3/8, 0/8; typed matches 6/8, 3/8, 0/8. Every exact matching target is current-source eligible. No copied-old-target/current-source contradiction occurred.
- WRITE actions outside both its admitted training-triple bank and the syntax-example triple: seed0 **0 (untested)**, seed1 **0 (untested)**, seed2 **4/4 eligible**, all `(3,7,11)` on first turns, with two true and two false fresh outcomes. Seed2's other four actions repeat example/training triple `(2,5,9)`; all eight typed full records differ from admitted targets. This rules out literal complete-target reuse for seed2 outputs, not compositional memorization, template use or another retrieval mechanism. “Outside training” here means the admitted memory bank only, not unseen to original Level1 or base-model training.
- LR0 non-bank/non-example executions: seed0 1/1 eligible, seed1 1/1, seed2 0/4. Do not interpret these as matched-action tests: jointly executed facts (action/outcome/prior) match WRITE/LR0 on only **7/8, 6/8, 3/8** slots. Seed2 WRITE uses prior F and `(3,7,11)` on first turns; LR0 uses prior T and other triples. Even identical initial prompts can lead to different experiences; later histories also differ.
- Paired WRITE-only/LR0-only gains are **1/0, 2/0, 4/0**, with full slot labels and cue×turn splits retained. Fixed cue assignment is confounded with episode IDs; no randomized causal explanation of comma use. Only three independent learners, not 48 independent trials.
- Prior WRITE held regressions **3/11/31** remain material; intact canaries and this scaffolded fresh-source endpoint do not establish stable substrate, strong H1/H2, recursive learning or automatic promotion.

## Reproduce

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /tmp/test_astra_post_memory_analysis_20260913.py -v
PYTHONDONTWRITEBYTECODE=1 python3 /tmp/astra_post_memory_analysis_20260913.py \
  --post-archive gpu_artifacts_local/post_memory_formation_20260913_attempt1/evidence.tar \
  --memory-archive gpu_artifacts_local/actual_record_memory_20260913_attempt1/evidence.tar \
  --scores-dir /tmp/astra_post_memory_collected_20260913_attempt1 \
  --out /tmp/CHOOSE_FRESH_POST_MEMORY_ANALYSIS_DIRECTORY
```

Default pinned-dependency source root: `/tmp/astra_level1_real_record_source_20260913_attempt1`. Output must not exist; no overwrite. Archive JSON members are read in place, never extracted. Memory JSON inputs are individually authenticated through pinned score→plan/completion hashes; adapter/model payloads are not read. Prior retention receipt is carried forward from already accepted memory scores, not recollected or newly rescored here. The initial intermediate `_attempt1` analysis output remains preserved; **use `_final` below**.

Tests: **12 PASS in 0.796s**, including real pinned six-state integration; synthetic original-core fixtures test source tampering, typed versus exact copying, wrong-source copies, fences, missing records, fixed pairing, duplicate JSON/rows/archive entries, pins and Boolean/nonfinite mistakes.

## Frozen files and SHA256

- `/tmp/astra_post_memory_analysis_20260913.py`: `760e20b86ad08d752c303278a3072b07a73a26750cac6599a2fa79d7d2562a86`
- `/tmp/test_astra_post_memory_analysis_20260913.py`: `2b0b8be566182ae8ee1f30c5c7587438fe1ccbe4430887a857499a77e73c5547`
- `/tmp/astra_post_memory_analysis_result_20260913_final/analysis.json`: `ee2b3d7f58e4ed8b6cc794815558b3e67ea2b58301c55868631d31876b196f92`
- `/tmp/astra_post_memory_analysis_result_20260913_final/analysis.md`: `2812af90e0acde8658a3b3b14046d1894fca360a8a41babe2ad2a827e13d6b54`
