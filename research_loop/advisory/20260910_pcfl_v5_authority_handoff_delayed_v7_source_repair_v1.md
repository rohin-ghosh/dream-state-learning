# PCFL V5 authority, handoff, delayed-twin, and zero-V7 source repair — v1

Date: 2026-09-10

Status: **source-only advisory proposal**. This file is not a ratification and
does not authorize preparation-source authoring, implementation, deterministic
materialization, fixture/root/data generation, checker or benchmark execution,
model/tokenizer use, training, LoRA/adapter/checkpoint work, parenting, GPU use,
resource acquisition, scientific execution, claim, release, or submission.

## Verdict and exact scope

The V4 consensus is correctly `recommendation="rework"` and
`state="human_required"`. Four of its unresolved dispositions can be closed by
adopting the normative text below in the proposed successor
`chg_20260910_pcfl_m0_mtext_bound_v5`:

- `D-V4-SOURCE-AUTHORITY-CIRCULARITY`;
- `D-V4-HANDOFF-PROJECTION-CLOSURE`;
- `D-V4-DELAYED-TWIN-ENTITLEMENT`; and
- `D-V4-ZERO-V7-PROVENANCE`.

This advisory does not dispose the other unresolved V4 disagreements. A V5
consensus is not technically releasable until every required V4 concern is
disposed in one newly hash-bound chain.

The controlling bytes inspected for this repair are:

| Artifact | SHA-256 |
|---|---|
| `AGENTS.md` | `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e` |
| V4 `change.json` | `a6332cfeab3bc2281404a568e2c04eaf8ffa28db96d3c33265140f9fe7c3408f` |
| V4 systems interpretation | `ac9b91c20cb75ca18d7b5608423e3377d0aaa6ff24e45513acfd4bfd4f6bf270` |
| V4 benchmark interpretation | `745f6514672ffaf2e14c87088c55dbad67232054a219a821a4a36f51ca8d6af3` |
| V4 critique | `6caa938022d9e6b2e47a3d3997b8d06c44a67568550fd86716d6123e2c1e2fad` |
| V4 consensus | `7cad92d5563f0b0be69d6dd72fca7419573d93fbb19021e5b614e0bac0798720` |
| integrated V4 candidate | `32d73b800971a61a20fa68694dc9cbed9203c65d59d3c01c5baffe2c3a6e53cc` |
| V4 governance audit | `0b11febe8abadc4d2c9bddfdf87ad269d5fb209e438e83352153a18d9c891a7c` |

## 1. Normative closure for `D-V4-SOURCE-AUTHORITY-CIRCULARITY`

### 1.1 Replace the ambiguous rule

Replace every occurrence of “before any preparation-source authorization” in
`M0V4-EXACT-SOURCE-RATIFIABILITY-00` with:

> Before `PREPARATION_EXECUTION_AUTHORITY` or any implementation authority,
> every executable or outcome-relevant source byte, schema, semantic table,
> materializer, checker, mutation fixture, runtime identity, input, roster,
> endpoint rule, prohibition, and source-provenance row MUST be present and
> individually bound by path, byte length, and SHA-256 in one closed
> `NormativeSourceManifestV1`. Permission to author those absent candidate
> bytes is the distinct, non-execution `SOURCE_CANDIDATE_AUTHORING_AUTHORITY`
> and requires an exact path/role/size plan, but cannot require hashes of bytes
> that do not yet exist.

The two authorities below are disjoint. Possession, completion, passage, or
hashing under one never implies the other.

### 1.2 Authority S: candidate-source authoring only

`SOURCE_CANDIDATE_AUTHORING_AUTHORITY` is represented only by a strict
`SourceAuthoringGrantV1` whose closed schema is:

