# Hostile statistical review of the RML evidence ladder

**Date:** 2026-09-03  
**Role:** fresh ICLR-style methods/statistics reviewer  
**Status:** read-only scientific advisory. This note authorizes no code change,
model call, GPU run, benchmark promotion, or scientific claim.

## Overall verdict

The RML proposal has the skeleton of a serious causal benchmark, but the
current evidence ladder cannot yet support the phrase **learned experiential
intelligence**, and its proposed confirmation size cannot support the stated
**beyond-saturation** result.

The strongest defensible interpretation of a fully positive fixed-deck study
would be narrower:

> In a prespecified population of synthetic maintenance worlds, a frozen
> language-model controller used target-blind, experience-derived semantic
> memory to improve later held-out action under a registered resource envelope;
> the action effect depended on the world binding and on cited memory, and the
> same admitted corpus could be transported into per-life LoRA weights without
> a practically important loss relative to text.

That is potentially publishable. It is not general intelligence, open-ended
continual learning, or evidence that weights are a better memory substrate.
The flywheel clause requires a separately randomized collection experiment.
The saturation clause requires an equivalence design much larger than the
currently proposed 8 pairs per pack, or a prospectively justified wider
practical plateau margin.

My recommendation is therefore:

1. Keep Stage A and G1--G3 as construct-validation and branch-kill stages.
2. Run a 48-pair, three-pack common-deck confirmation for the action-memory
   claim, conditional on a variance-based power audit.
3. Do not include `saturation` in the main claim at that sample size. Either
   make slopes descriptive, or run a separately powered equivalence extension.
4. Run the on-policy experiment as a distinct blocked randomized trial. Treat
   its four link-specific intention-to-treat effects as evidence consistent
   with a flywheel, not as identified natural mediation.

## What the checked-in evidence establishes

`rml_d0/stage_a_report.json` is correctly firewalled as
`CPU_STAGE_A_INSTRUMENT_CONFORMANCE`. It reports `passed: true`, zero model/GPU/
network calls, 16 pair attempts, 32 target attempts, 215,056 states, 1,230,784
transitions, 996 events and 285 mappings at the largest cut. It also contains
useful target-byte twins, nine-action solutions, J deletion witnesses, and a P
atoms-only value of 1/4.

These are properties of one finite deterministic subject package. They are not
sampling evidence, model evidence, an independent oracle audit, a memory
effect, or a population estimate. The hard-coded digest and in-package
mutation checks do not turn the package into an independent evaluator. The
report contributes zero degrees of freedom to a later method comparison.

The two-pair G1 fast gate is also correctly described as a falsifier. On a
binary success endpoint, `>= .85` over four target sides means 4/4 successes;
3/4 is only .75. The four-pair version permits 7/8. Neither estimates a
population performance rate with useful precision. These gates may reject an
unusable interface, but they must not appear as confirmatory efficacy evidence.

## 1. Unit of inference and hierarchy

The protocol must distinguish four different objects that are currently too
often called a “life” or a “sample.”

### Target population

The target population is not “maintenance worlds” in general. It is the
distribution produced by the frozen RML generator, conditional on a fully
prespecified validity filter, within the three named packs. Packs are three
fixed construct strata, not a random sample of all action domains. A claim may
generalize to these generator distributions; it may not average three packs
into a claim about embodied agents generally.

If invalid generated worlds are rejected, freeze the rejection rule before
generation and report acceptance rates and reasons. Hand-picking valid worlds
or target panels after observing model behavior destroys the sampling
interpretation.

### Independent scientific unit

The independent unit for common-deck efficacy is one independently generated
**causal-program counterfactual twin pair**. The H and twin sides, all targets,
all lifetime cuts, all method arms, and all model/adapter seeds are repeated or
nested measurements inside that unit. The twins should ordinarily be reduced
to a prespecified pair-level contrast or mean before inference; counting both
sides as independent doubles the nominal sample size without adding an
independent generator draw.

For the randomized on-policy experiment, each cloned branch is a treatment
unit only because a memory label is randomized to it. The randomization block
is world-side x boundary, and inference must still cluster at the parent
causal-program twin pair. If treatment at an earlier cut changes the state
used at a later cut, cuts are not independent blocks and ordinary crossover
analysis is invalid. The cleanest design randomizes at one post-native boundary
per independently generated life.

