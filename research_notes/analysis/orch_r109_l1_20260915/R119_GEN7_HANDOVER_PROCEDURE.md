# Prospective ovx physical7 handover — NOT RELEASED

Main alone owns the R120 evaluator. Herschel retains gen7 until Main supplies actual CPU/native evaluator READY, its pinned launch configuration, and the destination receipt path. This document is not a release, signal request, allocation expansion, or evaluator launch. Other13 L1 slots and all optimizers remain untouched.

## Actual bindings

Use `gpu/ovx_ssh.sh` only. Native root:
`/localhome/local-rohing/orch_r119_l1_generation_20260915_attempt2`.

At preparation, supervisor PID1397776/start_ticks72226952 and native PID1397837/start_ticks72227126, uid2524, boot_id8ff7b0dc-fbdf-4945-9044-3dffe94b5407. Physical7 UUID is `GPU-7c213554-a6c0-5c5a-1117-0422c8eee4ed`. Re-read START/HEARTBEAT/LAUNCH after READY: the supervisor can advance segments, so never signal these recorded PIDs without exact fresh identity checks.

Native base path usable by Main's evaluator:
`/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28`.
Interpreter: `/localhome/local-rohing/v2/venv/bin/python`.
Frozen generation seed is FULL15460, not the current evolving training checkpoint. Its COMMIT/state/base hashes are in `R119_GEN7_HANDOVER_PREPARED.json`. Main must separately bind the evaluator's selected before/after checkpoints; do not silently substitute the generator seed.

Service identity:
`/localhome/local-rohing/orch_r109_l1_20260915/SERVICE_IDENTITY.json`, SHA256 `26b16432e913ea03e6c2ae41977c60885d00ad601a6bf8d097b8a6e57734cbcc`.
Lease provenance is original C2 PLAN398b5e38bd3a7642ad1bf68a16b282304392e50f57dc4c7afb07e3345e16bebb, with lease expiry1789980180 and conservative hardwall1789958580 (original21600-second margin). No extension or reset. Evaluator bounds must fit its Main-approved budget and this wall.

## Completed-task boundary, not an arbitrary response

The frozen loop has no STOP file. Do not invoke legacy `retire`/`release` unchanged: they bind different roots/owners and zero-based call inventories. Current fork inherits15842 calls; only calls strictly above that are its own files. A successful draft alone is insufficient when the optional second response or route episode is pending.

The actual boundary is atomically persisted `PROGRESS.json` after the whole task. Require:
- `calls - inherited_calls == new_segment_calls` and positive new work;
- exact contiguous CALL and INTENT inventories from inherited+1 through calls;
- no next INTENT, no FAILED files, and the latest CALL's cumulative count matches PROGRESS;
- for route, the matching four-digit `EPISODE_{batch:04d}_{position:02d}.json` exists;
- identical progress before/after an acknowledged pause of the exact native process, with all boundary checks repeated while stopped.

`gpu/orch_r119_l1_gen7_handover.py` checks these conditions without signals. Its `candidate=true` is deliberately NOT a release authorization: live snapshots can race. Seven new focused tests plus ten existing V3 tests pass; native read-only checks also ran. Current admission correctly reports busy due to1397837.

## Exact action sequence, only AFTER Main READY

1. Bind READY/config hashes, source hashes, current segment, exact supervisor/native identities (PID+start_ticks+uid+boot), root/index command binding, native CVD UUID, service identity, and remaining lease/budget. Write a node-local pre-signal intent receipt in the separate handover root.
2. Open pidfds for both exact identities and revalidate. Pause only the supervisor with SIGSTOP; acknowledge its stopped state. This prevents automatic next-segment launches while the native finishes tasks. Resolve the current native again after the supervisor is stopped; if a segment transition raced, bind the new recorded owned native, never guess a PID.
3. Poll the cheap frozen `complete_boundary` predicate while the native continues. At a candidate, SIGSTOP that exact native via pidfd and wait for stopped acknowledgement; repeat the full boundary checks above against the same PROGRESS. If the boundary moved or a call is pending, SIGCONT the native unchanged and keep waiting. Never terminate mid-call or regenerate an already charged input.
4. Once a stopped boundary passes, atomically write a node-local hash manifest covering retained CALL/INTENT/EPISODE/PROGRESS/LOADED files, plus plan/source/checkpoint/counter bindings. Record `next_call=calls+1` and `next_position=position+2`; apply the original roster rollover if generation is ever separately authorized again. Record inherited15842 separately, not as new exposure. No raw rows leave the node.
5. With both exact owned processes stopped, terminate the held supervisor and the boundary-stopped native through their pidfds (SIGTERM followed by SIGCONT to deliver termination). Confirm both identities gone and no owned respawn. Retain original logs and outputs; do not rewrite old EXIT/COMPLETE or claim natural completion. Write a new handover terminal that truthfully labels external safe-boundary retirement. If termination/admission fails, report NOT_RELEASED, not a successful handoff.
6. Run the existing privileged node2 admission function on physical7 with the pinned service identity. Require `clear`, scanner_euid0, and exact UUID. Preserve its full report node-local; publish only its hash/reduction. Only then write `RELEASED.json` and send its path/hash to Main. Main rechecks admission immediately before evaluator loading; no generator restart thereafter without new allocation.

Bound the boundary-capture attempt to min(READY time+600seconds, remaining lease wall). This is an operational wait bound, not a changed generation lifetime. If no verified boundary is caught, resume any paused native and supervisor, write NOT_RELEASED with the reason, and leave generation running. Never turn timeout into forced mid-response termination. No fixed release ETA is claimed: route tasks can contain multiple calls. An externally captured completed task avoids waiting for the entire16384-response segment.

## Tested native read-only commands

The helper is already copied to the separate node-local handover source directory. Set:

```sh
export PYTHONPATH=/localhome/local-rohing/orch_r109_l1_20260915/generation_v3/source:/localhome/local-rohing/orch_r109_l1_20260915/source
export PYTHONDONTWRITEBYTECODE=1
/localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r119_l1_gen7_handover_20260915_attempt1/source/orch_r119_l1_gen7_handover.py inspect --directory /localhome/local-rohing/orch_r119_l1_generation_20260915_attempt2/gpu7/segment0000/gpu7
/localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r119_l1_gen7_handover_20260915_attempt1/source/orch_r119_l1_gen7_handover.py admission --service /localhome/local-rohing/orch_r109_l1_20260915/SERVICE_IDENTITY.json
```

Re-resolve the segment before using the first command. The admission callable is `gpu.orch_rich_hot_node2_scan.scan(7, Path(service_path))`, using the frozen original source closure and its sudo/root full-process check. Do not use `orch_r109_l1_run.scan`: its old allocation policy can reject the newly assigned physical7. No source changes to the frozen scanner, generator, or training loop are needed.

The helper intentionally contains no signal or release CLI. Herschel performs the identity-bound action sequence only after Main READY; no watcher, signal, or stop has been armed during preparation.
