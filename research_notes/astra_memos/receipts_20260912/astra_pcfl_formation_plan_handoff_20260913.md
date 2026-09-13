# PCFL OLD formation/query planner — author handoff, 2026-09-13

Status: EDITSTOP following the CPU checks below. Scoped implementation only;
no scientific claim, rubric, writer, fit, model call, native execution, D binding,
release decision, or change to any previously frozen manuscript file.

## Owned files and byte pins

- `organism_v6/pcfl_vertical_formation_plan.py`
  SHA256 `d7d24fb2b731427f2884056923be05fd828486cbf829bd7771bf0dc4a7b7d734`
- `tests/test_pcfl_vertical_formation_plan.py`
  SHA256 `65d71eabbe90e697383294c95cd4836d16239d7c079618a7bf381706ff054268`
- This handoff: `/tmp/astra_pcfl_formation_plan_handoff_20260913.md`.

Read-only dependencies at validation:

- `organism_v6/pcfl_vertical_dev.py`:
  `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e`
- `organism_v6/pcfl_vertical_prepare.py`:
  `e80266c4241116dc5701f8a394590645229ca089318903545ad064a1835e26a4`
- Existing synthetic contract fixture, `tests/test_pcfl_vertical_prepare.py`:
  `e66832d1891e9f83b7591ee454c5d7d93a3d6007e1df2da4607d9d5d23038862`.

## Stable API and schema

```python
build_plan(cell, actions, link_choices) -> plan
validate_plan(plan, preoutput_sha256) -> True
first_block_slots(plan, preoutput_sha256) -> list[slot]
bind_child(plan, preoutput_sha256, actions, event_raw, link_raw,
           *, contract=None, corpus_id=None) -> binding
source_pins() -> dict[str, str]
```

`cell` is the existing strict `WorldCell`. `actions` is a list of eight exact
caller-predeclared `EXPLORE` strings. `link_choices` is a list of four ordered
two-element lists of opaque chronological EVENT handles; it is not a list of
ideal-edge indices. Neither choices nor actions have defaults. Duplicate or
non-chained pairs and invalid/unavailable actions fail at planning time.

Plan schema `pcfl_old_formation_plan_v1` contains:
`schema`, `purpose`, `stage`, `source_pins`, `cell`, `old_sources`, `actions`,
`link_choices`, `opportunities`, `links`, `expected_bank`, `first_blocks`,
`native_custody_verified`, `execution_contract_valid`, `plan_sha256`.
The purpose is `EXPECTED_STRUCTURE_NOT_CHILD_TARGETS_OR_TRAINING_MATERIAL`.
The seal is the core canonical digest of all other plan fields. Source pins
hash actual planner/core/preparer file bytes. Validation replays construction
and checks both the independently supplied seal and current source semantics.
Determinism is relative to identical cell, exact caller choices, and source bytes.

## Chronology and seam

Each planned action executes through existing `WorldSession(cell, "OLD")`,
`public_affordances`, `explore_prompt`, `explore`, and `event_prompt`. Expected
EVENT fields come from the issued public receipt and chronological fresh handle.
There is no call to `ideal_rows` or construction of raw EVENT/LINK targets in
the planner. Link fields are structural receipt joins from caller choices;
real `admit_link` remains the authority at actual-child binding time.

The source order is exactly `S_L,A,H,S_R,B,Z,S_L,B`:

- e5/r5 is **Z --u--> Y**, not the ideal topology's second B edge.
- e7/r7 is **B's remaining port**, not the ideal topology's Z edge.
- Choosing f1 first makes e7 use f0. Choosing the non-A S_L branch first
  makes the A-reaching event e6; the caller can predeclare e6→e1 accordingly.
- Link opportunity l0…l3 follows the caller's order, not ideal pair numbering.

`first_block_slots` returns detached existing `SLOT_FIELDS` skeletons, `source=None`,
phase OLD, taint AUTHENTIC, IDs s00 onward in request-sorted order. Supports are
lexically ordered by opaque handle, matching existing `materialize_queries`.
The tested complete OLD bank gives 14 EVENT-bearing and 3 LINK-bearing first
blocks (8 EVENT rows, 4 LINK rows). No replay selection, counterparts, tokenizer
measurements, batches, full execution contract, or NEW skeletons are supplied.
Other owners must build those separately, without replacing the first banks.

`bind_child` requires eight actual action strings byte-identical to the plan,
eight exact EVENT spans, and four exact LINK spans. It replays OLD, immediately
calls real `admit_event` after each action, then real `admit_link` for the four
predeclared choices. It uses real `formation_report(required_bank=...)` and
`materialize_queries` only after successful admissions. Returned raw rows and
query targets therefore derive solely from supplied exact child spans. Fences,
missing/extra spans, reordered or incorrect commitments fail without repair.

If `contract` and `corpus_id` are supplied together, the existing execution
validator runs, first slots must equal the presealed skeleton exactly, and
`prepare.validate_formation_binding` checks actual rows/queries. The successful
binding includes admissions, rows, queries, formation report and optional
preparer receipt. No contract means `preparer_binding=None`, not implied closure.

## Checks and limitations

Commands (local CPU only):

```sh
python3 -m unittest discover -s tests -p 'test_pcfl_vertical_formation_plan.py' -v
python3 -m unittest discover -s tests -p 'test_pcfl_vertical_dev.py'
python3 -m unittest discover -s tests -p 'test_pcfl_vertical_prepare.py'
```

Final owned-source run: 13 new tests PASS in 3.898s; core/preparer byte hashes
above matched both immediately before and after that run. Earlier adjacent
checks passed 39 core and 26 preparer tests, with core hash
`03cc4fea5f606f223c15289b4cc86db9f9534bcddb5d3f298b39a0b06b09ab4f`;
that earlier combined run passed 78 tests. Those adjacent results do not certify
the subsequent other-owner core edits.
The new integration fixture replaces only a disposable corpus in the existing
synthetic test contract, then regenerates its test-only replay/batch registries.
No production validator is monkeypatched. Tests cover real chronological e5/e7,
both old bits and alternate port/link choices, exact bytes, deterministic seals,
resealed structural/source tampering, detached first slots, and real preparer
rejection of missing/extra queries, missing/duplicate rows and incorrect fields.

An initial shell command used unavailable `python`; all actual checks use
`python3`. The first new-suite run exposed a test snapshot serializer mismatch
(the core canonicalizer rejects contract floats); the test uses the existing
preparer canonicalizer for contract snapshots. No production semantics changed.
During finalization another owner updated the core's NEW/D definition. A stale,
out-of-scope test expectation that NEW must always raise was removed; the test
now checks this planner's OLD-only EXPLORE receipts and absence of fixture mode.
The planner code was not altered to implement or bypass that definition. The
final rerun used the stable dependency hashes recorded above.

These are synthetic CPU spans, not evidence of child success. The planner's
private cell, expected bank and receipts must never enter child prompts or
supervision. A seal alone cannot prove it existed before outputs: runtime must
retain it independently before generation, retain actual failed calls, verify
native receipts/timing/finish state, and abort on binding failure. This helper
raises rather than caching failures or fabricating replacement records. It does
not prove the supplied spans actually came from a model. Native custody and
execution-contract validity remain false/unverified; source file reads occur
for pins, but there are no writes or model calls in the library. NEW/D is outside
this planner; it neither asserts its resolution status nor enables a fixture
bypass. Other owners must freeze their dependencies before integration rather
than interpreting this handoff as authority to change them.

Only the two owned new repository files and this handoff were authored. Existing
unrelated edits were left untouched; no commit, launch, network call, training,
source/scorer change, or manuscript change occurred in this task.
