# PCFL V11 integration preflight repair v1

Date: 2026-09-10

Status: **source-only proposal repair; not ratified**. This advisory resolves
four design ambiguities in the V11 integration candidate, but it does not
create or authorize a workflow, state, source-authoring grant, candidate
source, governance-controller source, manifest, provenance row, review,
ratification, guard invocation, preparation, implementation, materialization,
fixture/root/data generation, checker/test/model/tokenizer execution,
benchmark, training, LoRA/adapter/checkpoint work, parenting, GPU use,
resource acquisition, scientific claim, release, or submission.

## 0. Exact scope and precedence

This repair binds the following existing bytes directly:

| role | path | SHA-256 |
|---|---|---|
| V11 integration candidate | `research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate.md` | `586500e72c6e03da5f9e4e9800094017888e1e4648bb656a2caad82335a8b5bc` |
| V11 source plan proposal | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan.json` | `46263de44eefccc9face8b9cf76fd48986a55e7a527cce1bd32b1bc731ae92ce` |
| V11 scope proposal | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/scope_proposal.json` | `ddc4235cacdd5c2fdd27efe97d9ef76756aa8525baaa32e941afac2ba96f381b` |
| V11 directive | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/human_directive.txt` | `42a678a04fb6be507f7f2adec781c1d9b72f3e7d205387d3fdc79945751cceff` |
| V11 denial corpus | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json` | `4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799` |
| V11 corpus evidence | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_denial_corpus_ratification_evidence.txt` | `3934b01d022ff6b463def3003408d2fb5822c9991764b4bc386aa5bcc2385b58` |
| sole corpus precedence closure | `research_loop/advisory/20260910_pcfl_v11_denial_corpus_ratification_closure_v1.md` | `a540470046064196d04dfa9602ab5aa9f8090706bf3e5e266ee630945ef580c2` |
| controlling corpus/provenance repair | `research_loop/advisory/20260910_pcfl_v11_denial_corpus_provenance_repair_v1.md` | `8d0c28201cec2e695d2a615ca2d8b9230bfee28c032b887096b24332d7431e65` |

For C11 only, this advisory supersedes candidate section 1's workflow-input
list, section 6's nonboundary provenance and analyzer/guard identity, section
7's `V11_V7_GUARD_SOURCE` path and 23-role census cardinality, section 10's
guard-source custody, and checklist items 1, 3, 6, and 7. All other candidate
clauses remain unchanged. The corpus closure remains controlling except for
the expressly proposed governance-role expansion in section 5.5 below. That
expansion has no authority unless a human later ratifies this advisory's exact
bytes and the exact expansion sentence specified there.

## 1. Direct workflow bindings; no transitive substitute

The only planned deliberation workflow path is:

```text
WORKFLOW_PATH_C11 =
  "research_loop/workflows/pcfl_m0_mtext_bound_v11.deliberation.json"
