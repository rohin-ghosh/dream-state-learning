# Prospective Astra transitions — 2026-09-16 03:20 UTC

R121 model choice, not a refusal retry. Historical Fable replies remain Fable;
historical MISSING/refused requests are not resent or relabelled. The current
paper scope remains Level-1 initialization and four-way skill acquisition.

## Actual transitions

| Lane | Observed state | Prospective parent result |
| --- | --- | --- |
| F1 | Actor2664733 resumed saved C55 at C56; R139B readiness03:14:42 verifies original adapter/AdamW/CPU+CUDA RNG; same20948 inherited optimizer steps | Broker2281435; request000119_F1_C0056 returned Astra SILENT at03:16:21; explicit silence is not substantive guidance. Native uptake not yet observed. |
| F2 | Actor2627464 resumed saved C45 at C46;15981 committed optimizer steps and ongoing new sleep updates; no reset | Broker2229344; new C46E0 and E1 both Astra COMPLETE at03:09:01 and03:10:05. Native injection not yet observed. |
| F4 | Actor2638280 resumed C111 after parent322 at03:10:40; same frozen-gen1 adapter; FINAL/wall custody2615040 armed | Broker2257434; new P0323 MISSING before provider dispatch. Contract failure under repair, not successful parenting. P0323 will not be retried. |
| A2 | Original actor4007301 untouched; native986,parent108,committed16029 optimizer steps; cycle42 sleep updates advancing | Native received Astra COMPLETE and SILENT at03:11:35. Earlier apparent stall is not present. |

F1's failed attempt preserved its uncharged signal-only episode metadata; first
real episode uses EPISODE_0_R139B.json. F2's first admission failed on transient
process drift; the subsequent unchanged privileged scan was clear. Failed
attempt receipts are preserved, not overwritten. F4 is elicitation-only, not
active optimizer learning. No retention/behavioural improvement is inferred.

## Rolling-hour queue publications

Measured at **03:20:23 UTC**, preceding3600seconds, using response finished_unix.
These counts are queue publications, **not native injection or completed
interventions**. MISSING slots without a published response are not included;
zero publications do not establish liveness or absence of child activity.

| Lane | COMPLETE | SILENT | MISSING | Actual model of nonmissing replies |
| --- | ---: | ---: | ---: | --- |
| F1 | 0 | 1 | 0 | Astra |
| F2 | 2 | 0 | 0 | Astra |
| F3 | 0 | 0 | 0 | None observed |
| F4 | 0 | 0 | 1 | None observed |
| A1 | 1 | 4 | 0 | Astra |
| A2 | 4 | 3 | 0 | Astra |
| A3 | 0 | 0 | 0 | None observed |
| A4 | 0 | 0 | 0 | None observed |

No sealed/readout content was accessed to compute this table. Raw requests,
responses, checkpoints and native receipts remain node-local. Implementation
pins and launch recipes are in the adjacent F1_REPAIR, F2_HANDOFF and F4_TIMER /
F4_BROKER_SCRATCH documents. Live repairs and state preservation do not make
these historical branches a controlled four-condition paper experiment.
