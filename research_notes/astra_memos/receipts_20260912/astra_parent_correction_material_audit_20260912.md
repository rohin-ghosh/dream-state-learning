# Parent correction: bounded public-constraint/material audit

2026-09-12. DEV diagnosis only; formal C11 deferred. No repo edits, git, network, GPU, launches, kills, training, admission, corpus construction, or gate changes.

## Material decision

- **No observed signal favoring process.** Both arms move from 1/32 to 2/32 first-ACT solves. Qualifying corrections are process 1, sham 2; raw multi-ACT episodes 15 vs 7. This is descriptive, not an equivalence claim.
- **Process 1850124: do not use unchanged Scratchpad as a truthful diagnostic lesson.** Its row-repetition claim is false despite a publicly valid proposed solution.
- **Sham 1850118: preserve raw exploration, not a validated diagnostic lesson.** Actual last-row change and unit uniqueness are supported; motives/pattern explanation are not verified. It omits that the first board failed original givens, and its Scratchpad ACT has literal quotes.
- **Sham 1850124: one unchanged modest lesson candidate survives content screening.** Its correctness observation and public rule reminder are supported, and its proposed board is valid. Preserve the WHOLE raw Scratchpad, including its uncalibrated PREDICT. No factual contradiction found is not a usefulness, introspection-truth, learning, or admission certificate.
- All three Scratchpads already contain the exact subsequently solved board. Wake2 is consistent with reuse/re-emission of own text; correction does not isolate an explanatory or learning mechanism.

## Evidence and replay

Independent deterministic standard-library-only replay checks sealed file inventory, all 32 capture/ledger joins per arm, every request/output/live-headroom record, raw ACT order, own source identities, Scratchpad batch receipt and exact ledger prefix, public-outcome request construction, same-episode injection byte spans and chronology. No native verifier, model, reference answer, or final-gym data used.
Original process copy and terminal process are byte-identical. Both replay summaries agree with Main's original-source native replay. Original repo source files are joined to 30cdad8e10fe99873787a0f6ba7bb32d9ac42fb6 via their archived bytes, not inferred from current checkout or git. Remote package/base bytes and origin authentication remain outside this audit.

- Terminal capsule: `/tmp/astra_parent_correction_terminal_20260912.tgz` SHA-256 `bd4f7c5d035f423f27c262efbb17cc90bcab57cb30a45d894f7b3c98db65dd5b`.
- Main CPU replay: `/tmp/astra_parent_correction_native_replay_20260912.jsonl` SHA-256 `711cc079da813c8e2631c8d7ebba90ef287ae54ffc453632bfac9025160af390`.
- Machine-readable full audit: `/tmp/astra_parent_correction_material_audit_20260912.json` SHA-256 `09cc51e42e245f01165f6006b5e36833c35fe1fba6e2d5fa970b697058ef1559`.
- Deterministic audit script: `/tmp/astra_parent_correction_material_audit_20260912.py` SHA-256 `524f1b56498d36bb9c28e79937519f037e9106da686f25840f123ab73cc9c478`.

## Endpoints (first ACT, denominator 32 per arm)

| Endpoint | Process | Sham |
|---|---:|---:|
| first_act_solves | [1, 2] | [1, 2] |
| first_act_formats | [8, 13] | [7, 10] |
| first_act_native_partial | [9, 20] | [9, 16] |
| first_act_failure_opportunities | 31 | 31 |
| qualifying_corrections | 1 | 2 |
| multi_act_episodes | 15 | 7 |
| all_actions | 91 | 80 |
| actions_by_wake | [35, 56] | [32, 48] |
| wake_requests | 64 | 64 |
| scratchpad_requests | 35 | 32 |
| generation_requests | 99 | 96 |
| generated_tokens | 12007 | 9449 |
| cumulative_package_tokens | 9603 | 9312 |

