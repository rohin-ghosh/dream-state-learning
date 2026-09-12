# Demonstration content audit — 2026-09-12

**Local verification: PASS; failures: [].** No generation, fit, GPU/network/git action or repo edit.
Capsule SHA256: `b2d03d6b41c7211ac0c87ff177e590badb137cb2a9624abca4bc5749ac1d1417`. Compared 28 extracted files to archived bytes; verified prep/arm inventories, 32 raw returns and original CPU replay.

## Recount (strict results unchanged)

| Arm / stage | Grounded /8 | Schema /8 | Invalid citations | Whole structured clean /8 |
|---|---:|---:|---:|---:|
| process / source | 2 | 7 | 5 | 2 |
| process / transfer | 1 | 7 | 6 | 1 |
| format / source | 0 | 8 | 8 | 0 |
| format / transfer | 0 | 8 | 8 | 0 |

The two process p01 outputs each name **three cells**, not two: schema failures score 0; no pair extraction/salvage. All other failures are factual citation failures, not numeric strings or JSON syntax. Invalid-citation totals exclude schema-rejected records by the original rule. Schema-valid does not mean board-grounded.

## Every raw citation against the actual candidate

| Arm | Case | Citation (group; cells; digit) | Observed values | Verdict |
|---|---|---|---|---|
| process | s01 | row; [[1, 1], [1, 2], [1, 4]]; 2 | [2, 2, 1] | coordinate_shape: expected exactly two two-integer cells |
| process | t01 | box; [[2, 2], [3, 1], [3, 3]]; 3 | [3, 2, 3] | coordinate_shape: expected exactly two two-integer cells |
| process | s02 | row; [[2, 2], [2, 3]]; 4 | [4, 2] | claimed_digit_not_at_both_cells |
| process | t02 | box; [[3, 3], [3, 4]]; 1 | [1, 1] | VALID |
| process | s03 | box; [[3, 3], [4, 4]]; 1 | [2, 3] | claimed_digit_not_at_both_cells |
| process | t03 | box; [[1, 3], [3, 3]]; 1 | [1, 4] | not_same_named_unit, claimed_digit_not_at_both_cells |
| process | s04 | row; [[4, 1], [4, 2]]; 4 | [4, 4] | VALID |
| process | t04 | column; [[1, 2], [4, 2]]; 4 | [4, 1] | claimed_digit_not_at_both_cells |
| process | s05 | row; [[1, 4], [4, 4]]; 1 | [1, 3] | not_same_named_unit, claimed_digit_not_at_both_cells |
| process | t05 | box; [[2, 2], [3, 1]]; 3 | [4, 3] | not_same_named_unit, claimed_digit_not_at_both_cells |
| process | s06 | column; [[2, 3], [3, 3]]; 3 | [2, 1] | claimed_digit_not_at_both_cells |
| process | t06 | box; [[2, 2], [3, 1]]; 1 | [1, 1] | not_same_named_unit |
| process | s07 | row; [[4, 1], [4, 4]]; 2 | [2, 2] | VALID |
| process | t07 | box; [[3, 3], [4, 2]]; 2 | [2, 1] | not_same_named_unit, claimed_digit_not_at_both_cells |
| process | s08 | row; [[1, 1], [3, 4]]; 1 | [4, 1] | not_same_named_unit, claimed_digit_not_at_both_cells |
| process | t08 | column; [[2, 3], [4, 4]]; 1 | [2, 2] | not_same_named_unit, claimed_digit_not_at_both_cells |
| format | s01 | row; [[1, 1], [3, 1]]; 2 | [2, 2] | not_same_named_unit |
| format | t01 | box; [[2, 2], [3, 3]]; 3 | [3, 3] | not_same_named_unit |
| format | s02 | box; [[2, 2], [3, 2]]; 4 | [4, 4] | not_same_named_unit |
| format | t02 | column; [[1, 2], [3, 2]]; 4 | [4, 2] | claimed_digit_not_at_both_cells |
| format | s03 | box; [[3, 3], [4, 4]]; 1 | [2, 3] | claimed_digit_not_at_both_cells |
| format | t03 | row; [[1, 1], [3, 1]]; 1 | [1, 1] | not_same_named_unit |
| format | s04 | box; [[3, 3], [4, 3]]; 3 | [3, 1] | claimed_digit_not_at_both_cells |
| format | t04 | column; [[3, 3], [4, 3]]; 1 | [3, 1] | claimed_digit_not_at_both_cells |
| format | s05 | row; [[1, 4], [3, 2]]; 1 | [1, 3] | not_same_named_unit, claimed_digit_not_at_both_cells |
| format | t05 | column; [[2, 2], [3, 3]]; 4 | [4, 4] | not_same_named_unit |
| format | s06 | row; [[1, 3], [3, 2]]; 3 | [3, 3] | not_same_named_unit |
| format | t06 | box; [[2, 2], [3, 1]]; 1 | [1, 1] | not_same_named_unit |
| format | s07 | column; [[2, 4], [4, 2]]; 2 | [4, 3] | not_same_named_unit, claimed_digit_not_at_both_cells |
| format | t07 | box; [[2, 2], [3, 3]]; 2 | [2, 2] | not_same_named_unit |
| format | s08 | box; [[3, 3], [3, 4]]; 1 | [4, 1] | claimed_digit_not_at_both_cells |
| format | t08 | column; [[2, 3], [4, 3]]; 1 | [2, 1] | claimed_digit_not_at_both_cells |

