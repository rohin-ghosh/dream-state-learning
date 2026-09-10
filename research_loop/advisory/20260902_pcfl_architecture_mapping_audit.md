# PCFL-Compose architecture-mapping audit

**Date:** 2026-09-02  
**Status:** read-only senior-scientist advisory. This document is not an
architecture consensus, ratification artifact, implementation scope, run
approval, or scientific result.

## Executive verdict

PCFL-Compose can be a strong **controlled assay of one narrow pass through the
Dream--Sleep--per-life-memory--Think architecture**. It does not, as presently
described, test the whole developmental architecture, and it can very easily
collapse into a known-algebra puzzle whose actual intelligence lives in an
exact compiler, a candidate generator, or a target-time planner.

Its genuine strengths are unusually clean:

- public action--outcome episodes are the only source of life-specific tool
  semantics;
- fresh tray handles force state-independent operator extraction;
- never-executed compound tools require factor completion rather than local
  transition lookup;
- noncommutativity makes the orientation relation behaviorally consequential;
- target-byte twins, whole-life memory swaps, factor cuts, and law cuts can
  identify whether life-specific memory changes action;
- old/new/cross-era targets can test finite per-life acquisition and retention
  after the raw stream exceeds context.

But those properties identify only a **prospective factor-law compilation and
use problem**. They do not by themselves establish autonomous dreaming,
connection-through-wake-traversal, learned sleep scheduling, hot-path
materialization, on-policy evidence acquisition, a learned LOOP adapter, or the
self-improving action--experience flywheel. The fixed anchor/chord explorer is
deliberately off-policy, the factor grammar is tiny, one event reveals a full
compound permutation, and a public exact program can recover the sufficient
statistic. The environment is therefore an algebraic mechanism microscope,
not yet a semantic developmental habitat.

The acceptance boundary is simple:

> In the headline organism, a frozen prompted resolver must propose the
> factorized connection target-blind from public life evidence; a restricted
> sleeper may format, deduplicate, provenance-check, and realize that committed
> content; a fresh per-life LoRA may transport it; and a goal-conditioned
> iterative resolver must retrieve local content and choose real actions. The
> exact factor solver and exact verification must remain labeled offline
> ceilings/scorers. If code derives the law, chooses the correct hypothesis, or
> plans the target action for the model, PCFL-Compose is not testing the
> architecture.

With that repair, Paper 1 may claim a fixed-controller, fixed-source,
prospective compiled-abstraction result and conditional per-life LoRA
transport. It still may not claim the online flywheel or a learned cognitive
policy. Without that repair, the honest paper is a benchmark of known-grammar
operator inference plus memory transport.

## 1. Architecture reconstructed from first principles

The intended organism is not “put facts in LoRA and ask questions.” It is a
causal loop with distinct ownership of content, operations, and timescales.

```text
present goal + public state + bounded working state
  -> WAKE / THINK RESOLVER
       choose one local operation
       query an associative memory or exact provenance handle
       update/revise an explicit working path
       act, release, defer, or request later replay
  -> public action + public outcome
  -> immutable episodic event with provenance
  -> DREAM CONNECTION
       replay selected episodes and prior semantic memories
       propose several local relations, exceptions, procedures,
       alternative access paths, and bounded shortcuts
       commit predictions before the relevant later evidence
  -> later public evidence marks proposals supported/contradicted
  -> SLEEP COMPILER
       canonicalize, deduplicate, preserve epistemic state/provenance,
       compile multiple access views, negatives, and eligible hot paths
  -> freshly scoped PER-LIFE MEMORY LORA
       lossy persistent associative access to life-specific local content
  -> LATER WAKE / THINK RESOLVER
       reconstruct a goal-specific path through iterative local reads
       compose in tokens/working state and choose an environment action
  -> changed outcomes and, eventually, changed future evidence
  -> repeat
```

This reconstruction follows `research_notes/00_THESIS.md`, notes 41--44, and
the active/alive rulings in `research_notes/IDEAS.md`. Five separations are
essential.

### 1.1 Wake/think traces

The thinker is a goal-conditioned state machine, not a one-shot answer prompt.
Its state contains the goal, public observations, unresolved dependencies,
workspace, provenance, and remaining operation/read budget. Each step performs
one typed query, one update/revision, one action, or one terminal decision.
The emitted trace records which local memories were actually retrieved and
co-traversed, which hypotheses failed, which action was released, and what
remained unresolved.

Those traces matter in two ways. Immediately, they externalize multi-hop
composition so the LoRA is not asked to “decompress” an entire graph. Later,
they are eligible sleep inputs: repeatedly useful two- or three-edge paths can
be materialized as bounded one-hop shortcuts, while failures become negative
controller data. A correct final action is insufficient evidence if the
recorded path used no authentic life memory.

