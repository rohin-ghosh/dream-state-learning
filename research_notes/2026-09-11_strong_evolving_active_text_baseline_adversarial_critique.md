# Adversarial critique: strong evolving active-text comparator candidate

Date: 2026-09-11

Status: **fresh independent scientific critique only.** This note authorizes
no source edit, implementation, fixture or root generation, model/tokenizer
call, training, adapter operation, parenting, GPU use, claim, release, or
submission. It is one critique input to the repository's architecture-
deliberation path, not consensus or ratification.

Reviewed candidate:
`research_notes/2026-09-11_strong_evolving_active_text_baseline_candidate.md`.

## Verdict

**REWORK before architecture intake.** The candidate identifies the correct
missing comparator: a frozen actor with an evolving, candidate-blind,
lossless external memory is much stronger than the historical static waking
brief. Its raw-evidence preservation, immediate visibility, provenance,
store-swap tests, prospective plateau, failure inclusion, and explicit cost
accounting are all directionally right.

It is not yet an executable or causally coherent experiment. The proposal
silently combines three different scientific objects:

1. a same-source **carrier diagnostic**;
2. a common auxiliary memory used to estimate the **incremental effect of
   promoted LoRA**; and
3. a standalone **strong active-memory agent** that Dream--LoRA--Think must
   eventually beat.

Those objects need different arm layouts. In particular, giving a graph-
structured ATE with personalized PageRank to every PCFL arm makes ATE itself
the connected-memory and traversal mechanism. Such an experiment cannot then
attribute connectedness or traversal to the LoRA carrier. Conversely, giving
ATE to both longitudinal arms can cleanly estimate the incremental total
effect of promotion, but it does not establish system-level superiority over
ATE. The candidate must split these claims rather than use one common-ATE rule
everywhere.

Five additional blockers are fatal as written:

- the proposed PCFL hybrid/PPR reader conflicts with the currently proposed
  common finite one-hop reader;
- historical CompilerGym ledgers do not contain the event identities and
  immutable source-envelope receipts the new eligibility contract requires;
- the current runner repeats the same generation seed for every recurrence of
  the same program and tick, so repeated visits are not independent stochastic
  opportunities;
- "one query before every continuation" is not "one query before every
  decision," because one continuation can emit and dispatch multiple ACTs;
- no exact workload, independent-root count, power rule, or implementable
  retrieval arithmetic is bound, so the claims and deadline cost cannot be
  evaluated.

## 1. Claim and estimand collisions

### 1.1 Common ATE destroys the PCFL carrier attribution

The candidate says every arm should receive ATE, while `ATE-PCFL` contains
admitted atom/link rows and performs graph expansion with personalized
PageRank. In the learned PCFL relay, the claim-bearing questions are whether
the LoRA carrier preserves necessary links, whether the actor follows
different paths under different goals, and whether an old-plus-new path
causes later action. If the LoRA arm also receives the complete external
typed graph and an automatic graph-expansion result, a successful action no
longer identifies any of those properties in LoRA. Adapter-off may behave
identically because ATE supplies the path.

**Required correction:** use phase-specific arm laws.

- For PCFL E2--E5 mechanism attribution, preserve the proposed common finite
  one-hop reader and compare `TEXT_SAME_SEMANTICS` with LoRA as alternative
  carriers. Do **not** mount the native ATE graph in the LoRA mechanism cells.
- Run `ATE-PCFL-NATIVE` as a separate standalone strong-system comparator.
  Its PPR/graph work is part of that system's computation, and success belongs
  to the active-memory system rather than to the child or LoRA.
- A later E10 longitudinal experiment may put ATE in both promotion arms when
  the estimand is explicitly "incremental value of promoted weights given
  strong text memory." That experiment cannot by itself support LoRA-formed
  connectedness or LoRA-over-ATE superiority.

### 1.2 Additive value is not system superiority