Format includes 1–4 domain validity, not just a rectangular board. Native partial scores are not constraint-validity certificates. The reported 0.68 for 1850124 is rounded from 0.675; 1850118 sham reports 0.34 from 0.3375.
All raw wake ACTs remain recorded. Multi-ACT cells are nonqualifying even when a later ACT solves; ACT strings within Scratchpad are NOT executed actions. Native first-ACT endpoints and all-action best scores must not be substituted for each other.
Each request contains the fixed 97-token package. Process/sham have 99/96 actual package presentations and 12007/9449 generated tokens: equal wake opportunities do not mean equal realized dose. Token counts are receipt-checked, not retokenized.

Paired first-ACT acceptance (wake1, wake2): `[{"both": 1, "neither": 31, "process_only": 0, "sham_only": 0}, {"both": 1, "neither": 29, "process_only": 1, "sham_only": 1}]`.

## Candidate-level public checks and exact own claims

### process rg/mini_sudoku/1850124

Capture hash `4311b730882c09bfd90e65940a2aed3173e1452d971f312afa58e468570476a4`; question hash `45b30df662c15582ad0d093e6f41bffdc122019dae65f12d2151b7f92ecda251`.
Scratchpad SHA-256 `da3e56d6879548e2a5bd4deb09bf9f2f09a554f168040db74ec89bd1c5c695a3`. Generation indices: `[75, 83, 91]`.

**Original public givens**
```text
_ 4 1 _
_ _ _ 2
4 3 _ _
_ _ _ _
```
First ACT: `2 4 1 3 ; 3 2 4 1 ; 4 3 2 1 ; 1 5 3 2`.
Second ACT: `2 4 1 3 ; 3 1 4 2 ; 4 3 2 1 ; 1 2 3 4`.
Second ACT independently passes all original givens, all four rows, all four columns and all four 2×2 boxes.
First ACT changed givens: `[{"actual": 1, "column": 4, "given": 2, "row": 2}]`.
First ACT unit violations: `[{"duplicates": [], "index": 4, "kind": "row", "missing": [4], "out_of_domain": [5], "values": [1, 5, 3, 2]}, {"duplicates": [], "index": 2, "kind": "column", "missing": [1], "out_of_domain": [5], "values": [4, 2, 3, 5]}, {"duplicates": [1], "index": 4, "kind": "column", "missing": [4], "out_of_domain": [], "values": [3, 1, 1, 2]}, {"duplicates": [2], "index": "r1-2c1-2", "kind": "box", "missing": [1], "out_of_domain": [], "values": [2, 4, 3, 2]}, {"duplicates": [1], "index": "r1-2c3-4", "kind": "box", "missing": [2], "out_of_domain": [], "values": [1, 3, 4, 1]}, {"duplicates": [], "index": "r3-4c1-2", "kind": "box", "missing": [2], "out_of_domain": [5], "values": [4, 3, 1, 5]}, {"duplicates": [2], "index": "r3-4c3-4", "kind": "box", "missing": [4], "out_of_domain": [], "values": [2, 1, 3, 2]}]`.

**WHOLE raw own Scratchpad (unaltered)**
```text
NOTE: The previous attempt had some numbers repeated in rows and columns, and the last row did not fit the constraints. I need to ensure each row, column, and 2x2 subgrid contains each number from 1 to 4 exactly once.

ACT: 2 4 1 3 ; 3 1 4 2 ; 4 3 2 1 ; 1 2 3 4
PREDICT: 0.85

```
The code fence is presentation only; the JSON raw field/hash is authoritative for trailing newline bytes.

- `The previous attempt had some numbers repeated in rows and columns,` — **CONTRADICTED_IN_PART**. No row repeats a number. Column 4 repeats 1 (r2/r3). Splitting the conjunction exposes a false row diagnosis; a correct later board does not repair it.
- `and the last row did not fit the constraints.` — **SUPPORTED**. Last row [1,5,3,2] contains out-of-domain 5 and lacks 4.
- `I need to ensure each row, column, and 2x2 subgrid contains each number from 1 to 4 exactly once.` — **SUPPORTED_RULE_REMINDER_NOT_VERIFIED_INTROSPECTION**. Public rules explicitly require this. It echoes the visible rules/process instruction and is not evidence of an independently discovered method or executed check.
- `PREDICT: 0.85` — **UNSUPPORTED_AS_CALIBRATED_FORECAST_NOT_A_FALSE_OUTCOME_REPORT**. Prediction is child output, not an observed score; the Scratchpad ACT was never executed. Later wake2 gets 1.0. Do not relabel this as authoritative reward or measured calibration.

