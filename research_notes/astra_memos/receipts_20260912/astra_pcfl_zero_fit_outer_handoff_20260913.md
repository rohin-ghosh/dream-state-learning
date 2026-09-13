# PCFL zero-fit outer — EDITSTOP, 2026-09-13

Owned only this handoff and the two files below. Other owners' driver, actor,
CLI, profile, source snapshots, failed measurement and fixed roots remain
untouched. No native/GPU/model/remote/queue command was executed by this author.

## Final pins and CPU checks

- `gpu/astra_pcfl_zero_fit_outer.py`:
  `7111fc4a3a5441776a30931341a2536d01d0c6859f972dab8f28d9e8662ceb69`
- `tests/test_astra_pcfl_zero_fit_outer.py`:
  `ab6ef5cd96f1c55168d81d0f5cab173a9f75c6645ad320508cdb3fa544929ac2`

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_astra_pcfl_zero_fit_outer.py' -q
```

Final result: **29 tests PASS, 84.647s**. AST parsing and trailing-whitespace
checks also pass. No native libraries/models were loaded; GPU queries, Popen,
signals and /proc are mocked. A late-deadline test mocks the clock. Synthetic
tokenizer/report fixtures satisfy the public outer schema but are NOT actual
offline measurement or native-generation evidence. The real driver manifest
validator and finalizer run without monkeypatching their behavior. No existing
scientific tests or scorer code were changed.

Final dependency hashes matched immediately before/after the suite:

| Dependency | SHA256 |
|---|---|
| `gpu/astra_pcfl_zero_fit_command.py` | `172f49a4a104f63920c5a7d139b793954706cf221604792fbeced20ef151d169` |
| `gpu/astra_pcfl_zero_fit_dev.py` (Main's Mapping repair) | `7bcc99f89b661f2f77202c3cc5aa61533bad2daff25f5b548ed8e1ecd1c1b5d5` |
| `gpu/astra_pcfl_native_actor.py` | `f6aae63e79213c24523201452e7f7de880167c4fb273db18de83f93a3a4f7a26` |
| `organism_v6/pcfl_vertical_prepare.py` | `c07ba9b684299a8d6cf6c7b45bbdbb95ed6f3e04db9e8de6e926791610b55c61` |

The outer does not embed a stale driver pin: it validates the manifest's
current source snapshot and every supplied actor source-file hash. Main must
freeze/deploy the source bundle and prepare a new manifest against the repaired
driver; there is no path rewrite, reselection, or modification of old attempts.

## Stable Python API / CLI

```python
controller(manifest_path, manifest_sha256, allocation_path,
           allocation_sha256, outer_dir, cleanup_seconds=120)
finalize(outer_dir, capture_sha256)
```

`manifest_sha256` and `allocation_sha256` are **exact file-byte SHA256s**.
`capture_sha256` is the exact `capture_complete.json` file SHA returned as
`capture_file_sha256` by controller and printed by the CLI. It is not the
driver's internal manifest/report canonical seal.

```sh
env CUDA_VISIBLE_DEVICES='' PYTHONPATH="$SOURCE" "$PY" -B "$SOURCE/gpu/astra_pcfl_zero_fit_outer.py" run --manifest "$MANIFEST" --manifest-sha256 "$MANIFEST_FILE_SHA" --allocation "$ALLOCATION" --allocation-sha256 "$ALLOCATION_FILE_SHA" --outer "$FRESH_OUTER_DIR" --cleanup-seconds 120
# After the worker has exited AND any Main/queue holder has exited:
env CUDA_VISIBLE_DEVICES='' PYTHONPATH="$SOURCE" "$PY" -B "$SOURCE/gpu/astra_pcfl_zero_fit_outer.py" finalize --outer "$FRESH_OUTER_DIR" --capture-sha256 "$CAPTURE_FILE_SHA"
```

Main supplies all variables. No host/IP, remote interpreter, lease or allocation
literal is guessed. The outer must start with CVD explicitly empty, not merely
clear it after process creation. Only its child gets the exact manifest UUID.
Child argv is `[allocation.python, '-B', command.py, 'run', '--manifest',
absolute_manifest_path, '--manifest-sha256', manifest_file_hash]`, launched
with `start_new_session=True`, separate exclusive stdout/stderr files and
offline/telemetry/spawn settings. The actual venv executable path may be supplied
as `python`; its resolved identity must match the actor's interpreter binding.

There is no automatic second run or automatic collection. Import does not
launch or query hardware. The outer does not submit jobs or choose GPUs.

## Closed allocation schema

Every field is required; extras are rejected:

```text
schema: "pcfl.zero_fit_outer.v1/allocation"
gpu_index: nonnegative int, not bool
gpu_uuid: actual allocated GPU-... UUID
boot_id: actual native boot ID (prepared monotonic domain)
uid: actual controller UID
python: absolute native interpreter executable
queue_dir: absolute existing directory with pending/ and running/
queue_mode: "direct" | "managed"
queue_allowlist: {"pending": {filename: exact_file_sha256},
                  "running": {filename: exact_file_sha256}}
