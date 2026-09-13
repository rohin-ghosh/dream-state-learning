# Fresh audit: target-disjoint composition birth-skill 2x2

**Date:** 2026-09-13 PT  
**Audited proposal:**
`research_notes/analysis/2026-09-13_target_disjoint_composition_birth_skill_2x2.md`
at commit `67dad540`  
**Scope:** independent design audit only; no source, corpus, benchmark, model,
tokenizer, adapter, process, GPU, or remote state changed

## Verdict

**REWORK before implementation; GO after seven bounded corrections below.**

The scientific question is excellent and unusually informative. The 2x2 can
separate an inherited policy for *using* information from separately written
personal content. It is the smallest clean experiment I have seen in this
repository for the Level-1-to-Level-2 boundary.

The current frozen numbers should not run unchanged, however. Two dose
assumptions make a false negative likely:

1. `1,024` units at batch `4` is `256` updates per epoch, not `320`;
   `320` updates is `1,280` presentations, or `1.25` corpus-equivalents.
2. The personal sleep allocates only `800` memory presentations while its
   gates appear to require at least `64` distinct EVENT-address blocks and
   `32` distinct source-index blocks. That is at most `8.3` presentations per
   tested block on average. The repository's only successful exact EVENT
   write used `40` presentations per scheduled block: twenty blocks across
   eight wrappers and five epochs, `800` total presentations and `200`
   updates. The low-dose sequential screen failed at `40` presentations per
   *fact* under a weaker schedule. Total updates are therefore not a safe dose
   unit; presentations per independently tested binding are.

The scale contrast is larger than the update totals suggest. The earlier
Level-1 authored fixtures used the same `320` updates over only `96` rows:
each row appeared `13` times and 32 appeared a fourteenth time, at LR `3e-4`.
The proposed birth uses roughly `1.25` presentations per unit at LR `3e-5`:
about one tenth the repetition and one tenth the learning rate, while asking
for a more recurrent skill. These are not interchangeable tasks or token
doses, so the ratio does not prescribe a tenfold increase. It does show that
`320` is an aggressive low-dose screen, not a repository-anchored terminal
acquisition dose.

As written, failure could mean “the proposed capability is absent,” “the
birth behavior was shown once and underfit,” or “the personal rows were
underdosed by roughly fivefold.” Those must be separated before paying for
the full factorial.

## What the experiment can answer

The intended factorial is sound if its factors are named precisely:

| factor | level 0 | level 1 |
|---|---|---|
| birth policy | active command-card sham | composition policy |
| fitted bank | matched foreign-life bank | evaluated child's life bank |

Its cleanest estimand is the interaction:

```text
I = (C1 - C0) - (S1 - S0)
```

A useful positive has the qualitative pattern `C1` high and `C0`, `S1`,
`S0` low, with storage matched and a causal memory cut redirecting behavior.
That would show that a target-disjoint inherited policy makes separately
written own-life facts usable. It would not show autonomous discovery of the
policy, continual improvement, parenting, or a whole-organism flywheel.

Two labels in the proposal are too strong:

- `C1-C0` is an **evaluated-bank versus foreign-bank substitution effect
  under composition**, not an own-write-versus-no-write effect.
- The foreign bank is an **active write/heat control**, not a no-write
  control. The literal preserved birth checkpoint is the actual no-update
  anchor.

Report all four factorial contrasts, not only the two favorable ones:

```text
own-versus-foreign under composition: C1 - C0
own-versus-foreign under sham:        S1 - S0
composition under own bank:           C1 - S1
composition under foreign bank:       C0 - S0
interaction:                         (C1-C0) - (S1-S0)
```

This decomposition catches both shortcut shapes: a high `C0` means the birth
or generic foreign fit may solve the task without evaluated-life content; a
high `S1` means the base/sham child already knows how to use the written bank.

## 1. Birth acquisition: useful screen, wrong terminal dose

The proposed `320`-update birth fit is fair only as a **positive low-dose
screen**. If it passes the strong held-family gates, the result is valuable.
If it fails, it is not a fair negative test of whether the policy is
acquirable.

Why:

- The `1,024` child-turn units are mostly diverse task contexts, so each
  particular state-to-READ/STEP relation is presented only once or slightly
  more than once.
- The inherited policy is a multi-turn conditional behavior, not a single
  exact string binding.
- The earlier 256-row birth work shows that narrow PROSPECT and REVISE maps
  can be installed, but held conditional selection/locality remained
  imperfect (`58/64` REVISE for AUTH and `15/16` addition). That is evidence
  of feasibility, not evidence that one pass is enough for a harder recurrent
  policy.
