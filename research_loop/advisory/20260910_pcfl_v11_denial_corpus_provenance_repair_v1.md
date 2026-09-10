# PCFL V11 denial-corpus provenance repair v1

Date: 2026-09-10

Status: **source-only governance repair proposal; not ratified**. This document
does not edit the proposed corpus and authorizes no candidate-source authoring,
source import or execution, candidate parsing through an interpreter, syntax
checking, preparation, implementation, materialization, fixture/root/data
generation, checker or test execution, model/tokenizer call, benchmark,
training, LoRA/adapter/checkpoint work, parenting, GPU use, resource
acquisition, scientific claim, release, or submission.

## 0. Exact scope, inheritance, and separation

This repair addresses defects in:

```text
research_loop/advisory/
  20260910_pcfl_v11_denial_corpus_ratification_candidate_v1.md
SHA-256:
  492980e15c8c35a16adcf6067aba0acdb0877944bb3d40a53c5bacf346b54357
```

It also incorporates the richer synthetic matcher specification in:

```text
research_loop/advisory/
  20260910_pcfl_v11_denial_corpus_ratification_candidate_v2.md
SHA-256:
  c1d109309804a6defadd1643c5259eeaec6a0471ca74bf659800e50234339f81
```

Candidate v2 controls the harmless synthetic bytes, temporary matcher corpus,
six-case registry, and unit/production identity receipts reproduced in section
4 below. This repair controls the C11 boundary projection and provenance. It
expressly replaces candidate v2's one-source boundary-row rule with exactly
the two sources in section 3.3; no other source count is legal.

It preserves without modification the proposed corpus:

```text
DENIAL_CORPUS_PATH_C11 =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json"
DENIAL_CORPUS_SHA256_C11 =
  "4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799"
DENIAL_CORPUS_NBYTES_C11 = 3880
```

The bytes are RFC 8785/JCS plus exactly one LF, with the LF included in the
length and digest. This repair does not claim that a V7/V5 target was opened or
rehash a live target.

If a human later ratifies the corpus and this repair, that decision means only:
the exact corpus bytes are admitted as a negative, governance-only V11 source
under the interpretation below. Corpus ratification does **not** create a C11
source plan, boundary member, source manifest, provenance row, review grant,
review receipt, consensus, exact-byte ratification, preparation grant, guard
pass, fixture, resource receipt, or scientific result. Every integration
artifact in sections 5--7 remains a separately reviewed future obligation.

The ratification, if issued, is one closed object:

```text
V11DenialCorpusRatificationV1 := {
  schema_version: 1,
  artifact_type: "pcfl_v11_denial_corpus_ratification",
  decision: "RATIFY_NEGATIVE_GOVERNANCE_INPUT_ONLY",
  corpus: {
    path: DENIAL_CORPUS_PATH_C11,
    sha256: DENIAL_CORPUS_SHA256_C11,
    nbytes: 3880,
    encoding: "RFC8785_JCS_PLUS_ONE_LF"
  },
  interpretation_advisory: {
    path: "research_loop/advisory/20260910_pcfl_v11_denial_corpus_provenance_repair_v1.md",
    sha256: hex64
  },
  hidden_substring_supersession_statement: exact_string_from_section_4_1,
  ratifier: nonempty_nfc_string,
  decided_at: rfc3339_utc,
  authorization_evidence: {path:repo_relative_path,sha256:hex64,excerpt:nonempty_nfc_string},
  negative_governance_input_ratified: true,
  source_authoring_authorized: false,
  exact_candidate_bytes_ratified: false,
  preparation_execution_authorized: false,
  implementation_authorized: false,
  fixture_generation_authorized: false,
  model_execution_authorized: false,
  scientific_claim_authorized: false
}
```

Every field is required, nested objects are closed, and no extra field is
legal. The interpretation digest is filled with the hash of this advisory's
final preserved bytes; it is not a self-hash stored in those bytes. The exact
human evidence excerpt must state that only the negative governance input is
ratified and that all seven authority booleans remain false.

