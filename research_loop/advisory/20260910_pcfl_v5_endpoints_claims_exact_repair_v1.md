# PCFL V5 endpoint, neutrality, and claim-disposition repair — v1

Date: 2026-09-10

Status: **source-only advisory; REWORK; not ratified and not executable**.
This file closes five V4 design defects at the level of exact normative source
direction. It authorizes no preparation-source implementation, deterministic
materialization, fixture/root/data generation, CPU benchmark execution,
model/tokenizer execution, training, LoRA/adapter/checkpoint work, parenting,
GPU use, resource acquisition, scientific claim, release, or submission.

## 0. Disposition

Adopt the definitions below in the next integrated, newly hash-bound proposal.
They close exactly:

- `D-V4-ALGEBRA-SHORTCUT`;
- `D-V4-PRODUCER-SCORER-NEUTRALITY`;
- `D-V4-BRIDGE-TWIN-ENDPOINT`;
- `D-V4-APPLICABILITY-MATRIX`; and
- `D-V4-CLAIM-CLAUSE-DISPOSITIONS`.

The repair adds no model condition, request slot, generated-token allowance,
root, topology, or claim. The roster remains exactly 18 conditions and 501
maximum request slots per root. The algebra decoder and all swap/mutation
cases below are model-free preflight/checker fixtures. The only model-level
algebra probes are the already registered
`TARGET_ONLY_ANSWER_PRIOR_TAPE`, `NO_MEMORY_RECURRENT`, and
`PASSIVE_SIGNATURE_RECURRENT` cells.

## 1. Closed endpoint vocabulary

Every scientific scalar has type `0|1|NA`. `0|1` below means that the exact
cell must contain one observed Boolean value; it does not prescribe which
Boolean. `NA` means structurally inapplicable and is never converted to zero.

For `g in {A,B}`, define the path-behavior family:

```text
PB_g = {
  task_success_g,
  plan_valid_g,
  first_action_correct_g,
  plan_execution_consistent_g
}
```

The definitions are:

```text
task_success_g = 1 iff the phase reaches the released target for g and the
  first terminal command is finish at that target.

plan_valid_g = 1 iff the last accepted pre-relation plan is exactly one
  complete remaining member of the two registered minimum path classes for g.

first_action_correct_g = 1 iff the first relation attempt is the first edge
  of at least one registered minimum path for g.

plan_execution_consistent_g = 1 iff the state-changing relation sequence is
  exactly the declared registered plan, contains no NO_EFFECT, reaches the
  released target, and is followed by finish there.
```

For the connected common-reader treatments, define:

```text
PM_g = {
  relevant_atom_returned_g,
  relevant_link_returned_g,
  public_handle_reused_g,
  connected_constructive_use_g
}
```

`relevant_atom_returned_g` and `relevant_link_returned_g` require a returned
row on at least one registered path for `g`; `public_handle_reused_g` requires
a later command dependency on an earlier explicit grant. The constructive
value is one only when `task_success_g=1`, every state-changing relation cites
its earlier returned atom, every adjacent pair cites its earlier returned
condition-authentic link, all dependencies precede the command, and the
dependency DAG is acyclic. Transformed AUTH links are condition-authentic only
when the transform contract declares them so. No static-context identifier is
a common-reader grant.

The uncertainty/acquisition family is:

```text
UI = {
  separating_choice,
  realized_information,
  belief_revision,
  acquisition_success
}
```

It retains the V4 meanings: target-separating `E0|E1` choice, a public outcome
that makes the target-bit posterior a singleton, an accepted structured change
from `UNKNOWN` to the observed bit before commit, and a correct `c0|c1` commit.
These are public-calibration endpoints, not connection endpoints.

The delayed behavior and connected-carrier families are:

```text
DB = {
  delayed_task_success,
  delayed_plan_valid,
  delayed_first_action_correct,
  delayed_plan_execution_consistent
}

DM = {
  delayed_relevant_atom_returned,
  delayed_relevant_link_returned,
  delayed_public_handle_reused,
  delayed_connected_integration
}
```

The delayed behavior definitions are the path definitions above with target
`D` and the isolated delayed-entry start. `delayed_connected_integration=1`
only if delayed task and plan execution succeed and the constructive trace
uses at least one admitted old atom, one old authentic link, the supplied new
atom, and the supplied new authentic link through earlier explicit grants.

