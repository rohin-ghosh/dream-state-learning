# Caption-judge failure: bounded source audit

September 17, 2026, 19:29 UTC. **Diagnostic only; not a launch/review gate.**
Ampere retains implementation/next-candidate ownership; Main relays this report.
Only source/tests and `FIRST_SCORING_REPORT_20260917.md` were inspected. No GPU,
provider, private-data/caption/label, locked-test, FINAL, or R176 contents read;
no model override, training changes, or coordination posts. This is a working-tree
audit, not verification of the private released-v6 source/checkpoint binding.

## Verdict and findings

**No deterministic label/gradient bug explaining constant humor predictions was
found. Prior-dominated fitting/selection is plausible, not established causation.**
Do not reopen the fixed first-scene-negative issue: reciprocal training and
balanced swaps are present (`gpu/ny_caption_judge.py:203`,
`gpu/ny_caption_judge.py:432`; regression tests at
`tests/test_ny_caption_judge.py:19`, `tests/test_ny_caption_judge.py:324`).

1. **The three-class objective and q wiring are internally consistent.** Counts
   are ordered not-funny/somewhat/funny, checked against votes and reconstructed
   mean (`gpu/ny_caption_data.py:195`). Smoothed targets and capped vote weights
   feed differentiable three-way log-softmax CE, backward, and AdamW updates
   (`gpu/ny_caption_judge.py:36`, `gpu/ny_caption_judge.py:563`,
   `gpu/ny_caption_judge.py:576`). q sums the last two probabilities
   (`gpu/ny_caption_judge.py:283`). Encoding forbids truncation rather than silently
   dropping content (`gpu/ny_caption_judge.py:546`). Actual smoothing/LR/weight
   distributions were not available in the permitted aggregate report.

2. **Very little distinct training exposure reaches the selected checkpoint.**
   The sampler takes equal-sized *mean-rating tertiles*, not three-class-balanced
   examples (`gpu/ny_caption_judge.py:69`), then draws contests/rows with replacement
   (`gpu/ny_caption_judge.py:569`). Equal tertiles do not rebalance positive-vote
   mass; mean = 1 + q + p(funny), so mean and q can even order captions differently.
   The permitted report gives 34,560 sampled rows / 180 contests, 32,000 draws /
   2,000 steps, and selection at step100 (`FIRST_SCORING_REPORT_20260917.md:17`,
   `FIRST_SCORING_REPORT_20260917.md:39`). Thus the selected model has only 1,600
   humor draws: expected **1,564 distinct rows**, versus **20,869** after all steps,
   approximately 0.15% / 2.00% of the 1,041,036 available rows. These are sampling
   expectations, not observed unique counts: N*[1-(1-1/N)^draws], N=34,560.
   Pooled soft log loss alone chooses checkpoints; recorded within-contest rank
   never enters selection (`gpu/ny_caption_judge.py:599`). A well-calibrated prior
   can beat a poorly calibrated ranking learner. This is an objective/coverage
   limitation, not proof that CE itself is incorrect or step2000 is deployable.

3. **Definite checkpoint coupling: scene-fit also rolls back to humor's best step.**
   Both models are saved only when humor log loss improves, then both reload from
   that directory (`gpu/ny_caption_judge.py:605`, `gpu/ny_caption_judge.py:615`).
   Under this code, best=100 means calibrated scene-fit is also step100, despite
   2,000 completed updates. The completed-step counters are truthful, but are not
   the selected heads' training ages (`gpu/ny_caption_judge.py:664`). Scene-fit
   has separate parameters/optimizer, so its repaired negatives cannot directly
   teach humor scene sensitivity. This coupling does **not** explain flat humor q.

4. **The published diagnostics do not establish near-constant predictions.**
   Low Spearman establishes weak ordering, not low prediction variance. Stress
   reporting averages *signed* q changes (`gpu/ny_caption_judge.py:645`,
   `gpu/ny_caption_judge.py:655`): +0.25 and -0.25 cancel despite large sensitivity.
   Low Brier/ECE likewise need a training-prior baseline. Have the owner expose
   aggregate within-contest q spread before/after temperature, mean absolute
   stress change, and baseline loss/Brier on model-selection only. Also distinguish
   failed learned ordering from an infeasible operating target using the threshold
   pool's oracle top-ceil(0.05*n) positive-mass mean; if that is below 0.30, no
   ranking can meet the stated coverage target. None of those values was inspected.

## Smallest targeted next objective ablation

Keep the existing weighted three-class soft CE, heads, canonical input, scene-fit
sampler, whole-contest partitions, q definition, calibration, and acceptance
standard. Replace independent humor rows with uniform **same-contest pairs**
(same row marginals; no new forwards), adding one modest, predeclared auxiliary:

`L = L_3class_CE + lambda * weighted_mean(((q_i-q_j)-(t_i-t_j))**2)`

Here q is the existing uncalibrated three-class positive probability sum, t is
the positive sum of the **same smoothed target**, and pair weight is the minimum
of the two existing vote weights. This directly trains within-scene differences
without hardening votes, changing class meanings, or assigning humor labels to
swapped captions; CE still anchors absolute probabilities. It is a hypothesis,
not a promised cure. Compare against lambda=0 using the same paired schedule,
seed, row pool and draw budget; leave broader row-coverage changes for a separate
ablation. Retain the declared model-selection rule rather than retroactively
choosing a rank-friendly checkpoint. Do not tune on the already reported audit;
any subsequent audit use is reuse, never a fresh test. Locked tests stay unopened.

Suggested owner-side synthetic checks: pair-row marginals and contest identity;
zero contrast loss at target predictions; nonzero/opposed per-example contrast
gradients at equal predictions with unequal targets; target-tie behavior; unchanged
q/calibration contracts. These are recommendations, not a new gate on Ampere.

## Verification and source anchors

Ran no full suite or model import. A bytecode-disabled stdlib-only check extracted
pure functions from the permitted judge source and passed target/weight checks,
mean-versus-q ordering counterexample, constant-prior Brier=0.00585 / q-ECE=0 /
undefined-rank example, absent-tau behavior, signed-change cancellation, and the
exposure calculation. All examples were invented, not dataset reads. Existing
tests cover arithmetic/ranking (`tests/test_ny_caption_judge.py:218`,
`tests/test_ny_caption_judge.py:275`) but do not demonstrate successful training.

SHA256 observed 19:28:53 UTC:
- `gpu/ny_caption_judge.py`: `1ee2e6092ef21b0e52b45a54f0d7589b28a5485783008c2a562722de04292599`
- `gpu/ny_caption_data.py`: `f9feb57ee6698d95fb1f88fcfe34104244ad1cfd85ca2db625cf403cfe7e184b`
- `FIRST_SCORING_REPORT_20260917.md`: `dd3d347367f8391303eda60266709e69cd2df782e61478440591638649581f49`

Files changed by this sidecar: **this new REPORT.md only**.
