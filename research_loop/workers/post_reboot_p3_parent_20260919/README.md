# P3 xhigh MODEL-parent reboot recovery

**Final cut: September19, 2026 01:30:14 UTC.** Parent346649 is alive, unchanged
model/xhigh, awaiting render of377. Four fresh provider attempts produced2 model
publications,1 intentional silent response and1 failed HTTP429. One fresh
publication374 has exact REQUEST6925 at01:25:50.373796, ACT REQUEST6932
at01:26:46.843450, ACT response6933 at01:27:23.892878, COMMITTED6934 and
R184_STAGE6935. 377 published01:28:06.925864 but its REQUEST/ACT is still pending.
No historical chain is counted fresh, and exposure is not semantic uptake.

Use `FINAL_RECEIPT.json`, `FRESH_PROVIDER_REQUEST_ACT.json` and
`TO_MAIN_AND_AVERROES.md` for the completed handoff. Current supervisor399392 was
freshly re-bound after the earlier311614 exited; both current singleton owners
are kernel-verified in `SUPERVISOR_OBSERVED.json`. No evidence-only native,
supervisor or parent start occurred. Existing parent/supervision continue; the
bounded receipt watch completed.18scoped+1original tests pass; boot installation
remains blocked/uninstalled. The sections below preserve the recovery chronology.

## Scope and identity

Non-material restoration under `INTAKE.md`, not a new parent treatment. Only P3
MODEL parenting is restored. Native699464/start33078516, actual current guard,
same journal and canonical LOADED5317 were freshly checked using the existing
receiving endpoint. C2/P7 belong to Main. Caption collection, native processes,
GPU launches, training policy, retention rollout and sealed scores are untouched.

The old VM model parent4071384/start187218132 is absent after the VM reboot at
**September 18, 2026 22:50:45 UTC**. Its original parent lock was free. The
surviving node4 processes include P3 `feedback_recovery.py` PID458401 and
`lease_bridge` processes428814/570041, not this xhigh model-parent runtime.

Restored process: **PID346649/start795156**, started **September 19 01:03:17 UTC**,
local boot `80d71f45-6f0c-4479-b0e5-77a9611c793e`. Check the timestamped
`VERIFIED_PROCESS.json` for current liveness, exact command hash and both kernel
lock owners. A stale STARTED/PROCESS file is not proof of current liveness.
`status.py` verifies the original seed and all **1016 prior attempt files** remain
unchanged. All 138 earlier attempts, including the explicitly reconciled
historical uncertain publication, remain preserved.

## Existing contracts preserved

- Exact original `p3_retry_parent.py` manifest/source pins and P3 retry endpoint.
- Existing `openai/openai/gpt-6-astra`, effective reasoning **xhigh**; no model
  substitution or reasoning downgrade. The original wrapper maps historical
  configuration effort to xhigh; actual API request bytes are checked again.
- Same original `r210_parent3` ledger, seed, publication lock, render gate,
  caught-up gate, validation, cadence-one boundary and source continuity checks.
- No new opener/static turn, publication retry, native relaunch or native signal.
- Existing hard end **September 25, 2026 18:00 UTC**, not a lease extension.
- Read-only aliases in this directory let the unchanged entrypoint use its exact
  original manifest while new transport logs stay here. Do not edit through
  those links. Only normal parent ledger/inbox/cursor runtime writes occur outside
  this new source/receipt scope, as required to reuse the existing parent.

The recovery wrapper adds only boot-bound process observation and provider429
backoff. It honors Retry-After seconds/HTTP dates, otherwise waits at least60
seconds with bounded exponential delay to300 seconds. Longer provider backoff
is not shortened. A429 remains a failed original attempt; no same-boundary or
publication retry occurs. Subsequent eligible provider boundaries wait without
disabling any gate. `operator/RATE_LIMIT.json` survives supervisor restarts.

## Verified last-three chains at initial recovery

`LAST3_PROVIDER_REQUEST_ACT.json` binds each original source snapshot, actual
xhigh API request, completed provider response, exact output message, publication
intent/result, canonical inbox bytes, literal parent render in TRAIN REQUEST,
and a real committed ACT with its stage receipt. No child-output excerpt or raw
parent/provider text is copied here. Record times are journal-file mtimes.

| Attempt | Model publication UTC Sep18 | First exact REQUEST UTC Sep18 | Committed ACT response UTC Sep18 |
|---|---|---|---|
| 332 | 22:06:03.916295 | 22:18:23.118183 | 22:19:53.614560 |
| 335 | 22:21:11.796926 | 22:31:58.046471 | 22:33:29.048202 |
| 338 | 22:34:51.462028 | 22:45:30.825321 | 22:47:02.040556 |

