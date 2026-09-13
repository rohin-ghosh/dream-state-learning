# Binding successor: M-COMBINE-4 Stage 2A

**Date:** 2026-09-13 PT  
**Status:** binding design successor; documentation only. This is not authority
to author source, materialize fixtures, run a tokenizer/model, fit an adapter,
use a GPU, or make a scientific claim.  
**Preserves:** Stages 0--1 of
`2026-09-13_target_disjoint_composition_birth_skill_staged_successor.md`.  
**Supersedes:** every Stage-2 description of LINKED/UNLINKED, the broad
`1,024`-unique-turn first birth, its dose-selection logic, and every later
replay/cost statement that assumes that birth.  
**Audit basis:**
`2026-09-13_m_combine4_fresh_adversarial_audit.md`.

## 1. Frozen question and narrow claim

M-COMBINE-4 tests two questions in order:

1. Can one target-content/topology-disjoint rank-8 birth adapter execute the
   coordinated exact-text loop

   ```text
   state + goal -> READ -> returned relation -> STEP -> public outcome
                -> keep/revise -> READ again or STOP
   ```

   on autonomous held tasks?
2. Does training with coherent accumulated histories help beyond fitting the
   same locally sufficient conditional decisions as separate examples?

The first question is primary. The second is a curriculum-format diagnostic.
It is explicitly **not** phrased as “causal links versus no links,” because a
locally sufficient PROSPECT or CHECK example necessarily retains a causal
input-to-target relation.

A positive result is a lab-taught exact-text controller. It is not parenting,
own-life learning, parametric-memory use, compression, recurrence across
sleeps, lifetime improvement, or the Dream--LoRA--Think flywheel.

## 2. Arms

Use one DEV learner seed and three model states:

- **BASE:** the exact frozen Qwen2.5-7B-Instruct base, no fit.
- **CLOSED:** every child decision is supervised from the authentic coherent
  accumulated history of its synthetic episode.
- **ATOM-LOCAL:** the exact same immediate conditional decisions and exact
  target byte strings are trained as locally sufficient, separately reset
  vignettes. Earlier episode history is absent.

CLOSED and ATOM-LOCAL share:

- the same base/tokenizer/chat-template bytes;
- the same rank-8 all-layer LoRA recipe (`alpha=16`, dropout `.05`, LR
  `3e-5`, response-only loss, batch `4`);
- the same concrete synthetic training inventory;
- the same `256` unique supervised child continuations;
- the same exact target multiset, target-command counts, target-token total
  in every batch, identifier-token marginals, presentations, batch slots,
  initialization, optimizer, dropout, and update tapes; and
- the same generic system instruction and static THINK/READ/STEP/STOP
  grammar.

BASE, CLOSED, and ATOM-LOCAL readouts use the same predeclared task order and
common seeded decode tape. No arm receives extra samples, retries, repairs, or
best-of selection.

Their loss-masked prefix bytes necessarily differ: coherent history is the
treatment. Record byte/token/role-count distributions for both and publish the
residual difference. Padding does not make them semantically equivalent and
must not be described as doing so.

## 3. Exact 256-unit training root

### 3.1 Cases and factors

Generate `64` target-disjoint synthetic cases from two unrelated train
topology families, exactly `32` per family. Each case contributes exactly one
unit for each functional transition, hence:

```text
64 cases x 4 child continuations = 256 unique target units per arm
```

Cross and manifest these factors:

| factor | exact case count |
|---|---:|
| topology family A / B | 32 / 32 |
| ordinary expected flow / recovery flow | 32 / 32 |
| final state reached / unresolved | 32 / 32 |
| left / right goal side | 32 / 32 |
| surface skin 0 / 1 | 32 / 32 |

Within recovery flow, use `16` prior READ failures and `16` prior STEP/outcome
mismatches. Split the READ failures `8` strict `MISS` and `8` registered but
irrelevant returns. Cross recovery subtype with family, terminal state, goal
side, and skin by a fixed remainder rotation declared before generation.

