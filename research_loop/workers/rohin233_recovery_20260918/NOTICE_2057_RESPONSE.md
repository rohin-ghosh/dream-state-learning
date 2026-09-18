# September 18, 2026 — response to the 20:57 UTC watcher

## C2 and P3 restoration

C2 actually loaded at **20:53:34.695 UTC**, journal **11505**, after
WALL_EXTENDED11504. It preserves COMPLETE11502 / sleep114 / optimizer7756,
adapter, AdamW, RNG, working state and the original history. The replacement
took118 seconds from dispatch to LOAD; exit-to-LOAD downtime was
**2h25m13.274s**. First restored ACT: REQUEST11523 → RESPONSE11524 →
COMMITTED11525. That ACT is a print-wrapped claim, not a successful derivation.
The subsequent actual SLEEP_RECIPE11546 and TARGET_ELIGIBILITY11547 explicitly
show R227_ALL_AUTHENTIC_CHILD_ROWS_V1, active_semantic_filters=[], and
semantic_row_exclusion=false. A completed sleep is a separate receipt.

The parent was rebound to the actual new incarnation; the first model-parent
call was SILENT, so that alone was not claimed as parenting delivered. At
**21:00:48.715 UTC**, the authorized source-grounded correction was published
as Astra inbox **a0ff9bd81cde4285ba7a7ef6fc7ea682**: V=3, not29, quoting
the child's own RESPONSE5840 (record hash
2fb0878a206b93f92a241e58ea74830bd08b14ccfa788977a1ea4ac70dfb3074):
26+3V=35; 3V=9; V=3. This is correction with a supplied source, not unaided
recall. Exact REQUEST rendering and the correction's following ACT are tracked
in CHECKPOINT_TAIL_V_DELIVERY.json; publication alone is not uptake.

P3 native699464 **loaded at20:58:52.486 UTC**, before the21:10 replacement
condition. Actual WALL5316 / LOAD5317, optimizer6748, new bound
September25 18:00UTC. Do not kill this successful recovery or launch a duplicate.
The queued xhigh parent turn315 remains in the same inbox; a sole renewed
parent process started at20:59:23.258UTC. Post-LOAD parent/Tool rendering is
verified separately from process liveness: both parent315 and the rescoring
Tool notice rendered in REQUEST5321 at20:59:03.289UTC, followed by ACT
REQUEST5328 → RESPONSE5329 → COMMITTED5330 at21:00:57.529UTC. This establishes
delivery, not correction uptake or caption quality. Parent318 is also published.

**DEADLINES_212301.json/.md verifies all17 kept native bounds and current
incarnations at21:23:01 UTC.** It does not assert every support process or every parenting
delivery is verified. C2's bound is September20 18:00UTC, within node5's reported
allocation; node3's September24 bound does not authorize using node5 that long.

### Verified follow-through

C2's current responsive parent is **4145645/start187292176**, with actual START
at21:11:44.989UTC, one completed-response cadence and the same September20
18:00UTC bound as its child. The fleet reporter now binds that successor's START
and exact native LOAD/guard, rather than reusing the retired471781 parent and
3590563 waiter. Eleven CPU reporting regressions pass; this is a non-material
evidence repair, with no native signal or source change.

The V correction is **actually ingested as INBOX11614 and rendered in
REQUEST11617 at21:15:43.060UTC**, with all parent-history tokens masked from
learning. This is not just a queued file. The two following THINK
outputs11618/11625 still claim adequacy rather than performing the supplied
calculation. The first subsequent ACT is **REQUEST11633 → RESPONSE11635 at
21:19:40.865UTC → COMMITTED11636 → ACT-stage11637**. It prints assertions of
correctness, not arithmetic: **no math-correction uptake is demonstrated**.
Compaction11632 removed the original correction before ACT; the authenticated
provider follow-up is what rendered in REQUEST11633. An older conflicting story
request was also present, and the new parent explicitly acknowledged that
conflict. This trace is not a clean test of retention or unaided recall.
`CHECKPOINT_TAIL_PARENT_DELIVERY_FINAL.public.json` binds these separate steps.

P3's post-LOAD xhigh turn318 also rendered: **REQUEST5400 at21:12:20.587UTC →
ACT5410 at21:14:04.735UTC → COMMITTED5411**. Its first resumed sleep is durably
complete as **SLEEP_COMPLETE5396, cycle154, optimizer6796**, after48 updates.
The R227 recipe keeps all3 authenticated new rows, zero semantic exclusions.
These are delivery/training-completion receipts, not proof of useful learning.

