# Constraint production content audit — September 12, 2026

## Result: a real type-contract gap, but mostly incorrect content

**Original strict results remain process 0/8 (format 0/8), active-format control 1/8 (format 8/8).** An independent, explicitly post-hoc coordinate-only recount gives **process 2/8, control 1/8**. This does not replace the official endpoint, approve material for training, or establish a parenting advantage/internalization claim.

| Scoring view | Process grounded / 8 | Control grounded / 8 | Process format / 8 | Control format / 8 | Process-minus-control |
|---|---:|---:|---:|---:|---:|
| Original strict; independently reproduced | 0 | 1 | 0 | 8 | −1 |
| Post-hoc coordinate-type normalization only | 2 | 1 | 8 | 8 | +1 |

All eight process responses encode all four coordinate components as strings; all eight control responses already use integers. The common task says `Coordinates are [row,column], one-based` and explicitly calls the **digit** an integer, but does not explicitly type the coordinates. The control card additionally says `Keep integer fields as integers`. This is an avoidable asymmetry in syntax guidance, not grounds for silently relaxing the original checker.

The post-hoc transformation changes **only** single-character strings `"1"` through `"4"` inside `checks[].cells` to integers: 32 components across eight process records, zero control components. It does not alter digit, group, cell order, case ID, lesson, whitespace in raw output, or any other field; it does not swap axes or seek alternative witnesses. Raw strings remain preserved alongside diagnostic copies. Narrow-scope conversion self-checks leave `"01"`, `" 2"`, `"5"`, `"2.0"`, digit strings, and lesson strings untouched.

## All sixteen citations checked against the actual candidates

Coordinates below are written numerically for readability. **Every process row required the post-hoc type conversion; no control row did.** Values are read directly from the captured candidate, not a solution or planted-witness whitelist.

| Process case | Claimed group and cells | Claimed digit | Actual values | Same named unit? | Content valid after type conversion? |
|---|---|---:|---|---|---|
| c01 | column (2,4), (4,4) | 4 | 2, 3 | Yes | No |
| c02 | column (2,4), (3,4) | 4 | 3, 2 | Yes | No |
| c03 | row (1,1), (1,4) | 3 | 3, 4 | Yes | No |
| c04 | column (2,2), (4,2) | 3 | 3, 4 | Yes | No |
| c05 | column (1,4), (2,4) | 1 | 1, 3 | Yes | No |
| c06 | column (2,2), (4,2) | 2 | 2, 2 | Yes | **Yes** |
| c07 | column (2,4), (4,4) | 1 | 1, 1 | Yes | **Yes** |
| c08 | column (2,2), (4,2) | 3 | 3, 4 | Yes | No |

| Active-format case | Claimed group and cells | Claimed digit | Actual values | Same named unit? | Content valid? |
|---|---|---:|---|---|---|
| c01 | box (3,3), (4,4) | 4 | 4, 3 | Yes | No |
| c02 | box (3,1), (3,2) | 4 | 4, 4 | Yes | **Yes** |
| c03 | box (2,2), (3,1) | 1 | 2, 1 | No | No |
| c04 | box (2,2), (3,4) | 2 | 3, 2 | No | No |
| c05 | box (2,2), (3,2) | 1 | 4, 3 | No | No |
| c06 | box (2,2), (1,4) | 2 | 2, 1 | No | No |
| c07 | box (2,2), (3,4) | 1 | 2, 3 | No | No |
| c08 | box (2,2), (3,2) | 3 | 3, 1 | No | No |

There is exactly one citation per output. After normalization, process has **six incorrect citations**, all failing the claimed equal-digit condition despite correct group membership. Control has **seven incorrect citations**; six also cross box boundaries. Its group and value failure counts overlap, so they must not be added. All cited coordinates are distinct and in range after conversion. The two normalized process successes are column witnesses, accepted on their own merits, not because they match the program's planted row pair.

Official process `invalid_citations=0` means schema rejection prevented content scoring, **not** that its eight citations were correct. Strict structured-record-clean counts remain 0/8 and 1/8; post-hoc structured-field-clean counts are 2/8 and 1/8. Neither measure certifies lesson truth.