Within-condition path aggregates are:

```text
two_goal_task_success = task_success_A & task_success_B
connected_two_goal_use = connected_constructive_use_A
                         & connected_constructive_use_B
```

The following tempting joins are prohibited endpoint names and are `NA` in
every condition:

```text
full_sequence_task
retention
acquisition_to_delayed_use
online_learning
```

V4's `P`, `U`, and `D` are independent factorial phases. Even under one AUTH
label, no U model receipt parents a D model input. A conjunction across these
independent cells is not a lived sequence, retained write, or learning result.

## 2. Exact algebra-prior falsifier

### 2.1 The registered decoder

The source must include a model-free `ALGEBRA_PRIOR_V4` fixture demonstrating
the precise bypass. It may read only the released start alias, released target
alias/goal label, and fixed relation catalog. It must never read a carrier,
reader return, public event ledger, hidden `h`, condition, split, score,
expected answer, semantic ID, or checker oracle.

Parse `node_alias(S)="n"+lower_hex2(k)` and set `m=k mod 16`. Define:

```text
rho(j,k) = "r" + lower_hex2(j XOR m)

ALG_A_0(k) = [rho(0,k), rho(1,k), rho(4,k), rho(5,k)]
ALG_A_1(k) = [rho(2,k), rho(3,k), rho(4,k), rho(5,k)]
ALG_B_0(k) = [rho(0,k), rho(1,k), rho(4,k), rho(6,k)]
ALG_B_1(k) = [rho(2,k), rho(3,k), rho(4,k), rho(6,k)]
ALG_D_guess(q,upper,k) = [rho(0,k), rho(1,k), rho(4,k), rho(7+q,k)]
ALG_D_guess(q,lower,k) = [rho(2,k), rho(3,k), rho(4,k), rho(7+q,k)]
  where q is selected in {0,1} without reading h
```

For all 32 `k`, both A alternatives and both B alternatives must execute and
score as registered successful paths without any memory. For D, a decoder
without `h` must choose one fixed terminal relation before seeing a separating
outcome; because the route consumes all four relation attempts, it cannot try
both `rho(7,k)` and `rho(8,k)`. Thus its per-`k` twin-minimum D success is
exactly zero. These goldens are an existence proof of the fixed-topology
shortcut, not model evidence and not an extra scientific condition.

### 2.2 Existing-call model probes

`TARGET_ONLY_ANSWER_PRIOR_TAPE` is the pure one-call-per-phase prior probe. Its
path and delayed renderings contain exactly the same system/template version,
public phase-start state, released goal, fixed action catalog, command schema,
four relation opportunities, terminal rule, and phase-level output allowance
as the corresponding registered tape envelope. It receives no memory rows,
reader-return handles, static context, retrieval result, path rank, expected
answer, or score. A fixed inert padding record may equalize a frozen byte/token
envelope; padding cannot depend on root truth, goal answer, condition, split,
score, or model output.

`NO_MEMORY_RECURRENT` is the recurrent opportunity-matched probe. It preserves
the AUTH phase call schedule, public state/outcome feedback, action/read
budgets, parser, and output allowances, but every memory dispatch returns the
same fixed identity-null no-grant envelope without index lookup.

Neither probe may be declared interface-identical to AUTH: TARGET_ONLY is a
tape and NO_MEMORY lacks memory content. They jointly determine whether this
fixed policy uses the explicit algebra under open-loop and recurrent
opportunities. No result generalizes beyond this frozen policy/topology.

For `e in {task_success_A, task_success_B, two_goal_task_success,
delayed_task_success}` and `c in {TARGET_ONLY_ANSWER_PRIOR_TAPE,
NO_MEMORY_RECURRENT, PASSIVE_SIGNATURE_RECURRENT}`, define:

```text
shortcut_count(e,c) = sum_{k in CONFIRMATION} min_{h in {0,1}} e(k,h,c)
```