- The base may already contain much of graph traversal from pretraining, so a
  low-dose positive is plausible; the demanding `104/128` whole-chain and
  `48/64` twin-pair gates nevertheless make a one-pass negative ambiguous.

Small correction:

1. Add a disposable birth-dose DEV family distinct from the untouched
   confirmation family and later release family.
2. Use full-pass endpoints: `256` updates (`1,024` presentations) and a
   prospectively permitted continuation to `512` total updates (`2,048`
   presentations), with identical deterministic order and exact C/S target-
   token coupling.
3. Stop at `256` if composition already passes the DEV acquisition gates and
   sham passes its own task. Continue both paired fits to `512` only if the
   first endpoint is intact but underfit. If `512` still fails, stop this
   version rather than adding a third heat or weakening the task.
4. Freeze the selected dose before creating the three confirmation fits.

If `320` is retained, call it `1.25 corpus-equivalents`, specify exactly which
`256` units receive the extra presentation, and prove balance by family,
turn type, goal side, swap status, and target-token count. Do not call it one
epoch.

“Balanced” also needs an integer schedule: neither `256` episodes nor `1,024`
units divides evenly across three families. Bind the exact `86/85/85` (or
other declared) episode allocation, rotate the remainder rather than hiding
it in sampling, and publish every unit's presentation count.

## 2. The active sham is necessary but not fully equivalent

The command-card sham is a good control for:

- action grammar and identifier copying;
- recurrent turn-taking and continuing activity;
- number of READ/STEP/STOP targets;
- target-token dose; and
- generic damage from fitting an active policy.

It is not a complete semantic control. Its decisive input explicitly names
the next command, while composition must infer that command from distributed
graph evidence. Thus conditional entropy, useful attention targets, and
semantic gradient structure differ even when lengths and outputs match.

Keep this sham in the 2x2, but narrow `C-S` to “composition curriculum versus
active command-following curriculum.” Before the full factorial, add one
single-seed **binding-deranged composition diagnostic**: preserve the same
graph prompts, memory returns, legal target multiset, sequence lengths, and
batch tape, but apply a fixed-point-free mapping between the decisive deep
relation and the legal next branch. It need not become a fifth release arm.
It only checks that the composition fit is responding to the intended
relation rather than benefiting from a more difficult/richer corpus in
general.

The sham's `>=115/128` own-task gate is appropriate. Also require matched
generic actor canaries for C and S. Copy success alone does not show that the
two fits preserved the ordinary actor equally.

## 3. Foreign-bank control: valid active control, incomplete null

The foreign bank is scientifically useful because it matches optimizer heat,
memory dialect, and a real exact-binding burden. Its limits should be explicit:

- Evaluated cues are in-distribution for `C1/S1` and out-of-support for
  `C0/S0`; some of `C1-C0` can therefore be cue-support competition rather
  than the presence versus absence of a write.
- A same-generator foreign bank may teach generic graph or memory behavior
  despite containing no useful concrete binding. This makes the contrast
  conservative, but not empty.
- “Matched size/shape/token lengths” is insufficient. Match the number of
  unique EVENT addresses, source fanout, block cardinality, request frequency,
  wrapper frequency, identifier-token lengths, and per-binding presentations.

Preserve and actually score the literal birth-only checkpoint on the final
task panel. Keep the proposal's wrong-life cross-mount. If the main C1 result
is positive, the stronger terminal content control is the already proposed
same-ID binding-deranged bank: it preserves cue support while changing the
fact. Foreign-bank, birth-only, wrong-life, and same-ID derangement answer four
different questions; none substitutes for all the others.

## 4. Personal writer dose must be defined per tested block

Before a personal fit, materialize and freeze these counts:

```text
E = unique READ EVENT targets
S = unique READ EVENTS_AT targets
M = E + S unique registered response blocks
P = memory presentations
P/M = average presentations per tested block
```

The gates must sample unique blocks without replacement. Otherwise `60/64`
can be inflated by repeated easy records.

The current minimum implied by the gates is `M >= 96`; `P=800` gives
`P/M <= 8.33`. The positive SEQ179 anchor used `40` presentations per
scheduled block under eight surface wrappers and five epochs. It is not a
universal optimum, but it is the only repository-backed starting dose. On an
underlying-experience accounting, SEQ179's `800` presentations over eight
authentic EVENTs is roughly `100` presentations per EVENT on average, versus
at most `12.5` per address if the new proposal has only the required 64
distinct EVENT addresses—and less once source blocks are included.

