# Seed-matched frozen reference — actual progress

[Builder Main] September 15, 2026, 16:05:07 UTC.

The evaluation actually launched on `gpu/ovx_ssh.sh`, physical 7, at
15:59:05 UTC (guard PID 1368928). This is the initial-adapter-matched frozen
reference, not the cancelled GPU annotation allocation. Node-local root:
`/localhome/local-rohing/orch_r118_frozen_seed_reference_20260915_attempt2`.

PLAN SHA256: `4567e302366fc8b65801372ec0c4706f3fadbda6f3d73b8f8eeabcb8b688f47a`.
Actual launch admission SHA256:
`16d916e2738ab618af88d41c6efa8729fd394ec990cd0defb4e90db13f1bdaa0`.
The earlier allocation receipt names a prelaunch scan, not this launch scan.

Four of six fresh-process groups are COMPLETE, each with two episodes,
no parent and zero optimizer steps. No failure or campaign terminal exists
at this observation. Accuracy is background, not a thinking-quality measure.

| Group | Correct / episodes | COMPLETE.json SHA256 |
| --- | --- | --- |
| 1 | 1 / 2 | `4933a4a0b249df0db14112fd4fdc103375aece2248dcaefe468aea227b6d5400` |
| 2 | 1 / 2 | `758e42d5dc6e1159b00342cdee2a3cc328800ab1ea12fb289190b6c51e9d72b6` |
| 3 | 2 / 2 | `62bd5dbc68b70a1c5a84d7d8d221e8184d30439072d601d5b43506c1e6bda67b` |
| 4 | 1 / 2 | `dbfa367e1c51e1ea9ee67a08e4b240eaba1f1ae4990a671d8c8954b5297ddbb5` |

Receipts are under `RESULTS/group_NN/COMPLETE.json` in that root. Raw stays
on-node. Native end remains 16:50 UTC, external guard 16:51 UTC, no retries;
at most 72 calls with 512 generated tokens per call.

The first CPU preparation caught a task-hash JSON serialization mismatch,
before any model calls. The repair preserves the exact 12 task identities
and matches the feasibility manifest's encoding. Attempt 1 and its failure
remain preserved. Fourteen local and fourteen native focused tests passed;
the local reference plus checked-dispatch suites passed 21 tests at 16:05 UTC.

This reference closes one historical control gap only. Historical guided and
unparented doses differ (424 versus 536 updates). It is not a control for the
pooled node-5 child and does not establish retained thinking or parenting
causality. Semantic measures remain unassessed.