`ATE+promoted` versus `ATE+shadow` estimates the total causal effect of
promoting the adapter in a system that already has ATE. It does not compare
Dream--LoRA--Think against the strong memory baseline, and ATE can either mask
or synergize with the adapter. The separate same-source read is only a carrier
diagnostic and does not repair the missing autonomous comparison.

**Required correction:** bind the claim before selecting the arms.

- Incremental claim: `ATE+promoted` versus `ATE+true-shadow`.
- System-superiority claim: independently evolving `DLT-native` versus
  `frozen actor+ATE-native`, under the same public opportunity and generated-
  token envelope, with native resource use reported.
- If both effects are wanted, use the full preregistered 2x2
  `ATE off/on x LoRA promotion off/on`; do not infer either missing corner.
  "ATE off" must still specify whether the existing ledger/RECALL tool is
  present.

The existing paper-core note currently specifies direct full-learner versus
ATE-agent lives. Changing that to common ATE is a material architecture and
claim change and cannot occur silently in a baseline note.

### 1.3 "Byte-identical admitted evidence" is false under the three lanes

ATE receives raw events, deterministic aggregates, and self/compiled text.
LoRA receives response-target training spans, often repeated or paraphrased.
These are transformations of a common source ledger, not byte-identical
evidence. Moreover, the eligibility section excludes compiler-written prose
and repaired endpoints while the compiled lane admits every writer target
with recoverable provenance. Current child-frame evidence includes harness-
repaired endpoints, so the two rules select different sets.

**Required correction:** define two distinct comparisons.

1. `SAME_SEMANTICS`: one immutable list of eligible canonical payloads; the
   text carrier renders exactly those payloads and the LoRA corpus targets
   exactly those same payload bytes. This localizes access/transport.
2. `NATIVE_SYSTEMS`: both systems start from the same authoritative raw event
   frontier but may transform it differently. This compares complete systems,
   not byte-identical carriers.

Every candidate LoRA item must have a deterministic `eligible_for_matched_ATE`
decision before either carrier is built. Repaired, parent-authored, unsupported,
or compiler-originated semantic bytes must be either excluded from both or
placed in a separately named non-matched native-system lane.

### 1.4 Parenting would leak through childhood ATE

Excluding literal parent text is insufficient. A child can restate a parent's
lesson, after which the proposal admits that restatement as
`SELF_INTERPRETATION`. If the childhood ATE store survives parent removal,
the parent-absent exam can be solved through external text rather than through
the child's learned state. That invalidates bounded parenting persistence and
parenting-by-write interactions.

**Required correction:** the parenting contract must name the memory
lifecycle. For weight-persistence E4, begin the parent-absent exam with a
canonical empty ATE store and no legacy RECALL state. For E5 deployment,
initialize the same canonical empty deployment store in all four cells and
admit only post-fork deployment events. A separate whole-adult system test may
retain childhood episodic memory, but it cannot be used as the weight-carriage
test.

### 1.5 CompilerGym cannot supply the advertised saturation claim

The candidate correctly notes that CompilerGym repeats roughly 67 programs,
then nevertheless defines a CG plateau epsilon. Exact-current-program
retrieval will naturally approach a cache lookup after each program has been
seen. A flat curve can therefore mean schedule exhaustion, deterministic
repetition, or no remaining novel public information—not saturation of a
strong memory on an expanding problem.

**Required correction:** ATE-CG may support only a bounded finite-horizon
carrier/system comparison. Remove CG from the paper-facing `beyond active-text
saturation` gate. A plateau claim requires PCFL cohorts with mechanically
certified semantic novelty and scheduled new information at every cut.

## 2. Information flow and implementation mismatches

### 2.1 No existing eligible historical ledger

The current CompilerGym ledger stores rows such as `episode_id`, `tick`, raw
action text, outcome text, score, and truncated prompts. It does not contain
canonical `episode_instance_id`, `occurrence_index`, `decision_index`, native
dispatch bytes, immutable source-envelope bytes/hash, or the proposed event
hash. Consequently the proposed deadline step cannot simply construct ATE
from "already sealed eligible source ledgers" while claiming the new receipt
law.

