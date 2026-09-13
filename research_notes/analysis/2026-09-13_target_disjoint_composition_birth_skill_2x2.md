# Target-disjoint composition/CoT birth skill: clean personal-memory 2x2

**Date:** 2026-09-13 PT

**Role:** independent experimental designer and adversarial reviewer

**Scope:** documentation only. No source, corpus, benchmark/root, model,
tokenizer, adapter/checkpoint, process, GPU, or remote state changed.

## Executive decision

Treat the missing Level-1-to-Level-2 bridge as an **inherited procedure
skill**, not as experiential content and not as a hidden graph solver.

The skill is one recurrent policy:

```text
current state + goal
  -> ask what information is missing
  -> choose and issue a memory READ
  -> interpret the returned relation
  -> update the working state
  -> STEP with an expected consequence
  -> compare expected with observed state
  -> READ/STEP again or STOP
```

Teach that policy at birth on varied synthetic graph families that have no
PCFL identifier, root, answer, topology fingerprint, life row, route, or
model output. Then test whether a later, separately written bank of the
child's own admitted action--outcome EVENTs supplies the content the policy
uses.

The primary experiment is:

| | no evaluated-life write | authentic own-life write |
|---|---:|---:|
| active sham birth | `S0` | `S1` |
| composition birth | `C0` | `C1` |

The primary result is not merely `C1` accuracy. It is the conjunction:

```text
composition skill exists before personal writing
+ both write arms carry personal rows equally well
+ C1 > C0 and C1 > S1
+ causal memory cuts/binding swaps change C1
+ the birth skill survives the personal sleep
```

This makes the interpretation clean:

- birth teaches **how to use information**;
- authentic SLEEP supplies **which lived information is available**; and
- their interaction measures whether the inherited loop used personal
  parametric memory.

It does not claim that the child discovered composition, learned to learn,
was parented, or completed a lifetime flywheel. It is the smallest causal
bridge that makes those later experiments worth running.

## 1. Keep THINK, DREAM and SLEEP simple

No new cognitive module is needed.

- **THINK** remains the recurrent one-line conscious stream between tool and
  world events. It may produce another thought, a READ, a STEP, or STOP.
- **DREAM** remains active-context distillation. It is not exercised or
  modified by this short birth-skill assay.
- **SLEEP** remains compilation plus one LoRA write. It does not choose the
  next thought or run graph search.

Rohin's “self-reflection as an index into the next skill” becomes an
operational, testable policy rather than a new object. On each turn the child
implicitly answers three questions:

```text
What is still unknown?
Which available operation reduces that uncertainty?
Is the evidence now sufficient to act or stop?
```

Correctly selecting `READ`, `STEP`, or `STOP` is the primary metacognitive
measurement. Free-form eloquence inside `THINK` is diagnostic only. Do not
score feelings, self-description, or long prose as evidence of composition.

The curriculum may demonstrate concise self-checking:

```text
THINK I need the outgoing events at the current node before choosing.
READ EVENTS_AT <current>
<exact memory result>
THINK Both choices look local; inspect the candidate continuation that could reach the goal.
READ EVENTS_AT <candidate destination>
<exact memory result>
THINK This supports port <p>; I expect the next state to be <n>.
STEP <p>
CURRENT <observed n>
THINK The observation matches; continue.        # or revise if it differs
...
THINK CURRENT equals GOAL; the route is verified.
STOP
```

These are taught connections between existing skills. They are not personal
memories, DREAM products, or PCFL solutions.

## 2. Birth material: same language, disjoint knowledge

### 2.1 What may be shared with deployment

It is legitimate for a lab-given skill to teach the public tool language:

- the type distinction among node, port, EVENT and LINK identifiers;
- the semantics of `EVENT source --port--> destination`;
- exact `READ EVENT`, `READ EVENTS_AT`, `READ LINKS_FROM`, `STEP`, and `STOP`
  interfaces;
- one-line LF-framed turns; and
- the fact that a world result follows a STEP.

Those are interface skills, like learning to call a tool. The corpus may use
the same identifier **types** (`N_`, `P_`, `E_`, `L_`) so transfer does not
depend on a syntax change, but all concrete values come from a separately
salted birth namespace and must have empty intersection with every PCFL
inventory.