```

No workflow is created here, and `WORKFLOW_SHA256_C11` is unknown until that
future file is closed. Before any model call, the workflow and its initialized
zero-attempt state must directly bind, as distinct input rows, the exact path
and SHA-256 of each of the eight objects in section 0, plus this advisory's
final path and SHA-256. In particular, the exact candidate, plan, scope, and
directive rows are mandatory and cannot be replaced by a hash appearing in
another context.

Each required row is closed and has exactly:

```text
WorkflowBoundInputV1 := {
  role: WorkflowInputRoleV11,
  path: the exact repository-relative path,
  sha256: the exact lowercase hex64 digest,
  access: "DELIBERATION_CONTEXT_ONLY"
}
```

`WorkflowInputRoleV11` is exactly this bytewise-sorted enum:

```text
V11_CORPUS_RATIFICATION_EVIDENCE
V11_DENIAL_CORPUS_PRECEDENCE_CLOSURE_V1
V11_DENIAL_CORPUS_PROVENANCE_REPAIR_V1
V11_HUMAN_DIRECTIVE
V11_INTEGRATION_CANDIDATE
V11_INTEGRATION_PREFLIGHT_REPAIR_V1
V11_NORMATIVE_DENIAL_CORPUS
V11_SCOPE_PROPOSAL
V11_SOURCE_AUTHORING_PLAN
```

Rows are sorted bytewise by `(role,path,sha256)`, duplicate-free, and each
file is independently rehashed before workflow authorization. The future
workflow also binds its own closed context-manifest digest, the exact five
role/model specifications, deliberation-only runner, `attempt_count:0`, empty
artifact slots, and a terminal `human_required` state. Missing, transitive-
only, stale, extra, aliased, directory, glob, or symlink bindings reject before
any call. Workflow authoring and state initialization are proposal rework;
running them still requires a separate exact human authorization not present
in the current directive, scope, corpus evidence, candidate, or this repair.

## 2. Complete per-member provenance catalog

### 2.1 One exact source for each nonboundary member

For each of the following 22 nonboundary plan members, the external
`SourceProvenanceRowV1[C11].derivation_sources` array contains exactly one
entry, byte-for-byte identical to the entry below. No language-standard,
standard-library, second normative, inherited V10, alias, or free-form entry
is permitted:

```text
{
  kind: "PCFL_V11_NORMATIVE",
  identifier: "PCFL-M0-MTEXT-V11-INTEGRATION-CANDIDATE",
  path: "research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate.md",
  sha256: "586500e72c6e03da5f9e4e9800094017888e1e4648bb656a2caad82335a8b5bc"
}
```

The closed catalog domain is exactly this bytewise-sorted list:

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

The integration candidate is a direct C11 normative source only if a future
human `SourceAuthoringGrantV1[C11]` binds its exact path/hash and this repair's
exact path/hash after successful V11 deliberation. Its references to older
heads do not create a provenance-parent graph: the human-bound candidate is
the single direct specification from which each nonboundary source member is
authored. Without that exact future grant the entry is not normative and no
member may be written.

### 2.2 Boundary remains exactly two-source

The boundary row remains exactly the controlling repair's two sorted
`PCFL_V11_NORMATIVE` entries and no third:

```text
{
  kind: "PCFL_V11_NORMATIVE",
  identifier: "V11-DENIAL-CORPUS-PROJECTION-RULE",
  path: "research_loop/advisory/20260910_pcfl_v11_denial_corpus_provenance_repair_v1.md",
  sha256: "8d0c28201cec2e695d2a615ca2d8b9230bfee28c032b887096b24332d7431e65"
}
{
  kind: "PCFL_V11_NORMATIVE",
  identifier: "V11-NORMATIVE-DENIAL-CORPUS",
  path: "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json",
  sha256: "4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799"
}
```

Every row otherwise uses the exact closed `SourceProvenanceRowV1[C11]`, false
V7 flags, cross-field denial matcher, external placement, and exact
`<G>`-interpolated attestation in the controlling provenance repair. The
manifest has exactly 23 rows in plan-member order. A missing catalog member,
different source count, source substitution, or boundary citation of the
integration candidate rejects atomically.

## 3. Closed deterministic observation grammar

### 3.1 Inputs, media partition, and canonical evidence primitives

The governance controller consumes all 23 exact reviewed member byte strings,
their external manifest/provenance rows, the exact plan, and the ratified
corpus as inert bytes. The nonboundary media partition is fixed by the plan:
17 `application/json` files, four `text/x-python` files, and one
`text/markdown` file. A media/path mismatch, unknown kind, BOM, CR, invalid
UTF-8, non-NFC decoded string, NUL, or unreviewed byte rejects.

All JSON evidence objects below are recursively closed and serialized as RFC
8785/JCS plus exactly one LF. `SHA256_JCS_LF(x)` means SHA-256 over exactly
those bytes. Byte offsets are zero-based half-open offsets in the original
member bytes, never code-point, character, token, or line/column offsets.

```text
SourceSpanV1 := {
  logical_path: repo_relative_path,
  member_sha256: hex64,
  start_byte: u64,
  end_byte: u64,
  slice_sha256: hex64
}

