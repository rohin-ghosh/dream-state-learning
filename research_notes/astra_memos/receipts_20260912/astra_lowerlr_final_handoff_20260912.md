# Lower-LR final analyst handoff — September 12, 2026

**Verified locally at 10:40:36 UTC. Main owns the scientific memo. No new experiment or repeat fit proposed.**

## Verification

- Re-executed the unchanged, hash-pinned reducer on the terminal capture: exit0, empty stderr, JSON exactly equal to main's `/tmp/astra_lowerlr_reduction_20260912.json`; `valid=true`, `off_match=true`.
- All **52** captured files match their bytes in `/tmp/astra_lowerlr_terminal_20260912.tgz`. Before/after capture hashes are identical. Source inputs match original baseline hashes and their new preparation receipts; fit/eval/remote-adapter metadata joins pass.
- Both fits: seed2, source-bank seed1, rank8, three epochs, 9,693 steps, 12,924 items, 749,985 input/711,213 supervised tokens; correct actual LR; zero training straddles/truncations. Existing token-preflight records agree. Logs contain TRAIN_DONE, EVAL_DONE and REPORT_DONE, with no observed NONFINITE/FAILED/traceback match.
- All1,313 cue IDs/order/saved metadata and candidate order match. All three pairwise OFF comparisons are exactly equal at serialized precision; zero changed cues and zero reported differences for raw probabilities, mass, logp and abstention. All required source-joined frame controls are present.
- Each treatment report selects exactly the original bank0 tag, one eval, sleep4, unchanged threshold. Native raw-eval G9 equals each report's bank0 and single-bank frame G9. The local baseline capsule has no native report; its bank0 result is reduced from the frozen raw eval, not a pooled three-bank headline.
- Both captured controller results say WORKER_COMPLETED. Both cleanup receipts have null error and `gpu_processes_absent`, `owned_group_empty`, `reservation_release_verified` all true. No captured timeout issue. Main's observation that controllers are absent was not independently rechecked remotely; no resource action was taken.

| LR | Native I_d_frame | Paired-owner95% interval | Spill | G9 |
|---|---:|---|---:|---|
| 1e-4 baseline | 1.921469872774875 | [1.2026075500735869, 2.682502692054215] | 0.41553692023821664 | FAIL |
| 3e-5 | 3.0775888272213274 | [1.990597907659552, 4.163140393550427] | 0.39360640989452245 | FAIL |
| 1e-5 | 1.1402326306841797 | [0.5201002964970097, 1.8159558603343995] | 0.29643610211603705 | FAIL |

Both new arms fail the unchanged spill limit .03 despite positive lower interval bounds. This does not establish a working selective writer.

## Smallest actionable points for the memo

1. **No missing-artifact or reduction blocker found.** Use the existing JSON/native report values; preserve the terminal archive plus the frozen reducer and verification receipt. No repeat fit or new assay is warranted by this verification.
2. **Use native acquisition columns consistently.** Native conditional P divides `p_raw` by the sum of candidate `p_raw`; the older campaign descriptive helper divided by separately rounded `mass`. Consequently native baseline frame P_OFF is **0.2596499202574766**, not the earlier descriptive **0.2596495149075415**. This tiny rounding/normalization difference is not OFF drift and does not change G9. Native P_ON is baseline **0.6853229797885013**, 3e-5 **0.9195088150013031**, 1e-5 **0.6172024279303997**. Keep frame candidate mass alongside P; do not substitute question-cue report mass columns. Reducer unchanged; no correction to old evidence bytes.
3. **Retain the existing limitation:** baseline node2 versus treatments node3, `UNRESOLVED_LOCAL_HASHES_ONLY`. Matching code, corpus, seed/recipe and rounded OFF scores does not authenticate historical base/dependency/initialization tensors. Within-bank owner intervals are not optimizer-seed uncertainty. Describe the acquisition/spill tradeoff without a generalized LR-only causal claim or clean-lineage/selective-writer promotion.

## Freeze and receipts

- Original reducer remains unchanged: `/tmp/astra_lowerlr_reduce_20260912.py`.
- Byte-identical read-only/executable freeze (mode0555): `/tmp/astra_lowerlr_reduce_20260912.frozen.py`.
- Both SHA256: `6a618ee48cadbb727266b447e6bb307148538a7580eaf13d370c31648b0bfbf2` — also equals the pre-terminal smoke receipt's hash.
- Detailed verification, exact replay argv, all52 file hashes, captured cleanup evidence: `/tmp/astra_lowerlr_final_verification_20260912.json`.
- Main reduction SHA256: `e62cbf9cc400773e8240240cd2c47cb7546902c729b909fb6366e3352937f94a`.
- Terminal archive SHA256: `f40c504ea67497bf64412f74195131dbf8701c7a8645f84ff0b92571ca121547`.

This is a local byte-bound verification/freeze, not a retroactive execution-time model seal. No repo edits, Git, SSH, GPU work, campaign-analyzer change, original-script edit, or captured-evidence mutation occurred.
