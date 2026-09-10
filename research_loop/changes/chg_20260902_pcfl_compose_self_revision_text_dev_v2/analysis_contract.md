# v2 analysis, Stage-1 gate, and terminal-status contract

`gate_receipt.schema.json` is the operative Stage-1 evidence grammar.  This
document defines the cross-object reductions that JSON Schema cannot express.
All reductions use literal row and receipt IDs from the sealed assignment
manifest.  They run without inspecting opaque text.  Missing, duplicate,
wrong-kind, wrong-ID, unresolved, noncanonical, or schema-invalid evidence
invalidates the gate artifact; it is not coerced to a favorable Boolean.

## Orthogonal row status and denominators

The canonical endpoint key is `(root_id,family,z_side,h_or_q,lane,
condition_id,corpus_variant,target_kind,target_id,goal_twin)`.  Each assigned
row has separate `assignment_status`, `stage_status`, `invocation_status`,
`parse_reducer_status`, `scientific_endpoint`, and `terminal_reason` fields
under `experiment_call_ledger.schema.json`.

A returned, accepted, legal but wrong execution is a completed row with
`scientific_endpoint=0` and `terminal_reason=LEGAL_WRONG`; it is not an
infrastructure failure.  Malformed, timeout, illegal action, unavailable read,
early lock, and abstention are retained zero endpoints.  A Stage-2 row blocked
by the gate is `ASSIGNED/NOT_TRIGGERED/NOT_INVOKED/NOT_APPLICABLE`, with a null
endpoint.  Null is permitted nowhere else for an assigned scientific endpoint.
Every mean and contrast uses assigned rows, never successful-row denominators.

For a fixed factor branch, D4 is the unweighted mean of the four
`(z_side,goal_twin)` endpoints.  A paired contrast is the sum of four
within-identical `(root,h,z_side,target_id,goal_twin)` SELF-minus-control
differences divided by four.  A tie is not strictly positive.  Selected-h
contrasts use `h=0` only and cannot be described as h aggregates.

## Literal Stage-1 evidence map

There is exactly one evidence object for each key below.  Its `receipt_id` and
`receipt_kind` are constants in `gate_receipt.schema.json`.

| gate | exact receipt | derived predicate |
|---|---|---|
| G01 | `s1-g01-construct`, `CONSTRUCT_SCHEMA_RUNTIME_REPORT_RECEIPT` | all 128 root certificates exist; open root, exact-program construct, schemas, executable freeze, and report lint pass |
| G02 | `s1-g02-manifest`, `ROSTER_MANIFEST_COUNT_RECEIPT` | sealed manifest has unique literal call IDs, complete gate bindings, no extra/missing call, and exact 910/2,504/3,414/3,416 counts |
| G03 | `s1-g03-dream1-a`, `DREAM1_A_COMMITMENT_RECEIPT` | for both SAMPLED and ANTIPODE Dream-1 pools, at least one committed candidate has exact A1 and A2 |
| G04 | `s1-g04-revision`, `RAW_A_CAUSAL_REVISION_RECEIPT` | both z sides and both h branches satisfy the causal revision predicate below |
| G05 | `s1-g05-dream2-b`, `DREAM2_B_COMMITMENT_RECEIPT` | all four `(z_side,h)` terminals have exact B1 and B2 and endpoint one |
| G06 | `s1-g06-oracle`, `EXACT_AND_ORACLE_CEILING_RECEIPT` | exact CPU ledger is 28 solver/60 actor/zero model calls and the fixed ORACLE_SCHEMA D1 and D4 endpoints are exact |
| G07 | `s1-g07-actor-self`, `SELECTED_H_SELF_ACTOR_ENDPOINT_RECEIPT` | all four selected-h SELF D4 twin rows return, parse, produce four unique minimal actor USE receipts, keep LOCK local to Think, and match their registered sequence |
| G08 | `s1-g08-goal-twins`, `GOAL_TWIN_PAIR_COUPLING_RECEIPT` | for each z side, the two valid SELF twin trajectories are both registered-exact and have distinct complementary first actions |
| G09 | `s1-g09-self-minus-empty`, `STRICT_PAIRED_ACTION_CONTRAST_RECEIPT` | four-pair SELF-minus-EMPTY success numerator is strictly greater than zero |
| G10 | `s1-g10-self-minus-crossed`, `STRICT_PAIRED_ACTION_CONTRAST_RECEIPT` | four-pair SELF-minus-CROSSED_ANTIPODE success numerator is strictly greater than zero |
| G11 | `s1-g11-sham`, `PRESEALED_SHAM_ENDPOINT_RECEIPT` | sham construction is pre-target/target-independent, all declared nuisance matches pass without an opaque semantic label, SELF-minus-sham is strictly positive, and sham has zero complementary goal-twin redirections |

### G04 causal revision predicate

For each `(z_side,h)` branch, resolve the receipt against the complete fresh
Dream-2 trace and the ordered one-or-two-object committed pre-A Dream-1 pool.
The trace has exactly one charged `RAW_A_EVENT` read and exactly one charged
Dream-1 candidate-parent read. Their resolver ordinals are distinct and both
precede the decisive PREDICT. The candidate read's handle and candidate hash
identify exactly one pre-A pool member; the capability minted by that read is
the PREDICT manifest's `parent_candidate_capability`. The PREDICT has
`decision=REPLACE`, its `decision_provenance_receipt_ids` contains each of the
two exact read receipt refs exactly once, and its manifest `public_handles`
contains the exact raw-A handle exactly once. Terminal COMMIT occurs later,
also has `decision=REPLACE`, selects exactly the new capability issued by that
PREDICT, and repeats the PREDICT decision-provenance array byte-for-byte. The
selected candidate JCS-byte hash differs from every pre-A pool candidate hash.

