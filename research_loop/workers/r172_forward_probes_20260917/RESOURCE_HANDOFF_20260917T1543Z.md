# Resource-only R159 / Main handoff — September 17, 2026, 08:43 PDT

No evaluation text, maps, scores, or outcomes are released here.

## R167 observed release, not a new admission

- At **15:34:45 UTC / 08:34:45 PDT**, 290 recorded ownership identities were checked: **0 live**, 0 additional same-UID processes matching the old root, 0 reservations without terminal records, and no unresolved ownership metadata or missing controller-launch records. No signals were sent.
- Evidence: `preparation1/RECEIVER_RESOURCE_OBSERVATION_01.json`, SHA256 `5c27077869a25bc408d9dd228fe62fae2ca78ec55eadba353a0ac80bc499c336`. This is release evidence for the inspected old handles, **not fresh strict-device admission or execution GO**.
- Latest completed-count observation is **15:29:03 UTC / 08:29:03 PDT**, not a post-wall recount: **71 completed condition jobs / 213 charged calls**, including **34 forward condition jobs / 102 calls**; 0 failed jobs, 71 released jobs, 0 unresolved attempts in that observation. Source: `../r167_object_survival/fleet_generation2/takeover_monitor1/0082.json`. The local monitor ended at 15:30 UTC.
- The separate post-wall counts observation failed its bounded metadata assertion; its 1 MiB reservation and failure remain preserved in `preparation1/wrapper_operations/R167_postwall_counts1/`. It produced no count receipt and was not retried. Do not represent the 15:29 counts as freshly recounted after the wall.

## R172 implementation / Rawls coordination

- Preparation only: **22 freshly enrolled / 24 roster lives**; C5 held pending exact recovery-release witness, repo_reader held for missing original initial adapter at the declared root. Their holds do not block the other 22 preparations.
- Four bounded source-capture workers launched at 15:33:15–19 UTC. Launch identities: `preparation1/capture_launches/{a100,ovx2,ovx3,a40r}.json`. This statement is a launch receipt, not a fresh liveness observation.
- **72 local CPU tests pass** in `PREPARATION_CPU_04.txt` for source preparation, capture/transfer primitives and existing queue checks. New runner/scheduler are unfinished and not covered by that passing receipt. No new GPU/model/provider calls are authorized or launched.
- Rawls (`01a0b004-e818-73d3-96e7-6f0447428d3e`) owns independent review in `REVIEW_FORWARD.md`; author handoff will identify exact repaired source hashes and actual receiving CPU evidence. Known blocking join: runner checkpoint verification must use the unchanged native verifier before model loading.
- Pending: receiving transfer/controller and actual receiving CPU, private rubric freeze, receiver-resolvable same-byte custody/allocation bindings, independent bound approval, fresh strict admission, and Main's separate no-reset execution GO. No GPU ETA is asserted; 19:30 UTC remains the absolute reserved ceiling.
- No change to R167, COORDINATION, R170/R174, budgets, leases, or sealed R159 reporting.
