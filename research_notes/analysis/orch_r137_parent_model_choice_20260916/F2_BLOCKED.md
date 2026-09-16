# R137 F2 prospective Astra transport: blocked before implementation

Observed September 16, 2026, 02:05:05 UTC. This is a compact CPU/read-only audit receipt, not an activated boundary, launch approval, or transport-ready claim.

## Decisive incompatibility

The live F2 resident (observed PID 3953966) loads its PLAN once in `resident()`. The native frozen `poll_parent()` checks `response['actual_model'] in plan['parent_models']` before accepting COMPLETE or SILENT. F2 permits only `claude-fable-5-1` and `claude-sonnet-4-6`; it excludes Astra. An honestly attributed successful Astra response would become native `MISSING / INVALID_ASYNC_RECEIPT`, not usable guidance.

Verified node source: `/localhome/local-rohing/orch_math_feedback_uptake_r124_readout_source_20260915_v1/gpu/orch_math_feedback_uptake_r121_independent.py`; resident source is the adjacent `orch_math_feedback_uptake_r124_readout.py`. Hashes and exact PLAN binding are in `F2_BLOCKED.json`. Repository counterparts: consumer gate at `gpu/orch_math_feedback_uptake_r121_independent.py:225`, one-time plan load at `gpu/orch_math_feedback_uptake_r124_readout.py:234`.

A broker-only adapter cannot change this in-memory consumer contract. Do not disguise Astra as Fable, overwrite a live PLAN, alter checkpoint/optimizer state, restart the child, or dispatch calls whose guidance cannot be accepted. No applicable tested hot-switch handshake was found in the inspected consumer. Resolving this needs a separately authorized consumer-side boundary outside the current broker-only/no-restart scope.

## Observed boundary, not authorization

At Unix 1789524305.6247869: F2 native=1062, parent=124, optimizer_steps=14125. Parent reservation high-water=124; latest reserved identifier `R121_C000042_E1_experience`; 124 request files. Queue-name digest and reservation timestamp are preserved in JSON. Nothing at or before this observation is eligible for a future new-turn switch. Re-establish and bind a fresh boundary if work is later authorized; this snapshot is not a dispatch barrier or permission to process later queued backlog.

The existing Fable broker cap is 384 calls, output cap 8192 and budget 1.0; A2's config instead uses 100000 calls and output cap 1024. Copying the A2 config wholesale would therefore not preserve F2's broker caps. Reusing its evaluator alone would still not solve consumer compatibility.

## A2 is advancing

A2 advanced from committed C36 in the prior audit to C37 at Unix 1789524219.982386 (02:03:39 UTC). Current counters: native=856, parent=98, optimizer_steps=14169. This does not support a stalled-child diagnosis. The latest three parent receipts are MISSING with ValueError at `construct_request`, before provider dispatch. Current settings match the transport's expected model, Responses wire, primary endpoint and environment-key name; no credential value was read out or changed. The precise construction failure remains undiagnosed; no raw prompts or transcripts were printed.

## Handoff

No transport source/test implementation, immutable node staging, provider invocation or launch command is represented as ready. No CPU unit tests were run: no implementation changed. Main owns the scope decision, Git and shared ledgers; F1/F4 and the head watcher were not modified. Preserve all historical refusals, MISSING outcomes, claims and charges.
