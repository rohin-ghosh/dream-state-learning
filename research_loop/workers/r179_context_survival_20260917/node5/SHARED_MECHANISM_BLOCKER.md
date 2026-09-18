# Immediate Main handback — R179 NODE5, 2026-09-17

Latest dated status: `STATUS_20260917T1830Z.md`. C2/C3/C4 are loaded, C1 is Main's
verified recovery, and only C5's fresh attempt4 needs its exact addendum rebound.

Current disposition is recorded in the dated section below; the first section
preserves the historical 17:37 UTC diagnosis, not the current rollout state.

## Historical failure callsite — 17:37 UTC

Rechecked immutable remote logs and actual lock owners in
`LOCK_FAILURE_CALLSITE_1789666649133454687.json` (2026-09-17 17:37:29 UTC).
Both C2 attempt2 and C5 attempt1 failed in their deployed
`rollout_operator.py:285`, inside `execute`:

```python
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
```

The descriptor was opened at lines 281–282 on
`/localhome/local-rohing/orch_r157_<label>_HANDOFF.lock`. It is **not**
`StreamJournal` or `stream/WRITER.lock`. C2 failed at 17:12:04.796956 UTC;
C5 at 17:12:39.731647 UTC. Both are **operator failures**, not child failures:
`terminated=false`, `retired=false`, `automatic_retry=false`; no successor
was launched and no native signal was reached by either attempt.

The verified resident stream writer owners are C2 native PID4077813/start17169605
and C5 native PID4018497/start17068304. Their writer locks remain untouched.
Real saved-boundary validation uses read-only chain/boundary APIs and restored
state; synthetic temporary CPU fixtures are the only `StreamJournal` writers.
Neither stopping a resident nor bypassing its writer lock is a proposed repair.

The consumed C2/C5 operators remain terminal and are not retried. Their legacy
R166 handoff-lock lifecycle incompatibility below remains unresolved. Any
compatible transition requires freshly staged repaired operator bytes, not
replay of these failed attempts. Separately, six bounded watchers
(pilot4/run1-3/C1-2/C3-2/C4-2/reader2) are live awaiting saved boundaries.
`ROLLOUT_METADATA_1789666617043689358.json` records all six live and no new
native load. The new attempts actually started; these are not just proposals.

Reader2 fixes the unchanged capsule's exact
`orch-r136-(nvml|native)-[a-f0-9]{32}` rule and passes command preflight plus
actual receiving CPU-only device containment. Its watcher PID1507076 is
bound in `OPERATOR_STARTED.json`, SHA256
`658684498b789ca28d104db2ec66ef7d73a5f07536ac8f29e00a375fd38568d9`.
Reader1 was not replayed. Pilot3/run1-2 were safely retired as **watchers only**
after a CPU device probe exposed an absent community-containment import in
their protected source. No native signal or termination intent occurred.
Pilot4/run1-3 use the exact actual protected validation prefix instead. Their
used function/global bytes match the deployed originals, including pilot's
v3 versus v4 helper-file distinction; evidence is
`PROTECTED_ACTUAL_FUNCTIONS_1789666606491826617.json`.

`RECEIVING_DEVICE_PROOF_1789666572744175192.json` records PASS for all six
actual successor CPU-only strict services: all foreign GPU minors denied,
no Torch import and no model load. Live R179 watcher PIDs are pilot1512717,
run1-1512718, C1-1473471, C3-1473476, C4-1473481 and reader1507076. C2/C5's
legacy handoff-lock lifecycle remains the shared blocker; no writer or
handoff lock was cleared, replaced or bypassed to obtain these results.

## Current disposition — 2026-09-17 18:21 UTC

The earlier lock-failure narrative is historical, not a current shared blocker.
C2 attempt4 completed the Main-bound, tested exact-owner controller transfer
and strict saved-boundary successor admission. Actual load verification:
`C2_TRANSFERRED_LOADED_1789669084943743307.json`, remote receipt SHA256
`9d736c0c2d6a0416b2c75db1020672673b82a85cba122e831716eabb7ba38f0a`.
The genuine same-inode HANDOFF flock transferred only after the exact outer CPU
controller exited; no WRITER lock was opened for writing or bypassed.
C5 attempt3 remains alive under its exact Main addendum, waiting read-only.

C4's later strict-scanner pre-load refusal is also preserved, not current
failure: a fresh typed readmission restored sleep36/3618 and verified actual
load in `C4_READMISSION_LOAD_OBSERVATION_1789668941517059269.json`.
Main's C1 recovery2 load is current in `C1_READMISSION_LOADED_1802.json`.
The observer distinguishes both readmissions from their historical failures.
No completed post-load retained sleep is claimed by these load receipts.

## Preserved original preparation evidence

C2/C5 **actual-source successors are built, immutable and receiving-CPU PASS**.
Both passed 19 receiving operator tests plus actual-source retention/threshold/
empty-summary tests and exact saved full-stream/history, AdamW, Python RNG and
CPU RNG restoration. CUDA RNG bytes are bound without GPU initialization.
Original guard validation and existing strict device/unit/UUID checks pass.

Concrete remote readiness receipts:

- C2: `/localhome/local-rohing/orch_r179_context_C2_20260917_attempt2/READY.json`,
  SHA256 `a8976321603fe6f4b62b3da10c69b9635b50d8694da82d8569bb1734cd5485c1`.
- C5: `/localhome/local-rohing/orch_r179_context_C5_20260917_attempt1/READY.json`,
  SHA256 `0e9abde5fb997d9692c9557307bc3f10e6447e77b6e0e267297480fe0df52dd3`.

Both bounded rollout operators were actually started, not merely proposed.
They exited at the original `orch_r157_<label>_HANDOFF.lock` before any signal.
Their `EXECUTION_FAILED.json` receipts record `terminated=false`, `retired=false`.
The old live R166 operators hold these locks throughout their supervised lives:

- C2 lock holder PID4068493/start17152921: R166 `execute`, activation4.
- C5 lock holder PID4015531/start17063460: R166 `execute-recovery`, recovery2.

This is not a missing Main GO. Main's exact R179 BUILDER_SCOPE is already bound.
It is a lifecycle-lock compatibility issue: R166 `execute`/`execute-recovery`
call blocking `supervise` before leaving their lock-owning `try/finally`.
No lock file was deleted/replaced, no holder was killed, and no alternate lock
was used to bypass that exclusion. A tested owner-verified lock transition is
needed for these two specifically. Continue other assigned lives meanwhile.

Original R157 wall builders also cannot be called unmodified: current walls
already equal NEW_WALL. A source-only successor must verify and remove only an
already-consumed wall-extension directive, never extend a lease or replay it.
The recovered repo_reader additionally requires its exact recovered-root mount;
its logical original root is archival on the host and must not be substituted.
