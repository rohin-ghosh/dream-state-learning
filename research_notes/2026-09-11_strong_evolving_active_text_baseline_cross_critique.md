# Cross-critique and repaired role matrix for active-text memory

Date: 2026-09-11

Status: **design rework only.** This note authorizes no source edit beyond
this note, implementation, materialization, model/tokenizer call, training,
adapter operation, parenting, GPU use, scientific claim, release, or
submission. It does not amend the parked C11 guard.

Inputs:

- original candidate:
  `2026-09-11_strong_evolving_active_text_baseline_candidate.md`;
- fresh critique:
  `2026-09-11_strong_evolving_active_text_baseline_adversarial_critique.md`.

## Verdict

The adversarial critique is accepted. The original unified
`ACTIVE_TEXT_EVOLVING` proposal is withdrawn as an arm law. It combined three
different scientific objects, used graph traversal inside cells intended to
attribute traversal to DREAM/LoRA, understated the workload, and left several
runner interfaces unresolved.

The useful core survives only after being split into three roles:

1. **`TEXT_SAME_SEMANTICS`**: a fixed same-source carrier diagnostic;
2. **`TEXT_COMMON_RAW`**: an optional narrow common textual-memory control;
3. **`ACTIVE_TEXT_NATIVE`**: a standalone strong external-memory agent.

These names do not rename or supersede the existing `ACTIVE_TEXT_FIXED` or
`M-TEXT-SUPPLIED` proposals. No result may move between the three roles.

## 1. Revised role and claim matrix

| Role | Evidence and reader | LoRA | Valid estimand | Explicitly cannot establish |
|---|---|---|---|---|
| Access certificate | Frozen opposing fixture stores; exact required-row identities | off | Can the fixed actor find, cite, and use returned text? | memory-system strength, learning, LoRA transport |
| `TEXT_SAME_SEMANTICS` | One immutable eligible payload deck; fixed finite reader; the text bytes and LoRA targets are the exact same canonical payload bytes | alternative text-only versus fitted LoRA-only carriers | local access/transport difference at a fixed age | an autonomous life, continual learning, superiority over active memory |
| PCFL E2--E5 mechanism | Existing finite one-hop reader only; one selected public row per charged call; no PPR, graph expansion, or automatic link following | alternative exact-text versus LoRA carrier | carrier-specific retention, connection use, goal-conditioned actor traversal, and one-cycle expansion | strength relative to a native graph-memory system |
| `TEXT_COMMON_RAW` | Same raw, deployment-only public event schema and same bounded lexical reader in both arms; no compiler prose, summaries, aggregates, or graph traversal | promoted versus true shadow | incremental total effect of promoting weights conditional on a common text aid | LoRA-over-text superiority or LoRA-formed connectedness |
| `ACTIVE_TEXT_NATIVE-CG-RAW` | Independently evolving raw action/outcome store plus frozen hybrid retrieval | off | bounded system comparison on CompilerGym | plateau, graph connectedness, open-ended growth |
| `ACTIVE_TEXT_NATIVE-CG-AGG` | CG-RAW plus explicitly task-specific public-score aggregates | off | stronger task-specific external-memory system point | byte-matched carrier effect or generic-memory superiority |
| `ACTIVE_TEXT_NATIVE-PCFL` | Independently evolving raw+typed store and native graph-assisted retrieval; retriever path work is measured | off | strong standalone external-memory system and later plateau | child/LoRA traversal when the retriever traversed |
| `DLT_NATIVE` | Native THINK--DREAM--SLEEP system plus only its explicitly registered append-only ledger/legacy `RECALL`; no `TEXT_COMMON_RAW` or native graph retriever hidden inside it | promoted LoRA | whole-system comparison with `ACTIVE_TEXT_NATIVE` under reported native costs | carrier-only effect |
| Parenting weight-persistence | Canonical empty external store and no legacy recall state after parent removal | registered child adapter on/off | durable child-state effect without textual childhood carryover | benefit from retaining childhood episodic text |

Two optional factorials are therefore distinct:

- **incremental promotion:** `TEXT_COMMON_RAW + promoted` versus
  `TEXT_COMMON_RAW + true-shadow`;
- **direct systems:** independently evolving `DLT_NATIVE` versus independently
  evolving `ACTIVE_TEXT_NATIVE`.

A full `TEXT_COMMON_RAW off/on x LoRA promotion off/on` 2x2 is needed only if
interaction between external text and promotion is itself a registered claim.
The absent corner will never be inferred.

In the incremental comparison the two stores are byte-identical at the fork
and follow the same updater thereafter. They are not required to stay
byte-identical after promotion changes action and experience; the later
difference is therefore a total recursive effect conditional on the common
memory policy, not a carrier-only effect.

## 2. Exact information boundaries

### 2.1 Evidence classes

All three roles begin from authoritative public events, but only the
same-semantics assay requires identical transformed bytes.

An authoritative event is eligible only when it is an ordinary wake or
deployment event in the same scientific root, precedes the query's causal
frontier, names an action actually dispatched by the harness, and contains
the exact associated public outcome. Probe, canary, report, evaluator,
parent, hidden-state, future, repaired, wrong-root, and unsupported bytes are
ineligible. Invalid dispatched actions remain eligible negative evidence.

The roles then diverge:

- `TEXT_SAME_SEMANTICS`: a deterministic eligibility decision is made before
  either carrier is produced. Each canonical payload is rendered unchanged
  as text and used unchanged as a LoRA target. Paraphrased or compiler-written
  semantic bytes are excluded unless the exact same bytes are deliberately
  admitted to both carriers under a separately named assay.
- `TEXT_COMMON_RAW`: only authoritative public action/outcome events enter.
  Child interpretations, parent messages, DREAM output, compiler prose,
  aggregates, and learned links never enter. This keeps the control from
  installing the mechanism attributed to DREAM or LoRA.
- `ACTIVE_TEXT_NATIVE`: starts from the same authoritative public frontier but
  may construct its own typed records, summaries, aggregates, and links under
  a frozen native updater. Derived rows remain interpretations and cite every
  supporting source. This is a systems comparator, never a byte-match claim.

Each event has a schema-versioned identity derived from canonical source
bytes and at least `(scientific_root, episode_instance, occurrence_index,
decision_index)`. Every derived record carries its document identity, exact
source-event list/digest, creator/type, causal creation frontier, support
count, payload, and status. The actor sees citations inserted by the harness;
model-invented citations never confer eligibility.

Historical CompilerGym rows lack this full envelope. They may support only a
named **retrospective reconstructed diagnostic** after a preflight identifies
which fields are losslessly recoverable. New paper-facing lives require a new
schema-versioned ledger. A hash of a truncated or reconstructed row is never
called the original source-envelope receipt.

### 2.2 Chronology

The causal visibility law is fixed across all text systems:

- an episode sees its own dispatched event on its next continuation;
- events from sibling episodes in a batched wake become visible only after the
  complete batch-round barrier;
- the canonical commit order is `(batch, round, episode_instance, decision)`;
- process completion time, cache timing, and arm identity cannot change it;
- a failed derived-index refresh keeps the prior index and exposes the raw
  transaction only according to the same frontier.

### 2.3 Parent removal and clean deployment

For a parent-absent weight-persistence exam, deletion means all of the
following: parent messages, child restatements from childhood, childhood raw
and derived stores, retrieval history, indexes, embeddings, caches, query
state, and legacy `RECALL` state. The exam begins from one canonical empty
external store.

Every final 2x2 deployment cell also begins with the same empty deployment
store and admits only post-fork deployment events. In parent-present cells,
`TEXT_COMMON_RAW` still admits environment action/outcome events only; neither
direct parent language nor child paraphrases of it enter the common text path.
A separately named whole-adult test may retain childhood episodic memory, but
it cannot be reported as weight persistence.

## 3. One query and one recall path

