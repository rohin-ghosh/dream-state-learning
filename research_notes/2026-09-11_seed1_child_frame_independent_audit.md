# Seed-1 child-frame writer: independent audit

Date: 2026-09-11 PDT (artifacts completed 2026-09-12 UTC)

Status: exploratory mechanism scout. This is not a parenting, continual-
learning, retention, or whole-organism result.

## Bottom line

An independent recomputation from the nine raw evaluation JSONs reproduced
every pooled child-frame frame/abstention aggregate reported below (maximum
discrepancy below `9e-16`). All three child-frame variants strongly changed
the probability of the exact trained continuation and showed a monotone
exposure response, but all three failed the predeclared selectivity limit:
off-target spill was `0.282`--`0.423`, against a limit of `0.03`.

The admissible interpretation is therefore **frame habit, not selective
memory binding**. Variant `c` also learned a broad abstention habit rather
than calibrated uncertainty.

## Audited pooled results

| variant | frame P, OFF -> ON | owner-vs-lookalike I_d (95% CI) | spill | dose-shape | abstention |
|---|---:|---:|---:|---|---|
| `a` | 0.252 -> 0.822 | 2.281 [1.374, 3.303] | 0.423 | pass | fail |
| `b` | 0.252 -> 0.706 | 1.721 [1.185, 2.291] | 0.282 | pass | fail |
| `c` | 0.252 -> 0.813 | 2.910 [2.055, 3.810] | 0.359 | pass | fail |

For `c`, the ON probability of the abstention token was `0.538` on
unexposed owners, but also `0.354` on similar owners, `0.277` on bicycles,
and `0.266` on the exposed dose-16 owners. The negatives therefore induced
general hesitation rather than a selective unknown-state.

## Important boundaries

- The confidence intervals resample owners within completed fits. They do
  not include fitting-run variance, which the symmetric cross-node audit has
  already shown can be large.
- Variants `a`, `b`, and `c` each have one separately trained adapter per
  bank. All use fixed train seed 0; these are not independent stochastic
  replications. Their differences are descriptive, not causal.
- `c - b` does not isolate the negative rows because their positive child
  generations also differ.
- The trainer uses full-token loss. In `a`, the harness supplies the
  canonical endpoint. In `b` and `c`, the harness reconstructs or repairs it
  when the child omits it: 2,000/16,128 positive endings were missing in `b`,
  2,030/16,128 in `c`, and 413/768 negative endings were missing in `c`.
  Thus this does not show that child-authored prose itself created the
  binding.
- The assay measures an exact canonical-prefix continuation on seen owner
  identifiers. It does not demonstrate held-out free generation, connected
  memory, goal traversal, retention, or improved action.
- The report's `n_evals=13` is a count of scanned files, not thirteen
  replications; twelve F/a/b/c x three-bank evaluation cells are used.

## Decision consequence

Do not scale this recipe as the final writer. Keep the running seed-2 and
same-fit/changed-seed repetitions: they probe whether the apparent
cell-to-cell differences survive another fit or seed, but do not by
themselves estimate fitting variance. The next writer design must improve
conditional selectivity, not merely increase storage strength. The dormant
C11 guard is unrelated to this failure and remains reserved for the final
paper-grade C11 run.
