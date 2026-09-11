# Multi-key writer gateway V6 — terminal proposal repair

Status: proposal only. No implementation or execution authority.

V6 inherits the complete V4 scientific protocol at `research_loop/changes/chg_20260911_multikey_writer_gateway_v4/exact_scope.md`, SHA-256 `f6beb7d23439ecc0d08152d3e63b8360db72b4fe3748e14ed36ad9ed3d81b2b4`, plus the four V5 systems repairs at `research_loop/changes/chg_20260911_multikey_writer_gateway_v5/exact_scope.md`, SHA-256 `f72d820ad349263671b5f6a23d75203790f3bbf779bbac801c780670dc2e0ee7`.

It makes exactly three terminal contract repairs:

1. `MWG6_T04`, `MWG6_T05`, `MWG6_T06`, and `MWG6_T08` have `required_before: model_execution`. All T01–T07 receipts, the immutable execution manifest, T08 passes, and separate exact human execution ratification must exist before any model-facing invocation on any device, including CPU.
2. Everywhere V5 said “two fresh independent reviewers,” V6 requires one fresh independent implementation reviewer and one separate author-side scientific advocate over identical immutable implementation, manifest, and T01–T07 bytes. Both must PASS; the advocate cannot override an independent rejection. Additional reviewers are additive only.
3. The four-commit barrier emits one immutable canonical receipt containing, in fixed order, the four exact `(root, condition, adapter_id, COMMITTED, adapter_sha256)` bindings. `trusted_evaluation_selector` may read only this receipt as derived adapter-stage information, verifies that each non-`OFF` selected call maps to its exact receipt identity/hash, and copies that pair byte-exactly into `selected_execution_call`; `OFF` has no adapter. Missing, duplicate, stale, unexpected, mismatched, or non-committed entries fail closed. The selector receives no adapter contents or capability.

Tests T01, T02, and T07 add exact receipt construction, order, equality, stale/duplicate/missing/unexpected/mismatch, alias, and non-committed fixtures. Every other V4/V5 test, model/data/dose/rank/workload parameter, estimator, threshold, lifecycle state, source rule, visibility denial, claim, exclusion, and authority boundary remains unchanged.

Exact ratification of a later PASS consensus may authorize only bounded source implementation and deterministic CPU/fault tests in the same four paths named by V5. This proposal does not authorize those writes and never authorizes model/tokenizer execution, benchmark/source generation, training, LoRA/adapter/checkpoint work, GPU use, parenting, resource acquisition, C11 work, scientific execution or claims, release, or submission.
