# PPC5r2 — minimal public-pathway consolidation protocol

Status: proposal only. These bytes authorize no implementation, model call,
training, canary, GPU execution, behavioral treatment, or scientific claim.
PPC5r1 and its consensus are provenance only; this file is standalone.

## 1. Question and boundary

PPC5r2 asks four non-substitutable questions:

1. **D1A supported selection.** Does an isolated evidence-gated READ-LoRA
   improve selection of a supported public record when the complete semantic
   candidate table is supplied?
2. **D1B recurrent path use.** Does a frozen policy use every returned edge in
   a presealed decisive length-two or length-three path to improve a later
   action?
3. **D1C DREAM context value.** Does one frozen same-model DREAM call select a
   working context that improves subsequent action relative to total,
   prospective recipient-local context policies?
4. **D1D DREAM-to-SLEEP selection value.** Do roots selected by frozen
   same-model DREAM yield more useful evidence-gated READ training rows and
   downstream action than total, prospective recipient-local root policies?

The base THINK, DREAM, and ACT weights are byte-identical and frozen. The only
learned life artifact is a clean-base READ-only LoRA mounted in an isolated
candidate provider. D1A is candidate-conditioned discrimination with external
semantic support, not closed-book storage or autonomous recall. The four-way
finite label is only an intersection of four separately passing component
claims, never a causal mediation claim.

PPC6 and later may test learned decision policy, rich free-form cognition,
repeated sleeps, schema compression, long-life learning, parenting, and
populations. They have no graph, evidence, authority, implementation, or
promotion edge here.

## 2. Authority and canonical objects

The normative proposal inputs are `human_directive.txt`, `protocol.md`,
`contracts.schema.json`, `claim_dependency_map.json`, `scope_proposal.json`,
and `change.json`. `AGENTS.md` governs the workflow. The architecture schemas
and intake code are validator dependencies. PPC5r1 consensus is provenance
only. No unlisted file contributes a default or permission.

All contract instances validate against `contracts.schema.json`, reject
unknown fields, and serialize as UTF-8 canonical JSON with sorted keys,
compact separators, and one trailing LF. Arrays retain the order declared by
their construction algorithm. Any invalid instance is rejected as a whole.
Public IDs are opaque, remapped per item, and contain no role, condition,
model, target, or truth substring.

Every unit has one private role before any model-visible bytes exist:
`ACQUIRE`, `PROBE`, or `STATIC`. Only closed direct public ACQUIRE observations
committed before a sleep boundary may support a positive training row. PROBE,
future, open, target-derived, cognitive, DREAM, scorer, policy-target, and
hidden-truth material is permanently writer-ineligible.

## 3. Minimal public THINK machine

The machine has `INITIAL`, `RUNNING`, and `TERMINAL` phases. Its closed state is
`ppc5.state.v2` in `contracts.schema.json`. Initialization verifies all static
hashes and starts with empty ordered workspace and opened-record arrays, no
live prediction, locked remaining budgets, zero call ordinal, the initial
public world state, and no terminal reason. Failure before dispatch produces
`TERMINAL(INVALID_CELL)`.

One model call emits exactly one operation:

```text
READ(subject_id, relation_id)
PREDICT(action_id, direction, value_bin)
ACT(action_id)
STOP(reason)
```

There are no branches, subgoals, hypotheses, revisions, backtracking, DREAM
requests, free-text notes, citations, or learned control operations in PPC5r2.
DREAM is invoked only by the presealed assay schedule.

Transition precedence is total:

1. A call after terminal returns the identical terminal receipt and changes
   no state or budget.
2. Before dispatch, verify state, cell, model, tokenizer, manifest, and mounted
   artifact hashes. Failure is `RUN_INVALID` and terminal.
3. If no call remains, append forced `STOP(BUDGET_EXHAUSTED)` and terminate.
4. Dispatch once and debit one call plus actual locked tokenizer tokens.
   Provider/model absence is `MISSING_NO_RETRY`; token overflow is
   `TOKEN_LIMIT`; neither retries.
