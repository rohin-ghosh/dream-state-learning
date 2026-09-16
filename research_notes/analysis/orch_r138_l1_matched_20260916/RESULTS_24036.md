# R138: matched Level-1 checkpoint 24036 versus 19428

[Builder / Main] September 16, 2026, 02:32:55 UTC native audit.

**No scored improvement after another 4,608 updates per arm.** Using the
unchanged, hash-pinned scorers, all per-case pass/fail outcomes match19428
in FULL and new-labels-masked CONTROL, ON and OFF.

| Fixed panel | FULL ON | FULL OFF | CONTROL ON | CONTROL OFF |
| --- | ---: | ---: | ---: | ---: |
| Capability | 22/32 | 24/32 | 22/32 | 24/32 |
| Code | 0/8 | 2/8 | 0/8 | 2/8 |
| Math | 7/8 | 7/8 | 7/8 | 7/8 |
| Tool call | 8/8 | 8/8 | 8/8 | 8/8 |
| Concise instruction | 7/8 | 7/8 | 7/8 | 7/8 |
| Source-present held discrimination | 16/16 | 6/16 | 16/16 | 6/16 |

Output shape: FULL ON352 generated tokens over32 capability cases, CONTROL ON336,
both OFF381; medians6.5,6.5,7.5 respectively, including EOS. Both ON31/32
single-line, OFF25/32. All responses terminal, no truncation. FULL ON changes
6 raw outputs and CONTROL ON2 relative to19428, with zero correctness flips;
all held outputs and OFF capability outputs remain byte-identical. These are
descriptive output-shape statistics, not persistence or metacognition evidence.

Eight panels rederived from384 original captures. All original capability records
reconstruct exactly; held scores recomputed from their original messages.468
source/checkpoint/receipt/capture files verified and unchanged across the audit,
including adapter, optimizer and RNG checkpoint files. Four distinct readout
identities at each checkpoint, distinct from their training processes; exit0 and
native unchanged-base/adapter postchecks verified. Eleven local CPU reducer
tests passed. No new GPU/provider calls or training ingestion.

Full native proof and manifest remain at
`/localhome/local-rohing/orch_r138_l1_audit_20260916_attempt1/RESULTS.json`, SHA256
`fa7f179ea589a022519e733bf6bd6cb35d4451cf19d43af5fd5e0dfff4b04e66`.
Compact aggregates and checkpoint/COMPLETE hashes are in `RESULTS_24036.json`.
Reducer source SHA256
`8ac78ecf738711399a82e71306d124e45cfc80871ca3a5517426cf9eb746ebc4`.

The held task supplies its source table. It measures parent-free, source-present
discrimination, **not file-free retention or four-condition skill acquisition**.
The code deficit predates the latest4,608 updates; this audit does not identify
its cause. Public-TRAIN R136 interface diagnosis is proceeding independently,
without exposing these held cases to generators or teachers. No scientific
promotion or new benchmark launch follows from this result.
