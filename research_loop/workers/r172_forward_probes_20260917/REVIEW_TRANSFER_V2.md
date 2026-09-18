# R172 B5/B6 transfer/accounting repair — bounded independent verdict

**2026-09-17 16:24 UTC: B5 repaired; B6 core accounting repaired, with one
remaining concurrent disk-admission defect. REWORK / explicit enforced serial
admission disposition required for that defect.**

The serial transfer primitives pass the new complete-closure/accounting checks.
This is not full-source/controller approval, receiving-host proof, or GPU GO.
No assertion is made that an unavailable controller actually invokes transfers
concurrently; the failure is conditional on overlap at the supplied interface.

Scope: non-material B5/B6 repair only, pinned by Main to `transfer.py`
`87a1c8555a9799b8e11eaad12607b31d924003f25bc935cb4b9781890b6a9a47`
and `prep_common.py`
`2b76c48c8fdcbf91bd351c63928ad4cc349ab4b949a45d1564d24051fa14c2a3`.

The author handoff `AUTHOR_B5_B6_20260917_review1.json` has been read. Review
uses complete synthetic closure fixtures, the new explicit persistent campaign
ledger/source-cap interface, and local CPU tests only. Neither the old review
nor its regression file is changed. Missing controller integration and actual
receiving-host CPU proof remain acknowledged limitations, not unit-test passes
or newly inferred defects. This review cannot issue controller readiness or GPU GO.

Preserved starting hashes:

- `REVIEW_FORWARD.md`: `aa1cfad03fadd8a575429a18c7dd968a9007a231e38f7ccf83766d94ef5ac27e`
- `test_review_forward.py`: `d45e00b8ceb5ea8870d681baa1a5323662272ae0a73bc046b5a9782dcb7f9e75`

Only this file and `test_review_transfer_v2.py` are reviewer-owned for this turn.
No real custody/witness/response/score/map contents, remote commands, GPU/model/
provider actions, or R170/R176 work are included.

## Prompt practical-defect handoff to Main / Ampere

The final valid-interface review runs **13 tests: 12 pass, 1 fail**
(including 13 member-omission and 2 role-cap subtests). The serial end-to-end
13-file closure, exact source/wire/receive charges, growth fix, inherited source
caps, global metadata/adapter caps, staging distinction, and disk bounds pass.

**Remaining B6 defect:** `receive` creates its operation directory/ONCE before
`DiskLedger.reserve(':control', ...)`. Two valid simultaneous receives on the
same root can therefore each find the other's new directory without a control
reservation and fail with `prior_transfer_disk_custody_unaccounted_hold`.
The independent regression synchronizes only that valid interleaving; both
streams, closures, ledgers and caps are otherwise unchanged. Both once-only
keys are consumed even though neither wire stream has been read. This is not
a missing-controller-proof objection: it is observable behavior of the repaired
public receiving interface. Fix atomic/serialized admission under the disk lock,
or explicitly enforce a serialized entry contract without treating fresh peer
admission as unknown historical custody. Preserve truly unknown old holds and
all failed attempts; do not reset a ledger to make the test pass.

## B5 disposition — repaired within the transport contract

The new `validate_header` (`transfer.py:81`) requires the 13-member closure,
allows only the optional adapter README, and validates exact names, sizes,
hashes, requested identity and capture-marker reference. `validate_closure`
(`transfer.py:104`) then checks the original registration/authority/frontier,
enrolled milestone, adapter inventory, manifest/COMMIT and birth/boundary/freeze
joins using the transmitted metadata cache. It does not silently dereference
missing sender-side payload files or modify the shared queue module.

New independent checks exercise real export and receive calls with the complete
synthetic closure and explicit persistent ledger/caps. All 13 single-member
omissions, including COMPLETE itself, are rejected without a ready receipt.
A fully hashed archive whose manifest lies about the COMMIT is also rejected.
The successful receiver copies every expected byte and does not wait for an
initial capture. Sender custody rereads are forbidden by an instrumentation
guard in a separate passing receiver test. COMPLETE publication happens only
after the transport/metadata closure checks, not merely header acceptance.

**B5's earlier marker-only/incomplete-copy defect is closed for these bytes.**
This checks the transported custody references; it is not a new independent
saved-state, original TRAIN, adapter-state, or evaluator admission attestation.
No real private content was read to reach this conclusion.

## B6 disposition — original defects repaired; bounded capacity checks pass