### 1.2 Dream connection

Dream is the same recurrent resolver in a broader, episode-conditioned,
write-proposing mode. Wake is narrow and goal/grounding driven; dream is broad
and replay/surprise/uncertainty driven. Dreaming proposes multiple local
connections and prospective claims. It does not need to solve a held-out goal,
emit a global graph, or directly train weights.

The critical epistemic rule is chronological: a proposal precedes the evidence
that can support it. Rephrasing the same observation is not independent
support. An unresolved thinker agenda may select eligible episodes for later
replay, but it cannot contain a candidate answer or become evidence.

### 1.3 Sleep compilation

Sleep is the whole offline process; dreaming is the thinking within it. The
sleeper is principally a compiler and write sequencer. It can canonicalize,
deduplicate, merge support, preserve contradictions, generate equivalent
training views, and turn repeatedly traversed supported paths into bounded
shortcuts. It must preserve the distinction between:

1. **semantic graph growth:** a model proposed and later supported a new local
   relation; and
2. **LoRA realization:** an already accepted relation was rendered in several
   forms and installed for associative recognition.

A deterministic compiler may change representation. It may not invent the
correct law, search a hidden hypothesis space with an exact checker, or repair
a model's proposal using truth. Otherwise the compiler is the reasoner.

### 1.4 Per-life LoRA

The MEMORY LoRA is medium-rate, per-life state. It is newly initialized or
cumulatively rebuilt from the clean base for every distinct life, never shared
across evaluation worlds, and never confused with a future cross-life LOOP
adapter. Its first earned role is persistence and associative access to local
life-specific atoms, relations, exceptions, procedures, and supported
shortcuts. It is not credited with discovering the schema, storing an
invertible graph, or directly becoming the target action policy.

Exact episodic observations remain in a separate immutable store and may be
fetched only through budgeted provenance handles returned by the common
reader. Multi-hop composition remains in the thinker's tokens and workspace.
Recognition-assisted reads are a measured memory interface, not unaided
parametric recall.

### 1.5 Goal-conditioned iterative thinker

At use time, the thinker should ask for the missing local dependencies,
receive one immutable fact or `NOT_FOUND`, update a cited working path, and
replan until it releases one action, requests a later dream, defers, or exhausts
budget. Its intelligence includes query selection, conflict handling,
calibrated stopping, and goal-conditioned redirection. The memory substrate's
job is to make useful local associations available; the clean frozen reasoner
still owns explicit composition and action choice.

The future outer loop trains a reusable LOOP policy from complete causal
traces across development lives. That adapter learns how to retrieve, dream,
revise, act, and stop. It is separate from the per-life MEMORY LoRA and is not
part of the Paper-1 learning claim.

## 2. Arrow-by-arrow map into PCFL-Compose

The table distinguishes a real intervention from a suggestive score. “Partial”
means the world can support the arrow, but the current proposal does not yet
force the intended organ to own it.

