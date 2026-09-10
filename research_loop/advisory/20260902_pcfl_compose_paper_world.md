# PCFL-Compose paper-world design advisory

**Date:** 2026-09-02

**Status:** read-only scientific design advisory. This is not an architecture
consensus, ratification artifact, implementation scope, model/provider/network
authorization, GPU authorization, experiment approval, or scientific result.

## Recommendation

Replace the independent transition-tree proposal rather than extend it. The
smallest credible paper environment is a factorized, noncommutative action
world: **PCFL-Compose / Compound-Tool Workshop**.

The prior recommendation to cut PCFL-Schema was correct for a storage-focused
PCFL-Stream paper. After the transition-tree audit, however, a small prospective
schema is necessary if the intended paper is meant to test DREAM-style
abstraction rather than indexed retention. It should become the core construct,
not an additional rung. If the schema is not adopted, the honest paper remains
a fixed-source causal storage/retrieval benchmark with no DREAM abstraction or
compression claim.

## One-sentence construct

A life exposes only public action--outcome rearrangements from a sparse set of
compound tools; a hidden per-life factor law makes never-executed tool
combinations predictable, and goal-conditioned depth-four tasks require the
agent to infer, retain, compose, and execute that law across old and new
factors after raw history exceeds context.

## Latent generative law

The public state is a tray of six fresh, uniquely named objects in six ordered
slots. A state is therefore a permutation `x` in `S_6`.

Every public tool has two visible nonce morphemes:

```text
USE(stem_i, suffix_j)
```

For each life, hidden bindings assign permutations `A_i, B_j` in `S_6`. One
hidden life-level orientation bit `h` selects one of two laws:

```text
h = 0: T[i,j] = B[j] composed after A[i]
h = 1: T[i,j] = A[i] composed after B[j]
```

Using a tool applies `T[i,j]` to the current tray. Public labels carry no
pretrained semantic information. The two-part morphology is public, but the
factor bindings and the composition order are life-specific and can be learned
only from that life's outcomes.

Noncommutative permutations are the smallest useful middle ground. Independent
transition bits collapse to lookup; XOR or translations make order irrelevant
and invite endpoint decoding. `S_6` keeps the world exact and enumerable while
providing enough states for sixteen depth-four action sequences to have unique
terminal arrangements.

For `r` stems and `c` suffixes, the observable hidden family has the exact
sufficient statistic

```text
(r + c - 1) group elements + one orientation bit
```

or `(r + c - 1) log2(6!) + 1` bits before serialization. It defines `r*c`
compound action programs. Increasing a life adds genuinely new factor
permutations and hence new independent causal information, while the learned
law gives reusable generative coverage over a quadratically larger set of
compound actions.

This supports a factorized-abstraction claim. Because the independent
information and exact sufficient statistic both grow linearly in the number of
factors, it does not by itself support an asymptotic compression claim over
independent information.

## Public episodes, actions, and outcomes

The environment never emits transition rules, permutations, schemas, proofs,
support labels, target paths, or QA pairs. An ordinary source episode is only:

```text
RESET tray=[six fresh object handles in ordered slots]
OBSERVE tray=[...]
USE(stem_i, suffix_j)
ARRIVED tray=[the six handles in their new slots]
cost=1
```

All six handles are distinct. One before/after event is therefore sufficient
in principle to infer the compound permutation, but only by abstracting a
state-independent positional operation from an actual intervention. Evaluation
uses fresh handles and never repeats the exact source state.

There is no passive fact deck and no environment query such as
`WHAT_DOES(tool)`. The only source of action semantics is executing a public
action and observing its public outcome. Every memory arm receives the same
immutable public chronology.

## Source policy and target blindness

The Paper-1 source policy is a fixed common coverage explorer. It is open-loop,
target-blind, and outcome-blind:

1. Publicly designate or mechanically choose anchor morphemes `i0` and `j0`.
2. Execute the anchor row `T[i,j0]` and anchor column `T[i0,j]` on fresh trays.
3. Execute a small, presealed set of chord pairs sufficient to distinguish the
   two possible composition orders.
4. Reserve disjoint pair roles for prospective schema probes and action
   targets; those compound tools are never executed in the source life.