### Nested observations

- Targets are measurement replicates nested in stratum x cut x twin side.
- Cuts are repeated longitudinal measures of the same causal program.
- Twin sides are matched counterfactual observations, not two worlds.
- Writer samples, decoding samples, adapter initializations, and checkpoints
  are technical stochastic replicates.
- LoRA seeds must be averaged within world-arm-cut before the world enters the
  confirmatory analysis. A seed is never an independent scientific sample.
- If the same numeric seeds are deliberately used in every world, seed is a
  crossed nuisance factor; if fresh seeds are drawn per world, it is nested.
  State which design is used. Do not alternate between the two interpretations.

Two adapter seeds per world are acceptable for a lean confirmation only after
three-seed calibration shows small seed dispersion and no multimodal failure
mode. Two seeds are not enough to validate an RMS-spread threshold by
themselves. A pragmatic rule is three seeds in locked calibration, then two in
confirmation if the upper confidence bound on seed-induced SD is below .05;
otherwise use three and count none of them as additional `n`.

### Consequence for the current proposal

“At least eight new pairs per pack” means `n = 24`, not 48 twin sides, hundreds
of targets, or thousands of resolver calls. Eight units in a pack cannot
support a precise pack-specific conclusion or a useful pack x method
interaction. At that size, pack consistency can be a qualitative guardrail,
not three independently significant replications.

## 2. Claims and preregistered estimands

The paper needs a short estimand table fixed before confirmation. Avoid a
post-hoc “strongest baseline” computed on confirmation data. Select the primary
baseline using DEV/locked calibration and freeze it, or define an all-baseline
conjunction.

Let `Y_wmls` be the pair-level normalized action value for independent world
pair `w`, method `m`, log2 lifetime cut `l in {1,2,3}` corresponding to
`{2x,4x,8x} L_native`, and stratum `s`. Within each pair, first average the two
twin sides, registered targets, and technical seeds using frozen weights.
Define `Y_wml` as the equal-weight mean of N/O/J/P/X. R remains diagnostic.
The arbitrary equal weighting must be declared as part of the construct, and
every stratum must also be reported.

| ID | Claim | Preregistered pair-level estimand | Decision rule |
|---|---|---|---|
| V0 | Benchmark validity | Oracle, shortcut, twin, necessity, isolation and direct-closure quantities | A deterministic gate. Any material failure invalidates the affected panel; it is not repaired statistically. |
| V1 | Resolver can use supplied local knowledge | Gold recurrent minus no-memory/open/atoms action and valid-trace contrasts | Engineering gate only. No population language. |
| W1 | DREAM/admission adds useful learned content | Prediction-supported compiled text minus deterministic witnessed atoms, with identical writer opportunities; raw proposal and matched reflection are additional contrasts | Positive prospective precision/coverage and later action; binding/life shuffle must remove the action gain. |
| A1 | Experience-derived memory improves post-native action | Mean over worlds of log-lifetime AUC difference between compiled text and the one frozen primary native external-memory baseline | One-sided 97.5% CI lower bound > 0 and point estimate >= .10, or a different smallest important effect fixed before data. |
| A2 | The gain is not isolated to one behavior | Compiled-text contrasts for N, O, J, P and X | Prespecified guardrails: no catastrophic negative stratum; J and P both directionally positive. Multiplicity-adjusted secondary intervals are reported. |
| T1 | LoRA transports the admitted corpus | Same-corpus LoRA minus identical-corpus text AUC | Noninferiority: lower 95% CI > `-.05` if the plan retains its stricter margin; `-.10` is an engineering gate, not a persuasive paper margin. |
| T2 | Consolidated corpus matters beyond generic LoRA training | Same-corpus LoRA minus direct-QA/raw-event LoRA | Superiority lower 97.5% CI > 0; same rank, examples/touches, optimizer, replay and reader budget. |
| B1 | Authentic world binding causes action | Authentic memory minus binding-shuffled/twin memory under the same substrate | Both registered directional contrasts pass, and target-twin action redirection is observed. A cited cut alone is secondary mechanism evidence. |
| D1 | Finite post-native development | Compiled-memory `8x - 2x` pair difference plus `8x - 4x` last-interval difference | Net lower CI exceeds a practical gain and last-interval lower CI > 0; O retention and N/J/P guardrails pass. |
| S1 | A named baseline plateaus | Both baseline interval changes `4x-2x` and `8x-4x` | A simultaneous equivalence region lies entirely inside `[-delta,+delta]`, with delta prospectively justified; see below. |
| S2 | RML grows after that plateau | RML interval changes, evaluated on the same worlds and cuts | Simultaneous lower bounds are > 0 for the interval(s) named in the prose, plus an RML-minus-baseline difference-in-differences lower bound > 0. |
| F1 | Memory changes evidence acquisition | ITT of randomized authentic versus each registered invalid-memory assignment on target-relevant information gain per action | Blocked randomization interval lower bound > 0. |
| F2 | The intervention improves later memory | Same assignment ITT on post-consolidation supported target-relevant precision/coverage | Lower bound > 0; no conditioning on choosing a particular action or on successful compilation. |
| F3 | The intervention improves later action | Same assignment ITT on presealed later action value | Lower bound > 0, all randomized branches retained. |

