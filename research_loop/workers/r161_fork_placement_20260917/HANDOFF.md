# R161 placement: two currently free node3 slots

Read-only audit September 17, 2026, 06:08–06:11 UTC. No GPU probe/model
load, remote file writes/copies, reservation, signal, restart or service change.
No sealed scores read. No other node was queried.

## Concrete placement

Host **[REDACTED_HOST]**, wrapper `gpu/ovx2_ssh.sh`, UID/GID2524.
Host SHA256 `3e10ebcb89f013079c1e088fa82820188b1a805b879ebb85a7ffeb689e7b86e9`.
Boot ID `589725e3-0bcb-4427-83b3-8ead5cbc1e9a`.

| Priority | Physical/minor | Historical lane | Exact UUID | Current evidence |
|---|---|---|---|---|
| First serial packet-fit comparison | 5/5 | creative_none | GPU-bc211959-642d-664b-3581-42a0dbe434e9 | 1 MiB / 46068 MiB; 0% utilization; no target compute process; privileged guard clear 06:10:14 UTC |
| Optional second slot | 6/6 | support_none | GPU-1a83d900-1e95-c7b4-9b12-8117399697f8 | 1 MiB / 46068 MiB; 0% utilization; no target compute process; privileged guard clear 06:10:15 UTC |

All other node3 slots showed compute occupancy. Both candidate device FDs were
held only by verified `nvidia-persistenced` PID2725, UID127, starttick1396;
no unverified owner/learner held either target device. This is point-in-time
availability, not an R161 allocation or future admission guarantee.

## Explicit existing budget, not inferred booking

Both original guards/plan bindings and the actual unchanged remote receipt give:

- **Hard wall: September 17, 2026, 18:00 UTC**, unix1789668000.
- **Runtime lease ceiling / next-reserved bound: September 18, 2026, 00:00 UTC**, unix1789689600.
- Receipt: `/localhome/local-rohing/orch_r118_node3_7_grid_20260915_attempt1/lease_budget_r119_learned/LEASE_BUDGET.json`.
- SHA256 `919e9fb3f9cfd6cadb57af90844319e50eb114068eb52cd75aa3ab715f9c3770`.

This is an R119 author-generated runtime-budget receipt, not independent provider
booking evidence. The wrapper says “lease to 2026-09-19” but supplies neither
an exact time nor a booking reference. **No provider reservation was verified
in this bounded trace. Do not promote the wrapper comment into a longer budget.**
The conservative candidate window is before the bound September17 18:00UTC
hard wall (about 11h50m after this observation), with new scoped admission.

## Exact guard/source/service paths

Physical5 original config:
`/localhome/local-rohing/orch_r144_node3_target_r145_5_20260916t1650z/GUARD.json`

Physical6 original config:
`/localhome/local-rohing/orch_r144_node3_target_r145_6_20260916t1650z_readmit1/GUARD.json`

Corresponding immutable sources:
- `/localhome/local-rohing/orch_r145_combined_targets_20260916t1645z_2/physical5/source`
- `/localhome/local-rohing/orch_r145_combined_targets_20260916t1645z_2/physical6/source`

Each has `gpu/orch_r125_continual_guard.py` SHA256
`4be0fd5ac06bf447e9ae425ad940efbd203a1d6c3cfb88ad8b4dec0db449bea3`,
and `gpu/orch_r133_node3_programmes.py` containment helper SHA256
`9f78c7983e4cc0c6142f9500ee0f95af2878120639db4557074a932742373e0c`.
These files are mode0444 and bound by each guard. R136 node1 launcher is absent
from these historical closures; do not assume its availability or import it
from an unpinned workspace. The node3 helper is historically host/lane scoped,
not a turnkey R161 native implementation.

Actual root-EUID guard scans succeeded using existing SERVICE_IDENTITY files;
no receipt-creation branch was needed. Existing R110/R111 reconciliation reports
retain original mixed process-drift reasons plus observations; the established
scanner reconciled argv-only non-GPU drift. This audit did not remove reasons,
patch the scanner, or issue a new launch-clear receipt.

Systemd255, cgroupv2, `/usr/bin/systemd-run`, and noninteractive sudo availability
confirmed. Existing retired units show MainPID0, no ControlGroup, failed state
(not running), User/Group2524, DevicePolicy=strict, and exactly one NVIDIA minor
plus control/UVM and standard devices. Historical CONTAINMENT_VERIFIED receipts
record denial of every foreign GPU minor. Persistence service is active.
No new strict-device service or open-device test was run: future R161 containment
must still verify its own fresh exact unit/config and foreign-device denial.

## Evidence and handoff

`PLACEMENT.json` contains exact config/source/lease/release paths, current owner
metadata, scan times and hashes of supporting local metadata receipts.
`PRIVILEGED_SCANS.json` preserves the existing scanner's reasons/reconciliation
metadata; process arguments are represented by hashes rather than raw text.
`STRICT_SERVICE_PROVENANCE.json` preserves actual unit properties and historical
containment receipts. `GUARD_PROVENANCE.json` records exact config/source pins.

Initial nvidia-smi query rejected unsupported `minor_number`; preserved in
`NODE3_INITIAL_METADATA.txt`. Corrected read-only query and kernel
`/proc/driver/nvidia/gpus/*/information` supplied the actual minor mapping.
Neither historical root is reused, resumed or modified. Main may select5 for
serial learning/frozen/unparented comparison and6 for a second serial worker;
selection here does not claim reservation or authorize a launch.