5. Introduce new paired stems and suffixes in geometric lifetime blocks.
6. Balance every scheduled source action under the twin involution.
7. Never let an outcome change a later source action, target, checkpoint,
   retained item, compiler admission decision, or arm allocation.

Edge roles, source order, reset trays, targets, depths, ages, checkpoints,
twins, and failure semantics must be sealed before source realization.
Introduced, supported, abstracted, compiled, readable, and action-usable
coverage remain separate denominators. Unsupported, malformed, compiler-failed,
training-failed, timeout, and runtime-failed assignments remain in the
world-life denominator.

The compiler may see only the eligible public source prefix and public
provenance. It may not see evaluation goals, target pair identities, target
templates or allocation, hidden factors, solver output, certificates, arm or
capacity assignments, earlier arm outcomes, or any descendant channel carrying
them. The resulting schema is frozen and hashed before target rendering. It
cannot be repaired after prospective probes or evaluation outcomes.

This is deliberately fixed-source/off-policy for causal attribution. It does
not test memory-selected exploration or the complete online flywheel.

## Exact public inference

Write the observed anchor transformations as:

```text
R[i] = T[i,j0]
C[j] = T[i0,j]
M    = T[i0,j0]
```

The two candidate completions for any never-executed pair are:

```text
h = 0: T[i,j] = C[j] * inverse(M) * R[i]
h = 1: T[i,j] = R[i] * inverse(M) * C[j]
```

Public chord outcomes identify the correct order. The generator must certify
that the wrong order disagrees on the registered prospective and target pairs.
A target-blind compiler can then emit an `O(r+c)` canonical schema consisting
of:

- the supported orientation;
- the anchor-relative operators `R[i]` and `C[j]`;
- `M` and the public composition rule;
- source provenance, prediction time, confidence, and support status.

It must not enumerate the `O(r*c)` closure. A small, presealed chord set should
be predicted and committed before those chord outcomes are exposed to the
scorer. Separate never-executed pairs remain for primary action evaluation.

The exact public-only program baseline is given the finite hypothesis class,
recovers permutations from source outcomes, selects the order using public
chords, stores the canonical sufficient statistic, and plans exactly. It must
score one itemwise under the declared caps before any model evaluation. It is a
ceiling and construct certificate, not a baseline DREAM is expected to beat.

## Prospective negative-law control

Include a small sentinel family with the identical renderer, labels, source
schedule, target construction, permutation marginals, and action counts, but
sample every `T[i,j]` independently. In this family, a never-executed compound
pair remains unidentifiable after all eligible source experience.

The frozen compiler should abstain, remain provisional, or produce chance
action value. Above-chance unseen-pair performance in this control indicates
target leakage, a target-only shortcut, hidden evaluator information, or an
invalid marginal match. This control is essential because a compiler prompted
to seek structure may otherwise hallucinate the factor law everywhere.

## Evaluation targets

Evaluation presents:

```text
start tray
goal tray
stage 1 menu: two compound tools
...
stage D menu: two compound tools
remaining action and memory budgets
```

The model must issue public `USE` actions, observe the actual resulting trays,
and finally issue `LOCK`. Reporting a plan, permutation, citation, or final
tool label earns no credit without the correct public trajectory and terminal
state. There is no reset or retry within the minimal cap.

All stage menus are visible initially so genuine planning is possible. The
generator exhaustively evaluates all `2^D` sequences and certifies that the
registered goal has one unique successful sequence, no shorter successful
path, no collision with another sequence, and no alternate proof using an
observed compound tool.

Primary depths are:

- **D1:** one compound action followed by `LOCK`; target-only value is `1/2`.
- **D4:** four ordered compound actions followed by `LOCK`; target-only value
  is `1/16`.

Each D4 stage uses a disjoint decisive factor pair, allowing four independent
factor-necessity interventions. The honest construct is minimum action/schema-
use depth, not learned graph depth or a claim about recurrent pointer traversal.

A paired goal twin holds the start tray and every menu byte fixed but changes
only the goal tray. Its unique successful sequence must differ at the first
action. Failure to redirect establishes that behavior is not goal-conditioned.

## New, old, and cross-era targets

At every checkpoint `k`, seal separate target families:

- **New acquisition:** every decisive factor was introduced since checkpoint
  `k-1`, while every decisive compound pair remains never executed.
