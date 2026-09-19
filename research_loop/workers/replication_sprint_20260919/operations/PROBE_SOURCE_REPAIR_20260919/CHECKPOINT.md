# Frozen probe-source repair checkpoint — 2026-09-19

**READY for main's CPU/code review only. NOT READY for live repair or unpause.**
Candidate implementation stopped at the explicit checkpoint. Only witness tests
and receipts were added afterwards. Original FLEET_CUT_1540 is untouched.

## What is actually established

The receiving native writer, SHA256
`08dab0bb84596b522fc08db8cdb2c4a26db9e416acfcf9cc35bacdd233d924a4`,
fully writes and fsyncs `NAME.json.partial`, creates the canonical hard link,
fsyncs the directory, unlinks the partial, and fsyncs again. The receiving
`epoch_cache.py` SHA256 is
`8bd9f79620a42653d9727045e9fab36497345bb586658be649eaf6cc088af0bb`.
It records device/inode/mode/ownership/link-count/size/mtime/ctime before reading.
The writer's legitimate link retirement changes nlink 2 to 1 and ctime without
changing source content. A deterministic CPU interleaving reproduces the exact
`source_record_changed_during_read` error and permanent failure latch in that
pinned baseline, with identical bytes before and after.

**The exact historical comparison is NOT established.** The original daemon
log records only the generic error, not source/index/path, failed check, or
before/after fingerprints. There are four checks with that error string. It is
not lawful to convert current stable hashes into proof of historical immutability.

The strongest time-correlated artifact is frozen sibling RESPONSE5614:
`/localhome/local-rohing/orch_r232_curriculum_frozen_20260918/raw/stream/records/00000000000000005614.json`.
Its mtime is13:59:42.534490 UTC, ctime13:59:42.575490; the pause WAL mtime is
13:59:42.604490 and log mtime13:59:42.672490. Its declared canonical hash is
`d9dc5eda02148b5277a51582e0691e3d50b055cb00678562446ef3a1376730cc`.
The current in-place raw hash is stable and pinned in FAILURE_WINDOW.json;
no full journal replay occurred. This is a strong candidate, not an asserted
historical attribution. Learner UPDATE11864 preceded it by3.5 seconds and
UPDATE11865 was created after the pause. The prior pending learner log entry
is not proof that the learner caused the later failure.

## Frozen candidate and limitations

Candidate SHA256:
`1d11d58676aa9a00cabc989dfcc545de048e612912b3c1d30f56a6b47ee40099`.
Only `EpochCache.snapshot` changes: after checking all previously verified
fingerprints, a newest, unverified, post-anchor canonical record with nlink=2
and an exact fingerprint-matched `.json.partial` sibling yields explicit
publication-pending, before reading/caching/admission. After the writer retires
the extra link, ordinary full canonical/chain/base/LOADED validation is required.

No changed-source exception is caught or ignored. All original raw-file identity,
size, before/after/path fingerprint, canonical hash, chain, source/base, new-LOADED,
timestamp-fence and sticky-failure checks remain. If the partial disappears
before the matching witness is observed, the original fail-closed error remains;
this residual ambiguous race is intentionally NOT patched away. The candidate
does not clear the running cache's already latched failure or the queue pause.

## Scientific admissibility and consumed work

**No existing epoch change is admitted or authorized.** No source substitution,
rewriting, latest-checkpoint selection, new-LOADED adoption, visibility change,
scientific equivalence claim, or acceptance-test relaxation occurs. Same-epoch
append remains subject to the complete existing proof and exposure/admission
rules; pending is not admission. Current LOADED pins remain learner2466 and
frozen1763, with both original index1 anchors unchanged.

The concrete registered capsule is not guessed from newest files: job
`4694399fdaa00125796b604de48551af434e8377a5ac06795bfa31241b4c5c3f`,
frozen journal`30fa18c869b34fd496a2758a4a28e197`, sleep24,
SLEEP_COMPLETE index800,
`7dfa305c4c2d689bd72a6ff343448c36246a2398190291d46688852ca1b565cd`,
adapter state`04341ab86f5f98718bc53218166537ecc20fc7d5053f3ed47cc0fcdda918f5d0`.
Its actual CAPTURE/config/LAUNCH/DISPATCHED receipts join those identities.
It was already dispatched and must not be retried. The pause had selected_key=null,
no active jobs, and8 no-retry attempts; it arose in source observation, not proof
of a new capsule launch failure. Original DB/WAL hashes are preserved; neither
SQLite file was opened through SQLite or edited. All retained pending eligibility
remains pending, never converted to accepted, failed scientific scores, or retried.

The existing capsule runtime manifest pins the OLD epoch-cache hash. The new file
cannot be silently substituted. Any future receiving closure or eligibility
reconciliation requires main's explicit review, without resurrecting a consumed
capsule. This checkpoint supplies no live repair authorization.

## CPU proof and boundaries

28/28 tests pass:22 regression/reproducer tests plus6 frozen-witness tests.
The added witness tests compare exact bytes AND SHA256 for synthetic sealed
context and source fixtures, preserve canonical source-record bytes and cached
prefix evidence under concurrent append, and preserve policy/capsule/consumed-job
ledger fixtures. Negative tests retain hard failure on genuine mutations and
make the byte-equivalence assertion fail if sealed-context fixture bytes drift.

These are **synthetic CPU custody proofs**, not an audit of actual sealed panel
contents, a proof of historical production equivalence, or a scientific run.
No production modules, provider calls, GPU/model loads, dispatchers or ledger
writers run in these tests. Tests write only temporary fixtures within this folder.

## Changed paths — all new, confined here

- `candidate_epoch_cache.py` — frozen isolated implementation candidate.
- `test_candidate.py` —22 source/publication regressions and baseline reproduction.
- `test_frozen_witness.py` —6 synthetic sealed-byte/prefix/no-retry custody tests.
- `REMOTE_DISCOVERY.json` — exact receiving code/policy/capsule/log identities.
- `FAILURE_WINDOW.json` — native publication code, timed artifact metadata and in-place hashes.
- `CANDIDATE_PROVENANCE.json` — baseline/candidate hashes and restricted scope.
- `CHECKPOINT.json` — pre-witness-test freeze and explicit non-admissibility decisions.
- `CPU_TEST_RECEIPT.json` —28-test result and limits of proof.
- `CHECKPOINT.md` — this review handoff.
- `FROZEN_MANIFEST.json` — complete file hashes for main's review.

**Real blocker retained:** exact historical failed metadata witness is absent;
ambiguous identity/content change still fails closed; the original pause and
consumed-capsule prohibitions are untouched. No production edit, unpause, retry,
source substitution, provider call, GPU run, commit or push was performed.
