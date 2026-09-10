# PCFL M0 + M-TEXT-SUPPLIED V11 — integration successor candidate v4

Date: 2026-09-10

Status: **proposal-only, precedence-closed candidate for future five-role
architecture deliberation; not source-authoring authority**. This file does
not edit or run a workflow/state; author, import, compile, review, or execute
source; prepare or materialize data; generate fixtures/roots/data; run a
checker/test/model/tokenizer/benchmark/training/GPU job; parent an agent;
acquire resources; or make/release/submit a scientific claim.

## 0. Exact identity and self-hash rule

```text
C11 = "chg_20260910_pcfl_m0_mtext_bound_v11"
CANDIDATE_V4_PATH_C11 =
  "research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate_v4.md"
WORKFLOW_PATH_C11 =
  "research_loop/workflows/pcfl_m0_mtext_bound_v11.deliberation.json"
DIRECTIVE_PATH_C11 =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/human_directive.txt"
```

`CANDIDATE_V4_SHA256_C11` is the sole lowercase SHA-256 independently
computed after these bytes are sealed. It is not stored in this file. A
future workflow names this exact path; runner-generated state binds the actual
digest; later consensus/state/grant/provenance uses must equal that digest.
A placeholder, guessed value, path-only binding, or author-selected digest
rejects.

## 1. Exact predecessor stack and precedence

This candidate binds:

| role | path | SHA-256 |
|---|---|---|
| integration candidate v3, predecessor only | `research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate_v3.md` | `76754fbdd3d8bba5f26924e2cc0125f0ae8f803d9559285be84275687652218a` |
| guard/plan closure v2, predecessor only | `research_loop/advisory/20260910_pcfl_v11_controllerless_guard_closure_v2.md` | `a768682b68e0bbab93dc50e6ea6011894a10b75475f55c18b4df0a187678a5e1` |
| controlling guard-plan census/review closure v3 | `research_loop/advisory/20260910_pcfl_v11_controllerless_guard_closure_v3.md` | `96a392cd487d2d399d76873d3fe633e581eb372e0f6bec5bf4254617c31cbd02` |
| source plan v1, predecessor only | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan.json` | `46263de44eefccc9face8b9cf76fd48986a55e7a527cce1bd32b1bc731ae92ce` |
| controlling source plan v2 proposal | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan_v2.json` | `1b7d618c79379494e98a674e56cae46a8c9346412a4e68d9575b911a9c17076a` |
| integration preflight repair v1 | `research_loop/advisory/20260910_pcfl_v11_integration_preflight_repair_v1.md` | `a9dc887e8acdf5eacb9a5eca6a2f4586e84269b8d15befd110bcf09a9f669f4e` |
| integration candidate v1 | `research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate.md` | `586500e72c6e03da5f9e4e9800094017888e1e4648bb656a2caad82335a8b5bc` |
| current directive | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/human_directive.txt` | `42a678a04fb6be507f7f2adec781c1d9b72f3e7d205387d3fdc79945751cceff` |
| current scope proposal | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/scope_proposal.json` | `ddc4235cacdd5c2fdd27efe97d9ef76756aa8525baaa32e941afac2ba96f381b` |
| normative denial corpus | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json` | `4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799` |
| corpus ratification evidence | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_denial_corpus_ratification_evidence.txt` | `3934b01d022ff6b463def3003408d2fb5822c9991764b4bc386aa5bcc2385b58` |
| sole corpus precedence closure | `research_loop/advisory/20260910_pcfl_v11_denial_corpus_ratification_closure_v1.md` | `a540470046064196d04dfa9602ab5aa9f8090706bf3e5e266ee630945ef580c2` |
| controlling corpus/provenance repair | `research_loop/advisory/20260910_pcfl_v11_denial_corpus_provenance_repair_v1.md` | `8d0c28201cec2e695d2a615ca2d8b9230bfee28c032b887096b24332d7431e65` |

Precedence is exact:

1. closure v3 controls the two census path remaps, exact C11 review-grant
   operation array, complete review-input preimage, and external final-workflow
   rule;
2. closure v2 controls plan-v2 authoring, same-grant guard custody,
   guard execution, checker nonparticipation, and its other express
   supersessions, except where closure v3 replaces it;
3. candidate v3 controls all remaining integration, deterministic grammar,
   registry, resource, authority, visibility, roster, and claim clauses,
   except its workflow section and non-boundary normative-source identity are
   replaced by sections 2 and 4 below; and
4. the effective corpus closure/provenance repair and V10 heads retain their
   stated precedence subject only to these explicit C11 supersessions.

Candidate v3, closure v2, plan v1, and every earlier candidate/closure are
predecessor evidence, not alternative controlling choices. Any unlisted
conflict is `REWORK`.