- **Old retention:** every decisive factor belongs to the earliest life block,
  and its last public support lies outside the model's native visible window.
- **Cross-era D4:** two stages combine old stems with new suffixes and two
  stages combine new stems with old suffixes. No decisive old/new compound pair
  has appeared in source experience.

Use lagged paired snapshots rather than endpoint rhetoric:

```text
acquisition_k = V(M_k, T_new,k) - V(M_k-1, T_new,k)

retention_k   = V(M_k, T_old) - V(M_acquisition, T_old)

cross_era_k   = V(M_k, T_cross,k)
                versus old-factor cut, new-factor cut, and both-cut forks
```

Capability growth requires positive acquisition, old-value noninferiority, and
cross-era action above its causal controls. They cannot be averaged into one
score.

## Exact target-byte twins

Pair public stems under a fixed involution `sigma`. In the twin world, swap the
hidden stem bindings:

```text
A_twin[i] = A[sigma(i)]
T_twin[i,j] = T[sigma(i),j]
```

Every target menu contains both `stem_i/suffix_j` and
`stem_sigma(i)/suffix_j`. Construct the goal from a registered action sequence
in world `H`. In `tau(H)`, the label-swapped sequence applies exactly the same
latent transformations and produces the same state trajectory and goal.

Therefore the following are byte-identical across twins:

- start and goal trays;
- action-label inventories and menu ordering;
- action, read, and resolver caps;
- renderer and serialization lengths;
- checkpoint, depth, and era fields visible to the model.

The correct action sequence is swapped. World IDs, filenames, handles, RNG
state, caches, error paths, timing channels, and conversation state must not
reveal the side. Source schedules are equivariant under `sigma`, so action and
outcome marginals remain matched even though the authentic outcome bindings
differ.

## Decisive causal interventions

The minimum causal package is:

1. **World-by-memory twin factorial.** Evaluate `H/M_H`, `H/M_tau`,
   `tau(H)/M_H`, and `tau(H)/M_tau`. Matched memories should succeed. Crossed
   memories should redirect toward the counterpart-valid sequence and fail in
   the actual world.
2. **Lagged snapshot.** `M_k-1` must fail new-factor targets that `M_k` solves.
3. **Complete factor-binding swap.** Swap one decisive stem or suffix binding
   while retaining all unrelated schema atoms, candidates, indexes, prompts,
   and caches.
4. **Order-law cut.** Hold every `R[i]`, `C[j]`, and `M` operator fixed while
   flipping the composition-order statement. Registered noncommuting targets
   must lose value or follow the wrong-law plan. This is the cleanest
   endpoint-held intervention on higher-order structure.
5. **Matched sham cut.** Alter an unused factor or an equal-sized schema field
   irrelevant to that target.
6. **Binding derangement.** Permute stem or suffix bindings while preserving
   label counts, outcome counts, chronology bins, corpus shape, and exposure.
7. **Goal twin.** Change only the public goal and require the first action and
   later trajectory to redirect.
8. **Execution necessity.** Credit only the realized environment trajectory
   and terminal goal, never a reported answer or post-hoc citation.

For text memory, remove or swap all equivalent records and derived indexes. For
LoRA, citation masking is insufficient: use authentic/twin whole-life adapters
and a small paired correct-law versus wrong-law adapter panel with matched base
checkpoint, initialization, optimizer, example order, exposure, negatives, and
training seeds. Report intervention effects unconditionally and conditional on
authentic-memory success.

## Why trivial lookup or a target decoder cannot solve it

The construct has three independent barriers:

1. Evaluation trays contain fresh object handles and exact source states never
   recur. A state-edge table cannot transfer even a seen tool without inferring
   a state-independent operator.
2. Every decisive compound tool pair is absent from source experience. An
   exact tool-key table has no target entry.
3. Target bytes are identical across paired worlds requiring opposite action
   sequences. Target-only label statistics, prompt shape, and goal signatures
   therefore have exactly chance value.

Success requires the system to:

1. extract a positional permutation from an action outcome;
2. infer and retain the supported factor law and order;
3. compose old and new factors into a never-observed compound operator;
4. plan and execute several such operators toward a goal.

