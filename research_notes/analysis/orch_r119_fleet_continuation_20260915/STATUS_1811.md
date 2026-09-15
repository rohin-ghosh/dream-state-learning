# Independent restoration — 2026-09-15 18:11 UTC

## Update: node5 all eight computing at 18:19:16 UTC

Independent wrapper census: physical 0–7 memory MiB = 23648, 15810, 17238, 36394, 35046, 15704, 16982, 18880; utilization percentages = 100, 85, 85, 100, 53, 87, 6, 81. F2/A2 now have active models; A4 is resident again after its packaging-failure recovery. This verifies eight active GPU slots, not eight delivered parents or successful math sleeps. First completed math calls and actual sleep updates still require receipts. Old-fleet empty slots remain assigned to their existing family owners for restoration; the earlier whole-fleet census below is historical, not updated by arithmetic.

Measured via the five SSH wrappers, not inferred from allocations. Resident means memory.used > 1024 MiB; computing means instantaneous utilization.gpu > 0.

| Wrapper | Resident / 8 | Computing / 8 | Empty physical slots |
| --- | ---: | ---: | --- |
| a100 | 5 | 5 | 5, 6, 7 |
| ovx | 8 | 8 | none |
| ovx2 | 4 | 2 | 3, 4, 5, 6 |
| a40r | 5 | 3 | 4, 5, 6 |
| ovx3 | 5 | 5 | 1, 5, 7 |
| Total | 27 / 40 | 23 / 40 | 13 empty |

Node5 F1/A1 (physical 0/4) are newly resident and computing. F3/A3 (2/6) and F4 (3) are computing. Math F2/A2 (1/5) is still pending. A4 (7) completed model calls earlier but is empty in this snapshot; its owner is checking termination versus reload. This is NOT saturation and NOT eight healthy branches.

## First completed independent model calls

- F1: 18:10:58.432195 UTC; original root `orch_r111_f1_v4_20260915_node5_0_attempt1`, call `cycle_0008/CALL_000426.json`; SHA256 `a00d4c47ca50b9578905ab711fd2ecc0678948d836d85716915e99a81f40bb9c` (13 generated tokens).
- A1: 18:10:59.111499 UTC; original root `orch_r111_f1_v4_20260915_node5_4_attempt1`, call `cycle_0005/CALL_000203.json`; SHA256 `28b570f933727a83f6c48a5b9b30c8abceef4596c49604041d0e27d7b0f67e1d` (12 generated tokens).
- F3: 18:06:04.281714 UTC; original root `orch_r108_code_parent_r115_node5_2_20260915_attempt1`, reservation `C023_E0_ORIGINAL.json`; SHA256 `1fc4f9f5eee5e94713b5d8875ceb3a6fa8934968eba90462ee2549612a81a4f6`.
- A3: 18:06:03.778007 UTC; original root `orch_r108_code_parent_r115_node5_6_20260915_attempt1`, reservation `C009_E0_ORIGINAL.json`; SHA256 `5d0d1caaa0732e873036537f5b227fa86d7a03fcebe84ea5d8bdb5b578f0a2a5`.
- F4: 18:06:10.307852 UTC; original root `orch_r115_grid_pair_20260915/F4`, call `calls/N00566.json`; SHA256 `15e1070ba3dca24a5916286d4419f4f99649c5b55230728e165cf7ff7df657ca`.
- A4: 18:06:14.981249 UTC; original root `orch_r115_grid_pair_20260915/A4`, call `calls/N00568.json`; SHA256 `a59ffb7af79f4d8428451f2da416f8b909ddc8f2b24d13c1c2e5b5252a09cc8b`.
- Code/grid are frozen-generation1 LoRA elicitation forks, with zero optimizer steps, not new sleep results. Full grid roots and counters: `../orch_r119_grid_continuation_20260915/INDEPENDENT_LIVE_1810.json`. Route first-call receipt: `../orch_r111_parent_20260915/R121_FIRST_NATIVE_1811.json`; this first-call snapshot does not certify new optimizer updates.
- First completed call receipts for other branches remain pending reduction; residency is not substituted for completion.

Code receipt added at 18:17 UTC from `../orch_r118_code_parallel_20260915_attempt1/R119_INDEPENDENT_LIVE_1814.json` (measurement timestamp 18:12:08 UTC). It records 15 new F3 COMPLETE native calls / 7179 tokens, versus 20 A3 / 7061 tokens; both have zero optimizer updates. A3 records two consumed COMPLETE parent statuses, whereas F3 records ten MISSING and no injected parent IDs. These are operational delivery counts, not a measured learning effect. The filename's 18:14 label is not the measurement time.

## Provider blocker: watcher action required

The low-effort node-local Fable calls fail before useful provider output, not beyond the 600-second request lifetime. Hubble verified F3 exits in 0.906 seconds because required remote managed settings are unavailable; F4 exits in 0.639 seconds with an expired OAuth session that cannot refresh. No credential or raw provider envelope is reproduced here. Please restore authorized Claude login/managed-settings access on node5. Do not bypass policy or replay already charged failures. Children continue generation and consume MISSING without waiting; first new COMPLETE remains unverified.

## Allocation and continuation

Family owners continue their existing assignments. No shared-learner startup or sleep barrier and no wait for the asynchronous head parent. Route and math use independent LoRA sleeps; math must use two episodes and anchor lambda 0.25. Code/grid remain explicitly elicitation-only. Node5 wall remains September 16, 2026 22:04 UTC. New September 16 06:00 FINAL epochs are separate from immutable old FINAL captures; a boundary trigger is not reported as an independently armed timer.

Main pushed journals and the independent two-tier run plan at commit `8b4d3860`; the local-to-origin ahead log was empty after that push. Raw forests and archives were not staged.