Decision: **EXCLUDE_UNCHANGED_SCRATCHPAD_AS_TRUTHFUL_DIAGNOSTIC_LESSON**.
Teacher/rule echoes: All prompts include a teacher package and the public rules. Generic rule repetition is observable; causal attribution or absence of subtler influence is not established. No full teacher-package copy detected in these candidate Scratchpads. Direct 4+-word normalized overlaps: `[{"normalized_text": "each number from 1", "source": "public_question", "words": 4}]`.

**Minimal exact spans for later consideration, NOT admission or a rewritten lesson**
Offsets are UTF-8 zero-based half-open bytes into the named decoded `captures.json` text field, not serialized JSON offsets. All selected text, parent-output hashes and span hashes are in JSON; no examples are assembled.
- `/24/wakes/1/generation/text` bytes `[0,42)`: **EXACT_OWN_ACT_FOR_LATER_CONSIDERATION_ONLY**, span SHA-256 `74887f842a07dd4e8e0992ecdc50d903859be33e5684c4709bdf5ceb4c084575`. Minimal standalone own-output action line independently satisfies original givens plus all 12 units. Not an explanatory lesson; no corpus constructed.
- `/24/scratchpads/0/capture/text` bytes `[224,261)`: **EXACT_OWN_BOARD_SUBSTRING_FOR_LATER_CONSIDERATION_ONLY**, span SHA-256 `067d612f872ad3e5504fb55cc5a9f41abf38f1715f4773d316ac09b299600332`. Already present before wake2; same board as the second action. If quoted, this is explicitly the inner byte span, not a claim the unchanged ACT parses. Not an independent second example.
- `/24/scratchpads/0/capture/text` bytes `[74,119)`: **SUPPORTED_EXACT_FRAGMENT_NOT_A_SILENT_REPAIR**, span SHA-256 `23024ef30c81f6684f90e8c295c2c36f96bfcc2c0ae5a30913fbb226600f9fde`. Last row [1,5,3,2] contains out-of-domain 5 and lacks 4. A fragment annotation only; retain and expose its full raw context.
- `/24/scratchpads/0/capture/text` bytes `[120,217)`: **SUPPORTED_EXACT_FRAGMENT_NOT_A_SILENT_REPAIR**, span SHA-256 `7b77ce8546aacdf96d6af6e8481ce09be8f1bec8f6914179602e390b8c8441ab`. Public rules explicitly require this. It echoes the visible rules/process instruction and is not evidence of an independently discovered method or executed check. A fragment annotation only; retain and expose its full raw context.

### sham rg/mini_sudoku/1850118

Capture hash `139c0e61a1dfaccfd312e12c56b5b90a8013e1d781d0eefe28eac2e5d46b34a9`; question hash `e5ae250e8240db45b775797f0ae5cf6e994221b83dfaf9bd56aa818780a6f52e`.
Scratchpad SHA-256 `5d5480d3f99620ba6393d8bf5ed91536c33c9a4ab68ef75a908a733e8821a220`. Generation indices: `[50, 58, 66]`.

**Original public givens**
```text
_ 2 _ _
3 _ _ _
_ 1 _ _
_ 3 1 4
```
First ACT: `1 2 3 4 ; 3 4 1 2 ; 2 1 4 3 ; 4 3 2 1`.
Second ACT: `1 2 4 3 ; 3 4 2 1 ; 4 1 3 2 ; 2 3 1 4`.
Second ACT independently passes all original givens, all four rows, all four columns and all four 2×2 boxes.
First ACT changed givens: `[{"actual": 2, "column": 3, "given": 1, "row": 4}, {"actual": 1, "column": 4, "given": 4, "row": 4}]`.
First ACT unit violations: `[]`.