**Required correction:** either collect a new schema-versioned source life, or
label a deterministic reconstruction from historical rows as a retrospective
diagnostic with weaker provenance. Never synthesize a source-envelope hash
from a lossy/truncated row and call it authoritative. A preflight must list
which existing roots are actually reconstructable and why.

### 2.2 Repeated-visit seed collision

The current batched runner derives generation seed from
`(episode_id,tick,base_seed)`. When the 67-program schedule repeats, the same
program at the same tick receives the same seed again. This can make later
visits replay identical continuations, exaggerate apparent stability, and
turn checkpoint samples into duplicates.

**Required correction:** all new ATE lives must address actor randomness by
at least `(scientific_root, episode_instance_id, occurrence_index,
decision_index, continuation_index, technical_replicate)`, with the same tape
address in paired arms. A CPU test must show that arm identity cannot change a
tape and that two occurrences of the same program do change it.

### 2.3 Batch chronology is undefined

The current wake runner advances several isolated episodes in lockstep; its
documented rule is that episodes in the same wake batch cannot see each
other's fresh ledger writes. A life-wide ATE updated "on the next
continuation" could accidentally reveal a sibling episode's same-round
outcome depending on update order.

**Required correction:** bind a causal frontier. Recommended rule: an episode
sees its own just-dispatched events on its next continuation, while cross-
episode events become visible only after the complete wake-batch barrier.
Index commits use a predeclared `(batch,round,episode_instance,decision)`
order, never process completion time. Test all batch permutations.

### 2.4 Continuation is not decision

The current parser dispatches every `ACT:` marker in one up-to-400-token
continuation. Those actions were all generated before any of their outcomes
could enter the next model context. One automatic query before the chunk is
therefore not a query before every decision, contrary to the candidate's
opening description.

**Required correction:** choose and name one of two interfaces:

- `QUERY_PER_CONTINUATION`: preserve multi-ACT chunks and claim only that;
- `QUERY_PER_DISPATCH`: stop consumption after the first legal ACT, dispatch
  it, update ATE, and start a fresh continuation. This materially changes the
  THINK interface and needs its own comparison.

Do not use "before every decision" for the first interface.

### 2.5 Legacy RECALL creates an unbound second memory path

Today, `RECALL:` immediately invokes `Ledger.recall`, while the candidate also
places the prior explicit query in the next automatic ATE query. The proposal
does not say whether both paths run, whether one replaces the other, how
multiple RECALL markers in a chunk are resolved, or which returned block wins
under context pressure.

**Required correction:** route all explicit recall through one state machine.
For example, the last well-formed RECALL in a continuation (maximum 64 child
tokens) becomes the next ATE query modifier; legacy `Ledger.recall` is disabled
in ATE cells. Malformed/multiple/late markers have fixed outcomes. Alternatively
retain legacy recall in every arm and factor it explicitly. Never silently
give ATE cells two readers.

### 2.6 The CG query and documents are unbounded or underspecified

The "latest NOTE or RECALL" has no byte/token cap or canonical escaping rule.
Compiled response spans have no maximum document length. The query omits the
current best action/score and most of the current episode history, potentially
handicapping retrieval, while exact-program reservation can hand back the best
historical answer and dominate repeated tasks.

**Required correction:** freeze exact normalized query bytes, per-field token
caps, missing sentinels, escaping, field order, and truncation side. Include
current best score/action and a deterministic bounded summary of all already
dispatched current-episode actions, or deliberately permit a bounded
agent-written query. Declare exact-program lookup a cache capability and
report novel-program results separately from repeated-program results.

### 2.7 Context-budget equality is asserted, not implemented

The current actor rebuilds context under a 22,000-character heuristic (about
6k tokens) inside a 16,384-token model window. Adding a tokenizer-measured
1,024-token block does not prove that no current-state or thought bytes are
evicted, especially because character length and tokenizer length diverge.

