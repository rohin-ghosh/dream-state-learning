# PCFL-Active-Stream C03 simulation-gate repair

Date: 2026-09-02

Status: **read-only statistical advisory only**. This memo addresses only
canonical critique blocker `C03`. It does not edit or ratify the proposal,
authorize implementation or scientific CPU/GPU/model/provider work, release a
claim, or create successor authority.

The canonical critique bytes were verified at SHA-256
`a8c9cb6e57a710c0d53908a660f6b02be796ca9dd4b4f0e5ace3825e6676f8ce`.

## Ruling

The current Monte Carlo gate is not executable: its scenario set uses a later
DEV quantity, does not define unique distributions or couplings, does not
enumerate the global-null cases, does not identify a simultaneous binomial
confidence construction, and permits an infeasible required case to be merely
documented.

Do **not** repair it by adding discretionary scenarios. Delete the Monte Carlo
go/no-go gate and replace it with the exact analytical rule below. The rule
uses only the already-bound independent-root unit, failure-inclusive P1--P4
definitions, planning alternative `theta_j>=.20`, variance premise
`Var(Pj_w)<=.09`, and deterministic endpoint supports. It covers every
distribution, atom pattern, skew, zero inflation, nested failure mechanism,
and cross-endpoint coupling satisfying those conditions. Consequently it has
no DEV-defined failure rate, copula, tail family, admissibility judgment, or
infeasible simulation case.

Fixed `n=26` is not defensible for this distribution-robust rule. Its `.806317`
calculation is exact only for four normal-theory marginal t-power calculations;
none of P1--P4 is normally distributed by construction. P1--P3 are minima, P4
contains a maximum, and assigned failures and binding indicators create atoms.
Normal marginals are also impossible for bounded P1--P4. The smallest integer
certified by the analytical rule below is **72 fresh roots**. This is a
minimum for this explicit Bennett/IUT construction, not a claim of a globally
minimax sample size over every conceivable test.

## Exact analytical decision

The frozen estimands imply these deterministic supports:

```text
P1_w in [-1, 0.75]   # its minimum includes binding score indicator - .25
P2_w in [-1, 1]
P3_w in [-1, 0.275]  # maximize min(A-tau,L-tau,L-A+.05), tau>=.50
P4_w in [-1, 1].
```

For P3, the upper endpoint follows by taking `tau=.50`, `L=1`, and balancing
`A-.50=L-A+.05`, which gives `.275`; larger `tau` cannot increase it. These
bounds include every registered failed-assignment score.

Let `v=.09`, `h(u)=(1+u)log(1+u)-u`, `n=72`, and use the following fixed
thresholds, rounded upward from the unique size-bound solutions:

```text
c1 = 0.096414
c2 = 0.099513
c3 = 0.090277
c4 = 0.099513.
```

Reject component `H0j: theta_j<=0` exactly when
`mean_w(Pj_w)>=c_j`. Reject the global IUT null only when all four components
reject. There is no t statistic, fitted covariance, simulated critical value,
DEV-selected parameter, alternate transform, or post-dispatch change.

For upper support `b_j in {.75,1,.275,1}`, the one-sided Bennett bound at every
component-null boundary is

```text
Pr_theta_j<=0(mean(Pj)>=c_j)
 <= exp[-n*v/b_j^2 * h(b_j*c_j/v)]
 <= .05.
```

For `theta_j>=.20`, lower support `-1`, and the same variance cap, the lower-tail
rate is least favorable at `theta_j=.20`. Therefore

```text
Pr_theta_j>=.20(mean(Pj)<c_j)
 <= exp[-n*v/1.2^2 * h(1.2*(.20-c_j)/v)].
```

At the frozen rounded thresholds, the four size bounds are

```text
(0.04999945, 0.04999973, 0.04999778, 0.04999973),
```

and the four alternative miss-probability bounds are

```text
(0.04590773, 0.05385682, 0.03314583, 0.05385682).
```

Thus global IUT size is at most `.05` under the full union null, regardless of
cross-endpoint dependence. By the union bound, arbitrary-dependence joint power
at `theta_j>=.20` is at least

```text
1 - sum_j miss_j = 0.81323279.
```

At `n=71`, choosing for each endpoint the smallest threshold whose Bennett
size bound is `.05` gives thresholds

```text
(0.09715696, 0.10029770, 0.09093570, 0.10029770)
```

and miss bounds summing to `.20244255`, for a joint lower bound only
`.79755745`. Hence 72 is the first integer certified by this rule.

This statement is conditional on the proposal's true root-summary variance
premise `<=.09`; C03 does not repair or reinterpret the separate simultaneous
DEV variance-certification gate. If independence across roots, a support bound,
the variance premise, complete failure-in-place scoring, or the fixed 72-root
roster cannot be certified before Stage C, the only result is
`STOP_CONFIRMATION_INFEASIBLE`. No condition is waived and no root, endpoint,
or failure case is excluded.