**WHOLE raw own Scratchpad (unaltered)**
```text
PREDICT: 0.6

ACT: "1 2 4 3 ; 3 4 2 1 ; 4 1 3 2 ; 2 3 1 4"
; I changed the last row to see if the pattern would work differently.
; This time, I tried to break the pattern but still keep the numbers unique in rows, columns, and subgrids.
```
The code fence is presentation only; the JSON raw field/hash is authoritative for trailing newline bytes.

- `I changed the last row` — **SUPPORTED**. Last row changes [4,3,2,1] to [2,3,1,4]. Other rows also change; the text does not claim only the last row changed.
- `to see if the pattern would work differently.` — **UNSUPPORTED_AS_VERIFIED_MOTIVE**. An expressed hypothesis/intention, not an observable causal explanation. It is not contradicted merely because motives cannot be verified.
- `This time, I tried to break the pattern` — **UNSUPPORTED_VAGUE_SELF_EXPLANATION**. No defined pattern or observable test identifies this mental operation; not proof of learning or diagnosis.
- `but still keep the numbers unique in rows, columns, and subgrids.` — **SUPPORTED_BEHAVIOR_NOT_VERIFIED_MOTIVE**. Both first and proposed boards satisfy all 12 units. The original failure was changed givens r4c3=1 and r4c4=4, not unit uniqueness; that cause is omitted.
- `PREDICT: 0.6` — **UNSUPPORTED_AS_CALIBRATED_FORECAST_NOT_A_FALSE_OUTCOME_REPORT**. Prediction is child output, not an observed score; the Scratchpad ACT was never executed. Later wake2 gets 1.0. Do not relabel this as authoritative reward or measured calibration.

Decision: **PRESERVE_RAW_HYPOTHESIS_NOT_ESTABLISHED_DIAGNOSTIC_LESSON**.
Teacher/rule echoes: All prompts include a teacher package and the public rules. Generic rule repetition is observable; causal attribution or absence of subtler influence is not established. No full teacher-package copy detected in these candidate Scratchpads. Direct 4+-word normalized overlaps: `[]`.

**Minimal exact spans for later consideration, NOT admission or a rewritten lesson**
Offsets are UTF-8 zero-based half-open bytes into the named decoded `captures.json` text field, not serialized JSON offsets. All selected text, parent-output hashes and span hashes are in JSON; no examples are assembled.
- `/18/wakes/1/generation/text` bytes `[14,56)`: **EXACT_OWN_ACT_FOR_LATER_CONSIDERATION_ONLY**, span SHA-256 `c99e48bf5123082e3420666c09fbf0d4cd090fe826eec75e1f075ed825901a6d`. Minimal standalone own-output action line independently satisfies original givens plus all 12 units. Not an explanatory lesson; no corpus constructed.
- `/18/scratchpads/0/capture/text` bytes `[20,57)`: **EXACT_OWN_BOARD_SUBSTRING_FOR_LATER_CONSIDERATION_ONLY**, span SHA-256 `4cf1a2adfa700735b5d7b726af28bfb9f9e480838a2b74e4dfdb4ffab8ab1760`. Already present before wake2; same board as the second action. If quoted, this is explicitly the inner byte span, not a claim the unchanged ACT parses. Not an independent second example.
- `/18/scratchpads/0/capture/text` bytes `[61,83)`: **SUPPORTED_EXACT_FRAGMENT_NOT_A_SILENT_REPAIR**, span SHA-256 `b77fb2940e29a455c6943ad6ebb70b5dbba0b2e5ff90326686a8f6534a611b8d`. Last row changes [4,3,2,1] to [2,3,1,4]. Other rows also change; the text does not claim only the last row changed. A fragment annotation only; retain and expose its full raw context.

### sham rg/mini_sudoku/1850124