## Exact valid child bytes and ancestry
These are decoded native `RequestOutput.outputs[0].text` UTF-8 bytes, not JSON-reserialized targets. JSON report also stores base64, byte length, full prompt/output hashes, raw-return line/hash and candidate. **Evidence identification only; none is training-approved.**

### process t02 — rg/mini_sudoku/1851301
Raw `/tmp/astra_demonstration_terminal_20260912/astra_demonstration_20260912_attempt1/process/generations.jsonl` line 11, pointer `/requests/0/outputs/0/text`; request index 3.
Output SHA256 `019bcf5685a46a2f05be4e32ac4e9f138b71da7b1fd72f38078ed65e32d842bf`; 121 UTF-8 bytes; 41 native output tokens.
Candidate SHA256 `0b38f1c804b5f458531d544260eb669571ba652108e03dfba669fc7400b45ffc`; board `[[2, 4, 4, 1], [4, 1, 2, 4], [2, 2, 1, 1], [1, 3, 4, 4]]`.
```json
{"case_id":"t02","checks":[{"group":"box","cells":[[3,3],[3,4]],"digit":1}],"lesson":"Check box members for duplicates."}
```

### process s04 — rg/mini_sudoku/1851203
Raw `/tmp/astra_demonstration_terminal_20260912/astra_demonstration_20260912_attempt1/process/generations.jsonl` line 20, pointer `/requests/0/outputs/0/text`; request index 6.
Output SHA256 `0044d1eaac7e4d9f59bb3c890789ece3d52a950c4d61162d0542af059ce377de`; 118 UTF-8 bytes; 41 native output tokens.
Candidate SHA256 `9586e62d9f8e695ba46164d8dad733f29d681a31c86cccdcd369df3f8a8eb7d8`; board `[[4, 4, 2, 3], [2, 3, 4, 1], [1, 3, 3, 4], [4, 4, 1, 2]]`.
```json
{"case_id":"s04","checks":[{"group":"row","cells":[[4,1],[4,2]],"digit":4}],"lesson":"Check row for repeated values."}
```

### process s07 — rg/mini_sudoku/1851206
Raw `/tmp/astra_demonstration_terminal_20260912/astra_demonstration_20260912_attempt1/process/generations.jsonl` line 38, pointer `/requests/0/outputs/0/text`; request index 12.
Output SHA256 `e8a739c3ef2cc977e3738afa98f4f87acd1c6a74cabcc2a4742c19ad6d8823f6`; 112 UTF-8 bytes; 40 native output tokens.
Candidate SHA256 `b3061c9cac46da54af768d798858ba03919755cf06c3f96e2d2b5ee2b5f95cc9`; board `[[2, 4, 1, 2], [1, 1, 3, 4], [4, 1, 2, 2], [2, 3, 4, 2]]`.
```json
{"case_id":"s07","checks":[{"group":"row","cells":[[4,1],[4,4]],"digit":2}],"lesson":"Check row for duplicate."}
```

