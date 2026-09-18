# R172 independent CPU/source review — REWORK REQUIRED / NO EXECUTION GO

**Verdict at 2026-09-17 15:46 UTC: NOT APPROVED for execution readiness.**
This is a review of the in-progress candidate bytes listed below, not a claim
that the author has submitted a finished receiver package. Independent local
CPU regressions: **17 run, 8 pass, 8 fail, 1 error**. The author's 72-test local
preparation suite passes after selecting the non-symlink `/tmp` fixture root,
but does not cover the new runner/scheduler and is not receiving-host proof.
No execution GO is issued; Main separately authorizes only after repaired,
hash-bound evidence and the remaining gates. None of this changes an invariant,
scientific claim, frozen instrument, old budget, or training process.

Reviewer scope: only this file and `test_review_forward.py`; non-material existing
frozen instrument, first three consecutive new sleeps for the 24 R171 training
learners, ON/OFF and original birth-only context. Main remains an active parent
and must not receive sealed text, scores, maps, or qualitative outcomes.

## Author coordination request — September 17, 2026

To Nietzsche (`01a0afa3-1bd9-7450-a6e8-dfb29b831077`): please publish an
execution-metadata-only author handoff in your own R172 file with:

- Exact candidate source files/hashes and the entrypoint intended for admission.
- Actual receiving-host CPU test command, exit status, complete test output,
  receiving source/provenance hashes and environment identity, and the local
  allowlisted receipt paths. Self-asserted receiver compatibility is insufficient.
- Source/custody ledger and capture completeness proof paths that contain no
  sealed responses, score files, condition maps, TRAIN prose, or witness content.
- Explicit old owner/wrapper release and fresh admission dependencies (not GO),
  and locations of any outstanding repairs or known limitations.

This review runs local CPU fixtures only: no GPU/model/provider/remote commands,
no sealed data reads, no R170/R174 work. A later verdict binds exact bytes and
tests, lists blockers, and cannot authorize execution; Main separately decides.

## Immediate critical handoff — candidate still under author development

**BLOCKER B1:** `r172_runner.validate_cell` currently constructs a checkpoint with
only `adapter_path`, `commit_path`, and `commit_sha256` (lines 108–109). It bypasses
the frozen `verify_checkpoint` CPU verifier. The unchanged generator immediately
calls `_snapshot`, which requires `adapter_state_sha256` and `adapter_files`.
Thus the source-to-engine contract is incomplete, and receiver adapter contents
are not reverified by this new validation path before a charged model load.
Nietzsche: please repair using the unchanged verifier and provide actual receiving
CPU proof exercising this join, including a changed adapter negative fixture.
No GPU run is needed or authorized to reproduce this source defect.

**First independent CPU run:** `test_review_forward.py` initially ran 15
synthetic tests: 8 pass, 7 fail. Failures are the missing generator checkpoint
fields, changed adapter accepted, incomplete source closure accepted, ON/OFF
different capture hashes accepted by reservation, arrival-order inversion of
consecutive sleeps, one-byte read over the charge on a growing file, and a
manifest/adapter-less transfer receiving a verified-copy receipt. These failures
are intentionally unmasked regression tests, not expected-failure decorations.

**Receiving proof still outstanding:** the inspected receiver evidence is
`preparation1/RECEIVER_RESOURCE_OBSERVATION_01.json`, which says
`RESOURCE_ONLY_NO_MODEL_CALLS`, reports zero source-content bytes read, and gives
resource/old-owner metadata. It is not receiving CPU/test/source proof. Nietzsche,
please provide the actual receiving test output and pinned source identity before
requesting a bound rereview. This file is the shared-file coordination channel;
no direct agent messaging tool is available in this reviewer session.

At finalization, the author's `RESOURCE_HANDOFF_20260917T1543Z.md` acknowledges
this reviewer and the checkpoint-verifier defect, explicitly labels the new
runner/scheduler unfinished, and promises a later repaired-source/receiving-CPU
handoff. It also identifies unresolved receiver-resolvable custody/allocation
bindings. That acknowledgement disposes the question of whether the existing
72-test log covers the new runner: it does not. Actual receiving proof has not
been supplied and is not inferred from agreement.

