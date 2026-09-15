# Genuine BASE reasoning-first refill: first measured output

September15,2026. Both node3 physical4/5 workers run frozen Qwen BASE with no
adapter. The replacement system prompt permits reasoning before a final action;
it does not retain the old whole-response bare-protocol restriction. Model state
AND prompt changed relative to37ec, so this is not a single-factor comparison.

## Throughput, not qualification

Fixed600-second window07:45:32–07:55:32UTC, after both actors became ready:

| Arm | Completed raw rows | Raw rows/hour | Content tokens | Bare-command rows | Exact duplicate raw rows |
|---|---:|---:|---:|---:|---:|
| Persistence permission, physical4 | 108 | 648 | 19441 | 0 | 3 |
| Functional allocation, physical5 | 121 | 726 | 19250 | 0 | 4 |

Combined229rawrows/600seconds =1374rawrows/hour. Neither arm has a native-call
failure in this window. These are output captures, not unique tasks or qualified
training rows. Qualified rows/hour remains UNKNOWN; prose length is not admission.

## Bounded functional audit

Author inspected the first3completed episodes per arm (5calls and4calls).
Each arm:0supported functional metacognitive changes,1not-supported episode,
2UNKNOWN. Ordinary evidence-conditioned updates occur in2/3 and1/3episodes;
these do not by themselves show a realization changed the reasoning strategy.
All6causal counterfactuals remain UNKNOWN: there is no matched intervention that
establishes what action would occur without the reasoning. Outcomes were not
used as the audit criterion. No population functional-rate claim follows from
this small prefix sample. Do not admit these rows as demonstrated functional
metacognition or claim that longer responses solve R107.

The earlier37ec command-only run and its null results remain preserved.
`AUTHOR_AUDIT_FIRST3.json` contains bounded judgments and source hashes;
`THROUGHPUT_600S_01.json` contains all window capture hashes. Raw stays on node3.
Measurement regressions:5local and5native tests passed. No new model/audit calls,
outcome-triggered stop, retrospective relabeling, or corpus ingestion occurred.
