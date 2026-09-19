# Exact-byte sampling candidate review — 13:36 UTC

Reviewed freeze:
`e717180b6caf7777dad84126a5cd30c503a908dc32c9f3f6fdde0a3a42f31ad0`
(`replication/EXECUTABLE_SOURCE_FREEZE.json`, authored 13:34:35 UTC).

**Scientific execution wrapper: CPU review passes.** **55 tests pass**
(48 candidate tests plus seven independent tests), inputs unchanged during
verification. This supersedes the executable pins at 13:31 and 13:33 in
`STATUS.md`. It does not establish actual receiving custody or GPU admission.

## One reproduced accounting defect, not a model-execution failure

`report_sampling.py:60` raises `ValueError: completed_original_cell_budget`
when a `RESULT.json` exists with a legitimate original-contract incomplete
status. The independent fixture is `INCOMPLETE_ZERO_TOKEN_GENERATION` after
128/1,024 generated tokens, with the correct diagnostic epoch, scene and seed.
The original `contract.run_cell` can return this status and the unchanged
original player writes that result before completion validation rejects the
shortfall. Thus this is a real reachable failure case, not malformed input.

The report currently returns **no six-source/seed table at all** in that case.
Absent files are handled correctly, but a present incomplete file is not. This
violates the declared requirement to preserve all denominators and failures.

Recommended narrow correction: retain all six rows; mark the specific cell
incomplete with observed tokens, status, receipt hash and any partial evidence;
exclude it from completed-cell rates/totals and leave the full-budget result
unknown. A genuinely misbound epoch/scene/seed must remain a hard integrity
failure. Add a fixture for a present incomplete result, not just absent results.

This does **not** justify idling source staging or changing prompts, seeds,
scores, source adapters, custody, deadlines, or retry policy. Main may keep
preparing the same diagnostic while the reporting defect is repaired. Because
the reporter is in the executable source seal, a repair needs a reseal and a
small exact-byte delta review; do not silently mutate already staged bytes.

## Reviewed final files

| File | SHA-256 |
| --- | --- |
| `construct_candidate.py` | `623c463cfaa02b67ba264dc3118de4b520861ec327f6f9ec77563c4dfc7fd3af` |
| `execution.py` | `a9d5b99852a76c366fce6f03ee660e0486ebaa4d4020390a796e51b8d83b72bd` |
| `prepare_executable.py` | `02b0db31dace0d2bb23bd4c547e0e42cfc38d66ae49d35781d5676e9324358dd` |
| `sealed_runner.py` | `f8fd3519b69b81a1d6d0fa1e6d9ff8ebcd1fb188bb900a98d2650a30e9794243` |
| `dispatch_sampling.py` | `598c09058d939477d23013918c1c1c5a8f8c3b3f3761a1dcfacad906f0d8ed40` |
| `report_sampling.py` | `cebd13f63249fc4f8c51f8916628ada3e8d942508f05708ef93974d10ba8b772` |

Scientific candidate SHA-256:
`83a897cf8a5054364a65b55918d5fde321aa552e9f5ab85a1ed5ee176e2eb51f`.
Diagnostic epoch:
`4df129caf0a0377ba91feec83923bc972e00b10dab13b5b198594db567689d95`.
Preregistration SHA-256:
`afb4de49f040c589ec416f7901c02b945776593ecf8670d4505aa417a30c5c63`.

## Resolved concerns

- The loaded tokenizer, chat template, decoder, libraries, source/base weights,
  frozen state and optimizer absence are checked before generation; tokenizer,
  template, decoder and library mutation tests reject drift.
- Completion scene IDs are joined to the pinned original manifest; the
  independent wrong-scene mutation is rejected.
- Original-function player/judge behavior was independently exercised with
  fake backend/scorer dependencies, including exact model-facing requests,
  THINK/ACT extraction modes and unchanged textual feedback.
- Seeds 23301/23302 are a separate sampling diagnostic: 18 cells, 18,432 tokens
  across base/sleep51/sleep117. Private 64-caption panels, scoring/extraction,
  source tensors and decoder remain pinned. The preregistration retains
  checkpoint-selection and non-independent-lineage caveats.
- The original V4 shared claims, real GPU admission functions, protected
  device/handle checks and confined transient-unit route are used. Historical
  attempted jobs are not reused; platform denials remain terminal.

## Still not established by this review

Actual receiving staged-file/config/mount hashes, fresh host/device/lease proof,
successful in-namespace role custody records, and the joined `PROOFS_COMPLETE`
record must come from Main's original route. The freeze itself correctly states
`actual_receiving_proof: false` and `dispatch_performed: false`.

No new human-ratification gate is requested. No model/service call, launch,
signal, original-bundle modification, commit, or push occurred in this review.
All reviewer outputs are under `replication_review/`. `CPU_REVIEW_RECEIPT.json`
contains the exact pin set and accounting reproduction; older runs are retained.

Reviewer-harness note: an initial partial-report fixture had an invalid nested
mock and was repaired locally; the reproduced candidate error above is the
subsequent `ValueError`, not that harness exception. Its archived receipt is
retained for transparency.