The manuscript should retire “learned experiential intelligence” as an
estimand. It has no measurable counterfactual. W1+A1+B1 establish a learned,
experience-conditioned memory/action effect on RML. T1/T2 establish parametric
transport. D1 establishes finite development. S1/S2 establish a resource- and
benchmark-specific crossover. F1--F3 establish one randomized improvement
cycle.

## 3. Saturation and slope tests

### The current rule is not sufficient

Failure to reject a baseline slope is not evidence of saturation. Conversely,
requiring only an improvement upper bound `<= .02` would allow a sharply
declining baseline to be called “plateaued.” A plateau is an equivalence claim
and needs both lower and upper bounds.

With exactly 2x, 4x and 8x, do not fit an elaborate nonlinear saturation
curve. There are only two post-native interval changes. On the log2 lifetime
axis define, for every baseline `b`:

```
d_b,24(w) = Y_w,b,4x - Y_w,b,2x
d_b,48(w) = Y_w,b,8x - Y_w,b,4x
```

Call baseline `b` plateaued only if a simultaneous confidence region for both
means lies wholly inside `[-delta_b,+delta_b]`. The region must also cover any
co-primary growth metric named in the claim; do not prove equivalence on a
pooled average while N, J, or P is still rising. Require a simultaneous oracle-
headroom lower bound of at least .10 and continuing unique causal-information
growth, otherwise the flat score may be a ceiling or a stalled benchmark.

For RML, “continued after the baseline plateaued” requires more than a positive
`8x-2x` total. Require a positive lower bound for `8x-4x`, plus the positive
difference-in-differences

```
mean[(Y_RML,8x-Y_RML,4x) - (Y_b,8x-Y_b,4x)] > 0.
```

If only the total 2x-to-8x gain is positive, write “improved across the tested
range,” not “continued improving after saturation.”

### The proposed sample is far too small for delta = .02

A planning approximation for a simultaneous equivalence interval is

```
n approximately ((c + z_power) * sigma_interval / delta)^2,
```

where `c` is the simultaneous critical value. Taking `c ~= 2.3` and 80% power
(`z = .84`) gives the following *optimistic* pair counts before allowance for
non-normal bounded outcomes, pack heterogeneity, attrition, or extra metrics:

| Paired world-level SD of an interval change | Pairs for `delta=.02` |
|---:|---:|
| .05 | 62 |
| .075 | 139 |
| .10 | 247 |

At `n=24`, the interval-change SD would need to be about .03 or less. That is
not a reasonable default assumption for multi-step agent behavior. More
targets within a world can reduce measurement noise but cannot remove genuine
between-world heterogeneity.

Therefore the existing plan cannot honestly combine “24 pairs” and “all named
baseline slopes are within .02.” The options are:

1. Drop the saturation claim and report the response surface.
2. Justify a larger practical plateau margin, such as .05, from task utility
   before results; do not choose it to make equivalence pass.
3. Use a blinded, preregistered internal-pilot variance re-estimation with a
   hard maximum sample size. The pilot may estimate nuisance variance only and
   may not change arms, delta, outcomes or effect thresholds.
