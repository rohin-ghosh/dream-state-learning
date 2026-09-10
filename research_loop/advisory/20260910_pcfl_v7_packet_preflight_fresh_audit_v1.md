# PCFL V7 deliberation-packet fresh preflight audit — v1

Date: 2026-09-10

Status: **BLOCK before approval of the configured V7 deliberation**. V7
materially closes the four V6 baseline-interface defects, but one inherited
`MemoryReturnV4` range conflicts with the V7 reader definition and one new RAG
null type remains undefined. This audit is not a ratification and grants no
source-authoring, preparation, implementation, execution, model, scientific,
GPU, resource, claim, release, or submission authority.

## 1. Exact packet and initialized state

The audit read the V7 directive, scope, workflow, hidden state, source plan,
integrated candidate, exact baseline-interface closure, and the inherited
V4/V5/V6 artifacts needed to evaluate context completeness, precedence, all
prior preflight blockers, baseline/resource/endpoint consistency, and the
runner boundary.

Current V7 control hashes are:

| Artifact | SHA-256 |
|---|---|
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v7/human_directive.txt` | `42208404f1e623b2c17091f74982009bb931f02078b20d7e60a9a7500e3e4e5f` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v7/scope_proposal.json` | `87d6c59aa3deb7250d797a2030799ef8e27e4c2b562ff3bd136616f27206b7e8` |
| `research_loop/workflows/pcfl_m0_mtext_bound_v7.deliberation.json` | `b5770e63039e63d73ae9669b5ee8690b3da1930e058094f17ce0bd6c9debe6a3` |
| `.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v7.deliberation.state.json` | `a1f8030bc2ad756966cfff2d64d41a323a2d2ecf983b214ea508514eb6a2de09` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v7/source_authoring_plan.json` | `2c4d51e833698e8d44c5b659c57e04d71c5c2601f8b5aada4355754f0bfcbfa1` |
| `research_loop/plans/pcfl_m0_mtext_exact_v7_source_authoring_candidate.md` | `ab1aee14de83c82ded3ff5c22cf763d5cb875ed47a20491dd33547aad953874b` |
| `research_loop/advisory/20260910_pcfl_v7_baseline_projection_exact_closure_v1.md` | `6ca612e41e3462ca6997cabcd089439a8d24be06ca7d37b5e29183ec362dd272` |

The initialized state contains exactly 38 source bindings: the V7 directive
plus all 37 workflow context files. Every binding rehashes exactly. The state
is pre-run: `phase="advocate_pending"`, all five attempt counts are zero,
`artifacts={}`, `human_required=true`, and `implementation_authorized=false`.

## 2. Prior-blocker disposition

The V4-chain context omission found in V5 remains closed. The V7 workflow
directly includes V4 `human_directive.txt` and the full preserved V4 role/state
chain. It also includes the zero-attempt V5 and V6 directives, scopes,
workflows, source plans, hidden states, candidates, and fresh preflight audits.

V7 materially closes all four V6 baseline defects:

1. Public `mode` and `read_protocol` now flow through a typed
   `MEMORY_INTERFACE_PROJECTOR` into the controller and model turn, with closed
   BLOCKED and PASSIVE_NULL reader edges.
2. `BLOCKED_READER` and `PASSIVE_NULL_READER` are separate modes and protocols
   with separate `BLOCKED` and `NOT_FOUND` return behavior.
3. TARGET_ONLY P/D reads execute open-loop against BLOCKED, preserving its 24
   registered READ opportunities without feeding results into its completed
   one-shot call.
4. RAG now binds document handles and scoring bytes, query fields and bytes,
   tokenization/multiplicity, Decimal BM25 equations and quantization, rank/tie
   ordering, four return slots, and domain-separated fingerprints.

Those repairs expose the two remaining exact defects below.

## 3. Exact blockers

### BLOCK-V7-PREFLIGHT-001 — `MemoryReturnV4.repeat_count` has two incompatible ranges

The inherited exact `MemoryReturnV4` schema declares:

```text
repeat_count: 1 | 2 | 3
```

at
`research_loop/plans/pcfl_m0_mtext_exact_v4_rework_candidate.md:197-216`.

V7 states that `BLOCKED_READER` and `PASSIVE_NULL_READER` return
`MemoryReturnV4`, including its public repeat count, but then declares for both
readers:

```text
repeat_count is 1..8; an out-of-range/malformed request is a registered
structural error
```

at
`research_loop/advisory/20260910_pcfl_v7_baseline_projection_exact_closure_v1.md:55-89`.

This is not resolved by precedence. The V7 advisory says it replaces only V6
baseline-repair sections 1, 2, 3, and 5, while the V7 candidate says all other
V6/V5/V4 clauses remain exact and any conflict outside the named precedence
requires `REWORK`
(`research_loop/plans/pcfl_m0_mtext_exact_v7_source_authoring_candidate.md:19-36`).
The range changes accepted requests, fixed return bytes, fingerprints,
padding/size maxima, rejection behavior, mutation fixtures, and potentially
resource counts.

Smallest repair: preserve the initialized V7 state and fork newly bound bytes
that do one of the following explicitly:

- retain `MemoryReturnV4.repeat_count=1|2|3` and define the behavior of a fourth
  identical anchor/cursor request within the eight total READ opportunities; or
- amend the inherited `MemoryReturnV4` range to `1..8` under an explicit
  precedence clause and update every affected schema, fingerprint, fixed-size
  derivation, golden, rejection test, and common/blocked/passive reader rule.

Do not let source authors choose between these interpretations.

### BLOCK-V7-PREFLIGHT-002 — `NULL_RAG_DOCUMENT` is used but never defined

The new closed return schema declares:

```text
RagSlotPublicV4 := {
  rank:0|1|2|3,
  document:RagDocumentPublicV4|NULL_RAG_DOCUMENT,
  score_e12:u64|0,
  pad:string
}
```

at
`research_loop/advisory/20260910_pcfl_v7_baseline_projection_exact_closure_v1.md:207-227`.
The following prose requires four null slots for empty/BLOCKED returns and
typed null padding when fewer than four documents exist, but neither V7 nor any
inherited artifact defines `NULL_RAG_DOCUMENT` as JSON `null`, a literal enum,
or a closed padded record. Repository search finds no other definition.

That choice is model-visible and resource-relevant: it changes canonical JSON,
fixed slot/return bytes, padding, request tokens, return-token counts, hashes,
goldens, and leakage/mutation expectations. Saying that all records are closed
does not supply the missing type.

Smallest repair: in a preserved-state successor, define
`NULL_RAG_DOCUMENT` exactly—preferably as a literal JSON value or a complete
closed field/type schema—state its canonical bytes and padding interaction, and
bind positive/reject goldens for empty, fewer-than-four, and BLOCKED returns.

## 4. Checks that otherwise pass

- All 38 initialized source bindings rehash to the exact recorded values. The
  V7 workflow and all context bytes are stable relative to initialization.
- The V7 workflow includes complete preserved V4, V5, and V6 contexts needed by
  its directive, including both predecessor preflight audits and zero-attempt
  hidden states.
- The V7 candidate's V6-candidate, V6-preflight, and V7-closure hashes match the
  current bytes; its precedence preserves earlier normative layers rather than
  editing them in place.
- The source-authoring plan contains exactly 24 unique, ASCII/NFC, bytewise-
  sorted, repository-relative literal paths: 23 rows with
  `manifest_member=true` and one `normative_source_manifest.json` output row
  with `role="NORMATIVE_SOURCE_MANIFEST"` and `manifest_member=false`.
- Plan roles, media types, positive byte maxima, V7 change ID, and manifest
  membership satisfy the inherited `SourceAuthoringPlanV1` vocabulary. No row
  is an absolute path, `..` escape, glob, directory, unresolved variable, or
  symlink.
- The seven-mode condition/phase table covers every applicable phase of all 18
  conditions exactly once and emits no handoff for structurally absent phases.
- COMMON, BLOCKED, PASSIVE_NULL, RAW_STATIC, RAG_DETERMINISTIC,
  NATIVE_GRAPH_STATIC, and NO_MEMORY modes have distinct legal payload/protocol
  combinations. The public tags reveal only the actual interface, not root,
  hidden bit, private condition, split, transform, answer, score, or oracle.
- The consumer graph now has explicit field-level mode/protocol routing,
  distinct BLOCKED/PASSIVE nodes, typed static projection, and typed RAG
  retrieval. Private handoff, scorer/oracle, carrier-to-RAG, scratch-to-query,
  and direct corpus-to-renderer edges remain forbidden.
- TARGET_ONLY keeps four model calls, 24 P/D READ opportunities, fixed BLOCKED
  no-memory execution, and no model feedback. Every applicable U phase has no
  READ opportunity.
- RAW and native graph remain unequal-resource static baselines with zero READ
  opportunities. RAG retains eight pre-action retrieval opportunities per
  applicable path phase and closes after the first relation attempt, including
  `NO_EFFECT`.
- RAG handle construction (`d00..dff`), JCS scoring bytes without inert pad,
  ASCII tokenization, ordered query serialization, duplicate query terms,
  50-digit Decimal BM25, HALF_EVEN `score_e12`, descending score/ascending
  handle rank, open/BLOCKED fingerprints, and empty/short corpus rules are
  deterministic apart from the undefined null sentinel.
- Baseline endpoint applicability remains coherent: RAW/RAG/NATIVE use
  substrate-neutral path/delayed behavioral endpoints, cannot populate common-
  reader mechanism endpoints, and do not support equal-resource or scalar-
  efficiency claims.
- Delayed baseline memory derives only from the model-independent supplied D
  fixture. No U model output, session, cache, scratch, retrieval state, or
  acquisition transcript survives reset.
- Resource rules continue to charge static context, RAG corpus/index build,
  every reader invocation, postings/documents examined, returned bytes/tokens,
  CPU time, model inputs, artifacts, and shared CAS work. No hidden or warm
  resource becomes free.
- The 18-condition arithmetic remains exactly 501 slots/root, 148,224
  generated-token allowance/root, and 4,104,192 maximum input-token
  allowance/root. V7 adds no condition, call, token, root, endpoint, gate, or
  claim.
- Test 19 now targets the seven-mode table, all typed edges/returns, TARGET_ONLY
  behavior, RAG arithmetic/wire bytes, reset, leakage, and resource charging,
  with independent goldens and mutations. Tests 20..22 remain unused.
- Requested and forbidden scopes are sorted, unique, disjoint, and restrict the
  present workflow to nonauthorizing architecture deliberation.

These passing checks do not compensate for either blocker.

## 5. Deliberation-only runner boundary

The configured V7 runner remains within deliberation-only authority:

- it contains exactly advocate, systems, benchmark, critique, and consensus;
- systems and benchmark receive independent fresh contexts;
- every Codex role is invoked with `allow_write=false` in the read-only role
  sandbox;
- runner writes are limited to bound prompts, response-schema/log/result
  records, the five canonical architecture artifacts, and deliberation/intake
  state;
- the runner has no ratification transition and must stop at
  `human_required` with `implementation_authorized=false`; and
- it does not execute planned source, preparation, materialization, checkers,
  benchmarks, a scientific model/tokenizer workload, or GPU work.

Therefore the configured run is authority-safe, but approval is blocked
because the exact bytes still leave source authors to choose a repeat-count
contract and a RAG null-document representation.

## 6. Audit execution statement

No deliberation role, PCFL source, fixture, root, data, checker, materializer,
benchmark, model, tokenizer, scientific workflow, GPU job, resource
acquisition, claim, release, or submission was executed or authorized during
this audit. No file other than this advisory was created or edited.
