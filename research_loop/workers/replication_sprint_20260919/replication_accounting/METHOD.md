# Independent new-seed accounting (declared before outcome retrieval)

Scope: **non-material, offline accounting only**. No model calls, runtime edits,
signals, evaluation launches, parent messages, training changes, or git commits.
Main monitors the experiment. Retrieve one bounded public snapshot after its
expected end, through `bash gpu/ovx4_ssh.sh`. Never read private panels, keys,
journals, model tensors, or generated caption text. Retain source-file hashes
and lossless projections of the accounting fields, not large source files.

The fixed 18-cell cross product and pre-outcome hashes are in `PLAN.json`.
Account from individual `RESULT.json` files independently of the runtime
report implementation; compare with that implementation's one read-only run.
The comparison is a check, not the input to our counters.

## Counting rules

- Deduplicate identical cell/event copies by identity AND content. Conflicting
  copies invalidate the unit; never select the more favorable one.
- For each arm/seed/scene, count each exact caption SHA once. Cache/replay flags
  never create a new discovery. Retain raw returned-status totals and duplicate
  counts to expose inflation. An orphan replay/cache without its original
  result is UNKNOWN, not a successful fresh submission.
- A genuine rankless execution failure followed by a scored retry is not a
  conflicting score: count the distinct eventually scored caption once, retaining
  the failure count. Two incompatible scored outcomes are a conflict.
- Count scored strings only with an explicit rank, accepted strings only with
  explicit acceptance, new pixels only with `new_pixel` and a distinct scene
  pixel ID. Rank alone is not a substitute for acceptance/relevance. Both THINK
  proposals and ACT proposals are eligible under the original scorer contract.
- Validate actual token counts against event ranges and the 1,024-token cap.
  Prompt tokens do not count toward the generated-token budget. Do not pretend
  18,432 generated tokens is total compute.
- Missing/partial/invalid cells stay visible. Complete-cells-only subtotals are
  labeled; full-arm totals and contrasts remain UNKNOWN until all six cells
  and the completed-arm source/weight receipts validate. Never zero-fill a
  missing cell, replace an arm, or select a winning seed.
- Count separately by arm, seed, scene, diagnostic epoch, and judge epoch.
  Novelty resets between seeds: source totals are **sums of seed-local counts**,
  not cross-seed distinct ideas. Show all three preregistered contrasts per seed.

## Provenance and limits

Bind the registry/config/freeze to their predeclared and prepared hashes; bind
each cell to its COMPLETE copy; join LOADED, COMPLETE and completion-verification
receipts. Compare recorded pre/post tensor hashes, source sleep identity and
adapter-file commitments to the preregistered source. Verify frozen/no-parent/
no-update flags and the adopted judge epoch. This checks **recorded** provenance,
not an independent model-tensor rehash or hardware attestation.

No analytic deduplication here removes an authentic row or changes training.
Selected-checkpoint, two-seed sampling is not independent training replication,
held-out transfer, a parenting/tapering experiment, or proof of literal humor.