4. Fund the required sample. If `.02` remains non-negotiable, a cap around 192
   pairs is defensible only when blinded calibration shows interval SD no more
   than roughly .088; otherwise even that cap is underpowered.

Every saturation sentence must name the baseline, outcome, lifetime interval,
capacity policy and resource envelope. A method forced to a fixed retrieval or
memory cap has saturated **under that cap**, not intrinsically.

## 4. Analysis and multiplicity

The common-deck method comparison is not a randomized treatment experiment.
Running all algorithms on the same sampled worlds creates pairing, but it does
not randomize “method.” Calling an arbitrary paired sign-flip test
“randomization inference” is incorrect unless the sign exchangeability
assumption is stated. Use world-pair level estimates with a prespecified
studentized paired analysis and robust confidence intervals; a sign-flip test
may be a sensitivity analysis when the paired differences are plausibly
symmetric. With fewer than about 40 independent pairs, ordinary cluster
bootstrap intervals are themselves unstable.

Blocked randomization inference is exact for G5 because memory labels really
are randomized among cloned branches. Preserve the assignment schedule and
enumerate/permutate labels only within the registered world-side blocks, while
forming uncertainty at the parent twin-pair level.

Recommended confirmatory model:

- primary analysis on one reduced observation per world pair x arm x cut;
- pack fixed effects and pack-by-method contrasts, because three packs cannot
  support a credible random-pack variance estimate;
- repeated cut covariance handled within pair, not by treating cuts as rows;
- bounded-outcome paired regression or studentized mean contrast as primary;
- hierarchical mixed models only as secondary precision/sensitivity analyses;
- unconditional ITT scoring: illegal, timeout, malformed, failed compile and
  failed fit cells remain zero where scientifically attributable;
- exact sealed rerun only for prespecified infrastructure failures, never for
  a bad model output.

Multiplicity should follow the claim logic:

1. V0/V1 are validity gates, not discoveries.
2. A1 is the single primary superiority test.
3. T1 is a separately declared noninferiority claim and T2 a superiority
   claim; allocate alpha prospectively if both are headline claims.
4. A claim of beating **all** frozen baselines is an intersection-union claim:
   every one-sided contrast must pass. No “winner” may be selected on the
   confirmation set.
5. A claim that **all** named baselines plateau is likewise conjunctive, but
   each baseline needs simultaneous equivalence across its two slopes and any
   named co-primary metrics.
6. Use max-T or Holm for exploratory arm, pack and stratum contrasts and show
   simultaneous intervals. Do not promote whichever of N/O/J/P/X happens to
   pass.
7. Stop/go looks at calibration and confirmation must be alpha-spending or
   fully separated. DEV and locked calibration pairs must never re-enter the
   confirmatory denominator.

Report effect estimates and intervals, not only gates and p-values. Release
the complete world-pair table so the degree of heterogeneity is visible.

## 5. Sample size and the leanest credible confirmation

No exact sample size is defensible before observing world-level paired
variance from a genuinely locked calibration set. A normal planning formula
for a one-sided .025 superiority test at 90% power is

```
n approximately ((1.96 + 1.282) * sigma_pair / Delta)^2.
```

For a smallest important AUC gain `Delta=.10`, this gives about 24, 43 and 66
pairs when the paired SD is .15, .20 and .25 respectively. These are planning
numbers, not guarantees; the actual calculation should simulate the frozen
bounded target hierarchy and expected failure process.

### Lean confirmation for the action-memory claim

The smallest design I would regard as plausibly confirmatory is:

- 48 new causal-program twin pairs: 16 per fixed pack, generated after every
  prompt, arm, hyperparameter, threshold and analysis choice is frozen;
- 2x, 4x and 8x post-native cuts, plus 0.5x only as a descriptive pre-native
  anchor;
- at least two presealed targets per N/O/J/P/X stratum per twin side and cut;
  targets are averaged inside the pair and never treated as `n`;
- two adapter seeds per world after the seed-stability calibration described
  above, averaged before inference;
- primary arms: compiled text, the calibration-selected strongest comparable
  native external-memory baseline, direct-QA/raw LoRA, and same-corpus LoRA;