| Intended causal arrow | PCFL-Compose realization | Required intervention / negative control | Primary metric | Audit disposition |
|---|---|---|---|---|
| Goal and current state -> thinker frontier | Start tray, goal tray, all D1/D4 menus, budgets | Exact goal twin changes only the goal; one-shot full-schema and random-query thinker controls | First-action redirection, useful-query precision, malformed/defer/stop rate | **Present but under-specified.** The goal twin identifies conditioning; it does not establish iterative resolution. |
| Local memory -> typed thinker read | Queries for witnessed operators, factor bindings, order, or relation; one local result per call | Candidate-only clean base, matched candidate-assisted text/LoRA, explicit index, wrong adapter, unaided LoRA | Per-kind found/not-found/conflict precision-recall, read fidelity, tokens/calls | **Possible, not automatic.** Candidate/index state can otherwise be the real memory. |
| Read -> cited working-path update -> replan | Explicit resolver state across bounded operations | One-shot planner; shuffled query results; correct local facts with composition links removed; oracle-reader thinker | Chain validity, dependency coverage, backtrack/revision quality, success at fixed calls | **Missing from the paper-world spec.** D4 success alone can be brute-force target-time algebra. |
| Thinker -> public action | `USE` then final `LOCK`; no credit for a reported label or plan | Goal twin, action-label permutation, exact program ceiling, no-memory planner | Realized trajectory value, first action, restricted actions-to-success, illegal/malformed rate | **Strong.** Execution credit is architecture-aligned. |
| Action -> public outcome-bearing experience | Fresh-handle before/after tray event from an executed compound tool | Shuffle action--outcome bindings; wrong-world/twin event stream; observed-tool table | Exact observed permutation recovery, supported-source coverage, shuffle effect | **Strong as ingestion.** Because the source explorer is fixed, it does not show memory-shaped action selection. |
| Experience -> immutable episodic/provenance store | Sealed public chronology with source event IDs | Remove provenance; corrupt a root event; cross-life canary; evaluation-state hash | Root-event coverage, provenance validity, contamination, state immutability | **Required but not fully operationalized in the advisory.** Must inherit note 44's store/taint contract. |
| Episodes/prior memories -> dream replay selection | Fixed anchor row/column and chord schedule | Matched random/recency replay; irrelevant-factor sham; agenda-answer laundering test | Eligible/selected coverage, replay cost, prospective schema yield | **Amortized, not learned.** PCFL fixes the selection policy and therefore cannot claim adaptive dreaming or sleep pressure. |
| Dream replay -> new local connection/provisional law | Target-blind resolver proposes factor bindings, orientation, and unseen-pair predictions from anchors | Prompted dream vs raw/atom-only, independent-law sentinel, commutative surrogate, generic-prompt vs PCFL-formula ceiling, bounded-k no-gate/self-check arms | Prospective chord precision/coverage, calibration/abstention, correct law before target, unseen-pair prediction | **The central missing ownership test.** If exact code derives the schema, DREAM was bypassed. |
| Later public outcome -> support/contradiction/revision | Presealed chord is executed after a committed prediction; comparator attaches its public result | Withhold chord; flip its outcome in a twin; prohibit post-outcome retries/repair; negative-law family | Support/contradiction accuracy, revision rate, false-support rate, correction latency | **Feasible if made chronological.** Seeing all chords and then fitting a law is ordinary batch induction, not prospective self-verification. |
| Supported semantic state -> sleep compiler | Frozen canonical `O(r+c)` schema, epistemic status, provenance, multiple training views | Prompted schema vs oracle schema; atom-only; edge/order-deleted facts; raw/direct-QA; closure-enumeration rejection | Admission precision/coverage, schema bytes, provenance, view equivalence, compiler failures | **Strong if the compiler is representational only.** A coded law fitter is a labeled ceiling. |
| Wake traversal trace -> sleep shortcut/connection | Repeated actual factor-composition path could become a supported bounded shortcut | Path-selected vs frequency-matched untraversed path; path-shuffled; M-before vs M-after trace; sham re-sleep | Later query/hop reduction at matched action value; authentic path mediation | **Absent.** Fixed source episodes contain no meaningful goal-conditioned traversal traces, and evaluation traces are sealed. |
| Compiled corpus -> per-life LoRA | Identical canonical schema realized in text and a life-scoped adapter | Same-corpus text/LoRA, direct-QA/raw LoRA, shuffled corpus, cross-life/twin adapter, training-seed panel | Atomic/reverse/paraphrase/partial-cue fidelity, calibration, bytes/FLOPs, action mediation | **Strong conditional transport test.** It is not schema discovery or learned reasoning-policy evidence. |
| Per-life LoRA -> later action | Thinker reads the adapter and executes never-seen compounds | Whole-life authentic/twin factorial, complete decisive factor swap, order-law cut, sham cut, lagged adapter | Unconditional and authentic-success-conditional change in first action and D4 value | **Potentially excellent.** Citation masking alone is invalid because the association remains in weights. |
| Repeated sleep checkpoints -> persistent life improvement | New factor blocks; `M_k`; old/new/cross-era targets after context | `M_k-1` on new targets; earliest snapshot; old/new/both factor cuts; frozen truncation and native context | Acquisition, old-factor noninferiority, cross-era value, post-context AUC, failure-inclusive curve | **Finite persistence only.** This does not show that memory improved the experience distribution. |
| Better action -> better/new future evidence -> later dream | Would require arm-selected surveys/interventions whose outcomes re-enter the life | Randomized memory at a branch, equal action budget, cross-system experience swap | Information gain, evidence quality, later memory/action mediation | **Absent by design.** Fixed open-loop source actions break this arrow. Defer the flywheel claim. |
| Across-life traces -> reusable LOOP adapter | Causal dream/think operation transcripts on development worlds | Prompt-only controller, proposal-only BC, shuffled operation order, whole-world heldout open-loop eval | Operation efficiency, unseen-world action, stop/revisit quality | **Absent and properly deferred.** |
| Outcome value -> sleep pressure / critic / scheduler | None; sleep occurs at fixed checkpoints | Learned-vs-fixed schedule at matched compute | Marginal action value per sleep FLOP; calibration | **Absent and properly deferred.** |

This map yields a sharp conclusion. PCFL-Compose natively supports the lower
chain

```text
public experience -> prospective schema -> compiled corpus
-> per-life transport -> goal-conditioned action
```

but not the complete recurrent chain