The effective V10 texts remain governing negative precedent:

```text
registry/render/claim v3:
  e676f3b638bfff6c63f119dbc47cf2ae2d704b36914690728c988f990cfec86b
provenance/resource/guard v3:
  d969fca712d18affed60879be63a96b2aa5d75596d7240c615a5b647dff4337e
authority/delayed-baseline v2:
  27668f5816958342b84a322c317281dc10131732153eeee387a228f67eea86ae
```

This document supersedes the V11 v1 advisory only where it states the exact
boundary projection, provenance matcher, embedded-member limitation,
synthetic matcher fixture, finite exposure union, or later-integration
obligation below. It makes no other scientific or resource change.

## 1. Exact meaning of the immutable corpus

The corpus has seven and only seven array-valued top-level denial classes. Its
integer `schema_version:1` is structural encoding metadata, not a registered
denial operand and not evidence that semantic scalar `1` has a V7 edge.
Likewise, object keys, array indices, matcher enum labels, and schema version
are not denied identities merely because they occur in governance bytes.

The finite production denial operands are only:

1. the eight `resolved_path_denials` rows' `path` values and six non-null
   paired `sha256` values;
2. the sole `module_identity_denials[0].value`;
3. the eleven `whole_artifact_sha256` values;
4. the two exact denied change IDs and one exact denied dependency ID in the
   provenance rules;
5. the 23 `distinctive_interface_identifiers` strings; and
6. the corpus `decision` value.

The matcher enums, rule-field names, capability surface labels, actor/model
sink labels, `artifact_type`, C11 `change_id`, `coincident_value_rule`, and
`schema_version` control matching but are not themselves denied V7/V5
identities. No unlisted value is discovered or inferred from a live target.

## 2. Exact boundary projection from the corpus

Define `BoundaryProjectionFromCorpusV1` only after the corpus path, digest,
length, canonical encoding, closed fields, cardinalities, sorting, and all
cross-field rules have passed. It performs the following pure projection over
already parsed governance values and performs no filesystem operation:

```text
G = rows in resolved_path_denials where kind == "GOVERNANCE_ONLY_SOURCE"
P = rows in resolved_path_denials where kind == "DENIED_PREFIX"
E = rows in resolved_path_denials where kind == "DENIED_EXACT"
M = module_identity_denials
H = whole_artifact_sha256
I = distinctive_interface_identifiers
G_hashes = set(row.sha256 for row in G)
D = H minus G_hashes
```

Reject unless `|G|=5`, `|P|=2`, `|E|=1`, `|M|=1`, `|H|=11`, `|I|=23`,
`|G_hashes|=5`, `G_hashes` is a subset of `H`, and `|D|=6`. Also reject unless
there is exactly one provenance rule
`(dependency,EXACT,FELTCRAFT_SYMBOLIC_KERNEL_V7)` and the corpus decision and
coincident rule equal their frozen values.

The output is exactly:

```text
V7BoundaryV1[C11] := {
  schema_version: 1,
  artifact_type: "pcfl_m0_v7_boundary",
  dependency: "FELTCRAFT_SYMBOLIC_KERNEL_V7",
  decision: corpus.decision,
  reused_primitives: [],
  governance_only_source_identities: [
    {path:row.path,sha256:row.sha256} for row in G
  ],
  distinctive_artifact_sha256: sorted_bytewise(D),
  denied_path_prefixes: sorted_bytewise([row.path for row in P]),
  denied_exact_paths: sorted_bytewise([row.path for row in E]),
  denied_module_prefixes: [M[0].value],
  denied_interface_identifiers: I,
  coincident_value_rule: corpus.coincident_value_rule
}
```

`governance_only_source_identities` is sorted by raw UTF-8
`(path,sha256)`. Every output object is closed; no field may be added, omitted,
renamed, or retyped. The later boundary member bytes are RFC 8785/JCS plus one
LF. Its digest is computed over only that newly authored member. Neither the
projection nor its writer resolves, stats, opens, imports, executes, or hashes
a denied target.