```text
SourceAuthoringGrantV1 := {
  schema_version:1,
  artifact_type:"pcfl_m0_source_authoring_grant",
  change_id:"chg_20260910_pcfl_m0_mtext_bound_v5",
  state:"source_authoring_approved",
  successor_consensus_sha256:hex64,
  human_required_state_sha256:hex64,
  source_authoring_plan_sha256:hex64,
  ratifier:string,
  decided_at:rfc3339_utc,
  authority_statement:string,
  decision_statement:string,
  authorized_operations:[
    "CREATE_OR_EDIT_EXACTLY_LISTED_CANDIDATE_SOURCE_PATHS",
    "COMPUTE_SHA256_AND_BYTE_LENGTH_OF_LISTED_PATHS",
    "WRITE_NONAUTHORITATIVE_NORMATIVE_SOURCE_MANIFEST"
  ],
  forbidden_operations:[
    "IMPORT_OR_EXECUTE_AUTHORED_SOURCE",
    "PREPARATION_OR_MATERIALIZATION",
    "CHECKER_OR_TEST_EXECUTION",
    "FIXTURE_ROOT_OR_DATA_GENERATION",
    "M0_OR_MTEXT_RUNTIME_IMPLEMENTATION",
    "BENCHMARK_MODEL_OR_TOKENIZER_EXECUTION",
    "TRAINING_LORA_ADAPTER_OR_CHECKPOINT_WORK",
    "PARENTING_OR_GPU_USE",
    "RESOURCE_ACQUISITION",
    "SCIENTIFIC_CLAIM_RELEASE_OR_SUBMISSION"
  ],
  authorization_evidence:{path:repo_relative_path,sha256:hex64,excerpt:string},
  source_authoring_authorized:true,
  preparation_execution_authorized:false,
  implementation_authorized:false,
  model_execution_authorized:false,
  scientific_claim_authorized:false
}
```

Arrays are exact, in the order shown; extra, missing, duplicate, or reordered
members reject. `authority_statement`, `decision_statement`, and the evidence
excerpt must explicitly say “source authoring only” and name the bound
`source_authoring_plan_sha256`. This grant MUST NOT use the existing generic
architecture-ratification schema whose `implementation_authorized=true` field
would misstate this authority.

The referenced `SourceAuthoringPlanV1` is a closed JCS object:

```text
SourceAuthoringPlanV1 := {
  schema_version:1,
  artifact_type:"pcfl_m0_source_authoring_plan",
  change_id:"chg_20260910_pcfl_m0_mtext_bound_v5",
  entries:[SourcePlanRow, ...],
  manifest_output_path:
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v5/normative_source_manifest.json"
}

SourcePlanRow := {
  logical_path:repo_relative_path,
  role:closed_role_enum,
  media_type:"application/json"|"text/markdown"|"text/x-python",
  maximum_nbytes:u64,
  manifest_member:boolean
}
```

`entries` is nonempty, sorted bytewise by NFC `logical_path`, unique, contains
no symlink, glob, directory, `..`, absolute path, or unresolved variable, and
is itself hash-bound before Authority S. `manifest_output_path` occurs exactly
once as a plan row with `role="NORMATIVE_SOURCE_MANIFEST"` and
`manifest_member=false`; every other row has `manifest_member=true`. Authority
S may write no path absent from the plan and may not enlarge a maximum.

At minimum, the V5 plan MUST contain exact rows for these four closure
surfaces; a complete V5 plan will also list every other deliberated semantic,
materializer, checker, mutation, and runtime source path:

```text
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v5/
  source/handoff_public_v4.schema.json
  source/mtext_handoff_v4.schema.json
  source/handoff_projection_allowlist_v4.json
  source/handoff_consumer_graph_v4.json
  source/delayed_twin_entitlement_v4.json
  source/v7_boundary_v4.json
  normative_source_manifest.json
```

These are literal paths, not directories or globs. The complete plan is the
authority allowlist; this minimum list does not silently authorize omitted
source files.

After authoring, the nonauthoritative candidate manifest has the exact schema:

```text
NormativeSourceManifestV1 := {
  schema_version:1,
  artifact_type:"pcfl_m0_normative_source_manifest",
  change_id:"chg_20260910_pcfl_m0_mtext_bound_v5",
  source_authoring_plan_sha256:hex64,
  source_authoring_grant_sha256:hex64,
  entries:[{
    logical_path:repo_relative_path,
    role:closed_role_enum,
    media_type:"application/json"|"text/markdown"|"text/x-python",
    nbytes:u64,
    sha256:hex64,
    provenance_row_sha256:hex64
  }, ...]
}
```

Its entries equal every and only plan rows with `manifest_member=true`, in the
same sorted order, and match plan roles/media types/maxima. The manifest never
contains its own hash. Its external SHA-256 is computed after close and may be
used only by later review and Authority P. Completing it grants no authority.

### 1.3 Authority P: one deterministic preparation execution

`PREPARATION_EXECUTION_AUTHORITY` is represented only by a separate strict
`PreparationExecutionGrantV1`:

