# Final audit: EVENT-retention-v2 attempt-5 launch gate

Date: 2026-09-13 PT  
Auditor: independent Codex subagent (`warmfix_followup_audit`)  
Audited commits: `cd2b8cea71a42d2af88d145b1d7a9095a7bd5a82` and
`6caffa15e5fb14293b01727e3b0e5b0dc5486799`  
Prior audit: `4daee9fb`  
I launched no model or GPU work.

## Verdict

**The exact attempt-5 protocol bound by `6caffa15` passes its prospective
launch gate: GO.** Warmfix4 preserves actual-destination freshness, the
reducer is committed and terminally tested, the three manifests bind fresh
four-arm runs from the original measured A200 parents, and failed attempts are
accounted without recovery or reuse.

However, the builder launched all three attempt-5 runs before this audit was
finished. During this audit seed 0 subsequently stopped after its valid B200
fit, at the next readout's preworker CVD check. Therefore the current runtime
verdict is:

- seed 1/2 attempt 5: **GO to continue under their already bound manifests**;
- seed 0 attempt 5: **terminal NO-GO/no resume/no reuse**;
- any seed-0 attempt 6: **NO-GO** until the new stopped-readout ancestry and
  physical cost are added to the operator/reducer, committed, tested, and
  audited.

The early launch violated requested audit sequencing. It did not change the
protocol bytes or make attempts 2/3/4 eligible.

## Committed source and terminal-test binding

`warmfix4_tested_source.sha256` exactly matches the committed objects:

- fit: `563354304444b306b7d1ba210c3dce42a4d9e6c1b1322f239e5256341210c45f`
- outer: `c9f01d41872fc3a890826eff1a5367c847c8e93d02be9d0fa274feb19424f319`
- follow-up operator:
  `ca82b3b2d13023d67b1a3c3e33d4ed951dbb86ff07b271cd710ef8486c1ba849`
- warm overlay:
  `7c69c44bf9253a536ceec9ebe5b081e38dd7e4d421a48563797fccd463ecfaaa`
- reducer:
  `07ad455b2dfe58319865ab6b7b8256e5d68ecbac8772cc78682043c5708803b3`
- reducer tests:
  `37b1638380f3b916f6b1afef3cb405ca68a9eec5c55e2268ab82a6069c9ec442`

There is no fit/outer/operator/overlay delta from the already-audited
`cd2b8cea` boundary. The committed terminal log
(`9d2844faa387f2fffb8e3e73871c964dc6479cd45701d14156100a24d6c8fdfc`)
records all 12 reducer tests passing in 532.070 seconds. The source-hash file is
`b5ece69dd0e109b713bcc515243e4357fcd27aa6a417cb29a0501cbc1779ed31`.
The tests cover raw-response recomputation, missing/corrupt files, wrong
parents/seeds/phases, warm receipts, source overlays, release evidence,
three-seed/same-bank reduction, attempts 2/3/4 ancestry, exact failed work,
and rejection of failed-outer recovery.

## Preflight and lineage

The committed preflight is
`2ce08417f74332fc52d08635c5a301a92209a8bd50a816c9ced9e5f1b77b19cd`.
Direct node-2 hashing matched all three manifest pins:

- seed 0: `c6e3ddf3d46194a59be7ac1c61e3bacfeecbf23171b3d8873dd0c7f38906b6e4`
- seed 1: `642d3c351b9c6347ebc470bb5733fdf6c28a8a13cff7adf941536a77702f4221`
- seed 2: `d27aa6110c17cf47a50cae561f67d5a14e5c3e3d16fd1e066287666290b3a48f`

The node-side operator is byte-identical to the committed operator. The
warmfix4 receipt is pinned at
`c79dff53330905c553a6ca0e276888055f5fc270d4c1124e5fe507f9c75213e4`.
Before launch, the receipt recorded four of four fit inputs passing for every
seed, material identity unchanged, and all failed checkpoints ineligible.

