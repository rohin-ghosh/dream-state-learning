# Separate route FINAL allocation: CPU schedulers armed

Authority: Main/user R118 FINAL READOUT SCOPE, September15 **13:07UTC**, followed by explicit Main ownership of the canonical selector. Actual scheduler verification: **2026-09-15T13:24:11Z**. No GPU launch or FINAL task inspection has occurred for this allocation.

## Actual processes and roots

| Branch | Future physical slot | CPU scheduler PID | New evaluation root |
| --- | ---: | ---: | --- |
| F1 | 0 | 1496784 | `/localhome/local-rohing/orch_r111_route_final_20260915_F1_attempt1` |
| A1 | 4 | 1496788 | `/localhome/local-rohing/orch_r111_route_final_20260915_A1_attempt1` |

Both started **13:23:21UTC** with `CUDA_VISIBLE_DEVICES=`. At verification both were sleeping, UID2524, exact command/start/boot identities recorded, **no NVIDIA device descriptors**, no sealed-file link and **zero native/provider calls**. These are CPU waiters, not GPU occupancy. The existing F1/A1 learner processes are not signalled by this preparation.

- Immutable scheduler source root: `/localhome/local-rohing/orch_r111_route_final_source_20260915_v2`.
- Source SHA256: `dbe2cf05b614ab374964249324c02d5e19f8b8bc29684fe5da398be505d9c618`.
- Test SHA256: `d1156f26b4f36963573488424bcff573c9151ecfbdffdf2c2c7b37588c487806`.
- Native CPU receipt `CPU.json`: `31844080634a415301999a2695e84064d65d1ea6baf9c520aca32398ae730bdc`.
- Native `SCHEDULERS_VERIFIED_1325.json`: `f0650c3720da1b06b3ac640f8ca72540f404e2f48d2915248505a8779cea7bc3`; filename1325 is a label, actual observation13:24:11.
- Repository compact `FINAL_SCHEDULERS_COMPACT_1324.json` contains exact config/PLAN/dispatch/start references and process identities; no raw tasks or responses.

## Separate bounds, unchanged task protocol

Each branch receives a **new evaluation-only ceiling of48 native calls**, at most8tasks ×6turns, and8 ×2048 =16384 target tokens. Pair ceiling96calls, zero parent calls, optimizer updates or training rows. These counters start in **new evaluation ledgers**, not by resetting or extending any old life. Old PLANs, reservations, sleep0, captures and optimizer remain untouched.

The only evaluation window is **September15 17:00–17:20UTC**, further clipped by verified lease end minus6hours. Existing route lease metadata gives September17 04:04UTC, so September15 17:20 is the tighter end. Each branch is bounded by at most1/3GPU-hour within that window; actual readout retains the existing415-second wall, additionally enforced by its parent CPU process using the exact child's pidfd. Five seconds are reserved for TERM; KILL at the bound if necessary, preserving partial captures and charges. It never signals another lane, a reused PID or the old training process.

The scheduler invokes only the already frozen `gpu.orch_r111_route_pair_shared` **readout** path, `--scope final --sleep-index 1`, in a fresh process using the separately prepared evaluation PLAN/root. No training, shared-client collection, optimizer restoration, parent request, open turn, DEV or sleep0 path is dispatched. Source snapshot remains `/localhome/local-rohing/orch_r111_route_shared_source_20260915_v2r1`, executable `c385db4fe1920ba645af8816327ddcbaebe10da3d1f42f3318330fa052ecb7ae`.

The originally sealed inventory is bound from the old PLAN metadata, not opened early. Both original `SEALED_FINAL.json` files have SHA256 **777cf837e4e95b616320d2d5e9c63d76639efa0eade9f78b26fb2bcf7192c2ae**. At or after17:00, the runtime validates that original hash and exactly8 distinct IDs; only then are the original file and store made available to the evaluation process. IDs and contents have not been newly inspected or exported during preparation. Runtime `FINAL_INVENTORY_BINDING.json` stays node-local. No new cohort is generated.

Decoder/gym are unchanged: greedy, one beam,16384context, original2048 per-task cumulative readout-token cap and at most6route turns. Completed evaluation results and cached responses are evidence files only: no learning/replay buffer, parent, head or exchange receives them. These paired evaluations share one learned checkpoint and are **not independent learned models**; no causal parenting advantage is claimed.

## Canonical checkpoint: Main only

All route consumption uses:

`/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1/FINAL_SELECTION.json`

