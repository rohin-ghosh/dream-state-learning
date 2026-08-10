# Report — Exp 1 CORRECTED (supersedes REPORT_exp0_exp1.md §3–6)

**Date:** 2026-08-10 · **Code:** `experiments/exp1_corrected.py` (30 seeds, budget-free AP + budget sweep, paired tests) · The original `exp1_value_vs_frequency.py` and its report are **kept in-repo as the flawed record**; an external adversarial code review (not prose review) refuted them. This corrects all five defects.

## The five defects (all confirmed, all fixed)

1. **Binary value magnitudes made the result closed-form.** With HIGH=1.0 > LOW=0.3 and `max` aggregation, "keep if ever tagged HIGH" is a label-threshold, not a ranking; the p_hit sweep reproduced a binomial, not a mechanism. **Fix:** continuous overlapping value ~ N(d′,1) vs N(0,1); sweep discriminability d′.
2. **p_hit=1.0 was a pure oracle** (label==label) and the headline gain was computed off it. **Fix:** d′=3 relabelled a CEILING, not the result.
3. **`dr_kept` was budget-fill**, not mechanism quality. **Fix:** primary metric is now **Average Precision (budget-free)**; budget reported as a sweep.
4. **The canary could not fail** (random never reads the label). **Fix:** the real canary is **d′=0** — value carries zero type information and must collapse to chance.
5. **Invalid significance test** (vs an unrelated mechanism's std). **Fix:** **paired per-seed** test (identical stream per seed).

## Results (Average Precision; structural=positive; chance ≈ 0.024)

| d′ | frequency | value_sum | value_max | value_mean | random |
|----|-----------|-----------|-----------|-----------|--------|
| 3.0 (ceiling) | 0.438 | 0.882 | 0.915 | 0.849 | 0.038 |
| **1.5** | 0.438 | 0.727 | 0.658 | **0.176** | 0.038 |
| 0.5 | 0.438 | 0.575 | 0.374 | 0.040 | 0.038 |
| **0.0 (canary)** | 0.438 | **0.137** | **0.204** | **0.024** | 0.038 |

Budget sweep @ d′=1.5 (structural retention): frequency 0.375→0.748 as budget 15→40; value_max 0.550→0.698. **Ordering FLIPS with budget** (value_max wins at 15, frequency wins at ≥25).

## What the correction reveals (this reverses the earlier claim)

1. **My earlier "value-weighting is CORE, oscillation resolved (+0.282, 6× noise)" is NOT supported under realistic overlapping value.** It was an artifact of binary magnitudes. Retract it.
2. **The canary now does real work and confirms the sharpest attack.** At d′=0 (no signal), `value_mean` → 0.024 = exact chance (clean, frequency-neutral), but **`value_max`=0.204 and `value_sum`=0.137 sit *above* chance with zero type information** — they are **frequency-contaminated** (max/sum of ~60 draws inflate frequent facts regardless of type). So the "max is load-bearing" result from the binary version was partly *frequency in disguise* — exactly the attack, now measured.
3. **No aggregation robustly beats frequency under moderate overlap.** At d′=1.5: `value_max` beats frequency on AP (+0.220, paired t≈14) but the win **flips with budget** and is partly contamination; `value_mean` (the only frequency-neutral aggregation) is **worse than frequency** (0.176 vs 0.438) because rare structural facts (1–2 samples) have noisy means. The metrics themselves disagree (AP vs retention@budget), so any "win" here is fragile.
4. **Clean separation needs a strong signal (d′≈3).** Only at the ceiling does a frequency-neutral aggregation (`value_mean`=0.849) decisively beat frequency.

## Honest standing of the thesis

The idealized experiments establish, defensibly, only this: **frequency/recency cannot exploit a value signal, and a value signal helps *only if it is both high-quality (d′≈3) and frequency-decorrelated*.** Hand-parameterized signals at realistic overlap do **not** beat frequency with a clean (non-contaminated) aggregation. This is a **negative-leaning necessary-condition result**, and it is more useful than the earlier false positive: it **quantifies the bar** any real value signal must clear.

## This is exactly why the value function must be TRAINED (Rohin's point)

The correction motivates the next experiment precisely. A hand-set signal fails; the mechanism only works with a value/reward signal that is (a) high-discriminability and (b) not a proxy for frequency. That is what a **value function trained on task outcomes** is for. Concrete path:
1. Generate high-quality synthetic data where episode outcomes (success/failure) are known by construction.
2. **Train** a value/reward model on those outcomes; **measure its realized d′ and its correlation with frequency** on held-out episodes — does it clear the bar this experiment set?
3. Only if it does: use it to weight consolidation into a **real parametric (ATLAS-style) memory**, and compare trained-value-weighted consolidation vs the ATLAS baseline, vs frequency, RAG, and LoRA-memory.

The idealized loop has done its job: it converted "value-weighting is core" from an assumption into a *testable requirement on a trained signal*, and killed the version of the claim that wasn't real.

## Methodological note

The original report was well-hedged, had a self-critique section, and still overstated — its self-critique missed the degenerate-oracle defect, the sharpest available attack. Lesson enforced going forward: **the critic must be a separate adversarial pass over the code and per-seed numbers, prompted to refute, not a narrative self-review.** Grading the prose grades the strongest part.
