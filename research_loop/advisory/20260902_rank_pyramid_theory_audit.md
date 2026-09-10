# Rank-pyramid theory audit — post-Paper-1 advisory

**Status:** scientific advice only; no architecture, experiment, GPU, or claim
authority is created here.  This is a post-Paper-1 / post-B3 discussion.  It
does not amend the frozen PCFL Active Stream proposal, whose current bytes make
associative LoRA a separately deferred successor after its sealed text gates.

## Bottom line

The useful hypothesis is modest and plausible: a *life-local* low-rank adapter
can compile repeated, verified experience into a lossy, task-conditioned bias,
while a distinct, much slower controller can be trained from carefully
sanitized cross-life data.  A data-mediated hierarchy is a reasonable way to
test that hypothesis because it retains source data, auditability, and a clean
reset boundary.

The strong version is not supported.  Neither a rank hierarchy nor a LoRA
merge establishes that the learned object is “experience,” “agency,” or a
biological synaptic cascade.  Rank is a capacity constraint, not a clock;
verification is a data-quality property, not an effective sample size; and
repeated SVD truncation is an irreversible, order-dependent projection with no
general task-loss guarantee.  Promotion of successful trajectories to base
training is conventional filtered self-training/data curation until it is
shown to improve held-out *action* under strict isolation.  It must remain a
separate, far-future base-training study.

The recommended first test is therefore **not** weight-mediated merging or
base promotion.  It is a new, independently ratified, development-only,
two-timescale **data-mediated** study with reset-isolated per-life experience
and a frozen cross-life operation prior.  It should first establish whether a
rank/data response surface and a cross-life transfer effect exist at all.

## Scope and vocabulary that remain scientifically usable

The project’s existing deliberation is already stricter than the shorthand.
`chg_20260901_experiential_reasoning_adapter_v1` treats the broad hierarchy as
future-only: its per-life result is at most life-bound operation bias, its LOOP
object is distinct and frozen within an evaluation life, and no “learned
agency,” creativity, algorithm, or mediation claim is currently eligible.  The
PCFL Active Stream likewise keeps parametric LoRA as a later independently
ratified successor.  Those boundaries should be preserved verbatim in spirit.

Use the following as engineering labels, not ontological identities:

| Shorthand | Defensible meaning | Not licensed by the label |
|---|---|---|
| base = intelligence | frozen pretrained general capability and priors | intelligence as a unitary state, or a safe permanent memory store |
| context = situation | current rendered state, goal, bounded workspace, and explicit path | the whole external situation, exact history, or an independent timescale |
| per-life adapter = experience | lossy, life-specific parameter change induced by admitted experience | exact episodes, evidence authority, or a literal experiential database |
| across-life LOOP adapter = agency | reusable prior over a declared legal operation/scheduling policy, trained on development lives and frozen at evaluation | agency in the broad sense, long-horizon credit assignment, or transferable world facts |
| base promotion = species learning | an offline population-training/data-governance intervention | evidence of evolutionary analogy, safety, or a continuation of a single life |

Two category errors are especially costly.

1. **Fast/slow is not low-/high-rank.** A rank-64 adapter can be updated every
   token and a rank-2 adapter can be frozen for a year.  A timescale is created
   by the update schedule, data window, optimizer, learning rate, replay,
   reset rule, and evaluation embargo.  Rank affects expressivity and optimizer
   geometry; it does not supply a retention time constant.
2. **A parametric cue is not evidence.** The adapter may make a query,
   hypothesis, or operation more likely.  Exact public claims must still come
   from the immutable episodic store / supported semantic ledger through the
   common reader.  Treating a completion as a fact would erase the project’s
   source-monitoring contribution and makes “verified data” irrelevant at read
   time.

The closest defensible target is therefore: *Does an explicitly isolated,
life-bound adaptation alter useful legal operation distributions and later
held-out action, beyond an identical explicit-memory interface and ordinary
SFT?*  Calling its effect “reasoning” is already stronger than necessary;
calling it “agency” is premature.

## Relation to prior art: plausible combination, limited novelty

