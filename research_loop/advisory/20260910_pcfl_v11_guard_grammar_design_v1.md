# PCFL M0 + M-TEXT-SUPPLIED V11 — guard/grammar design repair

Date: 2026-09-10

Status: **source-only design advisory for a future fresh architecture
deliberation; not authority and not an implementation**. This file leaves
`research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate.md`
unchanged. It creates no plan JSON, source, manifest, provenance row, grant,
review, ratification, guard, observation bundle, fixture, receipt, prepared
artifact, root, data, model result, or scientific result. It authorizes no
source or governance-tool authoring, parsing, import, execution,
materialization, fixture/root/data generation, checker/test/model/tokenizer/
benchmark/training/GPU work, resource acquisition, claim, release, or
submission.

## 1. Finding and narrow repair boundary

The current integration proposal is fixed for this review at:

```text
INTEGRATION_PROPOSAL_PATH_C11 =
  "research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate.md"
INTEGRATION_PROPOSAL_SHA256_C11 =
  "586500e72c6e03da5f9e4e9800094017888e1e4648bb656a2caad82335a8b5bc"
DESIGN_PATH_C11 =
  "research_loop/advisory/20260910_pcfl_v11_guard_grammar_design_v1.md"
```

`DESIGN_SHA256_C11` means the lowercase SHA-256 obtained only after these
advisory bytes are sealed. It is deliberately not stored in this file. Every
future object below must contain the actual rehashed value, never this symbol
or a guessed value.

Four defects remain in the current proposal:

1. its six-field future plan has no direct path/hash binding to the source
   design scope that source authors are meant to follow;
2. it requires a `PCFL_V11_NORMATIVE` root for every non-boundary provenance
   row but leaves all twenty-two root arrays to the author;
3. it delegates the inert observation grammar to candidate bytes in
   `source/provenance_contract_v4.json`; and
4. it makes candidate member `source/prepare_v4.py` the executing guard even
   though the effective authority repair requires the guard to be an
   authority-controller operation, not imported or executed candidate code.

The minimal coherent repair is one future, human-ratified successor that
adopts sections 2--6 together. Adopting only a subset is `REWORK`. Nothing in
this advisory changes the 24 plan rows, 23 manifest members, 22-path pass
projection, 32 acceptance-test records, 18 conditions, 501 slots per ordinary
root, 148,224 generated tokens per ordinary root, 16/32/16 root split,
endpoints, models, retries, gates, or claim ceiling.

## 2. Direct plan-to-scope closure

### 2.1 Exact plan extension

The future C11 `SourceAuthoringPlanV1` must retain the current proposal's exact
six fields and their values and add exactly these four fields, yielding ten
top-level fields and no others:

```text
scope_bindings
nonboundary_provenance_catalog
observation_grammar_binding
trusted_guard_binding
```

The existing `entries` array remains exactly 24 rows/23 members. The existing
`governance_inputs` remains the exact one-entry V11 denial-corpus singleton.
None of the four new fields is an entry, governance input, manifest member,
manifest output, or source-authoring write target.

`scope_bindings` is exactly this bytewise-role-sorted two-row array:

```text
[
  {
    role:"V11_GUARD_GRAMMAR_DESIGN",
    logical_path:DESIGN_PATH_C11,
    sha256:DESIGN_SHA256_C11
  },
  {
    role:"V11_INTEGRATION_PROPOSAL",
    logical_path:INTEGRATION_PROPOSAL_PATH_C11,
    sha256:INTEGRATION_PROPOSAL_SHA256_C11
  }
]
```

The rows and every nested object are closed. Both paths must resolve lexically
to regular repository files at those exact paths and rehash to those exact
digests without opening any denied target. The future source-only consensus
must bind both rows and stop at `human_required`. A later human
`SourceAuthoringGrantV1[C11]` continues to bind the plan directly through
`source_authoring_plan_sha256`; because the plan now binds both scope objects,
no new grant field is necessary for source-authoring scope closure. The grant
is invalid unless its evidence and consensus designate both rows as the exact
human-bound V11 normative source-design scope. A context-list mention, workflow
attachment, prose reference, predecessor hash, or consensus-only reference
does not substitute for these plan fields.

`observation_grammar_binding` is exactly:

