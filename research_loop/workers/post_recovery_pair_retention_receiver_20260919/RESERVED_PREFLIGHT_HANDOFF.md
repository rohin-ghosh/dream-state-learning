# Optional bounded reserved preflight — review-ready, NOT activated

[Builder] September 19, 2026 UTC. Non-material same-checkpoint continuity repair.
All implementation changes remain inside this worker. The shared boundary
coordinator, native sources, prepared/staged epoch2, root history, deadlines,
scientific claims, controls and confinement are unchanged. No actual native or
parent signal, reservation, remote probe, handoff, service management or dispatch.

## Concrete feasibility

The default path still prepares before reserving. It cannot reliably catch a
brief COMPLETE window while an 8–19 second reader runs. The new **opt-in**
`reserved_preflight.coordinate_reserved` instead performs:

1. Exact execution approval, same-life lock, one exact pidfd, static source,
   controls, checkpoint-family evidence, admission availability and owner checks.
2. Observe the actual COMPLETE+LEARN; check that checkpoint's family/COMMIT;
   persist a crash/retry gate; enter the existing pidfd guardian reservation.
3. Immediately confirm stopped exact identity and the same boundary. If already
   past COMPLETE, resume the same handle. Retry only a different COMPLETE, not
   the same missed candidate. No payload probe runs on this early race.
4. Under one conservative monotonic budget, run the full actual saved-payload
   proof, receiving checkpoint+tail restore, metadata-only consumed-wall proof,
   exact preservation/guard preparation, fresh CPU-owner checks and all existing
   source/checkpoint/identity/durable COMPLETE+LEARN/INBOX checks.
5. Only with the full proof and remaining margin may the unchanged guardian
   accept COMMIT. Confirm exact exit and exclusive writer access before issuing
   the unchanged handoff token and original dispatch entry point.

The total reservation remains **at most 30 seconds**. Its budget starts before
`reserve` (conservative relative to guardian STOP), not after restore. A margin
of at least one second is mandatory; the example below leaves two seconds.
CPU-probe and owner-RPC timeouts shrink to the shared remaining budget. Probe
children inherit no pidfd, have no native signaling role, and `subprocess.run`
kills/waits for its own helper on timeout. No background preflight worker exists.

Expiry, late guardian refusal, corruption, missing proof, owner failure or a
post-proof race is terminal: context exit resumes the old handle unless the
guardian already resumed it; no automatic re-reservation or dispatch follows.
`RESERVED_PREFLIGHT_REVIEW_REQUIRED.json` remains, blocking a new invocation.
Main must reconcile it; do not delete it to make a retry look fresh. Only a
verified early race clears this worker's own gate after reservation exit and a
same-handle running-identity check. A crash before that clear also fails closed.

**This creates a reachable synthetic handoff path, not proof of live timing.**
Main's historical COMPLETE reader costs (19.00s frozen, 8.06s learner) plus
approximately 1.8s payload leave a possible, not yet measured, margin. Full
prefix hashing remains O(retained journal bytes). Repeated source/owner checks,
guard CPU validation/imports, fsync, observation, identity and final audit must
ALL be included in the bound. The guardian remains the hard safety limit when
estimates are wrong. No larger stop cap or historical rollback is implemented.

## Exact opt-in API

`integration.build_operations` retains its old default when
`reserved_preflight_policy=None`. A policy selects the new operations class:

```python
policy = {
    "schema": "PAIR_RESERVED_PREFLIGHT_POLICY_V1",
    "stop_seconds": 30,
    "commit_margin_seconds": 2,
    "static_receipt_path": "/absolute/main-reviewed/STATIC.json",
    "static_receipt_sha256": "<exact sha256 of STATIC.json bytes>",
}
```

Main computes `execution_digest(binding, prepared, authority, policy)` from
`reserved_preflight.py` and reviews that exact strategy. The old coordinator
execution digest does **not** authorize this path. Pass the policy and digest to
`build_operations(..., reserved_preflight_policy=policy,
approved_execution_sha256=reviewed_digest)`. Construction activates nothing.
Only main may call `coordinate_reserved(binding, prepared, authority, operations,
policy=policy)` after the following real receipts exist. No activation CLI exists.

