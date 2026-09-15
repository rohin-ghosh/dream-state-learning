# Public-feedback pilot: completion and descriptive review

Observed 2026-09-15. Collection completed; no calls, replay, fit, ingestion,
rescoring or metric relabeling during this review. Original C2 run untouched.

## Completion and release

- Frozen C2 FULL15332, adapter ON child and adapter OFF BASE; 16 TRAIN tasks,
  three conditions, two responses per episode: 48 episodes / 96 responses.
- First response completed 16:43:25 UTC; last pair 16:46:23; guard exited
  successfully 16:46:51. Native16:55/external16:57 bounds were not extended.
- At16:49:59 UTC node2 physical7 was 0 MiB/0% and guard1387933/native1387951
  were absent. Natural release posted to COORD; no new work launched.
- Collection loaded no optimizer; zero optimizer steps/admissions. Frozen
  checkpoint and original optimizer identity retained in the JSON companion.
- Terminal SHA `fd508dc66da3172b068c11ecff86367c759a764b31cb2ced42389990b84f5a70`;
  clean guard SHA `9354f85a31c19a9966f07045a443834f2255831d97d8a92b890450c915cfd53f`.

## Frozen metrics versus descriptive revisions

Each condition has16 paired episodes. Counts below are not new success labels.

| Condition | Frozen before/after passes | Frozen success candidates | Raw changed | Extracted expression changed | Task-aligned partial edit | Expression syntax restored |
|---|---:|---:|---:|---:|---:|---:|
| CHILD public feedback | 0 / 0 | 0 | 7 | 1 | 1 | 0 |
| CHILD no feedback | 0 / 0 | 0 | 8 | 1 | 0 | 0 |
| BASE public feedback | 0 / 0 | 0 | 12 | 12 | 3 | 1 |

All96 public probes stopped at parser/schema/AST diagnostics; there were zero
interpreter outputs. Frozen `public_tests_executed=1` counts an attempted probe
even if parsing fails: it is not an executed-code test or a passed test.

## Actual partial/error-transition audit

Author reviewed all14 changed extracted-expression pairs against public task
specifications and AST structure, not hidden expected outputs. Pair-level source
hashes and every disposition are in the JSON companion; raw captures stay native.

| Cases | Descriptive assessment | Remaining obstacle |
|---|---|---|
| CHILD feedback ledger005 | Removes an unrequested filter: partial task alignment | Deduplication still before mapping/clamping, literal input and wrong key; schema error unchanged |
| BASE feedback ledger001/009/013 | Removes an unrequested filter, aligning helper order with the public map/clamp/deduplicate/sum instruction | Unknown input name and wrong key remain; no parameter/outcome re-verification |
| BASE feedback ledger015 | Extracted expression becomes Python-AST parseable | Last-line JSON failure unchanged; unknown identifiers, unsupported helper, helper arity remain |
| BASE feedback ledger010 | Substitutes already-public input via comprehension | No general input reference; unsupported comprehension and missing helper argument; not a usable identifier repair |
| BASE feedback ledger000 | Removes a required filter: task-alignment regression | Unknown-identifier diagnostic persists |
| BASE feedback ledger004/005/006/014 | Parseable expression becomes unparseable | Unchanged schema diagnostics mask a regression |
| CHILD no-feedback ledger005 | Parseable expression becomes unparseable | Public diagnostic worsens schema to JSON decoding |
| BASE feedback ledger007/011 | Malformed before and after | No supported semantic improvement conclusion |

Four task-aligned edits are all the same filter-removal pattern, not four
independent capabilities. The CHILD matched control changes formatting and
regresses syntax on ledger005, whereas the feedback continuation removes the
extraneous filter. This is a descriptive paired difference, not demonstrated
causal feedback benefit or a functioning corrected program. No actual
unknown-identifier-to-arity runtime transition occurred: that path is covered
by a synthetic reviewer regression test, not observed pilot evidence.

Runtime diagnostic categories: CHILD feedback15 JSON-decode self-transitions
and1 schema self-transition; no-feedback15 JSON-decode self-transitions and
1 schema-to-JSON-decode regression; BASE4 JSON-decode,9 schema,2 unknown-name,
1 expression-syntax self-transitions. Zero improving runtime-category transitions.

## Why all-zero BASE is not a pure capability result

The prompt asks for an expression JSON object on the last line but omits the
literal required key/schema. BASE has whole-response JSON in32/32 responses,
yet26/32 use the alternate key and8/32 hit last-line JSON decoding failures
(overlapping counts). CHILD feedback whole-response JSON is28/32 while30/32
public attempts hit last-line decoding failures. This documents an interface
mismatch across BASE and CHILD, rather than an adapter-only failure.

However, extracting the whole JSON and accepting the alternate key only for
inspection yields zero expressions satisfying the original allowed AST across
all96 responses. Undefined names, literal arrays, unsupported syntax/helpers,
arity and malformed expressions remain. Therefore formatting alone does not
explain every failure. No extracted expression was executed or rescored; the
frozen scorer and success-candidate columns remain unchanged.

## Evidence and limitations

Native root: `/localhome/local-rohing/orch_r109_l1_public_feedback_20260915_attempt2`.
Native descriptive table: `/localhome/local-rohing/orch_r109_l1_public_feedback_review_20260915_1647/results_v2/NATIVE_REVISION_TABLE.json`,
SHA `ccf648ccbd08fd4e0f3446dc7b5fb4f3953e0d81801fa9cbb9a857dbf41dcad8`.

Reviewer V1 is preserved. Its identifier/literal-removal counts incorrectly
treated a failed after-expression parse as an empty identifier set. V2 requires
both ASTs to parse; regression tests cover both false-removal paths. Even V2's
one removed old identifier in BASE is only substitution, not a functioning fix.
The frozen collection and its scores were never edited by either reviewer.

18 local unittest tests PASS (12 collection +6 reviewer); native collection12
and reviewer6 PASS. Public-feedback whitelist excludes expected/correct/success,
gold and hidden examples. No parents/teacher/FINAL reads, no fit, no ingestion.
Behavioral changes are present; general feedback learning, persistence,
metacognition and capability gains remain unproven.