The 64 cases carry two independent matching registries:

- `causal_pair_id`: `16` goal-switched pairs and `16` returned-relation/deep-
  swap pairs, balanced across both families and both flow classes;
- `recovery_match_id`: every recovery case has a role-isomorphic expected
  case under disjoint concrete identifiers, matched on family, depth, goal
  side, terminal state, and display order.

Do not force both registries to use the same partner. The manifest must make
both matchings explicit and bijective.

### 3.2 Four targets without broadening the screen

The literature-motivated expected/no-change/negative/recovery cases fit inside
the same four targets; they do not add a third arm, more unique units, RL,
DPO, general-chat replay, or another curriculum stratum.

For an **ordinary expected-flow** case, the four supervised decisions are:

1. **SEEK:** `READ <useful registered address>` from state plus goal.
2. **PROSPECT:** `STEP <supported port>` from the exact returned EVENT(s).
   The selected STEP is the operational forward prediction; Stage 2A makes no
   separate claim about a verbal numerical prediction.
3. **CHECK/no-change:** after CURRENT matches the EVENT-implied consequence,
   `THINK KEEP <implicated event-id>`.
4. **CONTINUE/STOP:** emit another useful READ if CURRENT is unresolved, or
   exact `STOP` if CURRENT equals GOAL.

For a **recovery-flow** case, a prior erroneous action and its public result
are present only as loss-masked input. The bad child action is never a target.
The four supervised decisions are:

1. **CHECK/revise:** after a strict MISS, irrelevant return, or STEP/outcome
   mismatch, `THINK REVISE <implicated event-or-query-id>`.
2. **SEEK:** issue the useful corrective READ.
3. **PROSPECT:** STEP through the port supported by the new exact return.
4. **CONTINUE/STOP:** issue a useful next READ or STOP only at verified GOAL.

Across all cases the exact target-command totals per arm are:

```text
READ 96     (64 SEEK + 32 unresolved CONTINUE)
STEP 64
THINK 64    (32 KEEP + 32 REVISE)
STOP 32
TOTAL 256
```

This imports the useful post-training lessons narrowly:

- expected twins teach **do not revise merely because a check was requested**;
- masked prior failures plus corrected continuations teach recovery without
  cloning the error;
- MISS and irrelevant-return cases teach that a retrieval-like action can be
  non-useful; and
- reached/unresolved cases teach STOP versus continued acquisition.

It does not attempt learner-distribution correction. If autonomous errors
remain the bottleneck after atomic acquisition, an on-policy/DPO/RL successor
is a new treatment, not an unlogged Stage-2 rescue.

## 4. No forward-answer teacher forcing

Every unit is exactly one serialized:

```text
loss-masked pre-decision prefix -> one supervised child continuation
```

The prefix may contain system/task text, prior executed child commands, exact
service returns, and public world outcomes. All are loss-masked. There is no
parent, command card, evaluator conclusion, solution text, future goal route,
or scheduled future command.

The following are hard source failures:

- an authored child THINK in the prefix contains the next target command;
- it contains the next concrete READ address or STEP port;
- it names the registered future route, a future destination not yet returned,
  an evaluator label, or an equivalent normalized alias;
- a task/service/world field contains a scheduled future action rather than a
  fact available at that point; or
- an erroneous action in a recovery prefix receives any loss.

Executed prior READ/STEP strings may remain because they are real past state,
but they may not equal or explicitly prescribe the next target. Run a literal
and normalized forward-answer scanner over every unit. The scanner's exact
forbidden-token derivation and every zero count enter the material manifest.

ATOM-LOCAL receives the minimal same-turn facts needed for its decision:

- SEEK: CURRENT, GOAL, and legal public interface;
- PROSPECT: CURRENT, GOAL, the issued request, and its exact return;
- CHECK: prior selected STEP, its EVENT-implied consequence, and CURRENT;
- CONTINUE/STOP: CURRENT, GOAL, and the checked working relation.

