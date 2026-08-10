# Exp 0 — Noise floor results (2026-08-10)

Run: `python3 experiments/exp0_noise_floor.py` (seeds=20, budget=50, 20 relations, 4 rel/ep, 4 detail/ep)

| N_ep | mech | struct_ret | detail_ret | diagonal |
|------|------|-----------|-----------|----------|
| 400 | truncation | 0.817 ± 0.053 | 0.021 | **0.796** |
| 400 | frequency  | 1.000 ± 0.000 | 0.019 | **0.981** |
| 400 | random (null) | 0.030 | 0.031 | **-0.001** |

(diagonal grows with N for both truncation & frequency; null stays ~0 at all N)

## Verdict — the gate did its job

- ✅ **Harness valid:** null/canary sits at diagonal ≈ 0.00 ± 0.04. Eval is not
  secretly biased toward "structure-preserving."
- ✅ **Noise floor small** (~0.04–0.09), effects detectable.
- ❌ **Task too easy / trivially baked in:** structural facts recur by
  construction, so *any* frequency- or recency-correlated rule wins. **Truncation
  (the dumb context baseline) already scores 0.80 diagonal.** Frequency's zero
  variance confirms the metric is deterministic in the task design.

**Conclusion:** "a diagonal exists" is not a result — the cheap baseline gets it.
The real bar is a regime where **truncation/frequency FAIL** and only a
value/structure-aware mechanism succeeds. This is exactly where value-weighting
must earn its place (resolves the earlier oscillation empirically).

## Task v2 design (makes it discriminating)

Introduce the two cases frequency cannot handle:
1. **Recurring-but-useless details** — a detail that appears often (high
   frequency) but is task-irrelevant. Frequency wrongly keeps it; value should
   drop it.
2. **Rare-but-critical structure** — a dependency that appears once but is
   essential. Frequency wrongly drops it; value should keep it.
3. **Downstream readout** — score memory by ability to answer a structural query
   (can you reconstruct the dependency needed to act?), not raw set-membership.

Prediction: in v2, truncation & frequency diagonals collapse; a value-weighted
rule (needs a reward/value signal) separates. If value-weighting does NOT beat
frequency even here → the "attention as capital" thesis is in trouble, and we
learn it cheaply. Either outcome is decision-grade.