## 2. Exact final workflow schema and 90 context paths

### 2.1 Closed workflow fields

The final workflow JSON has exactly the runner-supported top-level fields:

```text
schema_version workflow_kind name workspace change_id directive_file
context_files output_dir state_path intake_state_path run_dir roles
```

It has no `bound_inputs`, role/access context wrapper, context-manifest
digest, source binding, attempt count, or workflow digest field.
`directive_file` is exactly `DIRECTIVE_PATH_C11`; it does not also occur in
`context_files`.

`context_files` is exactly the following ordered array of 90 distinct
repository-relative path strings and no object or extra path:

```text
AGENTS.md
research_notes/64_iclr_paper_core_and_benchmark_v2.md
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v4/human_directive.txt
research_loop/workflows/pcfl_m0_mtext_bound_v4.deliberation.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v4/scope_proposal.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v4/change.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v4/interpretation_systems.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v4/interpretation_benchmark.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v4/critique.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v4/consensus.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v4/intake.state.json
.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v4.deliberation.state.json
research_loop/plans/pcfl_m0_mtext_exact_v4_rework_candidate.md
research_loop/advisory/20260910_pcfl_v4_governance_packet_audit_v1.md
research_loop/advisory/20260910_pcfl_v5_authority_handoff_delayed_v7_source_repair_v1.md
research_loop/advisory/20260910_pcfl_v5_endpoints_claims_exact_repair_v1.md
research_loop/advisory/20260910_pcfl_v5_provenance_resource_repair_v1.md
research_loop/plans/pcfl_m0_mtext_exact_v5_source_authoring_candidate.md
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v5/human_directive.txt
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v5/source_authoring_plan.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v5/scope_proposal.json
research_loop/workflows/pcfl_m0_mtext_bound_v5.deliberation.json
.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v5.deliberation.state.json
research_loop/advisory/20260910_pcfl_v5_packet_preflight_fresh_audit_v1.md
research_loop/advisory/20260910_pcfl_v6_baseline_projection_preflight_repair_v1.md
research_loop/plans/pcfl_m0_mtext_exact_v6_source_authoring_candidate.md
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v6/human_directive.txt
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v6/source_authoring_plan.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v6/scope_proposal.json
research_loop/workflows/pcfl_m0_mtext_bound_v6.deliberation.json
.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v6.deliberation.state.json
research_loop/advisory/20260910_pcfl_v6_packet_preflight_fresh_audit_v1.md
research_loop/advisory/20260910_pcfl_v7_baseline_projection_exact_closure_v1.md
research_loop/plans/pcfl_m0_mtext_exact_v7_source_authoring_candidate.md
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v7/source_authoring_plan.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v7/scope_proposal.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v7/human_directive.txt
research_loop/workflows/pcfl_m0_mtext_bound_v7.deliberation.json
.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v7.deliberation.state.json
research_loop/advisory/20260910_pcfl_v7_packet_preflight_fresh_audit_v1.md
research_loop/advisory/20260910_pcfl_v8_repeat_null_exact_closure_v1.md
research_loop/plans/pcfl_m0_mtext_exact_v8_source_authoring_candidate.md
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v8/source_authoring_plan.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v8/scope_proposal.json
research_loop/workflows/pcfl_m0_mtext_bound_v8.deliberation.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v8/human_directive.txt
.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v8.deliberation.state.json
research_loop/advisory/20260910_pcfl_v8_packet_preflight_fresh_audit_v1.md
research_loop/advisory/20260910_pcfl_v9_binding_boundary_exact_closure_v1.md
research_loop/plans/pcfl_m0_mtext_exact_v9_source_authoring_candidate.md
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v9/source_authoring_plan.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v9/scope_proposal.json
research_loop/workflows/pcfl_m0_mtext_bound_v9.deliberation.json
research_loop/advisory/20260910_pcfl_v9_packet_preflight_fresh_audit_v1.md
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v9/change.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v9/interpretation_systems.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v9/interpretation_benchmark.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v9/critique.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v9/consensus.json
.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v9.deliberation.state.json
research_loop/advisory/20260910_pcfl_v10_registry_render_claim_exact_repair_v1.md
research_loop/advisory/20260910_pcfl_v10_registry_render_claim_exact_repair_v2.md
research_loop/advisory/20260910_pcfl_v10_registry_render_claim_exact_repair_v3.md
research_loop/advisory/20260910_pcfl_v10_provenance_resource_guard_exact_repair_v1.md
research_loop/advisory/20260910_pcfl_v10_provenance_resource_guard_exact_repair_v2.md
research_loop/advisory/20260910_pcfl_v10_provenance_resource_guard_exact_repair_v3.md
research_loop/advisory/20260910_pcfl_v10_authority_delayed_baseline_exact_repair_v1.md
research_loop/advisory/20260910_pcfl_v10_authority_delayed_baseline_exact_repair_v2.md
research_loop/advisory/20260910_pcfl_v10_repair_trio_cross_preflight_v1.md
research_loop/plans/pcfl_m0_mtext_exact_v10_source_authoring_candidate.md
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source_authoring_plan.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/scope_proposal.json
research_loop/workflows/pcfl_m0_mtext_bound_v10.deliberation.json
.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v10.deliberation.state.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_denial_corpus_ratification_evidence.txt
research_loop/advisory/20260910_pcfl_v11_denial_corpus_ratification_candidate_v1.md
research_loop/advisory/20260910_pcfl_v11_denial_corpus_ratification_candidate_v2.md
research_loop/advisory/20260910_pcfl_v11_denial_corpus_provenance_repair_v1.md
research_loop/advisory/20260910_pcfl_v11_denial_corpus_ratification_closure_v1.md
research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate.md
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/scope_proposal.json
research_loop/workflows/pcfl_m0_mtext_bound_v11.deliberation.json
research_loop/advisory/20260910_pcfl_v11_integration_preflight_repair_v1.md
research_loop/advisory/20260910_pcfl_v11_controllerless_guard_closure_v1.md
research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate_v2.md
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan_v2.json
research_loop/advisory/20260910_pcfl_v11_controllerless_guard_closure_v3.md
research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate_v4.md
```