5. Parse one complete operation. Parse failure is `PARSE_ERROR`.
6. A named READ or ACT attempts its logical debit before semantic validation;
   zero pre-debit budget yields `READ_LIMIT` or `ACTION_LIMIT`.
7. Validate fields, finite domains, public references, prediction binding, and
   environment action validity in that order.
8. READ executes one candidate-provider request and appends exactly one public
   response before the next model call. PREDICT replaces the live prediction.
   ACT requires an exact action match to the live prediction, consumes it,
   executes once, and appends the public outcome. STOP is terminal.
9. Errors append their canonical public error receipt. The third consecutive
   error forces `STOP(ERROR_LIMIT)`. Any successful operation resets the
   consecutive-error count.
10. Every transition appends one canonical ledger event and updates the ledger
    hash. Cold replay from initialization must reproduce every state and byte.

`PREDICT` is registered, not necessarily calibrated: `direction` is
`INCREASE|DECREASE|SAME`; `value_bin` and legal actions are run-locked finite
domains. The action outcome records the realized direction and value. This
preserves an expectation/outcome ledger without claiming a learned verifier.

## 4. READ provider and typed response intervention

The semantic candidate table contains only candidate ID, record ID, subject,
relation, object, and public record bytes. It contains no role, condition,
target, truth, score, rank, future, equivalence, or probe field. Every provider
scans the complete table in canonical candidate-ID order.

`READER_LORA` forced-scores the exact run-locked candidate response sequence
under the mounted adapter and selects maximum score with candidate-ID
tie-break. `ADAPTER_OFF` uses the identical provider with no adapter.
`WRONG_LIFE_ADAPTER` mounts a prospectively assigned compatible donor adapter.
`OUTCOME_SHUFFLED_READER` uses the identical recipe after a presealed
within-life outcome permutation. `RAW_RAG`, `FULL_CONTEXT`, `EXPLICIT_GRAPH`,
and `BASE_AGENT` are descriptive reference cells; only core cells named by the
claim map gate release.

RAW_RAG uses full-table run-locked embedding cosine and threshold, then
candidate-ID tie-break. EXPLICIT_GRAPH performs only exact or reverse-exact
subject/relation lookup and returns NOT_FOUND for partial or paraphrase cue
families by declared design. FULL_CONTEXT presents the canonical table within
its locked allowance. BASE_AGENT receives no acquired table. No reference is
an oracle outside its declared cue family.

Provider scoring and selection never see a path target or intervention. A
separate non-model `RESPONSE_INTERVENTION` stage runs after selection and before
public emission. It receives only a sealed typed assignment keyed by condition,
item, target, exact query hash, and selected-response hash. `AUTHENTIC` emits
the selected response unchanged. `CUT` emits canonical NOT_FOUND. `TWIN` emits
the presealed directional-binding twin with equal schema, byte-length class,
locked-token count, logical debit, and allowance. `SHAM` applies the same
substitution machinery to a sealed nonpath response whose change preserves the
registered correct action. Nonmatching assignments are no-ops. The stage never
sees hidden truth at runtime.

The public response exposes only contract, status, subject, relation, object,
and record ID. It never exposes score, rank, provider, adapter, condition,
candidate ID, latency, provenance, target, or diagnostics.

## 5. Frozen DREAM and reversible context

At a presealed context-pressure snapshot the harness makes exactly one charged
frozen same-model DREAM call. The input includes only causally prior public
ledger records inside a fixed allowance, current public world state, live
prediction if any, and the allowed record-ID catalogue. It excludes roles,
conditions, hidden truth, probe/future outcomes, targets, provider scores,
writer eligibility, and downstream treatment assignments.

DREAM returns either `PUBLISH(retained_record_ids,next_focus_record_id)` or
`ABSTAIN(reason)`. Published IDs must be unique visible IDs in public commit
order and next focus must be null or retained. Publication creates no fact,
answer, target, or evidence. It is a reversible view over the append-only
ledger. Invalid output is `DREAM_INVALID`; missing output is
`DREAM_MISSING_NO_RETRY`; neither retries.

D1C clones the pre-call state and shares this one authentic output:

- `AUTHENTIC_DREAM_CONTEXT` installs valid PUBLISH, the valid empty view for
  PUBLISH_EMPTY, and no view for ABSTAIN or failure.
- `RECENCY_CONTEXT` selects the most recent allowed records up to the fixed
  allowance, independently of authentic output.
- `PERMUTED_CONTEXT` selects the same prospective number from a presealed
  recipient-local hash permutation, independently of authentic output.

All branches continue through the identical minimal THINK schedule and every
assigned life remains in ITT. Leave-one-out retained-item cuts, if explored,
are descriptive only and cannot release D1C.

## 6. Evidence gate, DREAM-to-SLEEP projection, and training

Private `root_provenance` maps record IDs to public source-event IDs and opaque
equivalence-class IDs. Private `writer_eligibility` supplies immutable role,
close event, commit ordinal, source-channel kind, target-derived bit, and final
eligibility. Neither contains truth, target, answer, score, rank, condition, or
model output. They are forbidden from provider scoring and model input.

For every DREAM-retained nominee, `dream_to_sleep.v2` checks in this exact
first-failure order: record existence; visibility to that DREAM call; ACQUIRE
role; closed item; pre-boundary commit; non-PROBE and non-future lineage;
non-target-derived; direct public environment observation; direct-relation
shape; source hash; final eligibility. Rejection occurs before equivalence
lookup. Only an admitted nominee opens its equivalence class. The class is
built target-blind from the exact canonical tuple `(subject_id, relation_id,
object_id, public_record_bytes)` over eligible records; its representative is
the lexicographically least eligible record ID. Representatives are
stable-deduplicated in nominee order.

D1D uses three total root policies over the same pre-call eligible snapshot:

- `DREAM_TO_SLEEP`: the valid authentic admitted representatives, possibly
  zero.
- `RECENCY_TO_SLEEP`: eligible representatives in reverse source-commit order
  up to fixed capacity.
- `HASH_PERMUTED_TO_SLEEP`: eligible representatives in a presealed
  recipient-local hash order up to fixed capacity.

Controls never use authentic cardinality, rank, slot, or donor output. Empty,
abstained, missing, invalid, projection-rejected, or zero-eligible states remain
assigned zero-dose outcomes; there is no fallback, retry, reassignment, or
realized-dose matching.

The SLEEP writer regenerates only atomic `(READ request, exact supported public
response)` rows from admitted representatives. It makes one deterministic pass
over every admitted row in canonical order, subject only to the presealed
capacity. It never cycles, downsamples, pads, paraphrases, adds rationale, or
uses cognition/policy targets. Training always starts from the identical clean
base and uses the later locked recipe. Validation either atomically publishes
one adapter or publishes none. Actual rows, tokens, updates, rank, bytes,
latency, energy, and cost are treatment dose/outcomes, never forced equal.

The wrong-life donor population and identities are sealed before any model or
training call. Assignment is one-to-one without reuse, reciprocal pairs,
cycles, or adaptive replacement. Base architecture, tokenizer, adapter shape,
recipe family, and mount interface must match. Impossible matching is
CONSTRUCTION_FAIL before recipient assignment; an assigned donor failure is
MISSING without replacement; hash or shape mismatch is RUN_INVALID. Only typed
adapter bytes cross lives—never ledger, IDs, roots, answers, prompts, or
workspace bytes.

## 7. Assay construction and interventions

D1A uses target-blind ACQUIRE/PROBE splitting and the complete public candidate
table. Its primary endpoint is the equal-weight recipient-life mean of correct
supported candidate selection; false selection and NOT_FOUND are safety gates.

D1B constructs a directed multigraph only from admitted direct public atoms
after target-blind alias canonicalization. It enumerates all simple directed
paths up to the locked READ budget in lexicographic edge-ID order. An item is
eligible only if it has exactly one action-decisive minimal path of length two
or three and no action-sufficient alternate path or subset. Target prompt,
action, and handles are source-disjoint by hash. Otherwise construction fails.

For path length L:

