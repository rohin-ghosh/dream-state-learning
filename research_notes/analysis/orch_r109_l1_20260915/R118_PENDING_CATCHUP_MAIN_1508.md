# R118 v4 settled pending consolidation — Main dispatch only

Third exclusive startup mode authorized by Main on September 15, 2026. This
continues the original two-episode loop, not a new benchmark or partial-episode
resume. V2 clean-boundary and V3 crashed-postcommit modes remain available.

Frozen source: `/localhome/local-rohing/orch_r118_fresh_exec_cpu_20260915_v4/source`.
Coordinator SHA256: `c56bb57b69405877a65124b623316f9b8bd769aa8f51db6f2481ff65325c5cdb`.
Native full source manifest SHA256:
`c66c24b62f83b9d9da7aab5e18e8120759448aa2d9234f3cc2b606b45295f2c4`.
Native CPU_READY.json SHA256:
`b51f751803c93e27abf5ebed30304ac6f64814a9e23d584cc39e37aa6e4ad0c4`.
V2 and V3 frozen manifests/receipts were verified unchanged. Family owners must
freeze this **v4 bootstrap** with their matching native hooks: dispatcher now
checks each receipt's explicit `startup_action`.

## Third owner boundary

Provide `settled_pending_consolidation:{path,sha256}` instead of either
`fresh_dev` or `postcommit_eval_disposition`, and retain `settled_cursor`.
`committed_checkpoint_sha256` is actual canonical STATE; `canonical_reload_required`
is true. `mounted_checkpoint_sha256` may be null or that exact canonical hash.

Pending document:

- `schema="R118_SETTLED_PENDING_CONSOLIDATION_V1"`, `status="SETTLED_PENDING_CONSOLIDATION"`, `root`, `branch`, current `generation`, canonical `checkpoint_sha256`, `cycle`.
- `episode_ids`: exactly two distinct permitted TRAIN IDs; `episode_completions`: exactly two `{episode_id,status:"COMPLETE",evidence:{path,sha256}}` records. Owners verify native episode completion semantics; common code checks the bound evidence and inventory.
- `rows:{path,sha256}`: immutable JSON list or object with a `rows` list, without rewriting captures or changing prefix masking.
- `terminal_calls:[{path,sha256,status},...]`: terminal statuses COMPLETE, FAILED, MISSING or CANCELLED; must cover every row source. Raw failed calls remain retained even when they produce no training row.
- `submission:{path,sha256}`: exact existing COMMON/generation_g/BRANCH.json, **or null** for precisely unpublished rows, in which case that path must be absent.
- `trained=false`, `replay_calls=false`.

Cursor document:

- `schema="R118_PENDING_CONSOLIDATION_CURSOR_V1"`, `root`, `branch`, current `generation`, canonical `checkpoint_sha256`, `cycle` equal to pending cycle.
- `next_cycle=cycle+1`, matching the release envelope: this is the next NEW cycle **after pending consolidation and its required readout**, not a command to skip the pending boundary.
- `native_used`, `parent_used` equal actual bounded envelope charges; `inflight_native_calls:[]`, `inflight_parent_calls:[]`.
- `action="RESUME_PENDING_PARALLEL_BOUNDARY_BEFORE_NEW_CALLS"`.

Pin both documents, all episode/call evidence and row inventory in the owner's
`preserved_files`. Actual RELEASED/dead-predecessor checks, original caps,
checkpoint completeness and no current sleep START remain mandatory. Pending
rows undergo the existing native source/prefix/TRAIN validator against the
current generation and canonical child. Previously trained branch captures,
including generation zero, held data, duplicates and incomplete episodes reject.

## Mixed startup without a circular wait

1. Every fresh actor loads/verifies canonical LoRA and bootstraps. F1 restores
   exact saved AdamW/RNG; peers still have no optimizer. All8 GO waits only for
   these eight bootstraps, **not** submissions or SAFE certificates.
2. Pending actors receive `startup_action="RESUME_PENDING_PARALLEL_BOUNDARY_BEFORE_NEW_CALLS"`.
   After `wait_fresh_collection_go`, call:

```python
resumed = resume_pending_consolidation(
    root=COMMON, branch=BRANCH,
    session_path=SESSION_PATH, session_sha256=SESSION_SHA,
    check=owner_stage_check,
)
```

3. The helper returns `cycle`, `next_cycle`, `episode_ids`, exact `rows`, and
   `submission`. Existing submissions are reused without calling submit;
   unpublished rows are submitted once using the existing validator. There are
   **zero new native calls and zero optimizer steps** in this helper. Exclusive
   START/COMPLETE/FAILED receipts prohibit a second resume attempt.
4. Owner builds its fresh-identity SAFE certificate using retained guards/FINAL
   bindings, then invokes existing `await_campaign_activation` and
   `launch_at_boundary` directly for the pending cycle. Do not run collection,
   reflection, parent calls or another submit on those rows. Finish the normal
   postcommit readout/disposition before starting `next_cycle`.
5. Other normal/recovered actors receive `startup_action="COLLECT_NEW_TWO_EPISODES"`
   and collect their next two episodes after the same GO. The Main CPU watcher
   arms once all eight actual current submissions and fresh SAFE certificates
   are available. A pending-resume FAILED receipt terminates the watcher without
   retries/signals instead of silently waiting for a missing arrival.

Owners retain their actual native-loop hooks; common code does not hotpatch
actors or claim their hooks were exercised on production GPUs. CODE/GRID hook
shapes were inspected against this return contract.

## Main commands

Use the request schemas and fixed deadlines in `R118_FRESH_EXEC_MAIN_1444.md`
and the postcommit alternative in `R118_POSTCOMMIT_MAIN_1457.md`, with the v4
source below and NEW request/output namespaces. All eight actual release
envelopes and independently frozen owner closures remain Main's responsibility.

```bash
export PYTHONPATH=/localhome/local-rohing/orch_r118_fresh_exec_cpu_20260915_v4/source
export CUDA_VISIBLE_DEVICES=
PY=/localhome/local-rohing/v2/venv/bin/python
MOD=gpu.orch_r118_parallel_consolidation
"$PY" -m "$MOD" publish-fresh-sessions --request "$SESSION_REQUEST" --output "$SESSION_JSON"
"$PY" -m "$MOD" prepare-campaign --request "$CAMPAIGN_REQUEST" --output "$CAMPAIGN_JSON"
SESSION_SHA=$(sha256sum "$SESSION_JSON" | cut -d' ' -f1)
CAMPAIGN_SHA=$(sha256sum "$CAMPAIGN_JSON" | cut -d' ' -f1)
"$PY" -m "$MOD" dispatch-fresh-sessions --session "$SESSION_JSON" --session-sha256 "$SESSION_SHA" --execute-owner-safe-release
"$PY" -m "$MOD" watch-campaign --campaign "$CAMPAIGN_JSON" --campaign-sha256 "$CAMPAIGN_SHA" --session "$SESSION_JSON" --session-sha256 "$SESSION_SHA" --execute-bounded-auto-arm
```

No GPU launch, release, signal, CONFIG change or Git action by this worker.
At 15:08:32 UTC, read-only canonical STATE remained generation1/checkpoint
`43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d`,
1884 shared steps, 319802 child / 35885 anchor exposures, COMPLETE matching STATE.

## CPU evidence and limits

90 native CPU tests passed; one optional live-cohort test skipped. Four actual
eight-process fresh starts include a mixed case with four postcommit-recovered,
two normal, and two pending branches. All8 GO completed before the unpublished
pending submission; existing F3 had zero submit calls, unpublished A4 had exactly
one. Second resume attempts rejected, canonical STATE and prior submissions
stayed unchanged, and no new native calls or optimizer steps occurred in resume.
Fourteen additional unsafe pending variants reject. Existing real Gloo,
checkpoint/FINAL, all-rank RNG and small Qwen2/PEFT-class CPU tests remain green.
This proves the startup/submission seam, **not** production all8 GPU catchup,
7B memory headroom, or throughput. Batch8 averaged-gradient AdamW remains
not serial-equivalent; no dose/context trimming, failed-partial replay or reset.