source_span_sha256 = SHA256_JCS_LF(SourceSpanV1)
```

Reject unless `0 <= start_byte < end_byte <= member_nbytes` and
`slice_sha256` rehashes exactly `member_bytes[start_byte:end_byte]`. Tokens
which include JSON or Python quotes include those delimiters in the span.
Repeated equal values at distinct spans remain distinct.

For every bundle row having `observation_id`, compute:

```text
observation_id = SHA256_JCS_LF(the exact row with observation_id omitted)
```

For every capability node, compute `node_id` the same way with `node_id`
omitted. Any claimed ID mismatch rejects. Arrays are sorted by the exact tuple
already specified by the controlling repair; ID hashing does not replace that
ordering rule.

Path evidence is exactly:

```text
PathResolutionEvidenceV1 := {
  schema_version: 1,
  artifact_type: "pcfl_v11_path_resolution_evidence",
  source_span_sha256: hex64,
  lexical_path: nfc_string,
  normalized_path: repo_relative_normalized_posix_path,
  resolution_mode: "LEXICAL_CLOSED_ROOT_NO_SYMLINK",
  components: [nonempty_nfc_string, ...],
  symlink_hops: []
}
resolution_evidence_sha256 = SHA256_JCS_LF(PathResolutionEvidenceV1)
```

Normalization replaces no character: it splits only literal `/`, rejects an
empty component, `.`, `..`, a leading slash, trailing slash except a corpus
prefix operand, repeated slash, backslash, drive prefix, URI scheme, NUL, or
non-NFC component, and rejoins the same components with `/`. Therefore
`resolved_target == normalized_path`. Any case requiring a filesystem query,
symlink hop, home/current-directory expansion, environment expansion, mount
lookup, or external resolution rejects. The complete evidence objects are
stored governance-privately in the future guard receipt; the authenticated
bundle contains only their digests.

### 3.2 JSON grammar and total leaf classification

Every `application/json` member must be RFC 8785/JCS plus one LF and have no
duplicate key. The controller parses only the JSON data grammar; it invokes no
candidate function. It traverses object keys in UTF-8 byte order and arrays in
index order, assigning each key token and scalar value its RFC 6901 pointer
and exact raw-byte `SourceSpanV1`.

Future `source/provenance_contract_v4.json` contains a closed
`json_leaf_classifications` array with exactly one row for every key token and
scalar leaf of every other JSON member:

```text
JsonLeafClassificationV1 := {
  logical_path: one of the other 16 JSON member paths,
  json_pointer: canonical_rfc6901_pointer,
  token_kind: "OBJECT_KEY" | "STRING" | "NUMBER" | "BOOLEAN" | "NULL",
  source_span_sha256: hex64,
  classification: "INERT_LITERAL" | "PATH" | "MODULE" | "INTERFACE" |
                  "DIGEST" | "EMBEDDED_BYTES" | "CAPABILITY_TARGET" |
                  "DOWNSTREAM_SINK",
  capability_surface: null | one_of_the_exact_11_corpus_surfaces,
  encoding: null | "UTF8" | "LOWERCASE_HEX" | "BASE64_RFC4648",
  consumer_ids: [nfc_string, ...]
}
```

Rows are sorted by `(logical_path,json_pointer,token_kind,source_span_sha256)`,
duplicate-free, and total. `capability_surface` is non-null iff classification
is `CAPABILITY_TARGET`; `encoding` is non-null iff bytes require decoding;
`consumer_ids` is nonempty iff a Python call site or downstream schema leaf
consumes the value. The controller reconstructs the entire key/scalar census
and requires exact set equality with the classification array. The
provenance-contract member itself is validated by the controller's built-in
closed schema above and is independently scanned for every denial operand; it
does not classify itself and contains no executable behavior.

Every key/string is compared literally against all exact change, dependency,
interface, digest, module, and path predicates. `PATH`, `MODULE`, `DIGEST`,
and `EMBEDDED_BYTES` rows emit their corresponding observations. Embedded
bytes are decoded only with the named exact encoding, and their declared
parent pointer, offset, length, and digest must agree with the decoded bytes.
`INERT_LITERAL` is legal only when `consumer_ids` is empty and the independently
reconstructed Python/consumer graph proves no read. A pointer read by source
but labeled inert, a consumer without an exact row, or decoded bytes with an
unclassified nested payload rejects.

### 3.3 Python grammar and complete static call census

The four Python members are parsed as inert UTF-8 source by the governance
controller's hash-bound parser; they are never imported, compiled to bytecode,
or executed before guard pass. The future preparation grant binds the exact
controller source hash and the exact parser-runtime executable and grammar
library hashes. A parser/runtime hash mismatch or disagreement with either
independent checker rejects.

The controller walks every syntax node and token span. It applies these closed
rules:

1. Every `import` and `from ... import ...` module is a literal dotted name
   and emits a module observation. Relative, wildcard, computed, hook-based,
   or failed-to-normalize imports reject.
2. Every call target is either a literal same-module function name or a
   literal dotted `Name`/`Attribute` chain. Subscripted, returned, computed,
   aliased, reflective, decorator-produced, descriptor-produced, or otherwise
   dynamic call targets reject.
3. Every call site has exactly one closed annotation in
   `python_call_classifications`, keyed by logical path and
   `source_span_sha256`, with classification `PURE_LOCAL` or `CAPABILITY`.
   A pure-local target must resolve to exactly one definition in the same
   member. A capability row names exactly one of the eleven corpus surfaces
   and every path/module/resource/subprocess/network/environment/
   configuration/argv/file-descriptor/deserialization operand as a literal
   constant or recursively literal tuple/list/dict. `*args`, `**kwargs`,
   f-strings, concatenation, formatting, decoding, environment-derived,
   data-derived, or name-derived capability operands reject.
4. Every string/bytes literal, identifier, attribute chain, subscript key,
   decorator, default expression, context manager, exception target, and
   serialization tag is separately scanned against the finite denial
   predicates. Literal path/module/digest/interface operands emit observations.
5. Exact names `eval`, `exec`, `compile`, `__import__`, `getattr`, `setattr`,
   `delattr`, `globals`, `locals`, `vars`, and any `importlib`, `pkgutil`,
   `ctypes`, dynamic loader, pickle, marshal, shell, or network target are
   rejected unless the exact call is classified as a capability with all
   operands literal; `eval`, `exec`, `compile`, and `__import__` always reject.
6. The reconstructed same-member call graph and eleven-surface capability
   graph must be finite, complete, and acyclic. An unresolved name, foreign
   callable, recursion, opaque decorator/descriptor, dynamic attribute,
   dynamic subscript key used for a consumer read, generated code, or syntax
   node without the required classification rejects.

`python_call_classifications` has exactly:

```text
PythonCallClassificationV1 := {
  logical_path: one of the four Python member paths,
  source_span_sha256: hex64,
  callee: nfc_string,
  classification: "PURE_LOCAL" | "CAPABILITY",
  capability_surface: null | one_of_the_exact_11_corpus_surfaces,
  literal_operand_span_sha256: [hex64, ...],
  json_consumer_ids: [nfc_string, ...]
}
```

Rows and both arrays are bytewise sorted and duplicate-free. Surface is null
iff pure-local. Set equality with the controller's complete syntax call census
is mandatory; the table cannot omit a call by calling it harmless.

Every Python access to a JSON member is additionally represented exactly once
in `python_json_consumers`:

```text
PythonJsonConsumerV1 := {
  consumer_id: hex64,
  logical_path: one of the four Python member paths,
  source_span_sha256: hex64,
  access_kind: "READ" | "WRITE" | "COMPARE" | "PUBLIC_EMIT",
  producer_logical_path: one of the 16 classified JSON member paths,
  json_pointer: canonical_rfc6901_pointer
}