| Prior work | What it already establishes | Consequence for this proposal |
|---|---|---|
| **CLS** (McClelland, McNaughton & O’Reilly, 1995) | Fast episodic learning and slow overlapping learning need interleaved replay to avoid interference. | Supports distinct stores and replay, not LoRA, a geometric rank schedule, or a rank-from-data law. |
| **Benna & Fusi** (2016) | Coupled fast and slow synaptic variables can protect memories from overwriting; their interactions are bidirectional. | Supports a multi-timescale inspiration only.  A one-way “merge, reset, decay” stack is not their model and inherits none of its capacity guarantee. |
| **PEAM** (2026) | Embodied experience is consolidated into physically isolated MoE-LoRA skill adapters, with consolidation-worthiness and self-triggering. | Very close on parametric embodied skills and adapter isolation.  A pyramid is not a clean novelty claim. |
| **TMEM** (2026) | Fast LoRA changes the future rollout policy; extraction writes are outcome-RL shaped and LoRA is updated within an episode. | Rules out novelty claims for fast weights changing future behavior, outcome-shaped writes, or self-evolving parametric memory.  Offline cross-episode consolidation and exact-evidence boundaries remain possible differences. |
| **EVAF** (2026) | Sparse, surprise/valence-gated LoRA writes retain goal-conditioned tendencies while retrieval retains shallow facts. | Directly overlaps “procedure/tendency in weights, fact in retrieval.”  Its selective consolidation is a required comparator, not just motivation. |
| **ReLoRA** (2023) | Repeated low-rank updates, merged into the *full* weights with restart-aware optimization, can build a higher-rank update during pretraining. | Shows a useful numerical precedent only.  It does not validate intermediate low-rank SVD compression, per-life/cross-life semantics, self-training quality gates, or policy transfer. |

What might be distinct is the **joint causal discipline**, if demonstrated:

- strict separation of exact evidence, life-local compiled experience, and
  cross-life controller policy;
- a data-mediated, outcome-verified promotion interface with full byte
  lineage, rather than treating a delta as an authoritative memory;
- a predeclared comparison of data- and weight-mediated transfer, including
  loss from merge/truncation rather than only final score; and
- a world-life evaluation in which the effect survives content/binding shuffles,
  cross-life swaps, strong explicit memories, direct trajectory SFT, and
  counterfactual/renamed states.

That is a measurement and systems contribution contingent on results.  It is
not a claim that the pyramid, low-rank policy adaptation, sleep consolidation,
or success-filtered self-training was invented here.

## States that must remain isolated

The proposal becomes uninterpretable if “separate adapters” means merely
separate checkpoint files.  The table gives the minimum state boundary.

| State | May cross a life? | Required treatment |
|---|---:|---|
| Base weights | only by a separately approved population update | frozen and hash-anchored for all current experiments; never trained on evaluation lives |
| Context, workspace, KV cache, RNG, optimizer, compiler process state | no | reset for every life and disposable evaluation clone |
| Immutable episodic roots and supported semantic ledger | no | exact life-local authority; not recoverable from a delta; reset and separately auditable |
| Per-life experience/content adapter `E` | no | rebuilt from the declared parameter anchor and that life’s admitted corpus; never merged upward as a default |
| Per-life operation adapter `P`, if introduced | no | separately mounted, independently reset, and treated as `operation-target-only`, not content-free |
| Cross-life LOOP/agency adapter `A` | development-to-new-life only | train only on sealed development trajectories, freeze before evaluation, and prove no life-specific content survives handle/skin/twin swaps |
| Corpus, selection policy, success labels, and validation scores | only through a registered data interface | preserve hashes/provenance; evaluation targets, scorers, and future outcomes never enter selection or training |

There are two additional non-negotiable rules.

- Do not merge **E** into **A**.  E is expressly allowed to encode life-local
  content.  Adding it to a cross-life “agency” object transports the very
  content the abstraction says should not transfer.  Any eventual
  weight-mediated test can concern only a separately sanitized P-like module,
  after counterfactual tests establish that its model-visible inputs, argument
  tokens, order, IDs, and state rendering do not transmit world facts.
- “Successful life” is not a sufficient admission decision.  It confounds
  task easiness, base priors, lucky exploration, evaluator errors, and policy
  changes.  Retain failed and ambiguous trajectories for audit and matched
  controls; register a target-blind quality/filter rule; and compare it with a
  length-, compute-, and world-balanced random or outcome/binding-shuffled
  corpus.  Success-conditioned data can be useful, but it cannot certify its
  own generality.

## Rank selection: verified volume is a gate, not a law

For a targeted linear map $W \in \mathbb{R}^{m\times n}$, a rank-$r$ LoRA
delta has roughly $r(m+n-r)$ degrees of freedom (often represented by
$B\in\mathbb{R}^{m\times r}, A\in\mathbb{R}^{r\times n}$).  This explains
why a larger rank needs more diverse evidence and stronger regularization.  It
does **not** yield an admissible rule such as `r = f(number of verified
tokens)`.  Verification says a record is supported; it does not make adjacent
tokens independent, distinguish repeated copies from novel decision modes, or
show that the chosen layer/subspace can use the signal.

