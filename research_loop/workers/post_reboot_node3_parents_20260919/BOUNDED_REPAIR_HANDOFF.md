# Bounded transport diagnosis and explicit error feedback

Non-material operational repair requested by the user on September19,2026:
preserve64MiB aggregate/32MiB individual bounds and complete ACT/THINK attribution;
do not mutate native, scorer, judge, epoch or training-target rows. No GPU work.

## Diagnosis

The existing exporter already selects the minimal contiguous window from the
latest own committed THINK response through the current ACT stage marker.
`latest_own_think` requires every intervening original record and chained hash;
`child_act` requires the original RESPONSE/COMMITTED/stage chain. Growing
COMMITTED state, CONTEXT_INPUT state and REQUEST resume state dominate the bytes.
Dropping these records, stripping their state, selecting ACT-only despite an
available THINK, resetting journals, or partitioning an oversized aggregate to
evade its bound would violate the requested contract. None is performed.

All five first failures are confirmed by local-on-node authenticated reads:

| Fork | THINK → ACT response → ACT record | Minimum bytes | Existing cap |
|---|---|---|---|
| historical unparented/currently parented | 7497 →7504 →7507 | 67,959,455 | 67,108,864 |
| revision | 7383 →7390 →7393 | 70,202,753 | 67,108,864 |
| selfderive | 6942 →6949 →6952 | 70,724,606 | 67,108,864 |
| observation | 7798 →7805 →7808 | 70,793,006 | 67,108,864 |
| perspective | 8176 →8183 →8186 | 71,076,805 | 67,108,864 |

Full authenticated record/file hashes and actual indices are authoritative in
`BOUNDED_DIAGNOSTICS.json`; the unchanged existing exporter rejects each window.
No compatible smaller contiguous transport was found. A representation/protocol
change would need separate coordination rather than silently weakening provenance.

## Scoped repair

The healthy existing node3 feedback relay deliberately skips failures lacking a
scorer receipt. Its behavior and process remain untouched. The new complementary
`report_transport_errors.py` only handles confirmed pre-dispatch bound failures,
cross-checking the exact VM transport file, native incarnation, response, native
ACT record, hash chain and actual minimum byte count. It uses the existing `_inbox`
publisher with speaker Tool and actor environment. Operational projections have a
distinct schema and explicitly set `scorer_receipt=false`; no fake score, rank,
acceptance decision or zero is emitted. Successful/scorer-receipted outcomes remain
exclusively owned by the original relay. Historical ACTs are not rescored/replayed.

Publication is immutable and idempotent by exact failed-origin evidence; an
interrupted acknowledgment recovers the already-published inbox rather than
duplicating it. Only Tool context is added, not native targets or training-row
filters. The original deadline1790272760 (September24 17:59:20UTC) applies.
Nine new CPU regressions pass, including deleting every intermediate record,
foreign/tampered source rejection, unchanged bound rejection, ambiguous-dispatch
rejection and duplicate-publication recovery. Existing components remain live.

Foreground command for Main/Averroes:

```
/usr/bin/python3 -B -u /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_node3_parents_20260919/report_transport_errors.py
```

Singleton `locks/OPERATIONAL_ERRORS.lock`. Actual publication/INBOX proof belongs
in `OPERATIONAL_ERRORS_LATEST.json`; startup is not evidence of delivered feedback.
Do not restart425470,330973,1970178,1973233/1973234 or any native/scorer for this repair.

## Exact first delivered operational failure

Revision's natural export failed at **01:28:38.960455UTC**:
RESPONSE7390 → native ACT7393, confirmed `ORIGIN_TRANSPORT_NOT_DISPATCHED`.
The operational Tool notice was published **01:38:37.613270UTC**, ID
`7ed4e546ca3f4bc3a3fd04d23334bba2`, publication SHA256
`f90aef2abec2978d89eaa095b8e11b0c08ab85d108535d2003a4d34b9bfc6fc5`.
Native **INBOX7530** has record SHA256
`83feda389b223c19a3789b12f2639b3c0f9f561827586c5644f170b0b5a80b7f`.
The exact text appears in **REQUEST7532**, started **01:38:49.982183UTC**, with
`all_history_tokens_masked=true`. This proves operational-error delivery, not
judge execution, ranking, zero scoring, task uptake, or learning.

Immutable proof: `FIRST_OPERATIONAL_ERROR_RECEIPT.json` and
`FIRST_OPERATIONAL_ERROR_RENDER.json`. All five initial failures have actual Tool
publications; consumption for other forks was still pending at this first cut.
The supplementary CPU reporter is459421/start1006370 on VM boot
80d71f45-6f0c-4479-b0e5-77a9611c793e, started01:38:29.395381UTC. It leaves the
existing caption parent, transport, scorer, Tool relay and native processes intact.

**26 worker CPU tests pass** in `BOUNDED_REPAIR_TESTS.txt`. Inherited pytest tests
could not run because the host Python has no pytest; no packages were installed.
The tests explicitly show every original record is required and an oversized
window remains rejected. The actual64MiB export problem remains unresolved under
the unchanged protocol; the repaired behavior is explicit, authenticated error
feedback rather than silence.

Main/Averroes: `OPERATIONAL_ERRORS_SUPERVISOR_ENTRY.json` is the exact source/lease-
bound adoption candidate for `node3-operational-errors`. It uses the existing
supervisor's `parent` category solely for a CPU Tool relay, not a model provider.
Adopt459421 without signals; no OS boot installation or additional native action.
This is a shared-repository handoff, not a claim of direct message acknowledgment.