Every applicable count must be `<=5`. `NA`, a missing receipt, an invalid
render, or a borrowed value cannot satisfy the bound. Any count `>5` is
`SHORTCUT_BREACH(e,c)`. It withdraws connected-memory specificity for the
corresponding path clause; a delayed breach also withdraws supplied-delayed-
carrier specificity. It is not baseline success that another contrast may
average away. The observed count and the deterministic decoder goldens must
both be reported.

This closes `MTEXTV4-TARGET-ONLY-ALGEBRA-DECODING-14` without adding calls.

## 3. Producer, query, and scorer answer neutrality

Register `M0V4-PRODUCER-SCORER-ANSWER-NEUTRALITY-15` with the following exact
model-free corpus. Failure invalidates the instrument before model execution.

### 3.1 Closed information flow

The carrier producer and index builder have exactly these inputs:

```text
(instrument_version, k, h, public primitive events, frozen slot map,
 registered transform, phase cut)
```

For old path carriers, `h` may affect only root-public rows already entitled
by the paired-world law; it may not affect path ordering or goal answers. The
producer has no parameter or ambient capability for released goal, expected
path, reference-script choice, task score, answer score, model output,
condition display name, split, dispatch order, scorer file, or oracle file.
Goal release and score construction occur strictly after the carrier/index
object hashes are sealed.

The common reader is exactly a pure function of:

```text
(carrier_sha256, anchor, cursor, reader_open, repeat_state)
```

The test harness's exhaustive query agenda is the lexicographically sorted
Cartesian product of all public-capability anchors and legal/one-past cursors.
It is a checker fixture only. A model remains allowed to choose a different
goal-conditioned sequence of legal reads; that intended policy behavior is
not called producer leakage.

The scorer reads a sealed trace only after its final receipt. It has no edge
to producer, index, renderer, reader, parser, controller, model request, or
model action. Removing, swapping, or corrupting scorer/oracle bytes may only
make the private score receipt unavailable/invalid; it cannot alter an actor-
visible byte or an action.

### 3.2 Required swaps and mutations

For every root, registered carrier transform, applicable phase, public anchor,
and cursor, the following tests are exhaustive:

| Test | Held fixed | Swapped/mutated | Required result |
|---|---|---|---|
| producer-goal | primitive events, slot map, transform, phase cut | A/B/D released goal and target | carrier bytes, index bytes, handles, row order, and candidate order identical |
| producer-answer | same producer inputs | expected answer, preferred path, reference-script choice | producer API rejects the fields; sealed objects remain identical |
| reader-goal | carrier/index, anchor, cursor, open/repeat state | released goal/target | return bytes and grants identical |
| reader-score | carrier/index and complete query agenda | task score, path score, answer score, split, oracle | all return bytes and order identical |
| path-order | carrier/index and sealed trace | scorer enumeration `[upper,lower]` versus `[lower,upper]` | producer/reader/render bytes identical and score identical |
| score-label | carrier/index, render, trace | correct and deliberately wrong private labels | no upstream byte/action changes; only the downstream private score changes or rejects |
| scorer-absence | complete unscored receipt | delete/corrupt scorer or oracle | no re-execution and no changed request/action; final assay becomes invalid/incomplete |

No row identity, slot, cursor order, padding, or return order may contain goal,
answer, score, path-equivalence rank, or reference-script rank.

The positive scorer corpus contains all six minimum paths, two per goal:

```text
A: [p0,p1,p4,p5]  [p2,p3,p4,p5]
B: [p0,p1,p4,p6]  [p2,p3,p4,p6]
D: [p0,p1,p4,nh]  [p2,p3,p4,nh]
```

Each is accepted under both scorer list orders when its own atoms/links were
earlier returned and cited. The reject corpus contains answer-only traces,
only the reference script's parent path, a copied final answer, an omitted
bridge, cyclic/post-action dependencies, the wrong terminal, and an
unchanged TWIN terminal action. Acceptance of one path may never depend on
which path the producer or a reference script happened to enumerate first.

## 4. Normalized path traces and terminal semantics

### 4.1 Raw trace closure

A raw path trace begins at its registered phase-start public state and records
every charged world relation attempt in order as
`(pre_state, semantic_relation, public_outcome, post_state)`, followed by
exactly one terminal record. Alias inversion occurs only in the private
scorer. Reads, plans, citations, scratch, calls, timing, padding, and receipt
IDs are not world actions and are excluded from normalization; they remain
available to their own diagnostics.

