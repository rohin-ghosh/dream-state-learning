# Independent review: main observer/staging helpers

Review date: 2026-09-19. Static, local review; no helper/test execution,
node inspection, polling, native actions, or changes to reviewed sources.
This document is the only new artifact for this review.

## Verdict and correction to the earlier handoff

- **PASS, narrowly scoped:** the observer checks pinned source bytes and
  producer-pinned journal/prefix identities through an existing native's root.
  Its receipt explicitly disclaims new-consumer admission/startup. The stager
  creates an isolated CPU observer candidate, not a dispatch authorization.
- **No production-reader defect identified for the reported omission.** The
  hash-bound v4 consumer below checks the separately pinned epoch and every
  source-object snapshot. The observer's omission is intentional under main's
  clarified SHA-plus-prefix-identity contract, not a violation of that contract.
- **BLOCK only the stronger claim:** neither observer success nor staging
  success proves full producer-to-consumer source/epoch object equivalence,
  original receiving admission, confined startup/LOADED, or a 30-second all-in
  handoff. This is not a blanket block on the production implementation.
- My earlier unqualified “P2 integrity gap” wording was too broad. Classify it
  as an **attestation/claim-scope limitation**, not an established production
  reader vulnerability. No observer patch is required to retain its explicitly
  narrow contract. Expand its checks only if main needs the stronger preflight
  attestation; the actual consumer must still perform its own checks.

## Exact reviewed bytes

Paths and line numbers below refer to these local bytes, not an independently
fetched production-node checkout.

Main helper directory:
`research_loop/workers/post_recovery_pair_receiving_checks_20260919/`

| File | SHA-256 |
| --- | --- |
| `native_view_probe.py` | `11f84ae656cf77353b2e59183f2f628cb339a856eddf422e419ab17cab226350` |
| `stage_prefix_observer.py` | `3c24d16781917bda639a96eed858cd726d3c0e3501de1e10f3898674820dc18e` |
| `test_native_view_probe.py` | `3f080843e7dd6a65a0d224966aa2a767d90262499940aa7e7a38343836d710b3` |
| `test_stage_prefix_observer.py` | `e43b0524b1dc59f0b247188a1b94b79f5bfa6c87aa824b2a7af21bc4ddeb6b09` |

Consumer candidate directory:
`research_loop/workers/post_recovery_prefix_proof_20260919/consumer_context_v4/`

| File | SHA-256 |
| --- | --- |
| `immutable_prefix_proof.py` | `ce5542e08f463cac4d795100bdc409480b4aef162632dc2aa6642bed9d08960b` |
| `checkpoint_tail_runtime.candidate.py` | `4e7746a8da7f99cb0354beb8d489a92e8fcb387e1409256901d1a9b0a033803c` |

## Exact observer mismatch

File: `research_loop/workers/post_recovery_pair_receiving_checks_20260919/native_view_probe.py`

Function: `verify_view(root_descriptor, proof)`, starting at line 63.

- Line 68 compares the journal root chain; lines 69 and 72 compare the
  manifest/lock and journal directory identities; line 79 begins the complete
  per-record/per-intent identity comparison. These checks are not omitted.
- Line 88 begins the source check. Line 94 receives the source parent chain as
  `unused_chain` and does not compare it with the producer's source snapshots.
- Line 99 captures **current** file metadata. Line 102 compares that metadata
  with metadata at the end of the same read and with the current pathname.
  This detects changes during that read, not a completed replacement since
  proof production. Line 105 compares source bytes against the pinned SHA.
- This function never accesses `proof['source_objects']` or the separately
  bound `proof['binding']['source']['epoch']` artifact. Source directories and
  the epoch artifact therefore are not producer-identity-attested here.
- `probe()` at line 125 repeats the view check; line 130 returns
  `EXISTING_NATIVE_VIEW_VERIFIED_NOT_NEW_CONSUMER_ADMISSION`, and line 136 sets
  `source_startup_or_admission_proven=False`. Those scope disclaimers are sound.

Concrete counterexample inferred from these checks, not executed in this review:
after producing a proof, replace one pinned source file with a fresh-inode file
containing identical bytes, preserving its mode and mtime. Leave the proof and
journal untouched. The observer can pass both reads because the new file is
stable and its SHA matches. It has not proved equality with the original inode.
Likewise, replacing/deleting a separately pinned epoch artifact outside the
source pins is outside this observer's checks. Neither behavior bypasses the
v4 consumer checks described next. These examples do not depend on sleeping or
on same-clock-quantum ctime detection.

## Why this is not the same defect in the consumer

File: `research_loop/workers/post_recovery_prefix_proof_20260919/consumer_context_v4/immutable_prefix_proof.py`

