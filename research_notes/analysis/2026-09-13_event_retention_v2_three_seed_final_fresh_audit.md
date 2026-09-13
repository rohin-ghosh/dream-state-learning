# EVENT-retention-v2 three-seed final: fresh evidence audit

**Date:** 2026-09-13 PT  
**Scope:** read-only review of the preserved native reduction and archives. I
did not run a model, tokenizer, fit, or GPU job and did not edit experiment
code or evidence.

## Verdict

**GO — accept this as bounded replay-retention evidence on the one exposed DEV
assay.** It is not confirmation or a general replay result.

The strongest defensible statement is:

> On one exposed, format-assisted eight-EVENT DEV bank, after A200 made the
> four A records exactly cold-readable, the fixed warm `REPLAY400` second write
> left all four old A and all four new B records exactly readable at W8 (and
> W0) for learner seeds 0, 1, and 2. Both B-only second writes acquired B 4/4
> but left A 0/4: this held both at the same B dose (`B200_NEW_DOSE`) and at the
> same update/presentation work (`B400_FIXED_WORK`). Matched clean-cumulative
> training also read 8/8.

Thus **replay retention is established for this fixed, bounded, same-bank DEV
mechanism assay**: the schedule containing explicit old-item rehearsal
preserved exact access to A across a later B write where both schedules without
A rehearsal forgot it. This is a descriptive within-bank contrast, not a
population estimate or a pure causal replay effect.

## Artifacts, roots, and implementation identity

The helper files match the supplied hashes:

- final reduction file:
  `49dad92b29779ccbcd346deba243ab81e38e34d1288f67936050c0f752a5ee1f`;
- recomputed embedded canonical receipt seal:
  `901b063f0d1cfd279f42f0e3b86e679599377c8496016c576f3e2385dd0a463d`;
- 1,995,735,040-byte, 3,336-member evidence tar:
  `e0492b7ec5c5034490ee19c848a36b40884a780d4675ffd4749cca407b7f7438`.

The tar's reduction member is byte-identical to the standalone reduction. The
three per-seed canonical seals also recompute. Exact eligible roots are:

| learner | root | manifest SHA-256 | completion SHA-256 | terminal status |
|---:|---|---|---|---|
| 0 | `pcfl_sequence_v2_followup_seed0_20260913_attempt6` | `a1d541f2c9d9f7ed5416700885f790b3d7e2a91d4990bc7788d1c8a7ee26f211` | `e974a06bab83a294b47b78f078f117b6a514a9fa12309327429492b4ef209658` | `CAPTURED_NOT_PROMOTED`, 8/8 ordered stages |
| 1 | `pcfl_sequence_v2_followup_seed1_20260913_attempt5` | `642d3c351b9c6347ebc470bb5733fdf6c28a8a13cff7adf941536a77702f4221` | `e4295f759d87853be141b91b8e8e96bdb3fe5076ce502d45b9f00c551cedc6fa` | same |
| 2 | `pcfl_sequence_v2_followup_seed2_20260913_attempt5` | `d27aa6110c17cf47a50cae561f67d5a14e5c3e3d16fd1e066287666290b3a48f` | `95b727b93d3d280201f127b7b7ddd6a6eea505e20860d4915aa331f9fb8c89ee` | same |

All 15 eligible fit collections and all 18 readout collections are complete
and GPU-released. `full_contract_released=false` and
`automatic_promotion=false` are intentional claim/lineage fields; they do not
mean a recorded worker remained alive.

The final reducer and operator bytes are exactly commit
`3f4c03bc80298d5fd1062db49fbe26174fdc1b34`:

- reducer `afee815b34ea30bbd156491055cc2fac95047360404f0edbfaa2df7335688dfd`;
- operator `bc4125bbc982be155623c0c96792a3386f41a91ace76c4eebc1f64ff178108ae`;
- reducer test `4fe111768a56fb7d9df4eb8f4e2eaf27303c033cad7df9b1cb1136901cf09cc1`.

The native warm repair is commit `cd2b8cea71a42d2af88d145b1d7a9095a7bd5a82`:
fit `563354304444b306b7d1ba210c3dce42a4d9e6c1b1322f239e5256341210c45f`,
outer `c9f01d41872fc3a890826eff1a5367c847c8e93d02be9d0fa274feb19424f319`.
All 14 unique
fit/readout runtime source pins match bytes in the final archive, and the
source sets are identical across learners. The reducer interface requires a
file-pinned request, exactly seeds 0/1/2, one common bank/model, the four
ordered branches, raw captures, same-seed A200 parents, immutable checkpoints,
release, no manual continuation/recovery, all failure ancestry, and the fixed
physical cap. It never promotes automatically.

Recorded tests are 61/61 operator tests, the prior 12/12 full reducer suite,
and 3/3 focused tests on the exact final reducer bytes (failure ancestry,
readout-preworker exclusion, and full raw vectors/contrasts). I independently
recomputed the final receipt/seeds, cell totals, raw exact-stop decisions,
paired deltas, work totals, and corpus counts rather than relying on those test
claims.

## Exact observations

Every row below occurred independently for **each** learner seed. W0 and W8
were identical:

| state | W0 A | W0 B | W8 A | W8 B |
|---|---:|---:|---:|---:|
| `NO_WRITE` | 0/4 | 0/4 | 0/4 | 0/4 |
| `A200` | 4/4 | 0/4 | 4/4 | 0/4 |
| `B200_NEW_DOSE` | 0/4 | 4/4 | 0/4 | 4/4 |
| `B400_FIXED_WORK` | 0/4 | 4/4 | 0/4 | 4/4 |
| `REPLAY400` | 4/4 | 4/4 | 4/4 | 4/4 |
| `CLEAN_CUM600` | 4/4 | 4/4 | 4/4 | 4/4 |

