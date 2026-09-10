# PCFL V10 authority and delayed-baseline exact repair — v1

Date: 2026-09-10

Status: **source-only advisory responding to the human-ratified V9 rework**.
This file authorizes no source authoring, source import, interpreter parsing or
syntax checking, execution, preparation, implementation, materialization,
fixture/root/data generation, model/tokenizer use, benchmark, training,
LoRA/adapter/checkpoint work, parenting, GPU use, resource acquisition,
scientific claim, release, or submission.

## 0. Exact disposition and scope

The controlling V9 critique is SHA-256
`e92e461fe8e37ed22353ffdefe0929afb98e1d59bb62643d138093a95ffbd4a5`.
The controlling V9 consensus is SHA-256
`9e2066e1782a627e3fab15e179f1e15c33dc829b51076dbdd52556c5053176cf`,
has `recommendation="rework"`, and stops at `state="human_required"` with
implementation forbidden. This advisory resolves exactly:

- `D-V9-DELAYED-BASELINE-ENTITLEMENT` /
  `CRIT-V9-002-DELAYED-BASELINE-ENTITLEMENT-CONFLICT`;
- `D-V9-SOURCE-GRANT-BINDING` /
  `CRIT-V9-003-SOURCE-GRANT-SCHEMA-BINDING`; and
- `D-V9-SOURCE-AUTHORING-NOT-BYTE-RATIFICATION` /
  `D-V9-AUTHORING-IS-NOT-EXACT-BYTE-RATIFICATION`.

It does not dispose `D-V9-REGISTRY-CLOSURE`, `D-V9-ALGEBRA-PRIOR`,
`D-V9-PREASSEMBLED-PATH`, `D-V9-RENDERED-BRANCH-BOUNDARY`,
`D-V9-PROVENANCE-POSITIVES`, `D-V9-RESOURCE-FACTORIAL`,
`D-V9-CLAUSE-DISPOSITIONS`, or `D-V9-V7-GUARD-EXCEPTION`. Those remain
`REWORK` requirements for a successor packet. The four already resolved V9
claim limitations remain exact.

The inherited authority/handoff clauses controlling this repair are the V5
authority and delayed-twin advisory at SHA-256
`ae74fae9516fba5a699514674fd2299ec3130eca7814be723ccc5717258fcb2a`,
the V6 baseline projection advisory at SHA-256
`12960868a1cafb820e33600482866a6387538280e8baeb698d59c8a4072d44ee`,
the V7 baseline exact closure at SHA-256
`6ca612e41e3462ca6997cabcd089439a8d24be06ca7d37b5e29183ec362dd272`,
and the V8 repeat/null closure at SHA-256
`5c5321a7d208830a4f1c2fd5b04669ca56207e6403d57a68483954fe2057d597`.
This advisory has precedence only for the three dispositions named above and
their directly dependent schemas, fixtures, tests, and boundary statements.

## 1. One supplied delayed public-event basis

For every `k in 0..31` and `h in {0,1}`, retain the inherited named public
visibility ancestor:

```text
O41_ACQUIRE_SUCCESS(k,h) = ordinary public ACQUIRED outcome at
  canonical position (41,0,0), produced by correct commit c_h, with value
  {src:alias_k(C), rel:alias_k(R(07+h)), dst:alias_k(D)}
```

`O41_ACQUIRE_SUCCESS(k,h)` remains the sole visibility ancestor of every
h-dependent byte in the supplied delayed treatment. The canonical public
`O40(k,h)` BIT outcome is not part of a D-entry public memory surface and is
not an allowed delayed twin divergence. Live U messages, commands, returns,
scratch, transcripts, receipts, caches, sessions, or outputs are likewise not
D inputs.

Define these exact primitive-row sequences:

```text
OLD_PUBLIC_ROWS(k) = the 32 primitive public evidence ROOT rows at canonical
  positions (00,0,0) through (31,0,0), in increasing Position order

O42_VALIDATE_P4(k) = the independent public p4 validation ROOT at (42,0,0)

O43_VALIDATE_NH(k,h) = the independent public nh validation ROOT at (43,0,0)
  for the nh admitted by O41_ACQUIRE_SUCCESS(k,h)

D_BASELINE_ROWS(k,h) =
  OLD_PUBLIC_ROWS(k) ||
  [O41_ACQUIRE_SUCCESS(k,h), O42_VALIDATE_P4(k), O43_VALIDATE_NH(k,h)]
```

Thus `D_BASELINE_ROWS` has exactly 35 rows. Its zero-based array indices are:

```text
0..31 = OLD_PUBLIC_ROWS(k)
32    = O41_ACQUIRE_SUCCESS(k,h)
33    = O42_VALIDATE_P4(k)
34    = O43_VALIDATE_NH(k,h)
```

The synthetic proposal at `(41,1,6)`, every A/B execution row at positions
32..39, `O40`, and all U-policy artifacts are absent. This public-surface rule
does not alter evidential support: O42/O43 remain independent evidence ROOTs,
the pair proposal remains SYNTH non-evidence, and the new atom/link becomes
supported only under the inherited provenance law. The selection and public
rendering of the h-specific `nh` in O41/O43 must nevertheless carry transitive
visibility lineage to `O41_ACQUIRE_SUCCESS(k,h)`.

For fixed `k`, the h=0 and h=1 byte trees have equal array lengths, schemas,
orders, positions, handles, slot ordinals, field sets, and fixed padding.
Within rows 32 and 34, only leaves encoding the h-specific public `nh` FactKey
or value may differ. Row 33 and every row 0..31 are byte-identical. A digest,
origin label, h, route, condition, split, answer, score, truth, oracle,
provenance ID, or private fixture identity may not be inserted into a public
tree to spread this entitlement.

## 2. Exact D-entry divergence allowlists by baseline mode

All JSON pointers below are RFC 6901 pointers into the D-entry
`HandoffPublicV4` tree. For baseline conditions the complete allowed
container-pointer set is the union of the inherited carrier set

```text
/carrier/atoms/25
/carrier/links/6
```

and exactly the mode-specific set below. A pointer names the smallest complete
container allowed to contain h-dependent leaves; it does not permit its stable
handle, rank, position, schema, order, count, or padding fields to differ.
Every actual differing leaf must be an O41 visibility descendant.

### 2.1 `RAW_STATIC`

The delayed raw object is exactly:

```text
RawContextPublicV4.rows = D_BASELINE_ROWS(k,h)
RawContextPublicV4.order = "CHRONOLOGICAL_POSITION"
```

Its mode-specific D-entry divergence allowlist is exactly:

```text
/memory_surface/static_context/rows/32
/memory_surface/static_context/rows/34
```

`mode`, `read_protocol`, `schema`, `order`, row count, all other rows, and
outer/static padding remain twin-equal. `RAW_STATIC` still advertises no READ
form and has zero READ opportunities.

Because `RawContextPublicV4` is rendered as static memory, the initial D
`ModelTurnPublicV4` may first differ only in the rendered byte spans that are
the unchanged identity projection of rows 32 and/or 34. All system text,
protocol text, goal, state, action catalog, budget, response schema, static
field names, ordering, padding, and bytes outside those spans remain equal.

### 2.2 `RAG_DETERMINISTIC`

The delayed RAG corpus is the exact document lift of `D_BASELINE_ROWS`:

```text
documents[i].public_document_handle = "d" + lower_hex2(i)
documents[i].event = D_BASELINE_ROWS(k,h)[i]
documents.length = 35
```

It therefore has consecutive handles `d00..d22`. Its mode-specific D-entry
divergence allowlist is exactly:

```text
/memory_surface/rag_corpus/documents/32/event   # handle d20
/memory_surface/rag_corpus/documents/34/event   # handle d22
```

The `d20`/`d22` handle fields, document ranks, document/slot padding, corpus
schema/order/count, all other documents, token-count shape, and sealed corpus
construction remain twin-equal. The h-specific relation token may differ only
inside the two allowed event objects. The corpus is never rendered directly.

Before any entitled document is returned, the initial rendered request and
every public RAG query, `query_tokens`, fingerprint, repeat count, status,
score, rank, handle, null slot, padding byte, and return containing only
documents outside `{d20,d22}` must be byte-identical across twins. The first
permitted model-visible difference is inside

```text
/last_public_result/slots/j/document/event
```

for `j in 0..3` only when that slot's unchanged
`public_document_handle` is `d20` or `d22`. In that first differing return,
the outer return, query, fingerprint, saturated repeat count, slot rank,
handle, `score_e12`, slot order, null slots, and padding remain equal; only the
allowed event descendant may differ. If no legal pre-action RAG return exposes
`d20` or `d22`, the complete actor/model-visible D trace remains twin-equal
until an ordinary world outcome independently separates it.

The inherited exact V7 query construction, Decimal BM25, integer ranking,
four-slot result, first-action close, and V8 saturated repeat/literal-null rules
remain unchanged. A query reached only after an entitled return may be a
dynamic descendant under section 3; the sealed corpus never becomes mutable.

