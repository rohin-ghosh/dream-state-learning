# PCFL-Active-Stream confirmatory power design

Date: 2026-09-02

Status: **read-only statistical advisory only**. This memo does not edit or
ratify the proposal, authorize implementation or CPU/GPU/model/provider work,
release a scientific claim, or create successor authority. Bare contract names
refer to `research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/`.

## Recommendation

Use **26 fresh twin-pair world-life roots**, not 24, and analyze four
failure-inclusive root summaries as one global **intersection-union test
(IUT)**. Test each of P1--P4 one-sided at alpha `.05` and release the joint
claim only when all four reject. Do not Bonferroni-split alpha for a claim that
is true only when every component is true. Fold every claim-bearing component
gate into the four tested summaries; an untested point-sign gate cannot remain
in the confirmatory sentence.

This is the smallest fixed root count justified by the proposal's planning
alternative `delta=0.20` and SD bound `sigma=0.30`, provided the composite
summaries, simultaneous variance bound, diagnostics, and prospective
simulation below all pass before confirmation dispatch. Otherwise Stage C is
calibration-only or stopped; roots and cells are not changed after dispatch.

## Why 24 roots do not have 80% joint power

Under the current one-sided Bonferroni test, at `n=24`, `df=23`,
`alpha=.0125`, and standardized distance `0.20/0.30=2/3`,

```text
lambda = sqrt(24)*(2/3) = 3.265986
c       = t_(.9875,23)  = 2.397875
power   = 1 - F_nct(c; 23, lambda) = 0.800576.
```

That is marginal power for one endpoint. If the four statistics were
independent, joint power would be `0.800576^4 = 0.410782`. With unspecified
dependence, the Frechet/union lower bound is only
`max(0,4*0.800576-3)=0.202305`; perfect positive dependence is the exceptional
case in which joint power can remain about `.801`. Mandatory P1 component
signs lower end-to-end power further.

The current observed-mean gates are an additional contradiction: at a true
mean exactly `.20`, `Pr(sample mean >= .20)` is about `.50`. Thus P1, P2, and
P4 cannot simultaneously use `.20` as both the planning truth and a raw sample
gate and still be described as 80%-powered. Recommended repair: remove the raw
`observed mean >= .20` gates and retain `.20` as the prospective design
alternative. If a practical effect greater than `.20` is itself the claim,
test against `.20` and plan at `.40` (again a `.20` distance); do not mix the
two designs.

## Four chain-complete root summaries

All quantities below are computed once per independent root. Sides,
checkpoints, treatments, targets, lanes, calls, and actions remain nested. A
missing, malformed, timed-out, failed, or unexecuted assignment remains zero
in its assigned denominator. No complete case analysis, root replacement, or
post-abort denominator change is permitted.

### P1: randomized, chain-complete flywheel and reconsolidation

For each side/checkpoint/treatment fork, freeze six ordered binary link passes:

```text
h1 = selected the registered world-directed informative probe
h2 = obtained the registered positive information gain
h3 = added the registered newly supported decisive public evidence
h4 = admitted and could read the branch delta under the assigned lane
h5 = completed the certified branch-spanning working path
h6 = executed the successful later return (V=1)
C_l = product(h_r, r=1..l), l=1..6.
```

`C_l=0` after the first failed link, so a lucky later action cannot receive
mediation credit. Define each randomized cumulative-link contrast as

```text
d_l,w = mean_(side,checkpoint) [
          C_l(AUTH) - 0.5*(C_l(TWIN)+C_l(NULL))
        ].
```

At 3L, apply the same cumulative-chain scoring to the exact registered
same-event lanes. Keep failure-inclusive integrative value for the separate
common-history conditions, which do not contain the diagnostic-action chain.
Let `r_q,w` be the six current
reconsolidation contrasts (SELF minus RAW-AO, ACTION-ONLY, WITNESS/MECH;
semantic-cut minus sham difference-in-differences; authentic minus same-probe
twin outcome; and generic SELF minus the rootwise strongest non-SELF
common-history condition), with terminal `Y` replaced by the relevant
failure-inclusive cumulative chain score for the first five and retained for
the common-history contrast. Define three binding scores as the mean, over twin
sides, of the indicator that BIND-AUTH chose the authentic probe, BIND-TWIN
chose the twin probe, or BIND-SHAM preserved the authentic probe, respectively,
minus the presealed four-probe Bayes value `.25`. Put all three into the same
set. Then use