All three warm arms name the acquisition validator's exact measured A200
completion. `CLEAN_CUM600` alone starts cold. The operator revalidates the
acquisition receipt and predecessor on every stage and refuses an already
started root, any existing fit/readout stage root, or a nested/overlapping
failed root. The reducer independently reconstructs the acquisition and again
joins each warm completion to that measured A200 receipt.

## Fixed topology and arithmetic

Per successful seed the fixed follow-up remains:

| arm | parent | new updates | new presentations | readout calls |
|---|---|---:|---:|---:|
| `B200_NEW_DOSE` | measured A200 | 200 | 800 B | 16 |
| `B400_FIXED_WORK` | measured A200 | 400 | 1,600 B | 16 |
| `REPLAY400` | measured A200 | 400 | 1,600 mixed A/B | 16 |
| `CLEAN_CUM600` | clean C0 | 600 | 2,400 cumulative A/B | 16 |

Including acquisition, a clean completed seed contains 5 fits, 1,800 updates,
7,200 presentations, and 96 readout calls.

The committed attempt-5 plans preserve the exact prior chain:

- attempt 2: preworker failure, zero fit/update/presentation/readout work;
- attempt 3: one completed physical B200 fit per seed, rejected after the
  exact PEFT namespace validation failure;
- attempt 4: seed 0 only, one completed physical B200 fit rejected by the
  exact post-fit freshness-checker impurity.

Thus the planned all-in totals after a successful attempt 5 were:

- seed 0: 7 fits / 2,200 updates / 8,800 presentations / 96 calls;
- seeds 1 and 2: 6 / 2,000 / 8,000 / 96 each;
- all seeds: **19 fits / 6,200 updates / 24,800 presentations / 288 calls**.

The reducer recursively pins each stopped manifest/collection/input/stage,
requires the exact error and released-worker state, requires no failed-attempt
readout, and marks every partial checkpoint ineligible. It rejects any
`recovered_b200`, recovery elapsed time, recovery marker, or failed collection
as a completed fit.

## Tensor and raw-evidence checks

The reducer uses the same narrow PEFT canonicalization as the repaired writer:
remove only `base_model.model.` and normalize `.default.weight`. It rejects
collisions on both sides before requiring exact source/trainable coverage. It
then requires complete initialized coverage, tensor SHA-256 values, shapes,
dtypes, same-dtype equality, and exact sparse conversion keys. Parent files
before/after must match the immutable measured checkpoint.

Every successful fit/readout branch must have a completed, released outer;
exact phase order is four fit/readout pairs. The reducer reopens all raw actor
captures, reconstructs requests/routes, token counts, stop reasons, scores,
panels, adapter mount bytes, and custody/release records. Final pooling requires
seeds 0/1/2 on the same single exposed DEV bank and remains descriptive only.

## Runtime event discovered during the audit

The builder recorded launches at approximately 20:17Z, before this verdict.
Direct node-2 inspection found:

- all three B200 fits completed with return code 0, sealed completion, clean
  release, and the repaired warm validator;
- seeds 1 and 2 then completed B200 readout;
- seed 0's B200 readout spawned no worker and stopped because `pre_cvd` could
  not read `/proc/258553/environ`; its collection is `FAILED`, return code is
  null, and `completed_sha256` is null.

Seed 0's B200 fit is not reusable because the fixed operator forbids resume
and automatic retry. A later fresh attempt 6 would need to charge that extra
fit and model a new failure shape: completed B200 fit followed by preworker
B200-readout failure. If seeds 1/2 finish attempt 5 and seed 0 later reruns the
full four arms, the all-in cap becomes **20 fits / 6,400 updates / 25,600
presentations / 288 calls**: seed 0 contributes 8 / 2,400 / 9,600 / 96, and
seeds 1/2 each 6 / 2,000 / 8,000 / 96. The current reducer intentionally does
not admit that new topology, so attempt 6 requires a prospective revision.