```text
PreparationExecutionGrantV1 := {
  schema_version:1,
  artifact_type:"pcfl_m0_preparation_execution_grant",
  change_id:"chg_20260910_pcfl_m0_mtext_bound_v5",
  state:"preparation_execution_approved",
  pre_authority_binding_sha256:hex64,
  normative_source_manifest_sha256:hex64,
  source_review_sha256:hex64,
  source_consensus_sha256:hex64,
  source_human_required_state_sha256:hex64,
  entrypoint:{logical_path:repo_relative_path,nbytes:u64,sha256:hex64},
  preparation_input_binding_sha256:hex64,
  preparation_input_root:hex64,
  execution_count:1,
  argv:[string,...],
  working_directory:repo_relative_path,
  environment:[{name:string,value:string},...],
  read_allowlist:[{logical_path:repo_relative_path,nbytes:u64,sha256:hex64},...],
  write_allowlist:[repo_relative_path,...],
  limits:{cpu_threads:u16,wall_seconds:u64,artifact_bytes:u64,
          network:"DENY",gpu:"DENY",model:"DENY",tokenizer:"DENY"},
  ratifier:string,
  decided_at:rfc3339_utc,
  authority_statement:string,
  decision_statement:string,
  authorization_evidence:{path:repo_relative_path,sha256:hex64,excerpt:string},
  source_authoring_authorized:false,
  preparation_execution_authorized:true,
  implementation_authorized:false,
  model_execution_authorized:false,
  scientific_claim_authorized:false
}
```

The grant is valid only if the manifest is closed, every entry rehashes, the
source review and consensus explicitly accept the exact bytes, the human
evidence quotes the `pre_authority_binding_sha256`, and `read_allowlist` equals
the transitive file closure declared by the runtime manifest. `argv`, working
directory, environment, write paths, and resource limits are values, not
implementation defaults. No network, model, tokenizer, GPU, retry, root
selection, replacement, or second attempt exists. Candidate CAS outputs and
receipts remain nonconsumable until the separate human fixture freeze.

Authority P cannot create or edit source. Any source-byte change invalidates
its manifest, review, consensus, grant, input root, and run identity and
requires a new chain. Authority S cannot execute preparation. This makes the
authority graph acyclic:

```text
V5 design consensus
  -> exact SourceAuthoringPlanV1
  -> human SourceAuthoringGrantV1
  -> candidate source bytes + NormativeSourceManifestV1
  -> exact-byte source review/consensus
  -> pre-authority binding
  -> human PreparationExecutionGrantV1
  -> one nonconsumable candidate preparation result
  -> separate human fixture freeze
```

### 1.4 Replacement acceptance test

Register:

```text
M0V5-SOURCE-AUTHORING-VS-PREPARATION-AUTHORITY-12
```

It passes only if closed-schema validation and negative mutations prove that:
(a) Authority S binds exact paths/roles/maxima but not nonexistent output
hashes; (b) Authority S cannot execute/import source or write outside its path
plan; (c) Authority P binds every actual byte/hash and one exact execution;
(d) Authority P cannot edit source; (e) neither grant parses as the other; and
(f) source completion, checker passage, or candidate production never creates
the next grant. Swap either boolean set, omit/extra a path, mutate a hash,
enlarge a maximum, execute an authored entrypoint under Authority S, write a
source path under Authority P, or attempt a second run: each MUST fail closed.

## 2. Normative closure for `D-V4-HANDOFF-PROJECTION-CLOSURE`

All records below are closed JCS JSON objects: unknown, missing, duplicate,
mistyped, out-of-range, non-NFC, or noncanonical fields reject. `pad` contains
only ASCII underscore bytes and is determined by the separately frozen V4
fixed-size rule. No map may be used as an extension point.

### 2.1 Exact public semantic payload

```text
HandoffPublicV4 := {
  v:4,
  artifact_type:"pcfl_m0_handoff_public",
  instrument:"PCFL_M0_THIN_V4",
  phase_public_mode:"PATH"|"UNCERTAINTY"|"ACQUIRE"|"DELAYED",
  semantic_cut:"OLD"|"NEW"|"DELAYED",
  carrier:CarrierV4,
  initial_view:FiniteViewV4,
  action_catalog:ActionCatalogPublicV4,
  budgets:{reads_remaining:u8,relation_attempts_remaining:u8,
           terminal_opportunity_remaining:0|1},
  response_schema:"PCFL_COMMAND_V4",
  pad:string
}
```