A linked memory that retrieves anchor episodes and induces the algebra at
target time may solve the task. That is an intended strong falsifier, not a
construct failure. Once it derives and stores the law, it is performing
structured program induction rather than indexed transition lookup. The paper
must localize whether abstraction occurred during target-blind compilation,
target-time external-memory reasoning, direct weight training, or an exact
program.

## Required baselines and attribution cells

The minimum defensible comparison contains:

1. no persistent memory and exact target-only Bayes;
2. honest full lifetime context while it fits, then frozen native-context
   truncation;
3. raw episodic RAG with iterative retrieval;
4. native linked/A-MEM retrieval, without forcing it through an artificially
   weak common interface;
5. an exact observed-tool operator table that performs no factor completion;
6. the exact public-only factor-law inducer and planner;
7. direct raw-transition-to-QA LoRA trained target-blind from the same public
   source experience;
8. target-blind compiled schema in text memory;
9. the byte-identical canonical schema corpus transported in LoRA;
10. oracle-schema text to isolate compiler failure from transport and planning;
11. matched candidate-assisted text and LoRA, candidate-only clean base,
    no-adapter, wrong/twin-adapter, explicit index, and unaided generative-LoRA
    sentinel cells.

Direct-QA examples must be constructed mechanically from public transitions,
without target pairs or goals. It must be allowed to exploit repeated
morphemes and learn the factorization implicitly; otherwise it is not a strong
baseline.

For every arm, report canonical memory bytes, training-view bytes and
repetitions, adapter precision, optimizer and checkpoint state, all indexes,
embeddings and candidate universes, prompt and resolver tokens, compilation and
training work, calls, FLOPs where available, latency, failures, and the number
of downstream targets over which compilation/training is amortized. A
recognition-assisted LoRA result is transport through that measured interface,
not unaided parametric recall.

## Exact positive claim ladder

Subject to prospective registration, adequate independent world-life/twin-pair
power, failure-inclusive inference, and independent review, positive evidence
could support only the following kinds of claims:

- **C0 -- Construct validity:** PCFL-Compose produces fixed-source lives in
  which public action--outcome episodes identify a reusable factorized operator
  law, while target bytes and exact local transition atoms do not identify
  never-executed compound actions.
- **C1 -- Prospective compiled abstraction:** Before target revelation, the
  named frozen compiler formed supported schema memories that predicted
  unseen compound actions and improved D1/D4 execution over named raw or
  atom-only controls; law and binding interventions redirected behavior in the
  predicted direction.
- **C2 -- Conditional parametric transport:** Through the exact registered
  reader and candidate interface, a per-life LoRA trained from the identical
  schema corpus transported life-specific factor bindings beyond clean-base,
  candidate-only, wrong-adapter, and direct-QA controls.
- **C3 -- Finite lifetime capability:** Over the registered PCFL-Compose range,
  the named system acquired new factors, retained earliest factors within a
  predeclared noninferiority margin, and composed old and new factors into
  successful never-seen action programs after raw history exceeded context.
- **C4 -- Optional measured efficiency:** Only if the complete resource
  frontier supports it may a named system claim a better observed
  action--storage--query--compute tradeoff than a named baseline.

No positive result licenses autonomous open-ended schema discovery, on-policy
self-improvement, a learned scheduler or exploration policy, generic SOTA
superiority, naturalistic external validity, human-like learning, unbounded
continual learning, learned graph organization, or asymptotic/semantic
compression of independent information. Do not put LoRA in the title unless
the substrate/reader panel earns it.

## Exact negative interpretations and falsifiers

- If A-MEM or raw recurrent RAG matches compiled memory, target-time external
  abstraction is sufficient over the tested range; there is no DREAM or
  compiled-memory moat.
- If direct-QA LoRA matches compiled LoRA, explicit semantic compilation adds
  no demonstrated value.
- If compiled text succeeds but identical-corpus LoRA fails, the result belongs
  to the schema/compiler; parametric transport failed.
- If only the exact program succeeds, the benchmark is construct-valid but the
  neural abstraction hypothesis is unsupported.
- If recognition-assisted LoRA alone succeeds and candidate/index accounting
  explains the gain, the system is an external enumerator plus reranker, not
  unaided parametric memory.
- If an observed-tool table solves never-executed pairs without algebraic
  completion, the target split or visibility contract leaked.
