# W1 bounded CPU preparation — 2026-09-12

Delivered at approximately 08:13 UTC. **CPU_PLAN_ONLY; W0_PARENT_PENDING; W1 execution_ready=false.**

Read `research_notes/analysis/2026-09-12_w1_cumulative_replay_readiness_audit.md` and the local frozen W0 material, recipe, receipt and read-only replay interfaces. The audit's original statement that only the aborted W0 exists is historical: main's latest instruction says attempt2 has completed fits and OFF generation/scoring but has no final label. This task did not inspect remote outcomes or assert a newer result. Neither partial completion nor this preparation authorizes W1.

## Scope and files

Only these NEW repository files were created:

- `organism_v6/writer_replay_plan.py` (214 lines).
- `tests/test_writer_replay_plan.py` (340 lines).

No existing repository source/test/notebook was edited. No Git operations, network activity, GPU queries, model/tokenizer loads, fitting, execution wrappers, retries or new attempts. No W0 run artifacts were touched. All parent API access is read-only. Test scratch files are local temporary CPU mock data.

Claim boundary: **prospective clean-base cumulative replay, not sequential-parameter retention or unrehearsed retention.** No TWO_BANK_CUMULATIVE_REPLAY_PASS label is produced. Every plan/geometry/exposure result has `scientific_label=None` and `execution_ready=False`; parent acceptance also remains not W1-ready.

## Explicit API

1. `build_new_bank(old_material)`
   - Validates OLD against the unmodified W0 generator.
   - Derives exactly the audit's domain-separated NEW identifiers using seed 20260912, and checks the first admissible orientation vectors at counters 5 and 1.
   - Root orientations are exactly `[0,1,0,1,0,0,1,1]` and `[0,1,0,1,1,0,0,1]`.
   - Preserves OLD templates, train/held coordinate orders, request seeds, spill families, unrelated-interface literals and expected outputs. Changes selected/neighbour identifiers and orientation-dependent training labels only.
   - Checks all 64 OLD+NEW selected/neighbour identifiers across both roots are distinct. No outcome-dependent inputs or reroll selection exist.
   - Returns a separate bank dictionary, not a W0-compatible execution material or a scientific receipt.

2. `validate_geometry(old_material, new_bank)`
   - Requires byte-equivalent canonical JSON to the prospective NEW generator, not merely Python numeric equality.
   - Produces 240 exact shortcut checks over both roots/maps, train/held panels, individual banks and pooled unions.
   - Includes W0 marginal controls, tool-only, and pooled bank, bank×mode, bank×stratum, bank×stratum×mode, bank×template, bank×template×mode controls. Every best accuracy is exactly 1/2 by integer cross-multiplication; panels are exactly label-balanced.
   - Checks orientation×mode remains a perfect positive joint oracle. It is deliberately not classified as a shortcut control.

3. `build_replay_plan(old_material, new_bank)`
   - Produces four root/map cells, each with reference `OLD_SINGLE`, prospective `NEW_SINGLE`, and prospective `CUM` ordered occurrences.
   - SINGLE: 128 rows × 2 logical epochs = 256 occurrences. CUM: 256 union rows × 2 logical epochs = 512 occurrences.
   - CUM epoch 0 is OLD[0], NEW[0], … OLD[127], NEW[127]. Epoch 1 is NEW[0], OLD[0], … NEW[127], OLD[127]. Both maps retain the same root's W0 optimizer seed.
   - Every occurrence binds bank/root/map, epoch, source-row index, step, optimizer seed, source-row SHA256, exact context, exact `ACT: a0\n` / `ACT: a1\n` target bytes and `context_only` mask policy. All ordered occurrences have a deterministic aggregate hash.
   - Four OLD fits are references only; the future proposal is four NEW_SINGLE plus four CUM fits (eight new fits; 3,072 proposed new optimizer steps). This does not schedule or authorize them.
   - `inherited_recipe` is an unchanged copy of the W0 recipe for reference. Separate `intended_dose` declares NEW_SINGLE 128/256 and CUM 256/512. This plan is NOT executable worker input and does not alter W0's fixed row/step recipe.
   - The output deliberately retains `W0_PARENT_PENDING`, `parent_binding=None`, `real_tokenizer_encodings_bound=False`, `training_run_replication=False`, `root_seed_confounded=True`.

