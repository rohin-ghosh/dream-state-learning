# R204 node2 dispatch repair — September 17, 2026, 20:36 PDT

## Outcome

The two initial OUTER_FAILED receipts remain failures, not live launches. They failed before any native/LOADED event. Under new R204 casefixed run identities, both replacements now have actual native, LOADED, REQUEST, THINK, ACT and LEARN receipts. Fresh process identity plus NVML reconciliation confirms four live assigned clones and no spare node2 GPU at03:36 UTC /20:36 PDT. Original C2, creative0/5/7 and repo2 were not signaled or modified.

| GPU | Arm | Native PID/start ticks | LOADED PDT | First ACT PDT | First REQUEST |
|---|---|---|---|---|---|
| 1 | MATH-D | 2128807/92801327 | 19:47:30.403132 | 19:49:27.991370 | 5850 |
| 3 | REPO-C | 2170067/92935338 | 20:09:50.453237 | 20:10:18.489407 | 5850 |
| 4 | CREATIVE-D | 2204408/93044490 | 20:28:02.732154 | 20:28:46.913354 | 5853 |
| 6 | MATH-TRANSFER-C | 2204538/93044773 | 20:28:05.558742 | 20:28:56.328125 | 5853 |

LOADED uses the recorded loaded_unix; ACT timestamps are journal file mtimes, not inferred response-completion times. Both new copies load exact adapter82a988a0ded69ce85723192b366251d21f8ec5fe8466e9ca98202fb09b57ce92 at4908 optimizer steps from fixed51 plus committed console5846.

## Precise cause and confinement

The fatal stderr is FileNotFoundError from r184_node2_confinement.verify reading `/proc/driver/nvidia/gpus/0000:CE:00.0/information` or `/proc/driver/nvidia/gpus/0000:D5:00.0/information`. Linux exposes lowercase `0000:ce:00.0` and `0000:d5:00.0`. This was a PCI-path case mismatch, not evidence of a host-gate problem or a bad child. Each strict probe returned1; no native started.

Repair checked the actual lowercase kernel directory's UUID/minor, preserved failed source/control/logs, checked no residual native owner, changed only the node-specific path/run identity and applied the authorized exact R204 payload. Confinement was not relaxed: GPU4 denied foreign minors0/1/2/3/5/6/7; GPU6 denied0/1/2/3/4/5/7. Both performed fresh privileged admission and own-minor open/close checks. No in-flight native launch was canceled. The idle transfer bridge had never dispatched; its exact owned identity was replaced. The existing first inputs were not republished and parents were not restarted.

Remote common root: `/localhome/local-rohing/orch_r153_r201_node2_clones_20260917_operator1/`. For each of `creative_d1` and `math_transfer_c1`:
- Prior evidence: `failed_dispatch_r203_pci_case/` plus original `control/` and `STARTED.json`.
- Current launch: `STARTED_R204.json`, `control_r204_casefix/GUARD.json`, `CONFINEMENT_CHILD.json`, `PRE_SERVICE_ADMISSION.json`, and root `R204_CASE_REPAIR.json`.
- Consumed source: `source/`; node2 helper `repair_unlaunched_r204_v2.py`; local reusable code `repair_unlaunched_r204.py` and corrected `prepare_r203_slots.py`. Never blindly rerun a consumed launch helper.
- R204 archive SHA: b0f148c92172af9d1525fda79a97bebfb31337e312e26c0f6bc805b3c687f8fc. Exact receiving source pins are in the current GUARD, not stale root SOURCE/CPU receipts.

## Actual feedback and limits

REPO-C's first inline-backtick action was not dispatched. Its later literal list operation ACT5938 completed against the safe pinned16352-file mirror; the actual result/receipt was fully visible in masked REQUEST5943, SHA f40751051520d52645ae9fcb33a95b26ada77a269871e6bb040e41a3f4449d54. No child code/test execution, merge or scientific success is inferred.

CREATIVE-D ACT5863 contains an actual four-turn dialogue contrasting Moby Dick with Pride and Prejudice. The operator read it and published a qualitative Astra response20:35:13.033821 PDT, specifically addressing the distinct voices, missing personal stakes and irrelevant calculation recap. The complete pinned parent reference was read, not bulk-pasted. Publication occurred with latest complete52 and before withdrawal; consumption/render is not yet claimed.

MATH-TRANSFER-C's first response contains an incomplete Python fence; ACT5870 reports LANGUAGE_RESPONSE_UNVERIFIED, not an execution. Truthful non-dispatch feedback appears in masked REQUEST5875. Its sandbox binding is real, but no successful actual sandbox result is established by this first ACT. MATH-D's first execution was a real NameError, whose stderr rendered in REQUEST5875. SymPy1.14.0/mpmath1.3.0 match the reported MATH-B package versions; full environment equivalence is unproven.

New-arm post-ACT REQUESTs are masked and bounded: CREATIVE-D7413 tokens; transfer8244. CREATIVE-D first cycle used one THINK, transfer requested a second explicit THINK. The configured R204 policy is R204_EXPLICIT_THINK_CONTINUATION_V1. No peer exchange has started; initial guided52–54 and withdrawn55–57 remain intact. Existing MATH-D/REPO-C R204 updates at saved complete boundaries remain outstanding and are not falsely reported armed. No rollback to source51 is allowed.

## Changed paths and evidence

All paths below are within `research_loop/workers/rohin201_c2_clones_20260917/node2_operator/`:
- `STATUS.json`, `STATUS.md`, `R203_LIVE_CAPACITY.md`, `R203_SCALE_ASSIGNMENT.json`: corrected four-live roster and exact current runtime/remaining-work distinction.
- `R204_DISPATCH_REPAIR.md`: this finite report.
- `inspect_dispatch_repair.py`: bounded read-only stderr, process, journal and first-action collector.
- `receipts/MATH_D1_REFRESH_20260918T033140Z.json`, `receipts/REPO_C1_REFRESH_20260918T033141Z.json`, `receipts/CREATIVE_D1_REFRESH_20260918T033141Z.json`, `receipts/MATH_TRANSFER_C1_REFRESH_20260918T033141Z.json`: fresh process/NVML observations.
- `receipts/DISPATCH_REPAIR_AND_ACT_20260918T033257Z.json`, `receipts/DISPATCH_REPAIR_AND_ACT_20260918T033613Z.json`: preserved exact failure stderr, new strict proofs, LOADED/first ACT and parent receipts.
- `receipts/R204_ACT_AND_REAL_REPO_FEEDBACK.json`: bounded actual operation/result/render evidence.
- `receipts/R204_CREATIVE_QUALITATIVE_REVIEW.json`: source-bound qualitative publication receipt, not yet consumption proof.

No canonical runtime/tests, fleet arm table or COORDINATION edits were made in this resumed finite repair-reporting turn. Existing Main/other-worker edits were left untouched. No expired node3 access, sealed/final evaluation results, credentials or subagents were used.