- required contextual arms reported on the same panel: no memory/native
  truncation, raw RAG, matched reflection, native linked/graph memory;
- generator-aware program induction as a ceiling/reference unless it truly
  satisfies the same information and resource contract; it must not be called
  a defeated fair baseline merely because it is computationally stronger;
- whole-memory binding/twin interventions for every substrate, on a frozen
  random subset large enough to retain at least 24 independent pairs;
- no confirmation-world hyperparameter selection or corpus repair.

Forty-eight pairs is reasonable only if locked calibration yields paired SD
`<= .20` for A1 and the preregistered simulation shows at least 90% power after
the chosen alpha allocation. Otherwise increase to 72 or 96 pairs, or narrow
the claim. At 48 pairs, slope results should normally remain descriptive.

This design supports an RML action/consolidation paper if effects are large and
consistent. It does not support the `.02` saturation claim.

### Extension required for a beyond-saturation claim

Use the same frozen worlds and arms in a group-sequential equivalence extension
with nuisance-only sample-size re-estimation. A realistic minimum is 96 total
pairs (32/pack) if `delta=.05` is substantively justified and paired interval
SD is no more than about .10. For `delta=.02`, plan up to 192--256 total pairs,
subject to the blinded SD audit. Stop early for futility if the maximum sample
cannot place the simultaneous interval inside the equivalence band even under
the observed nuisance variance.

Do not multiply all expensive arms into this extension. Freeze the few named
baselines to which the plateau sentence will refer. The full baseline panel is
needed for comparative credibility at confirmation; the equivalence extension
needs only RML, those named baselines, and the oracle-headroom checks.

### Separate randomized on-policy trial

Use new world pairs, not the common-deck confirmation worlds. At one frozen
post-native boundary, create isolated branches and randomize authentic, null,
binding-shuffled and twin memory within world-side blocks. Use all assignments
on every world where cloning is exact, with the label permutation sealed before
collection. One information-gathering block, one deterministic consolidation,
and one target deck sealed before collection are sufficient for a one-cycle
claim.

Start with 48 independent pairs only if calibration suggests a paired ITT SD
`<= .20` for a .10 action-value effect and adequate power for the information-
gain endpoint. Because F1 and F3 must both pass, and information gain is likely
noisier, 72--96 pairs is the safer planning range. If null, binding and twin are
each named causal controls, authenticate the claim only when authentic exceeds
each one; do not average three distinct failures into an easy comparator.

## 6. Causal pathway and intervention logic

The fixed-deck study identifies representation/use under common experience. It
cannot identify self-improvement of the experience distribution.

The randomized G5 assignment identifies ITT effects of initial memory on:

1. registered information-seeking action or intervention selection;
2. target-relevant information gain/coverage per action;
3. post-consolidation supported-memory quality;
4. later sealed action value.

Requiring all four positive ITTs is a useful causal-chain conjunction. It does
**not** identify natural direct or indirect mediation. Information action,
evidence and later memory are post-treatment variables. Conditioning on them,
analyzing only successful collectors, or multiplying fitted path coefficients
can introduce selection bias. Initial memory is also not a valid simple
instrument for information gain because it can affect state, resources and
later action through channels other than the measured mediator.

If the paper wants stronger component causality, add interventions rather than
mediation rhetoric:

- After collection, cross the sealed collected traces through every registered
  representation/compiler. This tests whether evidence quality survives a
  common downstream representation.
- Independently swap/null the post-consolidation snapshot before the sealed
  action. This tests whether later action depends on the newly formed memory.
- Replay matched authentic-collector and null-collector public evidence into a
  common frozen compiler when legally possible. This separates collection
  quality from writer quality.
- Preserve action costs and world state in every replay; otherwise “more
  information” may merely mean a different remaining-resource distribution.

Call these controlled component effects. Do not call them a complete causal
mediation decomposition unless a sequential-randomization estimand and its
assumptions are explicitly defined.

## 7. Cost matching and fairness

There is no scalar notion of equal compute across text, graph, retrieval and
LoRA systems. Equal parameter count is not equal memory capacity; equal reader
tokens are not equal index work. The paper should use two complementary
estimands:

1. **Capability under common hard caps:** same public evidence, frozen actor,
   context reserve, action cap, maximum reader calls/tokens, and target deck.
