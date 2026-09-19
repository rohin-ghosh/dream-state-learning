# Timestamp audit — frozen-source verdict, 2026-09-19

**Main's failure is valid. The original28-test freeze is NONDETERMINISTIC and
NOT promotable. No source revision, deployment or promotion occurred.**
The original main log is preserved verbatim and hash-pinned in MAIN_FAILURE.json.
All9 files listed by the original FROZEN_MANIFEST still match their frozen hashes.

## Exact cause of the test failure

`test_candidate.py:89` enters `patch.object(candidate.time, "time_ns", return_value=10**20)`
for initial validation. `decode` consequently marks freshly written files
`needs_content_fence=False`, as though they were already older than the2-second
fence window. The mutation test at line233 then rewrites an equal-length value
and restores mtime, but never forces/asserts a different ctime. Back-to-back
writes can report the same ctime here. Equal size/mtime/ctime/device/inode/etc.
then passes metadata-only reuse because the fixture disabled the raw-content
fence. My earlier green run was timing-dependent, not a stable proof.

The relevant `fingerprint`, `raw_record`, `decode` and `validate` functions are
AST-identical between the receiving baseline and the frozen candidate. This is
not evidence of a candidate-specific publication-guard regression.

## Measured comparison and residual limitation

32 bounded local CPU fixtures (8 per implementation/clock mode) were recorded:
- Forged far-future clock: baseline8/8 rejected (no equal-ctime case); candidate5/8
  rejected and3/8 missed (all3 had identical ctime/fingerprint).
- Actual wall clock: baseline8/8 and candidate8/8 rejected, including1 baseline
  and4 candidate same-ctime cases. Their active raw-hash fences caught those
  mutations. These are measured local cases, not a universal filesystem proof.

Deterministically holding the reported fingerprint equal AND falsely marking
the record settled reproduces a miss in BOTH implementations. The separate
residual test deliberately records that limitation; its success must not be
reported as source immutability. Once the raw-content fence is retired, neither
implementation detects byte changes with completely indistinguishable trusted
metadata. Truthful filesystem timestamps advancing beyond the fence interval
and compatible clock-age assumptions remain prerequisites. No ordinary-clock
local failure was demonstrated, but unconditional protection is not established.
If that metadata/clock assumption fails on a real source, keep the source blocked
and review a separately scoped proof-retirement repair; do not widen acceptance.

## Deterministic test-only proposal

The original test and source files are untouched: nothing deleted or skipped.
`test_timestamp_contract.py` is a separate proposed fixture revision:
- Real equal-size byte mutation and mtime restoration, with controlled reported
  metadata differing ONLY at ctime: exact metadata rejection required.
- Equal reported fingerprints while the record is fenced: raw-hash rejection required.
- Final fence before metadata-only reuse: content must be checked first.
- Explicit residual case: false settled-clock + identical fingerprint can miss.
- Failure latches stay set; relevant guards remain identical across implementations.

This separates the claimed guarantees rather than expecting the filesystem to
advance ctime on demand. The metadata projections are deterministic test inputs,
not a claim that a live file's ctime was modified or its precision measured exactly.
No production implementation or runtime test replacement is authorized here.

## Exact final results

| Frozen/test artifact | Result | Meaning |
|---|---|---|
| Main's ORIGINAL28 tests |27 PASS /1 FAIL,0.095s | Preserved independent failure |
| Unmodified ORIGINAL28 audit rerun |28 PASS /0 FAIL,0.091s | Confirms timing dependence; does NOT supersede main |
| Separate deterministic contract tests |14 PASS /0 FAIL |7 baseline +7 candidate cases; residual miss explicitly disclosed |

The final deterministic run's exact elapsed time, full output and file hashes
are in CONTRACT_TEST_RESULT.json. Original candidate SHA256 remains
`1d11d58676aa9a00cabc989dfcc545de048e612912b3c1d30f56a6b47ee40099`;
baseline remains
`8bd9f79620a42653d9727045e9fab36497345bb586658be649eaf6cc088af0bb`.

## Files added only in TIMESTAMP_AUDIT_1605

- MAIN_FAILURE.json — original verbatim failure, source hashes and file pins.
- CLOCK_DIAGNOSIS.json — all32 local filesystem/clock observations and guard AST comparison.
- FROZEN_RERUN.json — full unmodified28-test rerun output.
- test_timestamp_contract.py — isolated deterministic test-only revision proposal.
- CONTRACT_TEST_RESULT.json — exact14-test final result and proof limits.
- FINAL_RESULT.json — machine-readable verdict and unchanged frozen-file checks.
- VERDICT.md — this handoff.
- MANIFEST.json — hashes of this new audit's final files.

**No promotion. Parent and original queue failures remain latched.** No remote
reads, provider calls, capsule retry, ledger change, source substitution, unpause,
GPU execution, commit or push occurred. The historical probe-publication error
still lacks its original failed path/fingerprints; this timestamp audit does not
retroactively clear that separate failure.