Capture hash `0a20aef2436bdd1bbc5317cd603819c8727bf638142509031a90b6ca96478f4c`; question hash `45b30df662c15582ad0d093e6f41bffdc122019dae65f12d2151b7f92ecda251`.
Scratchpad SHA-256 `2bb4313d7faf713090143fb8b79148422295aee3610b63c15437666983d2587d`. Generation indices: `[72, 80, 88]`.

**Original public givens**
```text
_ 4 1 _
_ _ _ 2
4 3 _ _
_ _ _ _
```
First ACT: `2 4 1 3 ; 3 2 4 1 ; 4 3 2 1 ; 1 5 3 2`.
Second ACT: `2 4 1 3 ; 3 1 4 2 ; 4 3 2 1 ; 1 2 3 4`.
Second ACT independently passes all original givens, all four rows, all four columns and all four 2×2 boxes.
First ACT changed givens: `[{"actual": 1, "column": 4, "given": 2, "row": 2}]`.
First ACT unit violations: `[{"duplicates": [], "index": 4, "kind": "row", "missing": [4], "out_of_domain": [5], "values": [1, 5, 3, 2]}, {"duplicates": [], "index": 2, "kind": "column", "missing": [1], "out_of_domain": [5], "values": [4, 2, 3, 5]}, {"duplicates": [1], "index": 4, "kind": "column", "missing": [4], "out_of_domain": [], "values": [3, 1, 1, 2]}, {"duplicates": [2], "index": "r1-2c1-2", "kind": "box", "missing": [1], "out_of_domain": [], "values": [2, 4, 3, 2]}, {"duplicates": [1], "index": "r1-2c3-4", "kind": "box", "missing": [2], "out_of_domain": [], "values": [1, 3, 4, 1]}, {"duplicates": [], "index": "r3-4c1-2", "kind": "box", "missing": [2], "out_of_domain": [5], "values": [4, 3, 1, 5]}, {"duplicates": [2], "index": "r3-4c3-4", "kind": "box", "missing": [4], "out_of_domain": [], "values": [2, 1, 3, 2]}]`.

**WHOLE raw own Scratchpad (unaltered)**
```text
NOTE: The previous attempt had some numbers in the right place but wasn't fully correct. I need to ensure each row, column, and 2x2 subgrid contains the numbers 1-4 exactly once.

ACT: 2 4 1 3 ; 3 1 4 2 ; 4 3 2 1 ; 1 2 3 4
PREDICT: 0.85
```
The code fence is presentation only; the JSON raw field/hash is authoritative for trailing newline bytes.

- `The previous attempt had some numbers in the right place but wasn't fully correct.` — **SUPPORTED**. Four of five ORIGINAL givens retained; invalid 5, changed r2c4 given, column/box conflicts. Also 12/16 cells match the later independently public-valid board; no reference key used.
- `I need to ensure each row, column, and 2x2 subgrid contains the numbers 1-4 exactly once.` — **SUPPORTED_RULE_REMINDER_NOT_VERIFIED_INTROSPECTION**. Correct public rule reminder, not a specific failure diagnosis. Directly available in the question even under sham; not evidence process teacher supplied a superior lesson.
- `PREDICT: 0.85` — **UNSUPPORTED_AS_CALIBRATED_FORECAST_NOT_A_FALSE_OUTCOME_REPORT**. Prediction is child output, not an observed score; the Scratchpad ACT was never executed. Later wake2 gets 1.0. Do not relabel this as authoritative reward or measured calibration.

Decision: **UNCHANGED_MODEST_RULE_REMINDER_PLUS_VALID_OWN_SOLUTION_SURVIVES_CONTENT_SCREEN_ONLY**.
Teacher/rule echoes: All prompts include a teacher package and the public rules. Generic rule repetition is observable; causal attribution or absence of subtler influence is not established. No full teacher-package copy detected in these candidate Scratchpads. Direct 4+-word normalized overlaps: `[{"normalized_text": "1 4 exactly once", "source": "public_question", "words": 4}]`.