For a valid instrument, the terminal record is the first of:

```text
FINISH_OK(goal)       finish issued at the released target
WRONG_FINISH(state)   finish issued elsewhere; ordinary behavioral zero
ABSTAIN(state)        abstain; ordinary behavioral zero
BUDGET_EXHAUSTED      four relation attempts consumed without FINISH_OK
OUTPUT_INVALID(code)  registered model parse/size failure; behavioral zero
```

`finish`, `WRONG_FINISH`, and `abstain` terminate immediately. `NO_EFFECT` is
nonterminal but consumes one relation attempt and closes the reader if it is
the first relation attempt. When the fourth relation attempt is not followed
by a correct finish opportunity, append `BUDGET_EXHAUSTED`. Every unissued
call after a terminal is receipt padding `NOT_REACHED`; it is never a world
event, endpoint zero, or substitute terminal. An illegal/private command,
foreign/missing receipt, controller exception, scorer/oracle leak, or other
instrument fault invalidates the assay rather than entering this normalized
behavioral alphabet.

### 4.2 Canonical normalization

Discard `NO_EFFECT` records from the effective-move skeleton but retain their
effect through the charged budget and terminal record. Map state-changing old
relations as follows:

```text
p0 or p2 -> LEG_1
p1 or p3 -> LEG_2
p4       -> BRIDGE
p5       -> TERMINAL_RELATION_R05(destination_role)
p6       -> TERMINAL_RELATION_R06(destination_role)
nh       -> TERMINAL_RELATION_R07_OR_R08(destination_role)
other    -> OTHER_EFFECTIVE(pre_role, relation, post_role)
```

The normalized trace is `(effective_move_skeleton, terminal_record)`. The two
registered upper/lower paths are equivalent for goal `g` exactly when both
normalize to:

```text
(LEG_1, LEG_2, BRIDGE, TERMINAL_RELATION_TO(g), FINISH_OK(g))
```

where the terminal relation's semantic ID may differ only under the registered
TWIN binding transform. Extra harmless NO_EFFECT aliases cannot create a
dependence result; if they consume the budget and prevent completion, the
terminal changes to `BUDGET_EXHAUSTED`. Reads, prose, citations, or choosing
the other registered path class cannot alone create bridge behavior change.

### 4.3 Bridge and binding endpoints

For each `(k,h,g)`, `bridge_behavior_change_g=1` iff:

1. AUTH has `task_success_g=connected_constructive_use_g=1` and its normalized
   trace is in the registered goal-equivalence class; and
2. the BRIDGE_CUT trace is not in that same successful equivalence class.

Thus another registered upper/lower route is equivalent, while abstention,
wrong finish, budget exhaustion, output-invalid behavior, an unrelated move,
or inability to cross `p4` is a change. A generic action-text difference is
not enough. The separate aggregate AUTH-minus-BRIDGE task-benefit gate remains
mandatory, so causal trace change without useful benefit cannot support the
connected-path clause.

The decisive state is exactly public node `C`, reached through the effective
prefix `(LEG_1,LEG_2,BRIDGE)` with no earlier terminal. Define:

```text
auth_terminal(A)=R05    twin_terminal(A)=R06
auth_terminal(B)=R06    twin_terminal(B)=R05
```

`twin_terminal_switch_g=1` iff AUTH and TWIN_REDIRECT both reach the decisive
state, AUTH's first relation attempt from `C` is `auth_terminal(g)`, and the
TWIN arm's first relation attempt from `C` is `twin_terminal(g)`. A finish,
abstain, NO_EFFECT, output-invalid terminal, budget terminal, old AUTH action,
or any other relation attempt from `C` before the required terminal relation
makes it zero. The TWIN world need not count as ordinary task success: this endpoint scores the
content-correct action for the swapped public terminal binding, not an
unchanged answer in the authentic world.

Per root, never per pooled goal:

```text
bridge_pair(k,h) = bridge_behavior_change_A & bridge_behavior_change_B
twin_pair(k,h)   = twin_terminal_switch_A & twin_terminal_switch_B

connected_trace_dependence(k,h) =
  connected_two_goal_use(k,h,AUTH)
  & trace_support_integrity_A(k,h,AUTH)
  & trace_support_integrity_B(k,h,AUTH)
  & bridge_pair(k,h)
  & twin_pair(k,h)
```

