# SEQ-256 — additional trajectory targets fit TRAIN but do not improve PROBE

Both finite fits and fresh-process readouts completed. The declared engineering
target fails; this 400-update recipe is closed. Do not extend its dose or promote
its FULL adapter as the next successful adult actor.

Source `f325f9d3a91ea4f584b97ae17767bbfe1d575678`, prospectively declared at
`b74cb8c4`; node 2 GPU0/FULL guardian406618 and GPU1/LOSS_OFF guardian406619.
Both started September14 17:09:08UTC; completed17:27:30 and17:27:26UTC.
Root `/tmp/astra_goal_pair_train_20260914_attempt1`.

## Results

| Readout | FULL_TARGET | NEW_TRAJECTORY_LOSS_OFF | Unchanged37ec reference |
|---|---:|---:|---:|
| TRAIN goals | 8/8 | 3/8 | No unassisted TRAIN panel collected |
| TRAIN opposite-goal pairs | 4/4 | 0/4 | Not measured |
| PROBE goals | 5/8 | 5/8 | 5/8 |
| PROBE opposite-goal pairs (primary) | 2/4 | 2/4 | 2/4 |
| PROBE UNAVAILABLE goals / pairs | 0/8 / 0/4 | 0/8 / 0/4 | 0/8 / 0/4 |
| Old memory W0 | 16/16 | 13/16 | 16/16 |
| Old memory W8 | 16/16 | 14/16 | 16/16 |
| Held audit | 15/16 | 16/16 | 16/16 |
| Original taught graph, text | 2/4 | 2/4 | 3/4 |
| Earlier fresh graph, text | 3/4 | 2/4 | 3/4 |

The PROBE reference is the unchanged-child SEQ255 panel. Original memory/audit
and earlier graphs use the already bound prior reference receipts, not a new
contemporaneous no-write fit. Each PROBE world contributes1/2 pairs in all three
states. Correct cases remain A0/A2 and B0/B1/B3, but failure modes can change;
these are equal endpoints, not a claim that every output is unchanged.

FULL solves all eight TRAIN tasks without guidance after reload; control solves
A0/A1/B3, with no successful opposite-goal pair. The additional target gradients
therefore support acquisition on the taught instances under this recipe, not
held-out transfer. Both retain only tasks0/2 on the original taught graph, a
3/4→2/4 regression. FULL misses the >=3/4 PROBE-pair and >=3/4 taught-graph
requirements; control also misses memory and earlier-fresh-graph requirements.

On FULL PROBE-A, task1 takes the wrong first port to a wrong goal; task3 also
takes the wrong first port and later attempts an invalid route. B2 takes the
wrong first port. Control retains the same failed task identities with different
later failures. The goal-blind first-port reference solves no opposite-goal
pairs. Partial goal sensitivity existed before this fit; two-world teaching
has not made it more robust on the predeclared held instances.

## Matched treatment and limitations

Both start37ec, use the same270 rows, tokenized inputs, 400-update schedule,
freshAdamW3e-5, rank8 and frozen base. Only rows222–269 lose their labels in
LOSS_OFF; all12 original trajectory targets remain supervised in both.
Full-reference label denominator is shared, via active/reference scaling.

Training-row SHA256:
`4f3b8dfd989076a10df5442a35b1eb9003345aa8f2be647be787e70c6c4e0533`.
Reference-mask SHA256:
`8a708a4cd2dc8dddbea6d1c5397e2fff3d287c5ef7bd0794fc7c87ba22513dc3`.
Both match across arms. Actual/reference labels are33019/33019 FULL and
23885/33019 LOSS_OFF. There are800 new target presentations in FULL, zero
supervised new presentations in control. Identical input exposure does not mean
equal active-token budgets or equal achieved retention: the latter differs.

The old12 trajectory targets received only4 presentations each, versus16–17
for new targets. Both arms' original-graph regression motivates explicit legacy
trajectory rehearsal in a successor; it does not prove that rehearsal imbalance
caused the regression. TRAIN acquisition with unchanged PROBE motivates broader
actual experience, not additional updates on this closed recipe.

One exposed DEV lineage, one training seed, two held identifier instances of
one topology. No population efficacy, generic planning, H1/H2 or complete
developmental-flywheel claim. Independent raw-result review PASS:
`2026-09-14_goal_pair_incremental_fit_independent_result.md` reproduces both
fits' recorded masks/doses, all471 AFTER calls and64 episodes, primary ties,
TRAIN separation and exact retention failures. These are saved-file/state and
token-array joins, not independent tensor authentication or replication.
The sole FULL audit failure is true case10, `E_VEEAOY3IIH`: expected `NONE`,
emitted the event address. LOSS_OFF old-recall failures are W0 indices6/10/11
and W8 indices6/10, involving genuine field/identifier errors.

## States, cost and reproducibility

Saved/reloaded FULL state:
`fa3dec6dc3b10e11d888e7d5981b53a6eed677a603a480d0f7d234b37f36ea45`.
Saved/reloaded LOSS_OFF state:
`2a8076fb6445cb905c3a6bcfec116acd542f82ddc20aaad9ac607180f785bf80`.

FULL train837.661s + AFTER261.779s/239calls; control train837.942s +
AFTER257.382s/232calls. Summed native-phase cost2194.764s, approximately0.610
A40-hours across both GPUs. These include loading/checking, not just kernels.
No fits repeated, no source records recollected, no process killed.

Local capsule:
`gpu_artifacts_local/astra_goal_pair_train_terminal_20260914_attempt1/extracted`.
Complete terminal archive SHA256:
`2f3d604cb44972c93e1cbe7bf34cd73aab9cd82f6d5589bba0e495fead4c1db2`.
Native source, masks, dose/logs, saved adapters, raw calls, episodes, readouts
and launch completion records are preserved. Whole-root custody follows
completion; it did not delay training or evaluation.