Use an accumulated verified-data threshold only as a **conservative eligibility
gate** for candidate ranks.  The selection variable must instead be the
predeclared out-of-sample response surface over:

\[
N_{\mathrm{eff}}=(\text{independent world-life}\times\text{verified decision
motif/structural coverage}),\quad r,\quad \text{layers},\quad \text{training
FLOPs}.
\]

`N_eff` must count blocked, deduplicated support units, not training rows or
tokens.  It should be reported with: unique supported roots, counterfactual
motifs, entity/skin renamings, action-outcome diversity, temporal coverage,
and the effective replay weights.  Candidate rank is chosen on development
world-life validation outcomes, then locked and tested on untouched world-life
units.  The holdout that chose rank cannot also establish the pyramid claim.

An exponential rank schedule is thus a budget hypothesis, not a statistical or
neuroscientific consequence.  It is refuted if a fixed rank selected on the
same development surface performs as well, if rank is predicted by raw token
count but not by $N_{\mathrm{eff}}$/coverage, or if the apparent benefit
vanishes after layer placement and optimizer budget are matched.  The claim
“agency is low rank” additionally requires a stable small-rank optimum on
held-out *renamed and counterfactual operation states*, not merely a cheap
rank-8 adapter that improves training-life scores.

## Weight-mediated consolidation: the exact optimization hazards

For one layer, write the mounted update as

\[
 W_{\rm eff}=W_0+s_sB_sA_s+s_fB_fA_f.
\]

Keeping the adapters separate is exact and gives an additive functional
intervention.  Algebraically, their sum can be represented without loss at
rank at most $r_s+r_f$:

\[
 D_s+D_f=[B_s\;B_f]\begin{bmatrix}s_sA_s\\s_fA_f\end{bmatrix}.
\]

This is **not** a rank-$r_s$ slow adapter.  Reducing it to rank $r_s$ uses
some projection, commonly $\widehat D=U_{r_s}\Sigma_{r_s}V_{r_s}^{\top}$.
That SVD is optimal only for the unweighted Frobenius error

\[
 \lVert D-\widehat D\rVert_F^2=\sum_{i>r_s}\sigma_i(D)^2,
\]

not for next-token likelihood, legality of an operation, source monitoring, or
downstream action.  Even for one linear activation, the perturbation is
$Ex$, bounded by $\lVert E\rVert_2\lVert x\rVert_2$; activation covariance,
layer normalization, attention, residual composition, and later nonlinearities
make a small matrix error capable of a large behavioral change.  Near an
optimum the relevant local loss is approximately

\[
 L(\theta+\widehat D)-L(\theta+D)
 \approx g^\top(\widehat D-D)+\tfrac12(\widehat D-D)^\top H(\widehat D-D),
\]

so a Fisher/Hessian- or activation-weighted projection is the relevant object,
if any—not bare SVD.  It, too, needs task-specific evidence.

Specific failure modes follow.

1. **Non-associativity and chronological bias.** With a rank projection
   $P_r$, generally
   $P_r(P_r(D_1+D_2)+D_3)\ne P_r(D_1+D_2+D_3)$.  Earlier or later lives win
   depending on order, and “light singular-value decay” is an undocumented
   recency prior.  It is not the synaptic-homeostasis hypothesis and is not
   neutral forgetting.
2. **Factor and scale mistakes.** LoRA factors are non-unique
   ($BA=(BR)(R^{-1}A)$); adding A’s or B’s is usually wrong.  Merge only the
   scaled full deltas in a common dtype/layout, then refactor, and record target
   modules, alpha/scales, quantization, layer order, and base hash.  Addition of
   deltas on the same fixed tensor is commutative; noncommutativity enters
   through the *merge–project–retrain* sequence, a gated/routed composition, or
   an order-dependent optimizer state.  Those cases must not be called the
   same intervention.
3. **Interference is functional, not spectral.** A singular direction can be
   small in a global matrix norm but decisive on a rare high-value state.
   Conversely, two large deltas may cancel on common states and conflict on a
   counterfactual state.  SVD spectra, delta cosine similarity, and rank alone
   cannot establish transfer or retention.
