# R179 append-only phase-cap repair — bounded integration PASS

**PASS for the exact repaired first C2 sleep33 ON/OFF tranche, six calls only.**
**R179-I1 is closed on these new config bytes. No remaining review issue was
identified within this bounded integration scope. This is not GPU GO.**

Bound at **September 17, 2026, 17:56:57 UTC / 10:56:57 PDT**; independently
observed receiving bytes at **17:52:58 UTC**. The original
`REVIEW_INTEGRATION_R179.md` and its REWORK for the old 24 MiB configs remain
unchanged. This addendum does not approve the superseded configs, C5, later
checkpoints, a new baseline, or a change to R179 living-context work. No C5 or
R179-completion wait is introduced.

## What closes the issue

The append-only candidate is `runner_candidate3_metadata_repair2`. Direct
comparison on the receiving node confirms that only
`allowances.preflight.metadata` and `allowances.native.metadata` change in each
config. Each new authority is separately, immutably reserved: **32 MiB
preflight / 48 MiB native**. Replacing those two fields in memory with their old
values restores the exact original config object. The original runner/helper,
source/CPU/interpreter/service/lease bindings, capture, adapter passes,
model-load allowance, checkpoint, condition assignments and fixed six-call
scope are otherwise unchanged. No private condition assignment is disclosed.

The author completed four **actual receiving `validate` + real `Reader.charge`
+ persisted-write proofs**, one per config/phase. Independently checked on the
receiver: all four proof receipts and requests match their local hashes; all
**1,309 sequential read records per proof** exist; every record joins its
separate proof authority; and their sums equal the reported counters:

| Phase | Actual validator metadata per proof | Exact production metadata cap | Remaining after validation |
| --- | ---: | ---: | ---: |
| Preflight, each config | 25,618,085 | 33,554,432 | 7,936,347 |
| Native, each config | 25,618,085 | 50,331,648 | 24,713,563 |

Each proof also charged **80,798,775 adapter bytes** against a distinct
supplemental CPU-proof allowance. The production verification allowance remains
134,217,728 bytes. Proof metadata caps equal the actual production phase caps;
proof adapter caps are smaller, not relaxed. All four proofs returned
`COMPLETE_ACTUAL_VALIDATOR_PASS`. The formerly failing interpreter read now fits
and the validator continues through checkpoint/context/rubric verification.

The proofs used explicit in-memory authorization fixtures, not issued GO or
review approvals. They prohibited model-library imports and execution/admission
entrypoints; no model/provider/scanner call or production attempt occurred.
Their actual read/write accounting was **not mocked**. Separate pre-I/O proof
reservations paid for these proofs; production phases were not consumed.

## Independent additional coverage

`review_r179_phasecap1/test_phasecap_review.py` adds six nonoverlapping CPU tests:
actual candidate/request equality; all four actual proof-request/receipt and
ledger joins; preservation of **34 original, superseded and proof authority
files**; global/per-life/nominal-pass caps; native callback pressure; and
continued refusal under the old cap.

The callback test extracts the unchanged `native_run` check function's AST and
uses the real `Reader` and `charge_open_reads` hook with wholly synthetic local
files. It seeds the observed validator cost, additionally charges **one entire
17,011,448-byte source pass**, and performs **1,546 checks**: three call checks,
three generation checks, 3 x 512 forward checks, three base-hash checks and a
completion check. Every check rereads/hashes a synthetic config sized to the
larger actual repaired config (**4,899 bytes**). Total metadata charged is
**50,203,387 / 50,331,648 bytes**, leaving **128,261 bytes** even with that extra
whole-source charge. The old cap still refuses before a callback runs.

This is a CPU read-accounting stress test, not a model-load/inference test or a
claim about all native-library/mmap traffic. It exercises the remaining config
rechecks with the unchanged callback and hard cap; the previous model-load
accounting boundary and fixed native loading path are not weakened.

