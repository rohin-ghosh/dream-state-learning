# Node3 judgment transport — Main and Averroes

2026-09-19 01:26UTC: non-material recovery of the existing CPU transport only,
explicitly authorized by the user's priority redirect. All five model parent
chains are already sufficient; no additional parent calls, restarts or signals.

Root cause: VM reboot removed upstream SSH, CPU authenticated-journal proxy and
downstream SSH. All five native aliases still address stale source-lease sockets.
The node-local Tool relay1970178, parent publishers1973233/1973234, scorer499900,
and scorer bridges448173/502015 remain alive with their original incarnations.
The old324210 and current330973 are model-provider workers, not these transports.

CPU tests: three new regression tests pass for exact original registry bytes,
the five node3-only routes, and the unextended September24 17:59:20UTC deadline.
Read-only preflight verifies native incarnations, the actual shared2 scorer route,
unchanged LOADED hash and all five original epoch IDs. No scorer/GPU restart,
ledger reset, historical ACT replay, row filter or judge modification is planned.

Restore only the existing private Unix forwards with fresh temporary endpoints;
retain stale sockets and atomically retarget the five existing stable aliases.
No synthetic request is sent. First future natural ACT and Tool INBOX receipts
are still pending; process readiness must never be described as successful judging.

Foreground restart command (real VM host, not sandbox PID namespace):

```
/usr/bin/python3 -B -u /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_node3_parents_20260919/restore_transport.py
```

Singleton: `locks/TRANSPORT.lock`, also inherited by CPU children. Independent
CPU timeouts preserve the source-specific original deadline. On component failure
the controller records it and does not replay any request or signal natives.
No supervisor adoption or judgment success is claimed until observed.

## Actual natural feedback receipts — September19 01:30UTC

CPU transport425470/start939654 activated01:27:29.869487UTC on VM boot
80d71f45-6f0c-4479-b0e5-77a9611c793e. No native, model-parent, GPU scorer or
existing node-local feedback relay was restarted or signalled. All original
scorer epochs and ledgers remain in place; original authenticated registry SHA
a14411eb727c5b9b2bdc10e259f65d2b91f4396bd57c273f69d423a84bc8005f is unchanged.

| Fork | Natural RESPONSE → ACT → Tool INBOX | Scorer response UTC | Tool publication UTC |
|---|---|---|---|
| historical unparented, currently R233 parented | 7511 → 7514 → 7526 | 01:27:53.640325 | 01:27:56.130309 |
| revision | 7397 → 7400 → 7412 | 01:28:54.839777 | 01:28:56.999471 |

First receipt SHA256:
4524f92539785093112cb95fcb8b2bd3c2e429166939bc02fb99a58d646d042d.
Revision receipt SHA256:
f6329c14d85c73b8d4fa5a6dbbc18673dd1a44c8d142446b118b7fd13e797a67.

These are source-authenticated **no-judgment feedback**, with error
`scene_not_unambiguously_identified`, zero scored results, and confirmed consumed
Tool INBOX records. They prove the live scorer-service → native ACT → original
Tool relay → native INBOX transport, not successful caption admission/ranking,
task uptake, or learning. Other three forks are pending at this cut. No synthetic
request, parent task, or historical ACT replay was injected.

Remaining concrete transport blocker: some natural requests exceed the original
64MiB aggregate journal-export bound (`bounded_total_journal_mirror`), failing
before dispatch. Historical-unparented origin7504 reproduces this in a read-only
export diagnostic; it was never redispatched. No bound, ancestry, judge or policy
has been changed to hide this failure. Report partial recovery, not all-five
successful judgment cadence. Exact metadata is in `JUDGMENT_RECEIPTS_LATEST.json`.

All17 CPU tests pass, including frozen-source import and exact new-transport
receipt matching. `TRANSPORT_TESTS.txt` preserves the output. The failed first
startup and its socket/log/source artifacts remain under
`private/transport_runs/1789781196615433111100205/`; only its own newly-created,
unactivated CPU forward was cleaned up, recorded in
`FAILED_STARTUP_CPU_CLEANUP.json`. Original stale node endpoints remain intact.

Averroes has installed `services.d/node3-judgment-transport.json` with matching
entrypoint SHA, singleton and original source-lease deadline. Supervisor399392
heartbeat01:30:31.060350UTC confirms425470/start939654 as
`RUNNING_ADOPTED_NO_SIGNALS`. Real-host identity reverified01:30:33.968285UTC in
`TRANSPORT_REAL_HOST_VERIFIED.json`. OS boot enablement remains false; application
registration and adoption do not imply OS boot installation. No further tasks,
synthetic requests, replays, native actions or signals are performed after this handoff.
