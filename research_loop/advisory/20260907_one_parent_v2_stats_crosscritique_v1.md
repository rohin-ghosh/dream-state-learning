# One-parent/one-child v2 statistical cross-critique v1

Date: 2026-09-07

Status: **read-only cross-critique of a proposal-only synthesis**. This memo
changes no synthesis, bound plan, manuscript, workflow, benchmark, model,
tokenizer, adapter, or run state. It authorizes no implementation, scientific
generation, fit, GPU use, network access, or scientific claim.

Audited bytes:

- v2 repair synthesis, SHA-256
  `f5c839b58b248fca69bf0928443c7fb0f039faddf2ad5ca693b323232b750f6d`;
- statistics attack, SHA-256
  `78baa757a374bd803744c2e31ace142ef3c6ca343a1b298f95cc16f94562820e`;
- manuscript/protocol audit, SHA-256
  `29c7a2db3a7fcac38f2166afd3c74efec40c7a0962aaaff136f8eb55e52778ad`;
- objective-coverage audit, SHA-256
  `0751e6fea2821137b7e892dc2bd30f979ae63e8ca79b599ea404fc1706653c71`.

## Verdict

**REVISE BEFORE USING THE SYNTHESIS AS AN EXACT V2 SOURCE.** A1--A4 and B are
directionally strong repairs. They resolve the largest conceptual errors: a
root is one matched five-service unit; claims are conditional on one fixed
parent and child checkpoint; gain-AUC `D` is the sole primary endpoint;
`D>0` must be followed by beneficial `W_P`; absolute P1 improvement and
terminal R0 outperformance are separate estimands; and bare “saturation” is
replaced by comparator-specific local-plateau language.

They are not yet exact enough to ratify. A5 introduces a new outcome-dependent
missingness error: setting an entire missing service/cut to zero can create a
large favorable `D` when a write-off control is missing. A3 still does not
define the normalized per-program score or common entry measurement. A1--A2
name but do not fully instantiate `Q` and the seed coupling. A4 repairs the
logical SESOI problem but defers every number needed to call the study powered.
Its familywise-control statement covers only the five superiority rungs, not
the non-erasure gates, local-plateau claim, or two terminal mechanism claims.
B also omits the exact equivalence margin, an uncertainty-aware search-headroom
test, and a hard requirement that R0's once-only strong-memory certificate
pass before “strong comparator” wording is released.

The correct disposition is to preserve the synthesis as a repair map, apply
the exact closures below in the deliberated v2 bytes, and re-audit the final
statistics manifest before any scientific root.

## A1. Root population — PASS IN CONCEPT, REVISE FOR EXECUTABILITY

A1 correctly makes the full five-service root the independent unit, samples a
fresh wake/probe deck per root, pairs that deck within root, prohibits tasks or
cuts from increasing `n`, and conditions inference on one parent policy and one
child checkpoint. This resolves the manuscript's topology/sample-size blur and
the objective audit's concern that roots are replications rather than a
classroom.

However, “hash-bound root packet distribution `Q`” is only a label until the
distribution is enumerated. It currently specifies the deployment deck but
not:

- the nursery-family instance distributions and their pairing across P/U;
- the sampling measure over the registered CompilerGym universe (uniform,
  stratified, or weighted), program order law, and collision/reuse law;
- the distributions of actor, parent, writer, environment, updater, and probe
  randomness inside a root;
- whether program-universe construction itself is fixed or sampled; or
- the population over which the 10,000-sequence search reference in B is
  evaluated.

“Program identities may recur across roots only as independent draws” is
coherent if roots sample with replacement from a fixed finite universe, but
the exact sampler and weights must be frozen. Otherwise iid is asserted rather
than established.

**Required exact closure.** Define `Q` as a canonical schema with the nursery
packet, wake/probe deck, order, every stochastic domain, sampler algorithm,
sampling weights, rejection/collision behavior, and support. State
`mu_D=E_{R~Q}[D_R]` and print the conditional scope in the manuscript. If any
program panel is instead fixed across roots, narrow the claim to that panel or
predeclare a crossed root/program analysis; do not retain program-population
language with a root-only interval.

## A2. Counter-keyed randomness — PASS IN CONCEPT, REVISE THREE EDGES

The nonshifting counter design and no-retry rule are correct. Sharing a random
opportunity across matched potential calls is legitimate variance reduction,
not extra replication, provided each service keeps the correct marginal law.

