# Parenting alignment core — final inference-only handoff

2026-09-13. **EDITSTOP.** Only the core, its test and this handoff are changed.
No repository/old-module/runner edits, Git, network, model, native tokenizer,
native lifecycle, GPU, collector or launch operations. No writer is implemented.

## Final file pins

- `/tmp/astra_parenting_alignment_core_20260913.py`: SHA256 `71311d3d9add1f485289c6ee6824ef758393193ee05bcc088674d12697b11010`.
- `/tmp/test_astra_parenting_alignment_core_20260913.py`: SHA256 `639bf348f931cf5223e71093ce7a6c740785cd1b43207236bbd9bf45f0d17195`.
- `/tmp/astra_parenting_alignment_core_20260913_handoff.md`: SHA256 returned separately; not embedded self-referentially.
- Authoritative amended protocol: `research_notes/astra_memos/ASTRA_PARENTING_ALIGNMENT_DEV_2026-09-13.md`, SHA256 `5c53d6aa850b3a3a409c255ab9b28ce3b090f7325f35688437e42a86b1cccce5`.

This adopts the amended inference-only protocol, not the analysis note's writer
or post-SLEEP proposal. The initial protocol pin was replaced before any native
assay output. Native preparation/authorization remain Main's responsibility.

## LOCKED Parfit API

```python
load_dependencies(source_root=SOURCE_ROOT, *, protocol_path=PROTOCOL_PATH,
                  parented_path=PARENTED_PATH) -> deps
build_manifest(dependencies, *, prior_task_ids=(), prior_ids=None) -> manifest
run_phase(state, backend, deps, *, binding=None) -> capture
replay_validate(capture, deps) -> audit
summarize(captures, deps) -> summary

# Equivalent wrappers also provided:
run_state(state, backend, *, dependencies, binding=None) -> capture
audit_capture(capture, *, dependencies) -> audit
```

Parfit's current base API is supported directly. `prior_ids` and `prior_task_ids`
are alternate names; supply only one. The prior inventory is an explicit list
of unique strings. Main's prepared manifest binds that external inventory;
the capture's internal manifest hash uses the default known-ID inventory.
The lifecycle separately binds its full prepared manifest, as its current code
already does. A default inventory is not proof of unseen historical exposure.

States: `perception_seed0_ALIGNED`, `perception_seed0_SWAPPED`,
`perception_seed0_NO_PARENT`, and the analogous seed1/seed2 names. Native
binding, when supplied, includes `producer` with original `learner_seed`,
`parent_plan_sha256`, `adapter`, `adapter_files`; the core rejects descendants.
Optional other lifecycle identity fields are retained unchanged. Without a
binding, the capture declares the original root but does not claim native proof.

Requests contain `request_id`, `state`, `kind`, `episode_id`, `block_index`,
`task_index`, `input_messages`, `max_output_tokens`, `temperature`, `seed`,
`source_execution_sha256`, `contact_sha256`. Kinds/caps are
`restate:160`, `wake:256`, `record:384`; temperature0 and generation seed0.
No family, correct operation, expected NOTE, rule identity or score is passed
in request metadata. State/identity metadata is not part of model messages.

The backend returns exact `request_id`, `state`, `raw`, `finish_reason`; optional
native receipt metadata may be preserved, but is not required. The pinned
formation `_call`/event contract is reused. BaseException native faults propagate;
ordinary callback failures are recorded. Transport source/state mismatches stop.
Malformed model JSON, bad restatements, length finishes and low scores do not
abort or resample the assay. No second collector or model call occurs in replay.

Capture fields: `schema`, `state`, `seed`, `arm`, `phase="inference"`, `binding`,
`original_root`, `manifest_sha256`, `events`, `contacts`, `records`, `readout`,
`summary` (same readout copy), `capture_sha256`, `updates=0`, qualification and
false native/automatic-pass/fit-authorization flags. Every scheduled task has
a record slot, including execution failure and `record=None`.

## Frozen schedule and real public world evidence

- Seeds0/2 P-C-P-C; seed1 C-P-C-P. Four tasks/block, sixteen/state. Seed1 reverses
  structural variant delivery:1,1,0,0 versus0,0,1,1. Each lesson arm sees each
  identical lesson string twice. Ordinary task bytes/order match all three arms.