The deadline interface is **`QUERY_PER_CONTINUATION`**, not “before every
decision.” One continuation may contain several `ACT` markers; all were
generated from the same pre-continuation memory block. A future
`QUERY_PER_DISPATCH` interface would alter THINK and requires a separate arm.

For `TEXT_COMMON_RAW` and the CG native systems:

1. Exactly one automatic query is constructed before each actor continuation.
2. It contains only bounded public fields: objective/metric, current program
   identity, current best public score and action, the bounded sequence of
   already-dispatched current-episode actions/outcomes, counters, and one
   optional prior child query modifier.
3. Fields, escape law, missing sentinels, order, tokenizer-side caps,
   truncation side, and total query limit are exact proposal artifacts before
   implementation. The query never contains the current continuation,
   unexecuted action, evaluator/reference answer, future task, arm, adapter,
   report identity, candidate order, or hidden capability handle.
4. The last well-formed `RECALL:` body in a continuation, capped at 64 child
   tokens, becomes the modifier for the next automatic query. Earlier or
   additional markers have no effect; malformed or over-cap bodies become the
   canonical empty modifier. Those generated query tokens remain charged to
   the actor budget.
5. Legacy `Ledger.recall` is disabled in these cells. There is one memory
   state machine and at most one returned block per continuation.

`TEXT_SAME_SEMANTICS` instead uses predeclared fixed query cases and its finite
reader; actor-generated query divergence cannot contaminate the carrier
assay. PCFL E2--E5 retains its already proposed four-call `READ/FOLLOW/ACT`
state machine. `ACTIVE_TEXT_NATIVE-PCFL` gets a separately registered native
query state machine and is never called reader-matched.

Exact-program retrieval in CG is declared a cache capability. All CG results
must split novel-program visits from repeated-program visits.

## 4. Retrieval laws without hidden traversal

### 4.1 Common control

`TEXT_COMMON_RAW` uses a bounded raw-row retriever only. It may rank by a
frozen lexical rule over identifier-normalized public text, but it may not
build aggregates, infer relations, follow edges, run PPR, or automatically
return linked neighbors. The actor must do any connection or traversal in its
own generated stream.

This narrow system is an isolation control, not “the strongest baseline.”

### 4.2 Same-semantics and PCFL mechanism cells

`TEXT_SAME_SEMANTICS` and PCFL E2--E5 use only the existing finite reader.
The text and LoRA arms receive the same call opportunities and candidate
surface. No graph expansion is mounted in the LoRA cells. Thus any selected
multi-step path is actor work, not hidden retriever work.

### 4.3 Standalone native agents

`ACTIVE_TEXT_NATIVE-CG-RAW` may use frozen lexical+dense hybrid retrieval.
`ACTIVE_TEXT_NATIVE-CG-AGG` adds a clearly labeled public-score optimizer.
The old expression called `LCB` is withdrawn. If used, the aggregate ranking
utility is a support-penalized heuristic over a registered clipped utility,
with one deterministic observation-reduction rule; it is never an inferential
confidence bound.

`ACTIVE_TEXT_NATIVE-PCFL` may use typed graph retrieval and PPR because graph
work is part of that standalone system. Its report must expose expanded
nodes/edges, returned path distance, PPR-off, bridge-cut, deranged-link, and
necessary-edge interventions. Success belongs to the complete active-memory
system, not to child traversal.

Before either native retriever is executable, every tokenizer/encoder
revision, BM25 normalization and constants, fusion equation, graph
construction, direction/weights/dangling rule, numeric precision, fixed
iteration count, MMR equation, reservations, duplicate/supersession law,
document cap, packing, and tie rule must be bound with byte-exact goldens. No
library default is normative.

Opaque identities are normalized to equality-preserving local symbols in
first-public-appearance or registered-public-slot order before ranking. Ties
use rename-invariant public ordinals. Original handles are restored only in
the returned rendering. Equivariance is required over this registered
normalization, not arbitrary dense embeddings of arbitrary handle strings.

## 5. Randomness, context, and resource accounting

### 5.1 Common randomness

Every actor continuation receives a tape address derived from