`trace_support_integrity_g` is the model-free revalidation that deleting all
registered supporting atoms/links invalidates the cited constructive trace; it
is not a model condition or substitute for bridge behavior. The confirmation
numerator is exactly
`sum_k min_h connected_trace_dependence(k,h)` and must be at least 12 of 16.
No success on A compensates for failure on B; no `h` twin compensates for its
mate.

This closes `MTEXTV4-BRIDGE-TWIN-TRACE-EQUIVALENCE-16`.

## 5. Complete 18-condition by phase by endpoint matrix

The following abbreviations expand to every same-condition scalar in section
1; there is no unlisted same-condition endpoint:

```text
PB = path behavior family for that A or B phase
PM = path connected-mechanism family for that A or B phase
UI = uncertainty/information/acquisition family
DB = delayed behavior family
DM = delayed connected-carrier family
2B = two_goal_task_success
2M = connected_two_goal_use
F/R = full_sequence_task, retention, acquisition_to_delayed_use,
      and online_learning (all four together)
```

| MTextCondition | A.PB | A.PM | B.PB | B.PM | U.UI | D.DB | D.DM | 2B | 2M | F/R |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `AUTH_RECURRENT` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA |
| `AUTH_SCRATCH_OFF` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA |
| `ATOMS_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `DERANGED_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `REACHOUT_OFF_RECURRENT` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA |
| `NO_MEMORY_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `PASSIVE_SIGNATURE_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `RAW_CONTEXT_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `RAG_RAW_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `NATIVE_GRAPH_RECURRENT` | 0\|1 | NA | 0\|1 | NA | NA | 0\|1 | NA | 0\|1 | NA | NA |
| `BRIDGE_CUT_RECURRENT` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA | NA | NA | 0\|1 | 0\|1 | NA |
| `TWIN_REDIRECT_RECURRENT` | 0\|1 | 0\|1 | 0\|1 | 0\|1 | NA | NA | NA | 0\|1 | 0\|1 | NA |
| `UNCERTAINTY_SHAM_RECURRENT` | NA | NA | NA | NA | 0\|1 | NA | NA | NA | NA | NA |
| `OLD_CUT_RECURRENT` | NA | NA | NA | NA | NA | 0\|1 | 0\|1 | NA | NA | NA |
| `NEW_CUT_RECURRENT` | NA | NA | NA | NA | NA | 0\|1 | 0\|1 | NA | NA | NA |
| `NO_PERSIST_NEW_RECURRENT` | NA | NA | NA | NA | NA | 0\|1 | 0\|1 | NA | NA | NA |
| `TARGET_ONLY_ANSWER_PRIOR_TAPE` | 0\|1 | NA | 0\|1 | NA | 0\|1 | 0\|1 | NA | 0\|1 | NA | NA |
| `AUTH_NO_FEEDBACK_TAPE` | 0\|1 | NA | 0\|1 | NA | 0\|1 | 0\|1 | NA | 0\|1 | NA | NA |

The cross-condition scalars `bridge_behavior_change_A/B`,
`twin_terminal_switch_A/B`, `connected_trace_dependence`, shortcut counts,
cut dependence, and best-text deltas are not fields of any row above. They are
derived only from the exact named row/phase values in sections 2, 4, and 7.
Baseline-native trace diagnostics may be reported under their own typed
namespaces, but they cannot populate `PM`, `DM`, or `2M`.

### 5.1 Reducer schema and failure rules

Each endpoint record must bind:

```text
{
  root_id, k, h, condition, phase, endpoint_id,
  applicability: "APPLICABLE" | "NA",
  value: 0 | 1 | "NA",
  phase_receipt_sha256, trace_sha256, scorer_sha256
}
```

The reducer enforces:

1. `applicability=APPLICABLE` iff the matrix cell is `0|1`; its value must be
   an integer Boolean. `applicability=NA` iff the matrix says `NA`; its value
   must be the literal string `NA` and its phase/trace hashes must be the
   schema's null sentinels.