2. **Resource-performance frontier:** outcome against the full realized cost
   vector, with at least a small preregistered budget grid.

Record separately:

- source/environment actions and consumed resources;
- writer/reflection/DREAM calls, input/output tokens and model FLOPs;
- compiler/index/graph build CPU time and bytes;
- persistent semantic text bytes, graph nodes/edges/index bytes, adapter
  trainable parameters and checkpoint bytes;
- adapter examples, touches, optimizer steps, replay mix, train FLOPs and
  energy;
- reader calls, returned tokens, candidates scored, index nodes visited and
  any whole-life scans;
- actor/resolver calls, tokens, latency, failures and wall-clock/GPU-hours.

All generative consolidation arms should share writer model, source chunks,
opportunity count and maximum generated tokens. Text, graph and RAG must be
allowed their native planners/interfaces in the system comparison; a separate
common one-atom channel factorial may diagnose mechanism. Candidate roster
construction, cardinality resolution, clean-base composition and unmounting
are part of the LoRA system and must be charged and disclosed. A hidden
`O(lifetime)` candidate scan defeats a scaling claim even if adapter bytes are
constant.

Do not pad efficient baselines with dummy calls in the cost table. Dummy null
reads are appropriate in G1 to isolate thinking opportunity, but realized
efficiency should count actual useful work. Conversely, do not give RML extra
writer and training compute and then describe a score comparison as
cost-matched. Use matched caps plus Pareto curves.

The exact program learner is scientifically essential as a ceiling/adversary,
but generator awareness may make it incomparable as a resource-matched native
baseline. Label it honestly. The native linked/graph and matched-reflection
arms are the crucial fair external-memory competitors.

## 8. Kill criteria that save compute

The current backward evidence ladder is sensible. The following stops should
be immutable and should cancel later work rather than trigger benchmark repair.

### Before any model work

- Stop the affected generator/pack if independent oracle replay, twin-byte
  identity, opposite valid action, J necessity, P atoms-only ceiling,
  prospective chronology, run/skip isolation, direct-closure, or any shortcut
  probe fails.
- Stop if valid-world acceptance is so selective that the target population is
  no longer the registered generator distribution.
- Stop or redesign before unblinding if `L_native` is not measured for the
  exact deployed model/template or if “post-native” still exposes old source
  history through caches, retrieval metadata or process state.

### G1 supplied-gold gate

- Stop RML model work if typed gold fails; the model/task interface lacks a
  usable ceiling.
- Repair only the controller, not DREAM/LoRA, if typed gold passes but generic
  recurrence fails.
- Stop the construct if no-memory, open-query or P-atoms succeeds above the
  registered ceiling; the target does not require recurrent connected memory.
- Stop if cut/twin replacement does not redirect credited action.

### G2 learned-text gate

- Stop weight work if prediction-supported text fails to improve the
  prospective precision/coverage/action frontier over deterministic witnessed
  atoms, raw proposals and matched reflection.
- Stop the proposed-method branch if compiled text cannot beat raw RAG and the
  strongest fair explicit-memory baseline on both DEV pairs, or if its action
  gain survives binding/life shuffle and cited cuts.
- If generator-aware program induction wins, retain the result and benchmark;
  do not weaken the program arm.

### G3 transport gate

- Stop LoRA claims if fixed-query fidelity < .90, whole-adapter twin/binding
  swaps do not redirect reads/action, or seed failures are material.
- Stop the weights headline if the 95% noninferiority lower bound against
  identical-corpus text is below `-.05` in locked calibration/confirmation.
- Stop calling the effect consolidation-specific if direct-QA/raw-event LoRA
  matches the proposed LoRA under matched training and reader budgets.

### Confirmation and saturation

- Stop for futility after locked nuisance estimation if the maximum sample
  cannot deliver the desired CI width for A1 or S1.
- Stop a general three-pack claim if a prespecified leave-one-pack-out analysis
  reverses the effect or a pack shows a materially harmful interaction; report
  the bounded packs instead.
- Stop `continued` language if the last interval lower bound is not positive,
  old retention fails, causal coverage stops growing, or reader/rank work grows
  linearly without being named in the claim.