Three exact edges remain:

1. `experiment_hash` can be circular if it hashes a manifest that contains
   keys derived from `experiment_hash`. Define a ratified `protocol_hash` over
   source bytes that excludes generated root/key receipts, then derive the
   root manifest from it.
2. Specify the KDF/PRF, canonical field encoding, root-master generation,
   counter-to-distribution transform, and collision tests. A tuple alone is not
   a seed algorithm.
3. Enumerate coupling across both **arms and cuts**. State which probe uniforms
   are shared across P0/P1/U0/U1/R0 at a cut and whether the same uniforms are
   reused across cuts. Treatment-only or structurally absent calls need named
   disjoint purposes. The backend-honored-seed canary must test every stochastic
   backend, including fitting/order and updater calls, not only the actor.

Cut 0 should be cached once per common childhood checkpoint: one parented
entry measurement shared by P0/P1 and one unparented entry measurement shared
by U0/U1. Counter-matched duplicate evaluations are inferior because hardware
nondeterminism can break equality and add baseline noise. R0 has its own entry.

The restart law is sound, but it must distinguish a resumable infrastructure
interruption before a request from an observed agent/system failure after a
request. The latter stays in the assigned root and follows the failure-outcome
law; it is never rerun under the same or a new key.

## A3. Outcome and cut timing — REVISE

The gain-AUC algebra and cut order are coherent. The new absolute estimands
`L_terminal` and `T_R0` correctly close the objective audit's distinction
between relative gain, absolute within-life improvement, and terminal
outperformance. Declaring pointwise curves descriptive also resolves the
manuscript audit's primary-endpoint mismatch.

The claimed “exact outcome” is still not exact. “Best nonnegative IR
reduction” does not define the normalized scale later used for every `.05`
margin. Bind the per-program quantity, for example

```text
v_q = max(0, (I_base,q - I_best,q) / I_base,q)
V_c,r(t) = (1/8) * sum_q v_c,r,q(t),
```

including the `I_base=0` law, legal best-of attempts, tie handling, compiler
failure, invalid action, generated-token/action budget, and aggregation order.
State explicitly that `V(16/32/48)` follows program update, active-text update,
then committed-or-quarantined SLEEP, in that order. Hash the exact scoring
implementation.

Entry subtraction removes an intercept; it does not remove bounded-scale
floor/ceiling compression or a parenting-induced difference in the quality of
later self-generated training data. The synthesis dropped three required
protections from the statistics attack:

- a target-blind development headroom gate before confirmation;
- mandatory reporting of `V_P(0)-V_U(0)` and floor/ceiling occupancy; and
- one predeclared headroom-normalized sensitivity analysis.

Restore all three. Never match, exclude, regress, or stratify on realized entry
value, admitted-row count, or store yield because they are post-treatment.

## A4. Fixed sequence — PASS FOR FIVE NULLS, REVISE ITS BOUNDARY

For the five listed superiority nulls, fixed-sequence testing can strongly
control familywise type-I error if every rung uses the same predeclared alpha
and testing stops permanently at the first nonrejection. Requiring an observed
practical margin in addition to rejection can only make each rung more
conservative. The ordering is scientifically coherent:

```text
D -> W_P -> L_terminal -> C_public -> T_R0.
```

It ensures that “parenting taught beneficial learning” requires both a
positive interaction and beneficial parented writes, and that package gain is
not confused with absolute terminal superiority.

The bytes should say `lower endpoint of the two-sided 95% t interval > 0`, not
merely `mean(X)>0`; otherwise the success test is linguistically ambiguous.
Rung 1 should say parenting **increased** the later benefit of writes, not only
“changed” it. Each rung needs its own named practical margin `delta_j`; using
`.05` for interaction gain-AUC, within-life change, and terminal between-system
value is permissible only after separate scale-specific justification.

The family-control sentence is too broad unless its boundary is printed. It
controls the five superiority sentences only. It does not cover:

- statistically assessed routing, proposal, DREAM, generic-behavior, and
  action-cardinality non-erasure;
- the R0 local-plateau sentence in B; or
- the link-derangement and action--outcome-binding claims in D.

