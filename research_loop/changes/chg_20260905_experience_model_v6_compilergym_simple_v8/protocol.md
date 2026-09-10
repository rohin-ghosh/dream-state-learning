# Experience Model v6 — common-prefix CompilerGym pilot v8 amendments

Status: proposed ratification-candidate architecture bytes. The complete v8
protocol is the exact v7 protocol at SHA-256
`6ddec2537cabcd4228a1d3144988f3483ba1e86ecc6be85fe5c82301449836b1`
plus the amendments below. These clauses supersede only the conflicting v7
sentences they name. Every other v7 byte and scientific limitation remains
normative.

This revision responds to the two fresh v7 interpretations, their cross-
critique, and adjudicated consensus. It adds no arm, model capability, target,
training row, metric, claim, or GPU call.

## A1. Exact pre-run authority

Architecture ratification authorizes the two and only two `V6S8_T03` CPU/no-
model sealer invocations to enumerate candidate programs, cold-reset them, and
retain only URI, bitcode hash, Autophase reset bytes, I0, IOz, eligibility, and
first rejection reason in the environment evidence.

In the v7 sentence saying ratification does not authorize "target access",
target access means: any model-conditioned action on a selected target; any
target-cell execution; opening or using a target action/result receipt; or any
target information entering a model prompt, public life state, memory, writer,
training row, choice, or tuning decision. Those operations remain forbidden
until the later exact run-manifest ratification. The specifically enumerated
no-model T03 measurements are permitted and reveal no learned target result.

## A2. One-manifest failure scope

Every ordinary failure before final-panel entry terminates the entire manifest
as `RUN_INCOMPLETE`. An unaffected prefix/H/E branch may not continue. The sole
continuation exception remains an ordinary target-cell failure after panel
entry: seal that cell missing, run the remaining already-frozen cold cells, and
finish `PANEL_INCOMPLETE`. Any integrity-class failure terminates immediately,
has precedence over every other status, and suppresses all numeric values.

## A3. Literal descriptive interpretation only

Delete or supersede every v7 phrase saying this pilot can diagnose poisoning,
interference, sufficiency, harm as a mechanism, or absence of transferable
structure. The only permitted interpretation is literal:

* report the exact audited rational values and their signs/equality under this
  one frozen manifest;
* say whether mounting the one realized adapter changed any emitted action or
  fixed-panel score in this run;
* treat the choice of the next sleeper experiment as a documented heuristic,
  not an inference licensed by these four targets.

A negative value is evidence only that the corresponding score was lower in
this exact run. A positive value is evidence only that it was higher. Exact
zero is evidence only of equality on the registered score. No threshold,
"effect" category, cause, generic sufficiency, or null conclusion is registered.

## A4. T05 update-audit semantics

`V6S8_T05_POSTRUN_AUDIT` does not numerically replay floating-point training.
For each sleep it independently reconstructs row eligibility and deduplication,
exact token IDs/masks, `(row_hash,copy_index)` order, scheduled update indices
and total count, target-module inventory, optimizer/clipping configuration and
order, and required finite-value checks. It checks these against T04-frozen
per-update telemetry and verifies that the realized serialized adapter and
tensor-inventory hashes equal the atomic publication and every mount receipt.
This is discrete provenance plus realized-artifact verification, not bitwise
GPU reproducibility.

The minimal per-update telemetry schema and every non-model-visible audit/
receipt encoding are implementation artifacts. They must be frozen before T04,
hash-bound in the exact run manifest, sufficient for the recomputation above,
and immutable during the run. They are not new cognitive inputs or architecture
choices.

## A5. Independent fixture provenance

`V6S8_T01` and `V6S8_T02` expected fixtures must be authored before or
independently from the production path they test. Their receipt identifies the
fixture author/path/hash and proves the oracle does not import the production
serializer, reducer, parser, row selector, mask builder, or update planner.
Tokenizer goldens may call the pinned tokenizer through a separate fixture path
and then freeze literal token/mask arrays. T04 rejects fixtures produced by the
same helper under test or justified only by authorship metadata.

## A6. Acceptance-test namespace

Every v7 test and reference is replaced by the same suffix in the `V6S8`
namespace:

* `V6S8_T01_STATE_ACTION_GOLDENS`
* `V6S8_T02_SLEEP_SAMPLE_GOLDENS`
* `V6S8_T03_DOUBLE_SEAL`
* `V6S8_T04_PRE_GPU_REVIEW`
* `V6S8_T05_POSTRUN_AUDIT`

T05 is required before release of any status, raw cell, or numeric value; its
structured gate is `scientific_claim` only because that is the repository
schema's terminal release label. No scientific claim becomes permitted.
