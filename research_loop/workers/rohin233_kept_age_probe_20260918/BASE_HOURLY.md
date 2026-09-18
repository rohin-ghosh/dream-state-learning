# Continuous frozen-base hourly ACT and token receipt

Observed UTC: 2026-09-18T12:12:20.291868+00:00

Existing read-only receipt only; no new hourly daemon. ACT means completed-feedback attempt. Tokens count all completed child generations, charged on completion. Partial windows are not hourly rates.

| UTC window | ACT attempts | Scored strings | Raw accepted | New pixels | Faults | THINK tokens | ACT tokens | Total tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 07:00:00–08:00:00 partial | 15 | 0 | 0 | 0 | 15 | 2082 | 5815 | 7897 |
| 08:00:00–09:00:00 | 100 | 267 | 192 | 44 | 77 | 14899 | 39706 | 54605 |
| 09:00:00–10:00:00 | 37 | 201 | 117 | 5 | 13 | 7179 | 9199 | 16378 |
| 10:00:00–11:00:00 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 11:00:00–12:00:00 | 18 | 73 | 36 | 12 | 9 | 3097 | 4953 | 8050 |
| 12:00:00–12:12:20 partial | 4 | 29 | 23 | 3 | 0 | 907 | 641 | 1548 |

Retained token reconciliation: {"controller_total_tokens": 88478, "counts_as_of_finished_generation": true, "exact_retained_coverage": true, "retained_generation_tokens": 88478}

10–11UTC is verified inactivity during the known stopped epoch, not missing collection. 11–12UTC includes both the real gap before11:25 continuation and the R233 policy change; not a full active hour or single treatment.
R233 first actual guidance-bearing THINK completed11:51:03.269701UTC; exact request3756bc63… is the boundary. Treatment-separated counts are in PARENT_RENDER_LATEST.json / phase_counts and hourly_rows / treatment_breakdown.
Accepted strings are not certified literal jokes or novel ideas; repetitions and parser commentary may remain. No historical rescore. planned_unknown means missing declared cardinality, not unknown score. Guidance-span tokens are separately measured and unmatched; wrappers are not included. Main owns aggregate/hourly publication.
