# Adjudication of Rohin message 43: from atomic habits to one usable loop

**Date:** 2026-09-13 PT  
**Scope:** evidence/design synthesis only; no source, model, tokenizer, fit,
checkpoint, GPU, parent, benchmark, or external state changed

## Plain answer

Rohin's diagnosis is substantially right, with one correction.

The repository has shown that highly repeated, authored Level-1 procedures can
be installed. It has **not** shown one child coordinating all eight named
procedures, and it has not shown a remembered relation choosing the child's
next operation. But prior work was not literally all one-skill-only: several
smaller adapters held multiple routines at once. The missing boundary is the
**junction**:

```text
need information
  -> ask memory
  -> interpret what came back
  -> predict and act
  -> compare outcome
  -> continue, revise, or stop
```

This is the smallest useful Level-1-to-Level-2 bridge. It is better than
unioning eight worksheet corpora and hoping the labels compose.

## What the eight-behaviour result really was

SEQ142/146 ran `8 behaviours x 3 optimizer seeds = 24` fresh LoRA fits. Each
adapter saw `96` rows for exactly one behaviour, repeated about `13--14` times.
The resulting 48/48-style scores show that narrow output procedures are
writable under heavy rehearsal. They do not sum to one eight-faculty child.

The “perception” cell was real but narrow. Given an authored last TRY, prior
prediction, and public outcome, it learned to emit the prescribed extracted
record or abstain (`21 -> 47/48/48`). That is useful conditional extraction,
not autonomous broad perception. It is “single-hop” because one supplied
situation directly determines one response. Its response was never fed into a
second learned decision whose answer depended on it.

Three joint precedents keep the record honest:

- SEQ120 trained PROSPECT, REVISE, ADDITION, and COPY in one adapter. Headline
  routines mostly landed, but conditional locality/preservation did not.
- SEQ106 co-located prediction/action and an input-order convention.
- SEQ113 co-located exact memory and arithmetic, but tested them separately;
  the retrieved memory never controlled the arithmetic or an action.

Thus coexistence is partly shown; composition is not.

## What existing agentic post-training already gives us

The primary-source survey in
`research_notes/analysis/2026-09-13_agentic_posttraining_single_policy_survey.md`
shows that AgentTuning, Agent-FLAN, FireAct, STeP, ETO, SCoRe, Search-R1,
ReTool, and AgeMem already train combinations of reasoning, tools, retrieval,
multi-turn action, recovery, or external-memory operations. We should reuse
their data lessons rather than claim the generic loop is unprecedented:

1. Train closed trajectories, not a bag of psychological labels.
2. Supervise child decisions; keep task, tool return, world outcome, teacher,
   and evaluator text as loss-masked inputs.
3. Balance decision types, including useful READ, irrelevant/MISS, expected
   outcomes that should **not** trigger revision, genuine mismatches that
   should, and verified STOP.
4. Use learner-distribution correction or RL only as a separately named
   successor if response-only SFT installs atoms but not junctions.
5. Test on held topology families and causal twins; training loss and atomic
   fixture scores are insufficient.

TMEM and PEAM also preclude “first agent to put its experience in LoRA” as a
safe claim. The defensible unshown conjunction is narrower: a target-disjoint
birth teaches a generic composition policy; later the same adapter absorbs
exact opaque facts from its own life; after a clean reset the child chooses to
read and compose them into new goal-directed actions; own/foreign life,
same-identifier derangement, memory cuts, birth-only, and active controls move
the result causally.

## The next birth, staged

Keep the already accepted Stage 0 material audit and Stage 1 exact-text base
interface sentinel.

For the first fit, use `M-COMBINE-4`:

1. **SEEK:** choose what relation is missing and issue the opaque READ.
2. **PROSPECT:** interpret the returned EVENT, predict one consequence, STEP.
3. **CHECK:** compare prediction with CURRENT and revise only the implicated
   relation when mismatched.
4. **CONTINUE/STOP:** carry state into the next SEEK or stop only at a verified
   goal.

Use `32` causal-twin pairs = `64` cases = `256` unique child continuations.
Present every continuation four times at D1 (`1,024` presentations / batch 4 =
`256` updates), and only if intact but underfit continue the same paired fits
to eight presentations (`512` total updates). This repetition is anchored much
better than showing 1,024 unique turns once.

Compare:

- `LINKED`: authentic returned relation controls the next cue/action.
- `UNLINKED`: the same four atomic target classes, counts, token mass, and
  update tape appear only as independent local vignettes.
- `BASE`: no fit.

Both fitted arms must first pass matched atomic SEEK/PROSPECT/CHECK/STOP panels
and generic canaries. Then held exact-text chains decide whether the junction
exists. If both fitted arms succeed, mere co-residence was enough; if only
LINKED succeeds, causal trajectory training taught the junction; if atoms
pass and chains fail, the missing object is still composition/interface; if
atoms fail, the dose failed and no composition conclusion follows.

Only after a combined child passes exact-text chains should one continued copy
receive exact personal EVENT writes with birth replay. Only after actor/reader
coexistence passes should the own/foreign/deranged personal-memory factorial
and GOAL-BRAID goal-switch test run.

If the narrow repeated curriculum works, the later confirmation birth can
expand to the literature-informed three-stratum mixture (selective interface,
full successful loops, and matched recovery/no-change contrasts). Breadth is a
confirmation step, not the first acquisition gamble.

## LoRA placement answer

There is no controlled feed-forward-only versus attention-inclusive result in
this project. Every successful current Level-0/1 cell used all-layer rank-8
LoRA on attention (`q/k/v/o`) and MLP (`gate/up/down`) projections. The only
feed-forward-only TMEM-shaped pretest also changed layers, rank, optimizer,
initialization, and dose and degraded or collapsed, so it cannot identify the
module choice. Keep the all-layer recipe for this bridge. Reopen a module
ablation only if the combined writer shows a specific policy-memory
interference that placement could diagnose.

## Claim boundary

A positive `M-COMBINE-4` result would show a lab-taught composition policy in
one adapter, not parenting, self-learning, personal-memory utility, MCTS, or a
flywheel. The paper-relevant bridge arrives only when that policy uses later
own-life parametric EVENTs after reset and follows the expected causal memory
cuts. MCTS remains a useful analogy for adaptive branching, not the taught
algorithm or measured claim.