```text
{
  identifier:"PCFL_V11_INERT_OBSERVATION_GRAMMAR_V1",
  scope_role:"V11_GUARD_GRAMMAR_DESIGN"
}
```

It resolves only through the first exact `scope_bindings` row. Copying the
grammar into a candidate member, pointing it at `provenance_contract_v4.json`,
or accepting a second grammar authority rejects.

### 2.2 Direct-binding acceptance and rejection

An eligible plan passes this part only when all ten top-level fields are
present, both scope hashes independently rehash, the two roles/paths/hashes
are exact, and the plan hash is the same hash directly named by the C11 source
grant, review grant, exact-byte ratification, and later preparation grant.

The future mutation set must reject independently: a missing row; an extra
row; swapped roles; reordered rows; a path-only binding; a hash-only binding;
a wrong current-proposal hash; a wrong sealed-design hash; a symlink; a scope
row placed in `governance_inputs`; a scope file made writable by Authority S;
and any grant/review/ratification/preparation object that binds a different
plan hash.

## 3. Exact twenty-two-row non-boundary provenance catalog

### 3.1 Closed catalog rule

`nonboundary_provenance_catalog` is an array of exactly 22 closed rows:

```text
{
  logical_path:one exact non-boundary member path,
  derivation_sources:exactly CATALOG_SOURCES(identifier)
}
```

Rows are duplicate-free and bytewise sorted by `logical_path`. Define the
literal expansion, not an implementation-time macro:

```text
CATALOG_SOURCES(I) = [
  {
    kind:"PCFL_V11_NORMATIVE",
    identifier:"V11-GUARD-GRAMMAR-DESIGN-V1",
    path:DESIGN_PATH_C11,
    sha256:DESIGN_SHA256_C11
  },
  {
    kind:"PCFL_V11_NORMATIVE",
    identifier:I,
    path:INTEGRATION_PROPOSAL_PATH_C11,
    sha256:INTEGRATION_PROPOSAL_SHA256_C11
  }
]
```

The displayed order is the required inherited tuple order. There are exactly
two derivation sources per non-boundary row. No language-standard,
standard-library, third normative root, null path/hash, optional addition, or
author-selected identifier is permitted. Both sources become
`PCFL_V11_NORMATIVE` only if a fresh five-role deliberation and exact human
scope/grant binding adopt them; this advisory by itself does not do so.

The complete path-to-`I` catalog is:

| exact logical path | exact `I` |
|---|---|
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/acceptance_tests.json` | `V11-SOURCE-SCOPE-ACCEPTANCE-TESTS` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/cas_freeze_contract_v4.json` | `V11-SOURCE-SCOPE-CAS-FREEZE-CONTRACT` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/check_axiomatic_v4.py` | `V11-SOURCE-SCOPE-AXIOMATIC-CHECKER` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/check_constructive_v4.py` | `V11-SOURCE-SCOPE-CONSTRUCTIVE-CHECKER` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/claim_disposition_v4.json` | `V11-SOURCE-SCOPE-CLAIM-DISPOSITION` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/delayed_twin_entitlement_v4.json` | `V11-SOURCE-SCOPE-DELAYED-TWIN-ENTITLEMENT` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/endpoint_gate_registry_v4.json` | `V11-SOURCE-SCOPE-ENDPOINT-GATE-REGISTRY` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/failure_precedence_v4.json` | `V11-SOURCE-SCOPE-FAILURE-PRECEDENCE` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/handoff_consumer_graph_v4.json` | `V11-SOURCE-SCOPE-HANDOFF-CONSUMER-GRAPH` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/handoff_projection_allowlist_v4.json` | `V11-SOURCE-SCOPE-HANDOFF-PROJECTION-ALLOWLIST` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/handoff_public_v4.schema.json` | `V11-SOURCE-SCOPE-HANDOFF-PUBLIC-SCHEMA` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/integrated_contract.md` | `V11-SOURCE-SCOPE-INTEGRATED-CONTRACT` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/materialize_v4.py` | `V11-SOURCE-SCOPE-MATERIALIZER` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/mtext_handoff_v4.schema.json` | `V11-SOURCE-SCOPE-MTEXT-HANDOFF-SCHEMA` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/mutation_fixtures.json` | `V11-SOURCE-SCOPE-MUTATION-FIXTURES` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/object_schemas_v4.json` | `V11-SOURCE-SCOPE-OBJECT-SCHEMAS` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/prepare_v4.py` | `V11-SOURCE-SCOPE-PREPARATION-ENTRYPOINT` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/provenance_contract_v4.json` | `V11-SOURCE-SCOPE-PROVENANCE-CONTRACT` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/resource_roster_v4.json` | `V11-SOURCE-SCOPE-RESOURCE-ROSTER` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/runtime_manifest_v4.json` | `V11-SOURCE-SCOPE-RUNTIME-MANIFEST` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/semantic_table_v4.json` | `V11-SOURCE-SCOPE-SEMANTIC-TABLE` |
| `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/transition_table_v4.json` | `V11-SOURCE-SCOPE-TRANSITION-TABLE` |

For each non-boundary manifest entry, its external
`SourceProvenanceRowV1[C11].derivation_sources` must be byte-for-byte equal to
the catalog array for the same `logical_path`. The boundary path is forbidden
from this catalog and retains only the already ratified exact two-source
corpus/repair array. All other `SourceProvenanceRowV1[C11]` fields, false V7
flags, sorting, anti-laundering checks, and grant-hash-interpolated attestation
remain unchanged.

### 3.2 Catalog acceptance and rejection

Acceptance requires set equality with the 22-path projection, exact array
equality for all 22 manifest rows, absence of the boundary, and successful
rehashing of the two common normative paths. Independent mutations must cover
a missing path, extra path, duplicate, reordering, boundary insertion, wrong
identifier, reused identifier for the wrong path, null or wrong hash, source
root replacement, one-source row, third source, optional language source,
catalog/manifest mismatch, and a row whose source bytes were not explicitly
human-bound as V11 normative scope.

## 4. Deterministic inert observation grammar

### 4.1 Trust location and canonical primitives

`PCFL_V11_INERT_OBSERVATION_GRAMMAR_V1` is defined by this section and is
therefore bound through `DESIGN_PATH_C11`/`DESIGN_SHA256_C11`, never by a
candidate member. `source/provenance_contract_v4.json` and
`source/runtime_manifest_v4.json` may declare data conforming to it but cannot
define, amend, select, or version the grammar.

Let `JCS1(x)` be RFC 8785/JCS UTF-8 bytes for closed JSON value `x` followed
by exactly one LF, and let `H(x)` be lowercase SHA-256 of `JCS1(x)`. All byte
offsets below are zero-based half-open offsets into the authenticated UTF-8
member bytes. All arrays are duplicate-free and sorted by their displayed
identity tuple. An out-of-range span, duplicate key, invalid UTF-8, non-NFC
string, CR byte, NUL byte, ambiguous normalization, schema-extra field, or
noncanonical JSON rejects.

The trusted guard handles media types exactly as follows:

1. `application/json`: require JCS plus one LF and the exact closed source
   schema. JSON is inert data and creates no capability edge merely because a
   scalar resembles a path, module, digest, or corpus value. Exact typed
   identity fields and complete/embedded byte objects are still checked under
   the ratified corpus/repair matchers.
2. `text/markdown`: require UTF-8, NFC strings, LF line endings, exactly one
   terminal LF, and no NUL. Markdown is never rendered, executed, linked,
   included, or treated as a capability declaration at guard stage; its whole
   bytes and explicitly inventoried embedded objects remain denial inputs.
3. `text/x-python`: require the same UTF-8/NFC/LF rules and acceptance by the
   exact restricted profile in section 4.2. It is parsed as inert syntax by
   the separately bound trusted guard and is never imported or executed by
   the guard.

### 4.2 Exact restricted Python profile

Unrestricted Python cannot have a complete, decidable static capability
inventory. C11 therefore cannot honestly set
`unresolved_dynamic_observation_count:0` for unrestricted source. The minimal
sound repair is the following closed profile; rejection or claim withdrawal,
not heuristic inference, is required if source authors need more power.

The only permitted concrete AST node classes are:

```text
Add And AnnAssign Assert Assign AugAssign BinOp BitAnd BitOr BitXor BoolOp
Break Call Compare Constant Continue Dict DictComp Div Eq ExceptHandler Expr
FloorDiv For FormattedValue FunctionDef GeneratorExp Gt GtE If IfExp In
Invert Is IsNot JoinedStr LShift List ListComp Load Lt LtE Mod Module Mult
Name Not NotEq NotIn Or Pass Pow RShift Raise Return Set SetComp Slice Starred
Store Sub Subscript Try Tuple UAdd USub UnaryOp While arg arguments
comprehension keyword
```

Every node class not listed is forbidden. In particular `Import`,
`ImportFrom`, `Attribute`, `ClassDef`, `Lambda`, `With`, `AsyncWith`,
`AsyncFunctionDef`, `Await`, `Yield`, `YieldFrom`, `Global`, `Nonlocal`,
`Delete`, `NamedExpr`, and every `Match` node reject.

Additional closed rules are:

- module scope contains only literal `Name` assignments and `FunctionDef`
  nodes; it contains no call or other executable statement;
- every function is module-level, undecorated, unannotated, has no defaults,
  variadic argument, keyword-only argument, or type comment, and has a unique
  name not in either reserved-name set below;
- an assignment may not bind or rebind a function name, permitted builtin, or
  `pcfl_capability`; a name beginning and ending with `__` rejects everywhere;
- every `Call.func` is a `Name` resolving statically to exactly one module-
  level function, one permitted builtin, or `pcfl_capability`; calls through
  a parameter, assignment, subscript, returned value, or any other expression
  reject;
- the permitted builtin call names are exactly
  `abs`, `all`, `any`, `bool`, `bytes`, `chr`, `dict`, `enumerate`, `filter`,
  `float`, `format`, `frozenset`, `hex`, `int`, `isinstance`, `issubclass`,
  `iter`, `len`, `list`, `map`, `max`, `min`, `next`, `oct`, `ord`, `pow`,
  `range`, `repr`, `reversed`, `round`, `set`, `slice`, `sorted`, `str`,
  `sum`, `tuple`, and `zip`;
- the only permitted raised exception names are `AssertionError` and
  `ValueError`; neither may be caught through a dynamic type expression;
- function inputs and `pcfl_capability` results are limited to finite trees of
  null, boolean, finite integer, finite binary64 number, NFC string, bytes,
  list, and string-keyed dictionary. No callable, module, class, descriptor,
  iterator with effects, file object, socket, process, or foreign object may
  enter this value boundary; and
- after guard pass, the authority controller, not candidate code, injects the
  sole reserved function `pcfl_capability`. Before pass no candidate member is
  executed.

Each `pcfl_capability` call has exactly three positional `Constant` string
arguments and no keyword or starred argument:

```text
pcfl_capability(SURFACE, TARGET_KIND, TARGET_VALUE)
```

`SURFACE` is exactly one of:

```text
ARGV
AUTHORITY_P_READ_ALLOWLIST
CONFIGURATION
DESERIALIZATION_GRAPH
ENVIRONMENT
FILE_DESCRIPTOR
IMPORT_GRAPH
NETWORK
PACKAGE_DATA
SUBPROCESS
WORKING_DIRECTORY
```

`TARGET_KIND` is exactly one of `PATH`, `MODULE`, `DIGEST`, `RESOURCE`,
`SUBPROCESS`, or `NETWORK`; `SURFACE_ROOT` is guard-generated and is forbidden
as a call argument. `TARGET_VALUE` is a nonempty NFC string. A `PATH` value
must be a normalized repository-relative POSIX path: no leading slash,
backslash, NUL, empty component, `.` component, or `..` component. Its
`resolved_target` is exactly that lexical value; the guard never follows,
stats, opens, or hashes the target. A `MODULE` value must match
`[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*`. Every other kind uses
the exact NFC value without case folding, alias resolution, or coercion.

This profile deliberately moves all operating-system and interpreter-adjacent
effects behind a controller-supplied literal gateway. It does not alter any
scientific condition; it constrains only how future source may request an
already authorized effect. If this restriction cannot express the intended
source, the integration is `REWORK`; silently widening the profile is
forbidden.

### 4.3 Deterministic observation construction

For every permitted `pcfl_capability` call, let `origin`, `start`, and `end`
be the authenticated source path and exact call-expression byte span. Let
`span_sha256` be SHA-256 of those raw bytes. Construct:

```text
call_identity = {
  origin_logical_path:origin,
  byte_start:start,
  byte_end:end,
  surface:SURFACE,
  target_kind:TARGET_KIND,
  target_value:TARGET_VALUE
}
observation_id = H(call_identity)
```

Create exactly one capability target node for each distinct
`(TARGET_KIND,TARGET_VALUE)`:

```text
node_id = H({target_kind:TARGET_KIND,target_value:TARGET_VALUE})
```

Create the eleven required root nodes with
`node_id=H({surface:SURFACE,target_kind:"SURFACE_ROOT",
target_value:SURFACE})` and exactly one edge from the corresponding surface
root to each call's target node. Duplicate calls share the target node but
retain distinct observations. These rules create the complete finite
capability graph; no candidate-provided node ID or edge is trusted.

For `TARGET_KIND:"PATH"`, emit one `path_observations` row using the values
above and:

```text
resolution_evidence_sha256 = H({
  lexical_path:TARGET_VALUE,
  resolved_target:TARGET_VALUE,
  rule:"LEXICAL_NORMALIZED_REPOSITORY_RELATIVE_POSIX_V1"
})
```

For `TARGET_KIND:"MODULE"`, emit one `module_observations` row with
`surface:SURFACE`, `module_identity:TARGET_VALUE`, and
`source_span_sha256:span_sha256`. Other target kinds occur in the capability
graph and do not fabricate a path or module row.

`source/runtime_manifest_v4.json` must contain one closed
`DeclaredObservationGraphV1` value with exactly these fields:

```text
{
  schema_version:1,
  artifact_type:"pcfl_v11_declared_observation_graph",
  change_id:"chg_20260910_pcfl_m0_mtext_bound_v11",
  python_profile:"PCFL_V11_INERT_OBSERVATION_GRAMMAR_V1",
  capability_calls:[call_identity,...],
  embedded_members:[{
    parent_logical_path:repo_relative_path,
    member_name:nonempty_nfc_string,
    member_type:nonempty_nfc_string,
    byte_offset:u64,
    byte_length:u64
  },...]
}
```

The guard-derived `capability_calls` array and declared array must be
byte-identical after JCS canonicalization. For every embedded declaration the
guard authenticates the parent manifest identity, verifies an in-bounds,
nonoverlapping, unambiguous half-open range, hashes the raw slice, and emits
the inherited `embedded_member_observations` row. Every archive, package-data,
deserialized, fixture, static-literal, or other reachable byte container must
have such an exact row; an opaque, undeclared, overlapping, out-of-range, or
digest-inconsistent object rejects. Provenance edges are reconstructed only
from the authenticated external manifest rows. Candidate-declared provenance
cannot add, remove, or rewrite an edge.

The trusted guard then fills the already ratified
`AuthenticatedDenialObservationBundleV1` fields from the authenticated plan,
manifest, source bytes, external provenance, grammar-derived observations,
and computed embedded rows. Array equality, graph finiteness/acyclicity, all
eleven roots, corpus matching, and zero unresolved observations are mandatory.
Any syntax outside the profile, unmatched declaration, unclassified call,
unknown input object, or dynamic target yields `closure_status:"REJECT"`,
`unresolved_dynamic_observation_count` greater than zero, private status
`SOURCE_BOUNDARY_REJECTED`, and no projection.

### 4.4 Required grammar fixtures

The future exact mutation bytes must independently cover: one literal gateway
call for each of the eleven surfaces and six target kinds; duplicate call/
shared-node behavior; a clean local-function/builtin-only program; import;
attribute call; dunder name; dynamic callee; aliased/rebound callee; nonliteral
surface, kind, or value; unknown surface/kind; absolute/dot-dot/backslash path;
malformed module; forbidden AST node; executable module-scope statement;
callable input; undeclared call; declared-but-absent call; source-span shift;
missing/overlapping/out-of-range embedded member; opaque archive; forged
provenance edge; and a graph with a missing surface root, extra edge, cycle,
or unresolved node. Every mutation is terminal and no multi-defect fixture
substitutes for an individual case.

## 5. Trusted guard separated from `prepare_v4.py`

### 5.1 Exact identities and sole supersession

The future trusted guard identity is:

```text
TRUSTED_GUARD_PATH_C11 =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/trusted_v7_boundary_guard_v1.py"
TRUSTED_GUARD_ACTOR_C11 = "V7_BOUNDARY_GUARD"
```

Its digest is a future `hex64` computed only after separately authorized bytes
exist and are sealed. It is not one of the 24 plan entries, 23 manifest
members, 22 projected paths, or the denial-corpus governance-input singleton.
It is never writable under `SourceAuthoringGrantV1[C11]` and never imported
from the candidate tree.

`trusted_guard_binding` in the future plan is exactly:

```text
{
  logical_path:TRUSTED_GUARD_PATH_C11,
  sha256:future_rehashed_hex64,
  media_type:"text/x-python",
  actor:"V7_BOUNDARY_GUARD",
  candidate_member:false,
  source_plan_entry:false,
  source_authoring_writable:false
}
```

The `V11_V7_GUARD_SOURCE` role in the eventual 23-role census moves to
`TRUSTED_GUARD_PATH_C11`; no role is added and the census remains 23 rows.
`source/prepare_v4.py` remains the 23-member plan's
`PREPARATION_ENTRYPOINT`, remains one of the 22 pass-projected paths, and
remains the `AuthenticatedDenialObservationBundleV1.analyzer_logical_path`
whose manifest digest is stored as `analyzer_source_sha256`. Those two bundle
fields identify the candidate entrypoint being analyzed; they do not identify
or authorize the executable guard.

This is the sole necessary semantic supersession of provenance repair v1
section 5: replace “the exact analyzer source that will populate it” with “the
separately bound trusted governance guard that will populate it while treating
the manifest-member analyzer/entrypoint as inert analyzed bytes.” The repair's
closed bundle schema, requirement that its `analyzer_logical_path` be a
non-boundary member, and all completeness laws remain unchanged. The current
integration proposal's statement that `prepare_v4.py` is the “sole analyzer
and guard source path” is rejected and must not survive a successor.

### 5.2 Direct execution binding and receipt

The later human `PreparationExecutionGrantV1[C11]` must directly bind, as
closed fields rather than prose:

```text
source_authoring_plan_sha256
normative_source_manifest_sha256
exact_byte_ratification_sha256
trusted_guard_logical_path
trusted_guard_source_sha256
observation_grammar_logical_path
observation_grammar_source_sha256
guard_runtime_executable_sha256
guard_runtime_ast_library_sha256
```

The two grammar fields are exactly `DESIGN_PATH_C11` and
`DESIGN_SHA256_C11`; the two guard fields equal the plan's
`trusted_guard_binding`; and both runtime hashes are exact independently
reviewed bytes selected before the grant. A version string, executable name,
ambient `PATH`, current interpreter, lockfile, or “Python 3” label cannot
replace either runtime digest.

Substage zero invokes only the bound trusted guard/runtime. The guard may read
the exact governance inputs, boundary, plan, manifest, external rows, and 22
non-boundary members as inert bytes. It may parse but may not import or execute
any candidate member. In particular it never invokes `prepare_v4.py`. Only
after an exact pass projection may a later substage already named by the same
grant invoke the projected preparation entrypoint.

The governance-private guard receipt must add the following exact execution
binding around the unchanged authenticated bundle and inherited pass/fail
facts:

```text
TrustedV7GuardExecutionBindingV1[C11] := {
  schema_version:1,
  artifact_type:"pcfl_v11_trusted_v7_guard_execution_binding",
  change_id:"chg_20260910_pcfl_m0_mtext_bound_v11",
  preparation_execution_grant_sha256:hex64,
  source_authoring_plan_sha256:hex64,
  normative_source_manifest_sha256:hex64,
  trusted_guard_logical_path:TRUSTED_GUARD_PATH_C11,
  trusted_guard_source_sha256:hex64,
  observation_grammar_logical_path:DESIGN_PATH_C11,
  observation_grammar_source_sha256:DESIGN_SHA256_C11,
  guard_runtime_executable_sha256:hex64,
  guard_runtime_ast_library_sha256:hex64,
  authenticated_observation_bundle_sha256:hex64,
  passed:boolean,
  private_failure_status:null|"SOURCE_BOUNDARY_REJECTED",
  projection_sha256:null|hex64
}
```

Every object is closed. On pass, `passed:true`, failure status is null, and
`projection_sha256` hashes the exact inherited four-field/22-path projection.
On failure, `passed:false`, the status is exactly
`SOURCE_BOUNDARY_REJECTED`, and `projection_sha256` is null because no
projection exists. This binding is not public and reaches no candidate,
preparation, model, cache/index, error/timing, receipt, result, or claim sink.

Independent guard mutations must cover: using `prepare_v4.py` as the invoked
guard; a guard path/hash mismatch; runtime or AST-library hash mismatch;
ambient-interpreter substitution; candidate import; candidate execution;
denied-target read/stat/hash; source-grant write access to the guard; a guard
not present in the final census; a bundle naming a nonmember analyzer; a
receipt binding different plan/manifest/grammar bytes; second semantic
consumer; pass with missing projection; fail with any projection; public
failure detail; retry; and reserve substitution.

## 6. Authority and impossibility disposition

The following facts are exact:

1. **Current authority is insufficient.** The ratified corpus sentence allows
   only governance-input binding and proposal rework. It does not authorize
   writing, hashing, parsing, reviewing, or executing
   `TRUSTED_GUARD_PATH_C11`, any candidate source, any plan JSON, or any
   fixture/receipt.
2. **A trust bootstrap is missing.** No exact guard source/runtime path/hash is
   bound by the effective repair stack. Unless a pre-existing independently
   ratified controller is supplied and adopted by exact hash, creating the
   proposed governance guard requires a new, narrowly closed human
   governance-tool-authoring grant whose only writable path is
   `TRUSTED_GUARD_PATH_C11`, followed by independent exact-byte review and
   human exact-byte ratification of that tool before the C11 source plan or
   preparation grant can bind it. `SourceAuthoringGrantV1[C11]` cannot be
   widened to perform this write.
3. **The schema/path changes are material.** Expanding the plan from six to
   ten top-level fields, moving the guard-source census path, imposing the
   restricted Python profile, adding direct preparation-grant runtime fields,
   and superseding who populates the V1 bundle are architecture, visibility,
   and acceptance-test changes. They require fresh-context interpretations,
   adversarial cross-critique, adjudicated consensus, and explicit human
   ratification of exact bytes/scope before any tool or candidate authoring.
4. **Unrestricted completeness is impossible.** For unrestricted Python, a
   finite inert scanner cannot decide every dynamically constructed path,
   import, resource, subprocess, network, deserialization, environment,
   configuration, argv, file-descriptor, working-directory, or package-data
   effect. The honest choices are the exact restricted profile above or
   withdrawal of the complete-closure/zero-unresolved claim. A heuristic
   scanner, author assertion, or candidate-defined grammar cannot close the
   blocker.
5. **The inherited one-member-analyzer and noncandidate-guard requirements
   cannot both mean “execute `prepare_v4.py`.”** They become consistent only
   through the explicit analyzed-entrypoint/executing-guard split in section
   5. Without human ratification of that narrow supersession, the integration
   remains `REWORK`.

The minimum legal order is therefore:

```text
this design advisory
  -> fresh five-role design deliberation and adversarial cross-critique
  -> explicit human ratification of the chosen exact design
  -> either bind an already ratified trusted guard by exact hash,
     or separate human governance-tool-authoring grant
  -> independent guard-tool byte review and exact human ratification
  -> future ten-field C11 source plan binds scope/catalog/grammar/guard
  -> fresh C11 source-only deliberation ending human_required
  -> separate human SourceAuthoringGrantV1[C11]
  -> inert candidate author/hash/manifest only
  -> separate review, source consensus, exact-byte ratification
  -> separate human PreparationExecutionGrantV1[C11]
  -> trusted external guard at substage zero
  -> only on pass, later already-authorized preparation substages
```

No completion implies the next authority. Failure at any binding, grammar,
catalog, provenance, runtime, or guard check is terminal for the attempt,
emits no projection, and authorizes no retry or reserve substitution.

## 7. Stop boundary

This advisory is the only new file proposed by this act. The current V11
candidate remains byte-for-byte unchanged. This file specifies future exact
objects but instantiates none of them. It reads no denied target and performs
no source authoring, tool authoring, hash generation for future bytes,
candidate parsing, import, execution, preparation, materialization,
fixture/root/data generation, checker/test/model/tokenizer/benchmark/training/
GPU work, resource acquisition, scientific execution, claim, release, or
submission.