```text
P1_w = min(d_1,w,...,d_6,w, r_1,w,...,r_6,w, binding scores_w).
```

Because `P1_w` is no greater than any included component, `E(P1_w)>0` implies
positive population means for every claimed link and intervention. This is
conservative but chain-complete. Recurrent-versus-nonadaptive reader
separation remains a construct-validity stop, and the class-informed SELF
ceiling remains descriptive; neither is an extra unpowered efficacy gate.

### P2: acquisition at every post-native checkpoint

Replace the mean plus three point-sign gates by one conservative summary:

```text
a_k,w = Y[SELF,w,M_k,T_NEW,k] - Y[SELF,w,M_(k-1),T_NEW,k]
P2_w  = min(a_1.5,w, a_3,w, a_6,w).
```

Then `E(P2_w)>0` implies positive mean acquisition at every checkpoint. Failed
or unsupported rows stay zero and cannot be discarded.

### P3: acquired-and-retained old knowledge

For the exact preassigned OLD rows, let `B_OLD,w` be their presealed
target-only/twin-byte Bayes ceiling and freeze

```text
tau_w = max(0.50, B_OLD,w + 0.20).
```

If `tau_w>1`, the construct is invalid rather than relaxed. With `A_w` the
failure-inclusive value at the first post-acquisition snapshot and `L_w` the
value on the same rows at 6L, define

```text
P3_w = min(A_w - tau_w,
           L_w - tau_w,
           L_w - A_w + 0.05).
```

Testing `E(P3_w)>0` jointly requires above-floor acquisition, above-floor 6L
value, and the original `-0.05` noninferiority condition. In particular,
`0 -> 0` yields `P3_w=-tau_w<0`. Acquisition failures remain population
failures; the estimand is not conditioned on successful roots or targets.

### P4: cross-era action

Retain the registered rootwise comparator envelope:

```text
P4_w = AUC(Y[SELF,w,CROSS])
       - max(AUC(Y[AS-RAG,w,CROSS]),
             AUC(Y[frozen AS-EXT,w,CROSS]),
             AUC(Y[AS-MECH,w,CROSS])).
```

All three component contrasts are reported. Binding/action-direction
requirements needed by the causal sentence are already inside P1; they must
not survive as additional unpowered P4 signs.

The rootwise minima and maximum are frozen before data. The planning effect
and SD apply to these final four summaries, not to smoother precursor
components.

## Test family and exact fixed count

Let `theta_j=E(Pj_w)`. The scientific claim is

```text
H1 = intersection_(j=1..4) {theta_j > 0}
H0 = union_(j=1..4)        {theta_j <= 0}.
```

Reject the global null only if all four ordinary one-sided one-sample t tests
reject at `.05`. This IUT has strong size at most `.05`: under any point in
`H0`, at least one component null is true, and the probability that all tests
reject is no greater than that component's `.05` size. Bonferroni is neither
needed nor helpful here.

At `n=26`, `df=25`, and distance/SD `2/3`,

```text
c = t_(.95,25) = 1.708141
marginal noncentral-t power = 0.951579
dependence-free joint lower bound
  = 1 - 4*(1-0.951579) = 0.806317
independent joint power = 0.951579^4 = 0.819936.
```

At `n=25`, the corresponding marginal power is `.944343`, giving a
dependence-free lower bound `.777372` and independent joint power `.795278`.
Thus 26 is the smallest integer meeting 80% by both calculations. This result
holds only after all claim gates have been embedded in P1--P4 and the raw
`.20` sample-mean gates are removed.

## Simultaneous variance planning

The four separate 95% DEV SD bounds are not simultaneous. With eight DEV
roots and four final composites, use a familywise 95% Bonferroni variance
bound:

```text
U_j = s_j * sqrt(7 / chi2_quantile(.05/4, 7))
    = 2.290483 * s_j.
```