This is a 90-for-90 replacement of the predecessor list's final closure and
candidate paths: closure v2 is replaced by closure v3, and candidate v3 is
replaced by candidate v4. They are not appended as paths 91 and 92. Closure
v3 and candidate v4 bind their immediate predecessors by exact digest.

### 2.2 External workflow hash and runner bindings

This candidate does not bind any SHA-256 to the live `WORKFLOW_PATH_C11`.
After the exact 90-path workflow bytes are sealed, the runner computes their
digest and stores it in initialized state as `workflow_sha256`. The same
workflow path also occurs at its fixed context position; its runner-generated
`source_bindings` row has that same final digest. No historical workflow hash
is a current binding or authorization.

Runner initialization computes `source_bindings` exactly as the directive-
first sequence:

```text
[
  {path:workflow.directive_file,sha256:SHA256(exact directive bytes)},
  {path:workflow.context_files[0],sha256:SHA256(exact context-0 bytes)},
  ...,
  {path:workflow.context_files[89],sha256:SHA256(exact context-89 bytes)}
]
```

Every row has exactly `path` and `sha256`, no role/access/purpose field. State
validation requires its `workflow_sha256` to equal the final workflow rehash
and its 91 source bindings to equal a fresh directive-first recomputation.
The workflow's self-path causes no byte cycle because only the path string is
stored in workflow JSON; both state hashes are computed after workflow bytes
are sealed.

No state is initialized here. A separate exact human authorization over the
final externally computed workflow hash is required before any model call.

## 3. Final 23-role census and complete review binding

The original `GovernanceRoleV11` enum remains exactly 23 values in its
original order. Exactly these two role paths are controlling:

```text
V11_SOURCE_AUTHORING_PLAN ->
  research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan_v2.json
V11_V7_GUARD_SOURCE ->
  research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v7_boundary_guard_controller_v1.py
```

The final census must store plan-v2 SHA-256
`1b7d618c79379494e98a674e56cae46a8c9346412a4e68d9575b911a9c17076a`
and the future reviewed/ratified guard digest. A current-plan role containing
plan v1, candidate `prepare_v4.py`, either controllerless advisory, null,
alias, or duplicate rejects. No role is added.

For C11 plan v2, the existing `GovernanceExactByteReviewGrantV1[C11]`
retains its actor/schema/cardinality but has exactly this operation array:

```text
[
  "READ_EXACTLY_BOUND_SOURCE_REVIEW_INPUTS_AS_INERT_BYTES",
  "COMPUTE_SHA256_AND_BYTE_LENGTH_OF_BOUND_MEMBERS_MANIFEST_AND_SINGLETON_GOVERNANCE_NONMEMBER_GUARD",
  "VALIDATE_CLOSED_DATA_SCHEMAS_WITHOUT_CANDIDATE_IMPORT_OR_EXECUTION",
  "WRITE_ONE_GOVERNANCE_PRIVATE_EXACT_BYTE_REVIEW_RECEIPT"
]
```

Its `review_input_binding_sha256` hashes closure v3's exact closed
`SourceReviewInputBindingV1[C11]`: plan-v2 hash, source-grant hash, manifest
hash, exact corpus path/hash, all ordered 23 manifest member tuples, and the
exact singleton guard tuple. No inherited value may be omitted or replaced.
The same reviewer hashes/measures those 23 members, manifest, and guard, and
emits only the same `IndependentExactByteReviewReceiptV1`. No actor, grant,
receipt, role, or second review loop is added.

