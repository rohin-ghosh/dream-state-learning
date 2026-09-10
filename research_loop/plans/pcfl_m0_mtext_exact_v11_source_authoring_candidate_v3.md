# PCFL M0 + M-TEXT-SUPPLIED V11 — integration successor candidate v3

Date: 2026-09-10

Status: **proposal-only, precedence-closed candidate for future five-role
architecture deliberation; not source-authoring authority**. This file does
not create or run a workflow/state, author source, import/compile/execute a
guard or candidate member, prepare or materialize data, generate fixtures/
roots/data, run a checker/test/model/tokenizer/benchmark/training/GPU job,
parent an agent, acquire resources, or make/release/submit a scientific claim.

## 0. Exact identity and self-hash rule

```text
C11 = "chg_20260910_pcfl_m0_mtext_bound_v11"
CANDIDATE_V3_PATH_C11 =
  "research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate_v3.md"
WORKFLOW_PATH_C11 =
  "research_loop/workflows/pcfl_m0_mtext_bound_v11.deliberation.json"
DIRECTIVE_PATH_C11 =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/human_directive.txt"
```

`CANDIDATE_V3_SHA256_C11` means the sole lowercase SHA-256 independently
computed after these bytes are sealed. It is not stored in this file. The
future workflow names this exact path in `context_files`; runner-generated
state binds the actual hash in `source_bindings`; every later consensus,
human-required state, grant, and provenance row must use that same value. A
placeholder, guessed value, path-only binding, or author-selected digest
rejects.

## 1. Exact input stack and precedence

This candidate directly binds:

| role | path | SHA-256 |
|---|---|---|
| integration candidate v1 | `research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate.md` | `586500e72c6e03da5f9e4e9800094017888e1e4648bb656a2caad82335a8b5bc` |
| integration preflight repair v1 | `research_loop/advisory/20260910_pcfl_v11_integration_preflight_repair_v1.md` | `a9dc887e8acdf5eacb9a5eca6a2f4586e84269b8d15befd110bcf09a9f669f4e` |
| controllerless closure v1, predecessor only | `research_loop/advisory/20260910_pcfl_v11_controllerless_guard_closure_v1.md` | `37b4098f7cb809a86c3217a4c1267cad62dd799f3403a75c2b871c9f7d2f8f3b` |
| integration candidate v2, predecessor only | `research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate_v2.md` | `82dc79fe88dd7204898b123c02ce7cabb78761f38b0be0bfc97a248fe8579ffd` |
| source plan v1, predecessor only | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan.json` | `46263de44eefccc9face8b9cf76fd48986a55e7a527cce1bd32b1bc731ae92ce` |
| controlling source plan v2 proposal | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan_v2.json` | `1b7d618c79379494e98a674e56cae46a8c9346412a4e68d9575b911a9c17076a` |
| controlling guard/plan closure v2 | `research_loop/advisory/20260910_pcfl_v11_controllerless_guard_closure_v2.md` | `a768682b68e0bbab93dc50e6ea6011894a10b75475f55c18b4df0a187678a5e1` |
| current directive | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/human_directive.txt` | `42a678a04fb6be507f7f2adec781c1d9b72f3e7d205387d3fdc79945751cceff` |
| current scope proposal | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/scope_proposal.json` | `ddc4235cacdd5c2fdd27efe97d9ef76756aa8525baaa32e941afac2ba96f381b` |
| pre-successor workflow, predecessor only | `research_loop/workflows/pcfl_m0_mtext_bound_v11.deliberation.json` | `e0b9583d0d3e8c559676b1b5a8a477c091d61f518da908bad69d8dde21d2aaba` |
| normative denial corpus | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json` | `4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799` |
| corpus ratification evidence | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_denial_corpus_ratification_evidence.txt` | `3934b01d022ff6b463def3003408d2fb5822c9991764b4bc386aa5bcc2385b58` |
| sole corpus precedence closure | `research_loop/advisory/20260910_pcfl_v11_denial_corpus_ratification_closure_v1.md` | `a540470046064196d04dfa9602ab5aa9f8090706bf3e5e266ee630945ef580c2` |
| controlling corpus/provenance repair | `research_loop/advisory/20260910_pcfl_v11_denial_corpus_provenance_repair_v1.md` | `8d0c28201cec2e695d2a615ca2d8b9230bfee28c032b887096b24332d7431e65` |