```text
memory-shaped thought/action -> better evidence -> dream/revision
-> learned scheduling/controller -> still better later action.
```

## 3. Does the environment reward the intended operation?

### 3.1 What it rewards correctly

PCFL-Compose does reward four operations the architecture needs.

First, fresh object handles mean that success on an executed tool requires a
state-independent positional abstraction rather than memorizing one tray.
Second, target tools are never executed, so a local tool table cannot solve the
headline split. Third, noncommuting factor operators make the higher-order
orientation relation causally necessary. Fourth, D4 and exact goal twins
require remembered life-specific structure to be used under the present goal
in a real environment trajectory.

The old/new/cross-era split is also well matched to a per-life substrate. It
can distinguish fresh installation, persistence, and recombination instead of
hiding them in one endpoint. Authentic/twin whole-life adapters and law/factor
cuts are unusually strong tests that the transported life content caused the
action.

### 3.2 Where it becomes merely algebra

The hidden family has a known exact sufficient statistic: anchor operators,
one shared anchor, and one orientation bit. Given the anchor/chord schedule, an
exact public program can infer the law and enumerate target sequences. The
public two-part morphology advertises the factorization. If the prompt states
the two equations or code computes them, the “dream” problem has already been
solved; the remaining work is parameter estimation, storage, and small search.

The source ontology is also intentionally nonce. That makes it a useful
zero-prior control, but it departs from the repository's prior-anchored world
doctrine. It says little about whether a pretrained agent connects lived
experience to rich semantic priors. Any paper conclusion must name the frozen
algebraic world and model, not generalize to naturalistic agency.

One observed compound event reveals the entire `S_6` permutation. Thus there
is no diffuse within-tool evidence problem, and no need to reconcile several
partial views before a local operator is known. The difficult step is a tiny
global factor law. This is closer to controlled program induction than to an
experiential world model with noisy local causality, exceptions, and revision.

D4 does not automatically rescue the construct. With two choices at each of
four visible stages, the planner can enumerate only sixteen action sequences.
If all factor operators are supplied in one prompt or by an exact reader, a
one-shot clean-base solver can choose the sequence without an iterative thinker.
The one-shot full-schema control is therefore mandatory.

### 3.3 The reader-budget feasibility trap

The local-reader contract must be reconciled with the exact information needed
by D4 before any model run. In the advertised twin construction, each of four
stage menus can contain two swapped stems with a shared suffix. If stages are
factor-disjoint, exact planning can require up to eight stem operators, four
suffix operators, the anchor `M`, and the orientation: roughly fourteen local
semantic items. A four-query cap cannot expose that information unless one
read returns a composite schema or the target reuses factors.

That creates two symmetric errors:

- set the cap below the certified local information demand, and memory failure
  is merely interface starvation;
- return a whole schema or completed compound per query, and the reader becomes
  a solution packet rather than local associative access.

The generator should emit an itemwise **minimum local-read certificate**. The
primary query cap must cover the exact program's legitimate local reads while
remaining fixed across text and LoRA. If a compressed shortcut reduces that
demand, it must have been formed target-blind from eligible prior traversals,
not generated around the target.

### 3.4 Overall construct judgment

The environment rewards the intended operation **only in a narrow,
mechanistically useful sense**: learn a life-specific factorized operator
model from actions, preserve it, retrieve it, and use it toward a new goal. It
does not naturally reward adaptive replay, autonomous family discovery,
trace-based connection growth, exception handling, or memory-shaped
exploration. Those are absent rather than falsified.

For that reason, call PCFL-Compose an “algebraic organism microscope” in
internal reasoning. In the paper, use “prospective factorized operator
completion from action--outcome experience.” Do not use “world-model growth,”
“self-learning flywheel,” or “autonomous dream discovery” unless separate
experiments directly identify those claims.

## 4. What Paper 1 must contain

If Paper 1 is meant to bear on Dream--Sleep--LoRA--Think rather than merely
introduce PCFL-Compose, the following is the minimum non-negotiable package.

### 4.1 One complete prompted-organism path

At least one headline condition must execute, without oracle substitution:

```text
public source action/outcome events
  -> target-blind prompted dream proposals
  -> chronological public support/contradiction
  -> restricted sleep compilation
  -> same frozen accepted corpus in text and per-life LoRA
  -> iterative typed reads and working-state updates
  -> public D1/D4 actions and LOCK
```

All intermediate products and denominators must be scored. A correct endpoint
cannot conceal a failed dream whose output was replaced by an oracle schema, a
failed adapter bypassed by candidates, or a one-shot planner bypassing the
thinker.

### 4.2 Frozen prompt ownership