**These three chains predate the reboot.** They must not be used to claim a
post-reboot provider delivery. Exact render uses the existing attributed inbox
format, `Astra: ` plus the unchanged provider message. This is exposure, not
semantic uptake or quality. An initial observer comparison omitted that
existing speaker prefix and reported no matches; the comparison was repaired,
regression-tested, and both observations remain in `receipts/`.

The original authenticated cursor caught up without bypass. Attempt373 failed
HTTP429/TPM at **01:12:15 UTC September19**; no publication and no same-attempt
retry. Cooldown ended **01:13:15.883248 UTC**. Distinct attempt374 dispatched
**01:13:17.641363 UTC**, received a completed exact model/xhigh response at
**01:14:02.322938 UTC**, and published at **01:14:03.351945 UTC**, ID
`0e2ffa3c8fa54413b454119b1b5e648b`. At01:19:19 the exact REQUEST/ACT remained
pending while the native continued its existing sleep updates. The fresh
publication is real, but is not yet a completed ACT receipt at that cut.

Use `PROVIDER_ACTIVITY.json` and `VERIFIED_PROCESS.json` for fresh observations;
`observe.py` refreshes the last three actual MODEL publications and explicitly
counts post-reboot chains. The initial historical332/335/338 trace is preserved
in `receipts/LAST3_20260919T010747Z.json`; newer last-three cuts include374.

## Supervisor restart contract

Do not launch a second parent. `preflight.py` refuses a live recovery process and
requires the old parent lock to be free, the original manifest exact, no
unfinished attempt, and the current native guard/LOADED verified. Run it in the
existing credential-bearing supervisor environment; never place the key in argv,
logs, config or files. `runner.py` requires a preflight less than10 minutes old.

The metadata-only P3 entry was registered with Averroes's then-live supervisor311614;
the current observed replacement is399392, with the same registration intact.
`SUPERVISOR_OBSERVED.json` verifies its fresh heartbeat, exact boot/process and
**EXISTING_SINGLETON_LOCK_HELD_NO_LAUNCH** status. This intentionally protects
current parent346649 via its original lock, without restarting it to match a
different argv. It is not an argv-adoption claim. A real duplicate-start attempt
returned75 with protected files unchanged (`DUPLICATE_REFUSAL.json`).

Automatic restart argv, only after the existing lock is free:

```sh
/usr/bin/python3 -B /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_p3_parent_20260919/restart.py
```

The actual parent argv is recorded in `PROCESS.json` and `VERIFIED_PROCESS.json`.
The foreground restart entry checks pinned code, original ledger/seed and lease,
archives prior receipts, makes a fresh read-only preflight, then execs the runner
in the same PID. It preserves the inherited provider credential and429 cooldown.
Unfinished attempts, changed source/guard, absent credentials or expired lease
fail closed; supervisor retry backoff does not permit a provider retry or bypass.
After a supervised exec, **OWNED_PROCESS_COMMAND_CHANGED_NO_DUPLICATE** is the
expected status because the supervisor still owns the same local PID. Details
are in `TO_MAIN_AND_AVERROES.md`. Boot installation is still
**BLOCKED_UNINSTALLED / boot_enabled=false**, not reboot-persistent service proof.

Read-only checks while it runs:

```sh
python3 -B research_loop/workers/post_reboot_p3_parent_20260919/status.py
python3 -B research_loop/workers/post_reboot_p3_parent_20260919/observe.py
```

CPU checks: **18 scoped tests +1 original parent-context test PASS**, with logs in
`TESTS.txt` and `TEST_existing_parent.txt`. These test backoff/no retries,
unchanged tick gates, actual model/effort enforcement, real /proc command parsing,
exact attributed-parent render matching, duplicate refusal, fresh restart
preflight/exec order, secret-free failure metadata and registration conflicts.
The actual original-manifest dry
run, receiving guard/native check, single-owner lock proof and canonical trace
reads are separately recorded; CPU tests are not a provider-delivery claim.

The initial pending374 REQUEST→ACT observation is complete. Remaining at01:30UTC:
377 exact render/ACT and platform-authorized OS boot installation. Registration
is verified; do not start anything merely to obtain more evidence. If429 recurs,
respect the persisted not-before time. Exposure is not semantic uptake or retention.