- `Reader.raw` (`prep_common.py:146`) now uses unbuffered reads of exactly the
  reserved size. In the independent 3-byte-file/growth test it reads and charges
  exactly 3 bytes, detects growth, and preserves the charge. The old fourth
  uncharged byte is no longer read.
- `export` (`transfer.py:230`) reuses its charged metadata cache rather than
  rereading COMMIT/COMPLETE. A valid 13-file export charges source metadata and
  adapter bytes exactly once, plus a separate complete outgoing-wire charge.
  Receive charges another wire hop plus receiver control reads and the one-byte
  EOF probe. Exact arithmetic passes separately for metadata and adapter totals.
- For one direct export/receive, let P be all 13 payload bytes, A the adapter
  bytes, W the serialized archive bytes, and Cs/Cr the source/receiver control
  file bytes. The test observes total campaign charges **P + Cs + 2W + Cr + 1**,
  source read charges **P + Cs**, and campaign adapter charges **3A**. No extra
  metadata hash rereads are hidden in these results.
- Instrumented incoming reads confirm a durable reservation exists before
  every underlying read, including header, padding and EOF. Short/failed stream
  behavior and malformed/extra-member refusal also pass the rerun author suite.
- A preexisting source reservation leaving only one metadata byte of headroom
  refuses export before new source payload reads, using the actual bound caps
  rather than an invalid substitute interface. The charge and once-marker remain.
- The same persistent campaign ledger bounds all hops. Adapter headroom one
  byte below the combined export-source/outgoing/incoming requirement refuses
  receiving payload; a spent metadata ceiling refuses before any incoming wire
  read. No refund or fresh ledger is manufactured, and retries remain consumed.
- Both 24-GiB staging and 16-GiB receiving disk limits reject an over-cap new
  operation before wire consumption even with ample synthetic free space.
  Staging emits `EXACT_STAGING_COPY_VERIFIED`, never receiving readiness; an
  onward export/receive creates additional charges in the same campaign ledger.

These passing tests dispose the original B6 overread/export-reread problems
and verify aggregate source/transport/disk enforcement at this explicit local
interface. They do not claim a portable synchronized ledger, controller budget
reconciliation, a live disk observation, or an actual receiving CPU execution.

## Remaining defect V2-1 — fresh concurrent operations are treated as old debt

**Practical severity: fail-closed operational loss under overlapping receives;
no demonstrated content leak, overspend, or false COMPLETE.**

Relevant source: `transfer.py:333`–`transfer.py:337` creates the new operation
directory and ONCE before the control disk reservation. At
`prep_common.py:192`–`prep_common.py:201`, that reservation inspects all other
operation directories and requires their control reservations already to exist.
The reservation is written only after that scan. The publish lock is later,
at `transfer.py:354`, so it cannot serialize this earlier admission interval.

The regression runs two otherwise-valid receiving calls for consecutive sleeps
3 and 4 on one receiving root with one real persistent fixture ledger. A barrier
delays only each first control-reservation call until both operation directories
exist. This is a possible interleaving, not forged old artifacts, a changed cap,
a mocked validator, an incomplete archive, or the obsolete export interface.

Both calls return `prior_transfer_disk_custody_unaccounted_hold`; both input
streams are still at offset zero, and both ONCE and FAILED receipts persist.
The two no-retry keys are consumed. Because their control reservations never
existed, subsequent operations may also encounter them as unknown prior disk
custody. The positive control runs the same complete sleeps sequentially and
both receive successfully. This isolates concurrency rather than fixture shape.

Required disposition: make creation/control reservation admission atomic or
serialize it before a peer can observe an unreserved fresh operation. An
explicit **enforced** serialized receiving entry contract could instead bound
support to the passing serial case. Do not remove the genuine old-unknown-
custody hold, delete failed records, retry consumed keys, or reset disk ledgers.
The test remains an ordinary failing assertion, not an expected failure.

## Tests and evidence

All runs are local CPU only, with bytecode disabled and CUDA hidden. Temporary
test payloads are newly invented under `/tmp`; no real witness/response/score/
map files are used. Test caps/headroom and time are fixture values, not changes
to production allowances or the preparation wall. Assertions are newly written;
complete synthetic data construction reuses the inspected, hash-pinned author's
`TransferFixture`, which has no inherited author test methods.

From the repository root:

```bash
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -B research_loop/workers/r172_forward_probes_20260917/test_review_transfer_v2.py
```

