# Recovery handoff — September 19, 2026, 01:23 UTC

Non-material operational repair only. Source ownership remains with the
respective agents. No native launches/signals, GPU evaluations, scientific
policy changes, commit, push, or host-management bypass.

## Actual host and registrations

Host `nvl-ai`, boot `80d71f45-6f0c-4479-b0e5-77a9611c793e`.
Read-only escalated verification completed at **01:23:06.904145 UTC**:
`FINAL_HOST_VERIFIED_1789780986904523343.json` contains exact argv, start ticks,
manifest hashes, lease ends, kernel lock owners and receipt hashes.

| CPU service | PID/start ticks | Actual supervisor status |
| --- | --- | --- |
| Application supervisor |399392/891869|Foreground, boot uninstalled|
| Pair learner |345404/792480|RUNNING_ADOPTED_NO_SIGNALS|
| Pair frozen |345405/792480|RUNNING_ADOPTED_NO_SIGNALS|
| Node3 |330973/764197|RUNNING_ADOPTED_NO_SIGNALS|
| P7 bounded |378291/854895|RUNNING_ADOPTED_NO_SIGNALS|
| P3 |346649/795156|EXISTING_SINGLETON_LOCK_HELD_NO_LAUNCH|
| C2 owner |361010/822432|RUNNING_ADOPTED_NO_SIGNALS|
| Astra7 bridge |325634/753612|RUNNING_ADOPTED_NO_SIGNALS|
| Caption collector |311631/717211|RUNNING_ADOPTED_NO_SIGNALS|
| Correction observer |298357/687734|RUNNING_ADOPTED_NO_SIGNALS|
| Enrollment launcher |343304/788315|RUNNING_ADOPTED_NO_SIGNALS|

Pair's owner enabled both entries at01:20:33 UTC after the existing fleet
ceiling correction. This worker detected the concurrent registration and
did not overwrite it. Pair's unchanged source-bound end is1790791200;
collector/enrollment ends remain1790791170. At01:19:24 UTC only this worker's
CPU supervisor was gracefully refreshed; every worker incarnation survived.
`SUPERVISOR_REFRESHED.json` records the exact one-shot pidfd handoff and
in-memory runtime-environment preservation. It is not a boot installation.

P3's owner-approved `restart.py` registry intentionally differs from the
existing live `runner.py`. Both original P3 locks belong to346649. This is
verified existing-lock protection, **not argv adoption**. No P3 signal,
replacement, launch or source modification was performed here.

Epicurus's shared-repository handoff confirms node3's old324210 was deliberately
replaced at00:58:07.628787 UTC for the CPU-provider HTTP429 repair. The registered
successor330973 is live; no new restart is needed. See the scoped
`TO_EPICURUS_AND_MAIN_20260919.md` acknowledgment and the owner's handoff.

## Every-sleep: enrollment, not testing

The restored service is **16-root CPU enrollment metadata only**, not an
automatic GPU probe dispatcher. It does not capture, evaluate or dispatch
backlog jobs. The arbitrary probe-daemon placeholder remains disabled; the
approval-watch placeholder also remains disabled pending an approved command.

- Actual driver **343342/start788324**, launcher **343304/start788315**.
- Both original `enrollment/ENROLL.lock` and `extra_enrollment/ENROLL.lock`
  belong to343342; `QUEUE_LAUNCHER.lock` belongs to343304. Single exact argv
  match for each.
- Preserved all **1242** original references with exact prior entry contents
  and queued ages; original ledger paths and16 cursor identities retained.
- First full16-root poll completed **01:02:55.822780 UTC**, **1254** references:
  `runs/1789779728873833849/FIRST_CYCLE.json`.
- Latest completed poll at verification: **01:23:06.164945 UTC**, **1491**
  references, **16/16** frontiers advanced since the first poll, **12/16**
  caught up to their observed metadata head, four still scanning backlog.
- Zero cursor regressions, captures, dispatches or evaluations by this queue.
  Metadata caught-up status does **not** mean probe/test completion.
- `runs/1789779728873833849/LATEST.json` is the live convenience pointer;
  the append-only final receipt preserves this observation's hash and all
  per-root first/latest frontiers and baseline/current cursor comparisons.

## Collector and P7 receipts

Collector311631 owns the original `CAPTION_HOURLY.lock`. Backfills
**September18 23:00 UTC** and **September19 00:00 UTC** are complete, eight
players each, no read errors, and epochs remain separate:
`../cuts/20260918T230000Z.json`, `../cuts/20260919T000000Z.json`.
Latest successful current cut is **September19 01:01:02.572434 UTC**,
completed01:01:03.826171, eight players:
`../cuts/20260919T010102Z.json`. Next scheduled run is **02:00 UTC**.
These recovery backfills do not reconstruct exact historical completion
visibility times; no rescoring or epoch mixing occurred.

P7 handoff succeeded at01:13:14 UTC: the exact old325545/start753409 was
observed in a fresh idle window with no children and original locks, received
one pidfd SIGTERM, and exited. Bounded378291 holds both original locks.
`P7_BOUNDED_STARTED.json` records145 preserved preexisting files and zero
native signals. The newest actual poll sampled by final verification uses
`P7_POLL_RECEIPT_V1`, **1960 bytes**; SOURCE/RESPONSE/NEXT remain full actual-turn
records. Do not rerun the one-shot handoff.

## Tests and boot limitations

30 supervisor/collector tests and28 observer/registration/identity tests pass;
the owner's three restoration/bounded-poll tests also passed. Logs:
`FLEET_HORIZON_REGRESSION_TESTS.log`, `FINAL_OBSERVER_REGRESSION_TESTS.log`,
`P7_BOUNDED_MAIN_TESTS.log`. Registry validation reports zero errors.

**Boot installation: BLOCKED_UNINSTALLED. Boot-enabled: false.**
**Secure boot credential bootstrap: UNVERIFIED.** The present supervisor
inherits `NVIDIA_API_KEY` in memory; no supported fresh-boot credential
provisioning has been verified. No secrets were printed or written.
Templates alone provide **no future reboot-safe guarantee**.

Exact safe foreground command, only in the real host environment with already
provisioned runtime credentials:

```sh
/usr/bin/bash /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_services_20260919/boot.sh
```

The existing supervisor flock rejects duplicate foreground invocations.
No systemctl/loginctl/cron/startup-file/DBus/boot-installation alternative was
attempted. Platform-approved installation and independently verified secure
credential provisioning remain required for actual automatic boot recovery.