The dream and wake policies may be fixed prompts/state machines shared across
all lives. They must use a common operation grammar and differ only in input,
grounding, and write/action permissions. Prompts, schemas, parser, stopping
rules, candidate policy, and budgets must freeze on development worlds and be
evaluated on whole held-out world-lives.

The primary dream prompt may advertise that tools have public stems and
suffixes and may give generic operations such as compare, hypothesize,
compose, test, and defer. It should not state the two PCFL completion equations
or tell the model which family is true. A PCFL-formula prompt is useful as a
labeled ceiling. The factorized and independent-law families must use the same
primary prompt so abstention or family discrimination is measurable.

### 4.3 Prospective, bounded dreaming

From anchors alone, the resolver commits a bounded number `k` of local
candidate relations and explicit chord predictions. `k` must be small,
predeclared, and charged whether candidates succeed or fail. Chord outcomes
arrive later as ordinary public experience. Only then may the public comparator
append support or contradiction status. No hidden retries or exhaustive
propose-and-filter loop is allowed.

The compiler then freezes before goals and target pair identities are visible.
Unsupported, malformed, abstained, compiler-failed, LoRA-training-failed, and
runtime-failed targets stay in the original world-life denominator.

### 4.4 The organ factorial

The smallest causal factorial is:

1. raw public chronology with iterative RAG;
2. native linked/A-MEM-style memory with target-time abstraction allowed;
3. observed-tool table without factor completion;
4. exact public factor program ceiling;
5. oracle-schema text, bypassing dream;
6. prompted compiled text;
7. the byte-identical prompted corpus in per-life LoRA;
8. raw/direct-QA LoRA;
9. atom/full-factor facts with the orientation/composition relation removed;
10. candidate-only clean base, wrong/twin adapter, and unaided LoRA reader
    sentinels.

This is not gratuitous breadth. Each cell removes a distinct place where the
claimed organ can be bypassed: target-time abstraction, dream proposal,
compilation, substrate, candidate/index, or iterative use.

### 4.5 Causal action and lifetime tests

At one registered post-context sentinel, require the authentic/twin
world-by-memory factorial, order-law cut, decisive factor cut, matched sham,
goal twin, and independent-law negative sentinel. Across the lifetime curve,
require a pre-native checkpoint and at least three genuinely post-native
checkpoints with increasing factor entropy, not filler or replay tokens.

Report new acquisition, earliest-factor retention, and cross-era D4 separately
with lagged snapshots. The independent unit is the world-life/twin pair. Calls,
targets, stages, and training seeds are nested diagnostics, not replicates.

### 4.6 LoRA earns only conditional claims

The LoRA condition must be life-reset, causally bound to its world, and trained
from the identical accepted schema used by the text condition. Report atomic,
reverse, paraphrase, and partial-cue fidelity; candidate/index bytes; canonical
and realized corpus bytes; repetitions; adapter/optimizer state; FLOPs;
query/think work; and action amortization.

For the architecture to count as operational, the LoRA should at minimum:

- beat clean-base candidate-only, wrong/twin adapter, and shuffled/cross-life
  controls;
- preserve authentic life bindings well enough for above-chance D4 action;
- show the predicted directional action loss under a law or binding
  intervention; and
- be noninferior to the identical text corpus within a predeclared practical
  margin, or occupy a clearly useful disclosed resource/Pareto point.

If compiled text works and LoRA does not, the DREAM/SLEEP compiler result can
survive, but the per-life parametric organ has failed. If text dominates at all
resource points, LoRA belongs in a diagnostic table, not the title.

## 5. What is legitimately amortized or supplied by prompts

Paper 1 need not learn every organ. The thesis explicitly allows everything
except the per-life substrate to be amortized at this stage. The following may
therefore be frozen and supplied, provided the claims are correspondingly
narrow:

- a generic resolver operation grammar and separate fixed wake/dream mode
  prompts;
- the open-loop anchor/chord source schedule and fixed sleep checkpoints;
- replay priority rules, maximum proposal count, and stopping budgets;
- schema/parser definitions and deterministic representation transforms;
- deduplication, provenance-cycle rejection, taint enforcement, append-only
  status updates, and generation of logically equivalent training views;
- a public-outcome comparator applied only after immutable prediction
  commitment;
- a full, target-independent candidate universe plus `NOT_FOUND`, if its bytes
  and work are counted and candidate-only controls are run;
- the frozen clean base's arithmetic/composition ability at target time; and
  the exact PCFL factor program as a clearly labeled construct ceiling.

These supplied mechanisms make the current paper a test of **information flow
through a frozen reference organism**, not evidence that the organism learned
how to think or dream. Prompt scaffolding is legitimate process guidance; a
prompt containing the correct PCFL completion formula is solution guidance and
must be a ceiling. A deterministic compiler can re-express a proposed law; it
cannot be the primary source of that law.

