# Result-blind analysis plan: mini-Sudoku optimizer-seed replications

Prospective audit written September 12, 2026 after reading the fixed
replication specification and local implementation, but without inspecting
either seed-1/seed-2 root, job state, or outcome. Seed 0 is the disclosed entry
result, not blinded evidence. This plan changes no experiment or builder code.

## Analysis population and eligibility

The learner, not an episode, is the replication unit. Analyze seeds 0, 1 and 2
as three independently initialized useful/corrupt fit pairs. A seed is complete
only when both fits and all four useful/corrupt x OFF/ON probe cells complete
with valid custody. Execution failure is `INCOMPLETE`, not 16 behavioral
failures and not replaceable by a new seed; retain it and do not use a partial
pair in the replication label.

Before opening generations or scores, verify for each included seed: fixed 32
training and 16 canary IDs; byte-identical useful and corrupt corpora across all
three seeds (SHA256 equal to seed 0); identical base hashes and declared
rank/LR/epoch/batch/token recipe; the requested optimizer seed in commands and
fit manifests; 96 finite steps, no dropped tokens, and the declared token
passes; adapter hashes in the probes joined to the corresponding fit; fresh
OFF and ON worker receipts; and identical episode order, generation seed/salt,
temperature, tick, wake/Scratchpad/token/max-length budgets, birth prompt and
Reasoning Gym version. Report any duplicate-OFF disagreement rather than
pooling it.

The current preparer and launcher enforce the seed/path binding and sequential
same-device execution. The existing per-seed reducer correctly joins by episode
ID and validates its listed paired fields, but there is no multi-seed reducer.
Also, cross-seed equality and some fixed probe fields (including total token
budget/max length) are not all checked by that reducer. Therefore the checks
above are mandatory analysis eligibility checks, not assumptions inferred from
a successful reduction.

## Exact endpoints

For seed `s`, material `m` in `{U=useful, C=corrupt}`, condition `c` in
`{ON, OFF}`, and each of the fixed 16 episodes, let `Y_smci=1` only when the
first recorded ACT has validated native measured score exactly 1.0. Missing,
invalid or unmeasured first ACTs are zero; a later solve never replaces the
first ACT. Define the cell count `S_smc=sum_i Y_smci` (0--16).

Report all four counts for every seed, followed by these prespecified
seed-level endpoints in solve-count units and rates obtained only by dividing
by 16:

- useful adapter gain: `G^U_s = S_s,U,ON - S_s,U,OFF`;
- corrupt adapter gain: `G^C_s = S_s,C,ON - S_s,C,OFF`;
- direct ON material contrast: `O_s = S_s,U,ON - S_s,C,ON`;
- OFF imbalance: `B_s = S_s,U,OFF - S_s,C,OFF`;
- **primary material-specific effect:** `D_s = G^U_s - G^C_s = O_s - B_s`.

Secondary diagnostics use the identical formulas on zero-filled first-ACT
native score. Native-best score and total ACT count are reported by cell and
seed only. Formatting/status counts are also diagnostic. None can rescue or
replace the exact-solve primary endpoint.

## Seed-level aggregation and decision rule

Display the complete seed table and the sign vector `(D_0,D_1,D_2)`. Across
the three learners report the unweighted arithmetic mean, median, and full
range of `G^U`, `G^C`, `O`, `B`, and `D`; separately display seeds 1--2 as the
same-device replication set and label seed 0's separate-device layout. Do not
pool 48 episodes, fit a binomial model, bootstrap episodes, or quote an
episode-level p-value/CI as uncertainty over learners. With only three fixed
seeds, the seed points and their range are the uncertainty description; no
population hypothesis test is claimed.

Call the effect **repeatable directional material transfer at this 16-board
resolution** only if each new seed `s in {1,2}` satisfies all three integer
conditions `G^U_s >= 1`, `O_s >= 1`, and `D_s >= 1`. This requires useful ON to
improve over its own OFF, beat corrupt ON, and retain at least one net solve
after the two OFF baselines are respected. One solve is the panel's smallest
nonzero resolution, so passing supports only a limited directional effect, not
a strong effect. Exactly one passing new seed is `mixed/not repeatable`; zero
passing new seeds is `not replicated`. A behaviorally incomplete new seed makes
the replication decision `indeterminate/no advancement`, not null. Secondary
metrics never change these labels.

## Limits and next decision

This is a three-seed descriptive screen of consecutive optimizer seeds for one
model, writer recipe and known development panel. The panel is not untouched;
four solution grids overlap training, although puzzle identities/givens do
not. Generation uses one fixed sampling seed. Seed 0 had different device
placement, and seeds 1--2 have fixed useful-first order, so hardware placement
is improved but time/order drift is not counterbalanced. The external-oracle
material does not establish parenting, clean lineage, retention, general
reasoning transfer, or a mechanism.

If the repeatability rule passes, the next action is only to preregister the
smallest source-linked child-material comparison; do not start a full parenting
campaign. If useful gains occur but `O` or `D` is mixed, first run a targeted
association-specificity/repeated-or-joint-write diagnostic. If useful gains do
not repeat, prioritize a targeted material/capacity/dose/interface check. An
incomplete pair is diagnosed and preserved before any new scientific decision;
this plan authorizes no replacement seed or paid allocation.
