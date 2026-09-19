# Operator-only integration; current-boundary progress remains a separate gate

**Update:** the original/default ordering described below is retained. The
new optional executable `reserved_preflight.coordinate_reserved` and its exact
approval/receipt contract are in `RESERVED_PREFLIGHT_HANDOFF.md`. It moves only
candidate-specific proof under the unchanged bounded guardian; it does not
claim measured live feasibility or relax owner/admission checks.

September 19, 2026. No native/CPU-parent signals, handoffs, reservations, remote
probes, service management, or dispatch were performed here. No organism/history,
checkpoint reader, epoch1 or staged epoch2 source was edited. Main's possible
byte-equivalent history performance port belongs to main, not this worker.

## The 37-second question: safety is not progress

The current optimistic protocol can only finish if the exact selected
SLEEP_COMPLETE+LEARN remains current through preflight, allowing only INBOX
arrivals. It cannot reliably do so if the native begins the next REQUEST while
the CPU spends 37 seconds validating that candidate. A bounded immutable-cutoff
observer proves historical state, not that the live native is still there.
Replacing the current head with the historical cutoff, replaying old state,
ignoring new work, or extending the reservation would be incorrect.

Main's actual COMPLETE-only measurements supersede tiny synthetic timings:
sibling 37.08s = 18.50s prefix + 18.58s restore; learner 14.77s = 7.93s prefix +
6.84s restore. Main identified repeated TrainHistory restore/frontier work in a
long historical tail, not an unexplained hash bottleneck. No reader redesign or
second investigation was performed. O(tail) is not imposed as a requirement.

Source/guard/control preparation and immutable historical checkpoint/prefix
proof can be done ahead of time. Final adoption still requires proof for the
actual current exact boundary. Main must demonstrate a viable candidate-bound
fast path/window or separately review a boundary synchronization protocol before
activation. A performance port may reduce the cost, but does not by itself make
the native wait at COMPLETE. This integration does not claim that progress gate
has been solved and must not be activated merely because these CPU tests pass.

## Implemented retry and dispatch plumbing

Use `PairLinuxOperations`, not bare `LinuxOperations`, for this receiver:

- Expensive saved-checkpoint verification and receiving preparation run inside
  the coordinator's retryable observation phase, before any reservation.
- A moved COMPLETE or narrowly identified `journal_changed_during_scan`,
  `unraced_tail_probe`, or changed resolved state yields `ObservationRace`.
  The existing coordinator retries on the **same open native handle**.
- The prepared proof/artifact cache is bound to that candidate. The next native
  state is compared before a reservation; the reservation exit drops the cache.
- Observations while reserved never rerun checkpoint/tail preparation. Existing
  exact state, file hashes, fresh parent proof, intents and deadline checks remain.
- Probe timeout is a durable terminal pre-stop refusal, not 200 slow automatic
  retries. Corruption is not mislabeled as a race. No full-replay fallback exists.
- Exclusive dispatch claims and original `gpu.r232_recovery dispatch` admission
  remain unchanged. DISPATCHED is explicitly a supervisor PID, not LOADED and not
  a parent-rebind authorization. No management restriction is bypassed.

The real coordinator regression uses synthetic operations to lose the first
preflight boundary, then succeed: one handle open/close, one wait, one simulated
commit/dispatch. No live process is involved.

## Kuhn owner bridge: original CPU files, no fabricated mirror

`parent_dependency_bridge.py` exposes only `owner-check`. On the real CPU host
it calls Kuhn's existing `verify_fence(path, raw_sha256, LinuxCPU())`; it never
calls `fence`, `rebind` or `serve`. Kuhn checks the effective stopped owner,
publisher lock, disabled registry, drain state and complete original ledger
inventory. The endpoint returns the exact dependency-file bytes and bound
verification, not a new ledger or an unverified success boolean.