Similarly, mechanically extracting an observed before/after tray permutation
may be declared public preprocessing. If so, the paper does not claim the
dreamer learned local operator extraction; its claimed abstraction begins at
factor binding and composition order. This ownership choice must be explicit.

## 6. What should be deferred

The following are valuable but would either overstate PCFL-Compose or explode
the Paper-1 surface:

- learned LOOP adapter, conditional prefix/controller, or controller RL;
- learned outcome critic, value-guided sleep scheduling, or sleep pressure;
- on-policy exploration and the claim that better memory creates better future
  evidence;
- full action -> evidence -> dream -> memory -> action flywheel;
- autonomous discovery over an open-ended schema family;
- human-development, naturalistic embodiment, or external-validity claims;
- broad semantic worlds, exceptions, controlled rule change, and correction
  half-life;
- rank-by-compression surfaces, Goldilocks-capacity conclusions, and
  asymptotic/sublinear compression claims;
- multiple backbones, large skin grids, noise, public platform polish, and the
  full reader/rank/intervention Cartesian product;
- claims that the LoRA itself stores a graph, performs multi-hop reasoning, or
  has learned a general action policy.

One small **wake-trace-to-sleep sentinel** is worth preserving as a diagnostic,
not a headline requirement for the fixed-source causal paper: after `M1`, let
the frozen resolver solve presealed ordinary practice goals whose outcomes are
allowed into the life; compile only repeatedly traversed supported paths into
`M2`; compare `M2` against `M1`, path-shuffled re-sleep, and equal-compute sham
sleep on different held-out goals. The only licensed positive claim is that an
authentic traversal-conditioned write reduced later local reads or hops at
matched action value. Because practice behavior can change the ensuing
experience, this sentinel must be analyzed separately from the common-deck
substrate comparison. It does not establish the full flywheel.

## 7. Smallest honest end-to-end organism protocol

The following protocol is the minimum I would accept as evidence that
PCFL-Compose exercised the intended Paper-1 organism rather than only an exact
algebra solver.

### Phase 0: seal the life

Before realizing outcomes, seal world/twin factors, source episodes, anchor
roles, prospective validation chords, independent-law assignment, factor-era
blocks, D1/D4 targets, goal twins, target pair exclusions, memory interventions,
failure denominators, and RNG/rendering manifests. Certify target-byte equality
and that no registered target compound was executed. Keep hidden truth,
certificates, and exact solver output in scorer-only storage.

### Phase 1: live public anchor experience

Execute the fixed target- and outcome-blind explorer on fresh trays. Append
only public `RESET/OBSERVE/USE/ARRIVED` events to the immutable episodic store.
If a deterministic permutation extractor is used, label it supplied
preprocessing and apply it identically to every memory arm.

### Phase 2: blind Dream-1

Invoke the frozen resolver in DREAM mode on the eligible anchor prefix. It may
retrieve bounded public episodes and prior supported memories, then emit up to
`k` local candidate bindings/order relations and predictions for presealed
validation chords. The exact factor formula, validation outcomes, target pairs,
goals, solver, and world side are invisible. Preserve every proposal,
abstention, malformed output, and provenance root.

### Phase 3: chronological environmental validation

Execute the presealed chord actions as ordinary life events. A mechanical
comparator attaches only `SUPPORTED` or `CONTRADICTED` to already committed
predictions. It does not generate, normalize, rank, repair, or retry them. In
the independent-law family, a global factor law should remain unsupported and
the organism should abstain or stay near chance.

### Phase 4: Dream-2 and sleep compilation

The same resolver may perform one bounded revision pass using the now-public
chord events and append-only statuses. The sleeper admits only eligible
supported local content; canonicalizes/deduplicates it; preserves root
provenance and contradictions; rejects complete target solutions and closure
enumeration; and creates the fixed access views. Freeze and hash this semantic
snapshot before rendering any evaluation goal.

This two-step dream is the smallest real recurrent connection test: propose,
receive ordinary evidence, revise. A single batch after all chords is a useful
batch-induction control but should not be described as prospective dreaming.

### Phase 5: matched text and per-life realization

Mount the frozen snapshot through the common text reader and train a fresh
life-scoped LoRA from the byte-identical accepted semantic content and fixed
view generator. Save all failed writes. Verify recognition reads on a disjoint
non-target battery; then freeze both memories. No evaluation outcome may alter
the corpus, reader, candidates, or adapter.

### Phase 6: iterative Wake/Think evaluation

For each sealed goal, clear context/KV/workspace, show the public start tray,
goal, menus, and budgets, and run the frozen WAKE state machine. Each call may
query one local dependency, update/revise workspace, release one public action,
defer, or stop. The environment applies released actions and returns the real
public tray. No reset or hidden counterfactual feedback is available. Credit
only the executed trajectory and final `LOCK`.

