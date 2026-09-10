# One-parent v2 primary-power planning receipt v1 (superseded)

Date: 2026-09-07

Status: superseded by `20260907_one_parent_v2_power_receipt_v2.md` after the
feasible D bound and adverse-mixture repair. CPU-only planning evidence. This is not a confirmation reducer and
authorizes no architecture change, implementation, target generation,
model/tokenizer call, adapter operation, GPU use, or scientific claim.

## Frozen invocation candidate

```text
.venv/bin/python research_loop/advisory/one_parent_v2_power_sim.py --repetitions 300000
```

- source SHA-256:
  `2fa48c89f25ec001572acbc1c36a1acb39399fe49ab6c2f1fb5f8c3db45cc5bb`
- stdout SHA-256:
  `f51b30cc04e72f116b6d174757909c2cfda1e28c332f5a3ea3303ce511009836`
- Python: repository `.venv/bin/python` (system Python 3.9 symlink at this
  execution; exact executable/environment hash remains a later freeze field)
- NumPy: `2.0.2`
- RNG seed: `20260907`
- repetitions/family/cell: `300000`
- fixed root count: `N=32`
- primary-only joint rule: lower endpoint of the two-sided 95% Student-t
  interval above zero **and** observed mean at least `.05`
- design alternative: mean `D=.070`

## Result summary

At root SD `.10`, the estimated joint pass probabilities were:

| sensitivity family | pass probability |
|---|---:|
| normal | .8709 |
| standardized t5 | .8707 |
| standardized beta(2,5) | .8706 |
| standardized beta(5,2) | .8695 |
| standardized two-point, p=.20 | .9072 |

At mean zero and SD `.10`, the corresponding joint false-pass probabilities
were `.0014--.0059`. The joint rule is conservative because the observed
`.05` practical-margin condition is much stronger than merely rejecting zero
near the null.

At SD `.125`, outside the proposed `.10` design envelope, pass probability was
`.7972--.8131`. This is the declared precision boundary, not evidence for an
SD `.125` powered claim.

Only `D` is planned for this operating characteristic. Later fixed-sequence
rungs, the local-plateau composite, safety validity gates, and terminal
diagnostics are precision-gated and must not be described as 80%-powered.

## Limitations before binding

The simulated families are planning sensitivities, not an empirical model of
the future root distribution. Before confirmation, excluded development roots
must produce a one-sided 80% upper confidence bound on `SD(D)` no greater than
`.10`; otherwise the fixed-N study may proceed but must be called
precision-limited. The later source-bound statistics manifest must preserve
the exact reducer, feasible D range, executable/environment hashes, and
administrative-missingness blocking law.
