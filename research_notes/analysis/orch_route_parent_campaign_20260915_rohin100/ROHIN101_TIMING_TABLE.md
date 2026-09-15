# Rohin101 measured route cycle timing

Receipt created 2026-09-15T04:44:24.381471+00:00; timestamp-only snapshot 2026-09-15T04:40:37.727776+00:00. All times seconds; UTC boundaries September 15, 2026.

Experience includes loading, learner generation and parent waits. Pure generation and complete native parent wait are NOT separately instrumented. Queue = native reservation to provider dispatch (transport/scheduling/lock wait); provider = dispatch to verified receipt. Both are subsets of experience, NOT additive columns. Total = experience start through readout completion, including inter-phase gaps. FROZEN is the historical parented frozen-LoRA control, NOT the future NO_LORA arm.

| Lane | C | Experience | Parent queue / provider | Verified parent calls | Sleep | Readout | Gaps E→S / S→R | Total | Updates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GUIDED | 1 | 505.9 | 75.28 / 119.88 | 30 | 262.0 | 104.0 | 109.7 / 4.1 | 985.7 | 40 |
| GUIDED | 2 | 543.7 | 164.39 / 131.33 | 31 | 167.7 | 102.3 | 4.1 / 4.1 | 821.9 | 30 |
| UNPARENTED | 1 | 253.6 | 0.00 / 0.00 | 0 | 188.4 | 101.9 | 363.2 / 4.2 | 911.4 | 32 |
| UNPARENTED | 2 | 241.6 | 0.00 / 0.00 | 0 | 217.8 | 97.1 | 6.6 / 4.1 | 567.2 | 34 |
| FROZEN | 1 | 538.2 | 96.71 / 124.31 | 31 | 0.0 | 102.8 | 4.2 / 0.9 | 646.1 | 0 |
| FROZEN | 2 | 563.3 | 117.97 / 129.68 | 31 | 0.0 | 97.5 | 4.1 / 0.9 | 665.8 | 0 |

Dose: first cohort four scheduled presentations per admitted target at each cycle; admitted reflection targets GUIDED 8→3, UNPARENTED 4→5; FROZEN fits/updates zero. Each lane/cycle has eight TRAIN episodes and eight parent-free held goals (four paired worlds). Actual updates 40/32 then 30/34 are unequal; no pure-content causal claim. Parent calls are exact named DISPATCH/RECEIPT joins (123 verified total), not JSON-file counts. Actual primary claude-sonnet-5[1m] (canonical claude-sonnet-5); auxiliary-model calls excluded.

## Segment2 completed C1 and failure accounting

| Lane | Experience | Queue / provider | Verified/dispatched | Sleep | Readout | Total including gaps |
|---|---:|---:|---:|---:|---:|---:|
| GUIDED | 590.3 | 134.57 / 132.08 | 31/31 | 627.9 | 102.3 | 1434.0 |
| UNPARENTED | 236.7 | 0 / 0 | 0/0 | 706.2 | 95.5 | 1155.4 |
| FROZEN | 1185.0 failure-inclusive | 152.29 / 133.66 verified-only | 30/31 | 0.0 | 94.7 | 1284.8 |

FROZEN original failed work 494.8506s + failure→resume gap 534.7280s + resumed work 155.4200s = 1184.9986s experience envelope. Single malformed parent response preserved; one-character framing repair, no life reset or provider retry. Its absent verified receipt is not silently counted as verified latency. Segment2 dose remains 16; GUIDED/UNPARENTED C1 actual updates136/144; original controls unchanged. First-cohort historical privileged-admission failures remain in MEASURED_TIMINGS.failures and C1 scheduling gaps; no inferred failed-prelaunch duration.

Partials ONLY as of 04:40:37.727776 UTC snapshot: segment2 GUIDED C2 experience152.4s running; UNPARENTED C2 experience243.7s complete, sleep183.4s running; FROZEN C2 experience16.3s running. These are censored, NOT current/final totals.

Evidence: MEASURED_TIMINGS.json (phase REQUEST/COMPLETE paths and SHA256, exact parent receipt identities); TIMING_METADATA.json; FROZEN_FAILURE_TIMING.json. No raw VM collections or provider calls for this report. Rohin100 unlaunched queue retired; new NO_LORA boundary not launched.

## Exact phase boundaries (UTC)

| Lane / cycle | Experience | Sleep | Readout |
|---|---|---|---|
| GUIDED C1 | 03:38:38.342–03:47:04.192 | 03:48:53.912–03:53:15.954 | 03:53:20.057–03:55:04.082 |
| GUIDED C2 | 03:55:08.429–04:04:12.121 | 04:04:16.212–04:07:03.932 | 04:07:08.004–04:08:50.289 |
| UNPARENTED C1 | 03:38:38.312–03:42:51.932 | 03:48:55.082–03:52:03.485 | 03:52:07.716–03:53:49.665 |
| UNPARENTED C2 | 03:53:53.781–03:57:55.384 | 03:58:02.009–04:01:39.813 | 04:01:43.866–04:03:20.974 |
| FROZEN C1 | 03:48:57.384–03:57:55.630 | 03:57:59.796–03:57:59.797 | 03:58:00.697–03:59:43.528 |
| FROZEN C2 | 03:59:47.546–04:09:10.855 | 04:09:14.943–04:09:14.944 | 04:09:15.853–04:10:53.367 |