Precedence is exact:

1. guard/plan closure v2 controls plan supersession, guard source/custody,
   original 23-role census, checker nonparticipation, bundle analyzer
   identity, and its explicit supersessions;
2. integration preflight repair v1 sections 1--3 control workflow binding,
   the 22-path provenance domain, boundary sources, and inert observation
   grammar, except for the exact source-entry and checker clauses replaced by
   guard/plan closure v2 and sections 3--4 below;
3. candidate v1 controls all remaining integration, registry, resource,
   authority, visibility, roster, and claim clauses; and
4. corpus closure/provenance repair retain their stated precedence except for
   the exact nonmember analyzer supersession in guard/plan closure v2.

Candidate v2, controllerless closure v1, and plan v1 are predecessor evidence
only. The unbound exploratory guard-grammar design is noncontrolling. Any
other conflict is `REWORK`; no implementer or workflow chooses a reading.

The current directive's literal plan-v1 reference is not presented as a final
plan binding. The directive remains the exact proposal-rework authority;
guard/plan closure v2 is the non-self-referential proposal-level supersession
that makes plan v1 predecessor-only and plan v2 the sole plan eligible for a
later source grant. Fresh deliberation and human action remain required.

## 2. Exact workflow and runner-state schema

### 2.1 Workflow JSON

The future revised workflow keeps the runner's exact closed top-level schema:

```text
schema_version
workflow_kind
name
workspace
change_id
directive_file
context_files
output_dir
state_path
intake_state_path
run_dir
roles
```

It contains no `bound_inputs`, role/access wrapper, context-manifest digest,
attempt count, source hash, workflow hash, or other unsupported field.
`directive_file` is exactly the string:

```text
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/human_directive.txt
```

That path must not also occur in `context_files`. Every other required durable
input is an exact repository-relative path string in `context_files`, not an
object. Starting from the pre-successor workflow bytes at SHA-256
`e0b9583d0d3e8c559676b1b5a8a477c091d61f518da908bad69d8dde21d2aaba`,
the revised workflow retains every unique context string in its existing
order and appends exactly these six strings in this order:

```text
research_loop/advisory/20260910_pcfl_v11_integration_preflight_repair_v1.md
research_loop/advisory/20260910_pcfl_v11_controllerless_guard_closure_v1.md
research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate_v2.md
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan_v2.json
research_loop/advisory/20260910_pcfl_v11_controllerless_guard_closure_v2.md
research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate_v3.md
```

The current context already contains the exact scope proposal, plan v1,
candidate v1, corpus, evidence, corpus candidate/repair/closure stack, V10
heads, V9 evidence, and inherited packet contexts. Thus both plan paths and
the scope path are direct `context_files` strings, while the directive is the
one direct `directive_file` string. Missing, duplicate, reordered appended,
aliased, absolute, glob, directory, symlink, or URI strings reject before a
model call.

The pre-successor workflow already lists its own repository-relative path as
a context source, and that string remains in its retained position. This is
supported without a hash cycle: the workflow stores only its path, while the
runner computes the final workflow digest after the bytes are sealed and
records that digest both as `workflow_sha256` and in the corresponding
`source_bindings` context row. A prior workflow digest, including the current
pre-successor workflow, is not valid for the revised bytes.

### 2.2 Runner-generated state bindings

No hand-authored role/access binding schema exists. Initialization computes
exactly:

```text
source_bindings = [
  {path:workflow.directive_file,
   sha256:SHA256(exact directive bytes)},
  {path:workflow.context_files[0],
   sha256:SHA256(exact context-0 bytes)},
  ...,
  {path:workflow.context_files[n-1],
   sha256:SHA256(exact context-(n-1) bytes)}
]
```