```text
(study_hash, scientific_root, episode_instance, occurrence_index,
 decision_index, continuation_index, technical_replicate)
```

and never from arm, carrier, adapter, device, process order, cache, restart,
or wall time. Paired arms use the same address. Repeated occurrences of the
same program necessarily use different addresses. After treatments change
actions, equal tape addresses preserve common exogenous randomness without
pretending post-treatment histories remain identical.

### 5.2 Prompt packing

The complete chat-templated prompt is tokenized with the pinned child
tokenizer before inference. The law first reserves the registered generation
budget, then packs fixed partitions for system/task, current state, child
history, and memory return. Every kept/dropped token ID is receipted. Overflow
has one registered failure/truncation result; backend truncation is forbidden.
Matched carrier probes use neutral padding when memory-block length differs.

### 5.3 Deadline budget and cost statement

The original `{16,32,64}` sweep is withdrawn: at its upper end it could cost
hundreds of millions of output tokens and a 16-case point estimate could not
justify the choice.

For the CompilerGym deadline, first analyze already valid development output
to determine whether the existing fixed envelope of 16 continuations x 400
new tokens (6,400 generated tokens per episode) is token-sufficient under a
predeclared late-budget marginal-gain rule. If it passes, that envelope is
frozen for every deadline arm. If it fails, the paper-facing CG comparison is
`NO_GO` until a separately powered and resource-bound budget study exists;
the budget is not silently raised or lowered.

Before any actor run, a resource manifest must state exact roots, episodes,
continuations, maximum/expected input and output tokens, environment
dispatches, retrieval/index operations, CPU/RAM/storage, actor inference
device-hours, LoRA/shadow fits, VRAM, wall time, and hard stop. A standalone
active-text agent has no parameter-training cost but still has actor-inference
and retrieval cost. A promoted-versus-shadow experiment pays both training
transactions.

Generated actor tokens and public action opportunities are equal within a
registered comparison. Input context, storage, retrieval work, training,
latency, and energy are reported rather than called matched. The unsupported
Pareto-curve promise is removed; the deadline reports a native-resource cost
table. A later Pareto claim requires a separately registered resource grid.

## 6. Statistical repair

### 6.1 CompilerGym deadline

CompilerGym supports a bounded finite-horizon comparison only. There is no
CG plateau epsilon and no “beyond active-text saturation” claim.

The direct system primary is root-paired lifetime AUC on one fixed checkpoint
grid, integrated trapezoidally within root. Terminal score, novel-versus-
repeat score, action-count curves, invalid rate, and cost are secondary. The
incremental-promotion primary, if run, is the root-paired AUC difference
between promoted and true-shadow under `TEXT_COMMON_RAW`.

Development roots select the frozen native baseline and estimate paired-root
variance. Before confirmation output exists, the packet binds one smallest
effect of interest, one-sided alpha, target power, exact root count, resource
ceiling, and missing/failure rule. If the powered root count exceeds the
ceiling, the confirmatory claim is `NO_GO`; there is no adaptive stopping,
checkpoint pseudo-replication, outlier removal, or same-data model selection.
One primary estimand avoids multiplicity; all secondary intervals are labeled
descriptive or receive a predeclared family correction.

`CG-RAW` and `CG-AGG` are compared only on disjoint DEV using root-first
trapezoidal AUC. A predeclared equivalence band derived from the DEV-stage
SESOI selects the simpler `CG-RAW` when their difference is practically
unresolved; otherwise the higher-AUC system is frozen. Runtime noise never
chooses the scientific baseline. Both DEV results remain disclosed.

The access certificate separates deterministic instrument tests from actor
behavior. Its actor N and adverse margin come from a presealed variance/power
calculation after the comparator is chosen on disjoint DEV. The original
`n=100` and `0.01` noninferiority margin are withdrawn. If the affordable N
cannot resolve the prospective adverse margin, the access certificate fails
rather than being relaxed after observation.

### 6.2 Later PCFL plateau

