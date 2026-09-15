# All published responses: finish cohort, September 15, 2026

**Inclusive interval: 18:33:00–18:51:50.929972 UTC.** Enumerated ALL final response files; inclusion uses `finished_unix`, independently of request time. No new-request prefilter. All 61 selected request/response/PUBLISHED hash joins verify. Native submission/reservation timestamps determine the separate pre-cut column; no unknown request time among these responses. Pending counts are unfinished requests at the upper bound, outside the finish denominator; zero expired unresolved requests were observed.

Counts use **COMPLETE / MISSING / SILENT**.

| Branch | All finish-cohort publications | Queued before 18:33 | Pending at upper bound | Native observed C/M/S/unknown | Verified COMPLETE applications |
|---|---|---|---:|---|---:|
| F1 | 2 / 0 / 0 | 0 / 0 / 0 | 0 | 2 / 0 / 0 / 0 | 2 |
| F2 | 2 / 0 / 0 | 0 / 0 / 0 | 0 | 1 / 0 / 0 / 1 | 0 verified; not inferred from acceptance |
| F3 | 23 / 15 / 0 | 0 / 0 / 0 | 2 | 23 / 15 / 0 / 0 | 23 |
| F4 | 13 / 6 / 0 | 0 / 0 / 0 | 0 | 13 / 6 / 0 / 0 | 13 |
| Total | 40 / 21 / 0 | 0 / 0 / 0 | 2 | 39 / 21 / 0 / 1 | 38 |

**F2 actual delivery:**
- `R121_C000013_E0_experience`: request **18:42:21.197450**, COMPLETE finish **18:42:38.141366**, native COMPLETE receipt **18:42:44.174783**, before reflection. Native receipt SHA256 `2a915547edbec86473f7a76c2166cf2d1406d8c76acdf91d316cdd4b09302df8`. This proves native acceptance, not successful subsequent reflection completion or useful behavior.
- `R121_C000013_E1_experience`: request **18:42:24.984336**, COMPLETE finish **18:42:49.380990**; matching native acceptance/consumption unverified through the bound. Keep UNKNOWN.
- Both finishes occurred after the earlier snapshot ended **18:38:32.437056**. Preserve that original table unchanged; this supplement documents later delivery and explicitly checks cross-boundary requests.

First COMPLETE finish: F1 **18:39:07.737125**, F2 **18:42:38.141366**, F3 **18:33:43.308725**, F4 **18:35:17.137378**.

**Zero recurrent OAuth/managed-settings failures** among the finish cohort. Applications require separate native receipt/capture hash joins for completed subsequent TRAIN calls; publication alone is not consumption or semantic success. No provider, credential, prompt, scorer, child-process, raw-capture or original-table changes; no retries or Git actions. Raw remains on node5. JSON contains only metadata/hash references, not parent text, answer keys or FINAL contents.
