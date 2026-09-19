# Main endpoint-owner handoff — September19 2026, 02:33UTC

**Runnable offline projected wire implemented and byte-pinned. NOT deployed.**
Main owns any later bound source application; this is not an external-permission
wait. No live restart, source edit, alias switch, native/scorer signal, parent
task, historical replay, commit or push was performed. Current children and
operational-error paths were not touched; no fresh health or scoring claim is made.

Owned patch: `projected_wire/`. **69 CPU tests pass, including26 new tests.**
The test actually runs collector CLI -> owner installer CLI -> the original
serialized Unix scorer server -> existing NativeEpoch parser/salvage/seen/epoch
methods with a synthetic CPU game, never a GPU or live scorer.

Measured synthetic oversized fixture: **71,305,512 original bytes** still fail
the old `bounded_total_journal_mirror` guard. Full local authentication produces
a **4,089-byte owner receipt and445-byte socket envelope**, retaining the
67,108,864-byte transfer cap,32MiB per-record cap and original source traversal
bounds. Complete reports, parser offsets, source attribution, policy/token
accounting and seen sets match direct original-journal processing. Unicode,
CRLF, partial ACT and THINK de-duplication are covered.

Authority is the original authenticated operator SSH channel installing an
immutable0600 file in an expected-owner0700 scorer custody directory. Child wire
text, hashes without a custody file, changed metrics/session/epoch, stale native
incarnation, tampered files, symlinks/hardlinks and expired prepared receipts are
rejected before scoring. The original session object and judge epoch are reused.

Queue continuity: durable `claim-*` before callback, `complete-*` after actual
return; unknown claims survive continuation and prohibit automatic retry.
Original seen and full game/policy snapshots are retained. The offline gate
requires zero in-flight requests, exact queue/custody/ledger manifests, unchanged
weights/panels/deadline, COMPLETE session states, and an explicit new **transport**
epoch. Do not use old `attach_epoch` with a new handoff hash; reattach the original
ledger/BINDING/ACTIVE to avoid resetting the judge epoch or shadow clock.

**Activation assumption:** a child must not be able to act as the scorer custody
owner, modify pinned collector source/config, or use operator SSH credentials.
0700/0600 do not isolate unrestricted processes sharing a UID. If that custody
assumption is false, actual OS/account/namespace separation is required; another
digest does not fix it. Main must also bind gate inputs to real stopped-writer
state/queue artifacts and connect the operational no-judgment path for all outage
causes before changing admission. These are explicit activation checks, not an
assertion that the offline patch restored live scoring.

Sealed at02:32:54.522721UTC:

- `projected_wire/MANIFEST.json` SHA256:
  `21ae68138181485352efc2d964d46d5096e2cde9d3c6659a96a8a79af2c1f952`
- Runtime source digest:
  `2419a597c31abd76cb69caa19fd537f5f1d452cfa49fcfa35733e3b77b410610`
- Evidence: `projected_wire/CPU_TESTS.txt`, `projected_wire/OVERSIZE_CPU_PROOF.json`.
- Usage/security contract: `projected_wire/README.md`.
- Source-changing sole-scorer/queue/seen/epoch plan: `projected_wire/CONTINUATION.md`.

This repository handoff does not assert an external agent acknowledgment or
production receiving-source approval. All five historical fork names, including
unparented, retain the existing R233 parented policy.
