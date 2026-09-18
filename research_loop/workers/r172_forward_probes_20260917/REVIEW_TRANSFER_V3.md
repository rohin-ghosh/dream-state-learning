# R172 transfer V3 — scoped independent CPU/source PASS

**Verdict: PASS for the pinned B6 atomic-admission repair and the exercised
B5/B6 transport/accounting contract. V2-1 is closed on these new bytes.**

Reviewed and hash-rechecked **September 17, 2026, 16:38:46 UTC**. There are no
remaining defects identified in this bounded repair review. This is not full
runner/controller approval, actual receiving-host proof, saved-state admission,
scientific evidence, or GPU/model/provider GO.

## Prompt handoff to Main / Nietzsche

Bernoulli's repaired admission passes independent local tests. For the planned
C2/C5 receiving preparation, the V2 concurrent-admission component blocker is
disposed for the exact hashes below. Actual receiving CPU/provenance and any
controller/ledger integration or execution authorization remain separate. No
receiving operation, remote command, or GPU/model/provider action was performed
by this reviewer; this document does not supply those missing approvals.

## Exact scope and instructions

Non-material B6 race repair only, preserving the frozen instrument, budgets,
private-data rules, original custody references, no-retry semantics and old
receipts. Applicable repository-root AGENTS.md was read; there was no narrower
guidance file on the reviewer-owned directory path. Only this new review and
`test_review_transfer_v3.py` are added. All earlier review/test files remain
byte-for-byte unchanged, and other workers' priorities are untouched.

Main's exact new-source pins are:

- `transfer.py`: `e8b3aed5abe19cfc195ac4fde318e8316834c582d883e9dcfce892b02f19bb2e`
- `prep_common.py`: `f6751d157bb283627a185ecf14321d571673512b61f17aedac3b056ef5410aee`
- `test_transfer_admission_race.py`: `79ed428eb1e5e0acb9a3ca0a796129d830be8e137dc1de1379443c0e306a24ba`

## Why the race is closed

At `transfer.py:334`, receive takes the existing role/root disk lock **before**
operation-directory creation and ONCE publication. It invokes
`DiskLedger._reserve_locked` for the control reservation while retaining that
same lock. The reservation therefore precedes release of the admission lock.
`prep_common.py:186` makes ordinary disk reservations acquire the same lock
before calling the shared helper, so a competing control or payload reservation
cannot inspect a half-created operation through a different lock path. Control
reservation failures preserve FAILED/ONCE while still inside the protected
admission, rather than erasing failed attempts.

The independent test pauses a real receive immediately after ONCE is written,
before its control reservation. A separate file descriptor's nonblocking
`flock` is rejected, demonstrating that the actual disk lock is held. A second
valid receive attempts that lock, but its operation directory does not exist
and its future remains pending until the first admission is released. After
release, **both complete successfully**, for both receiving and staging roles.
No validator, disk reservation, or lock acquisition is replaced with a fake
success. The hook only observes the real lock and delays the existing write
interleaving; all payloads and persistent ledgers are synthetic local fixtures.

The independent test also verifies four durable disk reservations per pair
(control and payload for each copy), exact allocation-rounded disk totals, full
stream consumption, both completion receipts, and absence of failure receipts.
Exact incoming metadata/adapter charges include both control reads, wire bytes,
EOF reservations, and the second copy's existing shared-metadata rereads.

The rerun author race suite additionally exercises a prior payload reservation
overlapping fresh admission, for both roles, plus genuine unknown old
control/payload custody and consumed disk-cap failures. All pass locally.

## Closure/accounting preservation

- A new independent test exports the complete 13-member closure through the
  explicit existing campaign ledger and original source caps, then receives
  it and verifies every copied byte.
- For payload bytes P, adapter bytes A, archive bytes W, and source/receiver
  control bytes Cs/Cr, this roundtrip observes total campaign charges
  **P + Cs + 2W + Cr + 1**, source read charges **P + Cs**, and adapter charges
  **3A**. The admission-lock change introduces no uncharged payload reread or
  budget reset in this checked path.
- A transport whose header hashes match changed adapter bytes but whose
  original COMMIT inventory does not match is rejected before positive-copy
  publication. Charges persist and the consumed operation cannot retry.
- Genuine unknown old disk custody still holds before wire consumption;
  original evidence stays unchanged and the failed new attempt remains consumed.
