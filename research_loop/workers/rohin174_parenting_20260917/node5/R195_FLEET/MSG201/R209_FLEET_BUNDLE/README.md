# R209 transferable English-child quarantine and console drain

This is the unchanged 42-file R206 source frame with exactly two runtime files
replaced by the tested original-C2 R209 delta. It is an overlay, not a complete
standalone repository, checkpoint, plan, launch command, or ownership transfer.
No existing frozen bundle is rewritten. No fleet deployment is performed here.

## Payload and provenance

- `runtime_overlay.tar.gz`: all42 original R206 paths, only2 changed contents.
- `runtime_delta.patch`: those2 source changes against exact frozen R206.
- `regression_tests.patch`: narrow additions/expectation update to2 shared tests.
- `READY.json`: archive/file/patch hashes, exact base, feature options and checks.
- `SHARED_TEST_RECEIPT.json`:62 shared-source tests PASS, zero skips.

READY's actual status is `CPU_TESTED`, not an invented `READY` status. Original
C2 already has LOADED6544 at September18,2026 04:43:24.940UTC; its operator
applied the ordinary existing bridge binding after the portable source checks.
Other node operators retain their own launch/bridge bindings and custody.

Changed shared paths:

1. `gpu/orch_r184_think_act_learn.py`
2. `organism_v6/orch_r203_prose_target_filter.py`
3. `tests/test_orch_r184_think_act_learn.py`
4. `tests/test_orch_r203_prose_target_filter.py`

## Receiving with existing handoff machinery

1. Stage a fresh receiving copy, never overwrite an active source tree. Check
   the archive SHA and42 source hashes in READY. Alternatively apply the runtime
   patch to exact R206 bytes; do not force it across local bridge modifications.
2. Start from that arm's current plan. Merge only READY's feature-option maps.
   Verify its existing native prerequisites. Do not import the old R206
   manifest's whole native option map: that map contains a16-presentation default.
3. Preserve **P4/P32/other authorized `new_presentations`, `plasticity` including
   `learning_rate_multiplier`, optimizer LR groups, rehearsal setting, anchor,
   stage budget, wall, GPU identity, parent treatment and trial identity**.
   No LR or presentation setting exists in this bundle's override maps.
4. For an English arm opting into the prose filter, set
   `think_act_learn.prose_target_filter=R209_ENGLISH_PROSE_TARGET_QUARANTINE_V1`.
   Also retain R205 console ACT, R206 pins, R195 review and R203 stage boundaries
   as specified in READY. Existing row annotations with the old R203 policy
   remain capitalization-only; do not rewrite historical annotations. A plan
   using the new source and opting into prose filtering must use the new policy.
5. Rebind the normal guard/source pins and existing tool bridges to the staged
   source. The frozen CPU/exchange/transport console-origin exclusions and NFKC
   code policy are unchanged. Preserve the exact next COMPLETE checkpoint,
   history, journal, inboxes, optimizer and saved RNG before the same-life reload.
6. Report actual LOADED, first REQUEST/parent visibility, first R195 review and
   TARGET_ELIGIBILITY. Wrapper startup is not LIVE. No synthetic human turn is
   needed or authorized on a live life. This package adds no new approval gate.

## Exact behavior and limits

Every fresh genuine source-attributed Rohin inbox gets its own direct ACT and
receipt before the ordinary stage, including LEARN. Later queued turns are
not marked seen by an earlier reply. Arrivals during review trigger a reply and
another review before training. The final inbox poll is the admission cutoff;
an already-started sleep finishes before the next opportunity. No parent answer
or replay of historical consumed messages substitutes for a child reply.

The opt-in English-child filter checks only NEW child targets, including console
ACT, under existing R195 exclusion machinery. It preserves capitalization checks
and provisionally excludes fullwidth or CJK/Kana/Hangul glyphs in the bounded
65,536-character scan. It is not a general language/quality detector. Deliberate
quotations can be excluded too; use this policy only on the authorized English
arms. Human/parent text and masked prefixes are not scanned or normalized.
Raw targets, responses and journal evidence remain unchanged even when excluded.

Original C2's first live review6576 checked4 clean rows and excluded0. The earlier
ACT6441 is rejected only in retrospective classification:97 CJK/four fullwidth
characters, exact raw target hash in the adjacent operator receipts. Its16 prior
optimizer updates remain in COMPLETE59/AdamW5308; no rollback, undo or unlearning
is claimed. Current queue/exclusion receipts are posted separately in COORDINATION.

Rebuild from the repository root with `python3 <this-directory>/build_bundle.py`.
The builder refuses to overwrite a published READY, verifies the shared bytes
against the deployed delta, and checks recipe-preserving merges for P4/P16/P32
at all three existing LR multipliers. These are packaging checks, not GPU tests.