### 2.3 `NATIVE_GRAPH_STATIC`

The delayed native graph has exactly the authentic public atoms and supported
links at the supplied D cut, in public-capability-handle order. Its new
O41-descended atom is fixed at `a19` (decimal array index 25), and the supported
`p4`-to-`nh` adjacency is fixed at `l06` (decimal array index 6). Its
mode-specific D-entry divergence allowlist is exactly:

```text
/memory_surface/static_context/atoms/25
/memory_surface/static_context/links/6
```

The `a19`/`l06` handles, indices, counts, array order, schema, outer graph
fields, and padding remain twin-equal. Only their h-specific public FactKey or
value leaves may differ, and each must have O41 visibility lineage.
`NATIVE_GRAPH_STATIC` still advertises no READ form and has zero READ
opportunities.

Because the native graph is rendered as static memory, the initial D
`ModelTurnPublicV4` may first differ only inside the rendered identity
projection of these two containers. All bytes outside those spans remain
twin-equal.

## 3. Shared first-visibility and descendant boundary

The mode-specific origins above are narrow supplied-treatment entitlements,
not general h-taint. Before the first allowed model-visible origin for the
active mode, the initial public state, goal, action catalog, budgets, protocol,
response schema, commands available, system/template bytes, token IDs, parser
state, cache/session state, and all old/null returns are equal.

After an allowed origin becomes model-visible, only these dynamic causal
descendants may differ:

```text
model response
parsed public command
public transition and ordinary outcome
current public view
same-phase scratch
subsequent public query selected by that response
subsequent RAG ranking/return reached through that query
later reader return reached through that command
sealed same-phase behavioral receipt
```

The static RAW/native memory and sealed RAG corpus may continue to differ only
at their original allowlisted pointers; they do not acquire new differing
fields. Static prompt/protocol text, action catalogs, budgets, schemas, private
metadata, source/authority data, routing, scoring rules, oracle/checker data,
unselected sibling/abandoned branches, timing, padding, errors, filenames, and
cross-phase state do not become descendants merely because an entitled origin
was exposed. Reset still destroys every model message, scratch value, command,
tool/RAG return, query state, cache, KV state, session, RNG, timing value, and U
output. Only the declared immutable supplied D surface survives.

Private handoff hashes and route bindings may differ to bind different
immutable treatments, but they remain outside actor/model visibility and may
not affect public ordering, bytes, padding, errors, timing, cache keys, or
resource attribution.

Register the distinct test:

```text
MTEXTV4-DELAYED-BASELINE-OUTCOME-DESCENDANT-29
```

For all 32 `k`, both h twins, all three delayed baseline modes, every legal RAG
read schedule and saturated repeat sequence, and both forced-equal and
policy-produced continuations, independent goldens must prove the exact 35-row
basis, D-entry pointer sets, O41 lineage, equal stable fields, first-visible
origin, dynamic descendant closure, reset destruction, and unchanged resource
charges. Mutations that add O40; use a live U row/output; move, omit, duplicate,
or reorder rows/documents/atoms/links; change a stable handle/rank/count/pad;
alter a forbidden D-entry pointer; expose the RAG corpus directly; change a
score/fingerprint before an entitled document appears; allow a non-descendant
prompt/error/cache/timing/branch byte to differ; forge/remove/wrong-h the O41
lineage; or borrow an AUTH U endpoint must fail before model execution.

This test complements rather than replaces
`M0V5-DELAYED-ENTRY-OUTCOME-DESCENDANT-13`,
`M0V5-HANDOFF-DELAYED-VISIBILITY-CLOSURE-28`, and
`MTEXTV4-BASELINE-PUBLIC-PROJECTION-AND-RESET-19`.

## 4. Strict V10 source-authoring grant

Let the one allowed change identity be the literal:

```text
C10 = "chg_20260910_pcfl_m0_mtext_bound_v10"
```

For C10, the only object that can represent
`SOURCE_CANDIDATE_AUTHORING_AUTHORITY` is this closed V10 instance of
`SourceAuthoringGrantV1`:

```text
SourceAuthoringGrantV1[C10] := {
  schema_version:1,
  artifact_type:"pcfl_m0_source_authoring_grant",
  change_id:"chg_20260910_pcfl_m0_mtext_bound_v10",
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
  authorization_evidence:{
    path:repo_relative_path,
    sha256:hex64,
    excerpt:string
  },
  source_authoring_authorized:true,
  preparation_execution_authorized:false,
  implementation_authorized:false,
  model_execution_authorized:false,
  scientific_claim_authorized:false
}
```