- AUTHENTIC permits exactly L interleaved READ calls, then PREDICT and ACT.
- ONE_SHOT_READ permits exactly L READ-planning calls with returns withheld,
  appends all returns in request order, then permits PREDICT and ACT.
- OPEN_LOOP permits the same L READ-planning calls plus PREDICT and ACT with no
  returns or outcomes visible; it then executes returns and committed action
  with no later model call.

Every path edge receives a separate CUT and TWIN condition; every eligible item
receives SHAM. Any wrong, missing, extra, invalid, or over-budget operation maps
through the common status reducer and remains ITT. D1B releases only when every
edge necessity gate and both recurrence gates pass. Trace or citation analyses
are exploratory and cannot substitute for behavior.

D1C and D1D use the total regimes in sections 5 and 6. One authentic DREAM call
is shared across clones to prevent stochastic-call differences from becoming
treatment. Each status table row binds installed bytes or none, all debits,
receipts, downstream continuation, writer state, evidence state, and reducer
input.

## 8. ITT reducers, multiplicity, and resources

The recipient life is the only sampling unit. The roster is prospectively
constructed; every assigned lower-level unit contributes exactly once in
deterministic item/clone/edge order. CONSTRUCTION_FAIL blocks its dependent
claim before execution. Any RUN_INVALID blocks it after execution. VALID_EMPTY
and zero admitted roots are observed zero-dose regimes. MISSING remains flagged
and the primary estimate uses the adverse endpoint bound over the later locked
finite range; release also requires missingness below the locked limit.

Primary endpoints are:

- D1A: correct supported selection, with false selection and NOT_FOUND gates.
- D1B: normalized action value, with all edge CUT/TWIN, SHAM, ONE_SHOT_READ,
  and OPEN_LOOP contrasts as conjunctive gates.
- D1C: normalized downstream action value.
- D1D: co-primary supported candidate selection and normalized downstream
  action value.

The architecture binds these endpoint forms, finite ranges, denominator and
zero-eligible rules. The run lock binds only numeric range constants, margins,
alpha, life count, power inputs, assignments, capacities, budgets, seeds, and
missingness threshold. The four assay-release hypotheses form one Holm
step-down family. Required gates within an assay use intersection-union logic:
every named gate must pass. The finite label adds no fifth hypothesis and is
released only if all four components release.

Every cell reports inclusive and marginal model calls, tokens, training rows,
updates, adapter bytes/rank, wall time, GPU time, energy when available, and
cost. Resource-normalized and Pareto analyses are sensitivity analyses; no
causal claim depends on exact byte, token, or compute equality. Direct-action
and raw-trajectory LoRA may be descriptive policy comparators in later work but
cannot establish PPC5 supported selection or recurrent-use claims.

## 9. Acceptance stages

The authoritative order is:

1. `pre_ratification_specification`: exact proposal, schemas, claim map, two
   fresh interpretations, adversarial critique, consensus, and exact human
   architecture/scope ratification. No implementation exists before this.
2. `post_ratification_pre_static_seal_conformance`: implement only ratified
   contracts and pass CPU/no-model schemas, golden vectors, transition replay,
   visibility/noninterference, reducer fixtures, and run-lock-schema tests.
3. `pre_model_execution`: populate and hash-bind a run lock; obtain two
   independent static seals, fresh reviewer and advocate decisions, and a
   separate exact human run ratification. No CPU or GPU model/tokenizer call,
   canary, training, or behavioral dispatch is reachable earlier.
4. `runtime_validity`: execute the canary and registered runtime perturbation
   checks under the exact run authority. Any integrity failure is RUN_INVALID.
5. `pre_scientific_claim`: complete all-assigned audit, resource manifest,
   reducer recomputation, multiplicity procedure, adapter-off/wrong-life/
   shuffled controls, and claim-map audit before releasing literal text.

The old architecture-change schema exposes only `implementation`, `gpu_run`,
and `scientific_claim` in its `required_before` field. For this proposal,
`gpu_run` means **any model/tokenizer inference or training on CPU or GPU**;
the finer five-stage enum is normative in this protocol and the contract
fixtures. No experimental exploratory job outside this change supplies evidence
or authority to PPC5r2.
