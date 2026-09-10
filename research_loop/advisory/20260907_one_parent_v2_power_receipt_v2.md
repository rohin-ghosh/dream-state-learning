# One-parent v2 primary planning-sensitivity receipt v2

Date: 2026-09-07

Status: CPU-only proposal evidence. This is not a confirmation reducer and
authorizes no architecture change, implementation, target generation,
model/tokenizer call, adapter operation, GPU use, or scientific claim.

## Invocation and receipt

```text
.venv/bin/python research_loop/advisory/one_parent_v2_power_sim.py --repetitions 300000
```

- source SHA-256:
  `dab12b1d278e18cb34f9964e5a10949afbf76eb765586d14e934fe6a1ce9c987`
- stdout SHA-256:
  `d8c172178540a73cc36be5ffa99a9e6a41c62b25c1cc991e792122f265bc18f2`
- Python `3.9.6`; NumPy `2.0.2`
- RNG seed `20260907`; `300000` repetitions/family/cell
- fixed `N=32`; feasible `D` range `[-5/3,5/3]`
- joint primary rule: two-sided 95% Student-t lower endpoint above zero and
  observed mean at least `.05`
- requested planning alternative: mean `.070`, pre-clipping SD `.10`

## Named-shape sensitivities

| distribution | joint pass probability |
|---|---:|
| normal | .8709 |
| standardized t5 | .8707 |
| standardized beta(2,5) | .8706 |
| standardized beta(5,2) | .8695 |
| mild two-point, p=.20 positive tail | .9072 |
| adverse two-point, p=.0136 negative tail | .6441 |

The adverse mixture is deliberately retained. It has the same requested mean
and SD but rare strongly negative roots; most N=32 samples never observe one,
while a sample that does can lose the t lower bound. Therefore mean and SD do
not define an 80%-power envelope for this joint small-sample rule.

At requested mean zero and pre-clipping SD `.10`, joint false-pass probability
was `.0000--.0059` over the same named families. This is not a universal type-I
bound; it is a planning sensitivity under those distributions.

## Allowed language

The design may report fixed-N operating-characteristic sensitivities under
these named assumptions. It may not say “at least 80% powered” for the primary,
the full five-rung hierarchy, the local-plateau composite, safety gates, or
terminal diagnostics. All future inferential results are fixed-N precision
estimates unless a later separately ratified empirical power model supports a
narrower statement.