**Required correction:** build the complete chat-templated prompt first,
measure it with the pinned child tokenizer, reserve generation space, and
apply one exact partition-packing law shared by paired arms. Receipt must show
kept/dropped token IDs by partition. Overflow is a fixed failure or fixed
truncation, never backend truncation. LoRA-only/text-only carrier probes need
matched neutral padding if context length itself could change behavior.

## 3. `ATE-CG` scientific and arithmetic defects

### 3.1 The aggregate "LCB" is not valid on the current score domain

`mean - sqrt(log(20)/(2n))` is a one-sided Hoeffding form for values in
`[0,1]`. A CompilerGym action can increase instruction count and therefore
produce a negative raw reduction. No lower score bound is registered. The
formula also assumes a deterministic rule for reducing repeated observations
within a program, which is absent. It should not be presented as a confidence
bound without those conditions.

**Required correction:** either rename it a support-penalized ranking
heuristic, or define the aggregation utility as the task's clipped
`u=clip(score,0,1)`, choose exactly one deterministic value per
`(program,exact_sequence)` (the first authoritative dispatch is simplest),
and state that the value is used only for retrieval ranking, never inference.

### 3.2 Aggregate cards are a domain-specific algorithmic advantage

Exact-program best-action cards and cross-program sequence statistics are not
plain retrieval. They are a hand-coded optimizer over public scores. That is a
legitimate strong baseline, but it is stronger and more task-specific than
the raw indexed corpus and is not byte-matched to the LoRA dream compiler.

**Required correction:** label it `ATE-CG-AGG`, retain raw hybrid retrieval as
the generic baseline, and report both. A result against `ATE-CG-AGG` is a
strong system comparison; it is not a carrier-only comparison.

### 3.3 Retrieval arithmetic is not implementation-complete

The proposal omits BM25 `k1/b`, IDF formula, lexical normalization/stopword
law, dense normalization and precision, rank origin, duplicate-rank handling,
MMR similarity, relevance scaling, tie behavior inside reservations, document
maximums, and how raw and typed scores become comparable. "Greedy pass-token
diversity" is also undefined. Different reasonable implementations can change
the returned evidence.

**Required correction:** bind every arithmetic choice and provide golden
queries with byte-exact ordered IDs and rendered blocks before actor use. Use
integer/fixed-point comparisons or bind precision/platform and an exact tie
bucket. No library default may be normative by accident.

### 3.4 Development selection is noisy and incompletely defined

Mean AUC, the `0.01` near-tie rule, and measured retrieval latency have no
exact AUC integration, root weighting, paired uncertainty, cache/warmup, or
latency statistic. A hardware-noisy tie-break can choose the scientific
system. The candidate also freezes the hybrid constants without testing that
the chosen retriever is strong.

**Required correction:** define trapezoidal AUC on a fixed cut grid, average
within independent root first, and use a deterministic simplicity tie-break
after a predeclared paired equivalence band. If latency remains a tie-break,
use an isolated predeclared p50/p95 protocol; otherwise use returned bytes or
index complexity. A tiny fixed dev grid over BM25, dense, and RRF is preferable
to silently choosing one arbitrary hybrid.

## 4. `ATE-PCFL` conflicts and hidden solver work

### 4.1 It conflicts with the proposed finite reader

The current learned-PCFL proposal gives both carriers the same finite reader:
one exact one-hop lookup per typed call, one selected candidate, four charged
calls. The ATE candidate instead searches the entire store, seeds 16 rows,
runs 20 PageRank iterations, and packs several rows. These are different
interfaces and computational capabilities.

**Required correction:** keep the common finite reader for mechanistic
TEXT-versus-LoRA attribution. Treat hybrid/PPR ATE as a separate native
baseline with its own resource point. Never call the two read plans matched.

### 4.2 PageRank can perform the claimed traversal externally