CLOSED receives those same local facts plus its earlier coherent episode
history. Thus ATOM-LOCAL genuinely contains the conditional atoms but never
trains their use inside one accumulated history.

## 5. Material, leakage, and shallow-policy closure

Stages 0--1 remain as already bound. Stage 2A additionally requires, before a
fit:

1. zero concrete identifier or text intersection across birth train,
   Stage-1 tiny DEV, Stage-2A dose-DEV, untouched future confirmation, PCFL,
   and GOAL-BRAID inventories;
2. no import, inspection, hash, canonicalization, or generation from any
   sealed PCFL/GOAL-BRAID instance, trace, output, route, or score;
3. zero role-labelled decision-core or rooted-signature equality between
   train and dose-DEV; generic interface semantics may match;
4. at least one held combination of topology motif, route depth, goal switch,
   and match/mismatch state absent from train;
5. exact CLOSED/ATOM target, batch, dose, and RNG coupling receipts;
6. target action tabulated against identifier tokenization, byte/token length,
   character position, display position, goal side, route depth, family,
   surface skin, flow class, and all predeclared pairwise combinations; and
7. the scripted oracle scores every train/readout unit and chain perfectly.

Execute the original deterministic nulls on the actual Stage-2A material.
Single-field and pairwise nulls must remain `<=1/2`. The held causal
interventions below—not an assertion that every possible heuristic was
enumerated—are the decisive shortcut defense.

Generate once from fixed seeds. A failed balance/overlap/null/oracle audit
invalidates the bound generator; do not resample until a lucky root passes.

## 6. Non-exhaustible exact-text READ topology

Stage 1 remains deliberately exhaustible and is only an interface/headroom
sentinel. Stage-2A dose-DEV is not.

For every autonomous Stage-2A task:

- the registered reachable candidate-address set contains more than `12`
  distinct addresses, so the actor's `12`-READ cap cannot enumerate it;
- the registered sufficient witness set contains at most `4` READs and fits
  comfortably within the cap;
- the next useful address is made available by state/goal plus an earlier
  exact return, not by host scheduling, goal-directed retrieval, or a list of
  valid task-local commands;
- every fixed/lexicographic/position/read-all-within-budget schedule is
  `<=1/2` on the paired panel; and
- the oracle uses only the public actor-visible state and exact service, never
  a hidden host path or answer.

Record useful, irrelevant, repeated, MISS, unsupported, and total READ counts.
On a successful rollout, at most one pre-STEP READ may lie outside the
registered sufficient witness set. The `4,096`-token thinking allowance is
unchanged: this prevents brute-force store enumeration, not deliberation.

## 7. Held readouts

### 7.1 Four single-variable intervention panels

Create `8` pairs for each transition (`32` pairs, `64` one-turn calls per
model state). These use fresh identifiers and a held topology/feature
combination. In each pair, only the named causal field changes, except bytes
that are logically entailed by that field:

1. **SEEK/goal:** same CURRENT and store; change GOAL; correct READ changes.
2. **PROSPECT/relation:** same state, goal, issued request, candidate IDs and
   display order; replace only the valid returned relation; correct STEP
   changes.
3. **CHECK/outcome:** same prior STEP and EVENT-implied expectation; change
   only CURRENT between match and mismatch; KEEP versus REVISE changes.
4. **CONTINUE/STOP:** same CURRENT and available store; change only GOAL
   between satisfied and unsatisfied; STOP versus useful READ changes.

The frozen target is pair correctness: both members correct. Report exact
command, operand, typed validity, and pair correctness separately. Neither a
free-form THINK explanation nor one correct member passes a pair.

### 7.2 Autonomous exact-text chains

Use `16` held causal twin pairs (`32` tasks) from the reserved family/feature
combination. Each actor receives only START, GOAL, CURRENT, the generic grammar
and the exact passive service. It chooses every THINK, READ, STEP, and STOP.
No host repair, forced first READ, candidate ranking, output canonicalization,
or conversation carryover is allowed. A malformed/unsupported/over-budget
turn terminates the task.