The pinned static receipt has schema `PAIR_RESERVED_PREFLIGHT_READINESS_V1`:

- `life_binding_sha256=digest(binding)`, `prepared_sha256=digest(prepared)`,
  `source_pins_sha256=digest(prepared['new_source_pins'])`;
- exact `epoch_id`, unchanged `deadline_unix`, receiving plan's `physical`;
- `checks` containing all-true `actual_saved_payload_CPU`,
  `actual_checkpoint_tail_CPU`, `exact_source_control_tests`,
  `original_confinement_admission_available`,
  `owner_transport_and_guard_cost_bounded`;
- `reserved_total_seconds_upper_bound`: finite, positive, strictly less than
  `stop_seconds - commit_margin_seconds`;
- `evidence_pins`: original absolute evidence file paths to exact raw SHA256s.

No positive static receipt is generated by this worker. Main must bind actual
evidence; old historical benchmarks alone cannot assert all these checks.
Static checkpoint-family evidence never substitutes for candidate-specific
saved model/optimizer/Python+CPU+CUDA RNG/working-state proof under reservation.
If management preflight is unavailable, stop; never bypass original admission.

## Parent-owner contract

Use the existing nonce-bound `ParentDependencyBridge` and Kuhn's original-host
`verify_fence` endpoint. Its maximum timeout remains two seconds, further clipped
inside reservation. The original raw dependency bytes/SHA remain in the
receiving handoff, so Kuhn's actual `verify_loaded` join remains unchanged.
Owner rechecks occur before the reservation, during preparation, before commit,
after exact exit and before dispatch. Parent fencing is not native parking.

After real LOADED and RETENTION_SOURCE_ADOPTED, Kuhn still supplies a separate
exact new-native rebind/serve receipt. Neither this coordinator nor the dispatch
supervisor PID adopts a parent or resets/replays any ledger. No owner agreement,
fence, transport success, rebind or receiving admission is claimed here.

## CPU-only commands and results

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s research_loop/workers/post_recovery_pair_retention_receiver_20260919 \
  -p 'test_*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s research_loop/workers/post_recovery_retention_boundary_20260918 \
  -p 'test_*.py' -q
```

Latest bound run: **63 pair tests, 1.296s; 83 unchanged boundary tests, 0.213s;
PASS**, in `RESERVED_CPU_RECEIPT_v1.json` (September 19, 2026 02:10 UTC).
New coverage includes live-like unreserved advancement, reserved 21-second
simulated proof success, early race/same handle, pending REQUEST, guardian and
budget expiry, no repeated reservation, persistent review gate, corrupted or
missing saved state, owner refusal, late/mutated boundary, all arriving INBOX,
slow final audit, strategy-specific approval, unchanged 30-second cap and
static evidence/overhead gating. A real harmless CPU helper timeout test verifies
helper reaping and closed inherited descriptors; native signaling/fork/dispatch
are forbidden or mocked in coordinator tests.

## Remaining live blockers

1. Main's transport/selection and bound actual-source receipts for the prepared
   epoch3 closure in `prepared_epoch3_v1` (see `EPOCH3_HANDOFF.md`). Local sealing
   is complete; epoch2 alone retains the slower implementation.
2. Real all-in reserved cost bound and original management/confinement admission
   availability; neither has yet been supplied to this worker.
3. Actual Kuhn fence/dependency plus reviewed authenticated original-host RPC,
   same original ledger pins, source-epoch-bound parent rebind plan.
4. Fresh exact native/boot/start/guard/journal binding, consumed WALL_EXTENDED
   record+intent, real CPU receipt and new reserved-strategy approval.
5. Actual candidate proof under the bounded reservation, then original dispatch
   admission and actual LOADED before explicit owner rebind. These are runtime
   gates, not claims produced by CPU tests or historical timing.