**Crucial ancestry:** process s04 repeats the provided example check (different lesson wording); process s07 cites another valid row pair, not the example. Neither source case has a successful transfer. There are zero byte-identical/verbatim-example echoes in either arm. Different valid coordinates do not establish independent discovery.
The sole valid transfer is process **t02**, following **invalid s02**. Its box citation `(3,3),(3,4), digit 1` is true on the new board and differs from both the source example and the erroneous source note. It is also different from the program-planted target row witness. This is one correct new-board response conditioned on a bad self-note—not a verified correct-source-to-application chain.
The exact s02 note SHA256 is `8f52557fcc81cae0574c6cf984818063c5aa32ecfde606bd21dcf76d8279cdb8`; byte span 966:1087 in t02's UTF-8 user prompt (half-open):
```json
{"case_id":"s02","checks":[{"group":"row","cells":[[2,2],[2,3]],"digit":4}],"lesson":"Check row members for duplicates."}
```
All 16 transfers retain their own source outputs byte-for-byte, including failures. Direct parent/example content is absent outside the note; transfer is **parent-free but not note-free**, and its ancestry remains externally demonstrated. No child attempted Sudoku ACT or solved board is represented here.

## Lesson claims (separate from citation validity)
The three valid records say “Check row for repeated values.”, “Check row for duplicate.” and “Check box members for duplicates.” These are generic checking imperatives; the corresponding single citations support only their local duplicates, not a learned checking habit or universally effective lesson. Imperatives are not additional verified observations. Process s03 says “Check row, column overlap.” despite a false box citation; t03 says “Check column overlap.” while naming a box across different boxes and unequal values. Other generic imperatives accompanying false checks do not repair them. **Free-prose lessons remain unverified and unapproved for training.**

## Pairing, cost and verification limits
Fixed source IDs 1851200..7; transfer IDs 1851300..7. Recomputed public-question parsing, deterministic fills/edits, all candidate/source hashes, 16-way uniqueness and actual relocated v1/v2 prior content. All eight common examples are factual, all eight transfer boards contain witnesses, and all eight copied source checks fail on transfer even with the case ID rebound.
Sampler 7101 is generation-only; two worker PIDs [132012, 132748]. Both arms use eight identical examples, order/caps/temperature and 16 calls. All32 native stops are `stop`, each <=128 tokens; actual prompt-token IDs match recorded counts; no truncation/rewrite.
Native token totals: process 5637/652 input/output; format 5536/648. Process explanation tokens [67, 67, 78, 67, 67, 78, 67, 67]; format [57, 57, 57, 57, 57, 57, 57, 57]. **Not token- or compute-matched:** same call caps do not equate actual dose; source specificity is part of the intervention. Elapsed controller time 340.549s is retained from the receipt, not independently timed.
The control has zero valid child records. A later process-valid-only fit versus an empty control would combine material selection, training dose and content quality; it cannot identify a parenting effect. Replaying this one event many times never makes multiple experiences. No P1/H1/generalization/internalization/persistence claim follows.
Remote Qwen2.5-7B-Instruct model/package paths are absolute node paths: file-pin assertions are captured, not locally authenticated model provenance. Matching available local source hashes are reported separately. No remote hash reread or GPU/process inspection was performed. Both cleanup/full-release observations are archived receipts only. Full raw bytes, masks and future model identities must remain bound if another stage is selected.