**Minimal exact spans for later consideration, NOT admission or a rewritten lesson**
Offsets are UTF-8 zero-based half-open bytes into the named decoded `captures.json` text field, not serialized JSON offsets. All selected text, parent-output hashes and span hashes are in JSON; no examples are assembled.
- `/24/scratchpads/0/capture/text` bytes `[0,236)`: **WHOLE_RAW_CANDIDATE_FOR_LATER_CONSIDERATION_ONLY**, span SHA-256 `2bb4313d7faf713090143fb8b79148422295aee3610b63c15437666983d2587d`. No contradicted factual claim detected. PREDICT is an uncalibrated forecast, not an outcome fact. Preserve all raw bytes; not admission, demonstrated usefulness, learning, or a truthful-reflection certificate.
- `/24/wakes/1/generation/text` bytes `[0,42)`: **EXACT_OWN_ACT_FOR_LATER_CONSIDERATION_ONLY**, span SHA-256 `74887f842a07dd4e8e0992ecdc50d903859be33e5684c4709bdf5ceb4c084575`. Minimal standalone own-output action line independently satisfies original givens plus all 12 units. Not an explanatory lesson; no corpus constructed.
- `/24/scratchpads/0/capture/text` bytes `[185,222)`: **EXACT_OWN_BOARD_SUBSTRING_FOR_LATER_CONSIDERATION_ONLY**, span SHA-256 `067d612f872ad3e5504fb55cc5a9f41abf38f1715f4773d316ac09b299600332`. Already present before wake2; same board as the second action. If quoted, this is explicitly the inner byte span, not a claim the unchanged ACT parses. Not an independent second example.
- `/24/scratchpads/0/capture/text` bytes `[6,88)`: **SUPPORTED_EXACT_FRAGMENT_NOT_A_SILENT_REPAIR**, span SHA-256 `dbe00e60861ad3483e7004d798bc3516efda23bb750d0f9fd700a49b8352a74e`. Four of five ORIGINAL givens retained; invalid 5, changed r2c4 given, column/box conflicts. Also 12/16 cells match the later independently public-valid board; no reference key used. A fragment annotation only; retain and expose its full raw context.
- `/24/scratchpads/0/capture/text` bytes `[89,178)`: **SUPPORTED_EXACT_FRAGMENT_NOT_A_SILENT_REPAIR**, span SHA-256 `9d9da33899e8cb61ad563f0ede847c3a44066444ef1f3e1c2e4573a2f88adc39`. Correct public rule reminder, not a specific failure diagnosis. Directly available in the question even under sham; not evidence process teacher supplied a superior lesson. A fragment annotation only; retain and expose its full raw context.

## All 32 paired cells

Scores list EVERY ACT in order. `M` means at least one multi-ACT wake; `Q` means qualifying one-ACT-each correction. Blank flags imply neither. Format and public-validity bits are available per wake in JSON.

