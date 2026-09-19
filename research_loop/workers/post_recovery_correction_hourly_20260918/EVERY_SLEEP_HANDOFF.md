# Every-sleep enrollment daemon — read-only handoff to Main

Observed September 19, 2026, after the VM boot at September 18 22:50:45 UTC.
No enrollment daemon was launched, edited or signalled. No enrollment lock was
acquired, ledger written, checkpoint copied, score read, or probe dispatched here.

## Identify the correct predecessor

The latest fleet enrollment daemon was **PID3524450/start186568701**, outer
timeout PID3524448, started September 18 19:11:08 UTC. It superseded
PID3046824; both daemon PIDs are absent on this boot. Historical `alive:true`
fields in `rohin233_ovx4_recovery_20260918/SUPPORT_COMPONENT_TABLE.json` are
stale. This is the sixteen-root **enrollment-only** service, not the older
one-learner `rohin232_age_probe_20260918/boundary_queue.py` daemon125962 whose
deadline was September 18 14:00 UTC, and not a GPU backlog dispatcher.

The authoritative surviving implementation is:

- `research_loop/workers/rohin233_ovx4_recovery_20260918/lease_admission_enroll.py`
  SHA256 `865caf819089adafb83b7748c297b675a848fab02521c0b28f3c6b70b7de630a`.
- `research_loop/workers/rohin233_kept_age_probe_20260918/enroll.py`
  SHA256 `509f2611cb88aa54837febc093339627b3b64fd518f006988ccff0a42e7c9c4e`.

Both current file hashes match the last launch's
`rohin233_ovx4_recovery_20260918/LEASE_ADMISSION_RENEWED.json`.
The former frozen runtime `/tmp/r233-enrollment-admission-20260918T1909Z/`
and its `CONFIG.private.json` are absent. Its historical config hash was
`f18d1df81f564487b46c69cf868cee2fb080f39224506c29acb8e7dfa10d0c4c`;
it is not a usable current configuration.

## Preserved ledger state

Under `research_loop/workers/rohin233_kept_age_probe_20260918/`:

| Ledger | Registered roots | Enrolled references | Current STATE SHA256 |
|---|---:|---:|---|
| `enrollment/private/STATE.json` | 15 | 1197 | `e04f92e7a7a1c0d14b80ed6609b1f03df4b5ac18443e1c7abb87d71ec47320c8` |
| `extra_enrollment/private/STATE.json` | 1 | 45 | `1a03456943601e6a8bec3fe315bda856549e5229c1954c4425a8ac14d072e1cd` |

Total **1242 references, not 1242 captured or evaluated checkpoints**. These
counts/hashes describe this read-only snapshot and must be rechecked under locks
before any restart. The sixteen cursors survive; do not reset or backfill as new.
Only enrollment metadata was read, not private sealed results.

- `private/REGISTRATION.json`: SHA256
  `1e3ce8cf7fdac1e6d9f31e6517757f649bf6acacd22aa3d1be549dbb9bc8187b`.
- `private/EXTRA_REGISTRATION.json`: SHA256
  `d95dfb84b2e289ff19dc5f5871a73e09e02951658229bfb26072ea5bb6ee8bfb`.
- Singleton locks: `enrollment/ENROLL.lock` (`00:24:6428379`) and
  `extra_enrollment/ENROLL.lock` (`00:24:6599254`). Neither inode had a holder
  in the observed `/proc/locks`; this is not a future ownership guarantee.

## Actual start/configuration contract

`lease_admission_enroll.py` accepts exactly `--config PATH`. The prior launcher
froze it as `source/driver.py` and `enroll.py` as `source/enroll.py`, then used:

```sh
timeout --signal=TERM --kill-after=5 REMAINING_SECONDS \
  python3 -B FROZEN_RUNTIME/source/driver.py \
  --config FROZEN_RUNTIME/CONFIG.private.json
```

This is a documented template, **not executed**. The prior launcher set the
working directory to repository root, detached the process, used `/dev/null`
stdin and a runtime-local log. Recompute the remaining timeout from the existing
service end; do not reuse the old duration.

Required JSON fields, as enforced by the surviving driver:

- `repo`, `support_root`, `receipt_root`, `deadline_unix` (exactly **1790791170**,
  September 30, 2026 **17:59:30 UTC**), `driver_sha256`.
- `reader`: `{path, sha256}` for the immutable reader copy.
- `ledgers`: two `{output, state_sha256, registration: {path, sha256}}` entries;
  bind **freshly observed current** preserved states, not the obsolete initial
  handoff hashes. The old launcher also recorded `state_snapshot` provenance.
- `wrappers_sha256`: hashes of the unchanged registered SSH wrapper files.

At startup it takes both nonblocking ENROLL locks, validates state/registration/
driver/reader/wrapper hashes and exactly sixteen unique journals. Each iteration
uses 64-record metadata pages with canonical journal continuity and completed
SLEEP/COMMIT joins, preserving every previous entry and monotone cursor. Poll
sleep is 15 seconds after each round. Enrollment neither copies adapter bytes
nor claims evaluation. It emits `LOADED.json`, `FIRST_CYCLE.json`, `LATEST.json`
under `receipt_root`, and `LEASE_ENROLLMENT_LATEST.json` under `support_root`.

Per-source cutoff policy is `R233_PER_SOURCE_LEASE_ADMISSION_V1`: node2/node5
September 20 18:00 UTC; node3 September 24 18:00 UTC; node4 September 25
18:00 UTC; ovx4 effective September 30 17:59:30 UTC. Every remote read requires
admission strictly earlier than cutoff minus35 seconds, with a30-second caller
timeout and receiving-reader alarm ending at least5 seconds before cutoff.

## Main's remaining work — not performed here

Reconstruct a durable frozen runtime/config from the surviving exact sources;
freshly verify registrations, current source access/cutoffs, both lock holders,
state bytes and wrapper hashes. Run the focused admission tests, launch only one
CPU enrollment process, and record the actual boot UUID/PID/starttick/command,
lock owners, LOADED and a completed first poll with preserved counts/cursors.
The existing driver's own LOADED receipt lacks boot UUID: Main must bind it in
the new observed process receipt rather than trust historical PIDs.

**Do not rerun `renew_enrollment_admission.py` unchanged.** It requires the old
live PID3046824, signals that exact old process, uses a fixed `/tmp` runtime and
assumes a live handoff, not a post-reboot restart. Reusing its old config would
also fail its exact initial-state hash check after the ledgers have advanced.
Leave caption collection and all GPU/scorer/parent/life processes untouched.