Use one of two honest repairs:

- **Small bridge first (recommended):** reduce the first release bank to a
  block count that the validated `200`-update/`800`-presentation schedule can
  cover at approximately `40` presentations per block. A graph with about
  `14-20` registered address/source blocks is enough to test actor-reader
  coexistence and a few goal-switched routes.
- **Keep the 16-life bank:** scale `P` with `M`, initially to `40M`, and add a
  separately counted birth-replay dose. This is much more expensive and
  should happen only after the small bridge works.

Do not reduce `P/M` merely because the corpus has more facts. That would make
memory-bank size and acquisition strength inseparable. If later evidence
supports a lower per-block dose, calibrate it in a writer-only DEV screen
before opening goals.

## 5. One adapter serving actor and reader is the right test—and a major risk

Using the same mounted adapter for both roles is architecturally faithful and
more informative than stacking two modules. It is also the most likely point
of failure. Birth targets teach action selection; exact-memory targets teach
verbatim blocks; both change the same rank-8 directions. Prior repository
audits have already seen interface/schema effects from narrow birth fits.

Make coexistence a gate before behavior:

1. On the birth checkpoint, actor transfer passes and reader prompts for
   absent opaque addresses produce strict `MISS`, with no THINK/STEP spill.
2. On the continued checkpoint, exact W0/W8 EVENT and source reads pass.
3. The same continued checkpoint retains the birth held-family policy and
   generic actor canaries.
4. Alternating actor-role and reader-role requests does not change either
   score; no conversation state is shared between calls.
5. Failure is reported as actor-reader interference. Do not repair it by
   mounting separate adapters inside this experiment.

The proposed birth replay is sensible, but `800` replay presentations should
be described relative to the frozen birth dose. After a `2,048`-presentation
birth fit, replaying only `800` examples is not “one retained birth pass.”
Specify the stratified replay coverage and per-unit count explicitly.

## 6. Contamination and isomorphism boundary

Salted namespaces and whole-graph hashes are necessary, not sufficient.
Whole graphs can differ while their scored decision cores are identical.
Before materialization, bind:

- role-labelled canonical hashes of every scored decision core;
- rooted neighbourhood signatures around the first irreversible choice;
- route-length, branch-position, goal-position, and action-label marginals;
- subgraph/motif overlap against current PCFL and GOAL-BRAID decision cores;
  and
- zero concrete identifier/text intersection across train, DEV,
  confirmation, release, and PCFL inventories.

For every materialized panel, execute the declared deterministic nulls on the
actual instances and record their exact task IDs and totals: constant action,
lexicographic action, first displayed row, direct-goal, local outdegree,
LINK-presence, fixed READ schedule, fixed STOP depth, and action position.
A generator-level promise that each is `<=1/2` is not a result. Also report
their intersections; several individually weak policies can combine into a
strong shallow rule.

Do not ban every generic branch or graph-traversal motif: teaching generic
composition is the treatment. Ban exact deployment role topology, concrete
content, target route, and shallow decision signature. State the honest
boundary: the curriculum designer knows which capability PCFL lacked. This is
**target-content/topology-disjoint skill engineering**, not a curriculum
chosen blind to the downstream research question.

Materialize once from fixed seeds. A failed overlap audit invalidates the
bound generator/specification; repeated resampling until it passes is not a
clean remedy.

## 7. Cost is larger than the proposal makes visible

Before causal controls, the frozen plan already entails:

- `6 x 320 = 1,920` birth optimizer updates;
- `12 x 400 = 4,800` personal-sleep updates; and
- `3 x 400 = 1,200` binding-deranged writer updates;

for **7,920 optimizer updates**, excluding any dose repair.

The initial birth qualification alone evaluates six trained births plus one
reusable base on `128` tasks: `896` multi-step task rollouts. At the stated
caps that is at most `25,984` actor decisions and `3,670,016` generated actor
tokens. The final four-cell panel adds `384` rollouts, at most `11,136` actor
decisions, `1,572,864` actor tokens, and up to `4,608` separate reader calls.
Post-sleep birth-retention panels add another `768` multi-step rollouts. Text
ceilings, cuts, wrong-life mounts, derangement, read gates, and canaries are
additional.

These are caps, not GPU-hour estimates. Sequence lengths and measured
throughput are absent, so the proposal cannot yet support an honest wall-time
claim. Deterministically render one batch and profile one disposable fit and
one 32-task rollout shard before reserving the full run.

## A tiny composition assay should come first

