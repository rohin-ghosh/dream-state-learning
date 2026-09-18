# Bounded read-only C2 ACT comparison

Observed 2026-09-17T18:30:33.359059-07:00. **Malformed emitted code is present in both sleep41 copies as well as the original.** No intervention or learner-code execution.

| Source / ACT cycle window | ACT responses | Selected first blocks | CPU launch yes / no / unknown | Generation truncated | Syntax errors after parser / selected | Fullwidth punctuation / selected | Leading-dot assignment / selected |
|---|---:|---:|---:|---:|---:|---:|---:|
| explicit1 42–47 | 6 | 4 | 4 / 2 / 0 | 0/6 | 1/4 | 0/4 | 0/4 |
| brief1 42–47 | 6 | 6 | 5 / 0 / 1 | 1/6 | 3/6 | 2/6 | 0/6 |
| original_C2_recent 46–50 | 5 | 5 | 5 / 0 / 0 | 0/5 | 4/5 | 0/5 | 1/5 |
| original_C2_all_retained 42–50 | 9 | 9 | 9 / 0 / 0 | 0/9 | 7/9 | 1/9 | 1/9 |

## Receipt examples

| Source | ACT cycle / RESPONSE | Literal evidence | Execution distinction |
|---|---|---|---|
| explicit1 | 44 / 5274 | `2*n + １`, `/ ３₀` | Actual SyntaxError; numerals, not punctuation. |
| explicit1 | 45 / 5343; 46 / 5411 | `return =[eq1, eq２]`; cycle46 also `>>>` | Both NO_CPU_ATTEMPT from broken/non-fence delimiters. Both generation truncated=false. Includes malformed code-looking text, not selected executable Python. |
| brief1 | 43 / 5205 | `2 remedies*n` | Actual SyntaxError, stray word. |
| brief1 | 45 / 5343; 46 / 5412 | `（...）` in expressions | Existing parser replaces parentheses. Cycle45 still fails on `3０`; cycle46 parses but raises NameError for `symbols`. |
| brief1 | 47 / 5481 | `２ * n`, subscript numeral | Truncated=true; selected code is syntactically invalid, but actual execution UNKNOWN. Included in denominator. |
| original C2 | 45 / 5345 | `))／30`; `solve(equa` | Solidus normalized; actual unterminated-call SyntaxError. Earlier retained cycle, not current recent window. |
| original C2 | 46 / 5414 | `.S_3_correct = 98` | Actual SyntaxError. |
| original C2 | 48 / 5554; 49 / 5623; 50 / 5692 | `V = symbols 'V')`; `V =`; `9８` | Actual SyntaxErrors: malformed call/parenthesis, incomplete assignment, fullwidth numeral. |

## Bounds and interpretation

### Fullwidth ASCII including digits — Main follow-up

Counting any U+FF01–U+FF5E in the saved **raw selected first code block**, rather than punctuation alone:

| Source | Blocks containing fullwidth ASCII / selected blocks | ACTs in window | Flagged cycles |
|---|---:|---:|---|
| explicit1 | 1/4 (25%) | 6 | 44 |
| brief1 | 3/6 (50%) | 6 | 45,46,47 |
| original C2 recent | 2/5 (40%) | 5 | 48,50 |

This includes comments/literals in the selected source and includes the truncated/unknown brief1 attempt. It excludes later unexecuted fences and the two explicit1 responses lacking a selected block; it is not an all-response/all-code-block rate. Main recomputed these counts from `raw_code` in the two saved source receipts below, without executing code or reading new live records. The window remains ACTs leading into sleeps42–47 for copies and46–50 for the original, not the preceding-checkpoint convention in the watcher notice.

Current retained post-sleep41 journals only: explicit1/brief1 records5129..5520, original records5129..5751. ACT cycles are not claims of completed sleeps. Archived discarded suffixes, held data, readouts and captions not read.

CPU launch means a recorded interpreter launch, not a successful program body or correct mathematical result. Static syntax errors include the unknown-execution brief1 cycle47. Existing normalization fixes fullwidth punctuation only; do not equate raw punctuation with a surviving execution-source error. All18 published tool-result source hashes equal their selected normalized source hashes.

Per Main/user verified current math environment has SymPy installed since 2026-09-17 17:01 PDT; historical ModuleNotFoundError receipts are not claims of present absence.

No training/ON-OFF, later-weight or improvement conclusion. Same restored41 starting checkpoint does not match later contexts/weights, environments, sampling or interventions; requires a matched same-context probe.

## Exact source receipts

- `research_loop/workers/rohin174_parenting_20260917/node3/r194_act_comparison/copies_1789694752748910843.json` SHA256 `2f228c1e2de10e597bb5cea639cf1978679c20956dd70daa4f8ee4c36a01c61b`.
- `research_loop/workers/rohin174_parenting_20260917/node3/r194_act_comparison/original_1789694763749535150.json` SHA256 `aa36cfda539339dca7aabd29f1ddb669a949a82b6ecf76382eb98a3978c51e11`.
- `research_loop/workers/rohin174_parenting_20260917/node3/r194_act_comparison/NONEXECUTED_CODE_RECEIPTS.json` SHA256 `e22d8d6a7cae04320237eb2147190822bf99f16493fc1710f044ea0751f41499`.
- `research_loop/workers/rohin174_parenting_20260917/node3/r194_act_comparison/SUMMARY.json` SHA256 `285323afdfcf091160cca73aa79401b69cfdfd73d1e4c059ccba189433e8ce4f`.