PPR propagates query mass through all public edges before the child selects a
path. It can return a multi-hop neighborhood within one read even though the
PCFL actor is nominally limited to four one-hop reads. This is acceptable for
a strong external-memory system, but its success is evidence that the
retriever traversed the graph—not that the child or LoRA learned to traverse.

**Required correction:** report retriever path work (expanded nodes/edges and
distance) and use necessary-edge/PPR-off controls for the ATE system. Do not
use ATE-PPR output in the causal cells that license child/LoRA traversal.

### 4.3 Opaque-renaming equivariance is impossible as specified

A pretrained dense encoder and its subword tokenizer need not embed two
arbitrary opaque handle strings equivalently. Lexicographic `document_id`
tie-breaking can also change order after a bijective rename. Thus the required
byte-equivariant retrieval under arbitrary opaque-handle renaming will fail
even when semantics and equality are preserved.

**Required correction:** rank over an identifier-normalized projection. Map
opaque handles to equality-preserving local symbols by first public
appearance/registered public slot, run lexical/dense ranking on that
projection, render original handles only after selection, and tie-break by a
rename-invariant public ordinal. Alternatively weaken the test to a
predeclared finite token-class-preserving rename family and narrow the claim;
do not retain impossible arbitrary equivariance.

### 4.4 The PPR graph and score are not defined

It is unclear whether atom rows, link rows, or both are graph nodes; how a
link-row document gets a PPR score; whether edges are directed/weighted; how
dangling nodes behave; what "normalized RRF" means; how PPR and raw-row scores
share a scale; or how MMR compares raw prose with typed rows. Twenty floating-
point iterations do not by themselves define byte-deterministic ranking.

**Required correction:** provide a total graph construction and fixed-point
update, exact normalization, numeric precision, dangling rule, convergence-
independent fixed iteration, typed/raw score calibration, MMR equation, and
tie law. Golden bridge, null, deranged, disconnected, equal-score, and
rename cases must return exact IDs.

### 4.5 The PCFL query surface is absent

"Public goal/state" and 64 generated search tokens do not define exact bytes,
parsing, invalid queries, catalog visibility, repeated queries, HIT/MISS
handling, or whether query tokens count in the actor's generated budget. The
current PCFL proposal requires strict `READ/FOLLOW/ACT` emissions and a
finite adaptive closure; the ATE proposal has not reconciled that state
machine.

**Required correction:** bind one transition table for all four calls,
including automatic first query, optional query grammar, generated-token
charging, response block, repeated/malformed/empty behavior, stop, and the
terminal action. Prove the active baseline cannot read hidden compiler or
catalog values and cannot exceed its declared opportunity class.

## 5. Resource and statistical blockers

### 5.1 "No training GPU" is misleading for the primary experiment

ATE itself needs no fitting, but the actor still needs inference hardware and
the proposed true-shadow arm performs the identical LoRA compile/train
transaction. The primary ATE+promoted versus ATE+shadow factorial therefore
does consume the same training GPU work in both arms. Dense embeddings and
PPR also add nontrivial CPU/memory work.

**Required correction:** say "ATE has no parameter-training cost in a
standalone ATE-native life." Separately account actor inference and, in the
causal promotion experiment, shadow training.

### 5.2 The token-sufficiency sweep can dominate the project

The budget pilot alone permits:

```text
16 situations * 2 seeds * (16+32+64 continuations) * 2 actors
= 7,168 actor continuations
= 2,867,200 maximum generated tokens at 400 tokens/continuation.
```

At the 64-continuation choice, one 1,024-episode life permits 65,536 actor
calls and 26.2 million output tokens. Eight paired roots permit over one
million calls and 419 million output tokens before input-context cost. No
deadline/resource manifest or root count demonstrates feasibility. The
16-case point-estimate rule is also far too weak to distinguish a `0.007`
score change at observed CompilerGym noise.

