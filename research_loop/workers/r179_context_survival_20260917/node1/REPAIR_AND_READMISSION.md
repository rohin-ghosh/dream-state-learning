# R179 NODE1 execution repair and concrete admission blocker

## Preserved attempt1 defect

Attempt1 lane4 safely aborted before retirement at Unix `1789665554.0324495`:
`readout_drain_deadline_original_resumes`. The native dispatch marker is written
**before** resident offload and readout subprocess creation. Pausing on dispatch
alone can prevent the child from starting. This is an actual observed race, not
a hypothetical controller-readiness inference from CPU tests.

The independent actor-resume watchdog restored the original. There was no
retirement or reset. Exact CPU watchers on lanes 2/3/5/6 were cancelled after
PID/start-tick/argv/UID binding; learner signals were not sent by that cancellation.
Receipt: `WATCHER_CANCEL_FOR_RACE_REPAIR_1.json`. Attempt1 remote artifacts and
local exact source copies in `attempt1_source/` remain preserved.

Attempt2 repairs the gate using the R157 pattern: require the real owned readout
`REQUEST.json`, exact parent/plan/checkpoint/UUID metadata and independently
started child identity (or completed child) before pausing. Merely published
dispatch cannot satisfy it. The bounded independent watchdog is 900 seconds,
and boundary watchers have a 5400-second limit under unchanged life walls.

- Operator SHA: `fc960529e505d79e66ec92715535f770fc22a717210ec91c9dcfe0aea5775a87`.
- Tests SHA: `6fa2ea080b857f91eaaeb58ed0cfdbcf24adb54b237105fc6421453862b85205`.
- Thirteen CPU tests pass, including dispatch-without-child rejection and
  readiness-before-pause ordering. All five actual immutable successor sources
  again pass three receiving behavior checks each in their actual A100 process.
- Remote root: `/localhome/local-rohing/orch_r179_node1_20260917_attempt2`.

## Actual lane4 saved-state retirement and denial

Lane4 reached sleep41 and optimizer step4428. The current saved stream envelope
SHA is `7432e7356f129dfcbe61a28b36361f4eb95177ff821982fa44c47841f734a308`.
Actual receiving CPU restored that whole envelope exactly, including history,
active view, frontiers, adapter, AdamW and RNG provenance; no CUDA initialization.
It preserved 493,429,824 bytes of stream/history and 242,661,734 bytes of complete
checkpoint data, then verified the owned readout had finished and exited.

- `BOUNDARY_RECEIVING_CPU.json` SHA:
  `92b3999d77e8dbbf61c0db3d81dc3102c4314457f4d46d2a72d9d9fb93de3c8a`.
- `BOUNDARY.json` SHA:
  `8fafe5a80077f3c41f0a828e874e557753bc3fafbdcdf31a019a48565a32f0cc`.
- `RETIRED.json` SHA:
  `63430e928934b148bb78cd57884b96a9d5f06fff12b8dd49040fc5d63bf3d65f`.
- Actual original actor/timer/supervisor exited at Unix `1789665788.956909`.

The unchanged privileged guard then rejected admission solely for
`process_identity_drift:1371459`. Denial SHA:
`bf250b4874d451a4700d32a96ee392f6185eea9d1acf82352d61ec87d6b45958`.
Scanner EUID was0; target UUID is `GPU-31583768-d90f-520c-51ed-5dac761526d0`.
There was no LAUNCH, native log, admission-time or containment receipt. The drift
PID was absent and failed supervisor1372203 was a zombie at observation Unix
`1789665943.5808158`. This concrete shared admission-race blocker was immediately
reported to Main. CPU success was not misreported as successor load.

## Explicit fresh guarded readmission

`readmit_node1.py` creates one new `lanes/lane4/readmission1` control namespace,
never overwriting the denial/attempt or retrying a consumed model call. It
requires exclusively privileged identity-drift reasons, all those PIDs gone,
no native/containment/admission launch evidence, all old owners gone, failed
supervisor not live, the exact unconsumed saved boundary and source closures,
and full checkpoint/AdamW/RNG/history revalidation. It cancels only the proven
old CPU observer and acquires its original per-life lock.

Only attempt-directory and unique containment-unit identity change in GUARD;
PLAN/source/lease/allocation/admission policy remain unchanged. The existing
privileged scanner and seven-foreign-device confinement run again without
exceptions. A second rejection produces an explicit DENIED receipt, not a loop.

- Readmission helper SHA:
  `2bd1dbcde9e790c92a67d7b5e017e1b3fbc40c2449eb98585facea8d990601c3`.
- Tests SHA: `37cbc7b9c4e8c0c438b88cb1cceeb5a7ea490c085e0e1cd0bbea9d4a5b7c27f0`.
- Four CPU tests pass, including refusal of real device holders and any prior
  native/containment launch. Actual CPU receipt SHA:
  `f8b9c52af5ab2b3509750f331edea93388c03d944abd1503bff4c351ea7926e6`.
- Helper dispatch PID1417984; local evidence:
  `READMISSION_DISPATCH_1789666109759539212.json`.

Status remains determined by subsequent actual receipts, not this dispatch.
No first-load, first-new-generation or context-retained completed-sleep claim
is made without those actual observations. Lanes 2/3/5/6 remain independent
saved-boundary watchers; lane7 remains verified no-op. No COORDINATION edits.
