# Native projection compatibility diagnosis — 2026-09-15 01:20UTC

Question: did the new native encoding seam discard otherwise admitted child
turns and thereby cause SHORT's three zero-update cycles?

**No such failure is recorded.** Readonly inspection of the existing A100
root `/tmp/orch_l2_shared_20260914_attempt1` finds no projection errors in
SHORT C1–C3, UNPARENTED C1 or LONG C1. Recomputed initial eligibility from
every corresponding original episode/capture matches the saved gates. The
number admitted before native projection equals the number retained after it.
No code change or duplicate GPU test is indicated by this diagnosis.

| Lane/cycle | Captured turns | Eligible for semantic review | PASS | UNRESOLVED | Semantic FAIL | After projection |
|---|---:|---:|---:|---:|---:|---:|
| SHORT C1 |48|0|0|0|0|0|
| SHORT C2 |54|5|0|5|0|0|
| SHORT C3 |52|1|0|0|1|0|
| UNPARENTED C1 |75|5|1|4|0|1|
| LONG C1 |78|7|2|4|1|2|

In SHORT,148/154turns fail one or more necessary conditions upstream. The
remaining six are five unresolved and one semantic failure. Thus zero
admission is not evidence that154turns received and failed semantic review.
Nonexclusive necessary-condition counts are in the JSON; do not sum them
or infer the effect of changing a threshold from their marginal frequencies.

SHORT C2's existing review responses explain the five unresolved candidates:

- `SHORT/cycle2/experience/REVIEW_10.json`: empty reviews, JSONDecodeError
  `Expecting value: line 1 column 1 (char 0)`; SHA256
  `d4d56ebca2a25f88fc06007c77cedfd34d93af9de1e187a261f958bbf92c08da`.
- `SHORT/cycle2/experience/REVIEW_12.json`: empty reviews, ValueError
  `evaluator_failed_no_fallback:1`; SHA256
  `668ed163a161b1baa016a40615513e502ed3ee4bd6d4d7903b7964289c913bbe`.

These are unresolved transport/provider failures, not unfavorable content
judgments. The current parent worker already imports the strict envelope
helper; no second parser or retroactive regrading is proposed. The precise
provider-failure causes were not diagnosed here, and five candidates cannot
be assumed admissible. Preserve original zero-update/null outcomes and costs.

Evidence: `orch_guided_native_20260915_projection_diagnostic1.json` contains
exact COMPLETE/EPISODE hashes, recomputed predicate checks and counts. This
is an author-side seam diagnosis, not an independent semantic review or a
new scientific result. Additional model calls/fits/resources: zero.
Recommendation to Main: keep the working native seam unchanged; distinguish
upstream task/token/format failures, unresolved reviewer calls and actual
semantic rejection in the campaign analysis. Future transport repairs belong
to the existing parent-worker owner, not another framework in this module.
