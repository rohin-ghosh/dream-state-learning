# Reduced-screen dispatcher integration

Builder, September 13, 2026 Pacific; final validation September 14 UTC.
Source-only composition; no native or science GO.

James owns the new screen_runtime.py and test. The single-state runner uses
the existing 280-slot roster, chain/probe drivers and public projections. It
joins supplied state identity, unchanged logical slots, physical invocations
and actor-list indices; captures original native objects and exceptions in
finally; and retains unused/not-reached reservations. It selects no checkpoint,
scores nothing, admits no D2 and defines no material/route/core semantics.
Caller callbacks and objects are trusted in-process collaborators. State
identity, input authority and crash-durable storage remain external duties;
an in-memory sink notification is not a durable or JSON-safe receipt.

## Preserved pre-review execution and rejection

Worker reported 63 focused tests PASS in 4.805s, including 21 dispatcher tests.
Main then ran the complete Stage2A suite on the initial frozen source:

`python3 -m unittest discover -s tests -p 'test_composition_birth_stage2a*.py'`

Observed **23:51:10.043233–23:56:07.446327 UTC**: **574 tests, 557 PASS,
17 native-only skips, 295.983s**; all **54 source/test hashes unchanged**.
The receipt uses `SOURCE_HASH_CHECK_EXIT=False` for zero mismatches (boolean
spelling), and `TEST_EXIT=0`. Its green test result is NOT review acceptance.

Turing's independent review found a static transport/accounting counterexample:
`Generation("STOP", 1, 2, False, "stop")` can produce a probe ERROR with no
screen Failure; later callbacks can execute and the screen can finish as
completed_unscored. The normal ReadoutActor constructs matching counts, but
the dispatcher explicitly accepts caller callbacks, so the exposed interface
must handle this. Review verdict **REWORK**, not PASS. No executed invalid
native result or new scientific observation is claimed by this counterexample.
James is repairing the driver-error classification with regression tests;
ordinary wrong-action/length outcomes must not become infrastructure failures.

Both initial files were hash-verified and archived before repair. Reconstruct
the pre-review tree from Git commit `8b71e109001b9abedf6bb067dadf20294c1caf30`
plus this two-file slice; do not overwrite the original archive or receipt.

| Pre-review artifact | SHA-256 |
|---|---|
| organism_v6/composition_birth_stage2a_screen_runtime.py | b48629183c5b3a4528621d7e2aa12b387a74612daeddd1e7916a4a3b84e261d9 |
| tests/test_composition_birth_stage2a_screen_runtime.py | bc500b061e3ae1251b2f5d7981f2b21526235e3176a91a3a90c03401291ad4c7 |
| research_notes/astra_memos/receipts_20260912/astra_stage2a_screen_runtime_integration_20260913T2351Z_attempt1.log | d5af5b903e6ae7fd0cfe62d67a8e3ed8e797f07eb5d97208d16a22a7ab8dc6ed |
| gpu_artifacts_local/stage2a_screen_runtime_prereview_20260913T2351Z_attempt1/source_slice.tar | 5d9ceb8a70d5fd8f7f807e8a7dfd546f7696b66819052523438c7116bee96707 |

No native model/tokenizer or GPU science was run here. The 17 skipped cases
have earlier separate CPU-native receipts; they were not run in this suite.
The source-binding questions and material/native opening remain unresolved.

## Repaired source accepted, September 14, 00:06 UTC

The historical REWORK above is closed on the new source below, not erased.
Driver transport/accounting faults now become slot-bound failures after
preserving native captures and driver records, then abort remaining dispatch.
A fallback transport check catches faults masked by malformed-action or
length terminal reasons. Valid wrong-action/length-limited outputs remain
ordinary outcomes. Regressions cover chains, interventions and canaries,
late-chain attribution, retained evidence and absence of subsequent calls.

Worker reported **67 focused PASS in 6.637s**, including 25 dispatcher tests.
Main's final integrated run used the same discovery command and observed
**2026-09-14 00:01:10.876427–00:06:10.661665 UTC** (September 13 Pacific):
**578 tests, 561 PASS, 17 native-only skips, 298.369s**, all **54 source/test
hashes unchanged**, TEST_EXIT=0 and SOURCE_HASH_CHECK_EXIT=0. This is separate
from the preserved 574-test pre-review receipt, not a reinterpretation of it.

Turing independently reread the exact repaired source/test, returned scoped
PASS and closed P2 with no additional findings. No duplicate tests or native
execution by that reviewer. No active test/worker/GPU experiment remains from
this slice. Source acceptance does not certify durable sink implementation,
authenticated model/state/material identities or native/scientific readiness.

| Accepted artifact | SHA-256 |
|---|---|
| organism_v6/composition_birth_stage2a_screen_runtime.py | 90d836e32bcd54bc09279ad3f731a0d67f74edfac69704693565995791ca8e55 |
| tests/test_composition_birth_stage2a_screen_runtime.py | b0e1553c212c5420b181aa6865c383c1f1e3a20c837551a72e74696c11e79489 |
| research_notes/astra_memos/receipts_20260912/astra_stage2a_screen_runtime_repaired_20260914T0001Z_attempt1.log | c9d7e9a00df980917c903d25b8f214188fd6a796320f815e4fa1d0c026bd89bc |

At the 00:06 UTC pull, no source-owner answer to the remaining registered-route
and core-depth/history questions was observed. Full semantic/route inventory
and separate material/tokenizer/runtime preparation remain pending. The
intended next run is still reduced BASE/D1 ATOM_LOCAL, 560 reserved slots in
total, then a qualified same-adapter authentic two-SLEEP junction. No completed
assay was repeated; the broader campaign remains incomplete. Formal C11 stays
deferred under the current simple-hygiene instruction.
