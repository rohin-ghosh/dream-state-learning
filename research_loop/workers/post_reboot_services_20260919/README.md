# Local daemon recovery — non-material repair

**Boot installation is BLOCKED / UNINSTALLED. Boot enablement is false.**

**Boot credential bootstrap is UNVERIFIED.** The current ordinary CPU
supervisor inherited its existing `NVIDIA_API_KEY` in memory; this is not
secure credential provisioning for a fresh boot. No supported boot-time
credential provider has been verified, and no credential values were written
or printed. The repository unit/boot templates alone provide no reboot-safe
guarantee. Both explicitly permitted installation and supported secure
credential provisioning remain prerequisites.
Host service-management enforcement rejected read-only capability queries. No alternative service-management path, startup-file modification, cron job, linger change, unit installation or enablement is attempted. A repository template is not an installed service. Actual reboot-start needs separately permitted platform installation and an available boot-time user manager; login-only startup is not reboot proof.

Safe foreground command on the real VM host (not sandbox /proc):

```sh
/usr/bin/bash /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_services_20260919/boot.sh
```

It validates host/uid/PID1, acquires one supervisor flock, adopts exact matching same-user local processes, and starts only enabled validated entries. Another supervisor exits 75 without duplicates. No service-management command is executed. Stopping the foreground supervisor does not signal adopted daemons or child natives. All entries must enforce their own existing lease even if the supervisor disappears. The supervisor additionally stops only its own directly launched local daemon PID at that entry's deadline, never a process group or remote child. Owner-provided commands must stay foreground, must not fork/detach, and must not propagate local shutdown to child natives.

## Main/owner registration contract

Add one JSON file per existing local daemon under `services.d/`, with its `name` matching the filename stem. Main must coordinate active agents before enabling entries. Replace manifest files atomically. They reload every 10 seconds. Invalid entries are reported and never launched. Removing/disabling an entry suppresses launches, not an instruction to stop existing processes; owned processes retain their original bound until exit. Changed argv never auto-replaces a running owned daemon.

Use `caption-collector.json` as the complete schema example. Required fields: `name`, `enabled`, `kind` (`parent`, `collector`, `probe`, `queue`, `approval_watch`), `owner`, `approval_scope`, `local_daemon_only: true`, `child_native: false`, `restart_safe: true`, `self_enforces_lease: true`, `foreground: true`, `shutdown_leaves_child_natives_running: true`, exact non-secret `argv`, repository `cwd`, repository `entrypoint`, `entrypoint_sha256`, `until_unix`, and `lease_evidence` (`path`, `sha256`, `json_pointer`). The lease value referenced by the JSON pointer must be numeric and no earlier than `until_unix`; neither may extend the original fleet cap. The entrypoint digest must match at every launch check. Use absolute interpreter paths and an actual bound script, never shell `-c`, Python `-c`, environment assignments or inline credentials. Approval watchers additionally need `watch_only: true`; this is monitoring, never approval. Credentials stay in existing runtime environment/providers, never manifests or units. The supervisor does not capture daemon stdout/stderr into files; daemons retain their own existing approved logging.

Only the collector is initially configured. Pair, node3, C2, P7, probes, approval-watch and Lovelace's every-sleep queue remain explicitly disabled pending owner argv and lease provenance. Placeholder entries are not evidence of restoration. Main may split placeholders into multiple named manifests. Do not register a command that commits or pushes; publication is disabled in this recovery scope.

Validate without starting anything:

```sh
/usr/bin/python3 -B research_loop/workers/post_reboot_services_20260919/supervisor.py --validate
python3 -B -m unittest discover -s research_loop/workers/post_reboot_services_20260919 -p 'test_*.py' -v
```

## Collector evidence

The application supervisor's fleet ceiling is `1790791200` (September 30,
2026, 18:00 UTC), bound by the existing pair allocation in
`rohin231_curriculum_birth_20260918/recovery_20260918T1646Z/ALLOCATION_DATE_CORRECTION.json`
at `/hard_end_unix`. This non-material operational repair separates that
existing authority from the collector's 30-second shutdown margin. Collector
and enrollment deadlines remain `1790791170`; every registry entry still
requires its own hash-bound lease evidence. No lease is purchased or extended.

`collector.py` shares the existing R233 `CAPTION_HOURLY.lock`. It reuses the established epoch projector and read-only scorer-identity checks. Existing worker files and latest pointers are untouched. Recovery writes stay in this directory; `cuts/` and `receipts/` are append-only with atomic no-overwrite publication. Mutable heartbeats here are convenience pointers only. Per-source deadlines remain independent, expired sources are not queried, and missing metrics/errors are not converted to zeros. Failed reads retry, missed full-hour cuts are recovered in bounded batches, and a current partial cut is collected immediately and each UTC hour.

The 2026-09-18 23:00 UTC and 2026-09-19 00:00 UTC backfills retain all eight player epochs. They count ACT origins/admissions strictly before each cut, but observe immutable completion outcomes during recovery. They are **not** certified reconstructions of which completions were visible precisely at those historical times. No rescoring, GPU work, private caption export, inherited-cache mixing, humor claim, commit or push occurs.
