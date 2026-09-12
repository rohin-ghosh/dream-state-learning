# SEQ115 — completed process-v2 write synthesis

**2026-09-12; bounded offline author-side synthesis.** Two independently fresh-base LoRA fits completed finite 12-update writes on the four bound process-v2 wakes; behavioral usefulness is untested.

## Verified result

- Capsule SHA256 `9db826c86b306ba5a92bcfc2902e0baaaed83318f1c70b029cb0ca062ec17e5a` matches the supplied validation seal; all **68 members** match exact names/hashes and safe archive checks.
- Plan SHA256 `67f2b89a769dd1f21e2ae3f048aa2d3743a5761f0574dcca3f47e1a8c51b0f44`. Source snapshot `4c3064c1c3eef068951e9c3b2ca46630754564e7`.
- Both fit manifests/adapter metadata/attempts/receipts join the controller terminal and native collector audit. No partial-pair aggregate was accepted.
- Each arm: two own-wake rows, seed2, fresh unadapted base, rank8/alpha16/dropout0.05, AdamW LR1e-4, batch2, grad_accum1, 12 epochs/12 updates/12 microbatches/12 observed forwards. No warmstart, packing, splits, drops or skipped target rows.
- Before/after trainability inventories agree: frozen non-LoRA parameters, 20,185,088 trainable LoRA parameters across all seven projections in 28 layers; 392 saved LoRA tensors per arm. Native collector attests all saved weight values finite; **weights are not in this capsule**.

| Arm | Epochs / updates | First rounded epoch loss | Exact final loss | Corpus input / target+EOS | Presented input / target+EOS | Worker+cleanup seconds |
|---|---:|---:|---:|---:|---:|---:|
| P | 12 / 12 | 0.08319 | 0.000196301334654 | 760 / 32 | 9120 / 384 | 148.841920 |
| A | 12 / 12 | 0.38255 | 0.000449771119747 | 758 / 31 | 9096 / 372 | 103.036209 |

All 12 epoch losses for each arm are finite; zero nonfinite batches. Full epoch arrays are in the JSON. These are repeated in-sample training losses, not behavioral measurements; lower P loss is **not** evidence P is more useful than A.

## Masks, exposure and lineage

Final Main review SHA256 `6d92db5ab0dfb6f4295e971fde8f03d355eff591525cba8ab85b11b7ef8ac325` and candidate SHA256 `c54ae950ae04f469ccb8f8ce48a623592dd4cea5acfd4ae817a260475722a3f0` match the raw local files and native preflight pair. Four source slots/calls remain P lesson0/1 `0009/0024`, A lesson0/1 `0039/0054`.

Preflight rendered-context/raw-target hashes match the capsule summary and exact Main native-review bindings. Context labels are -100; complete unchanged own raw target is loss-bearing with exactly one EOS. First-target predictor positions: P 363/363; A 362/363. Raw target lengths P 15/15, A 14/15; including EOS P 16/16, A 15/16. Input lengths P 380/380, A 378/380. All 24 forward receipts agree with these rows and per-batch exposure, including actual row permutations.

P has no padding; A has two masked padding positions per batch, 24 over 12 batches. Both perform 9,120 padded input positions, but unpadded exposure differs (9,120/9,096). Totals: **24 updates, 18,216 unpadded input tokens, 18,240 padded positions, 756 supervised labels** including 48 EOS labels. Raw-target exposure is 360 P / 348 A. This is not token matched.

Both fits start from the same locally hash-pinned Qwen2.5-7B-Instruct base with `init_adapter=None`; neither uses the other arm or the earlier record-write adapter as a warmstart. This is **CONTEXT_DISTILLATION_NOT_UNCHANGED_NATIVE_CONTEXT**, not proof the child generated the target independently of teacher influence. Origin remains **UNRESOLVED_LOCAL_HASHES_ONLY**; no clean-lineage claim.

## Costs — nested, not additive

