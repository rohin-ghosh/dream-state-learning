# Independent restoration — 2026-09-15 18:11 UTC

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

- F4: 18:06:10.307852 UTC; original root `orch_r115_grid_pair_20260915/F4`, call `calls/N00566.json`; SHA256 `15e1070ba3dca24a5916286d4419f4f99649c5b55230728e165cf7ff7df657ca`.
- A4: 18:06:14.981249 UTC; original root `orch_r115_grid_pair_20260915/A4`, call `calls/N00568.json`; SHA256 `a59ffb7af79f4d8428451f2da416f8b909ddc8f2b24d13c1c2e5b5252a09cc8b`.
- These are frozen-generation1 LoRA elicitation forks, with zero optimizer steps, not new sleep results. Full roots and counters: `../orch_r119_grid_continuation_20260915/INDEPENDENT_LIVE_1810.json`.
- First completed call receipts for other branches remain pending reduction; residency is not substituted for completion.

## Provider blocker: watcher action required

The low-effort node-local Fable calls fail before useful provider output, not beyond the 600-second request lifetime. Hubble verified F3 exits in 0.906 seconds because required remote managed settings are unavailable; F4 exits in 0.639 seconds with an expired OAuth session that cannot refresh. No credential or raw provider envelope is reproduced here. Please restore authorized Claude login/managed-settings access on node5. Do not bypass policy or replay already charged failures. Children continue generation and consume MISSING without waiting; first new COMPLETE remains unverified.

## Allocation and continuation

Family owners continue their existing assignments. No shared-learner startup or sleep barrier and no wait for the asynchronous head parent. Route and math use independent LoRA sleeps; math must use two episodes and anchor lambda 0.25. Code/grid remain explicitly elicitation-only. Node5 wall remains September 16, 2026 22:04 UTC. New September 16 06:00 FINAL epochs are separate from immutable old FINAL captures; a boundary trigger is not reported as an independently armed timer.

Main pushed journals and the independent two-tier run plan at commit `8b4d3860`; the local-to-origin ahead log was empty after that push. Raw forests and archives were not staged.