**Required correction:** project calls, maximum and measured expected tokens,
prompt tokens, environment dispatches, wall time, and A40-hours for every
budget/root cell before model use. Budget selection needs either a powered
equivalence rule with independent situations as units or a declared generous
budget chosen from already valid development evidence. A resource ceiling may
return `NO_GO`; it may not silently lower the budget after outputs.

### 5.3 The access certificate's `n=100` is not justified

The certificate mixes deterministic instrument checks, model behavioral
rates, and a `0.01` noninferiority margin. One hundred cases may be enough for
a gross store-swap effect but generally cannot give a tight continuous-score
noninferiority bound at one percentage point. "Best" of three historical
comparators is also ambiguous: selecting the best on the same sealed
certificate creates selection bias, while three separate claims need a
simultaneous rule.

**Required correction:** use deterministic fixtures for mechanical gates and
choose behavioral certificate N from a presealed variance/power calculation.
Preselect the comparator on development, or require simultaneous
noninferiority to all three with an exact multiplicity rule. If affordable N
cannot resolve `0.01`, choose a scientifically justified wider adverse margin
before data or drop that gate.

### 5.4 Plateau and retention are incomplete

The plateau rule says neither interval gain may "exceed" epsilon, which lets a
large negative gain pass that clause. It leaves the lifetime grid, exact late
cuts, root N/power, AUC formula, old-cohort task construction, and
`epsilon_PCFL` justification open. "At least three" late cuts is not a
confirmatory contract.

**Required correction:** require each interval gain to be equivalent to zero
in `[-epsilon,+epsilon]`; freeze the exact information cohorts and all cuts;
define root-level trapezoidal AUC; define old-cohort retention cases and their
freshness; and bind N/power, SESOI, missing values, multiplicity, and stop
rules before confirmation materialization.

### 5.5 The promised Pareto curve has no sweep

One native ATE point plus one native LoRA point is not a cost--utility Pareto
curve. No memory-token, retrieval-compute, or writer-budget grid is registered.

**Required correction:** either remove the Pareto promise and report a cost
table, or predeclare a small feasible resource grid and compute the
nondominated points without post-hoc cell deletion.

## 6. Exact repaired role matrix

The successor should begin with this separation:

| Scientific role | ATE state | LoRA state | What it can establish |
|---|---|---|---|
| Access certificate | frozen opposing fixture stores | off | retriever/actor can find and use text |
| Same-semantics carrier | exact matched payload deck | exact same payload deck fitted | local text-vs-weight access only |
| PCFL E2--E5 mechanism | alternative exact-text finite reader | alternative LoRA finite reader | carrier-specific connection/traversal/one-cycle expansion |
| Native ATE system | evolving raw+derived store and native retriever | off | strength/plateau of external memory system |
| Incremental promotion | same ATE in both branches | promoted vs true-shadow | total effect of weights conditional on ATE |
| Direct system comparison | standalone ATE-native life | standalone DLT-native life | system superiority under reported native resources |
| Parenting persistence | canonical empty external store after parent deletion | on/off as registered | durable child-state effect without text carryover |

No result may migrate between rows without a separately defined bridge.

## 7. Minimal pre-implementation acceptance suite

Before source-authoring ratification, the successor proposal should contain
five exact artifacts:

1. **Role/claim matrix:** the table above expanded to every planned arm,
   naming which store survives each reset and which claim consumes each cell.
2. **Causal state machine:** exact event visibility frontier, batch barrier,
   query/RECALL/ACT order, one- versus multi-ACT semantics, update/refresh
   transactions, failure behavior, and sterile reset.
3. **Canonical schemas and rank arithmetic:** full event/document schemas,
   ID formulas, collision law, query/render bytes, tokenizer caps, BM25/dense/
   RRF/MMR/PPR equations, precision, and ties.
4. **Resource matrix:** exact development/certificate/scientific root counts,
   calls, maximum input/output tokens, environment actions, index operations,
   shadow fits, bytes, RAM/VRAM, A40-hours, and hard stop.
5. **Statistics/claim registry:** exact units, fixed cuts, AUC, margins,
   equivalence tests, power/N, adverse filling, multiplicity, release order,
   and prohibited claims.