coordination_owners: [exact_identity, ...]
lease_end: positive Unix timestamp
lease_margin_seconds: positive Main-selected margin
outer_sha256: exact frozen outer source SHA256 above
```

An exact identity is the closed object
`{pid, pgid, sid, start_ticks, boot_id, uid}` with strict integer numeric fields.
For the simplest direct launch use empty pending/running dictionaries and
`coordination_owners=[]`. In managed mode at least one running entry must be
pinned; Main provides the actual existing queue coordination, not arbitrary
invented job bytes. Queue directories/entries cannot be aliases/symlinks or
nonregular files. This is a snapshot agreement with Main, not a new scheduler.

`coordination_owners` are NOT arbitrary CVD exceptions: at preflight every one
must exactly match the outer's currently verified ancestry. Own-controller or
ancestor exclusions are enumerated explicitly in `excluded_own_ancestors`.
No process-name, daemon-name, user-wide or foreign-process exception exists.
Finalization ignores this allowlist and permits **no** explicit same-UID CVD
owner or unresolved same-UID environment read on the assigned index/UUID/all.

## Checks and receipts

Public check helpers: `validate_allocation`, `check_node`, `check_queue`,
`check_cvd`, `check_gpu`, `identity`, `group_members`, `cleanup_owned`.
They perform local observations only when explicitly called. Preflight records
the pending/running snapshot, same-UID explicit-CVD reservations and exact
allocated index→UUID plus all-user compute-process query. Unknown queue changes,
GPU occupancy/query timeout/bad rc, UUID drift, unreadable CVD metadata, source
drift, expired allocation or nonempty outer CVD prevent spawning.

The outer directory and sibling `<diagnostic-output>.outer_claim.json` are
exclusive once-only claims. Existing diagnostic output cannot be reopened.
Initial context binds manifest/allocation files, controller identity, original
entry/deadline and output path. `spawn.json`, `worker_start.json`,
`worker_wait.json`, `worker_exit.json`, `worker_release.json` preserve command,
PID/start ticks/PGID/SID/boot/UID, timing and exact return code. Bool return codes
are rejected, both for workers and GPU query commands. Raw stdout/stderr remain.

Timeout/error triggers cleanup of only the verified isolated worker PGID,
checking leader identity and surviving members' session/UID/start ticks before
TERM/KILL. Each signal waits at most three seconds; all loops/queries obey the
original remaining deadline. A reused PID, wrong session, wrong boot, inaccessible
start identity or foreign member is never blindly signaled. Primary worker
errors and cleanup failures are preserved separately, including when cleanup
itself fails. If the initial identity cannot be verified, the process may need
Main reconciliation: the controller records failure and NEVER claims release.
Abrupt external SIGKILL of the controller likewise cannot certify cleanup;
Main remains responsible for that abnormal outer-process lifecycle.

Capture performs fresh post-worker compute/CVD observations and preserves three
distinct fields: `worker_group_released`, `gpu_compute_vacant`,
`reservation_released`. A known ancestor still holding CVD makes the last field
false even when compute is empty. Capture status is
`CAPTURED_AWAITING_RESERVATION_RELEASE`, `finalized=False`; it is not a release
or full-assay result. Fixed 800 task IDs/scored counts, 800..1952 actor attempts,
native close status, report/source/config seals and zero fits/updates are checked.
All diagnostic-output file sizes/hashes and outer capture-receipt hashes are
bound into `capture_complete.json`.

One-shot finalize verifies the externally supplied capture hash, original
manifest/allocation/source pins and unchanged output inventory; requires the
owned group gone; accepts only removal (not new/changed entries) from the pinned
queue snapshot; and checks GPU compute vacancy plus CVD absence again. A final
CVD/group scan follows the GPU query to detect a late owner. Main must release
its holder before invoking finalize; a premature invocation consumes the
finalize claim and records failure rather than silently retrying.

`release_attestation.json` contains exactly the finalizer's five fields:
`report_sha256, gpu_uuid, owned_group_released, gpu_vacant,
elapsed_seconds_from_start`. `release_receipt.json` adds the absolute native
`evidence_path` and exact byte `evidence_sha256`. Raw process/GPU/CVD/queue evidence
is separate. `collection.json.files` crosslinks their exact hashes, attestation,
receipt, capture, unchanged report inventory, and the real finalizer's
`final.json`. A valid collection requires its success receipt and absence of
controller/finalize/cleanup failure, not an isolated final.json. Negative panel
thresholds are preserved and are not execution failure or grounds for retry.

## Timing and scope limits

Outer entry is sampled before validation and spawning, so the cap includes
command.run's offline tokenizer load **before** Diagnostic.started, all cold
model loading, generation, close, process cleanup and finalization. Hard deadline
is the minimum of original outer entry+wall/device caps (at most 36000s), the
unchanged prepared actor absolute monotonic deadline, and lease end minus the
bound margin converted on the current node. Prepared validity therefore includes
queue wait; neither command nor outer refreshes it. Cleanup reserve is an exact
integer in 30..120 seconds, default 120; worker wait ends that far before the
hard deadline. Finalization remains within that SAME envelope, not a fresh cap.

The exact finalizer elapsed is
`release_monotonic - report.started_monotonic`, while
`collection.outer_elapsed_seconds` measures from original outer entry through
finalization work. Both are recorded and constrained; neither generation-only
time nor the later report start replaces total outer elapsed. Same-boot checks
precede capture/release; the driver retains its own cold-load/close time as-is.

Checks certify observed compute/process/reservation conditions, not future
vacancy or a kernel-wide atomic lease. CVD scanning is explicitly same-UID,
explicit-environment only; it is not inspection of every user's future GPU
intent. Compute queries are all-user, not a display/graphics qualification.
Main supplies compatible queue coordination and hardware ownership. This is not
a full guard gate or a new transitive-source signing framework. The output byte
inventory/report checks do not replace independent replay of every raw model
call; they preserve those artifacts for the existing scientific validation.
No score changes, fits, retries, root reselection, C11 qualification, H1/H2 claim,
or full-v2.2 promotion is introduced.