## Recommendation: one bounded event-utility diagnostic, not another production hunt
**Choose the single t02 event only for a technical sleep-utility/no-update comparison.** It is enough to ask whether writing this one verified citation changes behavior beyond a format-only write; it is not enough to test a reliable parent-to-own-lesson internalization process. Treat selection as posthoc, unique experiences=1, source failures retained in the history. Do not combine it with s04/s07 or label any record clean ancestry.
Proposed smallest next comparison (Main selection required): two fresh-base LoRA fits, one fixed optimizer seed distinct in role from sampler 7101, plus a shared no-update baseline. Full condition supervises the exact t02 record structural/citation bytes; active-format condition supervises only structural syntax from the **same raw record**, masking case-ID value and group/cell/digit values. Both mask lesson text and all context. Preserve the original raw sequence, actual transfer prompt and erroneous own source note as provenance/context; no parent explanation/example or parent lesson may enter the sleep corpus or target. Do not rewrite bad s02 into a correct lesson. This is an own-citation write, not an approved whole-lesson sleep.
Use identical span partitions and tokenized input/target sequences, batch/order/steps/base/LoRA initialization for both fits; change only loss flags. A proposed cap is 32 optimizer steps, rank8/alpha16, AdamW LR1e-4, dropout0.05, all existing projection targets, bf16, batch1/accum1; freeze these once, no sweep or continuation. Exact forward/backward token work can be matched this way; supervised-token counts intentionally differ and must be reported, not called identical learning dose. The syntax control still sees citation values through teacher forcing: this isolates citation supervision, not all content exposure. The no-update arm is a no-write reference, not a compute-matched training arm. No synthetic prose, answer padding, invalid control-record training, or hidden corrected target.
Minimum new wiring is a source-bound loss-span selector, not a new trainer: `parent_correction_write.py:raw_span` demonstrates byte binding; `train_adapter_v3.py:normalize_items`, `encode_spans`, `encode_item_segments` provide existing span masks. `parent_correction_write.py:make_corpus`/`command_specs` are **not drop-in**: they hardcode the old event/whole-target mask/32 replays×3 epochs/three recipients. New mask spans need actual-tokenizer verification, nonempty targets, zero truncation and token-boundary accounting before any fit. Parent/lesson exclusion is a corpus property, not a prose whitelist. Do not run the old command helper unchanged.
Evaluate the same eight captured transfer boards **without parent/example/source note**: t02 is a retention/control anchor; the other seven are already exposed development boards, not a new held-out test and not generalization evidence. Freeze exact evaluation prompts and deterministic decode before fitting; measure shared OFF once, and one ON pass per fit (24 evaluation calls total). Score unchanged strict grounded count, invalid citations, schema and per-case transitions; report retention separately from other-seven gain and full-write minus format-write. Current stochastic note-conditioned 1/8 is not the no-note OFF baseline. If no nontraining-case content gain, regression, a format-only gain, or equal active-control gain results, stop and record no demonstrated utility beyond that contrast. Never tune to this panel or collect replacements; no automatic fit promotion or certificates.
This intentionally small question is informative even if negative, but advances only the own-output→write→parent-removed evaluation link. It does not complete P1/integrated parenting. Two fits, one optimizer seed and one selected event give no robustness estimate. Inference cost reference is the captured 32-call/340.549s run; 24 evaluations likely minutes, but fit latency/VRAM is **unmeasured here** and must not be quoted as an observed budget. Hard proposed bounds: 32 steps/fit, 24 evaluation calls, 128 new tokens/call, no automatic continuation; Main must set wall-clock/lease caps before selection.

## Why not switch directly to the old nursery runner?
Existing `nursery_dialogue.py:play_task`/`parent_turn` and `rulegame.py:RuleGame.evaluate` supply the stronger eventual child-action→world-feedback→own-note→different-task path. However the current runner is not an already matched clean baseline: parent makes two extra calls; solo makes none; arm names affect episode IDs; notes/prefixes are stripped and truncated; `admitted = post >= pre` is logged but failure branch is `pass`, not a selection veto. `RuleGame.evaluate` TRY reports boolean environment feedback with zero score; quiz score is a different endpoint. Do not equate quiz improvement to lesson truth or launch `nursery_dialogue --phase sleep` unchanged (it invokes the legacy v21 trainer).
If Main wants a substantive integrated-chain test instead of the explicitly narrow utility check, choose a fixed small RuleGame block, not more miniSudoku words/seeds: same task IDs/triples in both arms, active format restatement with equal calls/caps, raw own notes untruncated, real TRY/outcome grounding, explicit selection from predeclared fixed tasks, and one note-/parent-free ON/OFF quiz panel after a modern LoRA-only sleep. Zero material yield stops the block; no rule/source replacement hunt. That requires a separately selected protocol and several hygiene fixes, so it is not the smallest immediate reuse of these terminal bytes. Neither path is implemented or authorized by this audit.

## Reproduction
`PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/astra_demonstration_content_audit_20260912.py`
The script writes only this report and its sibling JSON. It uses a stdlib independent schema/citation witness enumerator plus the existing CPU replay as a cross-check; all comparisons and raw evidence are retained in JSON. No normalization or replacement of original strict scores.
