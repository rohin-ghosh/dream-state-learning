# P3 xhigh parent — Main / Averroes handoff

## Final bounded cut — September19, 2026 01:30:14 UTC

**P3 MODEL parent is alive, unchanged xhigh, phase AWAITING_RENDER.** Four actual
post-reboot provider attempts: **2 published, 1 intentional SILENT, 1 HTTP429
failure**. Exactly **1 fresh publication has verified REQUEST delivery and a
committed ACT chain**; these are unique-publication counts, not counts of repeated
context appearances. Do not wait for three fresh ACTs or restart for evidence.

| Attempt | Publication RESULT UTC | First exact REQUEST UTC | ACT REQUEST UTC | Committed ACT response UTC |
|---|---|---|---|---|
|374|01:14:03.351945|6925 at01:25:50.373796|6932 at01:26:46.843450|6933 at01:27:23.892878|
|377|01:28:06.925864|Not observed|Not observed|Not observed|

374's ACT is bound to COMMITTED6934 and R184_STAGE6935, original publication
`0e2ffa3c8fa54413b454119b1b5e648b`, and the literal attributed provider text in the
masked ACT REQUEST. 377 publication is `3e62442a438d4745985c7075d0601d45` and remains
behind the existing render gate. Attempt376 intentionally returned SILENT.

**Current supervisor is399392/start891869**, not the earlier311614. A strict
recheck detected the old PID absent, then verified the replacement's actual
boot/start/command, fresh heartbeat and exact supervisor flock. P3 registration
remains valid and its original lock is still held by346649; no parent restart
occurred. This worker did not start or restart either supervisor. OS boot
installation is still blocked/uninstalled.

Concrete evidence: `FINAL_RECEIPT.json`, `FRESH_PROVIDER_REQUEST_ACT.json`,
`LAST3_PROVIDER_REQUEST_ACT.json`, `PROVIDER_429_RECEIPT.json`,
`VERIFIED_PROCESS.json`, `SUPERVISOR_OBSERVED.json`, `DUPLICATE_REFUSAL.json`.
Last-three publication rows now338/374/377:338 is explicitly September18
historical,374 is fresh delivered,377 is fresh pending. Tests remain18scoped+1
original. The existing strong parent and supervisor registration remain live;
the bounded read-only proof watcher completed and starts nothing further.

Pending:377 render/ACT, platform-authorized boot installation, and any separately
assigned semantic review. Exposure is not uptake, retention or rollout evidence.

Only P3; C2/P7 remain Main's. This is a non-material CPU service restoration,
not a native restart, retention rollout or semantic promotion.

## Current exact owner

PID **346649**, start tick **795156**, VM boot
`80d71f45-6f0c-4479-b0e5-77a9611c793e`, started September19 **01:03:17 UTC**.
Actual argv:

```text
/usr/bin/python3 -B /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_p3_parent_20260919/runner.py
```

`status.py` checks current `/proc`, command SHA and both exact kernel flocks,
not a historical STARTED file. `VERIFIED_PROCESS.json` is its timestamped result.
Native699464/start33078516 and its actual guard/LOADED5317 remain unchanged.

## Actual post-reboot provider result

- Attempt373 dispatched September19 **01:12:14.912081 UTC**, failed HTTP429.
  The preserved604-byte provider error body mentions TPM. This is a failure,
  never a delivered turn. The boundary was consumed, never retried.
- Backoff ran until **01:13:15.883248 UTC**. Attempt374 was a distinct eligible
  boundary dispatched **01:13:17.641363 UTC**, after the cooldown.
- Attempt374's actual API request and completed response both identify
  `openai/openai/gpt-6-astra`; actual request reasoning is **xhigh**. Provider
  response file observed **01:14:02.322938 UTC**; original ledger publication
  RESULT observed **01:14:03.351945 UTC**, ID
  `0e2ffa3c8fa54413b454119b1b5e648b`.
- At the **01:17:40 UTC** read-only trace, this publication had not yet appeared
  in an exact canonical REQUEST/ACT. Do not claim fresh ACT from historical
  turns335/338. Check the current `LAST3_PROVIDER_REQUEST_ACT.json` and append-only
  `receipts/LAST3_*.json` for a later completed chain.

## Registration and restart semantics

`register.py` validates one P3 manifest against Averroes's existing supervisor
schema, requires the exact current parent plus its occupied original lock, then
atomically installs only `services.d/p3-parent.json` without replacing a
conflicting registration. `SUPERVISOR_ENTRY.json` is the same non-secret entry.
No parent or supervisor process is restarted by registration.

The existing parent does not have the new restart-entry argv. Therefore the
initial supervisor status should be **EXISTING_SINGLETON_LOCK_HELD_NO_LAUNCH**,
not argv-adopted. This is intentional: the original parent lock protects the
real current owner. Exact liveness/lock ownership is independently verified by
`status.py`. When that owner is absent and the lock is free, the supervisor may
run this restart argv:

```text
/usr/bin/python3 -B /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_p3_parent_20260919/restart.py
```

The restart entry stays foreground, validates source pins and prior ledger/seed,
archives prior receipts, runs a new native/guard/LOADED/source/ledger preflight,
then **execs** the pinned original runner in the same PID. No detached subprocess
or native process is started. The supervisor reports
**OWNED_PROCESS_COMMAND_CHANGED_NO_DUPLICATE** after that intentional exec and
still owns that exact local PID. Unfinished attempts, changed binding, missing
credential, changed source, live owner or expired lease fail closed. No uncertain
publication is retried. Existing429 cooldown is preserved across restarts.

Credential resolution is inherited runtime environment only. The current
supervisor's provider credential presence was checked as a boolean, never copied
or displayed. Both entry and original parent stop at the existing
**September25, 2026 18:00 UTC** horizon. Automatic boot installation remains
**BLOCKED_UNINSTALLED / boot_enabled=false**; registry reload/restart is not proof
of OS boot persistence. No service-management workarounds are attempted.

## Validation

**18 scoped regressions +1 original parent-context test pass**. Tests cover429
pacing, untouched gates/model/effort, exact attributed parent text, historical
versus fresh status, current boot/PID checks, duplicate refusal, same-PID exec,
preflight failure sanitization and registration conflict refusal.

Registration observed at **01:18:59.901127 UTC**: exact live supervisor311614,
start717203, same VM boot, fresh heartbeat01:18:54.147408. P3 status is
**EXISTING_SINGLETON_LOCK_HELD_NO_LAUNCH** and the original lock is owned by
parent346649. `SUPERVISOR_OBSERVED.json` records the manifest hash and both
actual identities. A real duplicate `restart.py` invocation returned75 without
changing PROCESS/PREFLIGHT/prior ledger pins (`DUPLICATE_REFUSAL.json`).

The earlier pending374 observation is now resolved by the final cut above.
Delivery/exposure does not establish semantic uptake,
retention, learning quality or a rollout. Caption collector, correction observer,
other parents, natives, GPU runs and private sealed scores remain untouched.
