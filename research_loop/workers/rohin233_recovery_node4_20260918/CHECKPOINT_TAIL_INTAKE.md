# C2 checkpoint-tail: non-material recovery repair

Directive: prepare a CPU-tested, provenance-preserving recovery from exact
COMPLETE11502 and retained suffix11503; Main alone owns replay replacement,
receiving timing, source/plan admission and native dispatch.

This changes startup reconstruction, not the learning architecture, base model,
benchmark, visibility, provenance or claim rules. The same canonical journal,
whole saved state, adapter/optimizer/RNG and inbox evidence remain preserved.
No history is rewritten and metadata cannot resolve pending operations.

The opt-in cold path hashes every retained prefix record's raw bytes and verifies
chain/intent bindings. It decodes historical INBOX registrations, the exact
checkpoint and referenced correction sidecar, but does not JSON-decode/replay
old REQUEST/RESPONSE transitions. It restores through the existing checkpoint
validator and applies every suffix transition through unchanged `_advance`.
Explicit `audit()` still performs full historical transition replay, restoring
the fast-path selector in `finally`, including on failure.

Cost remains **O(retained prefix bytes)** plus checkpoint/tail reconstruction.
There is no O(1) or future non-scaling-resume claim. Durable descriptors do not
silently authorize choosing a newer checkpoint. Hash changes, invalid pins,
sidecar-frontier conflicts, incomplete tails and writer conflicts still fail.

CPU evidence: 18 checkpoint-tail tests pass (1.648 seconds), plus two existing
journal regressions (0.183 seconds). These are local synthetic timings, not
receiving-node recovery timing. No production recovery or LOAD is certified by
this intake. Main owns receiving timing and the switch decision.

The copied closure is **not original-source-unchanged**: the earlier, separately
tested R227 four-file port precedes the checkpoint-tail delta. The adjacent
`CHECKPOINT_TAIL_SOURCE_MANIFEST.json` binds original source pins, R227 inputs,
intermediate hashes and final author-copy hashes separately. R227 still requires
its explicit plan/THINK selector and actual recipe evidence; staged code is not
proof of live no-exclusion behavior. Preserve the unconsumed wall-extension
authorization for the pre-LOAD continuation.

The new parent sidecar is prepared only: same parent view source, original
guard/source pins, provider, brief, ledger, cursor and masked delivery semantics.
New native identity is separately verified against its exact new guard and
actual WALL/LOAD. No native signal, journal write, parent start or waiter handoff
was performed for this preparation.
