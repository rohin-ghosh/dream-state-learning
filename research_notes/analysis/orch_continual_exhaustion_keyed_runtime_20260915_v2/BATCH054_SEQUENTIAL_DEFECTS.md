# Batch054: two sequential validation defects, not competing diagnoses

Read-only native revalidation at 2026-09-15 07:09 UTC, zero provider calls.
The 07:01 journal's prefix-only characterization was incomplete.
No captured response, verdict, reservation or old receipt has been changed.

Confirmed again at 2026-09-15 07:15 UTC against the native source and result
file hashes below. All ordinals in this diagnostic are **zero-based**:
ordinal3 is the fourth returned review; ordinal4 is the fifth.
Inputs were reconstructed losslessly from the immutable numbered packet lines
using the predecessor's row shape; captured review JSON was not repaired.
An initial diagnostic invocation passed packet objects directly and hit
`KeyError: target`; this was a diagnostic input-shape error, not a provider or
batch defect. The correctly shaped offline invocation reproduced the results below.

Frozen validator source:
`/localhome/local-rohing/orch_continual_exhaustion_publish_20260915_segment1/source/gpu/orch_continual_exhaustion_publish.py`
SHA256 `4c7e53ea0ac06234be30dcee48c84f08cfe30f7fa0187e65a644d27eec3fc5e7`.

Frozen policy source:
`/localhome/local-rohing/orch_continual_exhaustion_publish_20260915_segment1/source/organism_v6/orch_continual_batch.py`
SHA256 `1c2349d27cb4ab7eacd4e9d62519aacf45579be764fd65b1bd030eaccdc038be`.

Native batch root:
`/localhome/local-rohing/orch_continual_exhaustion_publish_20260915_segment1/orch_continual_exhaustion_feed_batch_054`.
Paths below are relative to that root; no response bodies are reproduced.

| Binding | Group0 | Group1 |
|---|---|---|
| Result path | `PROVIDER_UPLOAD/batch_054_0/reader/result.json` | `PROVIDER_UPLOAD/batch_054_1/reader/result.json` |
| Result SHA256 | `e04848a07a5ab59c70110249d34bb5403957fad370db632505a546536d5afb8e` | `6ad77b48d4e65df7bad21cff12bd29d041ea4454f3db00c0885a1d1ca90df40b` |
| Packet SHA256 | `69f6da0d78fffdfddcf127bdffde39dcab91fbd57817f46be670316647bc4294` | `a8ff670c9d2d2707ca748f41a2c5fa8d44d34a2a5c933d410ed1521697d874c9` |
| Exact offline validator result | VALIDATION_PASS for six rows | `ValueError: branch_measurement_requires_literal_evidence` |

Group0 validation success is **not** a claim of six semantic PASS verdicts.

**First failure:** group1 response ordinal4 explicitly reports a positive
legacy branch indicator. Its `branching_alternative` is literal source text,
but `branch_rejection_reason` is not a literal substring of the target.
`resolve_line_reviews` therefore raises before returning the resolved group.

**Additional, later-stage defect:** group1 response ordinal3 has a mismatched
`student_prefix_sha256`. Its target and raw-call bindings match. That row's
legacy indicator is false, so empty legacy spans do not violate the old
positive-indicator condition. The prefix mismatch would be checked later by
`validate_review`, only after the entire group's line-resolution pass succeeds.
No repaired review was constructed or passed through that later stage.
The source order is `validate_reviews`: `resolve_line_reviews` first, then
`validate_review`. The latter checks prefix/raw bindings and would raise
`review_hash_mismatch` for the independently observed mismatch. That second
exception was not executed on a fabricated or repaired group.

All six group1 target hashes join the packet and all six raw-call hashes match.
Provider status was completed, no provider error,4626 output tokens; these are
local response-validation defects, **not HTTP failure**. Batch054 remains
failed/unadmitted, both calls remain charged, and no retry/salvage is allowed.

Prospective V2 addresses each failure independently: row-key identity binding;
host-bound literal legacy evidence from source-line IDs; and an independent
R106 departure/return inventory. An explicitly author-false legacy rejection
indicator can coexist with an author-positive valid-check departure/return.
V2 rejects unsupported positive legacy claims rather than flipping them false.