4. **Restart dynamics are part of the intervention.** ReLoRA reports that
   naive merge/reinitialization can diverge and uses optimizer-state handling
   plus learning-rate warmup.  Reusing moments under new factors biases the
   optimizer toward old subspaces; resetting all moments changes the effective
   learning algorithm.  A pyramid must hash and ablate the optimizer state,
   reset policy, warmup, and checkpoint anchor—not call all variants the same
   “sleep cycle.”
5. **Loss of provenance and reversibility.** Data-mediated promotion leaves a
   replayable corpus and can remove a bad life.  A merged/truncated delta mixes
   individual life effects and cannot generally excise one source.  This is
   incompatible with the project’s correction, invalidation, and audit goals
   unless a per-life delta ledger and reversible pre-projection checkpoints are
   preserved.

The only fair weight-mediated comparison is a four-arm diagnostic on the same
frozen admitted data: (i) exact uncompressed additive deltas, (ii) SVD/projected
merge at the proposed slow rank, (iii) a fresh slow adapter trained on the
accumulated data, and (iv) a no-fast-update slow control.  It must report
per-layer retained energy *and* held-out action, evidence, old-life retention,
and counterfactual behavior.  A projected merge that loses to fresh training
does not demonstrate consolidation merely because its parameters were moved.

ReLoRA is relevant but narrower: it accumulates low-rank updates in full model
weights to gain effective rank and explicitly needs restart-aware optimization;
it neither projects the result back into a slower low-rank adapter nor tests
life-local content, agent credit, or outcome-filtered data promotion.

## Falsifiers to preregister before any later model study

These are proposed decision rules for a new study, not thresholds authorized
for the present program.  Let the independent unit be a paired world-life (or
counterfactual pair), and let the primary outcome be normalized, held-out,
executed action value on presealed post-context targets.  For a minimum
practical effect $\delta=0.05$ on that normalized scale, use a world-life
stratified 95% confidence interval and report every failed life.

| Hypothesis | Positive requirement | Precise falsifier / required claim deletion |
|---|---|---|
| Per-life experience adaptation | `E` beats its strongest predeclared explicit-memory/direct-SFT comparator by $>\delta$, with the CI lower bound $>\delta$, after context/cache reset | CI lower bound $\le\delta$, or a text/graph/direct-SFT comparator matches/exceeds E: delete parametric-experience advantage (and report the stronger comparator). |
| Life binding | Authentic E assignment helps; binding shuffle and cross-life E swap reduce the effect by at least $\delta$ | Either control remains within $\delta$ of authentic E: delete experience-binding attribution. |
| Cross-life agency prior | Frozen A improves new, handle-renamed and counterfactual lives by $>\delta$ while fresh E remains isolated; A carries no decodable life identifier/content above the registered null | No transferable benefit, a benefit only on original identifiers, or content/ID decoding above the null: delete reusable-agency interpretation. |
| Rank-from-data rule | A rank selected from locked development $N_{\rm eff}$/coverage gives $>\delta$ advantage over a fixed-rank rule on untouched worlds | Same/better fixed rank, no stable relation to $N_{\rm eff}$, or selection depends only on raw rows/tokens: reject the volume-selected-pyramid rule. |
| Two-level data-mediated cascade | `E+A` beats E-only, A-only, and a predeclared equal-total-parameter joint/single-adapter comparator by $>\delta$ under equal FLOPs and inference budget | Failure against any named best comparator: no cascade/synergy claim; retain only the winning component’s narrower result. |
| Operation interpretation | At byte-identical public states, swapping the registered operation module (P or A) changes a preregistered legal operation distribution and improves action; the shift survives renamed/twin states | Effect is teacher-forced only, vanishes under twins, or action changes without the registered operation effect: no learned-operation/search-control claim.  Do not infer mediation. |
| Weight-mediated merge | Projected merge noninferior to fresh data-mediated slow training within $[-\delta,+\delta]$ simultaneously on action, retention, source-monitoring, and correction metrics, with no larger false-memory rate | Any endpoint falls below $-\delta$, or merge order changes the outcome materially: reject that merge rule; do not call it sleep consolidation. |
| Success-filtered promotion | Target-blind filtered corpus improves a held-out base/slow-policy evaluation over world-balanced, equal-token random and outcome/binding-shuffled corpora by $>\delta$ | No excess over matched filters, gains confined to easy/lucky lives, or any evaluation-byte leakage: reject the promoted-success-data claim. |

One falsifier dominates all others: any source-monitoring, lineage, reset,
evaluation embargo, or target-taint violation fails closed.  No performance
gain rehabilitates a contaminated result.