| ID suffix | Process wake1 / wake2 native scores | Flags | Sham wake1 / wake2 native scores | Flags |
|---|---|---|---|---|
| 1850100 | [0.0] / [0.1125, 0.1125, 0.5625] | M | [0.0] / [0.1125] |  |
| 1850101 | [0.0] / [0.28125] |  | [0.0] / [0.3375] |  |
| 1850102 | [0.225] / [0.1125, 0.1125] | M | [0.225] / [0.39375] |  |
| 1850103 | [0.0] / [0.0, 0.225] | M | [0.0] / [0.0, 0.05625] | M |
| 1850104 | [0.0] / [0.0, 0.0] | M | [0.0] / [0.0] |  |
| 1850105 | [0.0] / [0.3375, 0.225, 0.0] | M | [0.0] / [0.1125] |  |
| 1850106 | [0.28125] / [0.1125] |  | [0.5625] / [0.3375] |  |
| 1850107 | [0.16875] / [0.16875] |  | [0.09177631578947368] / [0.13766447368421053] |  |
| 1850108 | [0.0] / [0.1585227272727273] |  | [0.3170454545454546] / [0.1516304347826087, 0.22744565217391305, 0.30772058823529413] | M |
| 1850109 | [0.0, 0.0, 0.0, 0.0] / [0.225] | M | [0.0] / [0.0] |  |
| 1850110 | [0.0] / [0.0] |  | [0.0] / [] |  |
| 1850111 | [0.5625] / [0.2051470588235294, 0.15386029411764707, 0.2051470588235294] | M | [0.5625] / [0.35900735294117647] |  |
| 1850112 | [0.0] / [0.23778409090909094] |  | [0.0] / [0.0] |  |
| 1850113 | [0.0] / [0.0, 0.05625, 0.28125] | M | [0.0] / [0.0] |  |
| 1850114 | [0.225] / [0.225, 0.3375] | M | [0.225] / [0.3170454545454546] |  |
| 1850115 | [0.0] / [0.0] |  | [0.0] / [0.0, 0.0, 0.0] | M |
| 1850116 | [0.0] / [0.675] |  | [0.0] / [0.675] |  |
| 1850117 | [0.0] / [0.225, 0.1585227272727273] | M | [0.0] / [0.45] |  |
| 1850118 | [0.3375] / [0.675, 0.39375, 0.675] | M | [0.3375] / [1.0] | Q |
| 1850119 | [0.0] / [] |  | [0.0] / [0.0] |  |
| 1850120 | [0.7875] / [0.30772058823529413] |  | [0.0] / [0.50625] |  |
| 1850121 | [0.0] / [0.0] |  | [0.0] / [0.0] |  |
| 1850122 | [0.0] / [0.50625] |  | [0.0] / [0.225, 0.225] | M |
| 1850123 | [0.0] / [0.22744565217391305] |  | [0.0] / [0.0] |  |
| 1850124 | [0.675] / [1.0] | Q | [0.675] / [1.0] | Q |
| 1850125 | [0.0] / [0.1125, 0.1125, 0.45, 0.45, 0.0] | M | [0.0] / [0.1125] |  |
| 1850126 | [0.0] / [] |  | [0.0] / [0.0, 0.0, 0.0] | M |
| 1850127 | [1.0] / [1.0, 1.0, 0.45] | M | [1.0] / [0.0] |  |
| 1850128 | [0.0] / [0.225] |  | [0.0] / [0.05625, 0.3375] | M |
| 1850129 | [0.0] / [0.0] |  | [0.0] / [0.0] |  |
| 1850130 | [0.3375] / [0.3375, 0.3375, 0.3375, 0.0] | M | [0.3375] / [0.30772058823529413] |  |
| 1850131 | [0.0] / [0.0, 0.0, 0.19815340909090912] | M | [0.0] / [0.0, 0.0, 0.0, 0.0, 0.1585227272727273, 0.3170454545454546, 0.3170454545454546, 0.3170454545454546, 0.45] | M |

## Smallest next comparison (recommendation only)

If Main elects existing gated V3 sleep: compare unchanged sham1850124 whole raw Scratchpad against its exact child-authored corrected ACT-only span, with identical source episode, base lineage, optimization/exposure opportunities and a common no-sleep/OFF baseline; report the unavoidable raw-token difference. Use fresh-process teacher-free OFF/ON evaluation on fixed disjoint problems, not this already-solved item.

Does the supported raw rule reminder plus own solution yield more teacher-free transfer than rehearsal of the same own solution alone?

Do not pool process false-diagnosis text, upgrade sham118 speculative motives to truth, add a curriculum/guard, or infer H1/P1 from one item.

A one-item DEV comparison may fail or be inconclusive; it cannot establish broad reflection truth, usefulness, or process-teacher superiority.

Keep the entire original text and ledger as evidence. Do not silently replace the false process diagnosis with an auditor-written truthful lesson; do not remove quotes/predictions and call the result unchanged. Span annotations identify possible future scopes, not an admitted corpus. Existing provenance/contamination/claim gates still apply; no new broad guard or curriculum is proposed.
