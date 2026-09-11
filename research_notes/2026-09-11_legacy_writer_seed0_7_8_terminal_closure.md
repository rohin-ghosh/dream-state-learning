# Legacy writer pretest: seed0/7/8 terminal closure

**Status:** bounded scout closure; all requested seed7/8 cells terminated normally.  
**Decision:** no legacy adapter recipe advances as the behaviour-block writer.
`A` remains useful only as a routine-rehearsal positive control; the
horizon-matched text brief remains the operational comparator/fallback.

## Terminal and receipt check

On `ipp2-ovx-p2-08`, both `R2_B_seed7` and `R2_B_seed8` ended with no live
controller or train/probe child. Each has 18/18 probe JSONs, 36 replicate
ledgers, 30 timing receipts with `rc=0`, and 29 durable step markers. The
completed probe cells are `A`, `A_v3`, `B`, `C`, `Bs`, `B_match`, `C_tmem`,
`OFF`, and `brief_mid`, each on report and disjoint panels; both summaries and
tables exist. `summarize` has a successful timing receipt but intentionally no
lasting marker. No restart, collision, or failure was observed.

The lives are distinct data replications, not optimizer-seed replications:
their source ledger and sleep-512 corpus hashes differ, while all v3 cells use
trainer seed 0 and `A` uses the unseeded v1 trainer. Recomputed source-input
hashes matched the compile manifests. The shared disjoint panel hash is
`24ecfe874fafb216d7b8073322b61dda53497da5080751131112b0845884003a`.

## Efficacy matrix

`R / D` means report-panel / disjoint-panel. Every entry is the absolute
two-replicate mean followed by its recomputed delta from the **same-life OFF**.
The matched comparison for an adapter written at episode 512 is `brief_mid`;
the final brief is shown only as a descriptive, exposure-mismatched reference.

| Cell | seed0 R / D (delta OFF) | seed7 R / D (delta OFF) | seed8 R / D (delta OFF) |
|---|---|---|---|
| OFF | .4845 / .2487 | .4893 / .2571 | .4852 / .2519 |
| brief_mid | .4952 / .2731 (+.0107 / +.0244) | .5293 / .2463 (+.0400 / -.0108) | .4956 / .2553 (+.0104 / +.0033) |
| final brief | .5291 / .2731 (+.0446 / +.0244) | .4884 / .2481 (-.0009 / -.0091) | .5033 / .2649 (+.0181 / +.0129) |
| A | .5293 / .2731 (+.0448 / +.0244) | .5293 / .2707 (+.0400 / +.0135) | .5163 / .2624 (+.0311 / +.0105) |
| A_v3 | .4896 / .2557 (+.0051 / +.0070) | .5264 / .2694 (+.0371 / +.0122) | .5037 / .2514 (+.0185 / -.0006) |
| B | .4817 / .2731 (-.0028 / +.0244) | .4542 / .1747 (-.0352 / -.0824) | .4999 / .2592 (+.0147 / +.0073) |
| Bs | .4878 / .2499 (+.0033 / +.0012) | .4889 / .2495 (-.0005 / -.0076) | .4878 / .2495 (+.0026 / -.0025) |
| B_match | .4813 / .2130 (-.0032 / -.0357) | .5278 / .2628 (+.0384 / +.0057) | .4624 / .2596 (-.0228 / +.0076) |
| C | .0000 / .0000 (-.4845 / -.2487) | .0000 / .0000 (-.4893 / -.2571) | .0000 / .0000 (-.4852 / -.2519) |
| C_tmem | .3098 / .1992 (-.1747 / -.0495) | .1650 / .0970 (-.3244 / -.1602) | .3809 / .2499 (-.1043 / -.0020) |

Against `brief_mid`, `A` differs by +.0341 / .0000 (seed0), approximately
.0000 / +.0244 (seed7), and +.0207 / +.0071 (seed8). No other adapter is
consistently competitive with that brief: `A_v3` is -.0056 / -.0174,
-.0029 / +.0231, and +.0081 / -.0039; `B` is -.0135 / .0000,
-.0752 / -.0716, and +.0043 / +.0039. The other B-family cells are small and
sign-inconsistent or have a severe negative replicate. Thus `A` is the only
consistent score carrier, but what it carries is the fixed routine.

Cross-life mean deltas from OFF are: `A` +.0386 / +.0161; `A_v3`
+.0202 / +.0062; `B` -.0078 / -.0169; `Bs` +.0018 / -.0030; `B_match`
+.0041 / -.0075; `C` -.4863 / -.2526; and `C_tmem` -.2011 / -.0706.
These are descriptive means over three lives, not inferential estimates.

## Consistency, action interface, and replicate variance

- `A` is positive on both panels in all three lives and has no flagged
  collapsed replicate. The report result is the six-pass routine in seed0 and
  seed7; action concentration remains high in seed7/8 (report/disjoint recipe
  shares .750/.917 and .688/.834). In seed8, the permissive episode-level
  `^ACT:\s*(.+)$` helper found at least one matching line in every episode of
  both reps. This is not strict exact-line action validation and must not be
  promoted to program-dependent choice.