2. A registered phase that ends in `WRONG_FINISH`, `ABSTAIN`,
   `BUDGET_EXHAUSTED`, or registered `OUTPUT_INVALID` remains applicable.
   Score every endpoint determined by its observed prefix; any unsatisfied
   success predicate is zero. Do not replace the phase by `NA`.
3. `NOT_REACHED` is legal only for unissued call-slot receipts after an early
   terminal. It never appears as an endpoint value and cannot erase an
   already-applicable phase.
4. Every raw endpoint is computed only from the same `(root_id,condition,
   phase)` receipt. The exact source rejects a foreign condition, sibling
   phase, other `h`, other root, AUTH fallback, fixed-entry fallback, cached
   summary, or copied score. Hash equality of public starts does not authorize
   result borrowing.
5. `2B` or `2M` is Boolean only when both same-condition A and B operands are
   Boolean; otherwise it is `NA`. `F/R` is always `NA` and no reducer may
   synthesize it.
6. A gate over endpoint `e` rejects unless every one of its 32 confirmation
   root-condition inputs is Boolean and every expected receipt is terminal.
   Gate-required `NA`, missing/duplicate/foreign receipts, invalid hashes, or
   an instrument fault makes the assay `INVALID` or `INCOMPLETE`, never pass
   and never a scientific zero.
7. Twin reduction is only `b_e(k,c)=min(e(k,0,c),e(k,1,c))`. Cross-condition
   endpoints first compute their named same-`(k,h)` Boolean formula and only
   then take the twin minimum. No other imputation or averaging exists.

This closes `MTEXTV4-CONDITION-PHASE-ENDPOINT-APPLICABILITY-17`.

## 6. Exact gate registry

All counts below are over the 16 confirmation `k` blocks after twin minimum.
They are integer predicates; no averaged gate or reserve rescue exists.
Within the equations only, `AUTH`, `ATOMS`, `DERANGED`, `BRIDGE_CUT`,
`REACHOUT_OFF`, `UNCERTAINTY_SHAM`, `OLD_CUT`, `NEW_CUT`, `NO_PERSIST_NEW`,
`NO_MEMORY`, `PASSIVE_SIGNATURE`, `RAW_CONTEXT`, `RAG_RAW`, and
`AUTH_SCRATCH_OFF` abbreviate the exact condition names in the section-5
matrix; `TARGET_ONLY` abbreviates `TARGET_ONLY_ANSWER_PRIOR_TAPE`, and
`NO_FEEDBACK` abbreviates `AUTH_NO_FEEDBACK_TAPE`.