No field is optional and no extra field is allowed. Arrays have exactly the
members and order shown. Strings are NFC UTF-8; hashes are lowercase hex64;
`ratifier` is nonempty; and `decided_at` is UTC with a literal `Z` suffix.

Let `H` be the lowercase value of `source_authoring_plan_sha256`. The two
statement fields must be exactly these templates after replacing `<H>` by H:

```text
authority_statement =
"source authoring only for source_authoring_plan_sha256=<H>; resulting bytes are candidate-only, unratified, nonimportable, nonexecutable, and not preparation-ready"

decision_statement =
"approve only the three ordered authorized_operations; deny every forbidden_operations item; no source byte or later authority is ratified"
```

Closed cross-artifact validation additionally requires:

1. `successor_consensus_sha256` rehashes to the canonical V10 consensus, whose
   state is `human_required`, whose recommendation permits requesting only
   source-candidate authoring, and whose context binds this advisory.
2. `human_required_state_sha256` rehashes to the corresponding V10 runner
   state with that consensus artifact, `human_required=true`, and
   `implementation_authorized=false`.
3. `source_authoring_plan_sha256` rehashes to the exact V10 closed plan; the
   plan has `change_id=C10`; every writable path is one exact plan row; and its
   one nonmember manifest output is the only additional output.
4. `authorization_evidence.sha256` rehashes the exact human decision at
   `authorization_evidence.path`. `excerpt` is a byte-exact contiguous UTF-8
   substring of that file and contains both exact statements above with H.
5. The three hashes name three distinct artifacts. A generic architecture
   ratification, V5/V6/V7/V8/V9 grant, conversational inference, favorable
   model consensus, plan completion, or preexisting approval cannot validate
   this object.

## 5. Strict V10 source provenance

Every future V10 manifest member must embed this closed row:

```text
SourceProvenanceRowV1[C10] := {
  schema_version:1,
  artifact_type:"pcfl_m0_source_provenance",
  logical_path:repo_relative_path,
  source_sha256:hex64,
  authored_for_change_id:"chg_20260910_pcfl_m0_mtext_bound_v10",
  source_authoring_grant_sha256:hex64,
  derivation_sources:[{
    kind:"PCFL_V10_NORMATIVE"|"LANGUAGE_STANDARD"|"STANDARD_LIBRARY",
    identifier:string,
    path:null|repo_relative_path,
    sha256:null|hex64
  }, ...],
  v7_runtime_derivation:false,
  v7_oracle_derivation:false,
  author_attestation:string
}
```

The row has no extra or optional field. `logical_path` equals one V10 plan
member; `source_sha256` rehashes those exact authored bytes;
`source_authoring_grant_sha256` rehashes the valid C10 grant above; and at
least one derivation source has `kind="PCFL_V10_NORMATIVE"`.

For `PCFL_V10_NORMATIVE`, `path` and `sha256` are both non-null and rehash to
an exact normative source bound by the V10 human-required state; `identifier`
is a nonempty stable clause ID in that source. For `LANGUAGE_STANDARD` and
`STANDARD_LIBRARY`, `path` and `sha256` are both literal JSON null and
`identifier` is a nonempty exact standard/primitive name. Mixed nullability,
an unbound path/hash, or any V7 governance/runtime/oracle source rejects.

`derivation_sources` is nonempty, duplicate-free, and sorted by the bytewise
tuple `(kind,identifier,path_key,sha256_key)`, where a null key is byte `0x00`
and a string key is byte `0x01` followed by its NFC UTF-8 bytes. The exact
attestation template, after replacing `<G>` by the lowercase grant SHA-256, is:

```text
"authored only from the listed V10 normative/language sources under SourceAuthoringGrantV1 sha256=<G>; no V7 runtime/oracle derivation and no import, checking, or execution occurred"
```

Governance-only V7 identities remain confined to the separately controlled
`v7_boundary_v4.json` guard and never appear as derivation sources.

### 5.1 Grant/provenance mutation corpus

Retain `M0V5-SOURCE-AUTHORING-VS-PREPARATION-AUTHORITY-12` and require the V10
positive grant/provenance golden plus independent rejection of each of:

- a V5, V6, V7, V8, V9, missing, extra, or non-NFC change identity;
- a stale/wrong plan, consensus, state, grant, evidence, source, or derivation
  hash; swapped consensus/state/plan hashes; or two hash fields naming one
  artifact;
