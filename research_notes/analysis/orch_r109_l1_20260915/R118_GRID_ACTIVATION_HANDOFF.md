# R118 grid activation handoff

Prepared 2026-09-15. Not an activation authorization or release certificate.

## Exclusive ownership

- Laplace owns F4/A4 predecessor native/guard signals, RELEASED receipts, and
  `ROOT/R118_SHARED_HANDOFF_BRANCH.json`. Herschel must not duplicate these writes.
- Herschel owns canonical boundary snapshots, activation sidecars and the frozen
  strict guard. Main alone initializes common CONFIG/adopts latest F1 optimizer.
- Launch requires Main's explicit launch GO after all eight actual releases and
  common adoption. ALL8 READY/release authorization is not launch GO.
- Hubble owns F4 broker transition to `SHARED_TERMINAL.json`; Laplace owns A4
  HTTP broker transition. Preserve old terminals and all existing claims.

## Frozen executable

Node5 is reached only with `bash gpu/ovx3_ssh.sh`. Inside that wrapper:

```bash
SOURCE=/localhome/local-rohing/orch_r118_grid_shared_source_20260915_attempt2
PYTHON=/localhome/local-rohing/v2/venv/bin/python
PAIR=/localhome/local-rohing/orch_r115_grid_pair_20260915
```

F4 is `$PAIR/F4`, physical3, wait600. A4 is `$PAIR/A4`, physical7,
wait120. No additional slots, no local optimizer, no lease or lifetime reset.
Both retain1858 native/298 parent calls, TRAIN cutoff16:55, FINAL17:00,
hard end17:02 UTC on2026-09-15. Common root:
`/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1`.

Source closure SHA256:
`03a2f241f2a043da9de28d9fc6d91fa7dc240b7ce6ef9fa08b2ff2bd92face9d`.
Native CPU_TESTS.json SHA256:
`63bc32cd5009935ae7d334abe5670554eeff298495754396a68afc8c6e994063`.
23 native tests passed, zero skips, CUDA uninitialized; entrypoint help exits0.

## After Laplace's actual release

Verify the release hash and `status == RELEASED`; verify each recorded
predecessor PID is absent, and every root-relative preserved file still hashes
exactly. Retain full recorded kernel identities, not just PID numbers.
Verify branch root/bounds against Main EIGHT_READY. Do not substitute the latest
observed completion while a predecessor still runs or has next-cycle charges.

Set ROOT to the exact released branch and COMPLETE to the completion file
recorded by that release, then execute this CPU-only metadata command once:

```bash
CUDA_VISIBLE_DEVICES= PYTHONPATH="$SOURCE:$SOURCE/gpu" \
  "$PYTHON" -B -m gpu.orch_r118_grid_shared_run boundary \
  --root "$ROOT" --complete "$COMPLETE"
```

This creates `ROOT/shared_boundaries/CNNNN.json`. Return its actual path/hash
to Main and Laplace. Match its next_cycle and charged counts to the release;
never regenerate or overwrite a previously published snapshot.

## Activation sidecar (only after Main adoption)

Write `ROOT/SHARED_ACTIVATION.json` once with these exact field meanings:

- `schema`: `R118_GRID_SHARED_ACTIVATION_V1`.
- `all_eight_ready_and_safe`: true only after Main confirms all actual releases.
- `ready_sha256`: hash of that root's immutable SHARED_CLIENT_READY.json.
- `predecessor_plan_sha256`: hash of original CONFIG.json (not PLAN.json).
- `inherited_bounds`: exact root READY inherited_bounds, unchanged.
- `shared_learner`: branch, common root, actual Main CONFIG config_sha256,
  actual Main adoption_path and adoption_sha256.
- `boundary`: actual canonical snapshot path and sha256.
- `predecessor_identities`: actual released native and guard identity objects.

No placeholder hashes or optimistic RELEASED status may be written natively.
Before sidecar publication verify common CONFIG and ADOPTION hashes, their
branch/readiness/bounds bindings, and source closure again. Do not initialize
or rewrite common state from this worker.

## Strict guard command (requires explicit Main launch GO)

For each released branch, with ROOT/SOURCE/PYTHON as above:

```bash
CUDA_VISIBLE_DEVICES= PYTHONPATH="$SOURCE:$SOURCE/gpu" \
  "$PYTHON" -B -m gpu.orch_r118_grid_shared_run guard --root "$ROOT"
```

Run only once with persistent process supervision and a new log path. The guard
uses an exclusive lock/ONCE marker, revalidates dead predecessors and preserved
boundary, records PRE_GPU.json, performs a fresh privileged exact-slot scan,
then starts the UUID-bound resident under the original hard deadline. Report
actual guard/native PID identities and PRE_GPU/LAUNCH hashes, not just readiness.
Do not clear ONCE/LOCK or repeat a failed launch without inspecting evidence.

TRAIN resumes the inherited next_cycle with two sequential episodes and TRAIN
open/presleep/reflection. All eight submit before F1 publishes; the same engine
reloads LoRA in place. Fresh-process parent-free DEV/FINAL and readout-open stay
excluded. Exactly F1 owns optimization; F4/A4 local optimizer steps remain zero.