- If the order-law cut or decisive binding swap does not reduce value relative
  to the sham cut, the claimed schema was not causally used.
- If wrong/twin memory preserves authentic action value, life-specific binding
  causality is absent.
- If the goal twin does not redirect the first action, behavior is not
  goal-conditioned.
- If the independent-table control rises above chance, invalidate the assay
  for shortcut or leakage investigation.
- If `M_k-1` solves new targets, acquisition is leaked or prior-driven.
- If new acquisition stalls or old value collapses, there is no increasing-
  lifetime learner over the tested range.
- If all information-bearing state grows linearly while the paper says
  sublinear compression, remove the compression claim.
- If the exact program or a structured external memory dominates the full
  resource frontier, report that result plainly; there is no LoRA systems
  contribution.

## Ruthless two-week surface

The smallest useful implementation and DEV surface is:

- one deterministic renderer and one pinned backbone;
- one public factor-law family with only the two composition orientations;
- one small independent-table negative sentinel;
- D1 and D4 only; no D2/D3 grid;
- one pre-native checkpoint and three post-native checkpoints chosen from the
  tokenizer-exact visible envelope, provisionally around `0.75C`, `1.5C`,
  `3C`, and `6C` if factor counts and compute make them feasible;
- one primary adapter capacity and one fixed-capacity diagnostic, not a rank
  grid;
- incremental direct-QA and compiled-LoRA training with saved checkpoint
  snapshots rather than independent retraining at every lifetime;
- full CPU construct certification, compiled-text calibration, and exact
  program first;
- the complete lifetime curve only for the core arms;
- reader factorial, authentic/twin adapters, order-law cut, decisive factor
  cut, sham cut, and independent-law diagnostics at one registered sentinel
  checkpoint;
- no second backbone, multiple skins, noise, exceptions, on-policy source
  adaptation, learned scheduler, recurrent repair, broad schema family, public
  platform engineering, or full Cartesian sweep.

Lifetime length must grow by introducing new stem/suffix permutations, not by
repeating old episodes or adding distractor tokens. Report unique independent
factor bits separately from raw tokens and replay views. If three genuinely
post-native checkpoints cannot be completed, do not use curve, continued-
growth, saturation, or crossover language.

With reuse of the existing PCFL world, reader, and LoRA harnesses, roughly two
weeks is plausible for the deterministic generator and certifiers, exact
program, target-byte twins, compiled-text DEV, and a limited incremental
LoRA/RAG/A-MEM sentinel. It is not credible for a powered paper confirmation
with tens of independent twin-life pairs, multiple backbones, faithful new
implementations of every external baseline, or extensive rank and reader
sweeps. A small two-week DEV cannot be promoted by inflating `n` with nested
targets or training seeds.

## Paper framing

A safe working title is:

> **PCFL-Compose: Prospective Abstraction from Long-Lifetime Action--Outcome
> Experience**

A safe thesis is:

> In a controlled fixed-source synthetic workshop with a life-specific
> factorized action law, target-blind compilation of public action--outcome
> experience can be tested for whether it forms a reusable schema that supports
> never-executed compound actions and old/new cross-era multi-step goals after
> raw history exceeds context. Exact twins and factor/law interventions separate
> authentic schema use from target decoding, local lookup, reader cognition,
> and memory substrate.

The paper remains worthwhile under several nulls because it cleanly separates
environment construct validity, compiler abstraction, external-memory target-
time induction, direct weight learning, LoRA transport, and exact structured
program memory. It should not promise that DREAM or LoRA beats the exact
program; the scientific question is whether and where learned experiential
memory approaches that structured ceiling, and whether compilation changes the
action/resource frontier against strong named baselines.

## Authority boundary

The current `chg_20260902_pcfl_stream_paper_target_v1` consensus is in
`human_required`, recommends rework, and has `implementation_forbidden: true`.
This advisory proposes a material replacement of the latent world law,
information structure, target family, causal tests, and paper claims. It cannot
be smuggled into the current change as a non-material repair or optional
diagnostic.

Any implementation, model/provider/network use, training, GPU work,
confirmation run, promotion, or scientific claim requires a fresh hash-bound
architecture deliberation, explicit human ratification of the exact new bytes
and scope, the applicable pre-GPU tests, and independent review under
`AGENTS.md`.
