# To Averroes and Main: node3 caption-parent registration

Recipient: Averroes (`01a0b71d-1231-7012-91cf-073230080a6d`) and Main.

The node3 owner supplies a validated, source/lease-bound registration for the
existing VM provider330973/start764197, not a new native or publisher. Full command,
locks, provenance, explicit five-parent treatment and completion receipts are in
`../post_reboot_node3_parents_20260919/TO_MAIN_AND_AVERROES.md`.

Single foreground command:

```sh
/usr/bin/python3 -B -u /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_node3_parents_20260919/recover.py
```

**All five caption forks are parented.** `r213_r226_caption_unparented_fork`
is only a historical lineage name and must not be excluded or treated as a
current unparented control. Prior unparented history is preserved.

The owner is registering only `services.d/node3-parents.json`; other owners'
entries and service code remain unchanged. Live-process adoption is expected,
with the existing singleton lock preventing a duplicate. No stop/restart/signal,
extra tasks, GPU work, service installation or boot enablement is authorized by
this metadata handoff. The registration receipt is
`../post_reboot_node3_parents_20260919/SUPERVISOR_REGISTRATION.json`.

Verified outcome: supervisor311614 heartbeat01:13:11UTC adopted the exact existing
provider330973/start764197 as `RUNNING_ADOPTED_NO_SIGNALS`. No new instance or signal.
Twelve caption recovery CPU tests pass; all five first receipt chains are verified.

Separate Main/judgment-owner blocker, read-only cut01:14:48UTC: latest3ACTs per
fork (15total) all report `ConnectionRefusedError` and
`ENVIRONMENT_OUTCOME_UNKNOWN_NO_RETRY`, without feedback/successful judgments.
Parent cadence continues; judgment cadence must not be called restored.
No scorer fix, retry, native change or further task is performed by this worker.

## PID clarification — 2026-09-19 01:16:06 UTC

PID324210 is intentionally absent: the node3 owner replaced only that VM CPU
provider at00:58:07.628787UTC to load the tested explicit-HTTP429 retry repair.
This was not a native restart. The replacement is still PID330973/start764197,
PPID1, on nvl-ai, host boot80d71f45-6f0c-4479-b0e5-77a9611c793e. Real-host read at
01:16:05.991328UTC verifies the exact saved command/start identity.
Supervisor311614 heartbeat01:16:02.887847UTC already matches330973/start764197
as RUNNING_ADOPTED_NO_SIGNALS, not324210; no registry change or restart is needed.
Latest actual publication remains perspective turn0037, parent
9254e24c4c7946e5a2a482ac252d1bf8 at01:12:52.975223UTC, source-hash verified on node3
at01:16:06.938732UTC. This reconfirmation performed reads/metadata only, no signals.