```text
G0 INSTRUMENT_VALID:
  every required source, handoff, rendered-prefix, delayed-entitlement,
  producer/query/scorer, reset/session, receipt, applicability, and resource
  invariant passes; confirmation registry is complete.

G1 AUTH_HEADROOM:
  count(two_goal_task_success, AUTH) >= 12
  count(delayed_task_success, AUTH) >= 12

G2 CONNECTED_BENEFIT:
  for c in {ATOMS, DERANGED, BRIDGE_CUT, REACHOUT_OFF}:
    count(two_goal_task_success, AUTH)
      - count(two_goal_task_success, c) >= 4
  count(connected_two_goal_use, AUTH) >= 12
  count(connected_trace_dependence) >= 12

G3 PUBLIC_CALIBRATION:
  for e in {separating_choice, realized_information,
            belief_revision, acquisition_success}:
    count(e, AUTH) >= 12
  for e in {realized_information, belief_revision, acquisition_success}:
    count(e, UNCERTAINTY_SHAM) <= 4
  count(acquisition_success, AUTH)
    - count(acquisition_success, UNCERTAINTY_SHAM) >= 8

G4 DELAYED_CARRIER:
  count(delayed_connected_integration, AUTH) >= 12
  for c in {OLD_CUT, NEW_CUT, NO_PERSIST_NEW}:
    count(delayed_task_success, c) <= 4
    count(delayed_task_success, AUTH)
      - count(delayed_task_success, c) >= 8

G5 SHORTCUT_PATH:
  all section-2 shortcut counts for task_success_A, task_success_B, and
  two_goal_task_success are <= 5

G6 SHORTCUT_DELAYED:
  all section-2 shortcut counts for delayed_task_success are <= 5

G7 ZERO_NET_ATOMS:
  for e in {task_success_A, task_success_B, two_goal_task_success,
            plan_valid_A, plan_valid_B, first_action_correct_A,
            first_action_correct_B, plan_execution_consistent_A,
            plan_execution_consistent_B, delayed_task_success,
            delayed_plan_valid, delayed_first_action_correct,
            delayed_plan_execution_consistent}:
    count(e, AUTH) - count(e, ATOMS) >= 0

G8 BEST_TEXT (optional):
  for e in {two_goal_task_success, delayed_task_success}:
    sum_k [b_e(k,AUTH)-max(b_e(k,RAW_CONTEXT),b_e(k,RAG_RAW))] >= 1
  and zero net AUTH loss to that root-wise max on every other endpoint in G7.
  NATIVE_GRAPH is a reported ceiling and is not in the maximum.

G9 CARRIED_SCRATCH (optional):
  count(acquisition_success, AUTH)
    - count(acquisition_success, AUTH_SCRATCH_OFF) >= 4
  count(delayed_task_success, AUTH)
    - count(delayed_task_success, AUTH_SCRATCH_OFF) >= 4
  and AUTH has zero net loss to AUTH_SCRATCH_OFF on every other mutually
  applicable PB, UI, DB, 2B endpoint.

G10 CLOSED_LOOP_FEEDBACK (optional):
  count(acquisition_success, AUTH_SCRATCH_OFF)
    - count(acquisition_success, AUTH_NO_FEEDBACK_TAPE) >= 4
  count(delayed_task_success, AUTH_SCRATCH_OFF)
    - count(delayed_task_success, AUTH_NO_FEEDBACK_TAPE) >= 4
  and AUTH_SCRATCH_OFF has zero net loss to AUTH_NO_FEEDBACK_TAPE on every
  other mutually applicable PB, UI, DB, 2B endpoint.
```

`G9` is evidence only for explicit carried structured scratch under recurrent
feedback. `G10` includes repeated interaction and within-phase public outcome
feedback; it is not pure recurrence, not DREAM recurrence, and not U-to-D
retention.

## 7. Clause-to-gate and negative-disposition matrix

“Mandatory” means mandatory for the maximum three-clause V4 statement. A
mandatory-clause failure withdraws that clause and the combined maximum
statement, but does not turn a separately passing clause into failure. The
three optional clauses can never rescue a mandatory clause.

| Claim clause | Status | Required evidence/gates | Exact failure or negative disposition |
|---|---|---|---|
| supplied connected memory supported two goal-dependent route constructions | mandatory | `G0 & G1(two-goal) & G2 & G5 & G7`; report AUTH constructive and bridge/twin numerators | Any invariant/receipt failure makes the assay invalid/incomplete. Any other miss, including algebra shortcut, withdraws connected-memory specificity; report task and intervention counts as bounded negative/mixed evidence, not connection use. |
| calibrated public evidence supported separating choice and revision | mandatory, mechanistically separate | `G0 & G3`; only public-calibration UI endpoints | A G3 miss withdraws only the calibration clause and the combined maximum statement. It cannot reduce or rescue a connection result and cannot be called DREAM or memory causality. |
| a supplied old-plus-new carrier supported delayed task completion and connected integration after sterile reset | mandatory, mechanistically separate | `G0 & G1(delayed) & G4 & G6 & applicable G7`; exact reset and supplied-entry checks | A cut/headroom/integration/shortcut/reset miss withdraws the delayed-carrier clause and combined maximum statement. Never relabel it retention, acquisition-to-use, self-write, or online learning, even on pass. |
| AUTH practically outperformed the strongest honest unstructured textual-memory baseline | optional | all mandatory clauses needed by the named endpoint plus `G8` and the per-arm resource-factorial receipt | G8 or resource-factorial failure withdraws all practical-superiority and efficiency language only. RAW/RAG success is an honest alternative, not a shortcut or invalidity. Core mechanism clauses are not rescued or defeated solely by G8. |
| carried structured scratch improved behavior | optional | `G0 & G9`; exact endpoints and zero-net comparisons above | Failure withdraws only carried-scratch benefit. Do not say recurrence necessity, persistent memory, SLEEP, or learning. It cannot rescue a mandatory clause. |
| closed-loop within-phase feedback improved behavior | optional | `G0 & G10`; exact tape terminal and resource receipts | Failure withdraws only feedback-benefit language. A pass is not pure recurrence and proves no U-to-D retention. It cannot rescue a mandatory clause. |

