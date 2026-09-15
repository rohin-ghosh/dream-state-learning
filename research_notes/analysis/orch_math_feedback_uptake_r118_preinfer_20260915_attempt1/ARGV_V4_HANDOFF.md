# V4 argv-only recovery — 16:03 scoped authorization

This supersedes the earlier v3 dead-process-only candidate, whose correctly blocked diagnostic remains archived. Main explicitly authorized the existing r110 >=3-observation argv-only interpretation at16:03. No earlier admission, failure, source, timer or charged work was modified.

## Ready exports

Native source: `/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_source_20260915_v4`.

- `PREPARED_EXPORTS.json`: `6879cb3a7dcadc9668f9f1d042c7b29a002befbc0dfc35c014d8a6873c0d7aa3`.
- `SOURCE_MANIFEST.json`: `6dccd6acb0d5c8916b4fbbc01c1aa0cf3768281e934bcb0df02010cce972af85`.
- `NATIVE_CPU_TESTS.json`: `ad8251574b797138d9832f6c57dbcd09a710e3bb71930025702d49424c0a44bd`; **248 PASS**, zero failures/errors/skips/CUDA initialization.
- Focused local admission suite:54 PASS. New own files are the argv wrapper/test and updated preinfer wrapper. Existing r110/r111 admission helpers are reused unchanged and included in the frozen source closure.

Fresh service prefix: `/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_20260915_attempt4`.

| Branch | Prepared owner | SHA256 | PLAN SHA256 |
|---|---|---|---|
| F2 | `lane1/FRESH_OWNER_PREPARED.json` | `1253bd0828089d717282fb0abaa9ea0a20073d69bca760e30bf27f4e6b3605d3` | `d50ffcce820690b99912a1ff89f17f5cc795370b101acfc9f413e5c6bf9406c1` |
| A2 | `lane5/FRESH_OWNER_PREPARED.json` | `ed04ec2a358257fedd7e5a211df26d6acf3548df50b579e75eb18c92ae3c1079` | `96f7875affe5843b24cb2a36d6e4102dd7f2a5a447d4d802fe14cf2cc504b944` |

Both owners contain exact executable command/cwd/env and complete inline `source_files`, without requiring stage first. Main can assemble the new campaign from these exports.

## Actual privileged CPU scans

Exactly one fresh read-only scan per branch completed CLEAR, with no remaining blocker/helper error. Both reconciled only live PID3159 using **four** observations each: stable PID/UID/start/boot and executable device/inode, complete visibility, no target-device FD and no CVD reservation, plus actual command-hash variation. PID3159 was not called dead. No exit-reconciliation reason was cleared.

- F2 native `lane1/CPU_SCAN_COMPACT.json`: `21130fa67fe68a4cf982dad8394499d7bf32f6dc6720bebdd96a991119e76940`.
- A2 native `lane5/CPU_SCAN_COMPACT.json`: `96d791c49b49cf64c3d427953dc88494286efaad08ab41ca158c14400af7896d`.

The existing node5<=1MiB idle-baseline handling is reused; memory remains exactly recorded and is **not** treated as proof of freedom. Kernel/executable changes, fewer than3 samples, incomplete visibility, target FDs/CVD, compute ownership, unknown/foreign blockers and excess memory remain rejecting. Full original scanner reports and identity observations are retained node-local. These CPU observations do not replace the guard's fresh launch-time scan.

## Tested scan command

From the source root above, the following module path was exercised in-process by both privileged diagnostics; it is also the successor guard's subprocess entry:

```sh
sudo -n env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_source_20260915_v4 \
  python3 -B -m gpu.orch_math_feedback_uptake_r118_preinfer scan \
  --service /localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_20260915_attempt4/lane1
```

Use lane5 for A2. No repeat scan is requested by this handoff; both diagnostics already exist. No model trial, provider call or optimizer step occurred.

## Coordinated stage, not executed

From the same immutable source:

```sh
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B \
  -m gpu.orch_math_feedback_uptake_r118_preinfer stage \
  --service "$SERVICE" --authorization "$NEW_MAIN_LAUNCH_AUTH" \
  --campaign "$NEW_MAIN_CAMPAIGN"
```

Keep the existing LAUNCH authorization schema with the new PLAN hash, actual new campaign/activation directory, gen1 checkpoint43ce68ac..., all-eight release proof and current bounded window. The failed1527/e834ff campaign/session is explicitly prohibited. Stage retires only the two identity-bound failed-startup CPU timers per branch and produces RUNTIME/FRESH_OWNER. Main alone dispatches GPUs; current pending timers remain untouched until that scope. Selector1519259 is not retired or rebound.

Original next cycles F2=11/A2=7, N274/P60 andN170/P36, carry, gen1 learned child, TRAIN16:55/native16:59/hard17:02 and43-cycle caps all remain unchanged. No old DEV retry or gen0 resubmission. The same separate canonical eight-call FINAL allocation is retained.

Future broker bindings use fresh attempt4 lane1/lane5 RUNTIME and GUARD_TERMINAL; old readiness must not be reused. Hubble owns F2, Math owns A2. There is no new control, thesis, outcome intervention or counter reset. Main owns Git/publication.
