> ⚠️ **SUPERSEDED (§3–6).** An adversarial code review refuted Exp 1's claims:
> binary value magnitudes made the sweep closed-form (a degenerate oracle), the
> canary could not fail, `dr_kept` was budget-fill, and the significance test was
> invalid. See `REPORT_exp1_corrected.md` — the corrected experiment REVERSES the
> "value-weighting is core" headline. Exp 0 (§2) stands. This file is kept as the
> flawed record for the honesty trail.

# Report — Exp 0 & Exp 1: Does value-weighted consolidation beat frequency where frequency must fail?

**Date:** 2026-08-10 · **Compute:** local, numpy-only, seconds · **Code:**
`experiments/exp0_noise_floor.py`, `experiments/exp1_value_vs_frequency.py` (reproducible, seeded)

---

## 1. What this solves (context)

The project ("Dream-State Learning") builds a memory that, during offline "sleep"
consolidation, keeps **relational structure** and sheds **episodic detail** — the
"Missing Diagonal" no released system implements. A central *open design question*
had been oscillating for several sessions: **is value/reward-weighting the CORE of
the mechanism, or a cosmetic side-lever on top of plain statistics (frequency,
recency)?** Committing cluster time or an ATLAS implementation before answering
this would be premature. These two experiments answer it at near-zero cost.

They also install the verification discipline needed for any later autonomous
loop: **oracle-by-construction, a measured noise floor, a null-mechanism canary,
and multi-seed statistics** — so results reflect truth, not plausibility.

## 2. Exp 0 — the noise-floor gate (and why it rejected the obvious task)

**Setup:** synthetic stream where structural facts recur and detail facts appear
once; fixed memory budget; mechanisms = truncation (context-at-budget),
frequency, random (null). 20 seeds, scales N∈{50,100,200,400}.

**Result (N=400):** frequency diagonal **0.981**, truncation **0.796**, null
**−0.001 ± 0.041**.

**Verdict — the gate did its job.** The canary is clean (null ≈ 0, so the eval is
not secretly biased). But the task is **non-discriminating**: even dumb
truncation gets a 0.80 diagonal, because structure recurs *by construction*, so
any frequency/recency-correlated rule wins for free. "A diagonal exists" is
therefore **not a result**. This was caught in ~10 seconds, before building any
mechanism. That is the gate paying for itself.

## 3. Exp 1 — a task where frequency PROVABLY fails

**Design (each choice defends against a specific way of fooling ourselves):**

- **Rare-but-critical structure (SR):** structural facts appearing once/twice.
  Frequency must wrongly drop them.
- **Recurring-but-useless detail (DR):** distractors appearing often. Frequency
  must wrongly keep them.
- **Downstream readout:** score = retention of *all* structural facts (SF∪SR) —
  a proxy for "can memory answer the query needed to act" — plus SR retention
  (hard case) and DR retention (distractor; lower is better).
- **Noisy, runtime-available value signal:** on each appearance a fact may be
  tagged; structural facts get a HIGH tag with prob `p_hit`, details a LOW tag
  with prob `p_fa=0.1`. `value_score = MAX tag` (dopaminergic one-shot imprint).
  **The mechanism never sees the ground-truth label — only the noisy tag.** We
  sweep `p_hit ∈ {1.0, 0.7, 0.4}` so there is no perfect oracle.
- **Ablation `value_sum`:** identical but accumulative (Σ tags). Tests whether
  "value" is just frequency in disguise.
- 20 seeds; budget=25; N=200; ~830 distinct facts.

**Results** (struct_all keep↑ | struct_rare keep↑ | dr_kept drop↓):

| p_hit | mech | struct_all | struct_rare | dr_kept↓ |
|------|------|-----------|-----------|----------|
| — | truncation | 0.307 ± 0.051 | 0.010 ± 0.030 | 0.665 |
| — | frequency  | 0.718 ± 0.043 | 0.435 ± 0.085 | **1.000** |
| 1.0 | value_sum (abl.) | 0.838 | 0.675 | 0.825 |
| 1.0 | **value (max)** | **1.000 ± 0.000** | **1.000 ± 0.000** | **0.415** |
| 0.7 | value (max) | 0.905 | 0.810 | 0.550 |
| 0.4 | value (max) | 0.760 | 0.520 | 0.770 |
| — | random (null) | 0.043 ± 0.048 | 0.025 | 0.020 |