consumer_id = SHA256_JCS_LF(the exact row with consumer_id omitted)
```

Rows are sorted by `(logical_path,source_span_sha256,access_kind,
producer_logical_path,json_pointer)` and duplicate-free. Every relevant
literal subscript, `.get`, iterator, serializer, parser, renderer, scorer,
receipt, or output access has one row; dynamic producer selection or pointer
construction rejects. Each JSON leaf classification's `consumer_ids` equals
exactly the bytewise-sorted IDs of rows targeting that leaf. The controller
reconstructs this bipartite relation from both sides; a dangling, hidden,
extra, multiply targeted, or incorrectly classified edge rejects.

### 3.4 Markdown grammar

The sole Markdown member is UTF-8 NFC with LF line endings and no BOM, CR, or
NUL. It is never rendered or executed by the guard. The controller scans all
bytes, including fenced/indented code, comments, and link labels, into maximal
nonempty identity tokens over ASCII `[A-Za-z0-9_./:-]`; delimiters are not
tokens. Every token receives a source span and is compared by the exact corpus
path/module/digest/interface/change/dependency rules. Markdown links, images,
autolinks, raw HTML attributes, and URI schemes reject; a repository-relative
path token is normalized by section 3.1 and emits a path observation. No
ignored region, entity decoding, case fold, Unicode confusable mapping, or
renderer-dependent interpretation exists.

### 3.5 Independent completeness and failure

The controller independently reconstructs member identities, all JSON leaves,
all Python syntax/call/consumer rows, Markdown tokens, embedded members,
external provenance parents, and all eleven capability-root closures. It then
requires byte-identical agreement with the declarative tables and emits the
exact `AuthenticatedDenialObservationBundleV1` from the controlling repair.
The two existing independent checkers separately implement this advisory's
grammar and must agree without importing the controller or candidate helpers.

An unrecognized file kind, token, node, call, consumer, payload encoding,
dynamic construction, missing/extra annotation, ID/span mismatch, unresolved
target, incomplete surface, cycle, parser disagreement, or denial match sets
`closure_status:"REJECT"`, emits only governance-private
`SOURCE_BOUNDARY_REJECTED`, and produces no projection. No accepted default or
author-selected classification exists.

## 4. Strict governance-controller separation

### 4.1 Exact role, path, and ceiling

Candidate `source/prepare_v4.py` remains only the inert
`PREPARATION_ENTRYPOINT` member. Before guard pass it may be read and parsed as
bytes but never imported, compiled, invoked, or executed. It is not the
analyzer, guard, runner, or authority controller.

The sole planned controller identity is instead:

```text
role: "V11_V7_GUARD_SOURCE"
logical_path:
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v7_boundary_guard_controller_v1.py"
media_type: "text/x-python"
maximum_nbytes: 262144
access: "GOVERNANCE_ONLY"
plan_entry: false
manifest_member: false
projected: false
candidate_preparation_runtime_input: false
```

That path is outside the 24-row source plan, outside the normative source
manifest, and outside the 22-path projection. No alias, symlink, generated
temporary copy, package import, or alternate controller is legal. The source
does not yet exist and no hash is guessed by this advisory.

### 4.2 Separate author, review, and exact-byte gates

The controller can exist only through this future sequence:

```text
fresh deliberation and human ratification of this repair
  -> human GovernanceGuardSourceAuthoringGrantV1[C11]
  -> GOVERNANCE_GUARD_SOURCE_WRITER writes only the planned controller path,
     then computes its byte length and SHA-256 without executing it
  -> human GovernanceGuardSourceReviewGrantV1[C11] binding those exact bytes
  -> independent GOVERNANCE_GUARD_SOURCE_REVIEWER reads and rehashes them,
     reviews conformance to section 3, and emits only
     GovernanceGuardSourceReviewReceiptV1[C11]
  -> human GovernanceGuardSourceExactByteRatificationV1[C11]
  -> a later V11 source-only deliberation binds the final controller hash
  -> only a still-later human PreparationExecutionGrantV1 may authorize one
     controller invocation as substage zero
