# Metadata handoff — Main and services agent Averroes

Recipient: Averroes, `01a0b71d-1231-7012-91cf-073230080a6d`, and Main.
User requests only supervisor metadata and a restart contract after recovery;
no new tasks, probes, native launches, or signals are requested or performed.
This is a durable shared-repository handoff, not a claim of direct agent-message
delivery or acknowledgment.

## Single restart-safe foreground command

```sh
/usr/bin/python3 -B -u /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_node3_parents_20260919/recover.py
```

Cwd: `/data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_node3_parents_20260919`.
The existing `NVIDIA_API_KEY` must remain inherited in the supervisor environment;
do not place its value in argv, manifests, logs, or messages. The application
registry command matches the already-running process exactly after interpreter
resolution, so the running supervisor can adopt it without restarting it.

## Ownership and treatment

- Real-host PID330973, startticks764197, PPID1, verified01:11:44UTC; command
  SHA256 `6cfe7e87bfa9f32d504421726a3ee2fc315fd90f309181660a2b8ec15b649ffe`.
- `locks/SUPERVISOR.lock` and five exact-life locks exclude duplicate workers.
  Node-local publishers1973233/1973234 retain their original locks and identities.
- **All five forks are parented under R233.** The root named
  `r213_r226_caption_unparented_fork` is a historical lineage name, not a current
  control assignment. Preserve the old unparented epoch as history; never exclude
  this fork from the parent service because of its name.
- Only caption-provider mailboxes are serviced; math trio parents are untouched.
  No native controls, row filtering, sealed evaluation, or credential forwarding.
- Existing horizon is2026-09-24 18:00UTC /1790272800, with all five independently
  matching deadlines in `BINDINGS.json`. This registration extends no lease.
- Explicit HTTP429 rejections retry with bounded15–60second backoff and preserved
  attempts. Ambiguous provider dispatches are not replayed.

## Completion and registration

All five first INBOX → masked ACT REQUEST → own RESPONSE → ACT chains are
verified in `FIRST_RECEIPTS.json`, independently preserved in `first_verified/`.
Twelve CPU tests pass. Delivery is not demonstrated caption-task uptake; initial
linked replies still include repetition, code and mixed-script text.

The validated owner manifest is `NODE3_SUPERVISOR_ENTRY.json`; install only as
`post_reboot_services_20260919/services.d/node3-parents.json`, replacing its disabled
placeholder atomically. The exact live provider and held singleton lock make this
an adoption registration, not a second launch. Never run the old all-eight provider
alongside this service. `SUPERVISOR_REGISTRATION.json` records the observed outcome.
Application-supervisor registration is not OS boot installation: the services
owner reports boot installation blocked/uninstalled and `boot_enabled=false`.

After recording the metadata outcome, this restoration task is finished. The
already-running provider continues its existing cadence; no further actions or
signals are part of this handoff.

## Observed completion

Registration succeeded: supervisor311614 heartbeat01:13:11UTC reports
`node3-parents: RUNNING_ADOPTED_NO_SIGNALS`, exact provider330973/start764197,
with no new process or signal. Receipt: `SUPERVISOR_REGISTRATION.json`.

Read-only final cadence audit01:14:48UTC: all five first chains remain verified;
four subsequent parent turns have actually published. **Judgment transport is
still a blocker:** the latest3ACTs per fork (15total) all report
`ConnectionRefusedError` / `ENVIRONMENT_OUTCOME_UNKNOWN_NO_RETRY`, executed=null,
no feedback and no successful judgment. Exact source hashes and timestamps are
in `FINAL_CADENCE.json`. Main/judgment owner should not interpret restored parent
delivery as restored judging or task uptake. This task performs no scorer/transport
repair, no ambiguous replay, and no further task or process action.

## Old PID is not a current outage

At01:16:05.991328UTC, real-host nvl-ai verifies live PID330973/start764197,
PPID1, under boot80d71f45-6f0c-4479-b0e5-77a9611c793e. Old324210 was deliberately
replaced at00:58:07.628787UTC for the confirmed-HTTP429 CPU-provider repair.
Supervisor311614 heartbeat01:16:02.887847UTC correctly adopts330973, not324210;
no new restart or signal is needed. The source-authenticated latest publication
at the01:16:06.938732UTC read is perspective0037 at01:12:52.975223UTC, ID
9254e24c4c7946e5a2a482ac252d1bf8. Read-only identity/publication reconfirmations
are preserved as `IDENTITY_RECONFIRMATION_*.json` and
`PUBLICATION_RECONFIRMATION_*.json` in this directory.