The exact local-read certificate determines a fair cap. Score query selection,
reader fidelity, working-chain validity, planning correctness, first-action
goal redirection, and terminal action separately.

### Phase 7: causal forks and lifetime checkpoints

At the sentinel checkpoint, replay the same target under authentic/twin
whole-life memories, correct/wrong order memories, decisive factor cuts, and
equal-size shams. Across checkpoints, test `M_k` and `M_k-1` on presealed new,
old, and cross-era targets. Preserve failure-inclusive world-life/twin-pair
analysis and full resource accounting.

This protocol closes one honest information-flow pass and one prospective
revision:

```text
experience -> dream proposal -> public validation -> sleep compile
-> per-life memory -> iterative goal-conditioned action.
```

It still does not close the on-policy developmental flywheel. The paper must
say so.

## 8. Mechanical-verification oracle firewall

PCFL's exactness is scientifically useful only if the machinery remains
outside cognition. The following firewall should be treated as a protocol
invariant.

1. **Separate certifier, comparator, compiler, and actor.** The certifier sees
   hidden factors and proves construct validity before runs. The comparator
   sees a committed prediction and a later public outcome. The compiler sees
   only eligible public/semantic records. The actor sees only model-visible
   state and memory reads. No process inherits a stronger process's fields,
   filenames, cache keys, exception strings, or timing signals.
2. **Commit before compare.** Hash prediction bytes, operands, provenance,
   target observable, world version, and deadline before the relevant outcome
   exists. The comparator may perform an exact equality check only afterward.
3. **No propose-and-filter oracle.** Bound `k`, charge every proposal, forbid
   adaptive retries after feedback, retain false candidates, and report both
   precision and total preassigned coverage. An exhaustive list plus perfect
   filtering is an exact solver even if each individual check is “mechanical.”
4. **No solver-derived positive data.** Exact factors, completions,
   certificates, target paths, and hidden labels never become prompts,
   candidates, retrieval keys, corpus examples, negatives, or trainer state in
   a headline condition. Oracle-schema and exact-program arms are separate.
5. **No target-aware compilation.** Evaluation goals, reserved target pair
   identities, allocation, target templates, and every descendant artifact are
   tainted. The compiler snapshot is hashed before target rendering.
6. **No candidate smuggling.** A candidate universe must contain all legal
   public values plus `NOT_FOUND`, be target-independent, and be counted as
   retained external state. Candidate-only clean-base and wrong-adapter cells
   must score every headline checkpoint.
7. **No action oracle.** During evaluation, the engine applies the action the
   model selected and returns only the resulting public tray. It never reports
   whether that action was on the unique path, ranks menus, repairs syntax, or
   supplies a counterfactual. Exact target search belongs solely to the labeled
   program ceiling.
8. **No post-hoc denominator.** Unsupported schema, failed compilation,
   adapter underfit, timeout, malformed read, and wrong action remain failures
   in the presealed world-life assignment. Success-conditioned diagnostics are
   secondary to unconditional effects.
9. **Evaluation is sterile.** Target outcomes, scorer verdicts, proof paths,
   and model-judge explanations never re-enter episodic or semantic state.
   Pre/post life hashes must be byte-identical.

The core distinction is that **public chronological feedback may support a
previously committed idea; hidden truth may only score it**. A checker that
chooses among uncommitted candidates or repairs a representation is no longer
a checker—it is the cognitive policy.

## 9. Strongest falsifiers

The strongest falsifiers are organ-removal tests, not a low aggregate score.

1. **Dream removal:** raw recurrent RAG or native A-MEM induces the law at
   target time and matches prompted compiled memory at matched work. Then
   prospective sleep compilation adds no demonstrated value.
2. **Connection removal:** full factor atoms with the orientation/composition
   relation deleted match the compiled schema. Then no stored higher-order
   connection was necessary.
3. **Prompt/formula substitution:** a generic dream prompt fails while a prompt
   containing the PCFL equations succeeds. Then the result is known-grammar
   parameter fitting, not dream abstraction.
4. **Exact-program-only success:** the public exact program solves the world
   while every neural dream condition fails. The benchmark is valid; the
   neural architecture hypothesis is not.
5. **Compiler bypass:** oracle-schema text succeeds but prompted compiled text
   fails. The bottleneck is dream/compilation, not memory or thinking.
6. **Sleep removal:** direct-QA/raw-transition LoRA matches the compiled LoRA.
   Explicit sleep compilation has not earned causal value.
7. **LoRA removal:** identical compiled text matches or dominates LoRA across
   the disclosed resource frontier, or LoRA fails wrong/twin and binding-cut
   mediation. The parametric substrate is unnecessary or unfaithful over the
   tested range.