The literal `artifact_type`, empty `reused_primitives`, and projection rules
come from this repair, not from the immutable corpus. Consequently a complete
external boundary provenance row must cite both the corpus and the exact
human-ratified bytes of this repair; section 3 gives the noncircular form.

## 3. Exact SourceProvenanceRowV1[C11] matching and placement

### 3.1 Closed external row

The later C11 source manifest must store exactly one external row for each of
the 23 already closed member byte strings. No member contains its own digest,
its own row, or a hash of a container containing itself.

```text
SourceProvenanceRowV1[C11] := {
  schema_version: 1,
  artifact_type: "pcfl_m0_source_provenance",
  logical_path: repo_relative_path,
  source_sha256: hex64,
  authored_for_change_id: "chg_20260910_pcfl_m0_mtext_bound_v11",
  source_authoring_grant_sha256: hex64,
  derivation_sources: [{
    kind: "PCFL_V11_NORMATIVE" | "LANGUAGE_STANDARD" |
          "STANDARD_LIBRARY",
    identifier: nonempty_nfc_string,
    path: null | repo_relative_path,
    sha256: null | hex64
  }, ...],
  v7_runtime_derivation: false,
  v7_oracle_derivation: false,
  author_attestation: nonempty_nfc_string
}
```

Objects are recursively closed. `derivation_sources` is nonempty,
duplicate-free, and sorted bytewise by `(kind,identifier,path-or-empty,
sha256-or-empty)`. Every row has at least one `PCFL_V11_NORMATIVE` entry. For
that kind, `path` and `sha256` are non-null and rehash exact human-bound V11
normative bytes. For either language kind both are null. Any true, missing, or
mistyped V7 flag rejects.

### 3.2 Exact mapping of the corpus provenance rules

For a row `r` and each derivation entry `d`, form this finite multiset of typed
observations without coercion or case folding:

```text
("change_id", r.authored_for_change_id)
("identifier", d.identifier)
("path", d.path)       if d.path is non-null
("sha256", d.sha256)   if d.sha256 is non-null
```

Apply the corpus rules as follows. This mapping replaces any assumption that
the row literally contains fields named `dependency`, `module`, or
`transitive_derivation_ancestor`.

- A denied `change_id` rejects if it equals `r.authored_for_change_id` **or**
  any `d.identifier`.
- The denied dependency rejects if it equals any `d.identifier`.
- A distinctive identifier rejects if it equals any `d.identifier`.
- The module rules apply to every `d.identifier` as an exact-or-dot-descendant
  module candidate.
- The path rules apply to every non-null `d.path` and to any `d.identifier`
  that is byte-equal to a denied exact path, denied source path, denied prefix
  root, or a descendant of a denied prefix.
- The digest rules apply to every non-null `d.sha256` and to any
  `d.identifier` that is exactly one of the eleven lowercase digests.
- `v7_runtime_derivation` and `v7_oracle_derivation` must both be literal
  `false` independently of every identity comparison.

Thus moving a denied value into another identity-bearing field cannot launder
it. Generic coincident scalar values, substrings, case-folded similarities,
and unrelated language identifiers are not matches.

`transitive_derivation_ancestor` is not a hidden field in
`SourceProvenanceRowV1[C11]`. Each row must cite ultimate normative/language
roots directly. If later C11 proposes any additional derived-source parent
graph, that graph is forbidden until section 5's authenticated observation
schema and its exact node/edge identities are separately deliberated and
human-ratified. Unknown, omitted, postdated, or cyclic parentage rejects; a
free-form claim of translation never supplies provenance.

### 3.3 Exact boundary row; no circle

Let `REPAIR_PATH` equal
`research_loop/advisory/20260910_pcfl_v11_denial_corpus_provenance_repair_v1.md`
and let `REPAIR_SHA256` be the SHA-256 of its final, separately human-ratified
bytes.
The external boundary row has exactly two derivation entries and no third:

```text
logical_path:
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/v7_boundary_v4.json"
derivation_sources: [
  {
    kind: "PCFL_V11_NORMATIVE",
    identifier: "V11-DENIAL-CORPUS-PROJECTION-RULE",
    path: REPAIR_PATH,
    sha256: REPAIR_SHA256
  },
  {
    kind: "PCFL_V11_NORMATIVE",
    identifier: "V11-NORMATIVE-DENIAL-CORPUS",
    path: DENIAL_CORPUS_PATH_C11,
    sha256: DENIAL_CORPUS_SHA256_C11
  }
]
```

The order shown is the required tuple order. `source_sha256` hashes the closed
boundary member and occurs only in the later nonmember manifest. Neither
normative input contains that future member digest. The manifest's own hash is
bound only by later review/state artifacts. This is acyclic. For C11 only,
these two entries explicitly supersede V10's boundary-specific one-entry rule;
human ratification of the exact supersession is required.

For the boundary row, `author_attestation` is exactly the following after
replacing `<G>` with its lowercase `source_authoring_grant_sha256`:

```text
authored only from the listed V11 normative sources under SourceAuthoringGrantV1 sha256=<G>; no V7 runtime/oracle derivation and no import, checking, or execution occurred
```

## 4. Whole-artifact scope and exact synthetic matcher evidence

### 4.1 Human-required V11-only supersession

The immutable digest-only corpus contains no V7/V5 preimage or byte length.
The guard is forbidden to obtain either by opening a denied target. Therefore
the following exact sentence must appear in a human ratification before the
corpus can be used:

> For C11 only, I supersede the V5 phrase “embeds one of those whole artifacts
> as a byte-for-byte member” and the corresponding production fixture meaning
> with “an entire non-governance candidate/input/output byte object, or an
> explicitly enumerated length-delimited member whose bytes are a verified
> in-bounds slice of such an object, has a SHA-256 in the ratified eleven-value
> deny array.” C11 does not claim arbitrary undeclared-substring detection.

Absent that exact human decision, the hidden-substring question remains
`REWORK` and no V11 source-authoring request is eligible. The supersession does
not permit an omitted declared resource: every archive entry, package-data
entry, deserialized blob, fixture payload, static literal resource, and other
resource exposed by the closed capability inventory must have one exact member
row. An unenumerated or opaque resource/capability rejects, but this is not
misreported as universal substring detection.

### 4.2 Exact adopted harmless bytes and temporary corpus

The unit matcher uses exactly these four harmless ASCII byte strings. The
terminal `0a` is part of the first, second, and fourth values:

| ID | exact hex bytes | nbytes | SHA-256 |
|---|---|---:|---|
| `V11-SYNTH-WHOLE` | `5631315f53594e54485f57484f4c455f41525449464143540a` | 25 | `da867dbd6efb7e026a84aff6092286075357eadba40f228220a292ad23bae395` |
| `V11-SYNTH-EMBEDDED` | `5631315f53594e54485f454d4245444445445f4d454d4245520a` | 26 | `b11f8c0ab05bac5c7706d6ee73c2116b7611106d9c1500b2016b0a349899f6f0` |
| `V11-SYNTH-CONTAINER` | `484541445631315f53594e54485f454d4245444445445f4d454d4245520a5441494c` | 34 | `0ef9defdeba49dd31ae0879d1a35d015a97b6f418181dabcc7ed82881124f870` |
| `V11-SYNTH-HARMLESS` | `5631315f53594e54485f4841524d4c4553530a` | 19 | `a3a0a8fc8f794d00dac2a73dffb4d52c36b391c4dffb37456dfae8cf17d2bb46` |

The embedded member is the container half-open byte range `[4,30)`. The
wrong-offset range `[5,31)` hashes to
`881f76334b1261a408a10b742ad5301ea2ab3820a30e28e2043af037d9e60210`;
the wrong-length range `[4,29)` hashes to
`c6f027e9be740803b50d8516cc763353fb26e569e799fdfea4bb0ba5f8fcf4f3`.

