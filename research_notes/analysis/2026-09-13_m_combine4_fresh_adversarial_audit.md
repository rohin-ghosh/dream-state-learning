# Fresh adversarial audit: M-COMBINE-4 and the staged composition birth

**Date:** 2026-09-13 PT  
**Role:** fresh adversarial reviewer  
**Scope:** repository evidence and protocol review only. No source, fixture,
model, tokenizer, fit, checkpoint, GPU, remote, or scientific execution.

## Verdict

**REWORK Stage 2 before source authoring. Retain Stages 0--1.**

M-COMBINE-4 is aimed at the right missing capability: one adapter must choose
a READ, use what the READ returned to choose an action, compare the outcome,
and continue or stop. The current proposal does not yet isolate that result.
Its `UNLINKED` arm is internally impossible as written, its training records
may teacher-force the decisive commands, and ordinary whole-chain success does
not prove that the returned relation controlled the action.

The smallest repair is not a larger curriculum or another trained control. It
is:

1. rename and define the comparator as **ATOM-LOCAL**, not causally unlinked;
2. prohibit a gold child thought from spelling the next supervised command;
3. add held single-variable interventions for all four transitions; and
4. retain autonomous held chains as the free-running endpoint.

This yields a clean narrow result at no additional fit cost. It does not yet
support parenting, own-memory use, long-horizon learning, compression, or a
flywheel claim.

## What survives attack

- The four functional transitions are much better targets than a union of
  eight heterogeneous worksheet contracts.
- Exact text before parametric memory correctly separates policy failure from
  writer/reader failure.
- Response-only loss, one adapter, a static action grammar, target-disjoint
  identifiers, causal twins, strict failure, and generic canaries are the right
  hygiene.
- Four presentations per unique child decision at D1 and eight at D2 are a
  defensible first dose screen given the repository's repeated-procedure
  evidence. A terminal negative after only one presentation would not be.
- A one-seed Stage 2 is acceptable as DEV if it is never promoted as a paper
  replication.

## Blocking attacks

### 1. `UNLINKED` cannot satisfy both promises

The proposal says `UNLINKED` contains the same SEEK, PROSPECT, CHECK, and
CONTINUE/STOP atomic targets while never showing a returned result controlling
a later cue/action. Those conditions conflict.

For PROSPECT to be the same conditional skill, its input must contain a
returned EVENT and its correct STEP must vary with that EVENT. For CHECK to be
the same skill, its target must vary with prediction/outcome agreement. If
those dependencies are removed, the atoms are not matched. If they are kept,
the arm is not causally unlinked.

Target counts, target-token mass, and update tapes do not solve this. Loss-
masked inputs still determine hidden states and therefore gradients. Full
coherent histories and independent local vignettes also differ in input
length, role sequence, identifier recurrence, and attention structure.

**Repair:** call the comparator `ATOM-LOCAL`. Give it every same immediate
conditional decision, target class, target multiset, presentation count, batch
slot, and update/dropout tape, but serialize each decision with only the
locally sufficient state. `CLOSED` receives the authentic accumulated
episode history. Match the input-length and role-count distributions as
closely as possible and publish the residual difference; do not call the two
gradient-equivalent.

The resulting contrast is honest:

> Does training coherent closed histories improve a recurrent policy beyond
> co-resident locally sufficient decision training?

It is not “causal links versus no causal links.” If both arms compose, local
atoms were sufficient and no linked-training-necessity claim is allowed.

### 2. Gold thoughts can teacher-force every command

The example curriculum emits a THINK that names the needed address or port and
then supervises the READ or STEP on the next call. If the next training unit
contains that gold THINK in its prefix, the model can learn to copy the
address/port instead of selecting it from state, goal, or returned evidence.
The same problem occurs when a gold CHECK statement supplies the revised state
that the next target consumes.

Free-running evaluation makes a positive harder, but it does not identify
which transition was learned and makes a negative uninterpretable.

**Repair:** freeze each of the 256 units as exactly one
`pre-decision prefix -> one child continuation`. The prefix may contain prior
executed commands and public world/service returns, but no authored child line
may contain the next target command, its concrete READ address, its STEP port,
the registered route, or an evaluator label. Run a literal forward-answer
scan before fitting. Prefer supervising the decisive READ/STEP/STOP directly
from the pre-decision state. A CHECK thought may be a target, but it may not
name the following command. Inputs and teacher text remain loss-masked; this
does not make answer-bearing teacher text safe.

### 3. Chain success alone does not show use of the returned relation

Causal twins that alter goals, topology, identifiers, and service returns at
once still admit a learned joint shortcut. A successful actor could use goal
side, action position, a fixed exhaustive READ schedule, or a memorized
topology-family policy without the claimed transition being causally active.

**Repair:** add held counterfactual decision pairs for every transition. In
each pair, change exactly the registered causal field while holding all other
rendered bytes fixed wherever logically possible:

- **SEEK:** same state/store, change only the goal; the correct READ changes.
- **PROSPECT:** same state, goal, request and candidate IDs, replace only the
  valid returned relation; the predicted consequence and STEP change.
- **CHECK:** same prediction and prior state, change only CURRENT from match to
  mismatch; keep/revise changes.
- **CONTINUE/STOP:** same CURRENT and available store, change only whether the
  stated goal is satisfied; READ/continue versus STOP changes.

Use `8` pairs per transition (`32` pairs, `64` one-turn calls per model state).
Require both members correct on at least `6/8` pairs for **each** transition.
These are isolated mechanism probes, not substitutes for autonomous chains.
The latter still determine whether the learned pieces survive their own
generated history.

### 4. The READ budget may permit exhaustive search

“Useful READ before first STEP” does not show SEEK. An actor that reads every
visible candidate in a fixed order can satisfy it. In the tiny Stage-1 graph,
three READs can inspect the source and both candidate destinations, so Stage 1
is only an interface/headroom sentinel, as the proposal correctly says.

The richer Stage-2 panel must have more reachable candidate addresses than the
READ cap can exhaust. A correct witness path should fit comfortably inside
the cap; exhaustive branching should not. Register a minimal sufficient READ
set per task and report useful, irrelevant, repeated, and unsupported READs.
For the DEV gate, successful tasks may contain at most one pre-STEP READ
outside the registered sufficient set. This is an information-acquisition
constraint, not token starvation; the generous thinking-token budget remains
unchanged.

### 5. Existing nulls do not close learned combinations of cues

Pairwise deterministic policies are useful but not exhaustive. Opaque action
IDs can still correlate with target class through tokenization, residue,
position, prefix fragments, or a higher-order combination, as the Level-1
prediction fixture already demonstrated.

The held single-variable pairs above are the primary defense: an invariant
shortcut cannot be correct on both members when the decisive variable alone
changes. Stage 0 must additionally tabulate target action against identifier
tokenization, string length, character positions, row position, goal side,
route depth, family, and all predeclared pairwise combinations. Correct action
and command type must be balanced within each surface skin and topology
family, not only globally.

### 6. “Target-disjoint” is narrower than generalization

Fresh identifiers and held generator families prevent literal content reuse.
They do not make the skill curriculum blind: the curriculum deliberately
teaches the missing state-to-READ-to-action controller. Nor does a new whole-
graph hash prevent the same scored local automaton from recurring.

Bind role-labelled decision-core hashes and rooted signatures across birth
train, dose-DEV, and later confirmation. Reserve at least one combination of
route depth, goal switch, match/mismatch, and topology motif—not merely new
concrete IDs—for held readout. The honest term remains
**target-content/topology-disjoint skill engineering**, not spontaneous
composition or broad out-of-distribution reasoning.

### 7. Headroom and interface must be separated

A very low base chain score can reflect inability to emit the grammar rather
than inability to compose. A very high base score leaves no birth-treatment
headroom. `ATOM-LOCAL` helps because it receives the same command classes and
conditional atoms, but strict typed validity, atomic correctness, and whole-
chain correctness must be reported separately.

Do not interpret `CLOSED > ATOM-LOCAL` unless both fitted arms pass the atomic
and generic-interface gates. If ATOM-LOCAL is under-acquired, the comparison
is dose/learnability, not sequence composition. Conversely, if ATOM-LOCAL and
CLOSED both pass held chains, advance the simpler atom-trained child and state
that coherent trajectory training was unnecessary at this scale.

### 8. The amendment does not yet connect to Stages 3--6

The staged successor's later arithmetic assumes `1,024` distinct birth units
and names one composition child `C` plus one command-card sham `S`.
M-COMBINE-4 has `256` unique units repeated four or eight times, and its
ATOM-LOCAL comparator can itself become a competent composition child. Thus
phrases such as “replay all 1,024 birth units once,” the later C/S lineage,
and the 21-fit Stage-6 cap are not automatically inherited.

**Repair:** treat the repaired screen as Stage 2A and stop there until its
branch is known:

- if CLOSED passes and ATOM-LOCAL fails chains despite atomic acquisition,
  CLOSED is the composition child and ATOM-LOCAL is a strong semantic sham;
- if ATOM-LOCAL passes, it becomes the composition child and a separately
  qualified command-card child is the later active sham;
- if neither passes, stop;
- if either passes only after D2, all later birth replay is defined over the
  exact selected **presentation tape**, not falsely over 1,024 unique units.

Only then may a binding successor recalculate Stages 3--6. The current later
cost table is not valid after the M-COMBINE amendment.

## Smallest exact Stage-2A repair

### Frozen material

- `32` train causal-twin pairs = `64` episodes.
- Four separately serialized pre-decision child units per episode:
  SEEK, PROSPECT, CHECK, CONTINUE/STOP.
- `256` unique target units per arm.
- Two unrelated train topology families; a third family plus held motif/depth
  combinations for dose-DEV.
