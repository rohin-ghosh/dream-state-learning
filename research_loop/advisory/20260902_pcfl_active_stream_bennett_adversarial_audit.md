# Adversarial audit of the PCFL Bennett recommendation

Date: 2026-09-02

Status: **read-only statistical advisory only**. This memo audits only the
uniform Bennett argument and the variance-cap certification used by
`20260902_pcfl_active_stream_simulation_gate_repair.md`. It does not edit or
ratify the proposal or authorize implementation or scientific work.

## Verdict

1. The stated Bennett exponents are uniform over `theta<=0` and
   `theta>=.20`; the changing centered support does **not** invalidate that
   part of the 72-root calculation.
2. The unconditional guarantee is nevertheless incomplete. The eight-root
   chi-square SD UCB is exact only for normal root summaries, whereas the
   Bennett recommendation deliberately permits arbitrary bounded, atomic, and
   skewed summaries. Alpha splitting cannot repair an invalid variance UCB.
3. If one accepts a valid distribution-wide `Var(Pj)<=.09` premise, the
   72-root Bennett/IUT rule remains conditional-valid. For an unconditional
   distribution-free claim using only the frozen supports and independent
   roots, the smallest integer certified by the explicit Hoeffding/IUT rule
   below is **538 roots**. A normal-model alpha-split compromise would use 74
   roots, but it is not distribution-free.

## 1. Uniformity of the centered Bennett bounds

For independent roots, Bennett's one-sided inequality for a centered variable
with variance at most `v` and upper bound `M` is

```text
Pr(mean-E(mean) >= t)
 <= exp[-n*v/M^2 * h(M*t/v)],
h(u)=(1+u)log(1+u)-u.
```

### Composite null

Let `X=Pj`, raw support `[a,b]`, mean `theta<=0`, and rejection threshold
`c>0`. Then `X-theta<=M=b-theta` and the requested deviation is
`t=c-theta`. Put `m=b-theta` and `d=b-c`, so `t=m-d` and the exponent rate is

```text
r(m) = v/m^2 * h(m*(m-d)/v).
```

For `u=m(m-d)/v`, differentiation gives

```text
m^3*r'(m)/v
 = -2h(u) + [m(2m-d)/v] log(1+u).
```

Because `m(2m-d)/v > 2u` and
`u log(1+u)-h(u)=u-log(1+u)>0`, the derivative is positive. Decreasing
`theta` increases `m`; therefore the smallest rate, and largest tail bound,
occurs at `theta=0`. The null calculation using `M=b` and `t=c` is uniform over
the full composite null, not merely its boundary.

### Planning alternative

For the lower tail, apply the same argument to `theta-X`. With lower support
`a=-1`, `M=theta-a=theta+1`, and `t=theta-c`. This again has the form above,
with `m=theta-a` and fixed `d=c-a`. The rate increases with `theta`, so its
least favorable point over `theta>=.20` is `theta=.20`, where `M=1.2` and
`t=.20-c`. Using the variance upper bound `v=.09` is conservative for every
smaller true variance. Thus the prior size and miss exponents are uniformly
valid **conditional on the true variance cap**.

## 2. The fallible variance gate

If the variance UCB were an exact 95% upper-confidence procedure for the true
root distribution and DEV were independent of confirmation, two `.05` errors
would not automatically add to `.0975`:

- when the true variance is `<=.09`, Stage-C false rejection is at most
  `alpha_C=.05`;
- when the true variance is `>.09`, false launch is at most
  `alpha_V=.05`, after which rejection can be bounded only by one.

Taking the supremum over the two fixed-parameter regimes gives
`max(alpha_C,alpha_V)=.05`. Hence a split is not mathematically required when
the UCB coverage theorem is valid.

Here it is not valid for the advertised distribution class. The frozen UCB

```text
s*sqrt(7/chi2_.0125,7) = 2.290483*s
```