Use the already bound full Stage-2A limits:

```text
8 THINK, 12 READ, 8 STEP, 1 STOP, 4,096 generated actor tokens
```

Stage 1's smaller `4 THINK / 3 READ / 2 STEP / 1 STOP / 1,536 tokens`
interface limit must not be copied into Stage 2A.

Success requires verified arrival followed by exact STOP. Score the first
irreversible STEP, full route, CHECK behavior, useful/irrelevant READs, typed
validity, and terminal STOP separately from whole-chain success.

## 8. Dose and stopping rule

### D1

For each fitted arm:

```text
256 unique units x 4 presentations = 1,024 presentations
1,024 / batch 4 = 256 optimizer updates
```

Evaluate BASE, CLOSED, and ATOM-LOCAL on all intervention pairs, autonomous
chains, and generic canaries.

### D2

Continue **both** fitted arms on the same uninterrupted, predeclared tape to:

```text
256 unique units x 8 presentations = 2,048 cumulative presentations
2,048 / batch 4 = 512 cumulative updates
```

Open D2 only if custody is valid, losses are finite, exact arm coupling holds,
neither fitted arm loses more than `2/16` generic canaries from BASE, and:

- at least one arm misses an intervention acquisition gate; or
- both arms acquire the interventions but neither passes autonomous chains.

If both arms pass acquisition and any arm qualifies on chains at D1, D1 is
selected and D2 is not run. Preserve every D1 checkpoint and raw output. D2 is
terminal. Do not tune LR, rank, heat, prompts, topology, target mix, parsing,
or thresholds after seeing it.

## 9. Exact gates

### 9.1 Acquisition/interface gate, per fitted arm

For an arm to receive any combined-policy interpretation, it must satisfy all:

- pair-both-correct `>=6/8` for **each** of SEEK, PROSPECT, CHECK, and
  CONTINUE/STOP;
- strict typed output `>=60/64` across intervention calls;
- generic actor canaries `>=15/16`;
- fitted-arm canary gap `<=1/16`; and
- all source, custody, coupling, forward-answer, loss, and parser receipts
  pass.

The CLOSED-minus-ATOM curriculum contrast is interpretable only if **both**
arms pass this gate. At D2, failure of either arm stops advancement beyond
Stage 2A; a qualifying acquired sibling may still be recorded as a
base-relative feasibility result.

### 9.2 Combined-policy gate, per acquired arm

On the `32` autonomous held tasks, an arm qualifies only if:

1. whole-chain success `>=26/32`;
2. arm minus BASE `>=8/32`;
3. at least `12/16` causal twin pairs are both correct;
4. useful autonomous READ precedes first STEP on `>=28/32` tasks;
5. strict typed validity is `>=30/32`;
6. every predeclared eight-task stratum is `>=6/8`;
7. every deterministic null is `<=16/32`;
8. every successful task has at most one pre-STEP READ outside its registered
   sufficient set; and
9. verified goal arrival is followed by exact STOP.

The gate is a DEV engineering threshold, not a p-value or paper replication.

### 9.3 Interpretation and branch

The branches below apply only after both fitted arms pass the acquisition
gate. If either remains unacquired at D2, record any acquired arm's
base-relative result but do not select a child for Stage 3.

- **CLOSED qualifies; ATOM-LOCAL is acquired but fails chains:** CLOSED is the
  candidate composition child. `CLOSED-ATOM-LOCAL >=8/32` is a DEV signal that
  coherent accumulated-history training helped. ATOM-LOCAL may be the later
  strong semantic sham.
- **ATOM-LOCAL qualifies:** local conditional atoms were sufficient. Select
  ATOM-LOCAL as the candidate composition child; do not claim closed-history
  necessity. A separately qualified command-card child is required as the
  later active sham.
