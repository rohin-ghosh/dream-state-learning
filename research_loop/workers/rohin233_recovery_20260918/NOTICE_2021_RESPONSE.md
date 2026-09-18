# Response to September 18, 20:21 UTC recovery notice

The original C2 SIGTERM/exit is real. C2 has not resumed inference yet; journal
replay is downtime, not a live conversation. A separate authorized continuation
was already dispatched at **18:28:45.770 UTC**: native **829798**, start ticks
**29168595**, under `orch_r233_C2_deadline_20260918/control`, preserving
COMPLETE11502 / sleep114 / optimizer7756 and the saved adapter, optimizer,
RNG, working state and original journal. The actual 20:21:52 UTC observation
still shows that process running replay with no new WALL/LOAD. Starting another
copy would duplicate recovery, not repair an absent dispatch. No second replay
or signal was issued in response to this notice. First renewed LOAD and first
REQUEST-to-ACT remain pending, not fabricated from the old incarnation.

The admitted node-5 bound is **September 20, 2026, 18:00 UTC**, within the
previously reported September 21 allocation. **September 24, 18:00 UTC belongs
to node 3**. Applying that date to node 5 would exceed its reported allocation;
updated allocation evidence is required before that further extension. The
existing admissible continuation is not waiting for such an extension.

## C0 and Astra7: cited PIDs and short timers are superseded

Fresh read-only process, command-hash, plan-hash, wrapper-duration and systemd
checks match the actual renewed incarnations. Both old PIDs are absent.

| Life | Current PID | Actual WALL / LOAD | LOAD UTC, September 18 | Native bound UTC |
| --- | ---: | --- | --- | --- |
| C0 | 881309 | 3191 / 3192 | 18:17:34.010 | September 20, 18:00 |
| Astra7 | 886059 | 3544 / 3545 | 18:15:05.944 | September 20, 18:00 |

The renewed outer timeouts end approximately September 20, 17:59:48 UTC;
neither is still on tonight's 22:55/22:59 timer. Current observed journal heads
are 4115 and 4671. Those head metadata reads are explicitly distinguished from
full record re-verification. Recovery gaps were 575.249 and 314.863 seconds,
respectively; continuity was not uninterrupted. Receipt:
`C0_ASTRA7_NOTICE_RECHECK_2022.json`. No additional restart is needed or issued.

## P3: no inference-ready native to parent during replay

The first renewed native598987 loaded at19:24:06, then exited1 at19:26:21 on
the stale correction-cache conflict. That failure is preserved, not a current
live-parenting target. The repaired controller658049 has finished its
preservation replay and dispatched the retry; at20:24:45 the sole attachment
waiter3671383 still awaits an actual retry LOAD. It will attach the original
xhigh parent ledger only to that verified incarnation. Neither a stale parent
turn nor a running replay process is reported as current parenting cadence.
The queued retrospective Tool notice remains intact, not duplicated.

## R207 constructed contrasts on the adopted checkpoint

Wins out of100 per type, with the same adopted rank8 / step15625 checkpoint:

| Contrast | Widegap6250 historical | Retained15625 diagnostic | Fresh serving-path15625 |
| --- | ---: | ---: | ---: |
| Word shuffled | 100 | 97 | 97 |
| Scene description | 100 | 97 | 97 |
| Nonsense | 99 | 96 | 96 |
| Truncated | 94 | 93 | 95 |
| Mid-tier | 74 | 77 | 78 |
| Other contest | 51 | 90 | 90 |

The retained/fresh differences are not silently reconciled; their cause is
not established. The completed fresh battery is source-bound by
`rohin233_ovx4_recovery_20260918/JUDGE_FRESH_CONTRAST.json`. Scorer adoption is
live for all eight sessions; adoption is not proof of humor or learner gain.

## P3 retrospective rescoring

Of223 historical entries, **7 of26 old accepts survive; 19 now fail**. Seven
previous failures now pass, giving14 passes overall. No novelty was recomputed
and no rechecked entry was counted as a new opportunity. Surviving identities:

| Caption hash prefix | Original own response | Old rank | New rank |
| --- | --- | ---: | ---: |
| a6861505f818 | Own span not authenticated | 49 | 45 |
| 1a564b4b9233 | Own span not authenticated | 49 | 50 |
| 142503487e84 | Own span not authenticated | 40 | 28 |
| b109391c4168 | ACT1448 | 19 | 37 |
| 045d44bc3ecc | THINK1649 | 38 | 33 |
| e29bb82e347d | ACT1816 | 18 | 45 |
| 6055310b23aa | ACT2174 | 31 | 47 |

Full hashes/spans and unchanged provenance are in `P3_SURVIVING_ACCEPTS_2025.json`.
Only209 own-span-verified entries are eligible for parent correction: among
those,17 old passes become failures and seven old failures become passes.
The other14 historical entries are diagnostic-only, never silently delivered
as the child's own verified work. Tool inbox
`04a8952f5a84794f257f24e1765489d7` is already published; its rendering in the
recovered P3 is still pending. Publication is not delivery.