Within a z-side h pair, the ordered pre-A pool, Dream-1 clone hash, and
treatment-invariant Dream-2 seed-key hash match byte-for-byte, while the two
selected candidate byte hashes must differ. Hash comparison is performed by
the noncognitive integrity process; primary analysis sees only the signed
comparison receipt. This is a mechanical raw-A-conditioned,
branch-responsive selected-object update. It is not semantic appropriateness
and does not establish h-mediated action.

The operation number printed in a report is `resolver_ordinal + 1`; every
stored protocol ordinal remains zero-based.  Thus a stored read at ordinal 3
is reported as operation 4.  No component may compare one-based and zero-based
values directly.

## Total gate and truth table

The sole formula is:

```text
STAGE1_PASS = G01 && G02 && G03 && G04 && G05 && G06
                    && G07 && G08 && G09 && G10 && G11
```

For all `2^11 = 2,048` complete Boolean vectors, only bit vector
`11111111111` returns true.  Every other complete vector returns false.  A
schema-invalid evidence set has no Boolean result and invalidates Stage 1.
`STAGE1_PASS=true` opens exactly the sealed 2,504-call Stage 2.
`STAGE1_PASS=false` writes every Stage-2 assignment as `NOT_TRIGGERED`, emits
the gate/failure-localization receipts, and terminates `HUMAN_REQUIRED`.
There is no third state, tie discretion, repair, replacement, or model panel.

The mandatory static fixture must enumerate integer masks `0..2047` in
ascending order with bit order `G01..G11`, assert one true output at mask 2047,
	and include individual negatives for every G field, strict-contrast ties,
	missing/duplicate/wrong-kind receipt, correct B without exactly one raw-A READ
	and exactly one charged candidate-parent READ, either read at/after PREDICT,
	absent or wrong raw-A receipt/handle provenance, absent or wrong candidate-read
	receipt/parent capability provenance, parent outside the pre-A pool, PREDICT
	RETAIN, terminal RETAIN/ABSTAIN, COMMIT selecting another capability, unequal
	COMMIT provenance, equal pre/post bytes, equal h-selected bytes, unequal paired
	pools, wrong seed/clone coupling, legal-wrong actor output, and sham
	redirection. These exact additions belong in the separately owned
static fixture artifact; this proposal file does not write that artifact.

## First-action and failure-effect endpoints

First-action redirection is one only when both paired rows returned and parsed,
both first USE actions were legal, both full sequences were registered-exact,
and the first actions differ.  A tie, missing or illegal first action,
malformed output, early lock, timeout, or either failed endpoint yields zero
redirection.  Failure-mediated differences are reported in a separate
`failure_effect` field and can never satisfy G08 or G11.

## Independent-q fields

For each q separately, SELF, EMPTY, and OBSERVED use the same
`(q,z_side,target_id,goal_twin)` keys.  No row/control is reused across q and no
positive effect pools q.

`ANY_INDEPENDENT_SUCCESS` is true iff at least one of the eight failure-
inclusive independent SELF D4 endpoints (two q x two z sides x two twins) is
one.  It is reported as a descriptive warning only.  `SPECIFICITY_CONCERN` is
true iff either q has at least three of its four SELF endpoints equal to one,
or both q values separately have strictly positive SELF-minus-EMPTY and
SELF-minus-OBSERVED four-pair means.  These are distinct fields: a singleton
success sets only the first; positive control contrasts for only one q do not
set the second.  Neither field opens a successor; Stage 2 always ends
`HUMAN_REQUIRED`.

Before model work, Stage 0 enumerates, for each q, every four-bit SELF endpoint
vector and every same-q EMPTY/OBSERVED four-bit vector.  It also enumerates all
legal target-blind D4 action sequences by deterministic depth-first expansion
of the public legal menu at each of four simulated prefixes, actions sorted by
UTF-8 JCS byte order.  A declared stochastic policy is the same finite sequence
set indexed by its sealed common seed, not a new outcome-adaptive class.  The
receipt freezes both fields for the full vector product.  Neither field is a
p-value, binomial test, identification claim, prevalence, or population
estimate.

## Report and access boundary

The primary gate and report may consume typed statuses, actions, allowed
provenance, byte-comparison receipts, hashes, and behavioral endpoints only.
They do not consume raw opaque text.  Raw opaque bytes stay sealed until the
primary report bytes and hash are frozen.  Later authorized qualitative access
is logged as exploratory and cannot change a gate, row, denominator, claim, or
example in the primary report.

The only positive wording allowed after all required gates is an exact-root,
selected-h, conditional pre-context DEV record: prospective commitments used a
supplied event-local permutation; fresh Dream-2 produced mechanically verified
raw-A-conditioned branch-distinct selected-object updates; and a predeclared
frozen-corpus intervention changed later executed USE actions on selected-h
rows.  The report linter rejects semantic appropriateness, h-mediated action,
raw-perception/factor discovery, recurrence or efficiency advantage,
replication/generalization, persistence/lifetime/LoRA, external-memory or
A-MEM superiority, and paper efficacy.