After scoped implementation but before any scientific actor run, require only
the following nonredundant tests:

### A. Model-free interface gates

1. **Identity/eligibility:** canonical round trip, hashes, collision failure,
   exact dispatch/outcome join, and rejection of probe, parent, repaired,
   future, wrong-root, and unsupported items.
2. **Chronology:** own-next-continuation visibility, cross-episode batch
   barrier, insertion-order permutation, restart, refresh failure, and no
   future-row access all return exact expected roots/IDs.
3. **Randomness:** same tape across paired arms; distinct tape across repeat
   occurrences; arm label, process order, restart, and cache cannot change it.
4. **Single memory path:** exact query count; legacy RECALL cannot produce a
   second block; malformed/multiple RECALL and multi-ACT cases follow the
   bound transition table.
5. **Blindness:** hidden answer, future goal, arm, report identity, truth bit,
   candidate order, and capability handles cannot change query, ranks, IDs,
   or render when public bytes are fixed.
6. **Ranking/packing:** exact goldens for BM25/dense/fusion/reservations/MMR,
   boundary-fit/one-token-overflow, duplicates, supersession, equal scores,
   empty store, and store swap.
7. **Opaque identity:** consistent renaming leaves normalized rank inputs and
   selected public rows equivariant; inconsistent rename fails.
8. **Prompt budget:** chat-templated token count stays within the model bound;
   partition drops are byte-receipted and identical across matched arms; no
   backend truncation.
9. **Phase isolation:** childhood-to-deployment reset empties the required
   store; PCFL finite-reader cells cannot import PPR/ATE; native ATE cannot
   access compiler/hidden tables.
10. **Accounting:** every call, token, action, store/index mutation, cache,
    fit, byte, and failure reconciles exactly to the resource manifest.

### B. Small actor/access certificate

Use one presealed source-disjoint panel of opposing-store cases with common
random tapes. Each case has one designated necessary row and incompatible
correct actions under stores A and B. Run `GOLD`, `ATE`, `EMPTY`,
`IRRELEVANT`, `SWAP`, and `NECESSARY_ROW_CUT` conditions. Missing, malformed,
timeout, zero-action, and invalid output are failures. Require prospectively:

- exact-key necessary-row recall `=1.00`;
- public-semantic necessary-row recall `>=.95`;
- citation/root identity `=1.00`;
- ATE correct-action performance within the registered adverse margin of
  same-sign GOLD in both stores;
- positive store-swap redirection and necessary-row-cut effects with their
  predeclared confidence bounds;
- irrelevant-store non-harm relative to EMPTY;
- strict interface non-harm relative to EMPTY; and
- oracle/reference-search headroom over the best frozen routine.

The exact N and adverse margin must come from the bound power/resource audit;
`100` and `0.01` are not accepted merely because they appeared in the first
candidate. For ATE-PCFL add authentic-link, truthful-null, deranged-link,
bridge-cut, binding-twin, and PPR-off cells; the external retriever's path work
is a mediator, not child traversal.

### C. Promotion gate

Only after A and B pass may ATE enter a scientific arm. One dry-run root must
prove that true-shadow compiles and trains byte-identically to promoted,
differs only in active adapter promotion, begins from byte-identical ATE state,
and that report/probe processes cannot mutate either store. Any failure is
`BASELINE_INVALID`, never positive evidence for LoRA.

## Final recommendation

Do not discard ATE. Split it. `ATE-CG-RAW/AGG` is a valuable deadline
development comparator; `TEXT_SAME_SEMANTICS` remains the clean PCFL carrier
control; `ATE-PCFL-NATIVE` is the later strong standalone memory agent; and
common `ATE+promoted/shadow` is a separate incremental-weight experiment.
This separation preserves the candidate's strongest idea while preventing the
baseline from either being quietly handicapped or becoming the very mechanism
the LoRA is supposed to prove.