### 2.2 What is forbidden

The birth train, DEV, sham, and transfer manifests must contain zero:

- PCFL root labels or concrete identifiers;
- PCFL OLD/NEW rows, receipts, routes, goals, A1--A4 outputs, parent text, or
  evaluator feedback;
- two-corridor topology isomorphic to current PCFL or the proposed PCFL goal
  braid;
- fixed five-action solutions, PCFL role order, correct branch-position
  statistics, or target route length; and
- material produced by a model after seeing a scored PCFL prompt.

Before any fit, independently compute identifier intersections and canonical
unlabelled graph hashes. Any overlap or forbidden graph isomorphism invalidates
the material; do not regenerate repeatedly until a sample happens to pass.

### 2.3 Synthetic family construction

Use three training families, all with variable node counts, depths, branch
positions, goal positions and row orders:

1. **braided layered DAGs:** three-way early choices, later reconvergence,
   and goals on different distant branches;
2. **rings with exits:** directed cycles whose correct exit depends on a
   distant goal and where continuing to READ eventually has negative value;
3. **crossbars:** locally matched branches connected by a late cross-edge,
   with one causal edge swap reversing the correct first action.

Do not use the two symmetric two-edge prefixes plus two-edge tails of the
proposed PCFL goal braid. Hold out a fourth generator family with different
depth and connectivity for the one-time birth transfer gate.

Every scored decision graph must satisfy, mechanically:

- correct and incorrect first-step destinations have the same direct-goal
  status, outdegree, and rooted neighbourhood signature through depth one;
- route lengths and action/token marginals are balanced;
- changing the goal changes the correct first action in half the pairs;
- changing one edge at depth two or deeper changes the correct first action
  while preserving initial task bytes and depth-one signatures; and
- fixed, lexicographic, row-order, direct-goal, local-degree, LINK-presence,
  and action-position policies are at or below one half.

The memory service is exact and passive. It answers only a child-issued
registered READ with exact rows or `MISS`. It never schedules a first READ,
expands a frontier, ranks a branch, retrieves by goal, or constructs a path.

### 2.4 Exact birth corpus size and loss boundary

For each birth condition, materialize `1,024` supervised child-turn units
from `256` training episodes, balanced across the three families, READ/STEP/
STOP turn types, goal side, route depth, edge-swap state and display order.

Only child continuations receive loss. System text, task text, teacher or
command-card text, exact memory returns, world outcomes, and evaluator fields
are inputs with zero loss. Parent messages are absent.

Use one fixed rank-8 all-layer LoRA recipe for both births:

```text
rank 8, alpha 16, dropout .05, learning rate 3e-5
response-only objective, batch 4, 320 updates
1,280 sequence presentations
```

The two arms use identical starting Qwen2.5-7B-Instruct bytes, tokenizer,
chat template, LoRA initialization seed, batch slots, dropout seeds, update
count and supervised target-token total. Per-batch supervised token counts
must match exactly; loss-masked input padding may equalize prompt length.
There is no dose selection on the untouched transfer panel.

## 3. Active sham that cannot silently become composition training

A weak or broken sham would make `C > S` meaningless. Use a **command-card
copy skill** over isomorphic synthetic interfaces:

- before every target, a public card explicitly names the next permitted
  `THINK`, READ address, STEP port, or STOP decision;
- the target copies/paraphrases that card in the proper one-line grammar;
- paired sham records have identical graph, current state and goal but
  opposite legal command cards and opposite target actions, so task evidence
  alone has zero predictive value for the target;
- both arbitrary branches have matched length and produce genuine ordinary
  outcomes, avoiding malformed or instantly collapsing examples; and
- READ/STEP/STOP counts, target-token counts, identifier token lengths,
  recurrence depth and batch placement exactly match composition birth.

This sham teaches tool syntax, ID copying, turn-taking and persistent activity
without teaching which operation or branch the task warrants.

The sham must itself pass an untouched command-card panel at `>=115/128`
exact next-command responses. Otherwise it is an inert/poisoned control and
the birth comparison is invalid, not positive.

## 4. Birth-skill qualification before any personal write