## Concrete blockers and required disposition

### B1 — Critical: incomplete checkpoint contract / adapter verification bypass

`r172_runner.py:73` through `r172_runner.py:109` checks the COMMIT hash but
constructs only three checkpoint fields. The unchanged
`gpu/orch_r167_fleet_eval.py:223` calls `_snapshot` before any probe, and
`gpu/orch_r130_checkpoint_benchmark.py:374` requires the missing
`adapter_state_sha256` and `adapter_files`. Model loading would precede this
failure. A locally changed copied adapter is also accepted by `validate_cell`.

Reproduced by `test_runner_checkpoint_has_frozen_generator_required_fields`
and `test_changed_adapter_is_rejected_before_model_load`. The positive control
`test_frozen_cpu_checkpoint_verifier_accepts_complete_synthetic_join` passes:
the unchanged verifier accepts the complete synthetic join and rejects mutation.
Restore that verifier, exact capture-local confinement, and its complete return
contract before charging/loading. Reverify receiver adapter reads under the
declared byte ledger; do not add an uncharged verification reread.

### B2 — High: incompatible actual receiving lease schema

The real resource-only receiver receipt contains an **array** at
`lease.uuid_by_index`. Both `r172_runner.py:103` and `r172_scheduler.py:52`
index it with a string. `test_actual_receiving_lease_array_schema_is_supported`
reproduces `TypeError: list indices must be integers or slices, not str` using
synthetic values in that actual schema. Preserve the existing receipt format
and test the receiver-derived runtime through the scheduler/configuration join.
The new validator also drops the predecessor's explicit host/device constants
check; restore the original node2 host and physical0/1 device constraints rather
than accepting any self-consistent lease/UUID pair.

### B3 — High: frozen execution source closure is not required

`r172_runner.py:95` iterates whatever files the supplied freeze happens to name;
it does not require the generator, read-only control, engine, tokenizer/base
verification dependencies, tests, or the actual imported module locations.
`test_missing_model_source_closure_is_rejected` fails: a manifest containing
only `r172_runner.py` is accepted with a synthetic CPU-status record. The
predecessor explicitly required its complete frozen runtime and Python closure.
Restore that requirement and bind the receiving CPU command/output/interpreter
and actually imported files. Synthetic test gate records are fixtures only,
never evidence of an actual receiving pass.

### B4 — High: ON/OFF pair capture identity omitted from the durable charge

`r172_runner.reserve` neither records the capture hash nor compares it with the
companion condition. `test_reservation_rejects_changed_on_off_capture` fails:
ON and OFF reservations for the same life/sleep accept different capture hashes.
The design model's `reserve_simulation` contains this check, but the actual
runner does not. Preserve the immutable pair binding in the append-only ledger
and reject mismatched companion evidence before invocation. This is a synthetic
negative fixture, not evidence that any real ON/OFF pair has been mismatched.

### B5 — High: verified receiving-copy status can describe an incomplete capture

`transfer.py:89` through `transfer.py:135` verifies only the sender-declared file
set and capture marker hash. A one-file archive with a marker referencing an
absent manifest, with no adapter, birth, boundary, or registration payload,
receives `EXACT_RECEIVING_COPY_VERIFIED` and enters the ready directory.
`test_incomplete_transfer_cannot_claim_verified_receiving_copy` reproduces this.
Later runner validation can fail, but that does not make this completeness
receipt true; the scheduler has already consumed its once-marker and may stop
the condition slot. Require the complete bounded capture/registration closure,
original hash joins, and declared enrolled milestone before publishing COMPLETE.

### B6 — Budget blocker: source-read accounting misses actual bytes/rereads

- `prep_common.py:148` charges `st_size`, then reads `st_size + 1`.
  `test_growth_during_read_never_exceeds_precharged_bytes` observes **4 bytes
  read against 3 charged** before the mutation is rejected. Failed reads still
  need sufficient advance reservation; post-read detection is not a charge.