The guard remains authored under the same future
`SourceAuthoringGrantV1[C11]`, reviewed and exact-byte ratified with candidate
bytes, and executed only under a later separate
`PreparationExecutionGrantV1[C11]`. The two candidate checkers and
`prepare_v4.py` remain inert at guard substage zero and do not validate it.
The guard fails closed internally without claiming independent checker or
parser execution.

## 4. Exact provenance-source successor

Candidate v3 section 3's exact bytewise-sorted 22-path non-boundary domain is
retained without addition, removal, or reordering. For every one of those 22
paths, replace only its one-entry `derivation_sources` value with:

```text
[{kind:"PCFL_V11_NORMATIVE",
  identifier:"PCFL-M0-MTEXT-V11-INTEGRATION-CANDIDATE-V4",
  path:CANDIDATE_V4_PATH_C11,
  sha256:CANDIDATE_V4_SHA256_C11}]
```

The digest is the exact externally rehashed candidate-v4 value directly bound
by the final workflow/state/consensus/human-grant chain; it is never an author
choice. No second, language, V10, predecessor-candidate, closure, optional,
null, or alias source is permitted.

The boundary remains outside the 22-path domain and retains exactly these two
sorted sources and no third:

```text
{kind:"PCFL_V11_NORMATIVE",
 identifier:"V11-DENIAL-CORPUS-PROJECTION-RULE",
 path:"research_loop/advisory/20260910_pcfl_v11_denial_corpus_provenance_repair_v1.md",
 sha256:"8d0c28201cec2e695d2a615ca2d8b9230bfee28c032b887096b24332d7431e65"}
{kind:"PCFL_V11_NORMATIVE",
 identifier:"V11-NORMATIVE-DENIAL-CORPUS",
 path:"research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json",
 sha256:"4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799"}
```

The manifest remains 23 member/provenance rows. The guard is a governance
nonmember and has no manifest/provenance row. All inherited attestation,
false-V7, ordering, anti-laundering, external-placement, and mutation rules
remain exact.

## 5. Preserved experiment, resource, acceptance, authority, and claims

Except for sections 2--4, candidate v3 and its exact predecessor stack are
inherited without amendment. C11 preserves the 25-row plan-v2 structure with
23 members, one manifest nonmember, one guard nonmember, the governance-input
singleton, one boundary, and exact 22-path projection; the complete 32-record
nine-field registry and fixture ownership; the exact inert observation
grammar and authenticated bundle; the 47/57 finite sets, 23 roles, 22 sinks,
and direct/encoded/causal nonexposure; and the same source-authoring, review,
consensus, exact-byte-ratification, preparation, and guard order.

It also preserves the exact `ChargedResourceV11`, `CasObjectChargeV11`, and
`ResourceMeterEventV11` parameterization, standalone/physical CAS,
nonomission, post-origin charging, and metered numerical CPU/latency/wall/GPU/
peak-memory rule; exactly 18 conditions; 501 slots and 148224 generated
tokens per ordinary root; 16 DEV / 32 CONFIRMATION / 16 RESERVE roots; 24
sentinels; active maxima of 24072 slots and 7120896 generated tokens; delayed
tests 13/29, test-28 dependencies, endpoint rules, and noncompensatory gates.

The claim remains limited to the fixed-policy/fixed-topology supplied-memory
experiment. DREAM authorship, SLEEP, LoRA/parametric transport, compression,
online learning, self-write, retention, parenting, recurrence,
generalization, scale/lifetime improvement, baseline saturation,
text-versus-LoRA efficiency, and whole-organism behavior remain excluded.

## 6. Eligibility and stop boundary

This v4 candidate and closure v3 close the known proposal-level census,
review-operation, review-preimage, and workflow-identity defects. Their paths
may replace the predecessor closure/candidate strings in a future 90-context
workflow. Actual deliberation remains blocked until the workflow is edited,
sealed, externally hashed, initialized with exact source bindings, and
separately human-authorized. Deliberation must use the five roles, fresh
independent interpretations, adversarial cross-critique, complete concern
disposition, and stop at `human_required`; its maximum recommendation is that
a human consider a later plan-v2-bound source-authoring grant.

This proposal creates no workflow/state/grant/review/consensus/ratification,
source, manifest, provenance row, guard result, preparation, fixture, root,
data, model output, or scientific result. It performs and authorizes no
source/checker/guard import, compilation, execution, preparation,
implementation, materialization, checker/test/model/tokenizer/benchmark/
training/GPU work, parenting, resource acquisition, scientific claim,
release, or submission.