Noise floor (null struct_all std) ≈ **0.048**.

## 4. What this proves (defensible claims)

1. **The task discriminates.** Both statistics-only baselines fail as designed:
   truncation drops 99% of rare structure (0.010); frequency drops 57% of rare
   structure and keeps **100%** of distractors. Neither is acceptable memory.
2. **Value-weighting is the load-bearing ingredient, not a side-lever.** Using
   only the noisy runtime signal, `value(max)` recovers **1.000** structural
   retention (incl. rare) and drops most distractors (0.415), a **+0.282**
   readout gain over frequency — **~6× the noise floor**. This empirically
   resolves the open question: **CORE, not cosmetic.**
3. **The mechanism is understood, not lucky.** The `value_sum` ablation
   (accumulative) underperforms `value(max)` markedly — struct_rare 0.675 vs
   1.000, dr_kept 0.825 vs 0.415 — because accumulation drifts back toward
   frequency (distractors rack up value over many weak hits). The **one-shot MAX
   imprint** — a single strong reward event burning in a rare fact — is what lets
   value beat frequency. This directly refutes "value is just frequency in
   disguise": the frequency-like value variant demonstrably loses.
4. **Graceful degradation with a measured breaking point.** value(max) stays
   above the noise floor at p_hit 1.0 (+0.282) and 0.7 (+0.187), but **falls to
   +0.042 (below 3× noise) at p_hit 0.4** — value-weighting is not magic; it
   requires a signal that fires on ≳50% of true structural appearances.
5. **Eval is trustworthy:** null canary shows no type preference
   (0.043/0.025/0.020, all ≈ budget/#facts), noise floor small and stable.

## 5. What this does NOT prove (honest limits — do not overclaim)

- **Idealized set-retention, not a parametric memory.** Retention here = "keep
  top-K distinct facts." A real ATLAS-style MLP memory is *lossy* — it superposes
  and interferes, and retrieval can fail. This experiment is therefore a
  **necessary-condition test**: had value-weighting *failed* even in this clean
  set model, the thesis would be dead. It succeeded → the thesis survives the
  cheapest possible test. It does **not** show the parametric version works;
  that is the next experiment.
- **The value signal is a noisy correlate of the label, by construction.** A fair
  objection: "you handed the mechanism a noisy version of the answer." True — but
  that is exactly what a reward signal *is* in RL. The contribution is not "a
  signal correlated with importance helps" (trivial); it is (a) the **noise
  tolerance / breaking point** (p_hit≈0.4), (b) the **aggregation dependence**
  (max ≫ sum), and (c) that value is **needed at all** in a regime where
  frequency/recency provably fail. We do not claim to conjure importance from
  nothing.
- **Synthetic, single generator.** "Structure vs detail" and the readout are
  defined by construction; one data generator; no real task execution, no LLM,
  no comparison to learned systems (Auto-Dreamer etc.). Those are later, larger
  tests.

## 6. Why this is good work

- It applied **scientific discipline before ambition**: measured the noise floor
  and ran a null canary *before* building any mechanism, then killed a
  non-discriminating task (Exp 0) in seconds rather than after a cluster run.
- It **resolved a real, blocking design question** (value: core or side?) with a
  cheap, decisive experiment, and **understood the mechanism** (max-vs-sum
  ablation) rather than reporting a bare win.
- It **states its own boundary** precisely (necessary-condition on an idealized
  model; signal is a noisy label; breaking point measured), which is what makes
  the positive claim credible.
- Total cost: seconds of local compute. This is the correct order of operations —
  cheap oracle tests gate expensive builds.

## 7. Next step

Replace idealized set-retention with a **real parametric memory** (small
ATLAS-style fast-weight MLP; write = value-scaled gradient imprint, read =
forward-pass probe) and test whether the value advantage *survives lossy
consolidation and interference*. Same oracle/noise-floor/canary discipline; same
p_hit sweep. If the +0.28 readout gain persists under real interference, the
necessary condition becomes sufficient and we have the paper's core result.