Schema: `R118_FINAL_SELECTION_V1`. Main owns `gpu/orch_r118_final_selection.py`, the selector process and the atomic marker. The scheduler calls only its **read-only** `validate_selection(common, config_sha256=..., initialized_sha256=..., adoption_sha256=..., clock=...)`. Dependency snapshot SHA256 **64ccee2884b1dddafde70da8ccc2795127c8a4553fb6eb1a301484da369334ed** is copied unchanged in the scheduler's dependency folder. Route code never calls `select`, initializes a shared learner, creates a competing marker, edits common STATE, or decides a different checkpoint.

Validation binds all three original lineage hashes, the immutable selected STATE snapshot, generation and lifetime/shared metrics, completed pre-cut sleep receipt or adopted generation0 checkpoint, and checkpoint/optimizer hashes. The marker must remain unchanged across validation and immediately before dispatch. Missing/invalid canonical selection is not replaced by inspecting an in-progress optimizer or choosing the latest filesystem checkpoint. At the evaluation deadline it yields `NOT_RUN_BOUND.json` if selection/release never becomes available.

## Release and admission before any GPU call

Before dispatch, the scheduler requires the **actual v4 cutoff controller's `COMPLETED.json` and branch `DISPOSITION.json`**, with confirmed RELEASED or PREDECESSOR_ALREADY_EXITED status. The original controller/source/PLAN bindings and old supervisor/actor/readout identities are checked. A historical peer terminal, mere empty-GPU observation or guessed completion is insufficient.

After that, it runs the original privileged service/full UUID+kernel-minor/process/CVD scanner against the exact assigned physical slot. Strict CLEAR is required and must be fresh; no bypass or foreign reclaim. This fresh scan will happen at dispatch, not now while healthy training occupies the cards.

Already completed original morning FINAL is skipped. Existing attempts in the new root fail closed with no retry/replay. Partial/failed native calls, charges and readout files are retained; no fake COMPLETE/TERMINAL or outcome-based restart. The scheduler's native subprocess inherits neither parenting provider environment variables nor any training context.

## Tests and readiness

**27 own native CPU tests PASS in0.73s**, with GPU visibility empty, no model/provider calls or real FINAL reads. **72 local combined tests PASS**:27route FINAL +29cutoff +16Main selector. Tests exercise the actual frozen route readout function with synthetic CPU responses, including exactly48 native reservations, the49th-call rejection, zero parent allowance, original default cap, unchanged-adapter check and no training buffer. Other tests cover early/late/lease clocks, real pidfd TERM/KILL with an untouched foreign CPU sentinel, read-only actual Main-selector integration, canonical tampering/partial checkpoints, old sleep0 vs morning completion, single attempts, source/CPU receipt binding and confirmed release requirements.

v1 was an unused CPU candidate only, never armed; it and its26-test receipt remain intact. The first attempt to use the model venv's absent pytest did not touch any model/provider. Tests use existing `/localhome/local-rohing/orch_r111_f1_pytest_support`; no environment/package installation or live-source patch was performed.

## Already running commands — do not duplicate

Transport: `gpu/ovx3_ssh.sh`. Commands shown are the already armed CPU-only invocations, not a request to launch additional schedulers.

```sh
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r111_route_final_source_20260915_v2/gpu/orch_r111_route_final.py wait --config /localhome/local-rohing/orch_r111_route_final_20260915_F1_attempt1/EVALUATION.json --config-sha256 b4d90fe2bc6d4bfb829264c8c435bbef3c1a1d6864a02d95dac0ece43c796fbc
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r111_route_final_source_20260915_v2/gpu/orch_r111_route_final.py wait --config /localhome/local-rohing/orch_r111_route_final_20260915_A1_attempt1/EVALUATION.json --config-sha256 45d9e004d93fff28d9c09aa759f047d62dc13b51396b945d67476356c4d3f4de
```

Observe each new root's `SCHEDULER_STARTED.json`, then after17:00 `ATTEMPT.json`, `ADMISSION.json`, `DISPATCH.json`, `FINISHED.json` or the truthful `FAILED.json` / `NOT_RUN_BOUND.json` / `SKIPPED_ALREADY_COMPLETE.json`. Never rerun an existing attempt without a separately authorized disposition. Runtime raw stays exclusively on-node; Main owns Git.

## Current training is unchanged

At **13:24:11UTC**, first pooled serial sleep remained healthy at **434/1884 in-memory updates**,75,363child/8,160anchor exposures, **UNCOMMITTED**. STATE remained generation0/shared steps0; no completed first pooled checkpoint or fresh post-pooled held result was claimed. Cutoff controller still MONITOR, errors empty. This evaluation preparation did not interrupt it.