The exact top-level field set is the set shown. `HandoffPublicV4` contains no
digest of itself and no source, manifest, authority, freeze, root, hidden bit,
condition, split, transform, expected answer, score, scorer, oracle, route,
filename, host, process, session, timing, model, tokenizer, renderer, parser,
or receipt identity. In particular the predecessor fields
`fixture_manifest_root`, `instrument_contract_digest`, and
`public_payload_digest` are forbidden. Neutral actor handles already exist in
`CarrierV4`, `FiniteViewV4`, and `ActionCatalogPublicV4`; projection may not
replace them with semantic hashes.

`phase_public_mode` states only the public interaction grammar. It never names
an arm or condition. `semantic_cut` states which public evidence cut is
available. The condition-appropriate carrier is reader input, not prompt
content.

### 2.2 Exact private binding envelope

```text
MTextHandoffV4 := {
  schema_version:1,
  artifact_type:"pcfl_mtext_private_handoff",
  semantic_contract_id:"PCFL-M0-MTEXT-HANDOFF-v4",
  change_id:"chg_20260910_pcfl_m0_mtext_bound_v5",
  m0_freeze_id:hex64,
  handoff_public_sha256:hex64,
  root_route_id:opaque32,
  condition_route_id:opaque32,
  checkpoint_route_id:opaque32,
  split_route_id:opaque32,
  transform_id:closed_transform_enum,
  fixture_origin:
    "FROZEN_OLD"|"FROZEN_NEW"|"SUPPLIED_CANONICAL_CORRECT_ACQUISITION",
  renderer_source_sha256:hex64,
  parser_source_sha256:hex64,
  controller_source_sha256:hex64,
  reader_contract_sha256:hex64,
  reset_contract_sha256:hex64,
  endpoint_oracle_sha256:hex64,
  model_projection_contract_sha256:hex64,
  model_boundary_manifest_sha256:hex64,
  roster_manifest_sha256:hex64
}
```

The exact field set is the set shown. Every `opaque32` is exactly 32 lowercase
hexadecimal characters, has a domain-separated controller-only derivation,
and is never rendered, echoed in an error, used for public ordering/padding,
or used as a model cache key. The private envelope contains no carrier, public
view, prompt, model scratch, model output, or mutable session object.

Verification first rehashes the separately loaded `HandoffPublicV4`, verifies
the named nonclaim `m0_freeze_id`, then verifies every source/contract binding.
A mismatch terminates before dispatch and produces a checker-only failure.

### 2.3 Exact projection allowlists

The renderer's first-turn input is exactly:

```text
ModelTurnPublicV4 := {
  v:4,
  prompt_mode:HandoffPublicV4.phase_public_mode,
  view:HandoffPublicV4.initial_view,
  action_catalog:HandoffPublicV4.action_catalog,
  budgets:HandoffPublicV4.budgets,
  last_public_result:null,
  scratch:null,
  response_schema:HandoffPublicV4.response_schema,
  pad:string
}
```

For later turns in the same phase, `view`, `budgets`, and
`last_public_result` may be replaced only by public transition outputs, and
`scratch` may contain only the model's previously permitted same-phase scratch.
No field of `MTextHandoffV4` is in the renderer allowlist. `carrier` and
`semantic_cut` are not rendered. The renderer receives an immutable typed
`ModelTurnPublicV4`, not either handoff object and not a generic dictionary.

The common reader's static input allowlist is exactly
`HandoffPublicV4.carrier`; its dynamic input is exactly
`(anchor,cursor,reader_open,repeat_state)`. It receives no private-envelope
field, goal, score, expected answer, condition label, split, transform label,
or endpoint oracle. The public transition controller's initial static
allowlist is exactly `phase_public_mode`, `initial_view`, `action_catalog`,
`budgets`, and `response_schema`. It may consume parsed public commands and
public reader returns but no scorer/oracle result.

The dispatcher may consume only the four route IDs, `m0_freeze_id`,
`handoff_public_sha256`, `transform_id`, and `fixture_origin`. The verifier may
consume all private-envelope fields and the raw public object. The sealed
scorer/checker may consume the verified envelope, dynamic public receipts, and
checker-only truth, but has no edge back to dispatcher, reader, controller,
renderer, parser, model, or model-visible error handling.

### 2.4 Exact consumer graph

The only permitted edges are:

```text
M0_PUBLIC_PROJECTOR -> HandoffPublicV4
M0_PRIVATE_BINDER -> MTextHandoffV4
HandoffPublicV4 -> HANDOFF_VERIFIER
MTextHandoffV4 -> HANDOFF_VERIFIER
HANDOFF_VERIFIER -> VERIFIED_PUBLIC
HANDOFF_VERIFIER -> VERIFIED_PRIVATE
VERIFIED_PRIVATE -> PRIVATE_DISPATCHER
VERIFIED_PRIVATE -> SEALED_SCORER_CHECKER
VERIFIED_PUBLIC.carrier -> COMMON_READER
VERIFIED_PUBLIC.{phase_public_mode,initial_view,action_catalog,budgets,
                 response_schema} -> PUBLIC_CONTROLLER
PUBLIC_CONTROLLER -> ModelTurnPublicV4
ModelTurnPublicV4 -> RENDERER
RENDERER -> MODEL
MODEL -> PARSER
PARSER -> PUBLIC_CONTROLLER
PUBLIC_CONTROLLER.{anchor,cursor,reader_open,repeat_state} -> COMMON_READER
COMMON_READER -> PUBLIC_CONTROLLER
PUBLIC_CONTROLLER -> DYNAMIC_PUBLIC_RECEIPT
DYNAMIC_PUBLIC_RECEIPT -> SEALED_SCORER_CHECKER
SEALED_SCORER_CHECKER -> SEALED_REPORT_ONLY
```

All unlisted edges are forbidden. Especially forbidden are
`MTextHandoffV4 -> RENDERER|MODEL|COMMON_READER`,
`HandoffPublicV4.carrier -> RENDERER|MODEL`,
`SEALED_SCORER_CHECKER -> any upstream node`, and any raw handoff object to the
model. A controller implementation that uses a shared untyped object rather
than these projections fails source review.

### 2.5 Leakage tests

Register or extend the handoff closure test to inject each of the following at
the top level and every nested public record: source/manifest/authority/freeze
digest, root or hidden bit, condition/arm, split, transform, route ID, expected
answer, score, scorer/oracle digest or output, filename, error detail, timing,
session/cache key, renderer/parser/model identity, and receipt identity. Closed
schema validation MUST reject each injection. Mutations that copy any private
field into rendered system/user/template/token bytes, reader candidate order,
status, grants, padding, error text, request length, cache/session key, or tool
envelope MUST fail noninterference before model execution.

`M0V4-CPU-CONFORMANCE-08` may establish semantic projection conformance only.
It does not clear model use. The later exact rendered-byte/token/session test
remains mandatory.

## 3. Normative closure for `D-V4-DELAYED-TWIN-ENTITLEMENT`

### 3.1 Named visibility ancestor and fixture origin

For each `k in 0..31` and `h in {0,1}`, define the model-independent canonical
correct-acquisition branch:

```text
O40(k,h) = ordinary public BIT outcome at logical location 40 for E0,
           with value h

O41_ACQUIRE_SUCCESS(k,h) = ordinary public ACQUIRED outcome at logical
           location 41 produced by correct commit c_h, with public value
           {src:alias_k(C), rel:alias_k(R(07+h)), dst:alias_k(D)}
```

`O41_ACQUIRE_SUCCESS(k,h)` is the sole named **visibility ancestor** of the
h-dependent delayed treatment. “Visibility ancestor” is a byte-taint/causal
lineage relation; it does not replace the separately required independent
support evidence or turn a transform into evidence.

The frozen `DELAYED_ENTRY(k,h)` is derived by the reference compiler, without
model output, from the authentic old carrier plus the admitted new fact and
adjacency whose visibility lineage contains `O41_ACQUIRE_SUCCESS(k,h)`. Its
private `fixture_origin` is exactly
`SUPPLIED_CANONICAL_CORRECT_ACQUISITION`. Its live U-trajectory reference is
absent. Acquisition, retention, acquisition-to-use, persistent-write, and
online-learning endpoints for every D cell are `NA`.

### 3.2 Exact semantic-handoff divergence allowlist

At D-phase entry for fixed `k`, compare `h=0` and `h=1`. The two
`HandoffPublicV4` canonical byte trees MUST be equal at every JSON pointer
except these two complete fixed slots:

```text
/carrier/atoms/25     # public handle a19; the admitted nh record
/carrier/links/6      # public handle l06; the p4-to-nh authentic adjacency
```

