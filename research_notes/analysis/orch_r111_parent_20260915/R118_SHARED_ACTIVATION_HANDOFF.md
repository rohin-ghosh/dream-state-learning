# R118 route shared-client handoff — 2026-09-15

## Actual state

F1 native356208 and matched A1 native459948 launched from immutable node5
`/localhome/local-rohing/orch_r111_f1_v4_20260915_source_v3`.
F1 first COMPLETE Fable response finished 10:55:52.275609 UTC.
A1 first COMPLETE Astra response finished 11:13:52.186321 UTC and was delivered
and observed. A1 also has an earlier valid SILENT response and preserved MISSING
attempts; these are not COMPLETE interventions. Behavior-change judgments remain
UNKNOWN. Use `gpu/ovx3_ssh.sh`; no internal hostnames are required.

Both current lives remain per-branch learners. Neither has been stopped for
pooling. No common coordinator configuration or pooled GPU run was created here.

## Implemented readiness format

Each existing life root now contains `SHARED_CLIENT_READY.json` with:

```text
schema = R116_SHARED_CLIENT_READY_V1
branch, root, train_ids, excluded_ids
successor_source, source_files
boundary_checkpoint, history_candidate
common_root, inherited_bounds, predecessor_plan_sha256
tests_receipt, native_capture_fields
ready_for_initialization = true
active_shared_client = false
transition = FINISH_CURRENT_CYCLE_AFTER_ALL_EIGHT_READY_NO_HOTPATCH
```

F1 root: `/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1`.
F1 readiness SHA256:
`280a1181f3ec6facc7bc71704c63f5e2ef199f4b59d393f41def3c6b3a8575fe`.

A1 root: `/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_4_attempt1`.
A1 readiness SHA256:
`e98e68bf0149a4d734d8a7a9debfdbd1c8fae690bf193516234f698cfab5253a`.

Each has 16 TRAIN IDs and 16 excluded DEV/FINAL IDs. Raw histories are referenced
by node-local path/hash, never embedded in repository readiness reductions.

Immutable successor:
`/localhome/local-rohing/orch_r111_route_shared_source_20260915_v1`.
Its `CPU_SHARED_FINAL.json` binds 44 passing native-CPU tests, including actual
tiny Qwen/PEFT rank8 in-place reload and optimizer/RNG roundtrip; CUDA remained
uninitialized. This is CPU implementation evidence, not a pooled science run.

## F1 adoption candidate, not a premature rollback

At readiness, the latest completed candidate was cycle2:

```text
checkpoint SHA256 85af12741d3966e8648a34f69281d44b599e7abc52bea7f0c71e7001c477f833
optimizer SHA256 133a6254cf74985e938d35897cc228aa928e800f91c3476800b44bcdb75f500a
actual optimizer state steps [382], 392 optimizer state entries
prior optimizer_steps 382
prior child_token_exposures 26505
prior anchor_token_exposures 6950
previously trained replay rows 23
```

The optimizer values were read from the hash-verified actual `optimizer_rng.pt`
on node5 with CUDA hidden. Both CPU and CUDA RNG keys exist. Full canonical
history is node-local at the readiness receipt's `history_candidate.path`.

If the current live cycle has advanced, this candidate must NOT silently replace
a newer completed adapter. Once all eight clients are ready, finish the current
cycle/readouts and bind the latest checkpoint at that exact owned handoff. Update
the candidate explicitly while retaining old receipts. Never merge A1 or other
independently trained adapters into F1's adopted optimizer.

## Activation contract

Main owns initialization of
`/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1` using all eight
ready specs, the selected F1 checkpoint, actual prior metrics, and explicit
previously trained histories. Unknown counters stay null, not zero.

The route successor consumes this addition to its existing life PLAN:

```json
{
  "shared_learner": {
    "branch": "F1 or A1",
    "root": "/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1",
    "config_sha256": "actual CONFIG.json file hash",
    "adoption_path": "absolute node-local ADOPTION.json path",
    "adoption_sha256": "actual adoption file hash"
  }
}
```

`ADOPTION.json` contains `checkpoint` equal to CONFIG.initial_checkpoint,
`prior_metrics` equal to CONFIG.pretransition_metrics, and `branch_bounds`
mapping branch names to their unchanged original bounds. It does not need a
second copy of raw history: CONFIG.initial_history is the coordinator's source.
Add the successor, client, and coordinator hashes to PLAN.source_files. Preserve
old PLAN/publication/approval bytes; rebind their hashes only after an exact
complete-cycle, identity-checked owned handoff and fresh admission. Keep existing
roots, reservation ledgers, call IDs, carry, and hard deadlines. Do not start the
shared successor against an unbound old PLAN or report fallback as pooling.

The new entrypoint is `gpu.orch_r111_route_pair_shared`, not the live v3 module.
After adoption, F1 alone restores AdamW/RNG and owns optimization; A1 constructs
no optimizer. Both collect two TRAIN episodes plus TRAIN open/presleep/reflection
rows. Captures record `shared_generation` and `shared_checkpoint_sha256` BEFORE
native generation and before their initial file write. Historical captures are
never retrospectively tagged.

At ROWS.json, submit replaces per-branch sleep. F1 consolidates all eight;
nonowners wait under their existing deadline checks and reload the common adapter
in place after COMPLETE, without replacing parameter objects. Base/adapter hashes
are checked. A1's local optimizer-update count is zero; shared and inherited
totals are reported separately. Fresh DEV/FINAL/open readouts never enter replay.
Partial shared transactions fail closed for explicit recovery rather than
replaying charged calls or optimizer work.

## Measured sleep cost

F1 cycle1 had 14 encoded rows and 224 optimizer updates:

- Last reflection finished 10:57:55.324385 UTC.
- ROWS.json was written 10:57:55.730089 UTC.
- Last update was written 11:01:57.102098 UTC.
- Checkpoint saved 11:02:50.017476 UTC.
- ROWS-to-checkpoint: 294.287 seconds; reflection-to-checkpoint: 294.693 seconds.
- Encoding-to-last-update: 241.340 seconds; remaining verify/save: 52.915 seconds.
- Subsequent fresh DEV: 100.332 seconds; fresh OPEN: 81.236 seconds, separately.

The actual log has 224/224 updates with one anchor and lambda .25; zero
anchor-empty updates. An earlier journal note incorrectly attributed another
helper's anchor gap to this v3 run; this observed count supersedes that statement.

An explicitly conditional example with eight similarly sized 14-row submissions
and 14 rehearsal rows gives 1806 updates and about 33.3 minutes using the observed
loop time plus one checkpoint save. This is not a hard timeout, bound, quality
claim, or prediction for different token lengths. Use actual encoded row counts
and elapsed first joint updates to revise the estimate; keep lease/call guards.
There is no arbitrary six-hour barrier wait.