- The complete focused local suite reruns aggregate metadata/adapter limits,
  source caps, disk caps/free-space refusal, exact read-before-charge behavior,
  malformed/incomplete closure rejection, and staging/receiving distinctions.

Thus V2's false peer-as-old-custody failure is repaired without weakening the
genuine historical-custody hold or completeness/accounting checks exercised by
this review. This does not claim a new synchronization design for a remote
campaign ledger or prove an unprovided receiving controller.

## Reproduction and observed results

Commands run from the repository root. All test data is invented under local
`/tmp`; no sealed responses, maps, score files, or actual TRAIN/witness content
are opened. The audited author fixture builds the complete synthetic custody;
the four new test methods and assertions are independent. Each new test first
checks the new source, author race-test, and fixture hashes.

```bash
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -B research_loop/workers/r172_forward_probes_20260917/test_review_transfer_v3.py
```

**Observed exit 0: 4 independent tests PASS**, including both role subcases of
the concurrency/lock/accounting test. No failures, skips, or expected failures.

```bash
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH="$PWD/research_loop/workers/r172_forward_probes_20260917:$PWD" python3 -B -m unittest test_transfer_accounting test_capture_transfer test_preparation test_transfer_admission_race -q
```

**Observed exit 0: 70 focused tests PASS** in 12.958 seconds. Main supplied the
author's 70-test/34-subtest report; this reviewer independently ran the 70-test
suite successfully, rather than relying on that report. Unittest's summary
does not separately enumerate subtests. The historical before-fix failure and
the V2 pinned test remain preserved, not overwritten or repinned to turn green.

## Exact local bindings and preservation

Paths below are relative to `research_loop/workers/r172_forward_probes_20260917/`,
except `gpu/` paths, which are repository-relative. Hashes were checked after
the passing tests. These are **local** bindings, not receiving-host attestations.

| File | SHA256 |
| --- | --- |
| transfer.py | `e8b3aed5abe19cfc195ac4fde318e8316834c582d883e9dcfce892b02f19bb2e` |
| prep_common.py | `f6751d157bb283627a185ecf14321d571673512b61f17aedac3b056ef5410aee` |
| test_transfer_admission_race.py | `79ed428eb1e5e0acb9a3ca0a796129d830be8e137dc1de1379443c0e306a24ba` |
| test_review_transfer_v3.py | `090a2a8725d89983dc9acf3e2cd2d909d239bf0c9bce7dea6055e176630f5e15` |
| test_transfer_accounting.py | `b172859347b4fb28a6a5e159b4f96cb5a567f5bd15dd8c1c01b81a4bdf0a01e0` |
| test_capture_transfer.py | `0415a8183441f083fa4fa63c1941565aef3b5633e1ba627529ba76ad9f1eadfd` |
| test_preparation.py | `9022a46f1c786eaef5454773fddd007adecb88e239f940705c21d7a31a7091a9` |
| gpu/orch_r167_object_probe_queue.py | `c81ee45dfa23adc3cda7745fba6429fbdf3b8a6921a9baa1025b402e5bf73267` |
| gpu/orch_r167_object_survival_eval.py | `12e971f547a05319ac6aa478e7cdea07b0d84fe8e285e28e5f574d4bdfb017ce` |
| REVIEW_FORWARD.md — unchanged | `aa1cfad03fadd8a575429a18c7dd968a9007a231e38f7ccf83766d94ef5ac27e` |
| test_review_forward.py — unchanged | `d45e00b8ceb5ea8870d681baa1a5323662272ae0a73bc046b5a9782dcb7f9e75` |
| REVIEW_TRANSFER_V2.md — unchanged | `7cec09372eebd12533d277a81a7e88380ca454cab085f6fa00a6f0a8624ce339` |
| test_review_transfer_v2.py — unchanged | `58dab421ead8a67762f73eb26603508ef23aff5217e678df86faf76f0e59fdb0` |

## Authorization boundary

This PASS disposes only the reviewed V3 transfer/accounting repair. It does
not retroactively approve earlier bytes or reopen unrelated earlier blockers.
Actual receiving evidence, controller/ledger integration, ownership/release
admission and Main's separate execution authority remain outside this verdict.
No remote control, GPU/model/provider operation, lease change, scientific claim,
or external publication is authorized or performed here.