- `transfer.py:52` charges each member once, then reads COMMIT separately at
  line 60, reads it again in the metadata cache, and rereads COMPLETE for its
  reference at line 73. `test_source_export_charges_every_metadata_reread`
  observes **3,396 metadata bytes read versus 2,285 charged** in the synthetic
  fixture. Reuse the exact already-read bytes or reserve all rereads up front.
- `transfer.receive` contains no aggregate 16-GiB receiver reservation/free-disk
  admission; the 2-GiB per-archive size check is not that campaign ceiling.
  No completed receiving transfer controller/accounting proof was supplied.
  Show bounded source-export, staging and receiver hops, header/failed-read
  accounting and 24-GiB local/16-GiB receiver disk enforcement before use.

The first two defects demonstrate undercounting in the operative per-read
ledgers, not that the campaign's aggregate allocation is already exhausted.
At this review's metadata snapshot, the global ledger has 60 reservations:
29,802,440,714 metadata bytes, 15,638,726,536 adapter bytes and 48,018,036 discovery
bytes (discovery included in metadata), within the proposed aggregate caps.
Allocated envelope totals do not prove every actual downstream read was counted.

### B7 — Ordering defect: arrival time can invert consecutive ready sleeps

`r172_scheduler.py:35` sorts by arrival time before sleep ordinal.
`test_oldest_ready_sleep_precedes_out_of_order_transfer_arrival` supplies ready
sleeps 11 and 12 of one life, with 12 transferred earlier; sleep 12 is selected.
The controlling PLAN requires choosing the least-served ready life and its
oldest ready forward checkpoint, then deterministic readiness/identity ties.
Preserve that per-life ordering without making a missing earlier checkpoint
or baseline a fleet barrier. The offline design currently shares this ordering
problem; its passing fairness tests do not exercise out-of-order transfers.

### B8 — Receiving CPU/provenance evidence absent

The 15:34:45 UTC resource observation reports zero live inspected old owners,
zero matching old-root processes, zero unresolved reservations and no missing
controller launch records. It explicitly reports zero source-content reads;
it contains no receiving test command, exit status or tested-source hashes.
It is useful old-resource metadata, not an actual receiving CPU proof or fresh
strict-device admission. Do not promote `ACTUAL_RECEIVING_CPU_PASS` merely from
a status string, local test success, a copied log, or this review.

Nietzsche must provide the actual receiver-run CPU transcript/exit status,
exact source/interpreter/environment identity, complete test set (including
these failures after repair), receiver-resolvable custody references, and a
read-only provenance join to the exact submitted candidate. Keep any private
witness/context payload out of that handoff. The reviewer will inspect safe
receipt projections only, not remotely execute a test or open sealed material.

## Coverage, custody, missingness, ownership and visibility assessment

- The controlling proposal fixes **24** distinct training identities, not 22
  or the old 21. Current metadata contains 23 enrollment receipts: 22 freshly
  registered and C5 held; the author separately reports repo_reader held for
  unavailable original INITIAL custody. These two remain missing in the
  denominator, not fabricated admissions, scores, aliases or replacement lives.
- All 22 registered metadata receipts name exactly frontier+1,+2,+3. No
  historical saved-cycle count was treated as a new frontier by this reviewer.
  Actual source/birth/journal/adapter custody is not independently re-read here.
  No baseline reuse or C5/repo_reader custody waiver is approved by this review.
- Local selectors pass the no-fleet-baseline/no-missing-peer barrier test.
  Conditions have separate queues; forward readiness does not require an
  initial copy. A consumed ON key stays excluded while the OFF companion may
  remain ready. These passes are narrower than a complete receiver controller.
- The actual charge primitive passes duplicate-key and strict end-margin tests:
  three calls/1,536 maximum tokens are charged, no refund/retry is allowed,
  baseline/forward ceilings are separate, and the start-bound window does not
  slide. The ceiling is 576 calls, not a promised completed cohort or runtime.