The following clauses are unconditionally withdrawn by design, not optional
outcomes: DREAM authorship, SLEEP validation, LoRA storage/transport, the
model's own persistent write, retention, acquisition-to-delayed use, online
learning, continued-life improvement, accumulation, compression, parenting,
topology/model/population generalization, baseline saturation, and complete-
organism or flywheel behavior.

Global dispositions are:

1. A semantic, producer, query, scorer, prefix, handoff, reset, session, CAS,
   receipt, applicability, or resource-integrity breach is `INVALID` or
   `INCOMPLETE`; it supports no scientific clause.
2. A complete valid confirmation gate miss is retained negative evidence for
   that clause. It is not dropped, retried, replaced, or repaired with reserve.
3. A shortcut breach is a specificity failure, not a successful baseline that
   may be averaged with AUTH.
4. `NA` at a required gate is a schema failure. Zero is an observed adverse
   behavior. `NOT_REACHED` seals calls only. These states never substitute.
5. DEV may select/fork before confirmation freeze but contributes no claim
   evidence. Confirmation is a finite census under one model/topology, not a
   sample, and produces exact numerators/denominators only.

This closes `MTEXTV4-CLAUSE-SPECIFIC-NEGATIVE-DISPOSITION-18`.

## 8. Maximum wording after this repair

Only if all three mandatory clause rows pass may the combined statement be:

> In one fixed finite topology under one exact frozen text policy, supplied
> grounded atom-plus-connection memory supported two goal-dependent route
> constructions under registered connection and binding interventions;
> separately, calibrated public evidence supported separating choice and
> belief revision; and a model-independent supplied old-plus-new carrier
> supported delayed task completion and connected integration after sterile
> reset.

Optional practical-baseline, carried-scratch, and closed-loop-feedback
sentences may be appended only when their own rows pass. None changes the
unconditional exclusions above.

## 9. Required next boundary

The next integrated proposal must copy these endpoint, normalization, matrix,
gate, and disposition choices into its hash-bound source direction and subject
them to fresh independent review. This advisory does not authorize that
proposal, its source bundle, preparation, implementation, model execution, or
science. Any change to an equation, matrix cell, gate threshold, condition,
or claim clause is outcome-changing and requires renewed deliberation and
explicit human ratification.

## 10. Source basis

This advisory was written after complete reads of the governing contract,
integrated candidate, and all V4 role artifacts at these SHA-256 values:

```text
AGENTS.md                                      1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e
pcfl_m0_mtext_exact_v4_rework_candidate.md     32d73b800971a61a20fa68694dc9cbed9203c65d59d3c01c5baffe2c3a6e53cc
change.json                                    a6332cfeab3bc2281404a568e2c04eaf8ffa28db96d3c33265140f9fe7c3408f
interpretation_systems.json                    ac9b91c20cb75ca18d7b5608423e3377d0aaa6ff24e45513acfd4bfd4f6bf270
interpretation_benchmark.json                  745f6514672ffaf2e14c87088c55dbad67232054a219a821a4a36f51ca8d6af3
critique.json                                  6caa938022d9e6b2e47a3d3997b8d06c44a67568550fd86716d6123e2c1e2fad
consensus.json                                 7cad92d5563f0b0be69d6dd72fca7419573d93fbb19021e5b614e0bac0798720
human_directive.txt                            ce1540a98aba52c1f4953faafdc10727056134a49b1dc19a5c413ae634c90a0f
scope_proposal.json                            12c5f1b459a697a59d4fecc1e2991f880a69898fa9a4013f66947fef1bd7ea0b
intake.state.json                              913520d6093f960fe6d4b39c293850468bcab6dcf488e3250a89200be6758ec6
pcfl_m0_mtext_bound_v4.deliberation.json       d1f9308b8e205dfc8aa4590a1462a571b7ef02c1335e4335e0bd5692a4811e49
```
