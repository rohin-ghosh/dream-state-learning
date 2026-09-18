# Frozen6: proven cause and saved-state recovery proposal

September 17, 2026. Investigation only: no restore, checkpoint/journal mutation,
source edit, GPU/model load, signal, parent change or service restart.

## Proven failure, not an optimizer/RNG comparison

Banach's `r162_activation_20260917/FROZEN_EXIT_RECEIPT.json` SHA
`12a5207309d6c0e58acec6ff05fad569df4e159bb54107c315111661d17de72f`
binds native failure05:56:42.151412UTC, exit1 at05:56:43.625066UTC, and
SERVICE_EXIT_VERIFIED with cgroup_empty_verified=true. Original no_retry
artifacts remain authoritative and unchanged.

Actual predicate in frozen candidate5
`organism_v6/orch_r150_matched_stream.py:122` compares adapter-state identity
AND `checkpoint_sha256['adapter']`, which is the digest of **all adapter
directory files**, including adapter_config.json. It does NOT compare the
optimizer/RNG file hash as adapter identity. The latter differs too, but is
not this failing conjunct.

Fresh read-only CPU saved-state audit, 07:04:15UTC:
`SAVED_TENSOR_CPU_AUDIT.json` SHA
`847bd68b7ccb877e2250185dae591a27e9c87b48fb539ab99500ad4f56000875`.
Original native verify_checkpoint passes BOTH actual commits, rehashing their
adapter files and optimizer/RNG payloads. Safetensors were then loaded on CPU,
and every tensor compared exactly; optimizer payloads used CPU/weights_only=True.
No CUDA initialization or model construction occurred.

- **392 FP32 tensors / 20,185,088 elements exactly equal.**
- adapter_model.safetensors byte SHA is identical:
  `2beaa09d4930b1eafa6a1a07a67f3d062b35336d5e5ac58778a00ad518cf9dfe`.
- Both recorded adapter state hashes:
  `95966e71c3ec81487d05e02d6b770c422febfc433fe367d856a6e4817f8dbe14`.
- AdamW state/groups identical, empty state, aggregate/payload steps0, exact
  parameter order and experiment equal. No observed optimizer update.
- CPU/Python RNG identical; **CUDA RNG differs**. Preserve sleep1's post-wake
  CUDA RNG, not the initial RNG. Its difference is consistent with generation;
  this audit does not replay RNG draws or claim to reconstruct them.
- **Only parsed config difference is target_modules list order**. Same seven
  unique module strings; no changed value, membership, rank, alpha or dropout.
  README and all other adapter-file hashes match.

Initial order: down_proj, gate_proj, k_proj, o_proj, v_proj, up_proj, q_proj.
Sleep1 order: v_proj, up_proj, gate_proj, down_proj, k_proj, q_proj, o_proj.
This proves a serialization-order mismatch, not changed adapter weights.
The upstream mechanism that chose that order has not been independently replayed.

## Exact retained state

Root `/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5/parented_frozen`.
Last journal record13 is SLEEP_REQUEST/cycle1, file SHA
`0a8711cb081396df3ac12f1ccd6ab1fb5005f62fddab6b589f1561fac6408f08`;
resume-state SHA `e8e04d4c7529b4aff6b12ee65ee56bc46aa37efec5e10cfb724281e02c5ac31c`.
Rows3; sleep_frontier0; sleep_receipts0; pending
`sleep:1c66b1314805d4779a3ecc10ddd0db0dd46f61b55acebf3bf6428dc2413357e2`.
Record11 committed the own response; record12 contains the already completed
compaction/carry. Neither may be regenerated.

- Stream-committed initial COMMIT SHA
  `68580b9e6f4db25d0bc8b5a2107eec7507863d617065ff8b3f6d7c352a97417c`.
- Existing, **not journal-committed**, sleep1 COMMIT SHA
  `1aa0ab173c105e880c5b8da7ce697d57113c49d6c6536255b15cd4a3d443b977`.
- Actual sleep1 checkpoint is at `checkpoints/sleep_000001/COMMIT.json`.
  It contains the post-generation RNG and verified unchanged adapter/optimizer.

This is NOT an ordinary saved-boundary restart. Existing `run(resume=True)`
requires pending=None and sleep_frontier==len(rows); existing finish_sleep
rejects the already existing sleep1 directory. R160's pre-birth operator also
correctly rejects this born root. **Do not reuse it or its consumed GO.**

## Proposed narrow recovery — requires new reviewed implementation and Main GO

1. Bind the exact failure/lifecycle, root/cohort/plan/source, record13 and both
   COMMITs plus this CPU audit. Recheck original bytes, writer ownership/native
   absence and checkpoint files before doing anything. Stop on any drift or
   additional journal/native operation; do not extrapolate the current snapshot.
2. Repair the frozen-state invariant narrowly for proven serialization-only
   target_modules permutation. Keep raw file integrity checks for every
   checkpoint, exact tensor/state equality, optimizer0/empty-state evidence,
   and equality of every other config field. A changed tensor, module membership,
   duplicate module, rank/alpha/dropout, optimizer state, or unrelated file must
   still reject. Do not simply delete the adapter-directory assertion or label
   all config changes nonmaterial. Preserve old source; use a new exact reviewed
   repair binding without changing training, parents, tasks, carry or walls.
3. Under explicit one-shot **boundary-completion** authority, revalidate the
   complete journal and restore record13's exact pending stream in memory.
   Recover the already written sleep1 checkpoint/AdamW/post-wake RNG, not the
   common initializer. Complete only the missing frozen SLEEP_COMPLETE transition
   against that actual checkpoint and exact pending row frontier. Do not call
   generation, compaction, sleep, checkpoint writing or optimizer.step again.
   Any repaired transition must pass the repaired journal's full replay checks.
   This is a newly logged recovery completion, never backdated as the old failed
   operation's success; bind the earlier failure outside the unchanged prefix.
4. Keep the existing sleep1 directory/COMMIT bytes. A new checkpoint namespace
   is not a drop-in solution: boundary_checkpoint requires the exact
   `checkpoints/sleep_000001` path. Avoid that broader path-schema repair.
5. Only after the journal genuinely reaches that validated saved boundary,
   prepare a new contained **resume=True** attempt/unit/GO, same root/condition/
   full history/carry/lease. Load that saved checkpoint and prove actual tensor,
   optimizer and all RNG restoration before continuation. Run the unchanged
   per-boundary readout disposition logic once; retain any existing readout
   intent/failure and never replay an uncertain readout.

Necessary CPU gates include order-only positive case; all semantic-config and
tensor mutations negative; optimizer0/parameter-order checks; orphan boundary
completion preserving record prefix, carry and all three RNGs; unexpected new
records/checkpoint drift refusal; one-shot/no-retry; regular saved-boundary path
unchanged; parent/inbox cursor preservation. New source/recovery helper review
and exact Main authority are needed before mutation or GPU resume.

## Current handoff

This identifies a bounded repair, but **no safe unchanged-source restore is
available now**. It must not hold R163's separate CPU preparation indefinitely.
Parent3693784 and R162 service1389517 were left untouched; queued messages and
their cursors remain theirs. No recovered SLEEP_COMPLETE/LOADED claim is made.
