# Actual memory analysis — implementation and completed local reduction

2026-09-13. EDITSTOP. Only new `/tmp` reducer/tests/handoff and local analysis artifacts were written. No native model/tokenizer/GPU calls, monitoring, launching, recollection, source/runtime changes or repository edits. This consumes already collected scores and pinned local receipts; it does not recreate native evidence or load tensor files.

## Files / checks

- `/tmp/astra_actual_memory_analysis_20260913.py`: `2d462f9dab797d72b397c33b0e823b65fda4ca8b7637babecf25b07cc144f994`.
- `/tmp/test_astra_actual_memory_analysis_20260913.py`: `c2256d534acf7461a15df9395841d3cb1766f27b67d7ca68f43603d63bd6ad5f`.
- This handoff: `/tmp/astra_actual_memory_analysis_20260913_handoff.md`.

**10 synthetic CPU tests PASS,0.437s.** Fixtures reproduce summaries using AST-extracted frozen runner summary functions independently of the new reducer. Coverage:14/8/8 denominators; all seeds; typed booleans/counts; nonfinite JSON/norms; finite WRITE-change/LR0-equality; missing/duplicate rows and seeds; source/target/plan pins; summary and original-retention disagreement; token/cost arithmetic; exact raw-byte checks; paired row IDs; strict-versus-content regression; complete local JSON/Markdown path and no overwrite.

Test command:
`python3 -B -m unittest discover -s /tmp -p test_astra_actual_memory_analysis_20260913.py -v`

## Actual reduction: all three pinned inputs PASS

Input scores under `/tmp/astra_memory_collected_20260913_attempt1/real_record_memory_seed{seed}_20260913_attempt1_collected/scores.json` were verified against Main's supplied hashes:

- seed0: `b56a0caa16259e29860efa284d283610ab9bfa9064c64f121fe7cc34266b72bf`.
- seed1: `5fe7638aa86e718b36ea00f9a97b9e36acbed4b464c968737acbc86447c71979`.
- seed2: `a0182417e86e85ab6a874c7e98d77fd5952e2bb036fe1a2e35d6e7289ecb0cef`.

The three memory plans and original perception scores were copied byte-for-byte into new `/tmp/astra_actual_memory_analysis_inputs_20260913/seed{seed}_{plan,original_retention}.json`, from the local memory evidence tar and original node2 second-roster tar. Every copied JSON digest matches the corresponding report plan or parent-score pin. No tensor payload was deserialized or read for evaluation; tar metadata located only the six required JSON entries. Original archives and score directories remain untouched.

Manifest: `/tmp/astra_actual_memory_analysis_inputs_20260913/manifest.json`, SHA256 `bff90c7c969b36088a6ff7862f06e3fa60fa1ee03b004fa50be914939aef13df`.

Completed outputs:

- `/tmp/astra_actual_memory_analysis_result_20260913/analysis.json`: `7bf30652548ed36800f8f1c5ee0c9a34dc79409d50c95b9818ce103364ebd323`.
- `/tmp/astra_actual_memory_analysis_result_20260913/analysis.md`: `e0d1ee714c0a8f277f281015d789dcac1c8d7c288df8d52b02a06565400ee314`.

The JSON records the current analyzer source hash. All native-reported totals, WRITE/LR0 paired counts and original_retention receipts reproduce exactly from cells plus pinned original post-fit rows. Raw readback SHA checks and same original source/target joins pass across both variants/arms. Recorded initialized tensor inventories match between arms; WRITE norms/deltas are finite and nonzero, LR0 changed_elements/delta are zero with equal initialized/final inventories. These are checks of recorded diagnostics, not a fresh tensor audit.

## Independent findings, preserving seed labels

| Seed | Exact production WRITE / LR0 | Paraphrase production WRITE / LR0 | Exact byte WRITE / LR0 | Held content WRITE / LR0 | Newly regressed held |
|---|---|---|---|---|---|
| 0 | 8/14 / 0/14 | 6/14 / 0/14 | 7/14 / 0/14 | 44/48 / 47/48 | 3 |
| 1 | 7/8 / 0/8 | 5/8 / 0/8 | 7/8 / 0/8 | 37/48 / 48/48 | 11 |
| 2 | 5/8 / 0/8 | 5/8 / 0/8 | 5/8 / 0/8 | 17/48 / 48/48 | 31 |