4. `validate_replay_plan(plan, old_material, new_bank)`
   - Rejects any canonical-byte change to the deterministic plan, including seed/dose/mask/target/order/claim/readiness modifications even if hashes are recomputed.
   - Independently compares SINGLE versus CUM occurrence counters for each bank and epoch in every cell: exactly 128 distinct source rows once per epoch, twice overall, with identical text, target, mask and seed.
   - Returns 16 exposure checks and a plan hash; it is not a performance reducer.

5. `validate_w0_parent(path, *, expected_source_hashes)`
   - Requires an explicit complete trusted W0 source-hash map, including module/tests/launcher. Local replay source bytes and the parent manifest must both match. Pins are never automatically accepted from an untrusted parent manifest.
   - Rejects aborted roots and missing REAL_EXECUTION_SEAL before replay. Uses the existing full `w0.replay_real` read-only reducer with no caller-provided report override or skip option.
   - Requires replay evidence REAL_GPU_EXECUTION and exactly MULTIKEY_BINDING_PASS in both report and nested reducer result. W0 replay verifies all four fits, OLD/OFF records, request schedule, complete sealed inventory, process/step/resource receipts and the combined root/map gates.
   - Additionally requires the sealed, manifest-bound repaired native-build receipt (compiler hash/version, headers, successful CPU compilation, Triton version), and explicitly rehashes the four OLD adapter trees.
   - Returns ONLY `REPLAYED_W0_PARENT_ONLY`, `parent_eligible=True`, `execution_ready=False`, with parent root/seal/report/manifest/material/request hashes, four adapter paths/hashes, native receipt hash, source hashes and model/tokenizer/environment/node/GPU/driver/seeds identity.
   - Exceptions fail closed and propagate. A replay rejection cannot be overridden by an advocate, partial pass, CPU fixture, guessed label or optimistic caller report. No package/driver/compiler/model probing or environment mutation occurs here.

## Remaining real bindings — NOT completed

1. Main must obtain the actual completed immutable W0 attempt2 seal and exact successful read-only replay. There is no eligible real parent established by this delivery.
2. Supply independently trusted matching W0 source pins and readable original parent artifacts; the parent root is not copied over or written into. If local W0 replay bytes differ, the validator rejects rather than silently using different scientific semantics.
3. Bind actual parent material/seeds to the chosen plan: the plan's `old_material_sha256` must equal the accepted parent binding's `material_sha256`. Default-material hashes below are prospective CPU examples, not claims about attempt2's material.
4. Construct and seal a separate W1 real manifest that binds the accepted parent seal/report, all OLD adapters/records, NEW geometry, source bytes and ordered occurrences. The current API intentionally does not attach a parent or promote a CPU plan to ready.
5. Perform real-tokenizer/target-mask/EOS preflight, bind all 512 CUM ordered encodings per cell plus NEW-only encodings, and prove matched tokenized per-bank exposures. Current checks are exact source/text occurrence checks only; they do not claim tokenized equality or successful tokenizer behavior.
6. Require the same actual node/model/tokenizer/software identity as the parent and live native-build/Triton prerequisites. This validator binds historical evidence; it does not verify current machine identity or launch eligibility.
7. Define and bind the NEW OFF and explicit-map oracle records; NEW full single-bank gates; OLD↔NEW and cross-root evaluation matrix; per-key absolute TV/legal-ACT orthogonality; and stage-2 stop-before-CUM conditions. No such records exist in this module.
8. A dedicated W1 execution/receipt contract, resource/lease budget, no-rescue policy enforcement, relative KMG/BA reducer, absolute bank/interface/spill gates and final label precedence remain unimplemented. W0's four-fit/three-hour cap cannot silently be reused as authorization for eight extra fits.