Yes: precede curriculum generation with a tiny exact-text `A -> B -> C`
composition assay. It is the cheapest way to answer whether the base already
has the state-to-cue-to-next-state behavior and whether the proposed static
actor/memory interface works at all.

Use 16 causal twin pairs with opaque fresh identifiers. Each task has two
locally matched two-hop corridors:

```text
A --p0--> B --p2--> C
A --p1--> D --p3--> E
```

The goal is `C` in one twin and `E` in the other; display order and ID position
are crossed. Only exact passive `EVENTS_AT` returns expose the second hop.
Require the actor to choose its own READs, take irreversible STEPs, verify the
observed state, and STOP. Constant-port, first-row, direct-goal, and no-READ
policies must be `<=1/2`.

- If base reaches at least `28/32`, use base as the common composition policy;
  a birth curriculum has little headroom.
- If base fails but a single development composition birth reaches the
  ceiling, proceed to the richer held-family qualification.
- If even exact text plus the development birth cannot solve this tiny
  assay, stop. Do not generate 16 personal lives or test LoRA storage.

This assay is an interface/headroom sentinel, not evidence of broad graph
composition: it has one two-hop shape and cannot replace the disjoint-family
birth confirmation.

## Smallest staged execution that stops early

The following order preserves the eventual confirmatory test while removing
most bad-run cost:

### Stage 0 — deterministic material audit; no model

Freeze train, dose-DEV, untouched birth-confirmation, writer-DEV, and release
families. Verify exact corpus arithmetic, target-token coupling, null-policy
ceilings, role-core nonisomorphism, identifier separation, and exact block
counts. Stop on any mismatch.

### Stage 1 — tiny exact-text composition and base headroom

Run the 32-task `A -> B -> C` causal-twin assay, then the base once on `32`
dose-DEV tasks. If base is already at the scaled composition threshold, the
birth treatment has no headroom; stop or use base as the common policy. If
base cannot operate the exact-text interface at all, localize that before any
fit.

### Stage 2 — one paired C/S birth

Fit one paired learner seed to `256` updates and evaluate train execution,
the 32-task dose-DEV panel, generic actor canaries, and the sham's own panel.
Continue both to the prospectively allowed `512` endpoint only if needed.
If composition still does not separate from base/sham or sham remains inert,
stop. Do not open the 128-task confirmation panel.

### Stage 3 — exact-text component ceiling

Using the surviving composition birth and one small writer-DEV graph, provide
all exact text rows but require autonomous cue choice and routing. If it fails
the scaled ceiling (for example `<14/16` when the final criterion is `28/32`),
the policy still cannot compose; stop before any LoRA memory fit.

### Stage 4 — same-adapter writer sentinel

Create a small bank close to the validated eight-EVENT/fourteen-address
regime. Continue one composition birth with the known
`200`-update/`800`-presentation memory schedule plus explicitly counted birth
replay. Test exact reads, birth retention, actor validity, and role spill. Run
the matched foreign continuation only after authentic coexistence passes.
Stop on storage or interference failure.

### Stage 5 — one-seed development 2x2

Run four descendants plus the literal birth-only anchor on `16` predeclared
writer-DEV tasks. Require the qualitative factorial pattern, autonomous READ,
and one indispensable-row cut before scaling. This is a development decision,
not paper evidence.

### Stage 6 — freeze, reset, and confirm

Only now freeze birth dose, block-scaled writer dose, sham, bank size,
generator versions, prompts, thresholds, and RNG tapes. Train all three
lineages from clean identical starts, open the untouched 128-task birth panel,
form the sealed release banks, and execute the full 2x2 and causal controls.

This order makes every expensive stage conditional on the immediately prior
component working. It also prevents using the confirmatory family to tune
birth heat or writer dose.

## Required rework before GO

1. Resolve `256` versus `320` updates and add a separate dose-DEV family.
2. Bind unique personal block counts and scale writer dose per block, or use a
   much smaller first bank.
3. Rename foreign write as the active bank control and score birth-only as the
   literal null.
4. Keep command-card sham but add the one-seed binding-deranged birth
   diagnostic and matched generic actor canaries.
5. Add the same-adapter actor/reader coexistence gate before task behavior.
6. Report all factorial contrasts and treat graph lives—not nested tasks—as
   the release-data units; three learner seeds remain robustness evidence,
   not an inferential population.
7. Bind the staged stop-early order and profile actual throughput before the
   full allocation.

With those corrections, this is a **GO** as a high-information developmental
bridge. Without them, it is a likely expensive null whose cause cannot be
localized.