Paraphrase exact-byte WRITE counts are4/14,5/8,5/8; all LR0 counts0. Exact canonical strict WRITE counts3/14,0/8,0/8; paraphrase canonical strict0 for every seed. This is not contradictory: many admitted child targets are valid **noncanonical** JSON; exact recall of those bytes can be production-eligible while strict_canonical remains false. Preserve these distinct metrics rather than replacing the target or calling whitespace changes content gains.

Both arms retain canary12/12 content and strict in every seed. LR0 held/canary raw responses and scored outcomes match original post-fit receipts exactly. WRITE held raw changes are4/11/31, while newly regressed outcomes are3/11/31: seed0 includes a changed row that was already incorrect. Held strict numerators equal held content numerators here, but **failure causes differ**, and an `exact` format label alone does not certify correct/valid content.

Direct raw-row and error-cell audit of newly regressed held rows:

- **Seed0:3 new duplicate-key JSON failures.** Example formerly correct full record becomes an object repeating `observed` and omitting the triple. There are4 total WRITE held failures, including1 previously failing slot. This is substantive syntax/schema loss, not harmless whitespace or an invitation to parse with last-key-wins.
- **Seed1:11 wrong `predicted` + `relation` records**, with observed value and triple retained in those scored cells. Eight had original null/unavailable priors; three had an original true prior. No held length terminations, syntax or schema errors account for these11 losses.
- **Seed2:23 wrong output variants plus8 wrong prior/relation records.** The23 should have abstained:8 missing-outcome,8 outcome/action-mismatch,7 ambiguous-prediction cases. WRITE instead emits a full record. The remaining8 had original null/unavailable priors. No held length terminations or JSON syntax errors explain these31 losses. This is failure to preserve required abstention/source handling as well as prior fidelity, not merely canonical formatting.

Thus the results support **checkpoint-specific source-withdrawn record acquisition/persistence with separately measured paraphrase performance, accompanied by substantial and seed-dependent authored retention damage**. They do not support a stable retained substrate, improved autonomous learning, a pooled causal claim or H1/H2. A clean canary result does not cancel held-screen regressions. No automatic pass is emitted.

Work accounting only:480 generation calls and480 optimizer steps across the three paired runs; per-arm same-seed exposures are preserved. LR0 optimizer steps are not parameter changes. Complete per-seed token/time/fit-loss/norm costs and every paired win/loss/retained/regressed/gained row ID are in the JSON.

## API / fresh-output CLI

```bash
python3 -B /tmp/astra_actual_memory_analysis_20260913.py \
  --manifest /tmp/astra_actual_memory_analysis_inputs_20260913/manifest.json \
  --manifest-sha256 bff90c7c969b36088a6ff7862f06e3fa60fa1ee03b004fa50be914939aef13df \
  --out /tmp/NEW_FRESH_LOCAL_ANALYSIS_DIRECTORY
```

Do not reuse the existing output directory; validation completes before a fresh directory is created. The module reads only explicit local JSON files and the frozen runner's Python source. `--runner` optionally relocates the exact source bytes, pin `7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e`. Only its pure `check_fit` AST is executed; no runner import or native command occurs.

Input manifest schema `astra_actual_memory_analysis_inputs_20260913_v1`: keys `schema`, `seeds`; exactly three entries, each with `seed` and four `{path, sha256}` local file bindings: `scores`, `plan`, `collection`, `original_retention`. Original strict/raw retention baselines are absent from the compact native original_retention summary, so the pinned original scores are required rather than inferred. Collection receipt must join the scores/completion; plans bind fixed runner/projector/protocol/formation and original same-seed parent. Missing/partial reports, mismatched pins, reused seeds/rows, inconsistent numerators/costs or changed LR0 diagnostics fail closed, never become accuracy0.

Python entry points: `analyze_manifest(manifest, runner_path=...)`, `reduce_seed(report, plan, original, entry, check_fit)` for loaded fixtures, and `run(manifest_path, manifest_sha256, out, runner_path=...)` for pinned local files. Per-seed results remain separate; only resource accounting is summed. No original scores are regenerated or modified.

EDITSTOP.
