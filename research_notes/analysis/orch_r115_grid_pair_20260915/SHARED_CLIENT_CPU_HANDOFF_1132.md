# Grid shared client — CPU handoff, not activated

2026-09-15 11:32 UTC. Main owns coordinator initialization and Git publication.
Neither F4 nor A4 has an actual `SHARED_CLIENT_READY.json` from this helper.
The current resident loops remain frozen-BASE elicitation-only. A1004 and
NODE3_6 are extra lanes, not members of the shared eight.

## Exact source and tests

- `gpu/orch_r116_grid_shared_client.py`: `ebb5a34315054db61af8f8edfdb7f9ccb70db3283ef0d096449c9a0beebf3577`
- `tests/test_orch_r116_grid_shared_client.py`: `961410ee77430d99c6e4f4aca04a49c5bef37ea221b1800f8b7ee1534fdca1fe`
- Current Main coordinator tested: `gpu/orch_r116_shared_learner.py`, `61e5e32cffe299285d95e10274500811649a09dac44da995d4703da041c0ed2e`.
- Latest local client plus coordinator suite: 52 PASS in 1.91 seconds.
- Earlier native CPU suite: 50 PASS at `/localhome/local-rohing/orch_r116_grid_shared_cpu_20260915_v1`, log SHA `ebaa2c69d099c9b607800e0daa5203cdc4a02adafc7de35d65dbcdc1b294035b`. That suite used an earlier coordinator; it is not claimed as native validation of the current coordinator.

## Wiring contract

1. `prepare(shared_root, branch, config_sha256=...)` validates the actual common
   CONFIG/STATE, complete checkpoint, same-owner optimizer file hash, adapter and
   frozen base. It returns the exact generation and checkpoint-bound session.
2. `load_shared(session, model_dir=..., gpu_uuid=..., check=..., readout=False)`
   loads only the published shared adapter using the native collection seam.
   The branch has no optimizer and no trainable parameters. For sealed readout,
   call this with `readout=True` in a fresh process; do not use the old BASE loader.
3. `SharedLife(root, decoder, config, cycle, session)` captures actual native
   messages/tokens and top-level shared generation/checkpoint binding before each
   call. `run_cycle_and_submit(life, two_train_tasks, memory)` preserves sequential
   episodes and enacted TRAIN OPEN/reflection, then submits the completed cycle.
4. `export_cycle(session, cycle)` checks reservations, complete reflection and
   actual adapter identity. Measured TRAIN aliases are `episode`, `continuation`,
   `open_turn`, `presleep`, `reflection`. Held/readout-open are excluded. No rows
   are selected by outcome; old BASE calls lacking exact capture provenance cannot
   be rewritten into shared-adapter rows.
5. `wait_for_next(session, deadline=..., check=...)` waits only within the original
   hard bound for the next complete common generation. `reload_shared(decoder,
   session, next_session)` reuses the tested route adapter reload, retaining
   parameter identity and no branch optimizer. It rejects skipped generations,
   missing completion or base mismatch; no per-branch fallback training.

## Remaining activation work

This is a callable client, **not a complete successor resident supervisor**.
The next-source runner must bind the common CONFIG and adoption receipt, wire both
collection and sealed-readout loaders, and publish actual branch readiness before
the shared transition. Refresh the latest F1-owned checkpoint at the common
boundary; never roll back to an earlier candidate. Do not stop current residents
or manufacture a readiness receipt to imply this wiring is already deployed.

The publication allowlist includes the client as CPU-only work. The full source
and test dependency closure separates frozen snapshot hashes from changed mutable
Hubble transport/plan files; publication must not rewrite live snapshot bytes.
