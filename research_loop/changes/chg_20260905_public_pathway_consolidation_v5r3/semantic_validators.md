# PPC5r3 pure semantic validators

This file is normative pseudocode. Implementations must translate each function
literally and both independent implementations must agree on every golden
vector. `FAIL(x)` rejects the whole object with code `x`; it never coerces.

## Common

```text
canonical(x): schema-valid x -> canonical bytes defined in machine_contract §1
digest(contract,version,x): domain-separated SHA256 defined there
assert_sorted_unique(xs,key): FAIL unless keys strictly increase
assert_hash(x,h): FAIL unless digest(contract(x),version(x),x without h) == h
```

`validate_id` applies the regex and forbidden-substring casefold rule.
`validate_semantic_table` validates all candidates, strict candidate-ID order,
unique candidate and record IDs, nonempty public bytes, and table hash.

`validate_read_response(response,table)`:

```text
if status == FOUND:
  all four IDs non-null
  exactly one table row has the same subject/relation/object/record IDs
else:
  all four IDs null
```

## State and transition

`validate_state` requires TERMINAL iff public_view is null and terminal_reason
is non-null; nonterminal iff view exists and reason is null. View and private
controller schedule, phase, slot, and queue-count invariants must match the
following table:

| mode | controller phase | public slot | private requests | committed action |
|---|---|---:|---:|---|
| AUTHENTIC | INTERLEAVED | 0..L | 0 | null |
| ONE_SHOT_READ | PLANNING_READS | 0..L | slot | null |
| ONE_SHOT_READ | FLUSH_READS | L | L | null |
| ONE_SHOT_READ | COMMIT | L | L | null |
| OPEN_LOOP | PLANNING_READS | 0..L | slot | null |
| OPEN_LOOP | COMMIT_BLIND | L | L | null until ACT accepted |
| OPEN_LOOP | FLUSH_AND_EXECUTE | L | L | non-null |

Any other cross-product fails. `path_length` is zero outside D1B and 2 or 3
inside it. Consecutive errors are 0..2 in a nonterminal view; the third creates
the terminal event rather than a state with value 3.

`validate_operation_envelope` requires operation non-null iff parse status is
PARSED; raw output hash non-null unless MODEL_MISSING; adapter hash is always
null for THINK/DREAM/ACT. `validate_operation_result` uses exactly one payload:

| status | required non-null | all other payloads |
|---|---|---|
| SUCCESS READ | read_response | null |
| SUCCESS ACT | outcome | null |
| SUCCESS PREDICT | none | null |
| ERROR | error_code | null |
| TERMINAL | stop_reason | null |
| SLOT_ACK | slot_ack | null |

`validate_event(prev,event)` checks ordinal increment, prior hash, every named
component hash, non-increasing budgets, exact debit difference from the
transition table, post-state ledger hash equals event hash, and event hash.
`validate_terminal_replay` requires every later call to return identical stored
terminal bytes and leave event count/budgets unchanged.

## DREAM, context, evidence, and artifacts

`validate_dream_receipt`:

| status | result | required meaning |
|---|---|---|
| VALID | nonempty PUBLISH | 1..K valid IDs |
| PUBLISH_EMPTY | empty PUBLISH | zero IDs, null focus |
| ABSTAIN | ABSTAIN | declared reason |
| DREAM_INVALID_OUTPUT | null | invalid raw output hash retained privately |
| DREAM_MISSING_NO_RETRY | null | no raw output |

`validate_context_install` recomputes its named policy. VALID requires installed
true, non-null render hash, and exact ordered IDs/focus. VALID_EMPTY requires an
installed canonical empty render. ABSTAIN, DREAM_INVALID_OUTPUT, and
DREAM_MISSING_NO_RETRY require installed false, empty IDs, null focus/render.
CONSTRUCTION_FAIL and RUN_INVALID never enter reduction as observations.

`validate_projection` recomputes the first failing nominee predicate in the
exact machine-contract order. A null first_failure requires one eligible exact-
tuple representative; a non-null failure requires null representative.

`validate_adapter_manifest`:

| status | artifact hash | rows | finite/structural |
|---|---|---:|---|
| VALID | non-null | >0 | both true |
| VALID_EMPTY | null | 0 | both true |
| TRAIN_FAILED | null | any | at least one false or trainer failure receipt |
| MISSING | null | any | assigned external artifact absent |
| RUN_INVALID | any | any | integrity mismatch; claim blocks |

All nonempty corpus, row, token, update, shape, recipe, base, tokenizer, mount,
and artifact hashes recompute. Atomic publication exists iff status VALID.

## Stage outcome and analysis

`validate_stage_outcome` recomputes the exact row in
`analysis_contract.status_rules`. CONSTRUCTION_FAIL and RUN_INVALID require
claim_blocker true, downstream false, endpoint NONE_BLOCKED. Missing statuses
require missing true and endpoint ADVERSE_BOUND. All policy-outcome statuses
require missing false and endpoint OBSERVED; TRAIN_FAILED installs null,
continues adapter-off, and preserves actual resource dose.

`validate_observation` requires analysis_value equal raw_value when not missing;
when missing it equals the arm- and direction-specific adverse endpoint bound.
Blocked outcomes create no observation. Every assigned unit has exactly one
observation or one claim-blocking receipt.

`validate_contrast`, `validate_assay`, and `validate_holm` recompute the formulas
in `analysis_contract.json` without stochastic approximation. `validate_claim`
applies global blocker precedence, requires every T01–T14 receipt plus the
claim-local cells/tests, and emits either exact registered text or BLOCKED.

## Authority

`validate_authority_transition(prev,next)` recomputes the ordered stage and all
requirements in `authority_contract.json`. The first two stages must have
reachable=false. PRE_MODEL_EXECUTION may have true only after every listed hash,
seal, reviewer, advocate, and separate human run-ratification binding passes.
RUNTIME_VALIDITY and PRE_SCIENTIFIC_CLAIM require the immediate passing
predecessor. `validate_preflight` denies unless exact run-lock, executable,
authority, dispatch-class, and immediate-state hashes match. A denied preflight
starts no process.
