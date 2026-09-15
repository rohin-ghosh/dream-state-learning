# Runnable math shared successor — 2026-09-15 12:02 UTC

Status: CPU/native ready, **not activated**. Original F2/A2 frozen-BASE fallback processes continue unchanged. No common CONFIG was needed to build/test/publish readiness. No inference, provider call, live signal, shared initialization, or budget reset was performed.

## Exact runtime and receipts

- Successor source: `/localhome/local-rohing/orch_math_feedback_uptake_r118_shared_source_20260915_attempt2`.
- Common coordinator destination: `/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1`.
- Existing life: `/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1`, members `lane1` (F2) and `lane5` (A2).
- Each member's `SHARED_CLIENT_READY.json` is schema `R116_SHARED_CLIENT_READY_V1`; includes all required branch/root/train_ids/excluded_ids/source/bounds/tests/command/activation fields. These are actual node-root receipts, not a helper-only promise.
- Native `R118_CPU_TESTS.json`: 81 tests PASS, no failures/skips, CUDA uninitialized, zero native/provider calls. Tests include actual two-episode/six-capture collection, canonical submission, reload-before-readout ordering, raw/failed-readout custody, late cursor42/43 with carry, actual owned CPU pidfds and counter-lock exclusion. The 81 comprise 26 new successor/boundary tests, 28 R117 tests, and 27 Main coordinator tests.
- Frozen closure includes611 Python sources/tests, recorded in each READY. Original R115 source/data/contract hashes independently checked; no original snapshot changes.

## Executable lifecycle

`gpu.orch_math_feedback_uptake_r118_shared_run` supports `activate`, `guard`, `resident`, `readout`, and CPU-only `scan`. It reuses R117 `collect_cycle`, `export_cycle`, `load`, and `reload_at_boundary` rather than replacing their source/mask contract.

Exactly two sequential TRAIN episodes plus their open turns, presleep and own reflection produce six prospectively generation/checkpoint-tagged native captures. Both episodes retain truthful failed attempts and parent-visible feedback. Canonical sourced own-token rows go to the F1-only barrier; no math optimizer is created. Resident waits for exactly the next published checkpoint within the original wall, verifies adapter/optimizer reference, and copies exact LoRA tensors in-place before fresh exec-isolated parent-free readout. No repeated admission between resident cycles. Actual weight-learning status requires the shared F1 publication and verified reload; existing BASE captures remain elicitation-only, never retrospectively tagged.

Readout counts remain20 each cycle (DEV8, attached opens8, focused2, TRAIN-attached PROBE2 excluded from rows) and16 terminalFINAL (FINAL8 plus opens8). Full decoded response and token IDs are saved; partial batches preserve every charged failure. No readout, its attached open, or oracle content enters replay, carry, parents, or the shared submission. Historical sleep0 readouts are not repeated.

Original caps:43 total cycles,1168 native and384 parent slots per life;16:59 UTC native cutoff,17:00 FINAL window,17:02 hardwall on September15. Existing counters/reservations/next task cursor and latest own-reflection carry survive adoption. No extra calls or new baseline.

## Agreed boundary only

Each member has an **unarmed** `shared_handoff_r118/REQUEST.json`, expiring2026-09-15 12:32:09 UTC. It pins actor/supervisor PID/start/UID/argv/cwd, original source/PYTHONPATH, startupCVD, UUID/kernel minor, READY and original data/contract. F2 actor351481/supervisor342937; A2 actor433220/supervisor425317. Reprepare to a new request path if identities change or expiry passes; never reuse an expired authorization.

For each command below use node-local Python `/localhome/local-rohing/v2/venv/bin/python -B` with `PYTHONPATH` set to the exact successor source, `CUDA_VISIBLE_DEVICES=` for controller phases, and `PYTHONDONTWRITEBYTECODE=1`. Substitute the chosen exact member root in `LANE`. These are **instructions for the agreed transition, not executed launches**.

1. Main supplies request authorization JSON with `authorized:true`, `all_eight_ready:true`, `common_handoff_coordinated:true`, `request_sha256:<exact REQUEST hash>`.
2. Run `-m gpu.orch_math_feedback_uptake_r118_shared_boundary execute --request LANE/shared_handoff_r118/REQUEST.json --authorization REQUEST_AUTH.json`.
3. Helper waits for all20 DEV/open reservations, locks the existing COUNTERS lock, lets already-reserved readout finish, requires original cycle COMPLETE/AFTER/final mount and no later charge, freezes only exact owned actor/supervisor, records carry/ledger/cursor. An already-created **empty** next-cycle directory is recorded, never treated as completed work. It then terminates only that identity-pinned pair without SIGKILL, preserves artifacts and writes `release/RELEASED.json`. No outcome-dependent stop. Original supervisor termination/error artifacts remain, annotated by explicit completed-cycle handoff rather than concealed.
4. Main initializes the eight-member coordinator and provides ADOPTION with `checkpoint`, `prior_metrics`, `branch_bounds` matching each READY. F1 initial history must be preserved. Math does not initialize.
5. Main supplies activation authorization with the same three true flags and `release_sha256:<exact RELEASED hash>`.
6. Run `-m gpu.orch_math_feedback_uptake_r118_shared_run activate --root LANE --release LANE/shared_handoff_r118/release/RELEASED.json --shared-root /localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1 --adoption ADOPTION.json --authorization ACTIVATE_AUTH.json`.
7. This creates `LANE/SHARED_ACTIVATION.json`, validating shared binding `{branch,root,config_sha256,adoption_path,adoption_sha256}`, original inherited bounds, READY and release, plus exact next cycle. Then run `-m gpu.orch_math_feedback_uptake_r118_shared_run guard --root LANE`. Guard performs fresh root-level full `/proc` scanner admission with UUID/CVD/base mapping, starts one successor and enforces original hardwall. No stop/launch is authorized by READY alone.

Hubble broker boundary requirement: preserve old `TERMINAL.json`; the successor broker must follow `SHARED_TERMINAL.json` after activation, using the same queue/claims, original max calls, cutoff, model/prompt policy, and no charged retries. Math does not mutate Hubble's broker.

## Build provenance limits

Initial preparation attempt1 was an incomplete dependency overlay: native CPU import failed before tests or model loads. Preserved; no READY published from it. Attempt2 is self-contained original source plus prospectively copied shared modules. `pytest` is unavailable locally and in the node model venv, so the actual81-test run uses stdlib unittest; no dependency download or false pytest claim. Source/test receipts belong to attempt2 only.

Main owns Git. Publish the explicit STAGE_PATHS list only; raw calls, prompts and parent transcripts remain node-local. COORD is a shared notification, not part of the worker's Git ownership.
