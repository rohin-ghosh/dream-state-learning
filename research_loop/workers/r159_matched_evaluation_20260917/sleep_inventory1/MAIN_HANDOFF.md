# R159 raw sleep snapshot inventory — September17 07:04 UTC / September17 00:04 PDT

Metadata-only observation ended07:03:27.098UTC at the original candidate5 cohort root `/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5`, cohort SHA`da04b4cd814f6f695ca49a1ace66f9378039f6166d04e26bbd27ed7692ad0b4b`. Current Main directive permits this bounded inventory; previous initial-only copy authority does NOT authorize these sleep snapshots.

`OBSERVATION.json` SHA`ea0a6ab8bbbb33860a592b414fd38a2dbad2deb6a0ae4447d6ad9d54863c9529`. Read36,589,324 metadata bytes; returned35,086 bytes, below256MiB/16MiB limits and08UTC source-read ceiling. No adapter/optimizer/RNG payloads, held readouts, private evaluator files, scores, or runner logs opened. No checkpoint copies, enrollment, dispatch, source writes, native recovery or process actions.

## Intended sleep1/2/4 findings

Each path is `<cohort>/<arm>/checkpoints/sleep_00000N/COMMIT.json`. Full journal record/intent paths and hashes are retained in OBSERVATION.json. Bindings verify contiguous record hash chains, paired intents, exact embedded checkpoint document equality, cycle, resume-state digest, last sleep receipt, arm and cohort. These are stable retained snapshots, not an inferred machine-wide complete-history attestation or exact event timestamp.

| Arm | Sleep | COMMIT SHA256 | SLEEP_COMPLETE record file SHA256 |
|---|---:|---|---|
| parented_learning | 1 | `3e8bffb0575e4f718b297b5fbf705955447992ba57cc77f512f58d03a99b65bc` | `3c433f1115e88e49c527c7833471211ab997b364a8310add577403206550b1b4` |
| parented_learning | 2 | `46112989ac300de3ace1799319c038be4c06245b31b437ee559b2de5a664f19e` | `6b33c1fc79e23eb799f2eecdfe58fc3d1bfd2857efef3a7e858d92d24bec4500` |
| parented_learning | 4 | `8c28ff18bb7bf3b27f33dab2793c5d09174f476918cbf09e4715100d45f86be2` | `5ba1ea61132e611d308bb5c1e73b9ebd9b814a9d2ffabd007e714b34a3e3549a` |
| unparented_learning | 1 | `f6567be0ef8ddf9efb998b5954f2f2eefebc5c9fd526c95466ec540a7169c680` | `fb3cc1bfbee78f116044d636f9ca315759246273a3b35d5b4a61680ac7b4ee02` |
| unparented_learning | 2 | `b906f40b829df48c7c8f0dc55d5eff3dbeed9c682fca311372330bb247dc2a8e` | `2e0f61ce621184538ab95ebe493022bbfeb4e957952264b23e793051aaabdd32` |
| unparented_learning | 4 | `b451818527855bf068890559cc7467fa9a68fc6b0d0574dafcf1aa86930d8f0c` | `cc41e512590c2e4fa5ed8b7e6a29fa943c57fbf4441d98801e14054d8b7e1928` |
| parented_frozen | 1 | `1aa0ab173c105e880c5b8da7ce697d57113c49d6c6536255b15cd4a3d443b977` | **NONE: orphaned COMMIT, not completed boundary** |
| parented_frozen | 2,4 | **ABSENT at observation** | **NONE** |

Learning694 verified records/9 total SLEEP_COMPLETE; unparented639/8; frozen14/0. Only intended1/2/4 are proposed, not later checkpoints. Six matching raw completed-boundary snapshots are prospective custody candidates, NOT enrolled/evaluated or evidence of valid training targets, improvement or retention. Frozen death cause is not determined by this inventory. Do not promote orphan sleep1, reconstruct its missing completion, or relabel initial as a completed sleep control. Remaining9 evaluator slots remain unevaluated; controls incomplete.

## Required custody and prospective scheduling — proposal only

1. Main/source owner must issue NEW exact authority for selected arm/milestone/source COMMIT hashes and the associated record+intent/chain/resume-state witnesses, citing this observation hash and namespace custody. Retain original initializer/cohort/task-freeze provenance. Explicitly exclude frozen orphan/missing boundaries and unrelated/repaired roots; no automatic source substitution.
2. Before any copy, a newly authorized bounded recheck must confirm immutable COMMIT bytes, original boundary witnesses, exact adapter-only file allowlist/hash/byte ceiling and receiving destination. Source authority must cover the actual copy time. No optimizer/RNG/history/held content; no permission inferred from the former initial-only allowlist or this metadata observation.
3. Existing dispatch cutoff06:59:45UTC has passed. No new job fits the original full3615-second requirement under08UTC. A separately approved prospective node2 schedule, exact config/GO, current node2 lease-minus6h and ownership/physical-slot admission evidence are required before any later execution; no wall/lease extension is performed or assumed. Any read past08UTC separately requires fresh source authority. Preserve fixed tasks/scoring/source semantics, existing ledger and672call/12slot ceilings; initial168 charged remain charged, leaving504. Six raw candidates would cost336 if subsequently authorized; no reservation is made now. Missing frozen controls prevent a completed matched longitudinal comparison.

Observer SHA`2610c87c48f0e71b972b8b68c50308fde09971297440a3ecbddb621e67c6fcf9`; tests SHA`8d330fdcb86dcec34aa2b2fc84e8d7e4cc0ff5eb69829a96d52c9a0b4ad0814b`. Seven CPU tests PASS: exact full binding, changed checkpoint rejected, duplicate/mismatch, orphan, missing, incomplete coverage, metadata-only projection/readout exclusion. One initial test assertion counted4 instead of5 metadata files (cohort+COMMIT+manifest+record+intent); corrected test-only, inventory bytes unchanged. Original parent-free results remain private, with no aggregate scores returned.