Every row has exactly the two fields `path` and `sha256`; the directive row is
first, followed by context rows in exact workflow order. There is no `role`,
`access`, `purpose`, or context-manifest row. The initialized runner state is
the exact closed schema implemented by `architecture_deliberation.py`,
including `workflow_path`, `workflow_sha256`, `source_bindings`, zero attempt
counts/attempts, and its normal timestamps/run ID. State validation requires
its `workflow_sha256` to equal the rehash of the workflow and its
`source_bindings` array to equal a fresh directive-first recomputation.

The directive, scope, both plans, this candidate, and both guard closures are
therefore directly byte-bound without inventing workflow fields. No runner
state exists yet, and this proposal neither initializes nor runs it. A
separate exact human authorization over the final revised workflow/state is
required before any model call.

## 3. Exact plan and provenance catalog

Plan v2 at SHA-256
`1b7d618c79379494e98a674e56cae46a8c9346412a4e68d9575b911a9c17076a`
has exactly 25 sorted rows: one governance-only nonmember guard source, one
nonmember manifest output, and the unchanged 23 manifest members. The guard
path is exactly:

```text
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v7_boundary_guard_controller_v1.py
```

It has role `V11_V7_GUARD_SOURCE`, media type `text/x-python`, maximum 262144
bytes, and `manifest_member:false`. The existing governance-input singleton,
manifest output, 23 member paths/roles/media/ceilings, boundary, and sorted
22-path pass projection remain unchanged.

For every path in the following exact bytewise-sorted domain, the future
external `SourceProvenanceRowV1[C11].derivation_sources` array contains
exactly one entry:

```text
{kind:"PCFL_V11_NORMATIVE",
 identifier:"PCFL-M0-MTEXT-V11-INTEGRATION-CANDIDATE-V3",
 path:CANDIDATE_V3_PATH_C11,
 sha256:CANDIDATE_V3_SHA256_C11}
```

```text
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/acceptance_tests.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/cas_freeze_contract_v4.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/check_axiomatic_v4.py
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/check_constructive_v4.py
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/claim_disposition_v4.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/delayed_twin_entitlement_v4.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/endpoint_gate_registry_v4.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/failure_precedence_v4.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/handoff_consumer_graph_v4.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/handoff_projection_allowlist_v4.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/handoff_public_v4.schema.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/integrated_contract.md
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/materialize_v4.py
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/mtext_handoff_v4.schema.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/mutation_fixtures.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/object_schemas_v4.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/prepare_v4.py
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/provenance_contract_v4.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/resource_roster_v4.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/runtime_manifest_v4.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/semantic_table_v4.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/transition_table_v4.json
```

`CANDIDATE_V3_SHA256_C11` is the externally rehashed value in the exact
workflow/state/consensus/human-grant chain, never an author choice. No v1/v2
candidate, repair, language-standard, standard-library, second normative,
null, alias, optional, or third entry is allowed.

The boundary is outside that domain and retains exactly its two sorted
sources and no third:

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

The manifest remains exactly 23 member rows/provenance rows. The guard is a
nonmember and has no manifest/provenance row. All inherited false V7 flags,
attestation, sorting, cross-field anti-laundering, external placement, and
mutation rules remain mandatory.

## 4. Same-grant guard custody and deterministic execution boundary

The one future `SourceAuthoringGrantV1[C11]` binds plan v2 and authorizes the
same Authority-S actor and three inherited operations. It writes/hashes the
23 member sources plus the one plan-listed guard source and then writes the
23-entry nonauthoritative manifest. It adds no grant type, actor, operation,
or role. Authority S imports, parses, compiles, and executes none of those
bytes.

The one existing `GovernanceExactByteReviewGrantV1[C11]` and one existing
`IndependentExactByteReviewReceiptV1` bind/review the same candidate closure
plus the exact guard tuple through guard/plan closure v2's inline
`SourceReviewInputBindingV1[C11]`. The reviewer rehashes and inspects but does
not execute. Fresh exact-byte consensus and the same human
`ExactByteRatificationV1[C11]` bind the guard together with candidate bytes.
No separate guard grant, receipt, consensus, ratification, or census role
exists.