The temporary matcher corpus is exactly this JCS line plus one LF:

```json
{"artifact_type":"pcfl_v11_synthetic_temporary_matcher_corpus","embedded_member_sha256":["b11f8c0ab05bac5c7706d6ee73c2116b7611106d9c1500b2016b0a349899f6f0"],"schema_version":1,"whole_artifact_sha256":["da867dbd6efb7e026a84aff6092286075357eadba40f228220a292ad23bae395"]}
```

It is 270 bytes with SHA-256
`87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293`.
It is a unit-test input only and cannot pass the production corpus identity
gate.

The six-case registry is exactly the following JCS line plus one LF:

```json
{"artifact_type":"pcfl_v11_synthetic_matcher_case_registry","cases":[{"case_id":"SYNTH-EMBEDDED-MATCH","expected_outcome":"MATCH","input_sha256":"b11f8c0ab05bac5c7706d6ee73c2116b7611106d9c1500b2016b0a349899f6f0","matcher_operation":"DECLARED_MEMBER_SHA256","member_nbytes":26,"member_offset":4,"parent_sha256":"0ef9defdeba49dd31ae0879d1a35d015a97b6f418181dabcc7ed82881124f870","temporary_corpus_sha256":"87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293"},{"case_id":"SYNTH-EMBEDDED-WRONG-LENGTH","expected_outcome":"NO_MATCH","input_sha256":"c6f027e9be740803b50d8516cc763353fb26e569e799fdfea4bb0ba5f8fcf4f3","matcher_operation":"DECLARED_MEMBER_SHA256","member_nbytes":25,"member_offset":4,"parent_sha256":"0ef9defdeba49dd31ae0879d1a35d015a97b6f418181dabcc7ed82881124f870","temporary_corpus_sha256":"87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293"},{"case_id":"SYNTH-EMBEDDED-WRONG-OFFSET","expected_outcome":"NO_MATCH","input_sha256":"881f76334b1261a408a10b742ad5301ea2ab3820a30e28e2043af037d9e60210","matcher_operation":"DECLARED_MEMBER_SHA256","member_nbytes":26,"member_offset":5,"parent_sha256":"0ef9defdeba49dd31ae0879d1a35d015a97b6f418181dabcc7ed82881124f870","temporary_corpus_sha256":"87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293"},{"case_id":"SYNTH-TEMP-AS-PRODUCTION","expected_outcome":"IDENTITY_REJECTED","input_sha256":"87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293","matcher_operation":"PRODUCTION_CORPUS_IDENTITY","member_nbytes":null,"member_offset":null,"parent_sha256":null,"temporary_corpus_sha256":"87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293"},{"case_id":"SYNTH-WHOLE-MATCH","expected_outcome":"MATCH","input_sha256":"da867dbd6efb7e026a84aff6092286075357eadba40f228220a292ad23bae395","matcher_operation":"WHOLE_ARTIFACT_SHA256","member_nbytes":null,"member_offset":null,"parent_sha256":null,"temporary_corpus_sha256":"87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293"},{"case_id":"SYNTH-WHOLE-NONMATCH","expected_outcome":"NO_MATCH","input_sha256":"a3a0a8fc8f794d00dac2a73dffb4d52c36b391c4dffb37456dfae8cf17d2bb46","matcher_operation":"WHOLE_ARTIFACT_SHA256","member_nbytes":null,"member_offset":null,"parent_sha256":null,"temporary_corpus_sha256":"87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293"}],"schema_version":1}
```

It is 2,369 bytes with SHA-256
`eb749849e9dda68b9b86c7f289b3eb8261107e973e4d78978c3ae43708643917`.
The four harmless byte strings, temporary corpus, and case registry are stored
as exact data inside the later `source/mutation_fixtures.json`; none is a new
plan row, production corpus, or V7/V5 preimage.

### 4.3 Exact adopted receipts

Future separately authorized unit evidence has this closed shape:

```text
SyntheticMatcherReceiptV1 := {
  schema_version:1,
  artifact_type:"pcfl_v11_synthetic_matcher_receipt",
  source_manifest_sha256:hex64,
  matcher_source_logical_path:repo_relative_path,
  matcher_source_sha256:hex64,
  temporary_corpus_sha256:
    "87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293",
  case_registry_sha256:
    "eb749849e9dda68b9b86c7f289b3eb8261107e973e4d78978c3ae43708643917",
  case_results:[{
    case_id:one_of_the_six_literal_registry_ids,
    input_sha256:the_registry_value,
    computed_sha256:hex64,
    expected_outcome:"MATCH"|"NO_MATCH"|"IDENTITY_REJECTED",
    observed_outcome:"MATCH"|"NO_MATCH"|"IDENTITY_REJECTED",
    target_read_count:0,
    passed:boolean
  }, ...],
  production_corpus_read:false,
  production_entry_point_invoked:false,
  target_read_count:0,
  passed:boolean
}
```

`case_results` has exactly six rows in registry order. The matcher path/hash
must equal one exact C11 source-manifest entry. Passing requires each computed
digest to equal its registry `input_sha256`, observed to equal expected, every
row and the receipt to pass, and all target-read counters to be zero.

Production corpus identity is separate:

```text
ProductionDenialCorpusIdentityReceiptV1 := {
  schema_version:1,
  artifact_type:"pcfl_v11_production_denial_corpus_identity_receipt",
  expected_path:DENIAL_CORPUS_PATH_C11,
  observed_path:repo_relative_path,
  expected_sha256:DENIAL_CORPUS_SHA256_C11,
  observed_sha256:hex64,
  expected_nbytes:3880,
  observed_nbytes:u64,
  canonical_jcs_plus_one_lf:boolean,
  target_read_count:0,
  passed:boolean
}
```

Pass requires exact path, independently computed corpus hash and length, and
canonical bytes. The temporary corpus always rejects here. A metadata-only
digest injection, omitted/extra/reordered case, hash without exact fixture
bytes, or any denied-target access rejects. Production separately compares
independently computed authorized C11 file/member digests with all eleven deny
digests. Neither component alone is reported as an actual V7-preimage test.

## 5. Authenticated observation metadata is a later V11 obligation

Corpus ratification does not authenticate a candidate's claimed path, module,
member, capability, or provenance closure. Before any V11 preparation grant,
a later source-integrated proposal must define and hash-bind the following
closed schema and the exact analyzer source that will populate it. An instance
is produced only inside guard substage zero under the later preparation grant;
no instance is produced or treated as already bound by this advisory.

```text
AuthenticatedDenialObservationBundleV1 := {
  schema_version: 1,
  artifact_type: "pcfl_v11_authenticated_denial_observations",
  change_id: "chg_20260910_pcfl_m0_mtext_bound_v11",
  source_authoring_plan_sha256: hex64,
  normative_source_manifest_sha256: hex64,
  corpus_sha256:
    "4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799",
  boundary_sha256: hex64,
  analyzer_logical_path: repo_relative_path,
  analyzer_source_sha256: hex64,
  analyzer_actor: "V7_BOUNDARY_GUARD",
  member_identities: [{logical_path:repo_relative_path,nbytes:u64,sha256:hex64},...],
  path_observations: [{
    observation_id:hex64,
    origin_logical_path:repo_relative_path,
    lexical_path:repo_relative_path,
    resolved_target:repo_relative_path,
    resolution_evidence_sha256:hex64
  },...],
  module_observations: [{
    observation_id:hex64,
    origin_logical_path:repo_relative_path,
    surface:string,
    module_identity:nfc_string,
    source_span_sha256:hex64
  },...],
  embedded_member_observations: [{
    observation_id:hex64,
    parent_logical_path:repo_relative_path,
    parent_sha256:hex64,
    member_name:nfc_string,
    member_type:nfc_string,
    byte_offset:u64,
    byte_length:u64,
    computed_sha256:hex64
  },...],
  capability_nodes: [{
    node_id:hex64,
    surface:CapabilitySurface,
    is_surface_root:boolean,
    target_kind:"SURFACE_ROOT"|"PATH"|"MODULE"|"DIGEST"|"RESOURCE"|
                "SUBPROCESS"|"NETWORK",
    target_value:nfc_string
  },...],
  capability_edges: [{from_node_id:hex64,to_node_id:hex64},...],
  provenance_edges: [{child_id:hex64,parent_id:hex64,parent_identity:string},...],
  unresolved_dynamic_observation_count: u64,
  closure_status: "COMPLETE" | "REJECT"
}
```

