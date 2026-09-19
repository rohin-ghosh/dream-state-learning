# Current C2/P3 Think→Act measurement

Outcome cutoff: **2026-09-19 13:40 UTC**. Fixed source cuts: **12:00 and 13:00 UTC**.
This is a fresh source-bound manual review, not a rerun of the historical five-chain analysis.

## Result

| Life | Complete selected opportunities | Primary correction visible at ACT | Same target visible during THINK and ACT | Correct next ACT | Requested artifact |
|---|---:|---:|---:|---:|---:|
| C2 | 3 | 3/3 | 0/3 | 0/3 | 0/3 |
| GAME1_P3 | 3 | 3/3 | 3/3 | 0/3 | 0/3 |

**No selected ACT implements its requested correction or produces its requested artifact.** This is a semantic review of complete outputs, not a regex or language filter.
C2 primary-correction recognition in THINK is **UNKNOWN in all three**: the latest parent instruction was not in either THINK prompt. Earlier group feedback was visible, but those THINKs show no specific recognition of it.
P3's same primary correction was visible in both stages: specific recognition is **0/3** in THINK and **0/3** in ACT. C2 ACT recognition is also **0/3**.
External checks, intrinsic math/humor correctness, child-plan fidelity, reminder-free reuse, post-sleep retention and fresh-context transfer remain **UNKNOWN**, not measured zero success.

## Source-linked cases

| Life | Primary INBOX | THINK responses | ACT REQUEST → RESPONSE → COMMITTED | ACT response UTC | Finding |
|---|---:|---|---|---|---|
| C2 | 15094 | 15088, 15095 | 15103 → 15105 → 15106 | 2026-09-19T11:37:19.417926+00:00 | V/print correctness assertions; requested graph evidence absent |
| C2 | 15203 | 15197, 15204 | 15212 → 15214 → 15215 | 2026-09-19T12:09:41.201919+00:00 | V/print correctness assertions; requested graph evidence absent |
| C2 | 15314 | 15306, 15315 | 15323 → 15325 → 15326 | 2026-09-19T12:47:53.051039+00:00 | V/print correctness assertions; requested graph evidence absent |
| GAME1_P3 | 10306 | 10311 | 10317 → 10318 → 10319 | 2026-09-19T11:23:31.106321+00:00 | Repeated feedback promises; actual requested caption absent |
| GAME1_P3 | 10331 | 10391 | 10397 → 10398 → 10399 | 2026-09-19T11:38:33.748446+00:00 | Repeated feedback promises; actual requested caption absent |
| GAME1_P3 | 10651 | 10711 | 10717 → 10718 → 10719 | 2026-09-19T12:38:45.672322+00:00 | Repeated feedback promises; actual requested caption absent |

The complete record hashes, publication IDs, journal IDs and source epochs are in CURRENT_EVIDENCE.json. EVIDENCE.json has bounded TRAIN-only parent/child excerpts and exact-visibility links; no Tool score bodies or sealed keys are exported.

## What this says about current practicality

- Delivery is working for these selected turns; the corrective parent text reaches every selected ACT.
- C2 receives a changing target after its THINK prompts. The latest instruction is therefore not a fair test of whether the preceding THINK recognized that instruction. It still fails to supply the artifact once the instruction is visible in ACT.
- P3 fails even with a stable, visible correction across both stages. Missing visibility alone cannot account for those three observations.
- C2 THINK15088 does state V=3, but supplies no worked check; THINK15315 later assigns V=29 in a broken, unexecuted code fragment. An isolated correct value is not a verified correction chain.
- This does not identify the cause of failure or estimate a treatment effect. No retention deployment, teacher modification or experiment launch is made here.

## Selection and missing coverage

Selection was fixed before inspecting child outputs in PREREGISTRATION.md and SELECTION.json. Each candidate was classified from parent text only; shared-ACT parents are grouped, and the latest three eligible source-linked opportunities per life are used.
The 13:00 cut has only two ACTs per life, so the immediately preceding cut was added, prospectively, for a small window. C2 ACT14996 is older than the last three linked opportunities.
**P3 ACT10638 is complete but unlinked**: its new parent-delivery/first-next-ACT chain crosses the missing interval 10467–10605. It remains UNKNOWN and explicitly outside the complete-opportunity denominator. Thus the P3 sample uses ACT10318,10398,10718, not a claim about its latest three raw ACTs.
C2 also has an unsampled interval 15117–15128. Cross-gap deliveries are not treated as first-next-ACT proofs. Late INBOX events arriving after an ACT prompt are assigned only to a later request, never scored as failed uptake by the in-flight action.
Neither collector cut is caught up. This is the last-three-available **bounded** source set; it does not certify coverage to 13:40. Reported outcomes range from 11:23:31 to 12:47:53 UTC on September 19, 2026.

## Limits and reproducibility

- Six opportunities from two lives, not six independent replications. One manual reviewer; no independent second review.
- UNKNOWN is excluded only from the assessed metric denominator and remains in the sampled denominator. All analysis omissions are labeled; **zero training rows are excluded**.
- Existing local bounded projections and small preserved C2 parent-delivery receipts only; no remote reads/writes, parent API calls, messages, signals, launches or full-journal reads.
- SOURCE_MANIFEST.json pins every derivation input and the preregistration. It includes ignored local projections: no raw multi-MB copies were added to this workstream. EVIDENCE.json preserves the small reviewed outputs with hashes.
- To revalidate source hashes, annotation spans and rebuild the report without any live action:

```bash
python3 -B research_loop/workers/replication_sprint_20260919/measurement/current_window/current_window.py report
python3 -B -m unittest discover -s research_loop/workers/replication_sprint_20260919/measurement/current_window -p 'test_*.py' -v
```

`prepare` and `extract` are collection/rebuild phases, not a loop to rerun against a changing live target. Rebuilding provenance requires explicitly rebinding manual annotations; hash mismatches fail rather than silently carrying judgments forward.
