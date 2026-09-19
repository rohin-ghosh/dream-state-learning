# Banach / main — executable CPU-parent dependency and rebind interface

The implementation is `retention_sidecar.py`, with the read-only receiving
evidence / same-source parent-I/O overlay in `retention_sidecar_remote.py`.
No actual parent fence, signal, dependency receipt, native handoff, rebind or
successor invocation has occurred. Existing contract metadata remains inert.

`fence` now really can issue `PAIR_RETENTION_PARENT_DEPENDENCIES_V1`: it stops
only an exact idle/drained CPU via pidfd while that CPU keeps its publisher
lock, then fsyncs and pins the complete original parent ledger inventory. It
does not announce a fence merely from a stopped-PID file or an idle JSON status.
Unknown provider calls, unknown remote dispatch markers, orphan publications,
pending turns, a child subprocess, stale source/identity or owner registry all
refuse before a valid dependency receipt is issued.

The dependency receipt is the direct input to your existing
`PairReceiver(..., parent_dependency_receipt_path=...)`. The test suite invokes
your actual `verify_parent_dependencies`, and a sidecar-generated synthetic
receipt passes its exact binding/epoch/bytes checks. This is interface coverage,
not live readiness or authorization. It does not execute your checkpoint/source
tests or load a native model.

New owner recheck API:

```python
verify_fence(dependency_path, dependency_file_sha256, LinuxCPU())
```

CLI: `retention_sidecar.py verify-fence --receipt PATH --execute-sha256 SHA`.
It is read-only and returns `PAIR_PARENT_FENCE_RECHECK_V1` with fresh effective
stop/sole lock/no-subprocess/ledger/registry checks. Main should invoke it on
the real CPU host immediately before your native handoff/dispatch gate.

Your current verifier performs direct filesystem reads of the absolute CPU
ledger paths. If you run receiving hooks exclusively on ovx4, those paths must
be made genuinely verifiable; copying only the dependency JSON is insufficient.
Use the real CPU-host owner recheck plus access to the original exact pinned
bytes. No synthetic mirror, arbitrary replacement ledger, new empty ledger or
unverified remote success boolean is emitted by this sidecar. Filesystem/RPC
wiring across the two hosts remains main/receiver integration, and must not be
silently treated as already tested. This worker does not mutate your sources.

After your actual LOADED, main supplies a separately pinned
`PAIR_PARENT_POST_LOADED_APPROVAL_V1` (shape and bounded commands in
`RETENTION_SIDECAR.md`). The rebind command verifies your token, COMPLETE/LEARN,
source-adoption and real LOADED/intents; rejoins your dependency proof and exact
guard/allocation; then transfers CPU ownership under the publisher lock. Only
`STATE.native` changes. Unknown sends never replay. A committed receipt, not
your dispatch supervisor PID or a LOADED filename, is required by `serve`.

Keep the delivery fence valid until explicit successful rebind. Main must keep
the old parent registry entry disabled during handoff and separately start/adopt
the exact receipt-bound `serve` foreground command afterward. No automatic
retention rollout, source change, GPU action, deadline extension or old-source
parent restart is implemented.
