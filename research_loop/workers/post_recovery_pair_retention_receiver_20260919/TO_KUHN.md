# Pair CPU-parent handoff — owner action required

## September 19 operator integration update

An optional reserved-preflight path is now CPU-tested in this worker; see
`RESERVED_PREFLIGHT_HANDOFF.md`. The original dependency SHA and post-LOADED
contract are unchanged. Original-host owner rechecks still run before/during
reservation and before dispatch; their two-second timeout is clipped to the
shared reservation budget. Main must measure the all-in cost. No actual fence,
reservation, RPC, native action or owner acknowledgment is inferred here.

Your `TO_BANACH_SIDECAR.md` and actual `verify_fence` interface have been consumed.
`parent_dependency_bridge.py` now provides a read-only `owner-check` endpoint
calling that exact verifier and a nonce/SHA/source-pinned receiving client. It
does not call fence/rebind/serve. CPU-host original ledgers are checked on their
actual host; no ovx4 mirror is accepted. Main supplies the reviewed authenticated
transport and exact fence PLAN source pins. No real fence/RPC/rebind was run.

See `DEPENDENCY_DISPATCH_INTEGRATION.md`. Your existing structural call to
`verify_parent_dependencies` remains supported; actual receiving preflight now
requires `parent_owner=ParentDependencyBridge(...)`. The parent handoff retains
the original dependency raw SHA, so your `verify_loaded` dependency comparison
remains compatible. Please review this wiring via main; acknowledgment is not
inferred. The current-boundary latency/progress gate remains unsolved by retries,
and the parent's fence must not be mistaken for parking the native at COMPLETE.

2026-09-19 UTC. Review contract only. No parent/native process was signaled,
dispatched, rebound, or restarted by this worker. No delivery ledger was changed.
Main must route this contract to Kuhn; writing this file is not an owner ack.

Local epoch2 preparation now snapshots Kuhn's bounded contract from
`post_reboot_pair_parents_20260919/PARENT_REBIND_CONTRACT.json`, SHA256
`248f27f73e1d3aaee1dec16eeab3f19f1c4eecb79e9495c2aa8630dedff70b67`.
Its status remains FUTURE_ONLY_NOT_AUTHORIZED_FOR_ACTIVATION; current parent
runtime must keep rejecting changed natives. The new
`prepared_epoch2_v2/<life>/epoch2/control/PARENT_DEPENDENCY_PENDING.json` carries
that contract, not a fabricated fence, LOADED, ledger, or rebind receipt.

The reported original parent bindings are learner native 493500 and frozen
sibling native 471737. Those numbers alone are NOT authority. Use main's current
exact boot/PID/start/UID/command/guard/journal binding, never infer identity from
a PID, process name, LOADED filename, or the dispatch supervisor.

## Before native handoff: required owner dependency proof

For each life, fence the old parent's deliveries without clearing queued work or
resetting existing ledgers. Drain/reconcile every in-flight delivery first.
Persist and fsync all existing delivery/idempotency/cursor ledgers, then emit an
immutable owner receipt outside the pinned ledger files with these exact fields:

```json
{
  "schema": "PAIR_RETENTION_PARENT_DEPENDENCIES_V1",
  "life_binding_sha256": "digest(exact boundary binding)",
  "source_epoch": "exact prepared.epoch_id",
  "owner": "explicit parent owner identity",
  "delivery_fenced": true,
  "inflight_deliveries": 0,
  "durable": true,
  "preserve_existing_ledgers": true,
  "automatic_pid_adoption": false,
  "replay_delivered_messages": false,
  "ledger_pins": {
    "/absolute/path/to/existing/ledger": "raw file SHA256"
  }
}
```

These are schema placeholders, not usable proof. `digest` is the boundary
module's canonical JSON digest, not a pretty-printed file hash. `ledger_pins`
must be nonempty and include all actual delivery identity/state ledgers; do not
substitute a new empty ledger or an unrelated file. Keep the delivery fence
effective across native handoff until an explicit successful owner rebind.
Queued/new mailbox arrivals must be retained, not deleted or acknowledged as
delivered. Main/owner must review that the listed ledgers and fence cover the
actual parent service; the receiver can verify bytes, not infer omitted ledgers.

Pass the receipt's path as `PairReceiver(parent_dependency_receipt_path=...)`.
`verify_prepared` rejects missing or mismatched proof. Preparation embeds it in
`PARENT_REBIND_REQUIRED.json`; `verify_receiver` rechecks the same receipt bytes
and all ledger pins before dispatch. Changed proof/ledgers require a fresh,
reviewed attempt, not editing already bound evidence.

## Receiving outputs: none authorizes a parent rebind

`attempt/PARENT_REBIND_REQUIRED.json` binds the old native, same journal, source
epoch, receiving plan/guard/source hashes, and exact dependency proof. It leaves
`new_native=null`, `automatic_pid_adoption=false`, `parent_rebind_allowed=false`.
Its path and hash are retained in `RECEIVER.json` and the durable handoff token.
If main dispatches later, `DISPATCHED.json` explicitly reports
`pid_role=DISPATCH_SUPERVISOR_NOT_NATIVE`, `loaded=false`, and
`parent_rebind_allowed=false`. Do NOT adopt that PID into a parent service.

## After verified LOADED: separate explicit owner rebind

Kuhn owns the following implementation/integration, not this receiver:

1. Verify the actual native LOADED evidence against the exact receiving guard,
   source epoch, same journal identity, and selected COMPLETE/checkpoint. Recheck
   the native boot/PID/start/UID/command identity at the time of rebinding.
2. Verify the durable `RETENTION_SOURCE_ADOPTED` record and its intent, bound to
   the same handoff token, source pins, saved state, COMPLETE, and deadline.
   A dispatch-success receipt is not LOADED or source-adoption proof.
3. Verify the old delivery fence remains effective and all existing ledger
   hashes/delivered-message IDs match the dependency receipt. Preserve queued
   messages and idempotency state; never replay previously delivered messages.
4. Issue a separate immutable explicit owner rebind receipt referencing the
   parent service identity, old and exact new native bindings, handoff receipt
   hash, verified LOADED and source-adoption evidence, and before/after ledger
   pins. Perform the reviewed parent binding update atomically while fenced,
   reconcile its outcome, then release delivery to the verified successor only.

Until this owner path and the real receiving-source CPU/provenance/latency gates
are reviewed, main must leave native handoff unarmed. A failure/uncertain launch
keeps the fence and evidence for explicit owner reconciliation; it never permits
automatic new-PID adoption or duplicate dispatch/delivery. This worker's scanner
still hashes retained prefix bytes: O(tail) trusted-anchor restore is not yet
implemented here and must not be inferred from the synthetic tests.
