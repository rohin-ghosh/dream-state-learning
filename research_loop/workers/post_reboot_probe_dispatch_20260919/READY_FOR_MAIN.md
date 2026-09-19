# Reviewed route: hash-frozen, not launched

Final receiving CPU preflight passed on **September 19, 2026 at 02:14:26 UTC**.
No scientific source, runtime, or configuration bytes were changed during Main's
review. `FROZEN_FOR_MAIN.json` records the exact hashes, source identity, CPU test
result, receiving inventory, and full launch argv. This is a hash freeze, not a
claim of filesystem immutability. Main owns the next execution; this worker has
not launched either role or called a service manager.

## Source, battery, and device binding

- Source: `FRESH_R231_s12`, journal `038f85cbde5c4abfb749ea4d59da6897`, sleep12,
  optimizer576. Original CPU preparer returned `CPU_SOURCE_READY_NOT_LOADED`.
  The inherited-exposure/freshness audit passed; no source-exposure blocker remains.
- All 103 original source files, 25 input artifacts, and the two new runtime
  modules are hash-bound. Source authorship and original files are unchanged.
- The original `probe.main()` retains the same three DEVELOPMENT scenes, two
  seeds, 1024 generated tokens/cell (6144/source), judge, reference panels,
  control policy, source epoch, and condition-scoped evaluation state.
  Parent tokens and optimizer/model updates remain zero.
- Player2: `GPU-ac7e4165-630c-eafe-4ba5-2b2fc4a4e5d1`; judge7:
  `GPU-b7ec9035-3ba3-464f-6c2f-7588a3e328c1`. Both had 0MiB and no compute PIDs
  at final preflight. These are observations, not reservations.
- GPU4 remains occupied by PID499900; GPU5 by PID499905; each reports 14363MiB.
  All physical devices other than2/7 remain protected. No native or scorer is
  signaled, restarted, or displaced.
- Each role is bounded by the job's common deadline of at most2400 seconds and
  the original lease end1790791170 (September30, 2026, 17:59:30 UTC).

## Exact node command for Main

Run on `ipp2-ovx-p3-02` as the original leased-host user1352:

```sh
python3 -B /localhome/local-rohing/post_reboot_probe_dispatch_20260919/465dedb4d06300e2a82046af61bd914f915a4ccbe588d5f05fb0616b90440ae7/runtime/dispatch_once.py \
  --config /localhome/local-rohing/post_reboot_probe_dispatch_20260919/465dedb4d06300e2a82046af61bd914f915a4ccbe588d5f05fb0616b90440ae7/runtime/JOB_CONFIG.json \
  --config-sha256 9744a62e40d0ebb64dfb1c9911416ff2e9be33184814b1d5cd687db78a44a380 \
  --launch
```

From the repo VM, the exact same node command can be passed as one quoted argument
to `bash gpu/ovx4_ssh.sh`. Replacing only `--launch` with `--check` performs the
read-only CPU preflight. Neither command changes the frozen configuration.

The dispatcher constructs the original confined GPU-host transient route with
`sudo -n systemd-run`, User/Group1352, `DevicePolicy=closed`, a single physical GPU
allowlist plus control devices, UUID CUDA mask, and finite runtime/teardown.
The role wrapper then independently checks all eight device opens before the
unchanged original runtime's own physical-device proof and model load.

No platform permission or actual cgroup confinement has been exercised by the
CPU check. Any actual platform/tool denial is terminal: no alternate execution
path, elevated retry, service-management workaround, or second invocation after
an ambiguous launch. Stable job identity, launch intent, role locks, and scoped
UUID claims prevent this dispatcher replaying a partial or completed attempt.
Coordinate other producers' lane use; this worker's claim is not a fleet-wide
lock respected by every producer. Admission rechecks occupancy before dispatch.

Standing builder scope already authorizes this experiment. Main's route review
is now complete; there is no new human/per-device ratification requirement.
Main will rerun the CPU suite and record the dated Builder provenance entry
before its one invocation; this worker does not edit global coordination docs.

## CPU tests and receipts

```sh
python3 -B -m unittest discover -s research_loop/workers/post_reboot_probe_dispatch_20260919 -p 'test_*.py' -v
```

All **24 tests passed**, including overlapping/occupied/protected devices, UUID
remapping, other-GPU exposure, expired/extended leases, changed battery, complete
source closure, no replay, exact cgroup command construction, and terminal
platform denial. `RUNTIME_REGRESSION_TESTS_FINAL.log` records the same frozen
tests; they were also rerun successfully during final verification.

`ROUTE_CHECK_1789783851566555298.json` retains the complete proposed route.
`FROZEN_FOR_MAIN.json` records the newer successful02:14:26 recheck. The older
`EXECUTION_READINESS.json` is historical and superseded, not a current
source-exposure or device-readiness assessment.

## Restored service health

Real-host `ps` confirmed supervisor399392, collector311631, enrollment
launcher343304, and enrollment driver343342 still alive. Supervisor heartbeat
02:14:21 UTC reported zero errors. Exact earlier process identities and kernel
locks remain documented in `HEALTH_1789783264102929861.json`; the final follow-up
used real-host `ps` and did not re-test locks or restart processes.

The completed first enrollment poll was1254 references; the latest observed
poll at02:14:19 UTC has1569 references,16/16 roots caught up, no cursor
regressions, unchanged historical entries, and **zero evaluations/dispatches**.
Enrollment is not GPU probe execution. This reviewed dispatcher is one bounded
job, not an enabled automatic fleet queue daemon.

The02:00 scheduled collector cut completed at02:00:01.208797 UTC for eight
players, with epoch separation, zero scoring calls, and no cut errors. Its
receipt is in `../post_reboot_services_20260919/cuts/20260919T020000Z.json`.

VM boot installation remains **BLOCKED_UNINSTALLED**. Secure automatic boot
credential provisioning remains **UNVERIFIED**; inherited shell credentials
and templates provide no future reboot-safe guarantee. No boot installation or
service-management capability probe was attempted.