8. **Reader removal:** candidate-only clean base or explicit index matches the
   adapter, or recognition-assisted gains vanish in unaided reads. The result
   belongs to candidate enumeration/indexing, not weights.
9. **Think-loop removal:** a one-shot full-schema planner matches the iterative
   state machine at the same information and compute. Iterative query/replan is
   unnecessary for this environment.
10. **Goal-conditioning failure:** the exact goal twin does not redirect the
    first action and later trajectory. The policy is following target-insensitive
    priors or a memorized sequence.
11. **Life-binding failure:** wrong/twin/cross-life memory preserves authentic
    value, or decisive law/factor cuts do no more harm than sham cuts. The
    action is not causally using life-specific memory.
12. **Negative-law failure:** unseen-pair value rises above chance in the
    independent-table family. Treat the assay as leaked, shortcuttable, or
    hallucination-selected.
13. **Chronology failure:** pre-chord and post-chord corpus/action are equal, or
    the model only succeeds when outcomes precede “prediction.” Prospective
    connection and revision are unsupported.
14. **Persistence failure:** `M_k-1` solves new-factor targets, or `M_k` fails
    earliest-factor retention and cross-era composition. Acquisition is leaked
    or the per-life store does not sustain useful growth.
15. **Resource explanation:** gains disappear when environment actions,
    resolver/read tokens, candidate/index bytes, adapter capacity, repetitions,
    and compilation/training compute are matched. There is no architecture
    advantage.
16. **Trace-path failure:** in the optional recurrence sentinel, path-selected
    sleep does not reduce later reads/hops over a path-shuffled equal-compute
    sleep. Connection-through-traversal and shortcut materialization remain
    unsupported.

Any null should narrow the corresponding organ claim without invalidating the
other identified links. For example, compiled text success plus LoRA failure
is still evidence for prospective schema utility; exact-program dominance is
still evidence that the construct is solvable; fixed-deck gain without
memory-shaped exploration is still a representation/use result.

## 10. Paper disposition

### Recommended Paper-1 identity

If the organism protocol above is implemented, the strongest honest thesis is:

> In a controlled fixed-source permutation workshop, a frozen prompted
> resolver can be tested for whether it prospectively connects public
> action--outcome evidence into a supported factor law, a restricted sleeper
> can compile that law into per-life text and LoRA memories, and a bounded
> goal-conditioned resolver can use those memories to execute never-observed
> old/new compound actions after raw history exceeds context.

The contribution is the causal decomposition and assay, not a new LoRA
algorithm, autonomous self-learning, or a claim that algebraic factorization is
general world-model development.

### If the prompted-organism ownership test is not added

Then PCFL-Compose should be a schema sentinel or controlled benchmark section,
not evidence for Dream--Sleep--LoRA--Think. The honest thesis becomes:

> A target-blind known-grammar factor compiler and bounded planner can be
> causally evaluated across text and parametric per-life substrates on unseen
> noncommutative action compounds.

That can still be publishable as a measurement contribution, especially with
the exact twins and intervention suite, but it is not the architecture claim.
PCFL-Stream may remain the safer retention-oriented Paper-1 core; PCFL-Compose
then supplies the necessary but separate abstraction microscope. Conversely,
if the project wants one architecture-facing core, Compose is preferable to a
pure transition stream only after the ownership and oracle-firewall repairs.

### Final judgment

PCFL-Compose is not “merely” an algebra puzzle: its causal twins, unseen
compounds, fresh states, post-context life, and action execution can test real
experiential abstraction and transport. But algebra is the task, and without
strict organ ownership the exact structure makes bypasses easier than the
intended cognition. The smallest honest result is therefore a **fixed-source,
fixed-controller, one-cycle organism result**. The recurrent self-improving
organism remains a later experiment.

## Source basis

This audit was grounded in:

- `AGENTS.md`;
- `research_notes/00_THESIS.md`;
- `research_notes/41_capacity_compression_and_loop_training.md`;
- `research_notes/42_system_thesis_and_experiment_map.md`;
- `research_notes/43_developmental_experiential_learning_v1.md`;
- `research_notes/44_developmental_protocol_v2.md`;
- the architecture-relevant active/alive rulings in
  `research_notes/IDEAS.md`;
- `research_loop/advisory/20260902_pcfl_compose_paper_world.md`;
- `research_loop/advisory/20260902_pcfl_stream_area_chair_review.md`;
- `research_loop/advisory/20260902_pcfl_compose_crosscritique_fast.md`; and
- `research_loop/advisory/20260902_pcfl_compose_novelty_audit.md`.

No code, model, network, environment, or experiment was run. No implementation
or execution is authorized by this advisory.