## Own lessons: plans, not evidence of completed checking

- Process: c01/c02/c04–c08 say `Check row next`; c03 says `Check column next`.
- Control: c01/c04 say `Check row 4`; c02 says `Check other boxes for 4`; c03/c05/c07/c08 say `Check rows next`; c06 says `Check next 2x2 box`.

These sixteen short imperatives propose future attention. They do not assert a completed check, concrete duplicate, or learned checking procedure. They are compatible with public checking actions, but provide no independent evidence that the current citation was checked correctly. For example, control c01's proposed row 4 has no duplicate; that does not make an instruction to inspect it a false factual assertion. Conversely, a proposed row that happens to contain a duplicate does not certify the lesson. **No lesson is machine-verified or approved for training; no normalized response becomes a target.** The captures are externally sourced observations, not the child's failed ACTs or clean ancestry.

## Smallest prospective clarification, if Main elects another production pair

Replace only the common-task coordinate sentence, identically in both arms, with:

> Coordinates are [row,column], one-based. Each row and column coordinate must be a JSON integer from 1 to 4, without quotation marks.

No worked coordinate answer, checker change, normalization at evaluation, parent-card revision, token padding, or extra training is needed. This is indicated to remove the observed typing ambiguity—not because 2 versus 1 demonstrates useful parenting.

Use eight **fresh**, prospectively frozen native training boards under the same deterministic exercise recipe and no-replacement collision/hash checks. The next contiguous range `1851008..1851015` is only a candidate for Main's collision check, not asserted unused or authorized here. Keep two fresh model processes, exactly 16 calls, one requested check, 128-token cap, actual tokenizer preflight, true stop/token receipts, original integer-only checker, and the existing time bounds. Freeze the clarified prompt before viewing new outputs. Finish and report all available cases or protocol failures; no success threshold, source hunt, fits, or post-hoc rescue of the new official score. The useful question is whether strict syntax improves and grounded citation accuracy survives it. Persistent low content accuracy would remain a production bottleneck, not evidence of successful sleep/internalization.

The existing cards were **not token-matched**: process 47 versus control 44 standalone tokens; total actual prompt tokens 2,104 versus 2,080. Output tokens were 392 versus 313. All sixteen stopped normally under 128 tokens. Record the new actual counts rather than claiming the clarification makes the packages equal; the small observed post-hoc difference is not a controlled causal estimate.

## Evidence and bounded verification

- Archive: `/tmp/astra_constraint_verified_terminal_20260912.tgz`; SHA256 `7935c254ac16cfbf33c8cbf9386e9a947ec9b02e50d28e9f03987efb3bbbda89` **matched**.
- Evidence root: `/tmp/astra_constraint_verified_terminal_20260912`. Preparation is `astra_constraint_check_preparation_20260912_attempt1`; pair is `astra_constraint_check_20260912_attempt1` beneath that root.
- Independently checked the preparation and both arm inventories; eight distinct actual question hashes and eight distinct candidate hashes; both arms' frozen configuration/prompt bindings; exactly eight request/raw-return/output triplets per arm; raw RequestOutput text versus output/summary text; text hashes, native token counts and `stop` finish reasons; and strict per-record/terminal counts. **No mismatch was found in these checks.** The independent scorer does not import the implementation checker.
- Captured cleanup receipts report owned groups empty, GPU processes absent and reservation release verified for PIDs 118957 and 119780. These are historical receipts, **not a new live GPU check**. Absolute remote model/source paths were not rehashed; no official base-origin authentication is implied.
- Recount command executed: `PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/astra_constraint_content_audit_20260912.py`. Detailed raw text, candidate matrices, hashes, conversion paths, per-citation predicates, lessons and totals are in `/tmp/astra_constraint_content_audit_20260912.json`. The script requires a fresh JSON output rather than overwriting it.

Only this audit's `.md`, `.json`, and `.py` were written. Original captures, strict results, repository code and training approvals remain unchanged. No GPU, git, SSH or network action; Main's objective PID 120373 and GPU0 work were not inspected or touched.