- P blocks contain all four prior/outcome Boolean combinations. C blocks contain
  both latest outcomes crossed with both display orders; priors are null, so
  prior comparison is uninformative. Chronology comes from receipt times, not
  display position. First/second blocks match these structures, not claimed
  model difficulty. The2:1order assignment remains confounded with seed.
- Earlier events are explicitly labeled **harness-provided, not child actions**.
  A deterministic prospective action search calls actual frozen RuleGame
  `evaluate`; every candidate/outcome is logged in the schedule, and only
  genuinely returned outcomes enter public receipts. No hidden-rule accessor
  is called by this core. Desired balancing labels and private world IDs never
  enter prompts. There are72selected public receipts and579CPU schedule probes.
- Each valid typed child action executes exactly once against its task's world.
  Its returned receipt uses a distinct child/state-bound ID. Invalid action
  produces no invented outcome and no replacement record call. All tasks reset
  world/history; no earlier task output influences task construction.
- Opaque `pa-` IDs are SHA256-derived from schema/kind/design coordinates. The
  manifest enumerates360distinct task/address/private-world/public-receipt/
  potential-child-receipt IDs, and rejects overlap with supplied prior IDs and
  known earlier formation/parenting IDs. New child IDs differ between siblings.

Manifest pins (default external prior inventory empty):
- `manifest_sha256`: `21901cfde3641ab84e9f932290932a9b83ce49ff85df57c60b563397242fa78b`.
- Canonical schedules SHA256: `c2aade94ab4754819397034df1fff3d832ff9ca908576e088ccc878b18bf9942`.
- Canonical selected public receipt map SHA256: `01096af7e4e631230872d01a0d94aa87364f750784ce2f1273fcc5cf077160ee`.

Hash serialization throughout this core is compact sorted UTF8 JSON,
`ensure_ascii=False`, finite values, **no terminal newline**. Capture/manifest
hashes omit their own hash field. File hashes are ordinary SHA256 of exact bytes.
The lifecycle must bind the core file pin as well as manifest/schedule pins.

## Exact visibility and parser contract

Restatement sees only its delivered fixed lesson and common instruction.
RESTATE is scored against that delivered lesson, including SWAPPED. Its raw
text is forwarded unchanged even when wrong or truncated. Application/record
context contains only the current raw restatement and current task; recording
also sees its current raw pre-action generation and real new receipt. The
harness never separately inserts fixed lesson text after restatement. If the
child copies the lesson, those child-authored bytes are retained, not filtered.
NO_PARENT has no input note/contact/restatement. New blocks replace old notes.

The common pre-action instruction requests a relevant-state NOTE and an action;
it does not name comparison, recency, P/C, ALIGNED/SWAPPED or a correct binding.
It asks for JSON keys `note`, `prediction` (Boolean), `action` with `kind="TRY"`
and `values` (three strict integers between-9999and9999). The public context
contains only legitimate raw receipts/chronological markers and opaque address.

Canonical P NOTE fields: `predicted`, `observed`, `relation`; optional `receipt_id`
must match if present. C NOTE fields: `receipt_id`, `try`, `observed`. Arbitrarily
mixed **predeclared** aliases are accepted:
- predicted: `predicted`, `prediction`, `prior`, `earlier_prediction`;
- observed: `observed`, `observation`, `outcome`;
- relation: `relation`, `comparison`;
- receipt_id: `receipt_id`, `event_id`, `id`, `latest_receipt_id`;
- try: `try`, `action`, `values`; array or `{kind:"TRY",values:[...]}`.

Relation aliases: matched/match/same/equal/agreement and
mismatched/mismatch/different/unequal/disagreement. Conflicting synonyms,
unknown NOTE keys, wrong types, duplicate JSON keys, nonfinite values and fences
are explicit parser/schema failures. Whitespace/key order are accepted.
Typed wrong values are binding errors, separately from parse errors. Canonical
serialization and canonical NOTE field form remain independent diagnostics.
PROCESS_USE depends on the task-bound NOTE, not action-format success; a correct
NOTE with a missing/malformed action can pass PROCESS_USE but not EXECUTED/FULL.

Record keys: `address`, `source` (the public-operation NOTE under the same alias
parser), `event` with exactly `receipt_id`, `try`, `predicted`, `observed`,
`relation`. The record binds the original task address, public operation and
own distinct fresh receipt. The unchanged public event judge checks the child's
new prediction/action/outcome/relation. Earlier/new/sibling receipt splices fail.
P prior/outcome checks are independent of C latest same-receipt checks.