- `A_v3` varies strongly across lives: near OFF in seed0, routine-like in
  seed7, and a small seen-only gain in seed8. `A` versus `A_v3` is not a clean
  masking contrast: with no context, all A_v3 string tokens are targets, and
  the recipes also change epochs, trainer geometry, seeding, and sequence
  handling.
- Full `B` has the largest instability: seed7's report reps are .5285/.3798
  and disjoint reps .1372/.2123. `B_match` reverses sign by life and has a
  seed8 report split of .5040/.4209. `Bs` stays close to OFF but never supplies
  the registered unseen gain. Matching target-token budget or dropping local
  views therefore does not rescue a repeatable writer.
- `C` scores exactly zero on both panels in every life and has zero recipe,
  note, and recall metrics. Its extracted answer targets never begin with the
  child's native `ACT:` or `PREDICT:` interface, so this is a failure of this
  narrow QA/rendering recipe, not evidence against all QA memories.
  `C_tmem` preserves some heuristic action/recipe behavior but is harmful in
  all three lives and highly variable within lives. The TMEM-shaped LoRA does
  not rescue the interface-mismatched corpus.
- Strict action-line validity was not computed for seed7/8 beyond the weak
  helper and the collapse indicators. The ritual fields describe output
  concentration; they are not action-validity or conditional-choice tests.

## Masking, target purity, and packing

The v3 manifests report no dropped target/context tokens, no targetless
examples, and no non-finite training events. B-family contexts contain masked
GOAL/harness material and the audits found no parent-marker target or leak hit.
However, child-authored harness-shaped echo mass in full B targets is 35.0%
(seed0), 48.6% (seed7), and 54.6% (seed8). Local context is also truncated for
5,596/6,780, 5,194/6,584, and 5,329/6,788 child rows respectively. “Child
target only” therefore does not establish clean semantic memory or exact
current-state conditioning.

Every requested packed v3 cell (`A_v3`, `B`, `C`, `Bs`, `B_match`) returned
`NOT_ISOLATED` on the attempted block-mask self-test and safely trained through
`fallback_one_item_per_sequence`. `C_tmem` was explicitly unpacked. This rules
out cross-item attention leakage in the actual runs, but it does **not**
validate the intended packed-neighbourhood implementation or measure a packing
effect.

## Registered decision and causal bound

The predeclared V6 rule requires a canary-passing, non-routine cell at least
+.015 above same-life OFF on the disjoint panel in at least two of three lives.
No cell qualifies:

- `A` crosses +.015 only in seed0 and is the known routine, so it is
  disqualified even apart from the count.
- `A_v3`, `Bs`, and `B_match` cross in zero lives.
- `B` crosses only in seed0, where its .2731 output is the routine; it is
  catastrophic in seed7.
- `C` destroys the interface and `C_tmem` is harmful.

Therefore the registered outcome is **target-only multi-scale: no lock-in**.
Stop the legacy `B`/`Bs`/`B_match` branch as a behaviour-block candidate and
retire `C`/`C_tmem` in their present answer-rendering forms. Do not continue
`A` as a memory mechanism: retain it only as a routine-positive control.
Further work, if wanted, should be a newly controlled, unpacked,
interface-canary-checked rendering isolation—not another legacy-recipe life.
This ruling does not stop the separately authorized mechanism/parenting runs
and does not activate C11.

## Integrity caveats

The raw probe means and per-rep ledgers are unaffected by the following
reporting issue, and recomputing same-life deltas does not change the stop
decision. The node used the older `write_ab_report.py` hash
`a36bd604...4853` rather than the repaired local `c1d07ef...f36c`. Its legacy
`A` token-pass field is wrong by about 3x, and its collapsed-rep flag compares
to the panel OFF mean rather than paired replicate-index OFF. Those formatted
fields are non-authoritative here. This also explains why older prose called
seed0 `A_v3` disjoint “-.002”: .2557 minus this run's .2487 OFF is **+.0070**;
-.002 borrowed the historical .2574 reference.

The seed0 copied summary/table is a partial post-probe resummarization, so its
earlier `A`/`A_v3`/`B` cells were taken from their recorded absolute probe
means rather than treated as absent. Finally, adapters and launch-source bytes
were not sealed into a complete immutable receipt chain. Current source hashes
match the audited launch-era files and predate the runs, but this remains a
scout-grade descriptive closure, not a paper-grade certified result.

Evidence: local terminal bundles under
`gpu_artifacts_local/write_pretest_terminal/seed{0,7,8}/`, the causal audit in
`research_notes/2026-09-11_write_pretest_causal_audit.md`, and the registered
rule in `research_notes/NEXT_EXPERIMENT_DESIGN_v3_BLEND.md`.