```

Each gate is recursively closed and has exactly the following form:

```text
GovernanceGuardSourceAuthoringGrantV1[C11] := {
  schema_version: 1,
  artifact_type: "pcfl_v11_guard_source_authoring_grant",
  change_id: "chg_20260910_pcfl_m0_mtext_bound_v11",
  state: "guard_source_authoring_approved",
  actor: "GOVERNANCE_GUARD_SOURCE_WRITER",
  repair: {path:this_advisory_path,sha256:this_advisory_final_sha256},
  controller: {
    role: "V11_V7_GUARD_SOURCE",
    logical_path: exact_path_from_section_4_1,
    media_type: "text/x-python",
    maximum_nbytes: 262144
  },
  authorized_operations: [
    "WRITE_EXACT_CONTROLLER_PATH",
    "COMPUTE_SHA256",
    "COMPUTE_BYTE_LENGTH"
  ],
  forbidden_operations: [
    "CREATE_EDIT_OR_DELETE_CANDIDATE_SOURCE",
    "EDIT_SOURCE_PLAN_OR_MANIFEST",
    "IMPORT_COMPILE_OR_EXECUTE_CONTROLLER_OR_CANDIDATE",
    "PREPARATION_MATERIALIZATION_CHECKER_TEST_OR_FIXTURE_EXECUTION",
    "MODEL_TOKENIZER_BENCHMARK_TRAINING_PARENTING_OR_GPU_USE",
    "SCIENTIFIC_CLAIM_RELEASE_OR_SUBMISSION"
  ],
  ratifier: nonempty_nfc_string,
  decided_at: rfc3339_utc,
  authorization_evidence: {
    path:repo_relative_path,sha256:hex64,excerpt:nonempty_nfc_string
  },
  candidate_source_authoring_authorized: false,
  controller_execution_authorized: false,
  preparation_execution_authorized: false,
  model_execution_authorized: false,
  scientific_claim_authorized: false
}

