# Preservation lambda0 control — 2026-09-12

Completed-control-only CPU reduction; no partial treatment read. Structured evidence: `/tmp/astra_preservation_control_analysis_20260912.json`.

## Validation and result

- Frozen reducer `25f03513e6092790337849282cdc780b4305518f760e08afcb7e81b2f28e4754`; native scorer/helper checks pass. Called `reduce_run(root, 0.0, original_hash)` and `historical_bridge` using `CUDA_VISIBLE_DEVICES='' /tmp/astra_preservation_cpu_20260912/bin/python -B`. No source edits, GPU, SSH, or Git operations.
- Explicit control producer: `a361af202a85e041dad119d57da7a54f583045e9472a358ae8a5efd31a32ef9c`. Expected future positive retry producer: `9a5ad83a246c07e0bf2094bafc9473c66952d56071d7a9cc75e93c2000bdf574` (cache-validation arithmetic repair; treatment not analyzed).
- Control capsule: `/tmp/astra_preservation_control_terminal_20260912/astra_A1_preservation_bank0_ts2_lam0_20260912_attempt1`. Valid with no errors: plans, original source/input hashes, ordered CE hash, anchors/preflight, setup/fit identities, complete loss log, DONE, 1,313 cues and native report. Report bank0 G9/G11 agrees with unchanged native recomputation.
- Acquisition I_d **1.921469872774875**, native interval **[1.2026075500735869, 2.682502692054215]**, 16 dose16 owners. Spill **0.41553692023821664**; **G9 FAIL** (unchanged spill limit 0.03).
- Dose16 conditional correct probability **0.2596499202574766 OFF → 0.6853229797885013 ON**; delta **0.4256730595310248**. Candidate mass **0.00873765625 → 0.99815843125**.
- Spill components: similar **0.41657727683077644**, unexposed **0.3213085371998146**, bicycle **0.5087249466840589**. **G11 FAIL**: ON abstention unexposed **0.00000465625**, bicycle **0.0000081625**, dose16 **0.0000066875**; original thresholds unchanged.
- Dose: **9,693 steps**, batch4, epochs3, rank8, seed2, lr1e-4; **749,985 input / 711,213 supervised tokens**. Cache unused, all anchor visits/forwards/tokens zero, KL absent. Mean CE **0.7169627227241947**, final CE **1.0938949584960938**; finite loss/accounting checks pass.
- Fit **1,227.287 s (20.45 min)**; eval **241.1 s (4.02 min)**; cache zero; stage total **1,468.387 s (24.47 min)**. These are recorded stage clocks, not total lease/controller time. Captured result says WORKER_COMPLETED at **12:12:07.667984 UTC**; cleanup receipt reports group empty, GPU processes absent, reservation release verified, no cleanup error. Receipt read only, not a fresh process/resource probe; reconciliation remains Main's.

## Historical descriptive bridge and limitations

Historical source recovered from existing mask reduction: `/tmp/astra_seed_bank0_evidence_20260912/runs/astra_A1_memory_dose_S1_F_r16k16_ts2_20260912`. Its bank0 inputs/fit/raw evaluation validate. All **1,313 cue metadata/order and OFF scores match exactly at serialized precision**. The bridge helper excludes model locators from its descriptive comparison; both actual eval locators are `hf`, so no eval-locator difference was observed. Dose16 acquisition/probability/mass and all spill-component deltas are **exactly zero**; paired-owner I_d difference interval **[0, 0]**. Historical fit time was **1,327.3 s**. This is agreement on observed reductions, not proof of native/clone identity or independent learner-seed replication.

Historical report is **absent from this capsule**, so historical report agreement is unavailable (no pooled three-bank claim). Historical model-file inventory is absent; current inventory is bound across plan/setup but model bytes were not independently rehashed here. Model location/display strings do not prove identical weights. Full fit metadata differences, including recipe, paths, instrumentation and timing, are retained in JSON rather than silently removed.

Both capsules omit adapter weights. Supplied remote receipt `/tmp/astra_preservation_control_weights_20260912.txt` records control adapter SHA-256 `c5bc4b2d7599d7f30732bb3adb98a1415206ecca41e0f96ce6d1db89015d6516` at the plan-bound remote adapter path. Receipt bytes/path are recorded and checked; **actual adapter bytes were not locally verified** and replay is unavailable from this capture.

**Conclusion:** validated CE-only control reproduces historical acquisition/spill reductions and still fails G9/G11. No treatment effect, preservation success, or readiness inference; full matched pair waits for completed positive capture.
