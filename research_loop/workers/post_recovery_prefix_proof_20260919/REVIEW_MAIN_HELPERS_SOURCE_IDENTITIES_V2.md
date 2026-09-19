# Independent rereview: native-view source/epoch identity patch

Date: 2026-09-19. Static local code/test inspection and local receipt inspection
only. No helper or test execution, node access, polling, or live actions.
The earlier `REVIEW_MAIN_HELPERS.md` is preserved unchanged as the review of
the prior helper bytes. This rereview supersedes its missing observer-check
finding for the exact new hashes below, not for the old helper.

## Scoped verdict

**PASS: the patched observer closes the previously identified source/epoch
object-attestation omission.** It compares the producer's exact source/epoch
file inventory, parent chains and file identities, separately verifies their
content SHAs, and compares the complete immutable source-directory inventory,
chains and full metadata. Both complete verification passes include these
checks. No blocking correctness defect was identified in this bounded patch.

**PASS: the supplied real receipt is internally consistent and bound to the
reviewed helper and receipt-time test revision.** A subsequent test-only
addition was also inspected, as distinguished below. The receipt supports existing-native filesystem-view
preflight, now including source-object identity, for the reported observation.

**BLOCK only stronger claims from this evidence alone:** original receiving
authorization, startup in the new consumer's actual confinement, LOADED, and
the all-in maximum 30-second handoff remain unproven by this observer receipt.
This review does not authorize deployment or request a fence/stop/rebind.
The actual consumer still must perform its own exact guard/admission,
environment, source-object, prefix and raw interval/tail checks.

## Exact byte bindings

Directory:
`research_loop/workers/post_recovery_pair_receiving_checks_20260919/`

| Artifact | SHA-256 |
| --- | --- |
| `native_view_probe.py` | `b0d44975c5a484125b2b94b29dd7333c592e1bb05c137eb5023bc52cc9f8a6e9` |
| `test_native_view_probe.py` (current, including additional metadata case) | `5cc11a6ea7dbc53125b41b652360f966bb0fdaf8d48b33cdc495ff149def31ae` |
| `test_native_view_probe.py` (earlier reviewed revision, bound by real receipt) | `1c61b5628edab1a820a19e7367a4ce3ceb296ae9ae371b5a7abbd965a31b2823` |
| `C2_EPOCH4_NATIVE_VIEW_IDENTITY_1789787593.json` | `56d898f29899c291e8c165b4f5d45eb0353c179256213bc86268daacd687fad9` |

The unchanged stager SHA is
`3c24d16781917bda639a96eed858cd726d3c0e3501de1e10f3898674820dc18e`;
its test SHA is
`e43b0524b1dc59f0b247188a1b94b79f5bfa6c87aa824b2a7af21bc4ddeb6b09`.
The previous stager-only verdict is unchanged; this patch does not make that
observer stager a production admission mechanism.

## Exact closure of the earlier finding

File: `research_loop/workers/post_recovery_pair_receiving_checks_20260919/native_view_probe.py`

- `verify_source_view()` begins at line 69. Line 72 includes the separately
  bound epoch in the expected file/SHA inventory; line 74 adds sorted source
  pins. Line 79 rejects overlap with the epoch path.
- Line 87 requires the exact ordered file-path inventory, so omissions,
  duplicates and extras do not pass. Line 89 requires the exact inventory of
  source root and all intervening source directories.
- Line 95 opens each source/epoch parent through the supplied native root FD.
  Line 97 compares its producer-pinned chain; line 102 compares the opened
  regular file's full identity against the producer snapshot, before reading.
  Lines 105 and 108 retain read-stability/path identity and content-SHA checks.
  Identical-byte replacement cannot pass just because the newly opened file
  is stable: its identity must first equal the producer's snapshot.
- Line 113 iterates every immutable source-directory snapshot. Lines 117 and
  118 compare its chain and full metadata. `immutable_directory_identity()`
  at line 32 includes dev, inode, size, mtime/ctime ns, mode and nlink.
- `verify_view()` at line 125 retains the original journal root,
  manifest/lock, journal-directory and all record/intent identity checks;
  line 149 calls the new source verifier.
- `probe()` at line 152 retains exact proof SHA, same boot and native process
  checks. Lines 164 and 165 execute the entire verification twice. Line 172
  now reports source identity attestation; line 177 still correctly disclaims
  new-consumer startup/admission and requires consumer revalidation.

The prior defect was in a stronger interpretation of the observer's receipt,
not an established omission in the v4 production-reader candidate. The new
observer now supports the stronger filesystem-object preflight claim as well.

## Regression inspection

File: `research_loop/workers/post_recovery_pair_receiving_checks_20260919/test_native_view_probe.py`

The fixture at line 28 includes a separate epoch; line 38 captures producer
file/parent snapshots; line 52 includes immutable-directory snapshots.
The positive test at line 77 asserts the new counts/attestation while retaining
the non-admission and no-live-action flags.

The initially added seven cases cover identical-byte source replacement (line 128),
identical-byte epoch replacement (line 135), source directory mutation
(line 142), source-file parent-chain mismatch (line 147), omitted source/epoch
snapshot (current line 159), omitted directory snapshot (current line 165), and epoch SHA
mismatch (current line 171). The replacement cases allocate a new file while the old
file still exists, so they do not rely on a sleep or timestamp-granularity
assumption to obtain a different inode.