**Exit 1: 13 tests, 12 pass, 1 fail; 15 parameterized subcases pass.** The only
failure is `test_new_simultaneous_transfers_are_not_mistaken_for_unaccounted_old_disk`.
The full receive/export positive and negative tests use the new ledger/cap
interface. The first 12-test run found the same race; the final run adds the
passing sequential-control test and verifies both failed operation receipts.

```bash
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH="$PWD/research_loop/workers/r172_forward_probes_20260917:$PWD" python3 -B -m unittest test_transfer_accounting test_capture_transfer test_preparation -q
```

**Exit 0: 66 tests pass** in the independent local rerun. The author's bound
focused XML separately records 90 passing testcases (66 tests + 24 subtests),
zero failures/errors/skips. Its old-review-subset XML records six testcases,
one failure; the author correctly reports that as 5 pass / 1 fail, not approval.
The obsolete reviewer export fixture omits the required ledger/caps and has
placeholder closure metadata. It was not edited or reused as proof that the
new interface is broken; the new valid-interface end-to-end export test passes.

## Exact bindings and preserved evidence

Paths below are relative to `research_loop/workers/r172_forward_probes_20260917/`
unless prefixed with `gpu/` or explicitly identified as the repository root.
Pins and preservation hashes were rechecked after tests at
**2026-09-17 16:24:25 UTC**. These are local source/evidence bindings only.

| File | SHA256 |
| --- | --- |
| transfer.py | `87a1c8555a9799b8e11eaad12607b31d924003f25bc935cb4b9781890b6a9a47` |
| prep_common.py | `2b76c48c8fdcbf91bd351c63928ad4cc349ab4b949a45d1564d24051fa14c2a3` |
| test_review_transfer_v2.py | `58dab421ead8a67762f73eb26603508ef23aff5217e678df86faf76f0e59fdb0` |
| test_transfer_accounting.py | `b172859347b4fb28a6a5e159b4f96cb5a567f5bd15dd8c1c01b81a4bdf0a01e0` |
| test_capture_transfer.py | `0415a8183441f083fa4fa63c1941565aef3b5633e1ba627529ba76ad9f1eadfd` |
| test_preparation.py | `9022a46f1c786eaef5454773fddd007adecb88e239f940705c21d7a31a7091a9` |
| AUTHOR_B5_B6_20260917_review1.json | `8d34ec6582c86e86e9f07680537f4b3a05d2262fe52cd15ccf8b4befd45f07be` |
| AUTHOR_B5_B6_20260917_review1.focused.xml | `1733034273cf5c8f1e31d8de8fe0a5074bed79d38010f0bcadc99fc9725ac3a3` |
| AUTHOR_B5_B6_20260917_review1.reviewer_subset.xml | `8c839277b8b5e6a42bd071bb586a970ee16a2910de85de233e11722bbff2a34a` |
| REVIEW_FORWARD.md — unchanged | `aa1cfad03fadd8a575429a18c7dd968a9007a231e38f7ccf83766d94ef5ac27e` |
| test_review_forward.py — unchanged | `d45e00b8ceb5ea8870d681baa1a5323662272ae0a73bc046b5a9782dcb7f9e75` |
| gpu/orch_r167_object_probe_queue.py | `c81ee45dfa23adc3cda7745fba6429fbdf3b8a6921a9baa1025b402e5bf73267` |
| gpu/orch_r167_object_survival_eval.py | `12e971f547a05319ac6aa478e7cdea07b0d84fe8e285e28e5f574d4bdfb017ce` |
| repository-root AGENTS.md | `7c9ee4b3050b72c31e933421e06a06a9fe167270dd804de97995d41bcf0a71f9` |

## Review boundary

This is a fresh, bounded B5/B6 source/CPU repair assessment, not an amendment
of the old B1–B8 review and not a new architecture/scientific authorization.
Only `REVIEW_TRANSFER_V2.md` and `test_review_transfer_v2.py` are added. Existing
review/test bytes, implementation, ledgers, capture attempts, coordination files
and other workers' R170/R176 work are untouched.

Actual receiving proof, exact controller integration/portable-ledger accounting
and any later admission remain pending as already declared by the author and
Main. Their absence is not inferred from the unit passes and is not V2-1's
evidence. Even after V2-1 is disposed and local checks pass, this document cannot
authorize GPU/model/provider execution or claim receiving/controller readiness.