Every differing leaf inside those slots MUST carry transitive visibility
lineage to `O41_ACQUIRE_SUCCESS(k,h)`. The slot handles, array lengths, slot
positions, outer carrier fields, carrier exposure values, cut, initial view,
delayed goal, action catalog, budgets, response schema, and padding bytes MUST
remain equal. No carrier-wide content hash, handoff digest, route ID, origin
label, event identity, or private provenance field may be inserted into the
public tree to spread the entitlement.

The private `handoff_public_sha256` and route bindings may differ because they
bind different immutable treatments, but they are outside actor/model
visibility and may not influence any public ordering, padding, error, cache,
or request byte.

### 3.3 First model-visible divergence and descendant closure

The initial rendered D-phase `ModelTurnPublicV4`, chat-template bytes, token
IDs, parser state, public action opportunities, session/cache state, and all
reader returns containing only old/null content MUST be byte-identical across
twins. The first permitted model-visible difference is exactly the nested
`atom` and/or `link` value in the first `MemoryReturnV4` produced by a READ
that returns slot `a19` and/or `l06`.

For that return, `status`, request fingerprint, anchor, cursor, grants,
repeat-count, outer shape, and padding remain twin-equal; neutral grants remain
`a19`/`l06`. The request fingerprint MUST be derived only from the public
query and repeat state, never from carrier contents or a private route.

After that entitled return, only its dynamic causal descendants may differ:
the model response, parsed public command, public transition/outcome, current
view, same-phase scratch, subsequent query chosen by that response, later
reader return reached through that query, and sealed behavioral receipt.
Static prompt bytes, action catalogs, budgets, private metadata, routing,
scoring rules, and oracle data do not become descendants merely because an
entitled return occurred.

If no READ returns `a19` or `l06`, the complete actor/model-visible D trace
MUST remain twin-identical until a later ordinary world outcome itself
separates the twins. A difference caused only by fixture identity, a carrier
hash, route, condition, timing, padding, error, cache, or hidden state is never
entitled.

### 3.4 Replacement acceptance test

Register:

```text
M0V5-DELAYED-ENTRY-OUTCOME-DESCENDANT-13
```

For all 32 `k`, both `h`, all registered delayed transforms, every legal
pre-action read schedule, all cursors/repeats, and both forced-equal and
policy-produced command continuations, it MUST prove:

1. only the two semantic handoff pointers above can differ at entry;
2. both carry the named O41 visibility lineage;
3. the initial rendered request is identical;
4. old/null reads are identical;
5. the first model-visible difference occurs only inside a returned `a19` or
   `l06` value;
6. non-descendant fields remain identical after that return;
7. a removed, forged, wrong-h, pre-O41, transform-created, or U-output-borrowed
   lineage rejects; and
8. all D acquisition/retention/learning endpoints remain `NA` and cannot be
   borrowed from AUTH U.

This is a narrow supplied-treatment entitlement. It is not retention evidence
and does not weaken paired-prefix noninterference elsewhere.

## 4. Normative closure for `D-V4-ZERO-V7-PROVENANCE`

### 4.1 Exact interpretation of zero reuse

Zero V7 runtime reuse is a finite provenance-and-capability rule, not an
attempt to infer copying from every coincident scalar. A PCFL value such as
`0`, `1`, `4`, `8`, `16`, a generic JSON key, or a standard-library idiom is
not V7 reuse merely because it also occurs in V7. It becomes a forbidden V7
edge only by one of the bounded predicates below.

The only component allowed to contain the registered V7 paths, hashes, and
identifiers for enforcement is the source-only `V7_BOUNDARY_GUARD` plus
governance deliberation/review artifacts. Materializer, checkers, fixtures,
runtime, tests, handoff, renderer, parser, model inputs, and scientific
receipts may not consume that metadata.

### 4.2 Frozen governance-only V7 identities

The guard binds these five V7 source-file identities:

| Path | SHA-256 |
|---|---|
| `feltcraft_symbolic_kernel/__init__.py` | `2274ed4d5ef1eaa63357f113a5a3f0f82a4321594c65596283e71601c68081e9` |
| `feltcraft_symbolic_kernel/kernel.py` | `c68771ec3d5f67193766cc56c16f152c5bc757a7e221c31a826b7649f2b69fdc` |
| `feltcraft_symbolic_kernel/report.py` | `41133956ad9f36842d439eea8df82f5f1407fb59e36b52a0510aa3dbd61921d3` |
| `feltcraft_symbolic_kernel/run.py` | `56f7e8d703bb7f3737f725d5b09c7ad3c12ce2a373308356c9c77b62a2b5b046` |
| `feltcraft_symbolic_kernel/test_kernel.py` | `d4a8a995be71a08413bdd718eebd25d3047a4c5b5edd52e3d1f3c715d3517219` |