Only mechanically novelty-certified PCFL cohorts may support plateau. DEV
selects and freezes the exact anchor, cuts, root N, old-cohort cases, SESOI
`epsilon`, and resource budget before confirmation. At each of the registered
late intervals, the root-level gain must be equivalent to zero within
`[-epsilon,+epsilon]`; a negative decline is not a plateau. Confirmation uses
independent roots, an exact anchor-plus-late grid, root-level slopes/AUC, a
registered equivalence test, retention margin, multiplicity rule, adverse
fill, and no optional stopping. If scheduled new public information or oracle
headroom is absent, no plateau claim exists.

The same-source carrier source is an exogenous immutable deck fixed before
the text/LoRA fork. It is not selected by whichever carrier later performs
better. Longitudinal native systems instead transform their own on-policy
events; their comparison is a total recursive system effect, not a fixed-
evidence carrier effect.

## 7. Disposition of every critique blocker

| Critique | Disposition |
|---|---|
| 1.1 common ATE destroys PCFL attribution | accepted; finite reader in E2--E5, graph native system separate |
| 1.2 additive value != system superiority | accepted; separate incremental and direct-system estimands; optional complete 2x2 only |
| 1.3 byte-identical claim false | accepted; exact payload deck only for same-semantics; native systems share raw frontier, not transforms |
| 1.4 parenting leak | accepted; sterile external-memory reset for weight persistence and final deployment |
| 1.5 CG saturation | accepted; CG plateau claim removed |
| 2.1 historical ledger incomplete | accepted; retrospective reconstruction labeled; new schema required for paper lives |
| 2.2 seed collision | accepted; occurrence- and continuation-indexed arm-independent tape |
| 2.3 batch chronology | accepted; own-next-continuation plus cross-episode batch barrier |
| 2.4 continuation != decision | accepted; interface renamed `QUERY_PER_CONTINUATION` |
| 2.5 second RECALL path | accepted; legacy reader disabled; one modifier and one returned block |
| 2.6 unbound CG query/documents | accepted; exact bounded format required; current best/history included; repeat cache disclosed |
| 2.7 asserted context equality | accepted; full chat-template token packing and receipts; neutral padding in matched assay |
| 3.1 invalid LCB | accepted; name withdrawn; any aggregate is a clipped-utility ranking heuristic only |
| 3.2 aggregates are algorithmic | accepted; `CG-RAW` and `CG-AGG` reported separately |
| 3.3 missing retrieval arithmetic | accepted; total equations/precision/ties/goldens required before implementation |
| 3.4 noisy DEV selection | accepted; root-first AUC, disjoint DEV, deterministic simplicity tie; no latency winner by noisy realization |
| 4.1 finite-reader conflict | accepted; native graph reader never called matched |
| 4.2 PPR performs traversal | accepted; PPR only in standalone system; path work and cuts reported |
| 4.3 impossible rename law | accepted; identifier-normalized ranking projection and rename-invariant ordinal |
| 4.4 undefined PPR graph | accepted; total graph arithmetic plus goldens prerequisite |
| 4.5 absent PCFL query surface | accepted; existing finite E2--E5 machine retained; native state machine separately bound |
| 5.1 “no training GPU” misleading | accepted; actor, retrieval, promoted, and shadow costs separated |
| 5.2 token sweep infeasible | accepted; sweep withdrawn; cached-evidence check or CG `NO_GO` |
| 5.3 unjustified certificate N | accepted; deterministic fixtures separated; N/margin powered on sealed design data |
| 5.4 plateau/retention incomplete | accepted; exact novelty cohorts/cuts, two-sided equivalence, retention, power, and failures required |
| 5.5 no Pareto sweep | accepted; Pareto claim removed; native cost table only |

## 8. Staged acceptance path

This path minimizes GPU spend and prevents a strong baseline from quietly
becoming either a handicap or the claimed mechanism.

### Stage 0 — role and claim freeze (design only)

Bind the matrix above, the one primary estimand for each planned comparison,
the exact reset/store survival law, and prohibited claim migration. Decide
whether the deadline needs only the same-source diagnostic, the direct native
CG comparison, or also the optional common-text promotion experiment.