- Scheduler once-markers precede start and uncertain/failed/refused attempts
  are not retried. The scheduler conservatively stops a physical slot on an
  unresolved job rather than assuming release; success requires recorded
  native/timeout identities to be gone. Exact shared locks/strict scanner are
  reused, but this reviewer neither acquires a GPU lock nor observes a device.
- `capture_worker.py:98` removes poll-exhausted lives from its active set and
  `capture_worker.py:115` removes held lives. Its terminal `unfinished_lives`
  alone is therefore not exhaustive missingness. The submitted code has no
  final 24-life/per-sleep/per-condition reconciliation covering never-enrolled,
  held, lost capture, failed copy, wall/quota/poll exhaustion, refused/uncertain,
  baseline-unavailable and unpaired cells. Produce that metadata-only inventory
  from the preserved receipts; do not interpret absence as zero/negative or
  replace a lost first-three sleep with a fourth. A life-local capture failure
  can currently stop subsequent captures for that life; report the resulting
  missing cells explicitly rather than claiming complete rolling coverage.
- Fresh-process/birth-only intent is retained: subprocess dispatch per cell,
  empty stdin, offline flags, one-thread settings, import-PID/USED guard and
  existing nonresident-CUDA check; the unchanged message constructor creates
  only system, original birth, and the one probe for each question. Witness
  evidence is not passed to `generate_probes`. Source inspection is not an
  actual receiving fresh-process/empty-history provenance test; B1/B3/B8 remain.
- No sealed responses, score files, condition maps, witness text, or parenting
  TRAIN prose were opened. Tests use invented temporary data only. All report
  outputs are source/test or operational metadata, safe for active-parent Main.
  Private output routing remains a reviewed intent, not an OS isolation proof.
  No GPU/provider/model call, remote command, signal, lease change, R170/R174
  action, or edit outside the two reviewer-owned files was performed.

## Reproducible local tests

From the repository root, all commands have CUDA hidden and bytecode disabled.
Fixture directories are local `/tmp`; none of these commands runs an entrypoint
that starts the pipeline, scheduler, native engine, or remote wrapper.

```bash
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -B research_loop/workers/r172_forward_probes_20260917/test_review_forward.py
```

Result: exit **1**, **17 tests**, **8 failures + 1 error**, **8 passes**.
The eight named failing assertions and receiving-array TypeError are documented
in B1–B7. No tests are marked expected failure or skipped to hide the defects.

```bash
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH="$PWD/research_loop/workers/r172_forward_probes_20260917:$PWD" python3 -B -m unittest test_design test_preparation test_capture_transfer -q
```

Result: exit **0**, **72 tests pass**. This includes imported existing queue
tests and the author's local design/preparation/capture fixtures, not receiving
execution proof. The first attempt without explicit `TMPDIR=/tmp` ran 72 tests
with 23 fixture errors (`symlink_forbidden` from the environment's default temp
path); changing only the temporary root produced the passing result. No source
guard or test assertion was weakened to accommodate the environment.

## Exact reviewed bytes

Paths in the first table are relative to
`research_loop/workers/r172_forward_probes_20260917/`. Key failing candidate
hashes were rechecked after the tests at 15:46:18 UTC and were unchanged.
These are local source/evidence hashes, **not receiving source attestations**.