GovernanceGuardSourceReviewGrantV1[C11] := {
  schema_version: 1,
  artifact_type: "pcfl_v11_guard_source_review_grant",
  change_id: "chg_20260910_pcfl_m0_mtext_bound_v11",
  state: "guard_source_review_approved",
  actor: "GOVERNANCE_GUARD_SOURCE_REVIEWER",
  source_authoring_grant_sha256: hex64,
  repair: {path:this_advisory_path,sha256:this_advisory_final_sha256},
  controller: {
    logical_path:exact_path_from_section_4_1,nbytes:u64,sha256:hex64
  },
  authorized_operations: [
    "READ_EXACT_CONTROLLER_AS_INERT_BYTES",
    "COMPUTE_SHA256_AND_BYTE_LENGTH",
    "REVIEW_EXACT_OBSERVATION_GRAMMAR_CONFORMANCE",
    "WRITE_ONE_GOVERNANCE_PRIVATE_REVIEW_RECEIPT"
  ],
  forbidden_operations: [
    "CREATE_EDIT_OR_DELETE_CONTROLLER_OR_CANDIDATE_SOURCE",
    "IMPORT_COMPILE_OR_EXECUTE_CONTROLLER_OR_CANDIDATE",
    "PREPARATION_MATERIALIZATION_CHECKER_TEST_OR_FIXTURE_EXECUTION",
    "MODEL_TOKENIZER_BENCHMARK_TRAINING_PARENTING_OR_GPU_USE",
    "SCIENTIFIC_CLAIM_RELEASE_OR_SUBMISSION"
  ],
  ratifier: nonempty_nfc_string,
  decided_at: rfc3339_utc,
  authorization_evidence: {
    path:repo_relative_path,sha256:hex64,excerpt:nonempty_nfc_string
  },
  controller_execution_authorized: false,
  preparation_execution_authorized: false,
  model_execution_authorized: false,
  scientific_claim_authorized: false
}

GovernanceGuardSourceReviewReceiptV1[C11] := {
  schema_version: 1,
  artifact_type: "pcfl_v11_guard_source_review_receipt",
  change_id: "chg_20260910_pcfl_m0_mtext_bound_v11",
  review_grant_sha256: hex64,
  source_authoring_grant_sha256: hex64,
  repair_sha256: this_advisory_final_sha256,
  controller_logical_path: exact_path_from_section_4_1,
  expected_nbytes: u64,
  observed_nbytes: u64,
  expected_sha256: hex64,
  observed_sha256: hex64,
  ruleset: "PCFL_V11_CLOSED_OBSERVATION_GRAMMAR_V1",
  reviewer: "GOVERNANCE_GUARD_SOURCE_REVIEWER",
  violation_codes: [nfc_string, ...],
  candidate_execution_count: 0,
  controller_execution_count: 0,
  denied_target_read_count: 0,
  passed: boolean
}

