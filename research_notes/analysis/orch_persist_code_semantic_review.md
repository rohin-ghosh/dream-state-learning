# PERSIST-CODE terminal whole-text diagnostic review

Author-side review, September 14, 2026; not independent certification.
Bound to attempt2 terminal archive
`33a9421ce15d494d1b3b792a01ea1ad9dd988ae98db9c73aec3c9e43f3c44940`.

All eight RICH episodes already fail the deterministic outcome gate. There
are **zero outcome-eligible RICH episodes and zero admitted rich rows**;
no semantic admission is inferred from a heading, word, or response length.

For diagnosis, read the whole first and last response of every RICH episode,
with its actual task, preceding feedback, and attempted action: 16/40 turns.
This is a posthoc diagnostic subset, not an estimated population pass rate.
The other 24 turns retain UNREVIEWED semantic status; all remain excluded by
their episode's failed outcome. Calls001–003 were additionally inspected during
execution debugging but are not part of the formal diagnostic denominator.
These judgments distinguish semantic grounding from action-format validity.

| RICH call | Semantic judgment | Substantive reason / supporting original span |
|---|---|---|
| 000 | FAIL | Invents input values and wrong arithmetic: “The sum of the mapped values is -28. This meets the requirement of the task.” No input or successful test supports it. |
| 004 | FAIL | Misreads a JSON parse error as list-type feedback; claims `affine(ge(xs, -4), -2, -5)` “is not providing a list,” contradicting helper semantics. |
| 005 | PASS | Correct generic affine→clamp→unique→sum ordering and conditional expectation for a list. This content judgment does NOT repair its missing JSON action or unbound `xs`. |
| 009 | FAIL | Introduces “Given the initial values [1, 2, 3, 4, 5, -1, -2, -3, -4, -5]” without observed inputs and truncates the purported action. The illustrative arithmetic alone is not an actual input-grounded repair. |
| 010 | FAIL | Treats absent self-records as an empty task input; concludes “Since the initial list is empty, no further action is needed.” Task requests a function over arbitrary `values`. |
| 014 | FAIL | Diagnoses a JSON parse error as `affine` failing on an empty integer list, contrary to public helper semantics, then repeats the same expression. |
| 015 | FAIL | Explicit memory/data confusion: “Since my stored records are currently an empty list [], there are no values to clamp.” Returns constant zero, fails actual `[0]` test expected1. |
| 019 | FAIL | “Since there are no records, the initial list is empty.” Also inserts deduplication into a task requiring duplicate-sensitive counting. |
| 020 | FAIL | “Given my current records are an empty list []” becomes a claim that the requested function returns zero; wrong interpretation of record absence as task data. |
| 024 | FAIL | Invents a sample and states mapped `[6,4,2,0]` sum is “12 - 8 = 4”; arithmetic is false, and no meaningful grounded repair addresses the parse error. |
| 025 | FAIL | Initially describes correct operation order but then assumes “Given the initial empty list []” despite no task input; fails to supply a general repair. |
| 029 | FAIL | Introduces an unsupported `ge([],0)` filter and moves `unique` before `clip`, contrary to “remove duplicates after clamping.” Empty-example zero does not justify equivalence. |
| 030 | FAIL | Uses `unique([])` and concludes the input is empty because the self-record store is empty; does not solve the requested arbitrary-input function. |
| 034 | FAIL | Treats JSON parse feedback as invalid empty-list input to `sum`, contradicting `sum([])=0`; returns constant zero instead of a general repair. |
| 035 | FAIL | “Since my stored records are currently an empty list []” grounds a fabricated empty input and unique-count interpretation, contrary to duplicate-sensitive count. |
| 039 | FAIL | “Since the ledger is empty” again substitutes memory state for arbitrary input. Correct empty-case arithmetic is insufficient grounding for the general function. |

Formal diagnostic counts: 1 PASS, 15 FAIL, 0 UNRESOLVED among these 16.
**No original text/action was rewritten or admitted.** RICH has 28 missing/
invalid final-JSON responses, 3 truncated responses, and 9 parsed actions.
All 9 parsed actions have 150–400 narrative tokens (152–326), yet none passes
the complete task oracle; 8 have expression errors and one constant-zero
attempt fails numerically. Narrative token counts for the other 31 are not
reported as failures or passes: action parsing did not produce that measure.

## TERSE own-record check

Read both entire original record turns with preceding successful expression,
visible prior record, task and actual success feedback. They are code-only
TERSE comparators, not rich-content candidates.

- CALL022, ledger_004: the record repeats the child's successful expression;
  deterministic recheck passes16/16. Narrow usable recipe, not a proven general
  lesson or cross-episode causal benefit.
- CALL029, ledger_006: the self-record adds a second threshold `-3` absent from
  its successful preceding expression, silently dropping permitted value `-4`.
  Same task's input `[-5,-4,-3]` requires27; the record recipe returns12.
  FAIL for fidelity to the grounded successful event. Provenance links and
  prior task success alone do not certify a truthful/useful lesson.

The alias diagnostic is separately marked **posthoc CPU counterfactual**.
Replacing AST name `xs` with `values` in already-parsed original expressions
would rescue only RICH ledger_000 and TERSE ledger_002/003. It creates no
native success, target, semantic PASS, or changed primary result. Namespace
ambiguity is therefore a credible contributor, not a demonstrated sole cause.