Evaluate base, sham-birth and composition-birth children with the same exact
external text memory service on `128` untouched tasks (`64` registered causal
twins) from the held-out topology family. No LoRA contains these task facts;
no update occurs during evaluation.

Every actor call uses one static union with no concrete IDs enumerated by the
decoder:

```regex
(?:THINK [^\r\n]*[^\s\r\n][^\r\n]*
 |READ (?:EVENT E_[A-Z2-7]{10}|EVENTS_AT N_[A-Z2-7]{10}|LINKS_FROM E_[A-Z2-7]{10})
 |STEP P_[A-Z2-7]{10}
 |STOP)
```

Use identical cumulative limits in all arms: `8` THINK, `12` READ, `8` STEP,
`1` STOP and `4,096` generated actor tokens per task. A malformed, invalid,
length-limited, over-budget or unsupported action terminates the task without
repair. A STEP returns only `CURRENT <node>`. A successful task requires an
exact STOP after CURRENT equals GOAL; reaching GOAL without verifying/stopping
does not pass.

Release all qualified composition births—do not select the lucky seed—only if
each of three paired learner seeds passes every gate:

1. composition whole-chain success `>=104/128`;
2. composition minus sham and composition minus base each `>=32/128`;
3. at least `48/64` causal twin pairs both correct, including correct
   first-STEP redirection under the deep edge swap;
4. at least `112/128` tasks autonomously issue a useful READ before the first
   STEP; externally forcing the first operator is forbidden;
5. each topology/depth/goal/order stratum is at least `75%` correct;
6. strict typed-turn validity is `>=122/128`, and no-task/interface canary
   degradation from paired OFF exceeds `6/128`;
7. every predeclared shallow policy is `<=64/128`; and
8. the active sham reaches `>=115/128` on its own command-card transfer panel.

Count the learner seed—not tasks, turns or decode repeats—as the birth-training
replication unit. The thresholds are engineering minimum effects, not
p-values.

If base already reaches `104/128`, there is no birth-skill headroom; stop and
use the base as the common procedure policy. If composition fails, do not
weaken the graphs, force READ, add host search, inspect the transfer targets,
or proceed to personal-memory fits.

## 5. Personal experience and SLEEP without PCFL contamination

Keep PCFL completely unopened during this experiment. The personal-memory
2x2 runs on three presealed **release banks**, one per learner seed. Each bank
contains `16` fresh graph lives from another generator family, with two
goal-switched sterile evaluations per life (`32` tasks per child).

For each birth lineage:

1. fork the exact qualified birth checkpoint;
2. let the child execute the same presealed exploration actions in each
   release life and receive the real public outcomes;
3. require the child to author exact EVENT commitments, accepted only by the
   world/receipt verifier; and
4. reveal no delayed goal, route task, answer, scorer output or future action
   during formation or SLEEP.

The exploration schedule and public outcomes are yoked across composition and
sham births. The child still performs every action and authors every record.
If one lineage fails to form the required bank, that is a formation result;
do not backfill it with researcher text or silently compare unequal memories.

The compiler creates only provenance-preserving read views of admitted own
EVENTs:

```text
READ EVENT <event>        -> that exact own EVENT row
READ EVENTS_AT <source>   -> all exact own EVENT rows at that source,
                             in a fixed target-blind order
```

No route, goal, good/bad label, search trace, future task, LINK closure,
teacher explanation, or model-written unverified inference enters the
personal corpus. Source-indexed views are a declared DREAM/compiler index over
the same EVENT atoms, not new world knowledge. This first bridge deliberately
excludes LINK; later AUTH-versus-ATOMS work can ask whether learned LINKs add
value.

## 6. One continued adapter; no stacking or weight merge

Do not stack a birth adapter and a memory adapter, average them, or merge one
into the frozen Qwen base. Use a single rank-8 LoRA lineage:

```text
frozen Qwen base -> one birth LoRA Bx -> one continued personal-sleep LoRA Bx,y
```

At the personal sleep, duplicate the byte-identical birth checkpoint and
start a fresh optimizer in every descendant. Run exactly `400` updates at
batch `4` (`1,600` presentations):

- `800` presentations are the same fixed stratified replay of that arm's
  birth corpus in every descendant;