- `validate_source()` at line 156 checks the separate epoch SHA at line 162 and
  each pinned source SHA at line 173. It also checks loaded-module source scope.
- The exact object-checking function is **`recheck_source_objects()`**, line
  477, called by **`VerifiedPrefix.recheck()`**, line 394; there is no function
  named `_recheck_source` in these candidate bytes.
- Line 479 constructs the required file list including the epoch; line 482
  requires exact snapshot coverage. Line 487 calls `_recheck_path()` for every
  source/epoch file. `_recheck_path()` at line 134 compares the saved parent
  chain and saved file identity, not merely metadata captured during this read.
- Line 488 requires exact source-directory snapshot coverage. Lines 495 and
  496 compare directory chains and full immutable-directory metadata. The
  compared metadata includes dev, inode, size, mtime/ctime ns, mode and nlink.
- `VerifiedPrefix.__init__()` calls `recheck()` at line 390 before prefix reuse.
  `VerifiedPrefix.finish()` at line 419 revalidates source hashes, consumer
  environment and those object checks before marking the scan finished.

Integration call sites in
`research_loop/workers/post_recovery_prefix_proof_20260919/consumer_context_v4/checkpoint_tail_runtime.candidate.py`:
`scan()` calls `prepare()` at line 196 and `verified_prefix.finish()` at line
238 before emitting a successful receipt/returning state.

Thus an identical-byte source/epoch inode replacement is rejected by the
consumer's producer-pinned identity check (`prefix_proof_external_file_changed`).
This is a static conclusion about the bound candidate, not proof that the
actual new process started under original admission with those exact bytes.

## Regression needed, depending on the intended observer contract

**If retaining SHA-plus-prefix scope:** add an explicit scope regression using
a v4-shaped proof: replace a source file with a new inode and identical bytes;
the observer may pass, must retain its non-admission receipt flags, and the v4
consumer must reject. Do not change that expected observer outcome into a
production blocker. Explicit receipt fields such as
`producer_source_object_identities_verified=False` and
`separate_epoch_artifact_verified=False` would make the limitation clearer but
are optional reporting improvements, not repairs to the production reader.

**If expanding to full producer-object preflight:** require all of these tests
before claiming the stronger result, without removing the existing source SHA
or prefix identity checks:

1. Unchanged v4 proof/source/epoch/journal passes through the supplied root FD.
2. Identical-byte source replacement with different inode, restored mode/mtime,
   and unchanged externally pinned proof rejects deterministically.
3. Replaced source root/nested directory with unchanged source bytes rejects.
4. Separately pinned epoch: changed bytes, deletion, and identical-byte inode
   replacement each reject.
5. Missing/duplicate/extra source or directory snapshots reject; use separately
   pinned malformed synthetic proofs, not an unpinned authority bypass.
6. Replacements between the two verification passes reject. Success still
   explicitly does not establish new-consumer admission/startup.

Current observer tests at `test_native_view_probe.py:38` build a deliberately
narrow fixture without epoch/source-object snapshots. The changed-source case
at line 93 changes bytes, so it does not cover an identical-byte replacement.
Existing v4 cases in `consumer_context_v4/test_consumer_context.py:125`,
`:141`, and `:159` cover every source/epoch file snapshot, actual same-byte
source inode replacement, directory metadata and omitted snapshot coverage.
These cases were inspected, not rerun in this review.

## Stager and evidence boundaries

`stage_prefix_observer.py:63` discovers an aged COMPLETE candidate, not an
original receiving authorization. `stage():100` writes an observer epoch with
`native_adoption_authorized=False`; line 113 returns
`CPU_ONLY_PREFIX_OBSERVER_STAGED_NOT_DISPATCHABLE`. No additional concrete
defect was identified in that bounded staging role. Its two tests exercise
payload validation, not the full `stage()` workflow or original admission.

Carried-forward evidence, not refreshed or polled during this review:

- `C2_EPOCH4_FAST_READ_A_1789787170.json`: failure after about 20.8 seconds,
  `journal_changed_during_scan`; **not** a successful epoch4 timing.
- Main reports `C2_EPOCH4_NATIVE_VIEW_1789787224.json`: 187 source SHA matches,
  26,242 prefix record/intent objects, two passes, about 0.3507 seconds. This
  supports only the observer's scoped claim, not full source-object identity
  attestation or new admission. This receipt was not independently reread here.
- Explicit forward-B measurement, actual confined startup/LOADED, and the
  unchanged maximum 30-second reservation remain separate proof requirements.

No request to stop, fence, rebind, restart, or change a live reader follows from
this review. A helper patch, if chosen, needs new hashes and a scoped rereview.