**Required exact closure.** Make the five-rung sequence the headline family.
Define the non-erasure gates either as deterministic zero-violation safety
requirements or as a simultaneous non-inferiority family with contrasts,
margins, confidence level, and multiplicity adjustment. State that every
released headline rung also requires those gates. Append B as an explicit
sixth gated composite claim after rung 5, or allocate it separate alpha, or
make it descriptive. Put D's two claims in a separately adjusted secondary
family or label them exploratory. “Run after primary artifacts are immutable”
prevents design feedback; it does not solve multiplicity on the same roots.

### What the hierarchy can honestly say about inherited competence

Passing `D`, `W_P`, and `L_terminal` shows more than a favorable parented entry
score: the write permission had a differential, beneficial effect and P1 ended
above its own entry. It does **not** identify a pathway independent of inherited
competence. Parenting may improve entry competence, which may cause better
deployment actions, higher-quality admitted rows, and thus larger write gains.
Those are legitimate post-treatment mediators in the total interaction.

Therefore the eligible sentence is:

> This frozen parenting protocol increased this fixed child system's later
> benefit from enabling personal writes, and those writes were beneficial on
> the registered fresh deployment distribution.

Do not say that the result “rules out inherited competence,” estimates a pure
learning-rate parameter, or proves a domain-general learning algorithm.

## A4 power language — CONCEPTUAL REPAIR PASSES, NUMERICAL CONTRACT MISSING

The synthesis correctly abandons the false claim of 80% power at a true effect
of `.05` under a rule also requiring `estimate >= .05`. Calling `.05` a minimum
observed practical effect and moving the design alternative above `.05` is the
right repair.

It remains an instruction to do a power analysis, not a power analysis. Before
v2 source binding, it must supply:

- the exact design alternative for `D`, desired power, alpha, candidate N, and
  distribution family or resampling population;
- operating characteristics for the **joint** interval-plus-estimate rule;
- type-I error and power under the complete blinded/adaptive N procedure if an
  internal variance tranche remains, including the exact variance bound and
  routing table;
- the effect of technical missingness and the non-erasure gates; and
- enough sensitivity cases for bounded, skewed, floor/ceiling-heavy `D_r`.

If only rung 1 is powered, say so and call later rungs precision-gated. If the
paper says the full five-rung conclusion is powered, simulation must estimate
the probability that **all rungs through five** pass under a predeclared joint
effect/covariance alternative. Per-rung 80% power does not imply 80% power for
the gated conclusion.

The simplest exact option is fixed `N=32` with no variance-adaptive routing.
If the blinded N rule is retained, simulation must include any dependence
between sample variance and mean under the nonnormal bounded outcome; normal-
theory independence cannot be assumed silently. If no feasible N meets the
chosen target, the synthesis's “precision-limited” language is correct.

## A5. Failure and non-erasure — REVISE; NEW BLOCKING ERROR

Scoring a valid completed probe with no legal dispatched action as zero is a
sound behavioral failure value. Scoring an entire technically missing service
cut as zero is not generally conservative for a difference-in-differences.

For example, let every observed cell remain at `V=.50` from entry through cut
48, so every true gain and `D` is zero. If the three post-entry P0 cuts are
technically missing and set to zero, then `gAUC(P0)=-.50`, `W_P=.50`, and
`D=.50`. The missing write-off control alone creates overwhelming apparent
evidence that parenting taught beneficial writes. Missing U1 can distort `D`
in the same favorable direction. The one-row-per-root requirement does not
cure bad imputation.

**Required exact closure.** Separate three cases:

1. **Observed behavioral failure:** a valid completed probe opportunity with
   no legal action scores zero.
2. **Protocol-defined system failure caused inside the assigned service:** if
   the estimand deliberately treats this as performance, prebind a composite
   terminal/future-zero law symmetrically for every service and validate it in
   simulations.
3. **Administrative/infrastructure missingness:** lost artifacts, evaluator
   outage, or corruption is missing, never automatically zero. Do not replace
   the root. Use a predeclared bounded worst-case analysis over `V in [0,1]`
   and release a claim only if its lower conclusion survives, or block the
   confirmatory claim at a frozen missingness threshold. Report complete-case
   estimates only as sensitivity because complete cases need not be unbiased.

Quarantining a rejected write and retaining the prior adapter is correct and
produces an observed outcome, not missingness.