- `800` presentations are either authentic own-life EVENT/read targets or a
  target-token-matched foreign-life bank; and
- batch position, supervised target tokens, lengths, dropout/RNG tape,
  optimizer settings and update count are coupled across authentic/foreign
  siblings.

The **foreign-life bank** operationalizes “no evaluated-life write” while
matching actual write heat and memory-format training. It is produced by the
same generator under a disjoint namespace, isomorphic size/shape and matched
token lengths, but contains no evaluated identifier or binding. Verify that
it is genuinely learned on foreign probes. Also preserve the untouched birth
checkpoint as a literal zero-update diagnostic; do not pretend a literal
no-update control can simultaneously match optimizer dose.

The primary four cells are therefore more exactly:

| | foreign/no-own write | authentic own write |
|---|---:|---:|
| sham birth | `S0` | `S1` |
| composition birth | `C0` | `C1` |

At evaluation only one adapter is mounted. The same mounted adapter serves
two explicitly prompted roles:

1. the actor emits THINK/READ/STEP/STOP under the static action grammar;
2. on a child-issued READ, the local memory-reader call receives only that
   opaque request and must reproduce an exact registered memory block.

The host checks the returned block against that child's admitted-memory
registry and returns exact bytes or `MISS`; it never repairs, completes,
ranks, automatically retrieves, or chooses an address. Thus the actor owns
the cue and the same single LoRA owns both the inherited procedure and the
personal content.

## 7. Memory and retention gates before behavior is scored

Behavior is uninterpretable unless storage is present and matched. Before
opening release goals, require in every learner seed:

1. `S1` and `C1` each reproduce at least `60/64` sampled `READ EVENT` blocks
   exactly under W0 and independently under held wrapper W8;
2. each reproduces at least `30/32` sampled source-indexed
   `READ EVENTS_AT` blocks exactly;
3. S1/C1 exact read fidelity differs by no more than `2/64` on address reads
   and `1/32` on source reads;
4. S0/C0 learn at least `60/64` of their assigned foreign address blocks but
   return no exact evaluated-life block (`0/64`) before the goal tasks;
5. the composition child's held-out birth-skill score falls by at most
   `6/128` after either sleep; and
6. generic instruction/action canary accuracy loses at most `5` percentage
   points, strict interface validity remains `>=.95`, and birth/action tags
   spill into unrelated prompts at most `.05`.

Failure of an AUTH storage gate is acquisition failure, not failed
composition. A material S1/C1 storage imbalance blocks the interaction claim.
Do not rescue a release bank by changing rank, learning rate, wrapper, dose or
replay after its goal panel is opened.

## 8. Clean 2x2 readout and exact release gates

After the gates above, erase source context, compiler state, external memory,
teacher/card text and optimizer state. Each final child receives only START,
GOAL and CURRENT. It chooses every READ and every irreversible STEP. All four
cells use identical prompts, static grammar, decode seeds, budgets, world
responses and scoring.

For learner seed `k`, let `Yxy,k` be exact whole-chain successes out of its
`32` tasks, where `x in {S,C}` is birth and `y in {0,1}` is
foreign/authentic memory. Define:

```text
personal-memory effect under composition:  MC = YC1 - YC0
composition effect with personal memory:    BC = YC1 - YS1
interaction: I = (YC1 - YC0) - (YS1 - YS0)
```

Release the bridge only if all three learner seeds satisfy:

1. `YC1 >= 24/32` exact THINK/READ/STEP/verify/STOP chains;
2. at least `11/16` life pairs solve both goal twins;
3. `MC >= 8/32` and `BC >= 8/32`;
4. `I >= 4/32`, with no seed negative;
5. every C1 success, and at least `24/32` tasks overall, contain an
   autonomous served READ before the first STEP; and
6. selected-port legality is `1.0` among accepted STEPs, with no parser
   repair, backtracking, reset or second-life retry.

Additionally require two causal controls prospectively selected by graph
identity, never by model behavior:

- **indispensable-read cut:** preselect `16` tasks by graph identity before
  any model result and replace one registered deep required block with
  `MISS`; paired uncut-minus-cut success must be at least `8/16`, while an
  equal-token irrelevant-row cut loses at most `2/16`;