- a missing, extra, duplicate, reordered, renamed, or mistyped operation; an
  enlarged plan maximum; an unlisted/symlink/glob/directory/absolute/`..` path;
- any swapped authority boolean, generic architecture-ratification object,
  inferred approval, non-UTC timestamp, free-form statement, wrong H/G
  interpolation, noncontiguous evidence excerpt, or evidence excerpt not found
  byte-exactly in its hashed file;
- a provenance row for another change, logical path absent from the plan,
  source hash not matching that path, grant hash not matching the C10 grant,
  empty/duplicate/unsorted derivation list, invalid kind, mixed-null source,
  unbound normative source, V7 source, or either V7 derivation flag set true;
  and
- any import, interpreter parse/syntax check, execution, test, preparation,
  materialization, fixture/data generation, model/tokenizer/GPU call, unlisted
  write, or attempt to treat completed authoring as a later grant.

Every mutation fails before a source write or other operation. The sole
positive operational scope remains the three exact ordered operations in a
valid grant.

## 6. Source authoring is not byte ratification

The following state/authority graph is exact and acyclic:

```text
V10 source-only deliberation reaches human_required
  -> exact human SourceAuthoringGrantV1[C10]
  -> author all and only plan-listed candidate bytes
  -> compute their byte lengths and SHA-256 values
  -> write the nonauthoritative candidate NormativeSourceManifestV1
  -> STOP: candidate bytes remain unratified and nonconsumable

candidate manifest + every exact candidate byte
  -> fresh independent exact-byte review
  -> fresh five-role source consensus reaching human_required
  -> new human PreparationExecutionGrantV1 bound to that exact chain
  -> at most the separately authorized deterministic preparation
```

The source-authoring grant approves an operation over an exact path/role/size
allowlist. It does not approve, validate, ratify, import, parse, execute, test,
or make preparation-ready the values later written at those paths. The
nonauthoritative manifest is a receipt candidate, not an approval artifact.
Its existence, internal consistency, hashing, checker-looking content, or
favorable author self-review creates no edge to preparation, implementation,
model execution, fixture freeze, science, claim, release, or submission.

The later exact-byte review must bind the manifest hash and rehash every member
by path, byte length, role, media type, provenance row, and SHA-256 without
importing or executing it. The later consensus must bind the review and same
manifest. Only a new human preparation grant may authorize the one exact
preparation, and that grant must bind the source review, source consensus,
human-required state, manifest, entrypoint, argv, working directory,
environment, read/write allowlists, and resource limits under the inherited
Authority P schema. Byte review is necessary but not itself execution
authority.

Any change to any candidate source byte, provenance row, manifest member,
path, role, media type, or byte length invalidates the manifest and every
downstream review, consensus, state, or grant. Reusing the V10 source-authoring
human decision as byte ratification; treating manifest completion as approval;
auto-creating a preparation grant; executing a checker or syntax parser under
Authority S; or modifying source under Authority P must fail closed.

## 7. Roster, resource, and claim invariants

This advisory adds no condition, phase, root, model call, request opportunity,
generated token, topology, endpoint, scientific gate, or claim. It preserves
the exact 18-condition roster, 501 maximum request slots per root, 148,224
generated-token allowance per root, 4,104,192 input-token allowance per root,
64 deterministic roots with the 16/32/16 split, and all registered per-arm
READ/action/terminal opportunities. In particular RAW/native remain zero-READ
static modes, RAG retains its existing eight pre-action opportunities, and the
V8 repeat saturation changes no opportunity count.

All delayed acquisition, retention, acquisition-to-use, persistent-write,
online-learning, and self-write endpoints remain `NA`. The new mode-specific
entitlements establish only a supplied, model-independent D-treatment
visibility boundary. They are not evidence of retention, learning, DREAM,
SLEEP, LoRA transport, compression, parenting, recurrence, lifetime
improvement, baseline saturation, generalization, or the full organism.

## 8. Successor and stop boundary

A V10 successor may bind this advisory as one partial rework input, but must
also resolve every still-open V9 disposition listed in section 0 in one
complete, hash-bound packet before requesting source-authoring authority. A
favorable future V10 consensus may recommend only that Rohin consider the
strict source-authoring grant above and must stop at `human_required`.

This advisory itself performs and authorizes none of the operations described
in a future grant. No source bytes, grant, provenance row, manifest, fixture,
root, or data are created here, and no interpreter, checker, test, model,
tokenizer, benchmark, training, parenting, or GPU operation may be run because
of it.