## Concrete interface limit / intentionally omitted reducer

The directly reusable reducer is W0's sealed-parent replay. W0 `validate_material` regenerates OLD from its frozen generator; `action` uses OLD orientations; `build_requests`/`validate_requests` and `reduce_records` fix the W0 bank layout and 1,504-request denominator. Its executor fixes four 128-row/256-step fits. Applying those interfaces directly to NEW or CUM would reject the material or score against the wrong orientation/denominator. No monkeypatch, W0 edit, speculative W1 request format, execution wrapper or partial scientific label reducer was introduced to hide this gap.

The audit's full W1 reduction additionally needs per-bank immutable OFF raw records, the orthogonality matrix and matched SINGLE/CUM cells. Those real request/receipt bindings are not defined by reusable W0 interfaces. This delivery therefore stops at geometry/exposure proofs and the reusable parent gate rather than inventing a large evidence system.

## Tests and verification

`python3 -B -m unittest tests.test_writer_replay_plan tests.test_multikey_writer_gateway_simple -q`

**85 tests passed (25 new W1 CPU tests + 60 unchanged W0 tests), 12.187 seconds, no skips.** Log: `/tmp/astra_w1_cpu_preparation_tests.log`.

Coverage: prospective identifier/orientation goldens; disjoint neighbours; template/coordinate/spill preservation; exact bank and pooled shortcut proofs; complementary maps; nonmutation; no outcome/loader/compiler/GPU calls during planning; complete interleave hash; alternating epoch order; identical per-bank exposures; seed/mask/target checks; reordered, duplicated, dropped and relabelled occurrences; canonical-byte/type tampering; readiness rejection; partial/aborted/counterfeit parents; real W0 replay rejection; CPU-fixture/nonpass labels; source-pin mismatches; native/Triton and adapter tampering; read-only parent binding.

Positive parent-wrapper tests explicitly mock the already-tested W0 replay result and use files marked CPU_MOCK_NOT_AN_ADAPTER. They are not actual parent evidence. An unmocked replay of those counterfeit artifacts fails. No real W0 pass or W1 scientific outcome was generated here.

Whitespace checks on the new files passed. Existing W0 hashes matched the task-start snapshot exactly; no Git operation was used to check them.

## Prospective deterministic hashes

For unmodified `w0.build_material()` defaults only:

- OLD material: `ba778314376f8ab871a697010d1ace4b8929819271ff68a4acd01b465476ee17`
- NEW bank: `7b968ba4a9ad6b8d2abebc719c31d80d3f423f1ebf8b71ef9ff3037fe2398ce8`
- Geometry: `838cb711d6f2d06afdd4a1b23bdbe9973b6ddb5cf53dbdec0cf5a27807858761`
- Full replay plan: `cf6347f70ead1fd0f6b4f579ef537b471b941786a2ecfef2b7e4b921dec7d63a`
- Ordered occurrences: `c787e565e057435a894087aba3505e26477ac464699730d910886baf61b82ee1`
- Exposure receipt: `4c32519189184ea8ee3cadade23c160add2ba74f7317c8b9560437a904dc8cfe`

New source SHA256: `20c77d471d2ea9b2542132f7fdb882a16a34755021f07a211506f33cd7887ea5`.

New tests SHA256: `2490dee7ec8ce7de242865a0ec9f56feac0f46057433ebec30ae583ad2034df6`.

Observed local W0 pins, unchanged during this task (NOT a claim about remote attempt2 until main binds them):

- module: `99abab2c78dc06756b0bbbeb86d5717c5baf430af2cbafdab206f4fc8af4cafc`
- tests: `874ca3984471694724c365d1efc98e04187afb3ddf997a173993eda7d2188f37`
- launcher: `3994bf389e63ac790b3eb500c74a974ed57b88fd8fd02d494ae6fecc0ab33665`
