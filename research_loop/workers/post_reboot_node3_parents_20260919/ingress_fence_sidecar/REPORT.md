# Existing-ingress fence assessment — OFFLINE / BLOCKED

Scope: non-material, source-only diagnostic sidecar. No changes to the sealed
03:01 transactional candidate, existing deployment, aliases, services, deadlines,
epochs, natives or scorer. No new network/kernel observation was attempted,
including alternatives to previously platform-denied tools.

## Precise result

**No complete fence-and-drain operation is supported by the inspected original
live-source interface using the evidence capabilities currently permitted.**
There is a supported dynamic **routing** operation, but it is not an acknowledged
admission fence and cannot revoke work that already captured an old route.

The two original bridge route files recorded in the preserved cut are:

1. `/localhome/local-rohing/orch_r233_lease_renewal_20260918/attempt2/shared2/bridge/TARGET.json`
2. `/localhome/local-rohing/orch_r233_judge15625_20260918/judge15625-shared2-v1/bridge/TARGET.json`

Each bridge handler rereads the file after receiving a frame, then stores
`target` locally before opening its upstream socket. A later owner replacement
would affect only handlers that have not read the file yet. **No replacement,
deletion, socket exchange or alias operation was performed against these paths.**

## Original-source evidence and concrete counterexample

`owner_plan.py` checks the byte-pinned deployed `lease_bridge`, `transport_proxy`
and `shared_scorer` sources before emitting any assessment. Pins match the
preserved deployed129-file manifest, not an assumption about the current checkout.

- `lease_bridge.py:57` captures TARGET; `:59` sets
  `max(.1, stop-time.time())`; `:60` connects and `:61` sends. No intervening
  fence-generation check or cancellation exists.
- A handler can read the old target, be descheduled, and later connect/send to
  it **after TARGET replacement and even after its stop/deadline**. The code
  permits a 0.1-second connection timeout then; it does not cancel the operation.
  Hence waiting108/110/115 seconds, or deleting TARGET, is not drain proof.
- `transport_proxy.py:27` loads configuration once. Its per-request body writes
  TRANSPORT only after outcome, so changing the config is not a running fence
  and missing log entries do not enumerate missing admissions.
- `shared_scorer.py:82` executes the callback synchronously before `:89` writes
  its result. Callback completion is not implied by client/bridge timeout, CPU
  process exit, or the absence of later session updates. The old server exposes
  no external close/drain acknowledgment API; its `server_close` is internal
  cleanup, not an operator command endpoint.

The regression executes the **unmodified original nested bridge Handler AST**
with fake socket objects and a controlled clock in temporary CPU fixtures.
It pauses immediately after target capture, changes only a fixture TARGET,
then resumes. The handler still selects the old target; advancing far beyond
stop/deadline still produces its connect/send with timeout0.1. These are code
counterexamples, **not claims about an actual presently-running handler**.
No real network/socket inspection or live scorer invocation is involved.

## Additional integration constraint

The legacy native bridge forwards the proxy's
`{session_id, request, records}` envelope. The sealed transactional relay's
**native** sockets accept `{origin, metrics}`. Pointing a legacy bridge TARGET
directly at those native sockets is therefore not a valid source-bound failure
route. It would require a separately specified envelope-compatible denial
endpoint; no such endpoint is assumed deployed or started here. The existing
candidate's planned **source-alias** placement uses the correct native wire.

## Irreducible blocker within this task

The missing fact is whether any old handler has captured an old target, any
old listener/SSH path retains an accepted or queued call, or the original scorer
still owns a callback whose caller has timed out. The original application
does not issue an acknowledged admission fence or exhaustive admission ledger.
The currently permitted artifacts cannot establish these lifetimes, and the
previously denied kernel/network observation cannot be obtained through another
utility, procfs/netlink access, custom socket code or equivalent workaround.

Thus **neither an executable live mutation plan nor readiness can be justified**
under the present observation/control scope. Main's queue review can reconcile
known completed requests; it cannot, by itself, close the unenumerated-admission
set. A genuinely authorized lifecycle-control/evidence capability that resolves
that set is required before original-writer retirement—not a new assertion of
zero, a synthetic barrier request, or a longer quiet interval. No alternate
denied-information collection command is supplied.

The52 complete /26 never-dispatched origins belong to the immutable
**September19, 2026 02:36:19.482254 UTC** cut. The sidecar explicitly labels that cut
historical, records `admission_closed=false` and `kernel_backlog_observed=false`,
and never treats it as a fresh drain or a currently measured queue.

## Executable read-only owner assessment

```sh
python3 -B -m research_loop.workers.post_reboot_node3_parents_20260919.ingress_fence_sidecar.owner_plan
```

It reads pinned local source/artifacts only, writes JSON to stdout, and exits
**2 = BLOCKED**. A source/evidence mismatch also fails closed. It has no remote,
kernel, service, socket-control or mutation API. `OWNER_PLAN.json` retains its
output; `executable_live_actions` is empty by design rather than a hidden apply
step. The sealed transactional candidate remains unchanged at manifest SHA256
`e00ed71d18f9dfd4cb7e41f020927fe4e292a5fa529ea885ca5968df82b762dc`.

## CPU tests

```sh
python3 -B -m unittest research_loop.workers.post_reboot_node3_parents_20260919.ingress_fence_sidecar.test_owner_plan -v
```

Eight tests cover dynamic route reads, post-read replacement/removal races,
post-deadline connect behavior, exact two retained route files, stale-evidence
rejection as readiness, source-pin failure, and absence of live observation APIs.
See `CPU_TESTS.txt` and `MANIFEST.json` for the result and sealed sidecar hashes.