The receiving-side `ParentDependencyBridge` executes only main's supplied,
reviewed authenticated transport command with a nonce-bound JSON stdin request.
It checks exact dependency SHA/path/life/epoch, old parent, original ledger pins,
reviewed owner source closure, fresh timestamp, and bounded elapsed time. The
default total RPC timeout is two seconds; a slow or inaccessible owner is a
refusal, never permission to use a stale JSON copy. Main must validate this
transport on the real hosts; no actual cross-host exchange has been performed.

The endpoint verifies the sidecar import closure before import. The owner command
tail, for main to place behind its existing authorized transport, is:

```text
/usr/bin/python3 -I -B ABSOLUTE_OPERATOR/parent_dependency_bridge.py owner-check
  --sidecar ABSOLUTE_KUHN_WORKER/retention_sidecar.py
  --sidecar-sha256 EXACT_CURRENT_SIDECAR_SHA256
  --dependency ORIGINAL_CPU_TRANSACTION/PARENT_DEPENDENCIES.json
  --dependency-sha256 EXACT_DEPENDENCY_FILE_SHA256
```

These named inputs are required binding values, not executable authorization.
The receiving client supplies stdin; do not hand-write a positive response. The
bridge file itself must also be pinned by main's transport deployment. If an
existing managed transport denies access, stop; do not use another identity,
privileged route or unchecked ledger mirror.

`parent_owner_config` has concrete constructor fields:

```python
{
    "command": reviewed_read_only_owner_transport_argv,
    "dependency_path": original_CPU_dependency_path,
    "dependency_sha256": exact_dependency_file_sha256,
    "owner_source_pins": exact_Kuhn_fence_PLAN_source_pins,
    "timeout_seconds": 2,
    "max_clock_skew_seconds": 5,
}
```

`PairReceiver.verify_prepared` now requires this fresh owner bridge. Its separate
`verify_parent_dependencies` retains direct-file structural verification for
Kuhn's existing interface tests, but structural verification alone cannot enter
the receiving preparation or dispatch path. With a bridge, original ledger
validation occurs on the CPU host, not at identically named ovx4 paths.

## Concrete construction; no automatic activation

`integration.build_operations(binding, prepared, authority, staged, ...)` takes
the real CPU receipt path, original consumed-wall record/intent, approved venv,
existing control root, `parent_owner_config`, and exact
`approved_execution_sha256=digest({binding, prepared, authority})`.
It returns `(receiving, operations)` without executing the coordinator, signals,
remote checks or dispatch. It has no activation CLI. Main alone may later call
the existing explicitly reviewed coordinator after the current-boundary gate and
all owner/admission dependencies are actually satisfied.

`package_operator.py` creates a fresh worker-local operator bundle: receiving
helpers, the unchanged boundary implementation, and package initializers. Do not
put this bundle in an immutable receiving source. Main should place its root on
the operator Python import path; `cpu_probe.py` is included at the path the
receiver resolves beside itself. The GPU/native source closure stays unchanged.

## Parent after LOADED

The existing receiving `PARENT_REBIND_REQUIRED.json` carries the original CPU
dependency file SHA. Kuhn's `retention_sidecar_remote.verify_loaded` already
compares that exact SHA with the post-LOADED approval and validates the actual
COMPLETE/LEARN/adoption/LOADED chain, guard and native identity. It does not need
a copied CPU ledger on ovx4. Rebind/serve remain separate explicitly approved
owner operations, preserving ledgers and preventing duplicate publications.
No automatic PID adoption or parent resume is introduced by this integration.

## Tests and ready artifacts

41 own-worker regressions pass, including six owner-RPC tests, six preparation
phase/coordinator tests, three probe failure tests, and the existing receiver/
source-preparation tests. 83 boundary tests pass unchanged. All process effects
and RPC are mocked; temporary fixtures stay inside this worker. The selected
operator bundle, its SHA manifest and dated Builder provenance are under
`operator_bundle_v1/`. The 209-file epoch2 and main's real checkpoint/source CPU
receipts remain separate evidence, not rewritten or reclassified as admission.