The collector4091776 is still alive after its first successful publication;
its next scheduled cut is22:00UTC. All17 natives are verified, but the report
does not claim every support component or every life has a current parent-render
receipt. The future trusted-writer checkpoint-plus-tail path is still CPU-only
and not deployed fleet-wide; the current C2 repair avoids semantic replay but
still hashes the historical prefix. It is not a universal constant-time resume.

## Hourly collector restored

Root cause: the previous R227 hourly schedule explicitly ended
**September18 14:09:07.498UTC**; its14:00 cut was its final scheduled report.
The replacement single-owner collector started **21:02:47.779UTC**, PID4091776,
and produced and pushed **R227_HOURLY_20260918T210249Z.json/.md**, plus
**R227_FLEET_SOURCE_20260918T210249Z.json**, in commit
**2139635eeab57df994230675ac7289292313220e**. It runs immediately and each UTC
hour, through the existing latest scorer bound, September30 17:59:30UTC.
Each source's own earlier lease bound is checked before any remote query.

The source receipt binds actual scorer PID/start/command/config and each
player's adopted judge epoch. The collector never rescores, submits captions,
trains, alters lives, or adds historical/cached results to new outcomes.
The isolated publication worktree publishes only bounded aggregate artifacts.
Three hourly-projection and six epoch-count regression tests pass. A first
worktree checkout timed out; its unheld lock was preserved under a new name,
and the new worktree was repaired with sparse checkout before the successful
publication. A shell-background launch did not survive and is not reported as
live; the verified service was launched with a separate process session.

### Last full hour: 20:00–21:00 UTC, adopted judge only

| Player | ACT origins reaching scorer | Distinct scored | Accepted | New pixels |
| --- | ---: | ---: | ---: | ---: |
| Frozen base | 10 | 72 | 54 | 10 |
| Node3 observation | 12 | 0 | 0 | 0 |
| Node3 perspective | 12 | 0 | 0 | 0 |
| Node3 revision | 12 | 0 | 0 | 0 |
| Node3 selfderive | 8 | 0 | 0 | 0 |
| Node3 unparented-named arm | 12 | 0 | 0 | 0 |
| Node2 extra caption arm | 12 | 0 | 0 | 0 |
| P3 | No epoch events in this hour | — | — | — |

The five node3 forks produced56 scorer-reaching ACT origins and no new scored
strings in this hour. This is not evidence of learner improvement. The base's
54/72 acceptance is75%; acceptance is not certified humor, and new pixels are
operational game clusters, not independently verified distinct joke ideas.
Absent P3 events are not presented as proof of uptime. Parsed totals, format
faults, no-caption ACT counts and generated tokens are not in this ledger and
remain null, not fabricated zeros. Older pre-adoption hours are not reconstructed
or mixed into this table.

## R207 six-contrast counts

Wins out of100 per type, same adopted rank8 / step15625:

| Contrast | Widegap6250 historical | Retained15625 | Fresh receiving-process15625 |
| --- | ---: | ---: | ---: |
| Word shuffled | 100 | 97 | 97 |
| Scene description | 100 | 97 | 97 |
| Nonsense | 99 | 96 | 96 |
| Truncated | 94 | 93 | 95 |
| Mid-tier | 74 | 77 | 78 |
| Other contest | 51 | 90 | 90 |

Source: rohin233_ovx4_recovery_20260918/JUDGE_FRESH_CONTRAST.json and the
retained diagnostic receipts. The fresh battery used a separate receiving
process with the adopted source and artifacts, not the live game RPC;600 cases
across20 contests. The retained/fresh difference remains unexplained;
neither result is silently substituted for the other.

## P3 rescoring correction

Seven of26 old accepts survive;19 fail; seven old failures newly pass.
The seven surviving new ranks are **28,33,37,45,45,47,50**, not all45–50.
Four survivors are authenticated child spans; three remain diagnostic-only
because their original own-text spans were not authenticated. Parent-facing
facts use the209 authenticated entries:17 old passes fail and seven old
failures pass. The existing source-bound Tool inbox is
**04a8952f5a84794f257f24e1765489d7**; its recovered-child rendering is tracked,
not assumed. Rescoring is not a new opportunity and novelty was not recomputed.