**Exit:** every scientific cell has one role and one claim. Otherwise stop.

### Stage 1 — provenance and feasibility audit (CPU/read-only design audit)

Inventory historical CG roots field by field. Mark each as authoritative,
losslessly reconstructable, or unusable. Produce the exact deadline resource
formula and test the 6,400-token envelope using only already valid DEV output.

**Exit:** retrospective diagnostic scope is honest; a new-life schema and
resource ceiling are bindable. Failure yields a diagnostic-only deadline.

### Stage 2 — exact contracts before source authorization

Prepare separate contracts for `TEXT_SAME_SEMANTICS`, `TEXT_COMMON_RAW`, and
`ACTIVE_TEXT_NATIVE-CG`. Bind the causal state machine, event/document schema,
seed address, query/RECALL grammar, rank arithmetic, prompt packing, reset,
resource manifest, root N/power, primary estimand, and claim order.

**Exit:** independent architecture/adversarial review closes all fields and
the human ratifies exact scope. This note alone is not authorization.

### Stage 3 — model-free conformance

Only after scoped implementation authorization: run identity/eligibility,
chronology/barrier, randomness, single-memory-path, blindness, ranking,
packing, rename, phase-isolation, graph-exclusion, and resource-reconciliation
goldens. No actor is needed.

**Exit:** exact pass. Any failure is instrument failure, not LoRA evidence.

### Stage 4 — smallest actor access certificate

On a source-disjoint opposing-store panel, run predeclared GOLD, TEXT, EMPTY,
IRRELEVANT, SWAP, and NECESSARY-ROW-CUT cases under common tapes. Require exact
retrieval/citations, directional store-swap and row-cut effects, registered
non-harm, syntax preservation, and task headroom at the powered N.

**Exit:** actor can use the memory. Failure stops the text comparison before
long lives.

### Stage 5 — deadline CG evidence

Run, in increasing cost:

1. retrospective `TEXT_SAME_SEMANTICS` diagnostic where provenance permits;
2. fresh DEV selection between `CG-RAW` and the separately labeled `CG-AGG`;
3. only if powered and affordable, fresh root-paired `DLT_NATIVE` versus the
   selected `ACTIVE_TEXT_NATIVE-CG` bounded lifetime;
4. only if specifically needed, `TEXT_COMMON_RAW + promoted/shadow` after a
   one-root true-shadow dry run proves byte-identical compile/train work and
   promotion-only difference.

There is no CG plateau gate. If time or power is insufficient, report the
carrier diagnostic and access certificate, not a weak superiority claim.

### Stage 6 — PCFL mechanism path

Retain `M0/M-TEXT-SUPPLIED` preparation and the finite-reader exact-text relay.
Run E2--E5 text-versus-LoRA mechanism cells without PPR or automatic graph
expansion. This path owns carrier-specific connectedness/traversal evidence.

**Exit:** only its registered mechanism claims may proceed.

### Stage 7 — later standalone PCFL baseline and plateau

Separately design, certify, and run `ACTIVE_TEXT_NATIVE-PCFL`, including its
native graph controls and resource point. Only novelty-certified DEV may set a
prospective plateau anchor; only independent confirmation may establish it.
Then compare standalone native systems or run the complete common-text
factorial, according to the already bound claim.

**Exit:** either a valid strong-baseline/plateau result or an honest
`NOT_ESTABLISHED`. It cannot retroactively change E2--E5 attribution.

## 9. Bottom line

The repaired deadline design is intentionally smaller than the original:

- same-source text is an assay;
- common raw text is an isolation control;
- the strong active-memory agent is a separate opponent;
- graph traversal belongs only to that opponent;
- CompilerGym supplies bounded evidence, never saturation;
- PCFL supplies later mechanism and plateau evidence through separate paths.

This retains the strongest feasible external-memory comparison without
letting it either inherit DREAM/LoRA's claimed work or donate that work back
to the LoRA arm.