- P training loop 38.5s; trainer wall 53.7s; supervised worker+cleanup 148.841920s.
- A training loop 9.4s; trainer wall 10.0s; supervised worker+cleanup 103.036209s.
- Worker-window subtotal **251.878129s**, contained within controller **484.619945s** (1200s limit; workers <=600s; cleanup reserve140s).
- Collector **68.362955s** (300s limit). Full observed launch-to-final-vacancy **912.231957s**, including waiting/CPU gaps/collection. **Do not add worker + controller + collector + full interval.**
- Initial archived vacancy XML/hash is verified. Final release is the supplied collector's process/session/vacancy/queue attestation, not a new query performed here. Timing asymmetry is recorded, not explained as an arm effect.

## Raw evidence paths

- Local capsule: `/tmp/astra_process_write_terminal_20260912.tgz`; validation: `/tmp/astra_process_write_terminal_validation_20260912.json`.
- Native preflight: `/tmp/astra_process_native_pair_preflight_20260912.log`; raw pair: `/tmp/astra_process_pair_v2_20260912.json`.
- Candidate: `/tmp/astra_process_native_candidate_v2_20260912.json`; **final** Main native review: `/tmp/astra_process_main_native_review_v2_20260912.json`. The earlier `/tmp/astra_process_main_review_v2_20260912.json` is preliminary and is not substituted for the final review.
- Native writer root: `/localhome/local-rohing/astra_diagnostics/astra_rulegame_process_write_v2_20260912_attempt1`.
- Capsule members: `metadata/run/plan.json`; `metadata/run/run/result.json`; `metadata/run/run/{P,A}/{process,supervision}.json`; `metadata/run/fits/{P,A}/{manifest,receipt,pre_update_trainability,post_update_trainability}.json`; `metadata/run/fits/{P,A}/adapter/{train_manifest,train_meta,adapter_config}.json`; `metadata/run/fits/{P,A}/forwards/0001.json` through `0012.json`; `metadata/collection/{audit,custody,material_summary,release}.json`, `release.xml`; `metadata/launch/launch.json`.
- Exact member inventory, all supplied input hashes and native-only excluded-file hashes are in the synthesis JSON. Native weight hashes are listed per arm there; excluded weight bytes were not transferred or locally rescanned.

## Limitations and claim boundary

- Metadata capsule contains no adapter weights or base files; finite-weight scans are native collector attestations, not local re-scans.
- Full actual forward tensor arrays and training-token files are excluded. Preflight causal labels/EOS and archived forward row/exposure joins are checked; actual tensor hashes are retained evidence, not entirely recomputed here.
- Final vacancy XML is not in the capsule. Initial vacancy XML is verified directly; final process/queue/vacancy claim is bound to supplied validation JSON, not a fresh local query.
- Raw pair/candidate/final Main review were checked locally, but native formation and source/model bytes were not re-opened on node3. Hash custody is not authenticated model origin.
- Context distillation uses teacher-influenced own raw wakes under teacher-removed conditioning; lexical exclusion/Main review do not establish semantic nonleakage or clean lineage.
- V2 is after-inventory exploratory amendment 96a71289. Frozen V1 shortage, fixed slots, native TRY aliases and wrong predictions are preserved.
- Two rows per arm, one seed, unequal targets/input exposure; training losses are in-sample fit statistics, not comparable behavioral utility scores.
- No reload/readout/retention/generalization/action-quality evidence is included. No G3/P1/G5/H1/H2, clean-lineage or efficacy claim follows.
- This is author-side custody synthesis, not fresh independent implementation review. The validation JSON is supplied provenance, not an external signature.

**Conclusion:** SEQ115 supports completed finite process-v2 writes with the specified masked exposures and fresh-base lineage. It does not support behavioral utility, transfer, better decisions, retention, or scientific promotion. No repo/Git/SSH/GPU or model execution; Main owns logging/archive.