GovernanceGuardSourceExactByteRatificationV1[C11] := {
  schema_version: 1,
  artifact_type: "pcfl_v11_guard_source_exact_byte_ratification",
  change_id: "chg_20260910_pcfl_m0_mtext_bound_v11",
  state: "guard_source_exact_bytes_ratified",
  repair_sha256: this_advisory_final_sha256,
  source_authoring_grant_sha256: hex64,
  review_grant_sha256: hex64,
  review_receipt_sha256: hex64,
  controller: {
    logical_path:exact_path_from_section_4_1,nbytes:u64,sha256:hex64
  },
  ratifier: nonempty_nfc_string,
  decided_at: rfc3339_utc,
  authorization_evidence: {
    path:repo_relative_path,sha256:hex64,excerpt:nonempty_nfc_string
  },
  controller_execution_authorized: false,
  preparation_execution_authorized: false,
  model_execution_authorized: false,
  scientific_claim_authorized: false
}
```

No extra field is legal. `nbytes` is positive and at most 262144. Arrays are
literal and ordered; `violation_codes` is bytewise sorted and duplicate-free.
Review passes iff observed length/hash equal expected, every binding rehashes,
all three counters are zero, and `violation_codes` is empty. Exact-byte
ratification is valid only for a passing receipt and the same controller
tuple. Neither grant, receipt, nor ratification authorizes an invocation.

The later preparation grant is valid only if it directly binds the exact
controller ratification and source hash, exact candidate-byte ratification,
plan, manifest, corpus, boundary, controller parser-runtime manifest, one
attempt, and the four-field pass-only projection. The authority-side runner
loads only the ratified controller source; the controller treats all 23
candidate members as inert bytes. It may parse them according to section 3 but
may not import, compile, or execute any candidate member. Only after a guard
pass may the same preparation grant invoke `source/prepare_v4.py` and later
substages it expressly enumerates.

### 4.3 Current readiness adjudication

This advisory closes the role/path/grammar/custody design choice but cannot
close controller-byte readiness: the controller source, its hash, grants,
review receipt, and exact-byte ratification do not exist. Therefore the
current V11 packet may be deliberated only as a repair proposal and is
**blocked from any `SourceAuthoringGrantV1[C11]` recommendation** until the
separate controller chain above is completed and a new exact packet directly
binds it. Model agreement cannot waive this blocker.

## 5. Governance census and nonexposure consequence

### 5.1 Exact C11-only role expansion

Moving the guard outside the source plan cannot be hidden from the finite
governance census. The closure's 23 roles remain unchanged except that
`V11_V7_GUARD_SOURCE` now maps to the governance path in section 4.1, not
`source/prepare_v4.py`, and these four new roles are inserted in bytewise
order immediately after it:

```text
V11_V7_GUARD_SOURCE_AUTHORING_GRANT
V11_V7_GUARD_SOURCE_EXACT_BYTE_RATIFICATION
V11_V7_GUARD_SOURCE_REVIEW_GRANT
V11_V7_GUARD_SOURCE_REVIEW_RECEIPT
```

Their sole paths are, respectively:

```text
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v7_guard_source_authoring_grant.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v7_guard_source_exact_byte_ratification.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v7_guard_source_review_grant.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v7_guard_source_review_receipt.json
```

Thus `GovernanceRoleV11` has exactly 27 roles. The optional corpus
ratification record remains the only role allowed absent/null; all 26 others
are required in the final census. All closure section-4.2 path/hash, sort,
uniqueness, regular-file, no-alias, and non-self-reference laws otherwise
remain unchanged. The new role/path/hash strings enter
`BOUND_GOVERNANCE_LITERALS_C11` and the same 22-sink direct/causal nonexposure
tests. None crosses the projection.

### 5.2 Required human supersession

The 27-role census is a change to the human-bound closure and is not effective
from this advisory alone. A future human decision must bind this advisory's
exact path/hash and state exactly:

> For C11 only, I replace the 23-role GovernanceRoleV11 census in the bound
> denial-corpus closure with the exact 27-role census and V11_V7_GUARD_SOURCE
> path in PCFL V11 integration preflight repair v1; I authorize no source
> authoring, controller authoring, review, execution, preparation, model call,
> GPU use, scientific claim, release, or submission by this decision.

Absent that exact supersession, the closure's original 23-role census remains
controlling, the controller gate cannot be represented completely, and the
source-authoring blocker in section 4.3 remains terminal.

## 6. Preserved experiment and stop boundary

This repair adds only future governance roles and governance CPU/storage. It
adds no experiment condition, root, sentinel, slot, endpoint, reader/action
opportunity, token allowance, model call, retry, resource exemption, gate, or
claim. It preserves exactly 18 conditions, 501 slots and 148,224 generated
tokens per ordinary root, the 16 DEV / 32 CONFIRMATION / 16 RESERVE split, 24
sentinels, and active maxima of 24,072 slots and 7,120,896 generated tokens.
Governance controller authoring/review/invocation work is metered separately,
never charged as or used as feedback for an experimental arm, and grants no
scientific evidence.

No source, controller, workflow, state, grant, manifest, provenance row,
review, receipt, ratification, guard result, projection, preparation,
implementation, fixture, root, data, test, model, tokenizer, benchmark,
training, LoRA/adapter/checkpoint, parenting, GPU, resource acquisition,
scientific claim, release, or submission operation is created, run, or
authorized by this advisory.
