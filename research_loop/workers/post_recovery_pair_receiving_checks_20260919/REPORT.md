# Receiving checks — September 19, 2026, 01:58 UTC

Non-material recovery/performance repair. No native was signalled, stopped,
restarted or source-swapped. The observations do not authorize a handoff.

## Actual checkpoint and source checks

The frozen sibling's COMPLETE3725/LEARN3726 and learner's
COMPLETE6495/LEARN6496 passed CPU checks of adapter bytes, optimizer counters,
Python/CPU/saved-CUDA RNG structure and working-state/model binding. Optimizer
steps were respectively 0 and 3888. Both exact 209-file epoch2 source closures
also passed their 14 source-integration tests on the node. These are historical
checkpoints, not proof of a current reserved COMPLETE or privileged admission.

## Slow-reader finding and repair

Both initial full-live-tail observations exceeded 90 seconds. Only the isolated
CPU observers timed out; exact original native identity was rechecked afterward.
An instrumented learner observation localized the main delay: hashing 4.75 GB
took 8.23 seconds, but restoring the history took about 6.85 seconds **again for
each subsequent state-bearing tail record**. The historical checkpoint had
159 later records. It was incorrect to attribute this observation entirely to
prefix hashing or to predict a multi-minute exact-COMPLETE restore from it.

`TrainHistory.frontier()` previously serialized and hashed every prior event for
each compaction receipt while replaying history. The repair maintains an
incremental hash of the same canonical JSON list and caches its closed-prefix
hashes. Event, operation, working-state, training-row and checkpoint serialization
are unchanged. Deep copying retains independent hash state. No integrity check
is removed and no cached digest is accepted from a checkpoint.

The exact-source overlay was tested in isolated observers against both real
checkpoint histories. Restored history checkpoints were byte-equivalent.

| Historical boundary | Original prefix + restore | Optimized prefix + restore | Optimized history restore alone |
| --- | ---: | ---: | ---: |
| Frozen COMPLETE3725 → LEARN3726 | 37.08 s | 19.00 s | 0.417 s |
| Learner COMPLETE6495 → LEARN6496 | 14.77 s | 8.06 s | 0.173 s |

These measurements stop at the historical LEARN record. They deliberately do
not validate the later live head or current sidecars; they are not full scanner
or admission receipts. Prefix verification still reads all retained bytes
(11.23 GB frozen, 4.56 GB learner), so this is **not an O(tail) reader**. Neither
the live source nor immutable epoch2 source was changed. The port is available
for a separately pinned next receiving epoch; live retention adoption remains
zero at this report's cut.

## Validation

- Eleven worker regressions pass, including exact overlay seams and refusal to
  apply twice, input pinning and no native-control operations in observers.
- 124 focused history/stream/journal unit tests pass. New cases cover all
  canonical prefixes, Unicode/escaping, duplicate/conflicting appends,
  independent deep copies and uncached/optimized checkpoint-byte equality.
- Broader pytest run: 228 passed and 197 subtests passed; one existing
  plain-context test fails with `KeyError: new_presentations` in its mocked
  `NativeChild.sleep` plan. The same failure was reproduced with the original
  uncached history implementation. It is not repaired in this scoped change.

Receipts are the `*_CHECKPOINT_CPU_*`, `*_SOURCE_CPU_*`,
`*_TAIL_OBSERVATION_*`, `*_COMPLETE_COST_*` and `*_ACCELERATED_COST_*` JSON
files here. Full journals and diagnostic work remain on their original node;
only small receipts and code were retained on the VM.

## C2 receiving evidence — 02:15 UTC

C2's separate epoch3 source is now staged on node5: 184 exact Python files,
unchanged live native1139778 and original source. Actual-node source checks,
retention/receiver integration tests and the history/frontier suite pass.
Neither admission nor a source-changing restart has been attempted.

The bundle's historical default COMPLETE11502 fails the current-wall check.
That refusal is preserved; no deadline validation was relaxed. A bounded
metadata read selected actual COMPLETE12902, followed by LEARN12903, with SHA
`4dbee358fe5cfd59b6440633e07142bd1d82ce70572c00602910a52e74d857ed`.
Its saved adapter, optimizer (8588 steps), RNG and working-state binding pass
CPU checks in 2.925 seconds. This is a saved-state proof, not a current-handoff
reservation or GPU restore.

The optimized historical COMPLETE-only reader takes **41.69 seconds** on C2:
**40.71 seconds hashes 23.12 GB**; the separately checked history restores in
0.219 seconds and serializes identically. It therefore **cannot fit a 30-second
reservation** as currently implemented. No native was interrupted to test this.
Prefix prevalidation outside the reservation, with authenticated immutable-file
rechecks and full tail verification, is under development; it is not yet an
admitted fast path. Increasing the reservation bound or pretending the prefix
was verified is not the remedy.

The independent code review found no core cache/deepcopy blocker across 189
prefix comparisons and mixed compaction/pinning/eviction cases. Its CLI finding
was fixed: an invalid overlay no longer leaves an empty output file. A new
failure-path regression passes. Previously sealed helper bytes remain preserved
in the C2 bundle; generated runtime source bytes are identical.