RESTATE is a frozen conservative lexical operation/scope screen; all regexes
and contradiction rules appear in the manifest. It is not an open-ended semantic
judge. Raw text and exact phrase overlap/diversity remain available to expose
that measurement limitation. No parser/alias changes may be made after results.

## Endpoints, feasibility and non-launch boundary

`PROCESS_USE`, `EXECUTED`, `RECORD_FAITHFUL`, `FULL_MATERIAL` use all16scheduled
slots. FULL is precisely process AND executed AND record, not RESTATE. Lesson
RESTATE denominator4; NO_PARENT RESTATE/denominator/mask are null, not failure.
Readouts include item masks, per-field errors, call/finish/uncalled counts,
canonical form, raw uniqueness, exact-word-span overlap, byte costs,8vs8delivery
counts and4vs4family-delivery strata. Native token/time costs remain runner-owned.
Individual P/C token lengths need not match; never pad or change lesson meaning.

`summarize` replays every supplied capture before reducing. Missing cells give
an incomplete gate, never pass; duplicate cells fail. Full9cell summaries report
all root counts, differences, seven component masks and their conjunction:
1. RESTATE>=3in at least2roots;
2. A−S PROCESS_USE>=4in at least2roots;
3. every A−S strictly greater than-4;
4. A−N PROCESS_USE>=2in at least2roots;
5. every A−N at least-2;
6. second-delivery PROCESS_USE>=first in at least2roots;
7. aligned FULL_MATERIAL>=8in at least2roots.

Every result has `fit_authorized=False`, updates0; no fit/launch function exists.
`feasibility_pass=True` is report-only, never authorization. Partial per-seed
collections remain available for later all-three-root independent reduction.
Maximum36/36/32calls per seed,104total/seed,312campaign,0parent-model calls.

The contrast concerns immediate task alignment of the fixed-lesson-to-raw-note
package. SWAPPED may interfere; absolute A/S/N and both contrasts are retained.
It does not identify restatement mediation, persistent parenting, improvement,
amortization, autonomous learning, H1/H2 or adoption of any proposed writer.

## CPU validation and remaining work

Command: `python3 -B /tmp/test_astra_parenting_alignment_core_20260913.py`.
**19tests PASS,2.612seconds.** Uses actual frozen CPU RuleGame and scripted child
responses only. No native/model/tokenizer library is invoked. Tests cover:
source/protocol pins; namespace collision; actual prior-world re-execution;
counterbalanced structures; all9states/312call maximum; alignment multiset and
task order; delivered RESTATE; answer-free lessons; parent removal/task-block
resets; noncanonical/alias success; generic prose refusal; P/C binding/splicing;
invalid/missing actions and retained slots; restatement failure not filtering
or FULL gate; length/ordinary failures without retry; propagated native faults;
resigned missing/extra/modified call/world/score replay; exact threshold edges;
positive report-only gate; partial cohort; strict JSON and original-root binding.

Additional in-memory deterministic positive-fixture hash exercise uses
`Fixture(mode="following_note")` on all9states:
`4046ee66229678078c54ce74d53749dc06930f5025828eb87e9a0ba85b81c824`.
This hashes the canonical state→capture mapping. Its scripted gate passes with
`fit_authorized=False`; this is **test evidence, not observed child behavior**.
No fixture output files were written outside the owned three-file scope.

Unchanged frozen source pins rechecked:
- Parented core `68ef29fcc162dbbf5fe1becf4c09b86ed5bc1f8a79e373276dd8ba3cda88e688`.
- Formation V2 core `b023a4321d0a20e465c96914316a730fbb2dd897c11369a9eb62d2d8f1248ef5`.
- RuleGame `88304996b00837ad1855e8a6661aad39e64f3beb0c0ab4491b63119e797226f3`.
- Public diagnostic interface `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`.

Main/Parfit own actual root inventories/model/tokenizer identity, full prior-ID
inventory, static/dynamic native context checks, cold per-arm processes, leases,
controller3600/collection180 budgets, raw native custody, once-only collection,
actual token/time costs and any launch decision. Direct agent messaging is not
available; coordination used Main's relay and read-only Parfit handoff/code.
No Parfit runner/tests were executed or edited by this worker.