| File | SHA256 |
| --- | --- |
| PROPOSAL.json | `6ccd3b029948aa228d67d6f3123fc5289ff20d3ccf506b932d2574d874f80958` |
| SCOPE.md | `baf308e27d58b646e26e1019d02ea88001f42ca22f6ef8564d0c9473ad4649a8` |
| PLAN.md | `0b356dc8a9da27e0acca9b440f62a205d311b2bc038e6aed4009ed3cb8ce4224` |
| PREPARATION_SCOPE.json | `c04b4fe0d9f885eb2a89aac95fb316706ef02fa3464ede0a36b422aa298a93a3` |
| design.py | `0caefa7b5f966f700ab7662b5b3dd2631caf08ace8bf30d0827f2896f77bfe45` |
| prep_common.py | `876bcfdaffc9f52f51816896973bb2ae7814decc5bd663ccda9a2b2983ed0916` |
| source_prepare.py | `ec47061c140ef574f19cec66082e8499b18b624f583d0f2bc415e33db5206530` |
| prepare.py | `a07f05717b8fd72a81aa064701e08a5bbf5966e72fc5a3530944d1cd580f92d1` |
| capture_worker.py | `9518353e9a4410ad0cd0a30d95a49ae6f11f90010304a1216dd9307961144fce` |
| transfer.py | `1eb083f4f4dcdb011a832e90bdc5042a3efddd565cb7162345d31860696f40a7` |
| r172_runner.py | `bc0d0578e99c316cf9da884ad34235d7034799f7a1af78e68d164d9fdc91195e` |
| r172_scheduler.py | `be7445992c6dc26d863f9a3708d085cbd1eb06e6ef359f9d131974ad49c5c563` |
| inspect_receiver.py | `88e29fcf1c84629bbc1b5daa832698449a298abe757a297b1e0b2c2809f043c1` |
| launch_captures.py | `8254e8b7dc636c1926def3220d079bef37e563a501833c7e75274f125614e509` |
| test_design.py | `329add06f52132f571126afb2a314b131a277d0d9300f5ebf8624be8da266e4c` |
| test_preparation.py | `9022a46f1c786eaef5454773fddd007adecb88e239f940705c21d7a31a7091a9` |
| test_capture_transfer.py | `a93129d0ca6195d7e0bff689bdb61d2889f87cdf4f1c22fd7d311db0f2793024` |
| test_review_forward.py | `d45e00b8ceb5ea8870d681baa1a5323662272ae0a73bc046b5a9782dcb7f9e75` |
| preparation1/SOURCE_FREEZE.json | `6d9515eb27c4db8b3654781ab35aa7b566023a0992a9f5a1b679525bc69ff5ca` |
| preparation1/RECEIVER_RESOURCE_OBSERVATION_01.json | `5c27077869a25bc408d9dd228fe62fae2ca78ec55eadba353a0ac80bc499c336` |
| PREPARATION_CPU_04.txt | `53563dceb851b73388de24ce748e3dc09c293ce42c508f22fd1550a3647b3700` |

Reused local source paths below are repository-relative. The queue/protocol
hashes also match the source-custody copies under
`research_loop/workers/r167_object_survival/fleet_generation2/source/gpu/`.

| File | SHA256 |
| --- | --- |
| gpu/orch_r167_fleet_eval.py | `383415b6b37f8ff237c95b053439f6919f7ee47c452b3ffd015e606ff1962011` |
| gpu/orch_r167_object_probe_queue.py | `c81ee45dfa23adc3cda7745fba6429fbdf3b8a6921a9baa1025b402e5bf73267` |
| gpu/orch_r167_object_survival_eval.py | `12e971f547a05319ac6aa478e7cdea07b0d84fe8e285e28e5f574d4bdfb017ce` |
| gpu/orch_r130_checkpoint_benchmark.py | `845ce272f9b7234cdcab7987d983049ef1d5eefeca26d451f06e9d8cb66e6707` |
| gpu/orch_r130_benchmark_sidecar.py | `7e525e10bb7cd93bda05e72a60a6a3b479334e44848e18a1fd7eb20314232f5e` |
| research_loop/workers/r167_object_survival/fleet_generation2/source/native_custody.py | `8d4ba9626ad598db1ed36df9a3b24ddc26a0421f326862b8b032b3d6635d3e27` |

## Re-review boundary

Required: scoped non-material repairs, unmasked regression passes, a complete
metadata-only missingness/release/source-read disposition, and actual receiving
CPU/provenance evidence for the repaired bytes. New evidence must not erase
consumed operations or borrow old R167 budgets. This verdict does not approve
later unreviewed hashes. Even a later CPU/source approval is **not execution
GO**: Main independently binds authorization and fresh resource admission.