- **binding-deranged writer:** from the same birth checkpoint, train one
  terminal sibling with a legal, fixed-point-free deep destination/port
  permutation, exact dose and batch tape. It must learn its assigned map at
  `>=60/64` exact reads and redirect the registered first action on at least
  `12/16` causal twins. An inert or malformed deranged adapter is not a valid
  negative control.

Wrong-life cross-mounts must score no more than `YC0 + 2/32`. Exact textual
memory with the composition birth child is the component ceiling and must
reach `>=28/32`; otherwise the remaining failure is still the composition
policy, not LoRA transport.

These are minimum effect gates, not confidence intervals. Three learner
seeds are robustness evidence only. Tasks and goals within one child are not
independent training replications.

## 9. Red-team failure map and dispositions

| observed result | correct interpretation / next action |
|---|---|
| composition birth fails exact-text transfer | inherited policy not installed; stop before personal writes |
| sham fails its command-card task | control is inert/poisoned; redesign sham, no positive birth claim |
| base matches composition birth | no inherited-skill headroom; use base as common policy |
| S1/C1 personal read fidelity differs | behavior contrast confounds storage and composition; stop |
| both store, C1 fails text-memory ceiling | actor/cue/composition failure, not writer failure |
| text ceiling passes, C1 LoRA fails | actor--reader role interference or parametric extraction failure |
| C1 and S1 tie high | personal memory works, but composition birth was unnecessary |
| C1 > S1 but C1 = C0 | birth directly solves/guesses tasks; no personal-memory effect |
| C1 > both but cuts/derangement do not redirect | correlation, topology shortcut or uncontrolled training heat; no causal bridge |
| C1 passes but birth transfer collapses after sleep | one-adapter interference/replay failure; do not scale the child |

Other mandatory protections:

- do not use a host DFS/frontier or automatic first READ;
- do not dynamically enumerate valid ports in one memory arm;
- do not score a final route extracted from free-form thought;
- do not call source-index indexing a learned connection;
- do not count teacher/card text, tool returns, or evaluator prose as targets;
- do not use PCFL-exposed A1--A4 traces as “generic” curriculum;
- do not select a birth seed on the untouched panel;
- do not continue a failed release child with a new dose and call it the same
  confirmatory lineage; and
- do not infer lifetime improvement from one birth plus one sleep.

## 10. Relationship to PCFL and the paper

This entire qualification is target-disjoint and completes before any new
PCFL confirmation root is opened. If it passes, freeze the exact composition
birth checkpoint and give that identical inherited child to **every** PCFL
memory arm: native experiential LoRA, OFF, wrong-life, active text, full text,
raw episodic and content controls.

The common birth skill is then a controlled lab endowment. It cannot be
credited to Dream/Sleep. PCFL experience alone supplies root-specific facts
and relations.

The current PCFL delayed topology remains only an interface/local-memory-use
endpoint because a depth-one public policy solves it. The proposed
`PCFL-GOAL-BRAID-v1`, if separately reviewed and authorized, is the natural
untouched transfer target because goals change the first action and branches
are locally matched. The birth corpus must exclude that braid topology as
specified above. This memo neither authors nor authorizes it.

A successful generic 2x2 supports the bounded statement:

> A target-disjoint inherited composition policy enabled a fixed 7B child to
> autonomously cue, read, interpret and act on its own separately sleep-written
> parametric EVENT memories after active context was removed.

Only a later PCFL goal-braid result with authentic-versus-atom/LINK/cut/text
controls can add connected experiential knowledge, goal-conditioned
prospective action and baseline comparisons. Repeated lifetimes with frozen
THINK/DREAM/SLEEP mechanics are still required for a flywheel or learning-
curve claim.

## Final recommendation

This is a feasible bootstrap and it directly tests Rohin's hypothesis that
the child may need examples connecting its already pretrained skills before
personal experience can become useful cognition. The clean implementation is
one continued LoRA, a strong active sham, an exact-text procedure ceiling,
matched personal-memory acquisition, and a target-disjoint causal 2x2.

Do not ask twelve personal EVENT rows to create the procedure. Teach the
procedure broadly at birth; then ask whether authentic lived rows change what
that procedure reads, believes and does.
