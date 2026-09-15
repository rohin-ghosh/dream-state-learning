# Actual FINAL-only CPU waiters armed — 2026-09-15 16:45 UTC

Main authorized this separate failed-startup custody repair under the **existing** FINAL allocation. It does not restart or extend TRAIN, reuse either failed session, or add any calls. The expired16:35 startup authorization remains expired.

## Actual on-node readiness

Evaluation prefix `/localhome/local-rohing/orch_math_feedback_uptake_r118_final_custody_20260915_attempt1`:

| Branch / physical | CPU waiter PID | Actual start UTC | Root | SCHEDULED SHA256 |
|---|---:|---|---|---|
| F2 / 1 | 2956733 | 16:44:42 | lane1 | cf08decee0e62c4d0bbf572b1c9cabd2e0dc25ae25c68966a1abba23adf3de38 |
| A2 / 5 | 2956814 | 16:44:43 | lane5 | 822cf3701d9016dea9c13dc9e008a8da5c2a629a25fc9787f8a39ef93752c824 |

Both verified live again16:45:11 UTC, parentPID1, stateSs. No per-evaluator/global native claim, LEDGER, LAUNCH or TERMINAL exists; no model/provider calls or sealed outputs. Main selector1519259 remains live and untouched. Both waiters automatically wait until **2026-09-15 17:00 UTC**, then use Main's sole canonical FINAL_SELECTION and the original **17:20 UTC** stop, fresh strict admission, and fresh read-only model process. No human callback is required to trigger the waiters.

Actual ARM receipt `/localhome/local-rohing/orch_math_feedback_uptake_r118_final_custody_source_20260915_v4/FINAL_ARMED.json` SHA256 `a44a7f68497b89aeeb2956e005e4b583b5259de500639ef674efddf6a4d5f9b5`. A compact copy is FINAL_ONLY_ARMED.json beside this document.

## Provenance and unchanged scope

Frozen source `/localhome/local-rohing/orch_math_feedback_uptake_r118_final_custody_source_20260915_v4`:

- FINAL_SOURCE_MANIFEST.json SHA256 `883c4bc9e043b5bb20738e358e14ce82a0831b95f08c290b93546d0dada16494`.
- FINAL_NATIVE_CPU_TESTS.json SHA256 `6af9f2e7ff56018f01e25fa1615fe1674cc79536d270741d3df0abbdd33c7524`: **73 PASS**,1.588s native;73 local PASS. Final-custody, original-final, drain and scanner regressions included.
- FINAL_PREPARED.json SHA256 `21c9bde1c0b2319448ada8387db84cb228406b713bd4c37731b6398d3e713d55`: full source_files and both plan refs.
- F2 PLAN SHA256 `31e636dfe093ccfb3c6d5bd9d81a1f16388d6a8d507c6e963cf7bbc7c58d6a4f`.
- A2 PLAN SHA256 `7a1f3c83e2134ea853c3f4aee825d60733d5a22eaa5a58b29b695a2becacd445`.

Exactly8 native calls per branch,16 total under the original quota; parent0/train0/optimizer0/OPEN0/retry0. The original frozen base plus selected committed LoRA is read-only; no optimizer is created. Original decoder and native capture implementation are reused and tested for full raw reasoning/token preservation. Raw results remain node-local and never enter replay/training/buffers/parents.

Failed-startup custody validates both actual prior failures, authentic exited actors and timer retirements, unchanged carry/charges, and the absence of attempt5 guard/LAUNCH/timers. It does **not** invent CLEAN_RELEASE or an unrun guard terminal. Missing proof causes NOT_RUN. The original source/checkpoint/failure records are untouched.

Deduplication: recursive four-era original FINAL plan lineage, old charged/partial/completed attempts checked only after17:00, and one original-branch R118_FINAL_ALLOCATION.lock plus write-once R118_FINAL_ALLOCATION_CLAIM.json. The quota identity binds the oldest real allocation. No quota claim can be reset or moved to a second namespace. Partial/model-load failures are not retried. Sleep0 is not incorrectly treated as morning FINAL.

CPU packaging history remains archived: v1 lacked the old FINAL test file, v2 its imported selector test, v3 the selector module; those CPU runs failed and did not prepare or launch evaluators. V4 includes the unchanged pinned selector64ccee... plus tests, and all73 pass. No failed packaging run was counted as GPU science.

## Actual executable commands

Run from frozen source; **already running, do not duplicate**:

```sh
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -m gpu.orch_math_feedback_uptake_r118_final_custody schedule --root /localhome/local-rohing/orch_math_feedback_uptake_r118_final_custody_20260915_attempt1/lane1
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -m gpu.orch_math_feedback_uptake_r118_final_custody schedule --root /localhome/local-rohing/orch_math_feedback_uptake_r118_final_custody_20260915_attempt1/lane5
```

## Publication allowlist

- gpu/orch_math_feedback_uptake_r118_final_custody.py
- tests/orch_math_feedback_uptake_r118_final_custody_test.py
- research_notes/analysis/orch_math_feedback_uptake_r118_preinfer_20260915_attempt1/FINAL_ONLY_READY_1645.md
- research_notes/analysis/orch_math_feedback_uptake_r118_preinfer_20260915_attempt1/FINAL_ONLY_ARMED.json
- research_notes/analysis/orch_math_feedback_uptake_r118_preinfer_20260915_attempt1/FINAL_ONLY_NATIVE_CPU_TESTS.json
- research_loop/workers/MATH_PIPELINE_L2.md

Main owns Git. This is verified **ARMED_NOT_EVALUATED**, not a claim that the17:00 evaluation has completed.
