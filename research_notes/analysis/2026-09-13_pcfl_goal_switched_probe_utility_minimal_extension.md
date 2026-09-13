# PCFL-GS1: minimum goal-switched probe-utility extension

**Date:** 2026-09-13 UTC  
**Role:** independent design audit  
**Status:** specification only; no implementation, materialization, model call,
fit, adapter, GPU execution, claim, or lineage change  
**Question:** can the current PCFL world cheaply test whether the *same
memory* selects a different experiment when only the goal changes?

## Verdict

Yes. The current topology already contains the exact counterfactual needed:

```text
frontier A: H -> S_R
frontier B: X -> Z
```

For a right-side goal (`G_R0` or `G_R1`), frontier A is useful and frontier B
is irrelevant. For the existing old node `Y`, their utilities reverse:

```text
right goal: S_L -> A -> H --frontier A--> S_R -> B -> G_Rg
Y goal:     S_L -> X     --frontier B--> Z -> Y
```

No OLD event, identifier, port alphabet, fitted row, LoRA, main reachout, or
authentic lineage needs to change. The minimum credible addition is a
**selection-only, read-only diagnostic** bound before results and run from
fresh forks of the already frozen S1 state. It changes only the public `GOAL`
node and the private expected choice.

Do **not** insert this into the current v2.2 critical path. Seal it as a
conditional `PCFL-GS1` sidecar now and execute it only after the unchanged
PCFL S1_AUTH gates pass. This preserves the deadline experiment and prevents
a useful strengthening from reopening its contract. If current PCFL never
reaches a valid S1_AUTH state, GS1 has no learned-memory object to diagnose
and should not run.

The current PCFL should remain the headline test of authentic
THINK/DREAM/SLEEP formation, carriage, expansion, retention, and OLD+NEW use.
GS1 adds one narrower statement:

> From the same reset memory state, changing only the stated goal reversed
> which unknown frontier the child selected.

It does not establish learning across goals, autonomous goal creation,
value-of-information optimality in general, or lineage improvement.

## 1. Why the reversal is already latent

The unchanged OLD graph is:

```text
e0  S_L --a_O------> A
e1  A   --b--------> H
e2  H   --c--------> G_L
e3  S_R --d--------> B
e4  B   --f_0------> G_R0
e5  B   --f_1------> G_R1
e6  S_L --a_(1-O)--> X
e7  Z   --u--------> Y
```

The already bound unknown frontiers are:

```text
q_R = q0 if R=0 else q1    H --q_R--> S_R
q_D = q0 if D=0 else q1    X --q_D--> Z
```

The two frontiers reuse the same two opaque public port IDs `q0/q1`. Actions
remain deterministic because they are keyed by `(source, port)`.

Under the maximal private graph containing both frontier truths, the unique
routes are:

```text
T=RIGHT, goal G_Rg: a_O,b,q_R,d,f_g
T=Y,     goal Y:    a_(1-O),q_D,u
```

Therefore:

```text
utility(frontier A | T=RIGHT)=1
utility(frontier B | T=RIGHT)=0
utility(frontier A | T=Y)=0
utility(frontier B | T=Y)=1
```

This is a real goal intervention, not a relabeling. `e6` shows that the left
start reaches `X`; `e7` shows that `Z` reaches `Y`. The child must use its OLD
memory to see why `X -> Z` matters for `Y`. Conversely, `e0/e1/e3/e4-or-e5`
make `H -> S_R` matter for the right goal. Opaque names prevent a pretrained
semantic shortcut.

## 2. Exact topology delta: none

GS1 adds no node, edge, event, link, probe, receipt, goal handle, or opaque
identifier. It reuses exactly:

- nodes `S_L,A,H,S_R,B,G_R0,G_R1,X,Z,Y`;
- ports `a0,a1,b,d,f0,f1,u,q0,q1`;
- OLD events `e0,e1,e3,e4,e5,e6,e7`;
- probe IDs already assigned to `H -> S_R` and `X -> Z`; and
- the same prepared root-local opaque inventory.

For GS1 private records, stop calling the probes permanently `relevant` and
`distractor`. Those names are true only for the current right-goal task. Use
goal-neutral structural labels:

```text
FRONTIER_H_SR = (H, q[R], S_R)
FRONTIER_X_Z  = (X, q[D], Z)
```

The original main-lineage state machine and its current labels remain
byte-for-byte unchanged. The neutral aliases exist only in the GS1 sidecar.

## 3. Exact public render delta

Use the already frozen `RA` and `RB` reachout renders, system message, PROBE
grammar, option order, opaque probe IDs, and token limits. The right and Y
members of a paired diagnostic item differ in exactly one typed substitution:

```text
GOAL {N_G_Rg}   <->   GOAL {N_Y}
```

`START` remains `{N_S_L}`. Both probe descriptions, their order, every other
byte, model mount, snapshot, wrapper, and generation seed are identical.
The two target values are both prepared `N_` identifiers of 12 ASCII bytes.
Preparation must additionally prove equal frozen-tokenizer length **in this
exact `GOAL ` placement**, rather than infer equality from the namespace.