- Stop `plateau` language if either interval equivalence test fails, oracle
  headroom is absent, the baseline is merely capacity-capped, or only a pooled
  score is flat.

### On-policy

- Do not power the full trial if a sealed relay sentinel shows no treatment-
  induced difference in information action.
- Stop the flywheel claim if any preregistered ITT link fails, if later targets
  were not sealed before collection, or if analysis conditions on a
  post-treatment success.
- A positive fixed-deck result survives this failure; the flywheel wording does
  not.

## 9. Strongest alternative explanations

Even a high score has many non-intelligence explanations. The final design must
make the following accounts implausible:

1. **Rendered-language prior:** meaningful maintenance words let the pretrained
   model solve tasks without life-specific experience. Target/state/renderer/
   identifier/passive-signature probes and byte-identical opposite twins are
   essential.
2. **Generator-template learning:** repeated DEV/calibration productions teach
   the finite generator rather than a world life. Hold out complete productions
   and freeze confirmation generation after all tuning.
3. **Host reader as solver:** typed keys, unique-cardinality resolution,
   candidate rosters or graph traversal may perform the inference attributed
   to memory. Charge and ablate these operations; preserve open versus recurrent
   and atoms versus schema controls.
4. **External snapshot does all epistemic work:** LoRA may only resubstitute
   candidate-constrained training cues while the explicit semantic graph
   remains the real memory. Same-corpus text, generative reads, held-out cue
   forms and whole-adapter swaps determine the narrow transport claim.
5. **More compute, not better consolidation:** DREAM receives extra samples,
   writer tokens, training passes or resolver calls. Match opportunity caps and
   publish resource frontiers.
6. **Benchmark tailored to RML ontology:** schemas, one-hop compiler views and
   query grammar may mirror the hidden generator. Non-isomorphic packs,
   production holdouts and an external action slice are needed for broader
   plausibility.
7. **Procedural imitation rather than a connected world approximation:** the
   adapter may memorize action macros. A real procedural-skill baseline,
   fresh handles/layouts and J/P binding interventions are necessary.
8. **Generic policy/compliance change:** LoRA may alter caution, formatting or
   action priors rather than store life facts. Candidate-only clean base,
   wrong-life adapters, instruction-preservation probes and twin redirection
   address this.
9. **Survivor bias:** only successful writers, fits, recognized reads or valid
   traces are analyzed. All registered cells remain in the unconditional
   denominator.
10. **Pseudo-replication:** targets, sides, cuts, calls or seeds are counted as
    independent. Reduce to causal-program pair level.
11. **Baseline handicapping:** graph/A-MEM is forced through a one-atom channel,
    long context is truncated early, or RAG is only cosine top-k. Native
    interfaces are required alongside matched mechanism cells.
12. **Budget-induced plateau:** a baseline flattens only because its bytes,
    index, queries or context are held fixed while RML gets growing compute.
    Saturation language must be resource-qualified.
13. **Ceiling-induced plateau:** the baseline has no room to improve. Oracle
    headroom must remain.
14. **Post-hoc metric/baseline choice:** the best stratum or weakest baseline is
    selected after viewing results. Freeze A1 and the named plateau baselines.
15. **State/resource pathway in G5:** authentic memory changes risk, travel or
    consumable use, and later reward changes without the claimed information
    mediator. Measure costs/state and use downstream snapshot interventions.
16. **Collider-biased mediation:** analysis keeps only branches that collected
    useful evidence or compiled successfully. Use ITT and avoid conditioning.
17. **Evaluator incompleteness:** registered shortest paths or necessity cuts
    may miss alternate legal solutions. Exhaustive certificates must cover all
    legal paths at the action cap.
18. **Cross-life leakage:** adapter/cache/KV/index/provider state survives a
    reset. Process-level isolation and whole-input/output hashes are required.
19. **Multiple testing and optional stopping:** many gates, packs, cuts,
    strata, seeds and baselines create abundant researcher degrees of freedom.
    Freeze the hierarchy and keep DEV/calibration disjoint.

## 10. Construct validation versus headline evidence

