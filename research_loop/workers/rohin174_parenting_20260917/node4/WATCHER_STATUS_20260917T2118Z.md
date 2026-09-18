# Main / watcher: NODE4, September 17 at 14:18 PDT

V2 exclusion is acknowledged and pinned to
`be536327a062b1e104f76e3adfae4b6957e71dc932bce1768b21677348acbf6f`.
The raw control remains `UNPARENTED_CONTROL_EXCLUDED`: no H operator, baseline,
republish, delivery recovery, peer, or R175 parent-arm retirement enrollment.
Its historical H publication is withdrawn before ingestion, not pending.

| Life / physical | Active arm | New PUB / rendered | Actual pending blocker |
| --- | --- | --- | --- |
| kernel0 / 0 | B/2 | 2 / 1 | Second publication `60e48df47d544f9cad77e6b61b13d1d9` awaits a later TRAIN REQUEST; do not duplicate baseline |
| raw_parented / 3 | D/3 | 0 / 0 | Predecessor publication `9916a18a66894d6498d60dce8c8c738b`, source response123, still awaits rendering |
| kernel_parented / 4 | A/1 | 0 / 0 | Predecessor publication `2219001390244860ad944082f8c0e367`, source response120, still awaits rendering |
| raw_unparented / 1 | Excluded control | 0 active / 0 | None: H remains OFF; one historical message was withdrawn by Main |

The three TRAIN snapshots are caught up; these are actual pending-publication
guards, not permission waits or reasons for another corrective/provider call.
Their parent processes remain alive: B489577, D489578, A489576. No new dispatch,
fallback, manual publication or source mutation was performed for this update.

## First delivery and sleep clock

Kernel0's first verified R175 delivery remains
`612cb544b9344a23b3d9a789333e3f23`, REQUEST4813 / request ordinal122.
The exact record's `started_unix=1789678810.6808615` corresponds to
**September 17, 2026, 14:00:10.680862 PDT**. The reported14:01:02 is not the
REQUEST timestamp in this bound receipt; it must not create another exposure
or justify a fallback. Its completed-sleep baseline is40; targets remain43/44.
Zero completed sleeps after that first exposure are currently verified.

## Current work and environment gap

All four unchanged native identities are alive and doing work. At14:18:15–17
PDT, each records increasing CPU ticks; latest TRAIN journal heads are UPDATE
records: kernel0=4830, raw control=5054, raw_parented=4918,
kernel_parented=4713. Exact native PIDs:653202,294158,259097,310254.
This is ongoing native work, not a claim of completed sleep or scientific
retention. Existing R179 retained-sleep/post-sleep proof monitors remain alive.

Environment blocker remains concrete: no bound executor/tool manifest in these
actual native plans, and the bounded known-service scan finds no active
R132/R141/R148/R155/R158 execution service. No executor result is fabricated.
Context16384 / generation512 / two segments per sleep / 16 new plus one
rehearsal presentation remain unchanged. No code caps were raised, no tool or
peer channel was connected, and no judge/Qwen/profile allocation was reused.

## Evidence

- `V2_CURRENT_OPERATIONS_1789679897247449468.json`: exact V2/withdrawal binding,
  current delivery receipt and fresh native identity/work samples.
- `PENDING_BLOCKERS_1789679842728598077.json`: exact pending IDs, source clocks,
  predecessor/result references and caught-up snapshot hashes.
- `LIVE_RECEIPTS_AFTER_WITHDRAWAL_20260917T2109Z/`: current per-life receipt
  stream, read-only watcher552074;90-minute bound, unchanged wall clamp.

Main's withdrawal receipt continues to override the historical H PUBLISHED
result. All former attempts and immutable parent bundles remain preserved.
