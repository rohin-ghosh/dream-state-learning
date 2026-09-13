# Independent bounded DATA review — protocol practice16

Review scope: the fixed material, all16 rendered prompts/targets/source derivations,
handoff, tests, and existing pure RuleGame/parser/record/settings utilities only.
No current formation, birth response audit, live outputs, runtime implementation,
native model/tokenizer, GPU, Git, or network inspected/executed. No source/helper,
test, or case changes. This document alone is the deliverable.

## Verdict for Main

**No public-label or causal-pair error found in the fixed16 data.** Valid as a
supplied-label serialization/public-record/repeated-observation developmental
probe, not induction or hidden-world quiz accuracy. No material repair required
before capturing this inventory. Main retains the launch decision; this is not
a runtime approval or new guard. One reproducible metric interpretation caveat
below should be retained before reporting scores.

## Exact reviewed bytes

- Material `/tmp/astra_birth_protocol_probe_material_20260913.py`:
  `2799efda619f7686db88d7990b203a3c7ad39eb8577228a26402037de16cc66b`
- Tests `/tmp/test_astra_birth_protocol_probe_material_20260913.py`:
  `927c870c1df79fe7f2b93c64562d36375ad18eff5d350625c652105a0b700485`
- Handoff `/tmp/astra_birth_protocol_probe_material_handoff_20260913.md`:
  `0f24d94e9ca4a2fc8b7b243ab20e169d1187856649981faf4240dbad538b5087`
- Regenerated candidate digest:
  `9c680f2010cd11b0116517383281764432f4351628f23059b1c9ee69a283e300`
- Regenerated call-map digest:
  `9f960c825d02a04fad40e86afd2e822ee52e7ea376a4fd198c0c1b74f5c064a6`

## All16 public target checks

Each row below was inspected against its rendered child prompt, not merely the
example target. T/F denote Booleans; no quiz hidden-rule truth was used as a label.

| External case ID | Public basis | Correct requested target |
| --- | --- | --- |
| practice-try-0 | Supplied `[2,5,8]`, T | `PREDICT: T` then `ACT: TRY 2,5,8` |
| practice-try-1 | Supplied `[3,6,9]`, F | `PREDICT: F` then `ACT: TRY 3,6,9` |
| practice-try-2 | Supplied `[-2,0,4]`, T | `PREDICT: T` then `ACT: TRY -2,0,4` |
| practice-try-3 | Supplied `[7,7,1]`, F | `PREDICT: F` then `ACT: TRY 7,7,1` |
| practice-quiz-0 | Unrevealed, zero TRY budget | `ACT: QUIZ ?` |
| practice-quiz-1 | Unrevealed, zero TRY budget | `ACT: QUIZ ?` |
| practice-quiz-2 | Revealed six triples; supplied TFTFTF | `ACT: QUIZ T,F,T,F,T,F` |
| practice-quiz-3 | Revealed six triples; supplied FTFTFT | `ACT: QUIZ F,T,F,T,F,T` |
| practice-record-0 | `[2,1,3]`, prior T, public T | observed true, predicted true, matched |
| practice-record-1 | `[0,9,0]`, prior T, public F | observed false, predicted true, mismatched |
| practice-record-2 | `[5,1,2]`, no prediction, public T | observed true, predicted null, unavailable |
| practice-record-3 | `[1,2,3]`, no prediction, public F | observed false, predicted null, unavailable |
| practice-revision-0 | `[1,3,5]`, prior T, public F | repeat same triple with PREDICT F |
| practice-revision-1 | `[1,3,5]`, prior T, public T | repeat same triple with PREDICT T |
| practice-revision-2 | `[6,1,6]`, prior F, public T | repeat same triple with PREDICT T |
| practice-revision-3 | `[6,1,6]`, prior F, public F | repeat same triple with PREDICT F |

Record JSON has exactly try/observed/predicted/relation fields. Nulls are retained,
not repaired to observed values; the wrong T prediction is retained as mismatched.
The existing record renderer explicitly supplies these facts and mapping. Thus
record success is scaffolded faithful serialization, not unaided extraction.

Public observation generator arithmetic is consistent: rule6 product-even gives
T for `[2,1,3]` and F for `[1,3,5]`; rule7 spread-at-most-four gives F for `[0,9,0]`
and T for `[1,3,5]`; rule8 first-largest gives T for both `[5,1,2]` and `[6,1,6]`;
rule9 sum-over15 gives F for `[1,2,3]` and `[6,1,6]`. Those are source observation
checks only. Target validation uses the joined public action/observation.

