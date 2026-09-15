# Post-authentication parent delivery — September 15, 2026

Observation interval: **18:33:00–18:38:32.437056 UTC**, inclusive. Watcher reported authorized authentication recovery at 18:33; this reducer made no auth, credential, provider, retry, or child-process changes.

Request cohort uses native submission/reservation timestamps. Finish cohort uses response `finished_unix`, independently of request time. Every selected request in this interval has a native timestamp; no file-mtime fallback was needed. Published counts require exact request/response/PUBLISHED hash joins and publication by the observation bound. A pending request is not a failed or consumed reply.

| Branch | New requests | Request-cohort published C/M/S/pending | Finish-cohort published C/M/S | Native observed C/M/S/unknown (finish cohort) | COMPLETE guidance applied |
|---|---:|---|---|---|---:|
| F1 | 0 | 0/0/0/0 | 0/0/0 | 0/0/0/0 | 0 |
| F2 | 0 | 0/0/0/0 | 0/0/0 | 0/0/0/0 | 0 |
| F3 | 12 | 5/6/0/1 | 5/6/0 | 5/5/0/1 | 5 |
| F4 | 5 | 2/3/0/0 | 2/3/0 | 2/3/0/0 | 2 |

F1/F2 zero traffic is not evidence of successful delivery or authentication readiness. F3's additional pending request is outside the finish cohort. Its one published MISSING without a bound native observation remains UNKNOWN, not consumed.

- **F3 first COMPLETE:** `C033_E1_OPEN_PARENT`, requested **18:33:25.709153**, finished **18:33:43.308725**; request-to-finish **17.599572s**, provider elapsed **16.634039s**. Native observed **18:34:07.729887**; guidance injected into completed TRAIN capture `C034_E0_ORIGINAL`, which started **18:34:07.732517**. Thus publication and actual next-turn application are distinct.
- **F4 first COMPLETE:** `P0068`, requested **18:35:05.077159**, finished **18:35:17.137378**; request-to-finish **12.060219s**, provider elapsed **10.148853s**. Native observed **18:35:20.036649**; applied receipt recorded **18:35:25.573500**, referencing verified capture `N00776`. The latter is the after-capture receipt time, not an asserted injection-start time.
- **No recurrent OAuth/managed-settings errors** among finish-cohort results. F3 MISSING: five `lane_guidance_limit_no_cropping`, one `parent_tag_class`; F4: two length failures, one tag/class failure. Original verdicts preserved, no cropping, relabelling, or retry.
- Application is supported by exact native receipt/capture hash joins, not inferred from COMPLETE publication. No claim of useful behavioral change, retained learning, or causal parenting effect. No FINAL contents, parent text, or answer keys exported; raw remains on node5.

The JSON reduction contains per-request source hashes, timestamps, response/publication joins, native observations and application references. This is a bounded snapshot, not a running hourly rate.