It also binds these distinctive whole-artifact identities:

```text
f6f3181db906b915d4711fc701cac4aee464fdd9b21bd0dbb41c95dc976ca83b
  V7 change.json
4250f8fa1678fbb91f79803a9b14336fbf84d2554fddc5409673db2502cc1567
  V7 consensus.json
d67f446f7b4cb11024033c49fd8b1dcb75424e1f8bf7efb1a64cadbdb02c1fb5
  V7 human_ratification.json
1ed5411ee562f71bf0214f0e4763471d8b8ca748046aab377942a517823c84ec
  V7 scope_audit.json (passed:false negative evidence)
dce3fe74e5f4918f306dd365fad984bd3440c168348b92f7dbb5efa1652bccb4
  V7 golden_report.json
9db56cbb6df4f4d481269ffc480a81b2634a0996d4d51c3612dcbd9056638dca
  V5 golden_vectors.json inherited by the V7 lineage
```

Those identities may be cited to establish the denial and failed predecessor
authority only. No permission, code, result, semantic truth, or scientific
credit transfers.

### 4.3 Bounded denial predicates

For every candidate source row, declared dependency, resolved import, build
input, runtime read, subprocess, serialized object, fixture, and output, fail
closed if any one predicate is true:

1. **Resolved-path denial:** a normalized, symlink-resolved path is under
   `feltcraft_symbolic_kernel/` or
   `research_loop/changes/chg_20260901_feltcraft_symbolic_kernel_v7/`, or is
   exactly
   `research_loop/changes/chg_20260901_feltcraft_symbolic_kernel_v5/golden_vectors.json`.
2. **Module denial:** an import, package resource, reflection target, plugin,
   callback, entry point, subprocess module, or dynamically constructed module
   name equals `feltcraft_symbolic_kernel` or begins
   `feltcraft_symbolic_kernel.`.
3. **Whole-artifact denial:** a non-governance candidate/input/output has any
   SHA-256 listed in section 4.2 or embeds one of those whole artifacts as a
   byte-for-byte member.
4. **Declared-provenance denial:** a `SourceProvenanceRowV1` names a V7/V5
   denied path, hash, change ID, primitive, output, golden, receipt, audit, or
   derived translation as a source of executable semantics, expected values,
   fixtures, or tests.
5. **Distinctive-interface denial:** executable/test/fixture bytes address the
   V7-only interfaces or oracle vocabulary
   `enumerator_call`, `projection_call`, `checker_call`, `ALIGNMENTS`,
   `ALIGNMENT_AT`, `GRAPHS`, `GRAPH`, `CALIBRATIONS`, `CAL`, `TOP`, `LOCAL`,
   `RANDOM_SOURCE`, `MOTIF_SCHEMA`, `ORACLE`, or V7 `SK01` through `SK09` as a
   dependency or expected-result source. A governance denylist mention is the
   sole exception.
6. **Capability denial:** the Authority P read allowlist, import graph, file
   descriptors, package data, environment, configuration, argv, working
   directory, subprocess surface, network surface, or deserialization graph
   can resolve any denied path/module/artifact, even if the normal path claims
   not to use it.
7. **Actor/model denial:** any V7 path, digest, protocol/change ID, primitive
   name, descriptor/role, error code, output, golden, audit value, or boundary
   decision reaches a public carrier, view, reader return, tool envelope,
   rendered bytes, tokenizer input, model/session/cache state, public error,
   timing surface, or scientific result.

No heuristic “copied constant” predicate exists outside these seven rules.
Short or ordinary coincident values are permitted only when their provenance
row points to the V5 PCFL normative specification or an identified language/
standard-library primitive and no denial predicate above is true.

### 4.4 Exact source-provenance row

Every executable, schema, semantic-table, checker, fixture, mutation, test,
and runtime-manifest entry in `NormativeSourceManifestV1` binds:

```text
SourceProvenanceRowV1 := {
  schema_version:1,
  artifact_type:"pcfl_m0_source_provenance",
  logical_path:repo_relative_path,
  source_sha256:hex64,
  authored_for_change_id:"chg_20260910_pcfl_m0_mtext_bound_v5",
  source_authoring_grant_sha256:hex64,
  derivation_sources:[{
    kind:"PCFL_V5_NORMATIVE"|"LANGUAGE_STANDARD"|"STANDARD_LIBRARY",
    identifier:string,
    path:null|repo_relative_path,
    sha256:null|hex64
  }, ...],
  v7_runtime_derivation:false,
  v7_oracle_derivation:false,
  author_attestation:string
}
```

Rows are closed, sorted by `(kind,identifier,path,sha256)`, and contain at
least one derivation source. `path` and `sha256` are both null for a named
language or standard-library primitive. Governance-only V7 evidence does not
appear in these rows; it remains in `v7_boundary_v4.json`. An attestation is
necessary provenance evidence but is not sufficient: all static capability,
resolved-path, import, whole-artifact, and mutation tests still apply.

The V7 boundary manifest itself is exactly a zero-reuse policy:

```text
V7BoundaryV1 := {
  schema_version:1,
  artifact_type:"pcfl_m0_v7_boundary",
  dependency:"FELTCRAFT_SYMBOLIC_KERNEL_V7",
  decision:"ZERO_RUNTIME_REUSE",
  reused_primitives:[],
  governance_only_source_identities:[{path:repo_relative_path,sha256:hex64},...],
  distinctive_artifact_sha256:[hex64,...],
  denied_path_prefixes:[repo_relative_path,...],
  denied_exact_paths:[repo_relative_path,...],
  denied_module_prefixes:["feltcraft_symbolic_kernel"],
  denied_interface_identifiers:[string,...],
  coincident_value_rule:"NO_EDGE_WITHOUT_A_BOUND_DENIAL_PREDICATE"
}
```

All arrays use exactly the values in sections 4.2–4.3, sorted bytewise and
deduplicated. The guard may read this policy but MUST NOT open a denied V7/V5
path. The materializer/checkers/runtime receive only a passed preflight bit and
the exact PCFL read allowlist, never this V7 metadata.

### 4.5 Replacement acceptance test

Retain `M0V4-ZERO-V7-RUNTIME-REUSE-01` with the following exact interpretation:

> Pass only when the closed source provenance manifest contains no V7-derived
> row; the Authority P capability closure cannot resolve any denied path,
> module, artifact, subprocess, resource, environment, configuration,
> serialization, or output edge; no V7 identity reaches actor/model bytes; and
> every injected violation of predicates 1–7 fails before preparation. Do not
> reject independently derived ordinary coincident values absent a bounded
> denial predicate.

The mutation corpus MUST inject at least one instance of each predicate,
including a symlink into the V7 tree, dynamically constructed import,
`python -m feltcraft_symbolic_kernel.run`, package-resource read, exact V7
whole-file copy, embedded golden report, V7-derived expected vector with a
declared provenance row, denied hash in a model-visible field, serialized
callback, environment-supplied V7 path, and a harmless independently derived
coincident scalar. Every forbidden mutation rejects; the harmless scalar MUST
pass. This is the deterministic distinction V4 lacked.

## 5. Resolution map and remaining boundary

| V4 resolution | Exact V5 closure in this advisory |
|---|---|
| `D-V4-SOURCE-AUTHORITY-CIRCULARITY` | Disjoint Authority S/P schemas, exact pre-authoring path plan, post-authoring byte manifest, acyclic graph, and `M0V5-SOURCE-AUTHORING-VS-PREPARATION-AUTHORITY-12`. |
| `D-V4-HANDOFF-PROJECTION-CLOSURE` | Closed nonoverlapping handoff schemas, field allowlists, typed projections, one-way consumer graph, and leakage mutations. |
| `D-V4-DELAYED-TWIN-ENTITLEMENT` | Named `O41_ACQUIRE_SUCCESS` visibility ancestor, two-slot semantic exception, first-return model-visible boundary, causal descendant law, and `M0V5-DELAYED-ENTRY-OUTCOME-DESCENDANT-13`. |
| `D-V4-ZERO-V7-PROVENANCE` | Finite path/module/hash/interface/capability predicates, exact provenance rows, mutation corpus, and explicit coincident-value safe case. |

Adopting this text authorizes nothing. The successor must hash-bind these
choices, integrate the other V4 repairs, undergo the full five-role path, and
receive exact human ratification at each named authority boundary. No M0
passage can clear M-TEXT; no supplied delayed fixture can support retention or
online learning; and no V7 governance citation can become a runtime edge.
