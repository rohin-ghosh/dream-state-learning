# Lifetime statistics watcher audit

Date: 2026-09-12 UTC

Status: watcher-side statistical design audit only. This note changes no
builder source, experiment, adapter, job, claim authority, release, or
submission.

## Verdict

The proposed four-cell root block is the right causal design for a bounded
**parenting-by-promoted-SLEEP** claim. Its root-level contrast

```text
B_P = AUC(P-RUN) - AUC(P-FROZEN)
D   = B_P - [AUC(U-RUN) - AUC(U-FROZEN)]
```

does not treat branches, episodes, checkpoints, tasks, decodes, or adapters as
independent learners. Requiring both `B_P > 0` and `D > 0` also prevents an
interaction pass caused only by promoted SLEEP harming the matched-neutral
child. This estimates effect modification by the exact childhood treatment
over the registered finite horizon. It does not by itself estimate positive
late-life improvement, retention, or superiority to external text.

The L proposal is close but not yet a fully valid estimation plan. Five
repairs are needed before confirmation:

1. Different exam material at different cuts can make item/form difficulty
   look like absolute improvement. Use seven preconstructed source-disjoint
   parallel forms and rotate their cut assignment across root blocks with a
   frozen balanced schedule. Every branch within a root receives the same
   form at a cut. Form adjustment may be a sensitivity analysis; it cannot be
   learned from the treatment curve.
2. The primary lifetime clock must be exogenous exposure: scheduled
   information cohorts, episodes, or action opportunities. Accepted-write or
   qualified-update count is a post-treatment mediator and cannot align the
   primary cuts. It may be reported as a secondary dose axis.
3. "Old competence" needs two explicit root-level endpoints and margins:
   childhood-skill retention and early-deployment retention. The latter is
   uninterpretable unless the fixed early cohort first clears a frozen
   acquisition floor.
4. Launching `P-TEXT` only after inspecting the same roots' `P-RUN` factorial
   can preserve a predeclared fixed-sequence test, but ordinary post-gate
   effect estimates and confidence intervals are selection-conditioned, and
   the later launch is calendar/order-confounded. For clean estimation, run
   the presealed fifth branch concurrently on every confirmation root. The
   compute-saving alternative is a new independent baseline-confirmation
   cohort after the factorial passes, not reuse of selected `P-RUN` curves
   with ordinary intervals.
5. An "exact sign-flip/randomization" test is not exact merely because all
   cloned branches use a common tape and execution positions are randomized.
   With every factorial potential branch observed, a sign-flip test also
   assumes symmetry of root contrasts unless the allocation scheme creates a
   genuine random sign. Use the mean root-block contrast with a root-level
   Student interval as primary; call sign-flip/permutation a sensitivity
   unless its randomization basis is explicitly constructed.

## Smallest defensible structure

Use one excluded end-to-end canary, one source-disjoint DEV cohort, and one
fresh confirmation cohort. A root block—not a branch—is one learner
replication.

DEV should run the four factorial branches plus `P-TEXT`. It may select one
horizon from the sealed finite set, the anchor from a sealed early-cut set,
one exact qualified text configuration, form rotation, endpoint reliability,
and nuisance covariance. It may not select the largest treatment effect,
relax a margin, or contribute observations to confirmation. Eight DEV roots
can be retained as a fixed feasibility budget, but eight is not a statistical
minimum and its variance estimate is too uncertain to dictate a final N by
itself.

The statistically smallest confirmation is one fresh set of five-branch root
blocks:

```text
parented adult:        P-RUN, P-FROZEN, P-TEXT
matched-neutral adult: U-RUN, U-FROZEN
```

All descendants begin at their corresponding sealed, parent-deleted adult,
use the same arm-independent exogenous tape addresses and within-cut exam
form, and remain on the same node per block with randomized execution
positions. The parent policy is reset from one frozen snapshot for every
root; no cross-root adaptation is allowed. Sterile disposable exams never
feed any live branch. Failed writes, invalid actions, and missing scheduled
outputs remain adverse intention-to-treat observations under frozen rules.

This single cohort can support fixed-sequence claims without pretending its
within-root observations create extra N:

| Claim | Frozen root-level statistic | Release rule |
|---|---|---|
| `PERSIST` | `(P_ON-P_OFF)-(U_ON-U_OFF)` on fresh trigger and contraindication cases after deletion | lower confidence bound above its frozen margin; correct use and non-use both pass |
| `DEVxSLEEP` | `B_P` and `D` from entry-adjusted, time-normalized AUC over all seven cuts | intersection-union: lower bounds for both exceed zero or their prebound practical margins |
| Absolute late improvement | mean per-root `P-RUN` slope over anchor plus at least three later cuts; anchor-to-terminal gain | both lower bounds exceed their frozen positive margins |
| Text advantage | paired `P-RUN minus P-TEXT` late slope and terminal value | positive slope-advantage bound and terminal bound above the practical margin |
| Childhood retention | `P-RUN` terminal minus entry value on a fixed untouched childhood-skill panel | noninferiority lower bound above `-m_child` |
| Early-deployment retention | `P-RUN` terminal minus anchor value on a fixed early-information cohort, after identity-disjoint later writes | acquisition floor first; then noninferiority lower bound above `-m_early` |

`LATE` is the conjunction of absolute late improvement, both retention rules,
and both text-advantage rules. A positive AUC interaction alone remains only
`DEVxSLEEP`. A qualified `P-TEXT` need not be declared saturated to estimate
finite-horizon advantage. Drop the plateau sentence from the minimum design;
if retained, it needs its separate equivalence, headroom, novelty, retention,
and doubled-read-budget conjunction.

## Sample size without invented precision

No exact confirmation N is currently justified. The historical `0.027`
interaction SD came from four lives under a different estimator, and neither
it nor the proposed `{16,24,32}` grid is a dependable variance basis for all
of `D`, late slopes, terminal advantage, and retention. Repeated checkpoints
reduce the measurement error of each root summary; they do not increase N.

Before outcome-bearing DEV, freeze scientifically meaningful superiority and
noninferiority margins, alpha, desired power, root inclusion/failure rules,
an affordable maximum N, and an accrual batch size. Then use one of these
predeclared rules:

- choose total N from an upper confidence bound on DEV root-level nuisance
  variances/covariances; or
- preferably, use a blinded/mean-free internal-pilot re-estimation in fresh
  confirmation roots, retaining those roots and increasing only by frozen
  batches until the variance-based target is met or the resource cap is
  reached.

The sizing vector must contain the actual root summaries for `B_P`, `D`, late
gain/slope, paired text contrasts, and both retention changes. Size for the
intended conjunction (or for the most demanding component under a conservative
joint-power rule), not only for `D`. No effect mean, favorable direction,
checkpoint p-value, or interim text ranking may alter N. If precision required
by the frozen margins exceeds the cap, the affected confirmation is
`NOT_ESTABLISHED`, not a smaller-N headline.

Because each headline is an intersection-union claim, all of its constituent
one-sided tests may be run at the headline alpha without a compensatory win;
the design must nevertheless target adequate **joint** power. Separate claims
(`PERSIST`, `DEVxSLEEP`, and `LATE`) should use a frozen fixed sequence or an
explicit familywise allocation. Report the root count, full root endpoint
vector, covariance, all intervals, failures, and sensitivity analyses.

## Bottom line

The four-cell AUC interaction is valid for the narrow finite-horizon
parenting-by-SLEEP estimand once root-block inference is used. Increasing-
lifetime improvement requires a time-unconfounded absolute late contrast;
retention requires acquired fixed old cohorts and noninferiority margins; and
external-text advantage requires paired root-level slope and terminal
contrasts against one frozen native text system. One concurrent five-branch
confirmation cohort is the smallest clean design. Its N must follow observed
root-level nuisance precision under a sealed variance-only rule, never a
count of episodes or a guessed historical SD.

## Controlling design sources

- `research_notes/2026-09-12_end_to_end_goal_closure_synthesis.md`, especially
  L/B
- `research_notes/2026-09-12_lifetime_parenting_factorial_fresh_audit.md`
- `research_notes/2026-09-11_decisive_evidence_path.md`, especially Sections
  5--6
- `research_notes/2026-09-11_strong_evolving_active_text_baseline_cross_critique.md`
- `research_notes/2026-09-11_minimal_causal_parenting_h2_consensus.md`
- `research_notes/2026-09-11_current_evidence_paper_gate.md`