Independent hashing of every embedded raw string against its target hash,
conjoined with stop termination, reproduced all 288 decisions: 168 exact and
120 non-exact. All **288/288** calls ended with `finish_reason=stop`; there
were **zero length stops and zero truncations**.

At both W0 and W8, replay minus either B-only control is A `+4/4` within every
learner and `+12/12` when the four repeated records are concatenated across
the three learners; B is `0/12` because both sides are 4/4. Replay minus clean
cumulative is 0 for both banks. The `12` denominator is four unique records
under three optimizer/dropout seeds, not twelve independent facts.

Direct archive recomputation confirmed per learner:

- B200: 200 updates, 800 B presentations (200 per B record);
- B400: 400 updates, 1,600 B presentations (400 per B record);
- replay: 400 updates, 800 A + 800 B (200 per record);
- clean cumulative: 600 updates, 1,600 A + 800 B (A 400, B 200);
- every fit had zero skipped targets, training truncations, target-token drops,
  and nonfinite batches;
- every clean-cumulative item list is exactly its same-seed
  `A200 corpus + REPLAY400 corpus`.

All nine warm branches initialize 392/392 LoRA tensors exactly from their
same-seed immutable A200 checkpoint, leave the parent files unchanged, and use
one adapter with a fresh AdamW optimizer having zero restored/initial entries.
This tests LoRA-weight continuity across a discrete write, not optimizer-state
continuation.

## Failure and total-work accounting

Eligible work is 15 fits / 5,400 updates / 21,600 presentations / 288 readout
calls. Excluded physical work is retained as 5 fits / 1,000 updates / 4,000
presentations / 0 calls:

- attempt 2: three preworker CVD stops, zero fit work;
- attempt 3: one failed 200-update B200 fit per seed (three fits);
- attempt 4 seed 0: one completed worker rejected by the impure collector;
- attempt 5 seed 0: one valid B200 fit followed by a preworker readout stop;
  its checkpoint was excluded and no manual continuation was admitted.

Total physical accounting is therefore exactly **20 fits / 6,400 updates /
25,600 presentations / 288 calls**, with 6,212.651 aggregate outer seconds.
No failed fit or readout was silently converted into a primary observation.

## Dependence, custody, and claim boundary

All learners share import
`cc9e97a290933633d67c371625ae5cfffeb46bc8ca7c130279022868e98a545e`,
record digest
`932edc58c15f330420807c648b07b2adcd53938fd430f6b4907da248502e3678`,
roster `7b9e4ada8469ccfd307ed454fd5afdfa131a2da99097fc397944067a556b6afe`,
and pinned Qwen2.5-7B-Instruct revision
`a09a35458c702b33eeacc393d103063234e8bc28`. The seed-specific spec seals
differ because the learner seed is part of each spec, but the
bank/model/runtime identities are otherwise one set. W8 is a previously
exposed DEV paraphrase over the same addresses and targets; W0/W8 are repeat
surfaces, not independent panels.

The final tar is **not standalone**: its absolute pins reach the earlier A200
acquisition and failure roots. Reproduction/audit therefore requires this
exact five-archive set, separately retained on the helper:

- final three-seed archive
  `gpu_artifacts_local/pcfl_v2_final_three_seed_20260913_attempt1/evidence.tar`,
  SHA-256
  `e0492b7ec5c5034490ee19c848a36b40884a780d4675ffd4749cca407b7f7438`;
- acquisition archive
  `gpu_artifacts_local/pcfl_v2_acquisition_20260913_attempt1/evidence.tar`,
  SHA-256
  `fdc22c730206c5c9e6486099fc908b5daaaad78916c106eeb4f738fa86446879`;
- attempts 2/3 plus sources archive
  `gpu_artifacts_local/pcfl_v2_failures_sources_20260913_attempt1/evidence.tar`,
  SHA-256
  `f19c45359e87828a0bb601b9243d83a1bfa8160799bc73e9cdaf4e39bbf912ed`;
- attempt 4 archive
  `gpu_artifacts_local/pcfl_v2_attempt4_20260913_attempt1/evidence.tar`,
  SHA-256
  `e4a7e7c76b27567dda9a9101b87930a1c319b813e6a1ef14b9120e7d80d05b9d`;
- seed-0 attempt-5 interruption archive
  `gpu_artifacts_local/pcfl_v2_seed0_interruption_20260913_attempt1/evidence.tar`,
  SHA-256
  `faf25b21619e951cf21a30624fa72bd7ab4d2c0f06b929d4e26b1a17505c20d5`.

Acceptance also requires Git commit
`3f4c03bc80298d5fd1062db49fbe26174fdc1b34`. Repacking a new self-contained
convenience bundle would improve portability but is not scientific rework and
must not replace these immutable hashes.

Do **not** generalize this result to unseen banks/facts, statistical
significance, autonomous replay choice, selectivity, LINK/composition/action
use, clean lineage, the clean-base PCFL S2 mechanism, C11, parenting, G3,
H1/H2, lifetime improvement, or the whole flywheel. `NO_WRITE` is not
compute-matched; B200 matches B dose but not work; B400 matches
updates/presentations but not B dose or exact target tokens; and the saturated
replay/clean tie does not establish equivalence.

**Final disposition: GO for the quoted bounded exposed-DEV retention claim;
REWORK for any broader or standalone-confirmation claim.**
