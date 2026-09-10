# ICLR nine-page evidence-slot outline v1

Date: 2026-09-09

Status: source-only manuscript planning. This is not an architecture,
experiment, claim, implementation, or execution authorization. It does not
modify `paper/iclr2027_experience_models/main.tex`. Scaled-THINK details remain
pending the direct Fable--Codex synthesis.

## The one paper story

Modern agents arrive with general reasoning skill but do not normally convert
one deployed life into a persistent change in how they later think and act.
Dream--LoRA--Think tests a developmental stack:

```text
inherited base/post-training
 -> optional target-blind learnability bootstrap
 -> one-to-one adaptive parenting in a disjoint classroom
 -> parent-deleted deployment
 -> THINK / DREAM / SLEEP over the child's own action--outcome experience
 -> later parent-absent action
```

The paper should not claim that all E0--E6 rungs passed merely because the
architecture contains them. Its title, abstract, figures, and conclusion must
be selected from the highest prospectively passing rung.

## Nine-page allocation

| pages | section | evidence slot |
|---:|---|---|
| 0.35 | Abstract | motivation, exact tested system, strongest passing result, one failure/limit |
| 1.15 | Introduction | genes/schooling/parenting/life distinction; why post-deployment personal experience is irreducible; contributions with no mechanism inflation |
| 0.75 | Problem and claim ladder | define one life, personal write, parenting-of-learning estimand, strong active-text comparator, E0--E6 separation |
| 1.15 | Architecture | exactly THINK, DREAM, SLEEP; context ledger; transactional cumulative LoRA; parent as development infrastructure, not a fourth organ |
| 1.20 | Parenting and clean lineage | adaptive parent, child application and public outcomes, clean developmental child, mechanism sibling, disposable deployment descendant, parent/nursery deletion |
| 1.45 | Benchmarks and causal design | target-blind classroom; deployment task; parenting/write factorial; strong baseline; held-out panels; root unit; budgets; stopping |
| 1.80 | Results | writer floor; primary learning curves; parenting interaction; retention/transfer; mechanism diagnostics; resource table |
| 0.65 | Related work | fleet post-training, external agent memory, offline experience distillation, inference-time recurrent/parallel reasoning, continual learning |
| 0.50 | Limitations and conclusion | local task/distribution, one base/parent/baseline, finite life, no phenomenology/alignment/population claim |

Approximate total: 9.0 pages before references. Detailed contracts, prompts,
schemas, additional controls, and full failure transcripts go to appendices.

## Four main figures/tables only

### Figure 1 -- the organism and its development

One simple diagram:

```text
PARENT/CLASSROOM (temporary)
         |
         v
THINK -> action -> outcome -> THINK
  |                            |
  +--------- DREAM ------------+   active context only
               |
               v
            ledger
               |
        SLEEP compile + write
               |
               v
        next-age personal LoRA
```

Show parent deletion before deployment and make clear that the ledger/auditor/
compiler are infrastructure, not extra cognitive organs.

### Figure 2 -- clean lineage and causal comparisons

Show three object types:

1. canonical developmental child, continued only under unchanged mechanism;
2. mechanism-change sibling, forked at the last clean common snapshot; and
3. disposable exam/deployment descendant with no return edge.

Overlay the parenting/write factorial only after its exact successor is
ratified. This figure should make contamination impossible to misunderstand.

### Figure 3 -- primary lifetime result

Use root-level uncertainty on entry-adjusted held-out value across registered
lifetime cuts. Plot the full learner and one certified `ACTIVE_TEXT_FIXED`
comparator; show the baseline's prospective plateau window, old-competence
retention, and terminal absolute values. Do not plot task/checkpoint rows as
independent observations.

If E1 is the highest passing rung, replace this with the parenting-by-write
interaction and the four causal curves. If only E0 passes, use the writer
failure/recovery figure instead and narrow the paper.

### Table 1 -- noncompensatory evidence and cost

Rows: E0 absorption/extraction/routing/rollback; entry effect; parenting-by-
write interaction; absolute learning; transfer; retention; baseline plateau;
late-window learner gain; terminal difference; generated tokens; calls;
optimizer tokens/steps; GPU hours; wall time; storage/retrieval work. Every row
states unit, interval, practical threshold, and PASS/FAIL/NOT RUN.

Mechanism-relay and compression results belong in a second table only if they
actually pass prospectively; otherwise state them as open objectives.

## Abstract slots

Use five sentences and fill only from sealed evidence:

1. **Gap:** fleet-level post-training fixes a shared agent before deployment;
   a particular agent's later life normally does not change its parameters.
2. **System:** one parent raises one target-blind child, then disappears; the
   child THINKs, DREAMs over active context, and SLEEPs by compiling its own
   grounded action--outcome continuations into a transactional per-life LoRA.
3. **Design:** independently raised roots separate parenting, personal writes,
   and entry competence, while one certified evolving active-text agent is the
   strong frozen-parameter comparator.
4. **Result:** insert only the highest passing absolute, interaction,
   retention, and late-window result with uncertainty and scale.
5. **Boundary:** insert the most informative failure or scope limit (for
   example writer drift, installed-policy rather than learnability, or finite
   local plateau).

Do not put connected knowledge, compression, traversal, expansion, baseline
saturation, or continuing lifetime improvement into the abstract unless that
exact rung passes its independent claim gate.

## What the bootstrap can and cannot contribute

If adopted after deliberation, call it a **target-blind learnability-policy
bootstrap** only after entry-adjusted later acquisition or a bootstrap-by-
parent interaction passes. Before that it is an installed policy.

The expensive primary comparison should be the candidate bootstrap versus a
prospectively fixed active non-metacognitive policy package. A form/style sham
and adapter-free birth are diagnostic anchors. There is no honest claim that a
control has “identical semantics minus metacognition.”

The paper must separately report:

- direct entry-policy change;
- later personal-experience acquisition;
- incremental parent benefit;
- whether a new personal SLEEP commit carries delayed behavior after parent
  and context removal; and
- task value per generated token, to distinguish useful amortization from
  simply producing more reflection.

## What scaled THINK would need to show

Pending Fable adjudication, the manuscript reserves only these conceptual
slots:

- one child can explore several state continuations without turning thought
  branches into child lineages;
- sequential depth, parallel breadth, and post-outcome reflection are distinct
  allocations;
- the learned skill is opening, extending, merging, retaining, or stopping a
  route based on uncertainty and expected information/action value;
- one matched-total-token topology test identifies whether branching adds
  value beyond more tokens;
- one generous-budget system test asks whether the complete organism benefits;
  and
- longer private traces, confident prose, or branch count alone are not
  endpoints.

The main paper should include scaled THINK only if it is frozen before the
scientific child and its behavior is measurable through public decisions,
revision, information-seeking, action value, or learned stopping.

## Evidence-dependent paper versions

### Version A -- full developmental-learning paper

Requires passing E0, causal E1, absolute parented personal learning, retention,
and terminal/lifetime superiority over the certified active-text comparator.
Mechanism E2/E4/E5 may strengthen but is not silently implied.

### Version B -- parenting plus per-life learning

Requires E0, parenting-by-write interaction, absolute parented learning, and
parent-absent retention/transfer. Use no baseline-saturation or connected-
representation language.

### Version C -- writer and developmental failure science

If higher rungs fail, report the prospective writer result: what can be stored,
what remains extractable, how action-channel or ritual failure emerges, and
which transactional gates prevent a bad sleep from corrupting a life. This is
scientifically valid but must not wear the full experience-model claim.

The version is selected by the registered claim ladder, never by preferred
story.

## Before the mechanism freeze

1. Obtain and adjudicate Fable's scaled-THINK/continuity response.
2. Ratify one compact E0 writer source and exact projection.
3. Prove rejected-corpus quarantine and previous-child promotion.
4. Freeze rank/capacity semantics, dose, replay, SLEEP cadence, and the allowed
   early-to-later plasticity schedule from bounded development-only evidence.
5. Freeze clean-child, sibling, classroom-branch, and disposable-descendant
   lineage rules.
6. Prebind one early horizon and at most one longer developmental runway, with
   causal proximal, ritual, harm, imprecision, and final transfer gates.
7. Convert this outline into exact `main.tex` claims only after the applicable
   design receives full deliberation and human ratification.

## Current blockers stated plainly

- The long-life runner still uses the legacy writer path.
- Rejected adapter rollback is not yet rejected-evidence rollback.
- The adaptive parent does not yet learn from delayed outcomes in the current
  implementation.
- Current classroom promotion can replace a better previous child while still
  looking acceptable versus raw base.
- Scaled THINK and the bootstrap/control semantics are not yet ratified.
- No current prospective run proves the central parenting, connected-memory,
  or long-lifetime superiority claims.

Those are the engineering/scientific jobs. Page count is not the bottleneck;
valid evidence is.