Every nested object is closed. Identity arrays are bytewise sorted and
duplicate-free; graph rows are sorted by their displayed identity tuple.
`member_identities` equals the exact 22 non-boundary member tuples in the
manifest. `CapabilitySurface` is exactly one of the corpus's eleven strings;
there is exactly one `is_surface_root:true` node for each surface, with
`target_kind:"SURFACE_ROOT"` and `target_value` equal to that surface. Graphs
are finite and acyclic. Every node reachable from any of those eleven roots
occurs exactly once, and every static or declared
dynamic path/module/resource/subprocess/deserialization/environment/
configuration/argv/network operation has an observation. Any missing,
unresolved, opaque, ambiguous, unbound, cyclic, or extra observation requires
`closure_status:"REJECT"` and produces no projection. A passing bundle has
`closure_status:"COMPLETE"` and
`unresolved_dynamic_observation_count:0`; no other combination passes.

The bundle is not trusted because a candidate asserted it. The later proposal
must identify `analyzer_logical_path` as one of the 22 exact manifest members,
bind its source digest, define its deterministic inert-byte grammar, and make
the guard independently recompute the bundle from the exact member bytes,
external rows, and declared manifests. Claimed metadata and recomputation must
be byte-identical. Plan members are regular files; a symlink member rejects.
Resolution evidence may use only source-review-bound regular-file identities
and lexical link targets already contained in the candidate closure. Missing
evidence rejects. Neither analyzer nor guard follows, stats, opens, hashes,
imports, or executes the resolved target.

This section is a precise eligibility obligation, not an authorization to
author the analyzer, generate the bundle, parse candidate bytes, or run the
guard. If the later V11 proposal does not bind the complete schema, analyzer
path/hash, observation grammar, and rejecting completeness fixtures, it must
remain `REWORK`.

## 6. Finite exposure identities and causal nonexposure

Define the direct-occurrence set `StaticExposureIdentityUnionV11` as exactly
the finite production denial operands in section 1 plus these two strings:

```text
"SOURCE_BOUNDARY_REJECTED"
"V11-NORMATIVE-DENIAL-CORPUS"
```

Define `BoundGovernanceIdentityTupleV11` later as exactly the path and digest
for each of: C11 plan, nonmember manifest, boundary member, denial corpus,
source-authoring grant, exact-byte-review grant, review receipt, exact-byte
ratification, preparation grant, detailed guard receipt, and observation
bundle. The tuple has 22 strings, sorted bytewise and duplicate-free; no
artifact content, scalar schema value, field name, array index, or matcher
enum is added.

Direct occurrence of a member of either finite set in any of the corpus's 22
actor/model sinks rejects. Encoded or causal influence is tested separately:
for two complete governance-private inputs with equal guard pass and equal
literal 22-path allowlist, all downstream semantic bytes and all 22 sink
observations must be identical. This twin comparison covers the full private
objects without incorrectly making structural `schema_version:1` or other
generic coincident values direct-denial identities. A pass-to-fail difference
may cause only absence of the projection.

The later integration must define a closed mapping from every public/rendered/
model/cache/index/error/timing/receipt/claim field to exactly one of the 22
sink enums. Missing or multiply classified fields reject. Until that mapping
and the authenticated observation bundle are bound, corpus ratification alone
does not establish actor/model nonexposure.

## 7. Exact later C11 integration boundary; no resource conflation