The score-bearing output remains exactly:

```text
PROBE Q_[A-Z2-7]{10}
```

with no terminal LF or extra prose. Missing, malformed, repeated, unknown, or
multi-command output scores zero.

The minimum panel ends after the first commitment. No probe result is supplied
to another model call, no `EXPLORE` is issued, and no EVENT/LINK formation is
requested. The private graph oracle scores whether the selected experiment
would reveal the port needed by the stated goal. This makes GS1 a clean
experiment-selection diagnostic; current PCFL separately tests actually
using the right-goal result and committing NEW memory.

This selection-only boundary is important. Allowing the Y branch to continue
would require a second executed event/receipt lineage or a special ephemeral
execution path. Either is unnecessary for proving goal-conditioned selection
and would stop being a minimal extension.

## 4. Separate collision certificate

Do not mutate the passed/current `(O,R,D,G)` collision cube. Add a separate
GS1 CPU certificate over:

```text
4 excluded roots x 2 O x 2 R x 2 D x 2 target families = 64 cells
```

`T=RIGHT` uses one right target preassigned per excluded root, balanced two
roots to `G_R0` and two to `G_R1`. `T=Y` uses `Y`. The assignment is derived
from the sealed root index before opaque allocation or model output.

For every fixed `(root,O,T)`, the four `R,D` cells must have byte-identical
pre-outcome input for a given RA/RB surface and the exact outcome pair table
`00,01,10,11`. Exhaustive bounded path enumeration must prove, without
averaging:

1. exactly one simple successful route in all `64/64` cells;
2. for `T=RIGHT`, every success uses `e0` and `H -> S_R`, never `X -> Z`;
3. for `T=Y`, every success uses `e6`, `X -> Z`, and `e7`, never `H -> S_R`;
4. deleting the goal-useful frontier destroys success in `64/64` cells;
5. deleting or toggling the other frontier leaves the exact correct route
   byte-identical in `64/64` cells;
6. toggling `R` changes only the right route and toggling `D` changes only the
   Y route; and
7. all syntactically legal routes containing the goal-irrelevant frontier
   fail to reach the stated target.

The information identities are conditional on target family:

```text
T=RIGHT: I(q_R; correct route)=1, I(q_D; correct route)=0
T=Y:     I(q_R; correct route)=0, I(q_D; correct route)=1
```

Both outcomes retain one bit of entropy. Prompt-only fixed-probe choice is
exactly `16/32` over every balanced right/Y selection panel, while a policy
that uses the OLD graph can attain `32/32`.

## 5. Model panels and frozen controls

### 5.1 Reuse rather than rerun the right half

For every condition, select a predeclared 16-item subset of the existing
excluded-root right-goal reachout panel:

```text
4 roots x 2 O x 2 surfaces = 16 current items
```

The registered right target is balanced by root as above. Add one Y-goal mate
for each item, with the same render, root, O, model state, and generation seed.
Only `GOAL_NID` and the private expected probe differ. This adds 16 calls per
condition, not 32.

Retain all five current zero-fit conditions:

```text
EXACT_WITNESSED_GRAPH
FULL_CHILD_TEXT
ACTIVE_LINKED_TEXT
NONE_OFF
WRONG_ROOT
```

For each memory-bearing ceiling, require `>=15/16` on each target family,
`>=30/32` jointly, and a different valid probe in `>=14/16` paired items.
For NONE/OFF, WRONG_ROOT, every registered ID/order/wording projection, and
fixed-choice policies, require joint success `<=18/32`. Report each target
half separately so a fixed probe that gets one half `16/16` and the other
`0/16` cannot masquerade as partial goal sensitivity.

### 5.2 DEV S1 read-only diagnostic

Reuse the existing eight right-goal panel items per DEV root. Add one Y-goal
mate to each item for these five conditions:

```text
native S1_AUTH
service S1_AUTH
service goal-critical cut
service NONE/OFF
service WRONG_ROOT
```

Every pair restores the exact same untouched post-S1 snapshot or clean actor
state and uses a coupled seed. The Y critical cut replaces the predeclared
local return for OLD event `e7` (`Z --u--> Y`) with `MISS`; no other return is
changed. The current right-goal cut remains unchanged. The cut addresses and
expected returns must be registered before output.

Per DEV root, native and service AUTH must each satisfy:

```text
RIGHT correct >= 7/8
Y correct     >= 7/8
joint         >=14/16
paired valid choice changes >=6/8
```

For the corresponding goal half, critical-cut, OFF, and wrong-root service
conditions remain `<=4/8`, and AUTH must exceed each by `>=3/8`. Also report
the joint right/Y rate and switch count; these are the direct defenses against
a fixed-probe policy.

Do not average roots to rescue a failed root. GS1 is passed only if both DEV
roots pass native and service reversal. ATOMS and LINK_PERMUTE need not be
added: GS1 asks whether the qualified authentic memory is goal-sensitive, not
whether stored LINK organization caused that sensitivity.

## 6. Authentic-lineage and custody rules

GS1 must be a separate, presealed diagnostic contract bound to:

- the immutable main v2.2 execution-contract hash;
- root-skeleton and opaque-inventory hashes;
- the exact S1_AUTH adapter and untouched snapshot hashes supplied later as
  typed custody substitutions;
- the paired item registry, target assignments, renders, seeds, expected
  choices, critical cuts, and work rows; and
- this specification hash or its exact adopted successor.

It must not modify the main `execution_contract.json`, root skeleton, fit
roster, work arithmetic, or stop state. Every GS1 transcript is marked
`TAINT_GOAL_SWITCH_DIAGNOSTIC` at creation. It has zero path into:

- the lineage-entering primary reachout;
- either R continuation;
- formation/admission;
- S1 or S2 corpora and replay registries;
- adapter training or selection;
- context shown to a later child; or
- a replacement/retry decision.

Run GS1 only in fresh workers after the main root's S1 measurements and raw
primary output have been sealed. A GS1 failure cannot terminate or alter the
main root; a main S1 failure suppresses GS1 because there is no qualified
memory state to test.

## 7. Exact incremental work and cost

There are **zero new fits, optimizer updates, training rows, adapters, cold
training loads, or child-authored memories**.

New zero-fit work:

```text
5 conditions x 16 added Y mates = 80 task cells
```

New DEV work:

```text
2 roots x 5 conditions x 8 added Y mates = 80 task cells
```

Total increment: **160 score-bearing task cells**. The already existing 160
right-goal mates are reused; they are not regenerated.

Under the current reachout service bounds, the added work expands to:

```text
zero-fit: 80..464 physical generations
DEV:      80..1,616 physical generations
total:   160..2,080 physical generations
```

The added actor/native output ceiling is `160 x 2,048 = 327,680` tokens. The
added returned-memory ceiling is
`16 x 4,096 + 64 x 4,096 = 327,680` tokens. Actual calls/tokens and device
seconds must be recorded; natural early EOS cannot reduce a denominator.

This is cheap relative to a new fitted arm because it adds no write, but it is
not free engineering: it adds a sidecar schema, a 64-cell oracle certificate,
paired task registry, one new cut, 160 work rows, reduction logic, and
fail-closed tests. That is why it should not delay current v2.2 execution.

## 8. Exact new fail-closed tests

The sidecar needs, at minimum:

1. source/main-contract/snapshot/adapter hash binding and closed schema;
2. 64-cell path, deletion, irrelevance, entropy, and conditional-information
   golden vectors;
3. no-new-ID and no-main-root-mutation assertions;
4. byte snapshot proving each pair differs only at the typed GOAL substitution;
5. exact-placement tokenizer equality for right/Y GOAL IDs;
6. total/injective 16-pair zero-fit and eight-pair-per-root DEV maps;
7. balanced right-target and RA/RB assignments independent of output;
8. e7-only Y-cut coverage and oracle proof of its effect;
9. exact 80 + 80 new work rows and 160..2,080 physical-call expansion;
10. scorer truth table for right, Y, malformed, fixed-choice, and switched
    actions;
11. taint propagation proving zero path to every authentic lineage/corpus
    artifact; and
12. suppression after invalid S1 plus proof that GS1 can neither fail nor
    promote the main root.

## 9. Comparison with leaving PCFL unchanged

| choice | gain | cost/risk | recommendation |
|---|---|---|---|
| unchanged v2.2 | fastest route to authentic formation, LoRA carriage, one useful reachout, NEW formation, retention, and OLD+NEW delayed action | cannot say experiment choice changes with goal; both registered future goals favor `H -> S_R` | **run first; do not reopen** |
| GS1 sidecar | same qualified memory must reverse its probe choice when only goal changes; materially strengthens prospective traversal | 160 new task cells, up to 2,080 physical generations, new sealed diagnostic/tests; no fit | **predeclare now, run conditionally after S1** |
| change main lineage so Y becomes a second authentic continuation | could test execution, formation, and consolidation on both goal-dependent frontiers | needs new EVENT/receipt/LINK slots, S2 arms, corpora, cuts, schedules, fits, and claim contract; no longer cheap | **reject for this paper deadline** |

The scientific value of GS1 is real: it closes the exact limitation already
stated in v2.2 Section 12.2. The scheduling value of leaving v2.2 unchanged is
larger right now. The right decision is therefore not “extension or current
PCFL”; it is **unchanged PCFL first, presealed GS1 as a conditional read-only
diagnostic second**.

## 10. Permitted and forbidden language

If both roots pass, permitted:

> Holding the learned memory, start state, probe affordances, surface form,
> and generation seed fixed, changing the opaque goal reversed the selected
> experiment in both development roots.

Also permitted, if the registered cuts pass:

> Removing the goal-critical old memory abolished the corresponding
> goal-conditioned selection advantage.

Forbidden:

- “the agent learned a general value-of-information policy”;
- “the agent autonomously created or switched goals”;
- “both new experiences entered and improved its authentic lineage”;
- “the LoRA contains an explicit utility representation”;
- “goal-conditioned planning improves with lifetime”; or
- any use of GS1 to rescue a failed main PCFL stage.

