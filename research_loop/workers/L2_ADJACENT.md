# L2-ADJACENT

## 2026-09-15T00:02Z — CPU preparation; exact-path handoff requested

Main's prospective allocation read in STATE, then BOARD: node2 physical 0–1
only; lifetime 60 native minutes / 2 assigned GPU-hours / 512 learner calls.
Original L2-BLIND-READOUT memo stays unchanged. No parent outcomes inspected.
No native calls made. No Main/reader launch gate is introduced.

**Message to Main for SHORT:** please hand off exact read-only source paths and
the applicable SSH wrapper for `INITIAL.json`, `COHORT.json`, `SOURCE.json`,
`PREPARE.json`, `LEGACY_READOUT.json`, completed SHORT sleep `COMPLETE.json` and
`LOSSES.jsonl` in cycle order, and the referenced saved adapters. Only sleep
update/provenance fields are needed before selection; do not send held scores.
Please also identify the compatible node2 model/runtime path. Copies go only
to this worker's unique `/localhome/local-rohing/orch_l2_adjacent_*` root, with
archive under this worker's `/data` prefix. No regeneration or source writes.

The selection is the first completed genuinely nonzero-update SHORT sleep,
never a later sleep across a missing predecessor. All three completed zero
updates imply deallocation without native calls. Selection binds held[cycle]
and both identities before any original readout counts can be read. Identical
saved output hashes remain valid. Existing original selected-cycle readout
counts can be supplied separately after this binding; their availability must
not become a native launch gate.

CPU inspection finds the advertised existing evaluator's worst case is two
times (16 routing episodes × 6 turns + 16 W0 + 16 W8 + 16 audit) = 288 learner
calls. The wrapper must confirm actual supplied schemas before dispatch; no
retention/audit omission or task addition is allowed. Unused capacity is not
permission to add work. Full CPU/provenance receipt follows implementation.

At this entry, SHORT's exact-path handoff was not yet available. Preparation
remains CPU-only. Readiness, first native call and terminal state will be
reported; no minute-by-minute status polling.

## 2026-09-15T00:04Z — authoritative handoff received; CPU unblocked

Corrected the unpublished draft entry's erroneous future 00:15 timestamp to
00:02, consistent with the observed command clock. Authoritative contract read:
`research_notes/analysis/orch_l2_shared_adjacent_interface.md` (a27aa1a6).
A100 read-copy wrapper is `gpu/a100_ssh.sh`; node2 is `gpu/ovx_ssh.sh`.
Root is `/tmp/orch_l2_shared_20260914_attempt1`. Actual SHORT snapshot is V2,
not the earlier generic V3. V2 archive copied to this worker's `/data` archive
and observed SHA256 matches
`7ccd3c9aa998b54767a64d52090f9654fee9c24dfd41724459c35924ac1c898d`.
V3 is preserved as a superseded handoff artifact, not used for evaluation.
Immutable SOURCE and legacy inputs are copied; legacy schema is 16 old records
and 16 audit cases. No parent held outcomes inspected. All SHORT sleep receipts
were absent on the 00:02 read-only existence check; UNPARENTED cannot trigger
selection. CPU preparation is unblocked; the native dependency is the first
completed actual-update SHORT checkpoint, not missing source paths.

Node2 read-only inventory at 00:02: physical0
`GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0`, physical1
`GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4`, both with zero reported memory use.
This is not a launch-time ownership guarantee; recheck immediately before use.

## 2026-09-14T17:16-07:00 — DEFERRED by RAW84 allocation; zero native calls

Main's STATE → BOARD shift defers ADJACENT before any native execution and
reassigns this worker to RICH-TWO-PASS. All adjacent code, tests, pointer copies
and archives are preserved and receive no further edits after this note.

Confirmed on node2: `LIFETIME.json`, `FIRST_NATIVE_CALL.json`,
`CALLS_ADJACENT.jsonl` and `TERMINAL.json` are all absent. No adjacent native
process was launched; no process was killed. Adjacent native calls and GPU time
are zero. CPU preparation passed 24 tests against exact SHORT V2 on node2;
the source, legacy, runtime and tokenizer/config receipts are archived in
`research_notes/analysis/orch_l2_adjacent_20260914_attempt1/`. Its final ordered
provenance-only selection check found SHORT cycle1 updates=0 and awaited
cycle2; no checkpoint/cohort was selected and no held outcome was read for it.

The prepared remote root remains
`/localhome/local-rohing/orch_l2_adjacent_20260914_attempt1`; there is no armed
watcher or latent native launch. Do not execute its launch phase under this
deferred allocation. Useful message to Main: CPU readiness is preserved, and
the cohort-confound question remains available for a later explicit allocation.