has simultaneous 95% coverage only under normal root summaries. A concrete
bounded mean-zero counterexample draws, with probability `.9`, uniformly from
`[-1/9-.01,-1/9+.01]` and, with probability `.1`, returns `1`. Its variance is
`.111141...>.09`. With probability `.9^8=.430467`, all eight DEV observations
come from the narrow component; then `s<=sqrt(8/7)*.01`, so the purported UCB
is below `.0245` and falsely certifies `.30`. Continuous narrow draws are
unique almost surely. The additional skew/outlier/Shapiro screens supply no
coverage theorem that reduces this `.430467` event to `.05`.

Therefore the present normal-theory variance screen plus the distribution-
robust Bennett test does not establish unconditional `.05` type-I control.
The available proof has no nontrivial bound on false launch outside normality.

## 3. Two exact dispositions

### A. Conditional normal-UCB compromise: split alpha

If the proposal explicitly assumes the chi-square DEV model, a conservative
governance split can set `alpha_V=.01` familywise and `alpha_C=.04`. The four
variance tails are then `.0025` each:

```text
SD_UCB_j = s_j*sqrt(7/chi2_.0025,7) = 2.968321*s_j,
SD_UCB_j<=.30 iff s_j<=.101067.
```

Using Bennett component size `.04`, the first root count whose four miss bounds
sum to at most `.20` is 74. The upward-rounded thresholds are

```text
(c1,c2,c3,c4)=(.098797,.102030,.092389,.102030).
```

Their size bounds are all below `.04`; their miss bounds are

```text
(.04782529,.05659975,.03388354,.05659975),
```

which sum to `.19490834`, giving joint power at least `.80509166`. This split
supports the crude union accounting `alpha_V+alpha_C=.05`, but only if the
normal-theory UCB coverage is accepted. Splitting alpha alone does not repair
nonnormal undercoverage.

The 74-root roster implies 67,192 rows, 1,480 H100-equivalent planning hours,
and 18.5 TB at the proposal's linear per-root rates.

### B. Recommended unconditional repair: remove variance certification

For an exact distribution-free result, discard the variance premise and use
only independent roots and the deterministic support ranges

```text
R_j=b_j-a_j=(1.75,2,1.275,2).
```

At component size `.05`, Hoeffding gives fixed thresholds

```text
c_j = R_j*sqrt(log(20)/(2n)).
```

At `n=538`, round upward to

```text
(c1,c2,c3,c4)=(.092339,.105530,.067276,.105530).
```

Every component-null size bound is below `.05`. At every
`theta_j>=.20`, the four miss bounds are

```text
(.01703604,.09065336,.00000863,.09065336),
```

whose sum is `.19835140`; arbitrary-dependence joint power is therefore at
least `.80164860`. At 537 roots the optimized miss sum is `.20031107`, giving
only `.79968893`, so 538 is the first integer certified by this exact
Hoeffding/IUT construction.

This rule covers all bounded distributions, atoms, skew, zero inflation,
failure mixtures, and within-root/cross-endpoint coupling. It needs no DEV
variance UCB or alpha allocation. The 538-root roster implies 488,504 rows,
10,760 H100-equivalent planning hours, 134.5 TB, and a `538/26=20.69230769`
multiplier. Resource infeasibility is an unambiguous
`STOP_CONFIRMATION_INFEASIBLE`, never cell pruning.

## Normative recommendation

> The 72-root Bennett/IUT thresholds are uniform over the complete component
> nulls and planning alternatives, but their guarantee is conditional on the
> true variance cap `Var(Pj)<=.09`. Do not describe the eight-root chi-square
> SD UCB as distribution-free certification of that cap. If exact normal-root
> UCB coverage is adopted, allocate `.01` familywise to variance certification
> and `.04` to Stage C, require all four `.0025`-tail SD UCBs to pass, and use
> 74 roots with thresholds `(.098797,.102030,.092389,.102030)`; otherwise stop.
> For unconditional distribution-free size and 80% joint power, delete the
> variance gate and use 538 independent roots with Hoeffding thresholds
> `(.092339,.105530,.067276,.105530)`, releasing the IUT claim only when all
> four root means meet their thresholds. Failure of the full roster/resource
> gate is `STOP_CONFIRMATION_INFEASIBLE`; no variance failure, root, or assigned
> observation is excluded.