## Smallest useful post-B3 study

**Name:** *development-only data-mediated two-timescale calibration*.  Its job
is to falsify the rank-pyramid premise, not to promote a base or validate
weight-space sleep.

**Preconditions.** B3 must be completed on its own terms; this advisory does
not make B3 a pass.  A separate human-ratified preregistration must bind fresh
development world-lives, G1/G2/text transport prerequisites where applicable,
the legal operation grammar, source-byte projections, comparator fidelity,
resources, reset matrix, and the result-to-claim table.  PCFL evaluation roots
remain untouched.  No base update, GPU dispatch, or recurrent merge is implied
by this outline.

**Objects and data flow.** Start every life from one hash-anchored frozen base
and a null (or earlier independently frozen) A.  Train an `E_r` adapter only
from that life’s chronological verified corpus; reset it with the life.  From
*development lives only*, project a separately sealed, rationale-free,
operation-target corpus into `A_R`; train it from data, not E/P deltas.  Make
A read-only on a fresh evaluation life, where E again starts fresh.  Exact
facts continue to pass only through the common bounded reader.  This tests the
claimed semantic split without pretending a local content delta can safely
become general agency.

**Minimal response surface.** Before selecting a schedule, run ranks
`{2, 8, 32}` (or layer-budget-equivalent configurations) across three locked
verified-coverage cuts.  Measure the data summary above, training FLOPs,
adapter bytes, operation distributions, explicit evidence use, action value,
old-life retention, and correction after a contradiction.  Pick one E and one
A configuration on development validation only; hold the test worlds and
counterfactual/handle-renamed variants untouched.  A geometric rule has earned
consideration only if it wins this response surface rather than being assumed.

**Primary factorial, on new world-life units.** At equal declared total
trainable parameters and training FLOPs, run: null; E only; A only; E+A
data-mediated; an equal-budget single/joint adapter trained on the pooled
registered corpora; identical examples in bounded text; strong explicit
episodic/linked memory; direct matched operation/trajectory SFT; and
authentic/binding-shuffled/cross-life-swapped assignments.  Report native
interfaces as primary and common-channel diagnostics separately.  The
independent sample is world-life, never probe, checkpoint, or decoding seed.

**Stop rule.** If the data-mediated E+A factorial does not clear its
preregistered falsifiers, stop the pyramid line and keep only any narrower
component result.  If it does clear them, the next—not simultaneous—study may
compare the four weight-mediated arms above.  Base promotion comes only after
that, with an entirely new data-governance, contamination, capability-drift,
and population-evaluation protocol.  It should never be used to rescue a
per-life failure.

## Sources consulted

Local primary-paper notes were used for the project-specific reading of PEAM,
TMEM, EVAF, CLS, and continual-learning context:
`research_notes/09_sleep_consolidation_deep.md`,
`research_notes/16_tmem_deepread.md`, and
`research_notes/related_work/psychrev1995_complementary-learning-systems.md`.
The proposal/change materials reviewed were `research_notes/00_THESIS.md`,
`research_notes/IDEAS.md` (2026-08-31--2026-09-02 entries), and all five
requested artifacts in `chg_20260901_experiential_reasoning_adapter_v1`.

Primary sources checked for the claims above:

- McClelland, McNaughton & O’Reilly (1995), [*Why There Are Complementary
  Learning Systems in the Hippocampus and Neocortex*](https://doi.org/10.1037/0033-295X.102.3.419).
- Benna & Fusi (2016), [*Computational Principles of Synaptic Memory
  Consolidation*](https://pubmed.ncbi.nlm.nih.gov/27694992/),
  doi:10.1038/nn.4401.
- Guo et al. (2026), [*PEAM: Parametric Embodied Agent Memory through
  Contrastive Internalization of Experience in Minecraft*](https://arxiv.org/abs/2605.27762).
- Ren et al. (2026), [*Scaling Self-Evolving Agents via Parametric
  Memory*](https://arxiv.org/abs/2606.04536).
- Han (2026), [*Memory Depth, Not Memory Access: Selective Parametric
  Consolidation for Long-Running Language Agents*](https://arxiv.org/abs/2606.26806).
- Lialin et al. (2023), [*ReLoRA: High-Rank Training Through Low-Rank
  Updates*](https://arxiv.org/abs/2307.05695).
- Hu et al. (2022), [*LoRA: Low-Rank Adaptation of Large Language
  Models*](https://arxiv.org/abs/2106.09685).
