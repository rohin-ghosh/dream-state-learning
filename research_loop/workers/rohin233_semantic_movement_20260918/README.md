# R233 semantic movement sidecar

Read-only manual semantic review of Main's already-collected evidence for 16
native lives. This worker does not collect more evidence, contact providers,
change prompts, signal processes, run child code, or use GPUs. It is independent
of Main's P3 repair and aggregates. Publication is the only network write.

## Result and exact cut

- `REPORT.md`: 16-life table and individual cut/ACT timestamps.
- `REPORT.json`: SHA-bound evidence, manual judgments, canonical frame references,
  rendered-parent evidence and carefully attributed feedback.
- Collection cut: **2026-09-18T12:02:36.371377+00:00 through
  2026-09-18T12:03:44.838176+00:00**, not simultaneous.
- Local freeze: **2026-09-18T12:03:46.375117+00:00**. Later events are outside scope.

There are 32 reviewed ACTs: 26 substantive attempts, two specific plans without
the requested task artifact, two intention-only outputs and two meta-only
outputs. Substantive attempts include wrong/off-task answers and unexecuted
listings, not just successes. Fourteen lives have rendered parent events in
the defined recent request interval; P3's are retained Rohin messages, not a
fresh Astra intervention. Neither GAME_N3_7 nor GAME_UNPARENTED_N2 has a parent
event in the supplied evidence window. Wider/current status is unknown.

The narrow positive observations are C0's two-way numerical check, a checked
calculation in the frozen sibling, and caption artifacts emerging in P3 and
GAME_UNPARENTED_N2. The latter still gets a zero-extracted-caption result.
GAME_N3_0 has two exact-text matched rejected captions (ranks 63 and 62); no
selected-caption acceptance is established for the other caption pairs.
The classroom has substantive outputs, but not a checked shared conclusion in
these pairs. None of this establishes adapter improvement.

## Method

`prepare.py` froze the existing local inputs once. `private/` contains the exact
bytes and raw review material and is ignored, never published. Do not rerun the
freeze against changing Main evidence to reproduce this cut.

`report.py` validates the pinned private cut SHA, all 16 source file SHAs and the
R232 canonical parser SHA. Canonical frames require a masked REQUEST, digest-linked
RESPONSE, COMMITTED/CONTEXT_COMMITTED and R184_STAGE in order. It selects exactly
the last two committed ACTs per life, not the last two responses or THINKs.
Record cycles come from the source projection; multiple ACTs can share a cycle.
Manual judgments in `annotations.py` are bound to the cut and expected indices;
full-response span hashes bind their underlying text without publishing it.

Recent parent evidence spans the THINK immediately preceding the first ACT
through the second ACT request. Counts include retained events. Only the latest
three parent references by first visibility are projected, plus a hash of the
complete reference list. First visibility is within this window, not proof of
delivery time. Explicitly reviewed events have their own references. Peer or
child replies with a Tool prefix never count as independent evaluation.

No direct R184_ACT execution receipts exist in this evidence projection. A
listing alone is not execution; C2's rendered successful print stdout is not
a mathematical check. Judge text matches are labeled content-only matches,
not unique attempt identities. Only the N2 JSON links contain both full
response-record digest and index. P3's link uses an index and 12-hex digest
prefix. Explanatory prose that the scorer ranked is not automatically counted
as a human-readable caption.

## CPU validation and reproduction

From the repository root:

```sh
python3 -m unittest discover -s research_loop/workers/rohin233_semantic_movement_20260918 -p 'test_*.py' -v
python3 research_loop/workers/rohin233_semantic_movement_20260918/report.py
```

The tests use synthetic text plus observer-side arithmetic only; they do not
execute child code. Report regeneration additionally requires the local private
freeze. R232's canonical `audit.py` is an existing repository dependency; its
expected SHA is recorded in `REPORT.json`.

Publication uses an isolated clean worktree and an explicit file allowlist.
Only source, synthetic tests, paraphrased findings and provenance hashes are
published. No transcripts, host identifiers, addresses, credentials or binaries.
