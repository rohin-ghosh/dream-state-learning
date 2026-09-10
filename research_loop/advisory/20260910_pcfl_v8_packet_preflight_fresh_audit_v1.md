# PCFL V8 packet preflight — fresh audit v1

Date: 2026-09-10

Status: **BLOCK before any configured deliberation call**. This was a fresh,
read-only packet audit. It authorizes no source authoring/import/checking,
implementation, preparation, materialization, fixture/root/data generation,
model/tokenizer/benchmark execution, training, LoRA/adapter/checkpoint work,
parenting, GPU use, resource acquisition, scientific claim, release, or
submission.

## Verdict

The initialized V8 packet has exactly two blocking defects. The repeat-count
and literal-null repairs themselves pass, but the five-role deliberation must
not start until the missing predecessor authority source and invalid source-plan
row are repaired and a new zero-attempt state binds the repaired bytes.

## BLOCK 1 — the V7 human directive is absent from V8 context and bindings

`research_loop/workflows/pcfl_m0_mtext_bound_v8.deliberation.json:41-47`
binds the V7 closure, candidate, source plan, scope, workflow, initialized
state, and fresh negative preflight, but omits:

```text
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v7/human_directive.txt
```

That omitted predecessor authority source exists at SHA-256
`42208404f1e623b2c17091f74982009bb931f02078b20d7e60a9a7500e3e4e5f`.
Its lines 28-60 contain the V7 successor task, required checks, stop condition,
and no-execution boundary. A nested path/hash reference in the bound V7
workflow/state is not the directive's content and does not make it a V8 role
context. Therefore the current 44-context workflow and 45-source-binding state
are authority-incomplete.

Smallest repair: add that exact V7 directive path to `context_files` adjacent
to the V7 packet, recompute the workflow hash, and initialize a fresh state
whose source bindings contain the current V8 directive plus all 45 contexts.
The repaired state should therefore have 46 source bindings and remain at zero
attempts/artifacts.

## BLOCK 2 — the V8 boundary plan row violates the inherited closed role enum

`research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v8/source_authoring_plan.json:167-171`
uses:

```text
logical_path = .../source/v8_boundary_v4.json
role         = V8_BOUNDARY
```

The controlling closed `SourcePlanRow` schema in
`research_loop/advisory/20260910_pcfl_v5_authority_handoff_delayed_v7_source_repair_v1.md:123-142`
permits `V7_BOUNDARY`, not `V8_BOUNDARY`. No V6, V7, or V8 precedence clause
widens that enum. The row also contradicts
`research_loop/plans/pcfl_m0_mtext_exact_v8_source_authoring_candidate.md:87-91`,
which says V8 keeps V7's validated roles and filenames under the V8-scoped
directory.

Smallest repair: restore the final row to the V8-directory path
`source/v7_boundary_v4.json` with role `V7_BOUNDARY`; recompute the exact plan
SHA-256 in `human_directive.txt:37-38`; then reinitialize the repaired workflow
so the plan, directive, workflow, and source-binding hashes are exact. Do not
expand the authority enum merely to accommodate the erroneous row.

## Otherwise-PASS checks

- Current workflow SHA-256:
  `cddddd008d5852669f7427d8df230cbb34ea918cf33d4797f3ef6c79a712a2cc`.
- Current initialized state SHA-256:
  `d67651b3e03751f186034078dbb2bcbeea5c59d50d537324302e17e8d2b0c972`.
- The current state has exactly 45 unique source bindings: the V8 directive
  plus 44 unique workflow contexts. Every one of those 45 recorded SHA-256
  values matches the current file bytes. Every context is below the configured
  300,000-character per-file ceiling; the largest is 42,111 bytes.
- State is structurally pristine: `attempts=[]`, all five role attempt counts
  are zero, `artifacts={}`, phase is `advocate_pending`, `human_required=true`,
  and `implementation_authorized=false`
  (`.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v8.deliberation.state.json:2-17`).
- The source plan has exactly 24 unique ASCII/NFC literal, repo-relative rows,
  sorted bytewise, with exactly 23 `manifest_member=true` rows and one matching
  nonauthoritative manifest output row. Schema version, artifact type,
  V8 change ID, media types, maxima, and all roles other than the single
  `V8_BOUNDARY` defect are consistent with the inherited plan schema.
- The V8 repeat precedence closes every inherited `1..8` conflict without
  changing the eight legal READ opportunities: every public memory-return
  field remains `1|2|3`; the visible sequence for eight identical legal reads
  is `[1,2,3,3,3,3,3,3]`; anchor/cursor and RAG request identities are exact;
  counters are identity-local and reset at phase and condition/root boundaries;
  malformed requests reject before increment; and only the saturated value
  enters returns, fingerprints, padding, tokenization, charges, or other
  model-visible bytes
  (`research_loop/advisory/20260910_pcfl_v8_repeat_null_exact_closure_v1.md:20-55`).
- `NULL_RAG_DOCUMENT` is closed as the JSON literal `null`.
  `RagSlotPublicV4.document` is exactly `RagDocumentPublicV4|null`; all four
  slot ordinals/ranks, null score zero, real-before-null order, NOT_FOUND and
  BLOCKED four-null returns, FOUND one-through-four-real returns, fixed padding,
  exact JCS/padded goldens, and rejecting mutations are specified
  (`research_loop/advisory/20260910_pcfl_v8_repeat_null_exact_closure_v1.md:57-89`).
- The configured roles are exactly advocate, systems, benchmark, critique, and
  consensus. The runner supplies bound read-only contexts with
  `allow_write=false`, tells roles not to edit or launch jobs, and terminates at
  `human_required` with `implementation_authorized=false`
  (`research_loop/architecture_deliberation.py:538-592,636-661,872-919`). The
  directive and scope permit only those five non-scientific deliberation calls
  and forbid source checking/execution, science, GPU work, external actions,
  claims, and inferred ratification.

## No-execution boundary

No configured role was called during this audit. No source was authored,
imported, interpreted, syntax-checked, executed, prepared, or materialized; no
fixture, root, or data was generated; and no model, tokenizer, benchmark,
science, training, parenting, or GPU operation was run.