**Coverage note resolved during rereview:** the initial directory-mode test
could fail at the earlier parent-chain check, without isolating the full
metadata comparison. The test file changed during review to add
`test_source_directory_full_metadata_rejected()` at current line 153. It
changes only a directory snapshot's `identity['mtime_ns']`, leaves its chain
unchanged, explicitly pins the synthetic proof through the fixture, and
requires `same_immutable_source_directory_metadata`. This directly addresses
that nonblocking coverage note without a timestamp-resolution assumption.
Removing only those six added lines from the current file reproduces the
earlier receipt-bound test SHA exactly. Helper and receipt bytes are unchanged.
There is no outstanding finding from this coverage note.

Main reported 28 passing worker tests before this additional test-only change.
This rereview inspected the earlier 13 observer methods and the added 14th
method, but did not rerun tests, attest execution of the added test, or
independently attest the broader worker-suite execution.

## Real receipt checked

File:
`research_loop/workers/post_recovery_pair_receiving_checks_20260919/C2_EPOCH4_NATIVE_VIEW_IDENTITY_1789787593.json`

- Return code 0; empty stderr. Parsed `stdout` exactly equals `report`.
- Recorded `helper_sha256` matches the unchanged reviewed helper. Recorded
  `test_sha256` matches the earlier reviewed test revision, not the subsequent
  metadata-case addition. The old receipt is not relabeled as evidence that
  the added test ran.
- Proof SHA:
  `feda00b37b392c306c59bac8f0c6099c01c66b843c09a7f3ea153f07fb075ad4`.
  This is the same reported epoch4 proof pin, not a newly produced proof.
- Reports 187 source files plus 1 separate epoch and 8 source directories;
  26,242 prefix record/intent files; two complete verification passes.
- Inner observer time: 0.297167362 seconds. Wrapper time: 1.190780401 seconds.
  These are not reservation-to-LOADED or total handoff timings.
- Native PID 1139778, start ticks 30025875, UID 2524;
  boot `2c05ffec-1b4c-472f-9688-2a37543a6f4a`;
  existing native mount namespace `mnt:[4026536303]`.
- `source_identity_attested=True`,
  `source_startup_or_admission_proven=False`,
  `next_consumer_must_revalidate=True`, `live_adoption=False`;
  zero GPU calls, journal writes, native signals and raw prefix bytes hashed.
  The metadata-not-cryptographic-immutability disclaimer is retained.

This confirms receipt consistency, not an independent rerun on node5 or a
measurement of a newly confined process. The existing producer quiet-age and
metadata-coherence/no-concurrent-prefix-mutation trust assumptions remain;
two metadata passes are not a replacement for them.

The earlier `C2_EPOCH4_FAST_READ_A_1789787170.json` remains a failed scan
(`journal_changed_during_scan`), not timing success. No later scan,
authorization or live state was polled for this rereview.

## Addendum: forward-B production-source CPU scan

2026-09-19: inspected the specifically supplied local receipt, without polling
or running any helper, test or native action:
`research_loop/workers/post_recovery_pair_receiving_checks_20260919/C2_EPOCH4_FORWARD_B_1789787815.json`.
Receipt SHA-256:
`2ccc7d689cab0001e6de4844244f2bd8197f4c944e6deb6f9d6db67723ec5c5e`.

**Scoped PASS:** the receipt reports a successful real epoch4-source read-only
forward-B scan, not merely the earlier A-to-A benchmark. Outer return code
and both nested command return codes are zero, with empty stderr; parsed outer
stdout exactly matches the outer report.

- Reuses prevalidated COMPLETE A=13120 and selects exact COMPLETE B=13231,
  SHA `8715c6a9c27d97ed1a8dbf14abc6c73d044d7a733f868678806152b86a705d54`.
  The wrapper records LEARN=13232 and optimizer step count 8780.
- Rechecks metadata for 13,121 prevalidated prefix records and reports full
  raw verification of the 111-record A-to-B interval: 602,615,152 bytes.
  It also reports full raw verification of four tail records: 52,678,239 bytes.
- Total newly hashed raw record bytes: 655,293,391. Reports 360 INBOX entries,
  pending REQUEST=true, RESPONSE=false, SLEEP_REQUEST=false, pending preserved,
  and the correction-ledger sidecar present.
- Scan internal elapsed time: 4.318751402 seconds. Its command wrapper takes
  4.517996270 seconds; the enclosing recorded operation takes 6.735642672
  seconds. None is a reservation-to-LOADED/all-in handoff measurement.
- The same proof SHA remains
  `feda00b37b392c306c59bac8f0c6099c01c66b843c09a7f3ea153f07fb075ad4`.
  Exact forward guard SHA:
  `1b306e25143491ee974e68748b137ab0a4edab6bfba91a5f870c385f5d64f87b`.
  `implicit_fallback=false`, `prefix_rewritten=false`; no writer lock acquired.

**Authority/confinement limit remains explicit:** guard creation reports
`CANDIDATE_NOT_AUTHORIZATION`; scan reports
`READ_ONLY_PROBE_NOT_LOADED_OR_DISPATCH`. Consumer context is
`SAME_MOUNT_NAMESPACE`, with producer and consumer namespace inode 4026531832,
same boot, and `admission=null`. This is not execution in the original native's
namespace 4026536303, not original receiving admission, and not a handoff.
The receipt reports no GPU calls, journal writes, native signals or live
adoption. There is still no all-in <=30-second proof from these observations.
The failed earlier A scan remains a failure; this distinct forward-B receipt
is the new scoped success.

Main now reports 29 passing worker tests, including all eight new observer
regressions and the isolated full-directory-metadata case. This supersedes the
earlier user-reported count of 28, not the exact test/receipt SHA distinction
above. No tests were independently rerun for this addendum.