The non-erasure paragraph still defers the contrasts, margins, reducers, and
joint decision. Calling them “safety gates” does not remove statistical false-
pass risk. Bind exactly which services/cuts are compared, whether every root
must pass deterministically or a root-level non-inferiority interval is used,
and how the several gates combine with the five-rung family. The manuscript
audit is right: any undefined endpoint must be deleted rather than constructed
after results.

## B. Local plateau and public outperformance — PASS IN CONCEPT, REVISE TEST

B correctly selects R0 prospectively for the public claim, tests R0's own two
increments rather than substituting P0 after inspection, requires absolute
terminal outperformance through rung 5, requires positive P1 last-era growth,
and forbids bare “saturation.” This directly addresses the objective audit.
Keeping a separately labeled descriptive P0 plateau is coherent.

Five bytes remain necessary:

1. Name the equivalence margin and justify it separately from the gain-AUC
   SESOI; `s1`, `s2`, `D`, and terminal value are different estimands.
2. Define the exact last-era interaction
   `[V_P1(48)-V_P1(32)]-[V_R0(48)-V_R0(32)]`, its root-level reducer, and all
   lower-bound tests.
3. Treat B as the sixth fixed-sequence composite claim after rung 5. Because
   all listed components must pass, they can form an intersection-union test,
   but every component null, alpha, sidedness, and equivalence procedure must
   be explicit.
4. Define root-paired search headroom, for example
   `H_r=V_search,r(48)-V_R0,r(48)`, and require an uncertainty rule appropriate
   to the target population. A deterministic fixed-seed search score being
   `.10` above the observed mean R0 does not by itself establish population
   headroom.
5. Require all once-only `ACTIVE_TEXT_FIXED` strength certificates to pass
   before calling R0 a **strong** active-memory comparator or releasing the
   standing-objective sentence. If they fail, R0 may remain a frozen-parameter
   active-memory reference, but not a certified strong baseline.

Even after passing, the eligible wording is only “R0 showed a registered local
plateau over programs 16--48 under this updater/read/action budget, while P1
continued improving and ended higher.” It is not representational saturation,
global active-memory saturation, or superiority to plural memory methods.

## New statistical gaps outside A/B

The synthesis appropriately keeps connected/compressed knowledge inside LoRA
as a separate experiment. Its C/D replacements are not yet claim-ready:

- C defers the compression rate and functional non-loss thresholds and drops
  the objective audit's illustrative numeric candidate. That is acceptable for
  a repair map, but no “shorter code” sentence is confirmatory until the exact
  denominator, threshold, root reducer, confidence rule, and raw-ledger scope
  are bound.
- D says intact P1 “must beat” each diagnostic without defining a root
  statistic, practical margin, interval, failed-derangement value, or what
  happens when an exact no-fixed-point derangement is impossible. Roots with no
  authentic traversed link cannot be filtered out. Bind failure-inclusive
  estimands before scientific identities.
- The two D claims use the same locked roots but sit outside A4. Their late
  execution does not make their p-values multiplicity-free. Put them in a
  separately corrected secondary family, power them separately as the
  objective audit requires, or keep them descriptive.

The manuscript correction list otherwise agrees with the manuscript audit:
active text remains a candidate until certified; isolated on-policy stores are
not shared contents; exact gain-AUC `D` leads; one-parent/one-child is topology;
undefined secondary endpoints are removed; and the baseline stays singular.

## Required v2 statistical closure list

1. Fully instantiate `Q`, including nursery and every stochastic domain.
2. Replace circular `experiment_hash` seeding with a defined pre-manifest
   protocol hash, KDF, encoding, and coupling table.
3. Bind the normalized per-program score and cache common entry values.
4. Restore headroom, entry-difference, floor/ceiling, and headroom-normalized
   sensitivity requirements.
5. Replace missing-cut-equals-zero with a causal-failure versus infrastructure-
   missingness law and worst-case/blocking rule.
6. State exact confidence-bound success syntax and scale-specific margins.
7. Supply actual type-I error/power simulations for the chosen N procedure;
   distinguish primary power from power for all five rungs.
8. Integrate non-erasure and B into the multiplicity contract.
9. Make R0 “strong” and its plateau claim conditional on certificate passage.
10. Bind failure-inclusive, multiplicity-controlled estimands for D's terminal
    diagnostics or keep them descriptive.

With those repairs, A1--A5/B would be coherent enough for source-bound
deliberation. Without them, the synthesis is a strong advisory map but not an
exact statistical protocol.