For this repair, `C11` means exactly:

```text
"chg_20260910_pcfl_m0_mtext_bound_v11"
```

The future integration constants are:

```text
PLAN_PATH_C11 =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan.json"
MANIFEST_PATH_C11 =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/normative_source_manifest.json"
BOUNDARY_PATH_C11 =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source/v7_boundary_v4.json"
```

The future successful guard projection's allowlist is the following literal
bytewise-sorted array of exactly 22 paths:

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

No boundary, plan, manifest, corpus, directory, glob, alias, symlink, URI, or
current-working-directory relative path may be added. The four-field
`V7GuardProjectionV1` schema and failure-with-no-projection rule remain exactly
those of the effective V10 guard repair, with only the listed C11 path literals.

The later plan must have exactly 24 rows: 23 manifest members and the one
nonmember manifest output. Its `governance_inputs` array has exactly the one
closed row already proposed for `DENIAL_CORPUS_PATH_C11`, role
`V11_NORMATIVE_DENIAL_CORPUS`, media type `application/json`, the literal
corpus digest, and `GOVERNANCE_ONLY` access. The corpus is not an entry,
member, output, candidate/preparation/runtime input, fixture, or scientific
artifact.

The manifest does **not** gain a corpus field. It binds the exact plan hash;
that plan transitively commits to the governance-input path/hash. Later grants
and states bind the plan hash and, where their already closed schema has a
normative-corpus field, repeat the same path/hash. This replaces V11 v1's
ambiguous demand for literal corpus placement in the external manifest.
The C11 human-required state must additionally bind `REPAIR_PATH` and
`REPAIR_SHA256` as an exact normative interpretation source. The closed
source-authoring grant binds that exact state digest; no extra grant field is
added. This transitive binding does not make the repair a plan row, manifest
member, output, or runtime input.

The exact authority order remains:

```text
separate human corpus/repair ratification
  -> fresh V11 source-only deliberation ending human_required
  -> separate human SourceAuthoringGrantV1[C11]
  -> Authority-S inert write/hash and nonmember external manifest
  -> separate human GovernanceExactByteReviewGrantV1[C11]
  -> independent review and only IndependentExactByteReviewReceiptV1
  -> fresh five-role exact-byte consensus ending human_required
  -> separate human ExactByteRatificationV1[C11]
  -> separate human PreparationExecutionGrantV1
  -> V7_BOUNDARY_GUARD as substage zero
  -> four-field pass projection only on success
```

No completion issues the next authority. Failure emits no projection and
consumes the one preparation attempt under the inherited rule.

This corpus repair adds no experiment condition, root, slot, token, endpoint,
reader opportunity, action opportunity, resource exemption, or scientific
claim. It preserves as ceilings exactly 18 conditions, 501 slots and 148,224
generated tokens per ordinary root, the 16 DEV / 32 CONFIRMATION / 16 RESERVE
split, 24 sentinels, and active maxima of 24,072 slots and 7,120,896 generated
tokens. Governance authoring/review/guard/test CPU, storage, and receipts are
not silently amortized into or used as feedback for an arm.

`ChargedResourceV10` was explicitly C10-scoped. Corpus ratification neither
renames nor silently extends it to C11. Before C11 source authoring, a separate
V11 integration repair must human-ratify a closed C11-scoped resource schema
or explicitly bind an exact scoped supersession while preserving every V10
field, type, extra-field rejection, nonomission equation, standalone/physical
CAS rule, post-origin charging law, and the ceilings above. Until then the
resource portion of C11 remains `REWORK`; that does not prevent independent
ratification of this negative corpus.

## 8. Stop boundary

This advisory writes only governance prose. It does not modify the corpus,
create or approve a V11 integration packet, authorize source authoring, or
execute any matcher, parser, checker, test, model, tokenizer, benchmark,
training, GPU, preparation, materialization, resource-acquisition, claim,
release, or submission operation. Every new operational object described here
is a future exact-source obligation gated by the full deliberation and human
authority chain.