Only a later separate human `PreparationExecutionGrantV1[C11]` can execute
the exact ratified guard as substage zero. It directly binds the plan,
manifest, exact-byte ratification, guard path/hash, corpus, boundary,
parser-runtime hashes, and one attempt. The guard applies integration repair
section 3's exact inert grammar and independently reconstructs the
authenticated bundle. It never imports, compiles, invokes, or executes a
candidate member. `prepare_v4.py`, `check_axiomatic_v4.py`, and
`check_constructive_v4.py` remain inert until pass and do not validate the
guard at substage zero.

There is no checker-agreement or independent-parser-execution requirement.
The guard fails closed internally on parser/runtime mismatch or exception,
unrecognized syntax, missing/extra classification, unresolved dynamic
observation, incomplete eleven-surface closure, denial match, or any grammar
equality failure. This does not claim independent guard execution. Its bundle
analyzer path/hash are the plan-listed guard path and exact ratified guard
digest. Pass emits only the inherited four-field/22-path projection; failure
emits only governance-private `SOURCE_BOUNDARY_REJECTED`, no projection,
retry, or reserve substitution.

The original `GovernanceRoleV11` census remains exactly 23 roles, with its
existing `V11_V7_GUARD_SOURCE` role mapped to the guard script. The guard path
and hash enter the existing bound-governance literal/nonexposure machinery;
no role is added.

## 5. Preserved experiment, resource, acceptance, and claim contract

Except for the exact plan/guard/workflow/provenance supersessions above, the
v1 integration candidate and effective V10/V11 repair stack remain controlling
in full. C11 preserves:

- the complete ordered 32-record, closed nine-field acceptance registry,
  exact fixture ownership and terminal receipts, test-13/test-29 separation,
  exact test-28 dependencies, and test-01/test-34 guard ownership;
- the exact corpus projection, embedded-artifact supersession, 47/57 finite
  sets, 23-role census, 22-sink map, and direct/encoded/causal nonexposure;
- the exact `ChargedResourceV11`, `CasObjectChargeV11`, and
  `ResourceMeterEventV11` parameterization, standalone/physical CAS,
  nonomission, post-origin charging, and metered numerical CPU/latency/wall/
  GPU/peak-memory exception;
- exactly 18 conditions, 501 registered slots and 148224 generated tokens per
  ordinary root, 16 DEV / 32 CONFIRMATION / 16 RESERVE roots, 24 sentinels,
  and active maxima of 24072 slots and 7120896 generated tokens; and
- the inherited authority order, delayed-baseline rules, endpoint semantics,
  noncompensatory gates, and fixed-policy/fixed-topology supplied-memory claim
  ceiling.

The exclusions of DREAM authorship, SLEEP, LoRA/parametric transport,
compression, online learning, self-write, retention, parenting, recurrence,
generalization, scale/lifetime improvement, baseline saturation,
text-versus-LoRA efficiency, and whole-organism behavior remain unconditional.
No source, review, consensus, ratification, guard result, or partial test can
broaden them.

## 6. Eligibility and stop boundary

This v3 candidate closes the known proposal-level plan, guard-custody,
checker-bootstrap, provenance-parent, and workflow-schema choices. Its bytes
are eligible to be added to a revised V11 deliberation workflow. Actual
deliberation remains blocked until that workflow and runner-generated
zero-attempt state satisfy section 2 exactly and a human separately authorizes
the final workflow hash/model calls. Deliberation must use the five roles,
fresh interpretations, adversarial cross-critique, exact concern disposition,
and stop at `human_required`. Its maximum recommendation is that a human
consider a later exact `SourceAuthoringGrantV1[C11]` bound to plan v2.

This proposal is not a workflow, state, grant, review, consensus,
ratification, or implementation. No source/guard/checker import, compilation,
execution, preparation, materialization, fixture/root/data generation,
checker/test/model/tokenizer/benchmark/training/GPU work, parenting, resource
acquisition, scientific execution, claim, release, or submission follows from
these bytes.