## Failure and null coverage

No probabilistic failure scenario is needed. Once scientific dispatch begins,
every registered missing, malformed, timed-out, failed, or unexecuted assigned
cell is mapped into P1--P4 exactly as frozen. Any mixture of those outcomes is
covered because the proof permits arbitrary root distributions on the supports
above. Dependence among sides, checkpoints, targets, branches, components, and
P1--P4 is unrestricted within a root. Only distinct roots must be independent.
Environment-wide `NOT_RUN` before the first scientific dispatch produces no
test and no claim.

Likewise, no finite list of null configurations is needed. The size proof
covers the complete global null

```text
union_(j=1..4) {theta_j<=0},
```

including one boundary component with the others arbitrarily favorable,
multiple boundary components, and the all-null case. Under every global-null
point at least one component has size at most `.05`, so the probability that
all four reject is at most `.05`.

If a future proposal nevertheless declares a named failure or distributional
scenario mandatory, its generator, parameters, support, coupling, and expected
P vector must be frozen before B0. Failure to instantiate any required
scenario is `STOP_CONFIRMATION_INFEASIBLE`, not “infeasible,” “inadmissible,”
documented-and-excluded, or grounds to redefine its moments.

## Monte Carlo confidence construction if simulations are retained descriptively

The analytical rule above has zero Monte Carlo gating scenarios. Simulations
may be reported only as non-gating sensitivity analyses. To remove the current
confidence ambiguity, let `B` be the total number of scalar Monte Carlo bounds
actually registered before B0 across all power and size scenarios, and set

```text
alpha_MC = .01 / B.
```

For a power scenario with `R` independent simulation replicates and `K` global
IUT rejections, its one-sided Clopper--Pearson lower bound is

```text
L = 0                                      if K=0
L = BetaQuantile(alpha_MC; K, R-K+1)      otherwise.
```

For a size scenario with `Q` global rejections, its one-sided
Clopper--Pearson upper bound is

```text
U = 1                                      if Q=R
U = BetaQuantile(1-alpha_MC; Q+1, R-Q)    otherwise.
```

Counting every reported lower or upper bound once in `B` gives at least 99%
simultaneous coverage over the entire frozen table by Bonferroni. Per-scenario
99% intervals are forbidden. The replicate count, RNG/counter mapping,
Beta-quantile implementation/version/float mode, table cardinality `B`, and
all scenario bytes must freeze before B0. A missing replicate or infeasible
required scenario is STOP; it cannot reduce `B`. These intervals cannot
override or rescue the analytical Stage-C rule.

## Resource consequence

Replacing 26 by 72 roots multiplies Stage C by `72/26=2.76923077`:

```text
target-evaluation rows = 72*908 = 65,376
planning compute cap   = 72*20 = 1,440 H100-equivalent hours
planning storage cap   = 72*.25 = 18 TB.
```

These are arithmetic consequences, not resource authority. If the complete
roster and separately authorized resource envelope cannot support them, the
result is `STOP_CONFIRMATION_INFEASIBLE`; cells are not pruned.

## Exact normative replacement text

> Before B0, delete the DEV-dependent Monte Carlo scenario gate in full. Stage
> C uses exactly 72 fresh independent twin-pair roots. For the four frozen,
> failure-inclusive root summaries, use deterministic supports
> `[-1,.75]`, `[-1,1]`, `[-1,.275]`, and `[-1,1]`, respectively, and the
> separately gated true-variance premise `Var(Pj_w)<=.09`. With
> `h(u)=(1+u)log(1+u)-u`, reject component `j` exactly when its 72-root mean is
> at least `(0.096414,0.099513,0.090277,0.099513)_j`; reject the global
> intersection-union null only when all four reject. The one-sided Bennett size
> bounds are at most `.05` for every component null, and at planning truth
> `E(Pj_w)>=.20` the four miss bounds sum to `.18676721`, giving
> arbitrary-dependence joint power at least `.81323279`. No DEV output,
> distribution family, copula, failure frequency, simulated critical value, or
> Monte Carlo confidence interval enters this decision. All assigned failures
> remain in place. Failure to certify independent roots, any deterministic
> support, the separately bound variance premise, complete scoring, the full
> 72-root roster, or its resource envelope is
> `STOP_CONFIRMATION_INFEASIBLE`; no failed or infeasible required condition is
> excluded, recentered, rescaled, or documented away. Any retained simulation
> is descriptive only and uses simultaneous 99% Bonferroni--Clopper--Pearson
> bounds with per-bound tail `.01/B`, where `B` counts every frozen scalar Monte
> Carlo bound before any run.

