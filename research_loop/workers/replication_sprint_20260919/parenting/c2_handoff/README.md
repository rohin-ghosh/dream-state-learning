# C2 identity-bound CPU handoff — prepared, not deployed

September 19, 2026. Non-material, invariant-preserving operational CPU repair.
Only this new directory is owned by this assignment. No parent policy,
measurement, live ledger, native process, supervisor or deployment is changed.
The helper has not been run, including in dry-run mode. Main owns native/pending
turn inspection, approval of the existing candidate, and any actual execution.

Main reports on September 19 that parent112 physically appears as original
native INBOX15741 at 14:50, native is alive and sleep153 is complete, but the
snapshot exporter still awaits a complete cut and DELIVERED is not yet written.
This is Main's observation, not a helper-generated receipt. The helper still
refuses that pending ledger: it never translates an INBOX observation into a
synthetic DELIVERED, treats the publication as lost, or replays it.

## Fixed scope

- Publisher **325487 / start ticks 753205**, exact original argv and repo cwd.
- Supervisor **361010 / start ticks 822432**, exact service argv and cwd; never
  signalled. The existing supervisor retains its locks, cursor computation,
  inherited C2 credentials and successor creation. No new publisher is launched.
- Exact seed SHA256:
  `14b4a285dda3abcb7ccd9421ccbd8135bd26883cde7cead410e52a56cd073330`.
- Exact install patch SHA256:
  `5a42f5a572b2cdd3bcd80a8d4f43b7c5d1fab8b30b5c93f45eb6c55e45e20c96`.
- The sibling `candidate.py` is itself hash-bound before loading; its existing
  seed/pin/STARTED/config/addendum/ledger checks are reused without importing or
  running the service or any provider. Questions-only keys, including null or
  nested keys in the seed/current config, are conflicts, not mode defaults.

## Behavior

Dry-run is the default: read-only identity, pin and current-ledger checks;
no signals, patch subprocess, native check or deployment authorization. Linux
pidfd support is mandatory; there is no numeric-PID signalling fallback or
arbitrary PID/signal/path/command option. Both pidfds are opened before their
identity checks, checked for exit around proc reads, and closed on every path.
Only `stat`, `cmdline`, `cwd` and task `children` are read under `/proc`; never
`environ`, credentials or remote native files. Patch execution receives a
minimal PATH-only environment, not inherited credentials.

Execution additionally requires both explicit exact reviewed hashes. A read-only
advisory lock on this helper's own inode excludes concurrent copies using the
same file, without acquiring or editing the supervisor's original locks.
An initially unsettled ledger causes no STOP. A sleeping, single-threaded
publisher with no children is briefly stopped through its pidfd. After observing
state T, the helper rechecks seed/install bytes, every seed pin, supervisor,
and the frozen ledger. It requires empty `pending` and last status PUBLISHED
or SILENT. Missing consumption receipts or a latest HTTP failure block handoff;
historical HTTP failures remain recorded and reserved, never replayed.

Only then does `apply_patch` receive the already-verified, single-Add-File patch
through stdin. No raw live-file writes, fake STARTED/DELIVERED, cursor edits or
old-result relabelling. Existing targets and symlink installation paths fail
closed. The installed bytes, unchanged frozen ledger and both process identities
are checked again before TERM of the same publisher pidfd. CONT in `finally`
allows termination, or resumes the original publisher on rejection/exception.
Cleanup is armed before STOP, including an uncertain STOP syscall result.
Catchable INT/TERM/HUP and a 10-second alarm unwind through cleanup; STOP
acknowledgment is bounded to one second and patch execution to three seconds.
The helper never retries HTTP, patch execution or termination, escalates to
KILL, touches a process group, or fabricates consumption. Exit observation is
reported separately from a TERM request; successor delivery is never asserted.

## Unresolved races / owner obligations

- This is **not an atomic transaction** with the supervisor, filesystem or
  another operator. External CONT/KILL, process exec, edits after a last check,
  a competing discovery manifest, or supervisor death remain possible. pidfds
  prevent retargeting a reused PID, not these races. Main must own the window.
- A crash/error/interrupt after `apply_patch` starts can leave a complete or
  partial discovery seed installed. CONT does **not** roll it back. The old
  publisher can later exit and the supervisor can discover it; Main must inspect
  this state before any retry. No automatic rollback or repeated install occurs.
- `finally` cannot survive SIGKILL, host failure, indefinite kernel I/O, or lost
  signal permission. CONT errors other than an already-exited original are
  surfaced. The alarm is best-effort, not an independent crash-safe watchdog.
  No absolute guarantee against a stopped process under those failures is made.
- No child process is stopped; finding any child/thread refuses the handoff.
  A stopped ledger is local readiness evidence, not fresh native liveness,
  ACT visibility, learning success, or proof that the supervisor will choose
  the seed. Main still reconciles historical missing-consumption receipts,
  verifies native continuity and the first real successor/provider/delivery
  receipts. Preserved historical ledgers are not rewritten or declared settled.

### Main's reconciliation after an install-stage failure

Do not automatically rerun the helper. Preserve its output/error, seed target
bytes/hash and timestamps, old publisher identity/state, and any supervisor
session/STARTED/EXIT evidence. Determine whether a patch subprocess is still
running after an external helper kill; absence of helper output is not proof
that no installation happened.

- **Target absent:** establish the old publisher's actual identity/state and
  ledger readiness again before considering a newly reviewed attempt.
- **Target equals the pinned seed:** it is already a discovery input, even if
  TERM was never sent. Check whether the supervisor selected it or created a
  successor. A matching file alone is not a deployment/delivery receipt, and
  another helper invocation will refuse the existing target.
- **Partial/different target:** preserve the evidence and inspect supervisor
  discovery/errors. Main decides on separately approved `apply_patch` repair
  or removal after reconciling current process/session state; this helper
  neither overwrites nor deletes it, and never changes prior ledger evidence.

These are owner reconciliation steps, not a crash-atomic rollback protocol.

## Tests and prospective invocation

Tests use temporary synthetic ledgers and mocked pidfds, signals, process
identities, timers and patch subprocesses. They never signal real processes,
apply the live patch, inspect the actual current ledger, or call a provider.

```bash
SCOPE=research_loop/workers/replication_sprint_20260919/parenting/c2_handoff
python3 -B -m unittest discover -s "$SCOPE" -p 'test_*.py' -v
```

**Main only, after review; neither command was executed in this assignment:**

```bash
SCOPE=research_loop/workers/replication_sprint_20260919/parenting/c2_handoff
python3 -B "$SCOPE/handoff.py"
python3 -B "$SCOPE/handoff.py" --execute \
  --seed-sha256 14b4a285dda3abcb7ccd9421ccbd8135bd26883cde7cead410e52a56cd073330 \
  --install-sha256 5a42f5a572b2cdd3bcd80a8d4f43b7c5d1fab8b30b5c93f45eb6c55e45e20c96
```

The execute command is prospective usage, not approval of the sibling seed's
policy or authority to deploy it. Nonzero exit means refused, not ready or
interrupted; inspect the reported error and installation state rather than
automatically rerunning it.