The combined suite passes **55 tests**: 36 original author tests, five original
independent regressions, eight supplemental-proof reservation tests and six new
independent tests. `CPU_REVIEW_01.txt` preserves a reviewer-only arithmetic error
in the stress-test expected total; the corrected assertion and final passing
run are in `CPU_REVIEW_02.txt`. No runtime or author source was changed by this
reviewer.

## Budget and evidence preservation

All original authorities, failed/superseded repair authorities and the original
REWORK evidence remain byte-for-byte intact. The four supplemental adapter
proofs total **323,195,100 bytes** and retain all twelve nominal checkpoint-pass
envelopes. No refund, reset or R172 borrowing was found. At binding time the
global reserved metadata was **1,035,075,584 / 2,147,483,648 bytes**, with C2
metadata **953,286,656 / 1,073,741,824 bytes**; adapter, per-life and storage
ceilings also passed. These are observation-time budget totals, not a freeze on
other already-authorized disjoint preparations.

The independent receiving check rehashed the unchanged 1,285-file source
closure and runner/helper closure, interpreter and service; compared original
and repaired configs without exporting their contents; and verified the four
persisted proof ledgers. It read **28,462,957 metadata/source bytes across
6,546 files**, within a 64 MiB reviewer safety bound. It performed **no new
adapter read**, no receiving write, no signal, no scanner invocation and no
model/GPU/provider call. No production attempt or reservation existed at that
observation. The fixed custody/instrument/transport/admission analysis in the
original review remains applicable to the unchanged bytes.

## Exact public pins and handoff

Complete local/receiving/evidence pins are in
`review_r179_phasecap1/PUBLIC_BINDINGS.json`, SHA256
`8ad00fe62aca843bf58c265b18436eb8ebf8dbbbca233812a59906034a30706c`.

| Binding | SHA256 |
| --- | --- |
| Repaired safe candidate receipt | `ed43eeca656d826c600bdc112ae1da7cbb8e28630bb79881edef0a8b190ee14c` |
| Repaired local/receiving request | `dee5e18ed38cb12551a4456f4084859709edcff8af7f853f0bbacf1d720a3e7f` |
| Opaque repaired execution config | `6d4f77f44546739b06691f5cd869d25872be1a1086fd2d1cf7c8eb6350c756d8` |
| Opaque repaired execution config | `83d09ddf7ff9adababd87d0d4ef12a54617aa413522fd5948aff4f5b5d590bf5` |
| Unchanged local/receiving runner | `4ff1c97b374930b2b6e4c96d2f8d24fbedcdccfaae8c07471edd52720d7a6952` |
| Unchanged helper | `1fcb8f90a1f98ad38389af87b1527c11c018da65369588ec720005fa24229681` |
| Unchanged receiving source request | `b34fd19b891f5639456abaa0ad112727b643869350b5e5aafd10c3dd0203ed9d` |
| Actual four-phase proof script | `2a0285b765a5162379b2990ca037f8425c220175f9e92f72697f1ad9b29bf4ad` |
| Final 55-test log | `a2fe5b76b8a5461f9f1c60587e23152858161665d825f7c5861817e0ffdedaab` |

`REVIEW_R179_PHASE_CAP1_APPROVAL.json` is the local machine-readable independent
review record, using `status: APPROVE` for the unchanged runner's review schema
and `verdict: PASS`. It binds exactly the two repaired execution references,
source, runner, original CPU gates and new public evidence. It is **not** a
`MAIN_R176_EXECUTION_GO`, has `execution_authorized: false`, and was not staged
on the receiver by this reviewer. Main can bind those exact bytes when preparing
its separate no-reset GO; fresh strict admission remains required by the
existing scope. This introduces no additional gate and grants no GPU GO.

No responses, labels, scores, witness/rubric contents, condition maps or
qualitative retention outcomes are disclosed. Only reviewer-owned output files
and temporary synthetic local fixtures were written.