- **Both qualify:** select ATOM-LOCAL by the predeclared simpler-curriculum
  rule and report the CLOSED comparison as null/non-necessary.
- **Neither qualifies:** stop this version.
- **CLOSED qualifies while ATOM-LOCAL is not acquired:** do not advance; the
  between-arm contrast is uninterpretable.

No separately trained binding-deranged adapter is required in Stage 2A. The
four within-state single-variable interventions are cheaper and more direct.
A full-history relation-permuted fit is permitted only in a later, newly bound
mechanism study after a positive Stage 2A, never as rescue.

## 10. Exact resource cap

Stage 0 remains zero fits, updates, model calls, and GPU work.

Stage 1 remains separately capped at:

```text
32 autonomous rollouts
320 actor calls
49,152 generated actor tokens
0 fits / 0 updates / 0 reader-model calls
```

Stage-2A D1:

| component | exact/capped work |
|---|---:|
| CLOSED + ATOM-LOCAL | 2 fit invocations; 512 updates total |
| autonomous BASE/CLOSED/ATOM | 96 rollouts; <=2,784 actor calls |
| intervention panels | 192 one-turn calls |
| generic canaries | 48 one-turn calls |
| **D1 total** | **<=3,024 model calls; <=454,656 generated tokens** |

If opened, D2 adds:

| component | exact/capped work |
|---|---:|
| two fit continuations | 2 invocations; 512 additional updates total |
| autonomous CLOSED/ATOM | 64 rollouts; <=1,856 actor calls |
| intervention panels | 128 one-turn calls |
| generic canaries | 32 one-turn calls |
| **D2 addition** | **<=2,016 model calls; <=303,104 generated tokens** |

Terminal Stage-2A cap:

```text
4 training invocations
1,024 optimizer updates across both fitted arms
160 autonomous rollouts
5,040 model calls
757,760 generated tokens
0 reader-model calls (the service is exact text)
```

These are caps, not wall-time estimates. Record sequence tokens/update,
seconds/update, actual actor tokens, engine load, and peak GPU memory.

## 11. Later stages are deliberately unbound

Stop after the Stage-2A branch. Stages 3--6 may not inherit their present
arithmetic or lineage labels.

Before any same-adapter EVENT writer sentinel, a new binding successor must:

1. name the selected composition presentation tape and checkpoint exactly;
2. define birth replay over that exact tape (not “1,024 unique birth units”);
3. choose the later comparator by the branch rule above;
4. recalculate every replay presentation, optimizer update, call, token, and
   fit count;
5. preserve an exact-text component ceiling before parametric memory;
6. retain same-adapter W0/W8 exact acquisition, MISS selectivity,
   actor/reader alternation, composition-retention, own/foreign/same-ID
   derangement, indispensable/irrelevant cuts, and goal-redirection gates; and
7. freeze an untouched multi-seed confirmation without using Stage-2A dose-
   DEV outputs for scientific selection.

No current Stage-3--6 “C/S,” `1,024`-unique-unit replay, 21-fit, 46,272-update,
101,056-call, or 18.64M-token number remains binding after this successor.

## 12. Allowed wording after Stage 2A

If a selected arm passes all intervention and autonomous-chain gates:

> A target-content/topology-disjoint supervised birth adapter learned a
> coordinated exact-text controller: its READ, STEP, keep/revise, and
> continue/STOP decisions changed under held single-variable interventions,
> and it completed held chains under its own generated history.

Only if CLOSED qualifies and acquired ATOM-LOCAL fails chains by at least
`8/32` may one add:

> Coherent accumulated-history training improved the controller relative to
> a dose- and target-matched locally sufficient atom curriculum on this DEV.

Do not use “learned from experience,” “parented,” “self-learning,” “parametric
memory use,” “connected/compressed personal knowledge,” “general reasoning,”
“MCTS,” “recurrence,” “lifetime improvement,” or “flywheel” for this stage.