Since `chi2_quantile(.0125,7)=1.334270`, all four `U_j<=.30` requires each
observed DEV `s_j<=.130977`. Freeze the formulas, quantiles, and numerical
library before DEV output. This is a normal-theory variance statement and is
usable only when the frozen diagnostics below pass. Its severity is honest:
eight DEV roots provide weak variance assurance. If it fails, obtain a
separately authorized larger variance pilot before confirmation or stop; do
not substitute four marginal bounds, add confirmation roots adaptively, or
prune failures/cells.

## Prospective simulation and executable diagnostics

Before Stage C, freeze a simulator and seed hash and run at least 100,000
replicates per scenario. It must generate the exact nested denominators and
failure rules, compute the component links and minima/maxima, and execute the
four `.05` t tests and global IUT. It must not simulate four Gaussian endpoints
while omitting the component gates.

Required scenario grid:

- independent roots; all dependence is within root;
- final failure-inclusive composite means `.20` and SDs `.30` at the planning
  boundary, without recentering after minima/maxima are computed;
- exact discrete target denominators, plus Gaussian, rescaled `t_5`, skewed
  beta/binomial, and zero-inflated marginals;
- catastrophic whole-root failure probabilities `0`, `.05`, and `.10`, plus
  cell failures at the DEV upper bound, always scored in place;
- four-endpoint Gaussian-copula equicorrelations
  `rho in {-0.30,0,.25,.50,.75,.90}` and an antirank coupling of empirical
  marginals; and
- P1 link/lane common-root loadings `0`, `.5`, and `.9`, so the minimum and all
  cumulative-link gates are actually exercised.

For power, require the one-sided 99% Monte Carlo lower confidence bound on
`Pr(all four tests reject)` to exceed `.80` in every admissible scenario. For size,
put each endpoint at its null boundary in turn while the others are favorable
and require the one-sided 99% Monte Carlo upper bound on global rejection to be
at most `.0525` (simulation tolerance around the analytically controlled `.05`
IUT size). A scenario that cannot realize mean `.20` and SD `.30` after failure
inclusion documents infeasibility; it is not silently recentered.

The following deterministic diagnostic is run on each **eight-root DEV** final
summary vector before confirmation dispatch; there is no alternate test if it
fails:

```text
finite(x) and len(x)=n
s(x)>0
unique(x) >= 4
largest_atom(x) <= .50
abs(adjusted_Fisher_Pearson_skew(x)) <= 1.5
max(abs(x-mean(x))/s(x)) <= 2.5
Shapiro_Wilk_p(x) >= .01
```

Pin the Shapiro-Wilk implementation/version and tie behavior. A failure prevents
confirmatory dispatch and records `STAGE_C_CALIBRATION_ONLY_NOT_CONFIRMATORY`.
On confirmation data, report the same diagnostics descriptively but do not add
a new outcome-dependent claim gate: doing so would itself require inclusion in
joint power. DEV diagnostics do not prove normality or license a post hoc
bootstrap, sign test, transform, dropped root, or changed alpha; their role is
to stop use of the planned t approximation when the non-smooth composites
already behave pathologically before confirmation.

## Resource consequence

Moving from 24 to 26 confirmation roots multiplies every complete Stage-C
quantity by

```text
26/24 = 1.083333.
```

At the frozen 908 target-evaluation rows per root, this is **23,608 rows**
instead of 21,792, an increase of 1,816 rows. Under the current linear planning
caps, 480 H100-equivalent hours becomes **520 hours**, and 6 TB becomes
**6.5 TB**. Model calls, actions, provider tokens/cost, transfer time, and
review time require the same measured per-root multiplication; nested rows or
clones never increase statistical `n`. The future resource contract must raise
those caps explicitly or stop confirmation without pruning the roster.

## Bottom line

Twenty-four Bonferroni roots are individually, not jointly, 80%-powered, and
the raw `.20` gates make the discrepancy worse. The smallest coherent repair
is 26 fresh roots, a four-component `.05` IUT, chain-complete conservative
root summaries, simultaneous DEV variance control, and a frozen simulation
and diagnostic gate. Any retained qualitative claim gate must be placed inside
those summaries and repowered; otherwise it is descriptive only.