- CLOSED and ATOM-LOCAL have identical target-class counts, exact supervised
  target multiset, target-token count per batch, identifier-token marginals,
  presentation counts, initialization, optimizer, dropout, and update tape.
- Publish their necessarily different loss-masked prefix bytes and token
  counts. Padding is not evidence of semantic matching.
- No gold forward answer in any prefix; no PCFL/GOAL-BRAID content or
  inspected legacy Level-1 row enters either lineage.

### D1 and D2

```text
D1 per arm: 256 units x 4 presentations = 1,024 presentations
            / batch 4 = 256 updates

D2 per arm: continue to 256 units x 8 = 2,048 cumulative presentations
            / batch 4 = 512 cumulative updates
```

At D1, evaluate BASE, CLOSED, and ATOM-LOCAL. Continue both fitted arms to D2
only when custody/loss/canaries remain valid and either (a) an atomic gate is
underfit or (b) atoms pass but no arm passes autonomous chains. Preserve D1
artifacts. If one arm's atoms fail, a D1 between-arm chain gap is not evidence.
D2 is terminal; do not tune heat, rank, prompts, or topology on its result.

### Acquisition and behavior gates

Before any whole-chain comparison:

1. CLOSED and ATOM-LOCAL each get both members correct on `>=6/8` held pairs
   for every one of the four transitions;
2. each is strict typed on `>=60/64` atomic calls;
3. each preserves `>=15/16` generic actor canaries, with a gap `<=1/16`;
4. no target/input/custody/forward-answer audit fails.

An arm qualifies as a combined policy on the 32 autonomous held chains only
if all of the following hold:

1. whole-chain success `>=26/32`;
2. arm minus BASE `>=8/32`;
3. `>=12/16` causal twin pairs both correct;
4. useful autonomous READ before first STEP on `>=28/32`;
5. strict typed validity `>=30/32`;
6. every eight-task stratum `>=6/8` and every deterministic null `<=16/32`;
7. on each successful task, at most one pre-STEP READ lies outside the
   registered sufficient set; and
8. verified arrival is followed by exact STOP.

`CLOSED - ATOM-LOCAL >=8/32`, with both atomic gates passed, is a DEV signal
that coherent closed-history training helped. It is not required for the
existence of a combined policy. If both qualify, report that local atom
co-residence was sufficient and do not claim linkage necessity.

No separately trained binding-deranged adapter is needed at this stage. The
four held causal-field interventions are cheaper and more direct. A
full-history relation-permuted fit is optional only after a positive result if
the paper later needs a data-format mechanism claim.

## Exact resource arithmetic through Stage 2A

Stage 0 remains `0` fits, updates, model calls, and GPU work.

Stage 1 remains:

```text
32 autonomous rollouts
<=320 actor calls
<=49,152 generated actor tokens
0 fits / 0 updates / 0 reader-model calls
```

Stage-2A D1:

| component | count |
|---|---:|
| CLOSED + ATOM-LOCAL fits | 2 invocations, 512 optimizer updates total |
| autonomous chains, BASE/CLOSED/ATOM | 96 rollouts, <=2,784 actor calls |
| four-transition intervention probes | 192 one-turn calls |
| generic canaries | 48 one-turn calls |
| **D1 model-call cap** | **3,024** |
| **D1 generated-token cap** | **454,656** |

If D2 is opened, its two continuations add `512` optimizer updates total.
Re-evaluating CLOSED and ATOM-LOCAL adds `64` autonomous rollouts, at most
`1,856` actor calls, `128` intervention calls, `32` canary calls, and
`303,104` generated tokens.

Therefore the terminal Stage-2A cap is:

```text
4 training invocations (two D1 fits + two continuations)
1,024 optimizer updates across fitted arms
160 autonomous rollouts
5,040 model calls
757,760 generated tokens
0 reader-model calls (exact-text service only)
```

These counts exclude Stage 1, which adds the separately stated `320` calls
and `49,152` tokens. They are hard call/token caps, not GPU-hour estimates.
Record sequence tokens/update, seconds/update, actual generated tokens, engine
load, and peak memory before estimating wall time.

## Claim boundary

The strongest positive from this repaired DEV is:

> A target-content/topology-disjoint supervised birth adapter passed held
> single-variable SEEK/PROSPECT/CHECK/STOP interventions and autonomously
> completed held exact-text chains after reset.

If CLOSED alone qualifies, one may additionally say coherent trajectory
training helped relative to a locally sufficient atom curriculum on this DEV.
If ATOM-LOCAL also qualifies, one must say it did not.

Even the strongest result is a **lab-taught exact-text controller**. It is not
evidence that the agent learned from its own action--outcome experience, that
its LoRA contains usable personal memory, that knowledge is compressed or
connected parametrically, that parenting worked, or that lifetime performance
improves. Those claims remain gated by the same-adapter writer sentinel,
own/foreign/same-ID memory controls, goal-conditioned use, retention, and the
later lifetime experiment.