Quiz generation uses rule6/rule7 solely to generate the reveal triples/outcome;
the target labels are explicitly supplied, not queried from hidden-rule accuracy.
The existing reveal's `INVALID: quiz needs 6 answers ...` wording is preserved and
the prompt explicitly declares the quiz revealed. This is faithful existing
environment behavior, not a fabricated error or mislabeled successful quiz.

## Partition, causal contrast, and request parity

- All10 generator-backed cases use indices6–9; all6 pure scaffolds have no rule
  index. Forced source EIDs and declared exclusion of0–5 agree. Neutral prompt IDs
  contain no hidden rule names/indices. This establishes the declared generator
  partition, not global tuple novelty, clean lineage, or a sealed test split.
- Each revision pair has identical public fields except outcome. Rendered prompts
  differ only in the observed True/False word. Same prior, triple, public ID,
  remaining budget, tick, and generation seed; targets change only forecast.
  Distinct external case/call IDs remain routing metadata, never prompt content.
- Independent request comparison found precisely call_id/case_id/prompt differing
  within each revision pair. Pair seeds are771149157 and741648210 respectively.
  No source rule, reward, derivation, or example target is sent in requests.
- OFF and AUTH lists are identical in every request field and independent deep
  copies:16 per state,32 total. Role/settings match existing helpers:12 wakes at400
  output tokens and4 records at100 per state; temperature0.7; interaction_v3;
  wake stop `['\n[OUTCOME]']`, record stop `[]`; exclude stop string from output.
  Total output ceiling10400 tokens, not observed dose or input token count.
- TRY/revision targets meet process-v2's single preceding unambiguous PREDICT and
  native action parser checks; quiz targets meet six-label/reveal legality.
  Wrong order, missing/duplicate prediction, multiple actions, emitted OUTCOME,
  wrong/null record substitutions, wrong quiz labels, and incomplete32 mappings
  are covered by passing negative tests. Invalid outputs remain in denominator.
- Stop-string filtering means absence of returned OUTCOME text alone cannot prove
  absence of an attempted world continuation. The data specifies settings only;
  actual backend settings, fresh state/custody, capture completeness and runtime
  isolation were not independently reviewed here. Routing IDs must not be appended
  to prompts, particularly for the causal revision comparisons.

## Metric caveat and minimal disposition

At material lines127–132, public_contract_correct compares full parsed dictionaries,
including the raw `action` string. Consequently both of these valid native grammar
responses return parser_valid=True but public_contract_correct=False, with an empty
failures list:

```text
practice-try-0:  PREDICT: T\nACT: TRY 2, 5, 8
practice-quiz-2: ACT: QUIZ T, F, T, F, T, F
```

This is not a wrong public target or revision confound; canonical serialization is
explicitly requested. It does mean this field is formatting-sensitive rather than
a pure semantic truth score. Similarly record instruction_compliant requires the
particular compact JSON/key order even though the rendered record instruction only
requires a JSON object; ordinary correct JSON whitespace remains public-correct.

**Minimal disposition without code/case changes:** label public_contract_correct as
the existing formatting-sensitive contract measure and instruction_compliant as
reference-serialization compliance; do not interpret either failure alone as a
false public belief or failed causal update. Retain parser validity and raw text.
If Main needs a genuinely semantic metric later, the minimal prospective repair is
compare parsed values/prediction or ordered quiz labels rather than raw action
spelling, leaving exact/reference metrics separate; do not silently change the
frozen reducer after seeing outcomes. No such repair was implemented or required
for the present bounded data capture review.

## CPU evidence and limits

Executed once from `/data/home/rohing/dream-state`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_birth_protocol_probe_material_20260913.py -v
```

Result: **21 tests PASS; unittest elapsed0.044s; exit0**. Existing source regeneration
and all16 target controls passed; the test that disables RuleGame.evaluate/_rule
during output validation passed, demonstrating public-only validation. Printed and
inspected all16 generated contexts/targets/source records; tiny in-memory checks
confirmed OFF/AUTH equality, revision routing/seed/prompt parity, and reproduced the
two whitespace cases above. No extra framework or persistent test file was created.
Tool output is the CPU log; this review records its result without inventing a
separate logfile. No native efficacy/outcome inference is made.

Preserve SOURCE_AUTHORED_PROTOCOL_PRACTICE_NOT_CLEAN and local-byte-only provenance.
No H1/H2/generalG3/P1, clean-lineage, induction, efficacy, or freeze claim.
**EDITSTOP — DATA review only; Main owns all runtime decisions.**