| Evidence rung | What it validates | What it cannot headline |
|---|---|---|
| RML-D0 Stage A | Finite fixture self-consistency, target/twin/J/P candidates | Model use, learning, population effect |
| G1 supplied gold | Resolver can use bounded connected local memory to act | DREAM, experience-derived memory, LoRA, scale |
| G2 DEV learned text | Writer/admission/compiler can create useful text on selected development worlds | Confirmatory efficacy, parametric memory, saturation |
| G3 same-corpus micro | LoRA branch is technically viable and binding-sensitive | Population noninferiority, superiority, lifelong learning |
| Common-deck confirmation | Experience-derived representation/use improves held-out RML action | Better evidence acquisition or a flywheel |
| Multi-cut confirmation | Finite acquisition/retention/composition over 2x--8x | Plateau unless equivalence is powered and passed |
| Same-corpus confirmatory LoRA | Recognition-assisted per-life parametric transport | Retrieval-free recall or LoRA superiority to text |
| Randomized on-policy trial | Initial memory causally changes collection and later outcomes for one cycle | Natural mediation, repeated open-ended self-improvement |
| External action slice | Some transport beyond the bespoke generator | General intelligence or broad lifelong-agent superiority |

The construct ladder is valuable even if a later rung fails. It prevents a
negative result from being “repaired” by adding LoRA or intelligence downstream.
But passing all construct gates does not accumulate into statistical evidence;
confirmation still needs new independent worlds.

## 11. Conference plausibility if the gates pass

If the 48+ pair fixed-deck confirmation passes with strong native linked/graph,
reflection, RAG and direct-QA LoRA baselines; if same-corpus transport is
noninferior; if binding/twin/cut interventions redirect action; and if the
randomized on-policy trial shows positive ITTs for information gain and later
action, the work is plausibly competitive for ICLR. The contribution would be
the unusually clean causal evaluation of experience-conditioned memory in
action, not a novel dream/sleep/LoRA architecture.

Even then, three bespoke synthetic packs create a serious external-validity
risk. A small, clean ALFWorld/ScienceWorld or comparable continual slice, full
benchmark/code release, and frank prior-art positioning would materially
improve plausibility. I would view a full, adequately powered causal result as
borderline-to-credible main-conference work, with the decision driven by effect
size, baseline strength, and whether the synthetic instrument teaches a
general lesson.

If only G1--G3 or a two-pair DEV passes, this is an engineering appendix or
workshop result. If common-deck confirmation passes but G5 fails, it can still
be a narrower consolidation/representation paper, but not a self-learning
flywheel paper. If graph/program induction matches or wins, the benchmark and
negative phase diagram may be useful, but the method novelty becomes weak. If
the `.02` plateau claim is made from 24 pairs or from nonsignificant slopes, I
would recommend rejection on statistical grounds regardless of the mean score.

## Bottom line for the authors

RML can support a credible, bounded claim that learned semantic memory from
public experience causally changes later action. The design's twins,
prospective P law, J cut, common deck, same-corpus transport, and randomized
collection stage are unusually good ingredients. The current paper language
nevertheless outruns the proposed sample.

The lean scientific path is: kill cheaply with G1/G2/G3; freeze one primary
action contrast; confirm it on at least 48 independent twin pairs; treat packs,
cuts, targets and seeds with the correct hierarchy; run G5 as an actual blocked
randomized trial; and either fund an equivalence extension or remove
“saturation.” No amount of additional targets, calls, or adapter seeds inside
the same 24 worlds repairs that last problem.

## Local materials reviewed

- `AGENTS.md`
- `research_notes/49_rml_paper_architecture_and_next_experiment.md`
- `research_loop/plans/rml_pilot_v1.md`
- `research_notes/42_system_thesis_and_experiment_map.md`
- `rml_d0/stage_a_report.json`
- `research_loop/advisory/20260903_paper_benchmark_architect.md`
- `research_loop/advisory/20260903_paper_learning_architect.md`
- `research_loop/advisory/20260903_paper_prior_baseline_audit.md`
- `research_loop/advisory/20260903_paper_design_crosscritique.md`
- `research_loop/advisory/20260903_rml_d0_to_stage_b_audit.md`
- `research_loop/advisory/20260903_rml_stage_b_reuse_map.md`
- `research_loop/advisory/20260903_v1e_scientific_value_and_next_gate.md`
