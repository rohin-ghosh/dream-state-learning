# PCFL V11 normative-denial-corpus ratification candidate v2

Date: 2026-09-10

Status: **source-only governance proposal; not ratified; not a complete V11
successor packet**. This file authorizes no source authoring, source import,
candidate parsing or syntax checking, preparation, implementation,
materialization, fixture/root/data generation, checker or test execution,
model/tokenizer call, benchmark, training, LoRA/adapter/checkpoint work,
parenting, GPU use, resource acquisition, scientific claim, release, or
submission.

## 0. Exact predecessor, corpus, and controlling semantics

V2 preserves these existing files byte for byte:

```text
research_loop/advisory/
  20260910_pcfl_v11_denial_corpus_ratification_candidate_v1.md
SHA-256:
  492980e15c8c35a16adcf6067aba0acdb0877944bb3d40a53c5bacf346b54357

research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/
  v11_normative_denial_corpus.json
SHA-256:
  4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799
nbytes:
  3880
serialization:
  RFC 8785 / JCS JSON followed by exactly one LF, included in hash and length
```

The only change identity defined by this proposal is:

```text
C11 = "chg_20260910_pcfl_m0_mtext_bound_v11"
CORPUS_PATH =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json"
CORPUS_SHA256 =
  "4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799"
CORPUS_NBYTES = 3880
```

V2 replaces v1 sections 4.3, 4.4, 4.7, 5, and the corresponding mutation
wording in section 6 with sections 2--7 below. It also corrects v1's scalar
wording as follows: the corpus contains integer `1` solely as
`schema_version` metadata. It contains no numeric `0`, `4`, `8`, or `16`, and
no number in it, including `1`, is a positive PCFL semantic value. All other
v1 clauses remain proposed requirements unless this v2 expressly narrows or
defers them.

The exact inherited semantics used here are the effective V10 repair heads:

| advisory | SHA-256 |
|---|---|
| `research_loop/advisory/20260910_pcfl_v10_registry_render_claim_exact_repair_v3.md` | `e676f3b638bfff6c63f119dbc47cf2ae2d704b36914690728c988f990cfec86b` |
| `research_loop/advisory/20260910_pcfl_v10_provenance_resource_guard_exact_repair_v3.md` | `d969fca712d18affed60879be63a96b2aa5d75596d7240c615a5b647dff4337e` |
| `research_loop/advisory/20260910_pcfl_v10_authority_delayed_baseline_exact_repair_v2.md` | `27668f5816958342b84a322c317281dc10131732153eeee387a228f67eea86ae` |
| `research_loop/advisory/20260910_pcfl_v10_repair_trio_cross_preflight_v1.md` | `77fb19c70f62d63c58f314d705058b0cee36841daaa14e788da4d8402ab8c7c5` |

Those hashes bind semantics; they do not parameterize or authorize a V11
plan, manifest, boundary path, grant, reviewer, guard, preparation, or run.

The corpus schema remains recursively closed and has exactly seven array
fields: eight resolved-path rows, one module rule, eleven whole-artifact
digests, eight provenance rules, twenty-three interfaces, eleven capability
surfaces, and twenty-two actor/model sinks. It has exactly five scalar fields.
No live V7/V5 target was read or hashed to create it, and this v2 requires no
such read.

## 1. Exact corpus-to-`V7BoundaryV1` projection

`BoundaryProjectionFromCorpusV1` is the following total function of the exact
ratified corpus bytes. It first validates the v1 recursive schema,
cardinalities, sorting, constants, JCS-plus-LF identity, path/hash pairings,
and `CORPUS_PATH`, `CORPUS_SHA256`, and `CORPUS_NBYTES`. It then emits exactly
this value:

```json
{
  "schema_version": 1,
  "artifact_type": "pcfl_m0_v7_boundary",
  "dependency": "FELTCRAFT_SYMBOLIC_KERNEL_V7",
  "decision": "ZERO_RUNTIME_REUSE",
  "reused_primitives": [],
  "governance_only_source_identities": [
    {"path":"feltcraft_symbolic_kernel/__init__.py","sha256":"2274ed4d5ef1eaa63357f113a5a3f0f82a4321594c65596283e71601c68081e9"},
    {"path":"feltcraft_symbolic_kernel/kernel.py","sha256":"c68771ec3d5f67193766cc56c16f152c5bc757a7e221c31a826b7649f2b69fdc"},
    {"path":"feltcraft_symbolic_kernel/report.py","sha256":"41133956ad9f36842d439eea8df82f5f1407fb59e36b52a0510aa3dbd61921d3"},
    {"path":"feltcraft_symbolic_kernel/run.py","sha256":"56f7e8d703bb7f3737f725d5b09c7ad3c12ce2a373308356c9c77b62a2b5b046"},
    {"path":"feltcraft_symbolic_kernel/test_kernel.py","sha256":"d4a8a995be71a08413bdd718eebd25d3047a4c5b5edd52e3d1f3c715d3517219"}
  ],
  "distinctive_artifact_sha256": [
    "1ed5411ee562f71bf0214f0e4763471d8b8ca748046aab377942a517823c84ec",
    "4250f8fa1678fbb91f79803a9b14336fbf84d2554fddc5409673db2502cc1567",
    "9db56cbb6df4f4d481269ffc480a81b2634a0996d4d51c3612dcbd9056638dca",
    "d67f446f7b4cb11024033c49fd8b1dcb75424e1f8bf7efb1a64cadbdb02c1fb5",
    "dce3fe74e5f4918f306dd365fad984bd3440c168348b92f7dbb5efa1652bccb4",
    "f6f3181db906b915d4711fc701cac4aee464fdd9b21bd0dbb41c95dc976ca83b"
  ],
  "denied_path_prefixes": [
    "feltcraft_symbolic_kernel/",
    "research_loop/changes/chg_20260901_feltcraft_symbolic_kernel_v7/"
  ],
  "denied_exact_paths": [
    "research_loop/changes/chg_20260901_feltcraft_symbolic_kernel_v5/golden_vectors.json"
  ],
  "denied_module_prefixes": ["feltcraft_symbolic_kernel"],
  "denied_interface_identifiers": [
    "ALIGNMENTS","ALIGNMENT_AT","CAL","CALIBRATIONS","GRAPH","GRAPHS",
    "LOCAL","MOTIF_SCHEMA","ORACLE","RANDOM_SOURCE","SK01","SK02",
    "SK03","SK04","SK05","SK06","SK07","SK08","SK09","TOP",
    "checker_call","enumerator_call","projection_call"
  ],
  "coincident_value_rule": "NO_EDGE_WITHOUT_A_BOUND_DENIAL_PREDICATE"
}
```

The derivation is exact: the five `GOVERNANCE_ONLY_SOURCE` rows, sorted by
path, produce `governance_only_source_identities`; the six sorted members of
`whole_artifact_sha256` not equal to those five paired hashes produce
`distinctive_artifact_sha256`; the two `DENIED_PREFIX` paths and one
`DENIED_EXACT` path produce their corresponding arrays. The sole module row
must equal
`{"match":"EXACT_OR_DOT_DESCENDANT","value":"feltcraft_symbolic_kernel"}`.
The dependency is the sole provenance tuple with `field="dependency"`; the
other scalar and interface fields copy exactly from the corpus. The five- and
six-digest sets must be disjoint and their union must equal the eleven corpus
digests. Any count, tuple, pairing, split, or constant mismatch rejects without
a boundary value.

This fixes the semantic content sufficient to reproduce inherited
`V7BoundaryV1`. The later integrated V11 packet must separately choose and
bind the boundary source path, serialization, byte length, and hash; none is
inferred here.

## 2. Exact external `SourceProvenanceRowV1[C11]` and laundering ban

The known nested provenance schema is retained and parameterized only by C11:

```text
SourceProvenanceRowV1[C11] := {
  schema_version:1,
  artifact_type:"pcfl_m0_source_provenance",
  logical_path:repo_relative_normalized_posix_path,
  source_sha256:hex64,
  authored_for_change_id:"chg_20260910_pcfl_m0_mtext_bound_v11",
  source_authoring_grant_sha256:hex64,
  derivation_sources:[{
    kind:"PCFL_V11_NORMATIVE"|"LANGUAGE_STANDARD"|"STANDARD_LIBRARY",
    identifier:nonempty_nfc_string,
    path:null|repo_relative_normalized_posix_path,
    sha256:null|hex64
  }, ...],
  v7_runtime_derivation:false,
  v7_oracle_derivation:false,
  author_attestation:string
}
```

The row and every nested source object are closed. `derivation_sources` is
nonempty, duplicate-free, and strictly sorted by
`(kind,identifier,path-or-empty,sha256-or-empty)` in raw UTF-8 order. It has at
least one `PCFL_V11_NORMATIVE` row. Such a row has both non-null path and hash
and must equal one exact `(identifier,path,sha256)` tuple in the later
plan-bound V11 normative-source catalog. A language or standard-library row
has both path and hash null. A partial-null pair, unknown tuple, path/hash swap,
duplicate, unsorted row, unbound source, or extra field rejects.

The attestation is exactly, after substituting the bound source-authoring grant
hash for `<G>`:

```text
authored only from the listed V11 normative/language sources under SourceAuthoringGrantV1 sha256=<G>; no V7 runtime/oracle derivation and no import, checking, or execution occurred
```

Both V7 booleans must be literal `false`; omission, `true`, another type, or
an attestation inconsistent with them rejects.

The corpus's eight provenance-rule rows map onto this nested object as
follows. All matches are OR-composed; an allowed field never masks a denial in
another field.

1. Both forbidden `change_id` literals are compared with
   `authored_for_change_id` and every authenticated ancestor's change ID.
2. The forbidden dependency, every interface identifier, and the module
   exact-or-dot-descendant predicate are each compared independently with
   every `derivation_sources[*].identifier` and every authenticated ancestor
   identifier. Classification under another `kind` does not suppress a match.
3. Every path rule is applied to `logical_path`, every non-null
   `derivation_sources[*].path`, and every authenticated ancestor path.
4. Every whole-artifact digest is compared with `source_sha256`, every
   non-null `derivation_sources[*].sha256`, and every authenticated ancestor
   hash.
5. Transitive derivation is the least fixed point over exact authenticated
   `(path,sha256)` references in the later plan-bound normative-source catalog
   and external provenance DAG. Unknown, missing, hash-inconsistent, or cyclic
   references reject; a denial at any depth rejects the descendant.

The same identity appearing in an unanticipated field of this closed schema
rejects rather than laundering the identity. Specifically, a harmless
identifier plus a denied path or hash, a harmless path plus a denied
identifier, a denied identity mislabeled as a language/standard source, a
`PCFL_V11_NORMATIVE` source with null custody, and any V7-true boolean all
reject. Free-text attestation is not a provenance escape and supplies no
derivation edge.

The future boundary member's external provenance row must have exactly one
derivation source and no other source:

```text
{
  kind:"PCFL_V11_NORMATIVE",
  identifier:"V11-NORMATIVE-DENIAL-CORPUS",
  path:CORPUS_PATH,
  sha256:CORPUS_SHA256
}
```

Its `authored_for_change_id` is C11, its V7 flags are false, and it uses the
same attestation template. Its `logical_path`, `source_sha256`, and grant hash
remain integration-bound because no V11 source plan or grant exists here.

Every eventual member provenance row must remain external in the nonmember
manifest under the inherited acyclic sidecar law. The corpus itself is never a
source-plan entry, source member, manifest entry, provenance row, manifest
output, candidate input, preparation input, or runtime input. It is bound only
as a governance input to the later plan/grants/state. This sentence supersedes
v1 section 5's erroneous requirement to place the corpus in the external
manifest.

## 3. Explicit V11-only embedded-artifact supersession proposal

There is no target-free algorithm that proves absence of an arbitrary,
unframed hidden substring whose bytes/preimage are unavailable. V2 therefore
does not claim that power and does not silently weaken the inherited V5 phrase
“embedded golden report.” Instead it proposes the following named, V11-only
human decision:

```text
V11-EMBEDDED-ARTIFACT-SUPERSESSION:
For C11 only, the inherited embedded-artifact digest predicate is superseded
by SHA-256 checks of (a) each complete candidate member and (b) every member of
a closed authenticated EmbeddedMemberInventoryV1 that is either explicitly
declared by the bound V11 source plan or has a byte range proven by an exact,
plan-bound length-delimited format schema. No arbitrary substring scan or V7/V5
preimage is required or claimed. Every undeclared resource, unbound format,
ambiguous boundary, overlap, out-of-range range, missing member, or digest
mismatch fails closed before projection.
```

Human ratification must quote that identifier and bind this advisory hash and
the exact corpus path/hash/length. Generic approval, corpus approval without
the supersession, or inheritance by silence does not adopt it. Until that
separate exact decision is present, the inherited embedded predicate remains
unresolved for V11 and no source-authoring or preparation grant may issue.

`EmbeddedMemberInventoryV1` is produced and authenticated only by a later
integrated V11 plan/guard design. Each row must at least bind parent
path/hash, member identifier and media type, byte offset, byte length, member
SHA-256, delimitation mode
`SOURCE_PLAN_DECLARED|FORMAT_SCHEMA_LENGTH_DELIMITED`, and, for the latter,
the exact format-schema path/hash. Those final schemas and producers are not
created or authorized here.

## 4. Frozen synthetic bytes, matcher corpus, cases, and receipts

The unit matcher uses exactly four harmless ASCII byte strings. The terminal
`0a` shown below is part of the first, second, and fourth fixtures:

| fixture | exact hex bytes | nbytes | SHA-256 |
|---|---|---:|---|
| `V11-SYNTH-WHOLE` | `5631315f53594e54485f57484f4c455f41525449464143540a` | 25 | `da867dbd6efb7e026a84aff6092286075357eadba40f228220a292ad23bae395` |
| `V11-SYNTH-EMBEDDED` | `5631315f53594e54485f454d4245444445445f4d454d4245520a` | 26 | `b11f8c0ab05bac5c7706d6ee73c2116b7611106d9c1500b2016b0a349899f6f0` |
| `V11-SYNTH-CONTAINER` | `484541445631315f53594e54485f454d4245444445445f4d454d4245520a5441494c` | 34 | `0ef9defdeba49dd31ae0879d1a35d015a97b6f418181dabcc7ed82881124f870` |
| `V11-SYNTH-HARMLESS` | `5631315f53594e54485f4841524d4c4553530a` | 19 | `a3a0a8fc8f794d00dac2a73dffb4d52c36b391c4dffb37456dfae8cf17d2bb46` |

The embedded member is exactly the container half-open byte range `[4,30)`.
The wrong-offset range `[5,31)` hashes to
`881f76334b1261a408a10b742ad5301ea2ab3820a30e28e2043af037d9e60210`;
the wrong-length range `[4,29)` hashes to
`c6f027e9be740803b50d8516cc763353fb26e569e799fdfea4bb0ba5f8fcf4f3`.

The temporary matcher corpus is exactly this single JCS line plus one LF:

```json
{"artifact_type":"pcfl_v11_synthetic_temporary_matcher_corpus","embedded_member_sha256":["b11f8c0ab05bac5c7706d6ee73c2116b7611106d9c1500b2016b0a349899f6f0"],"schema_version":1,"whole_artifact_sha256":["da867dbd6efb7e026a84aff6092286075357eadba40f228220a292ad23bae395"]}
```

It is 270 bytes and has SHA-256
`87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293`.
It is a unit input only and cannot pass the production corpus identity gate.

The complete case registry is the following JCS line plus one LF. Case rows
are sorted by `case_id`; their shape is closed and every field is required:

```json
{"artifact_type":"pcfl_v11_synthetic_matcher_case_registry","cases":[{"case_id":"SYNTH-EMBEDDED-MATCH","expected_outcome":"MATCH","input_sha256":"b11f8c0ab05bac5c7706d6ee73c2116b7611106d9c1500b2016b0a349899f6f0","matcher_operation":"DECLARED_MEMBER_SHA256","member_nbytes":26,"member_offset":4,"parent_sha256":"0ef9defdeba49dd31ae0879d1a35d015a97b6f418181dabcc7ed82881124f870","temporary_corpus_sha256":"87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293"},{"case_id":"SYNTH-EMBEDDED-WRONG-LENGTH","expected_outcome":"NO_MATCH","input_sha256":"c6f027e9be740803b50d8516cc763353fb26e569e799fdfea4bb0ba5f8fcf4f3","matcher_operation":"DECLARED_MEMBER_SHA256","member_nbytes":25,"member_offset":4,"parent_sha256":"0ef9defdeba49dd31ae0879d1a35d015a97b6f418181dabcc7ed82881124f870","temporary_corpus_sha256":"87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293"},{"case_id":"SYNTH-EMBEDDED-WRONG-OFFSET","expected_outcome":"NO_MATCH","input_sha256":"881f76334b1261a408a10b742ad5301ea2ab3820a30e28e2043af037d9e60210","matcher_operation":"DECLARED_MEMBER_SHA256","member_nbytes":26,"member_offset":5,"parent_sha256":"0ef9defdeba49dd31ae0879d1a35d015a97b6f418181dabcc7ed82881124f870","temporary_corpus_sha256":"87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293"},{"case_id":"SYNTH-TEMP-AS-PRODUCTION","expected_outcome":"IDENTITY_REJECTED","input_sha256":"87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293","matcher_operation":"PRODUCTION_CORPUS_IDENTITY","member_nbytes":null,"member_offset":null,"parent_sha256":null,"temporary_corpus_sha256":"87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293"},{"case_id":"SYNTH-WHOLE-MATCH","expected_outcome":"MATCH","input_sha256":"da867dbd6efb7e026a84aff6092286075357eadba40f228220a292ad23bae395","matcher_operation":"WHOLE_ARTIFACT_SHA256","member_nbytes":null,"member_offset":null,"parent_sha256":null,"temporary_corpus_sha256":"87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293"},{"case_id":"SYNTH-WHOLE-NONMATCH","expected_outcome":"NO_MATCH","input_sha256":"a3a0a8fc8f794d00dac2a73dffb4d52c36b391c4dffb37456dfae8cf17d2bb46","matcher_operation":"WHOLE_ARTIFACT_SHA256","member_nbytes":null,"member_offset":null,"parent_sha256":null,"temporary_corpus_sha256":"87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293"}],"schema_version":1}
```

It is 2,369 bytes and has SHA-256
`eb749849e9dda68b9b86c7f289b3eb8261107e973e4d78978c3ae43708643917`.

Future execution evidence, if separately authorized, has this closed receipt
shape; no receipt is asserted to exist now:

```text
SyntheticMatcherReceiptV1 := {
  schema_version:1,
  artifact_type:"pcfl_v11_synthetic_matcher_receipt",
  temporary_corpus_sha256:
    "87a248570fa3eaefd535c75ff7f5457a93654700e8cc3761d4d6de7afe3f6293",
  case_registry_sha256:
    "eb749849e9dda68b9b86c7f289b3eb8261107e973e4d78978c3ae43708643917",
  case_results:[{
    case_id:one of the six literal registry IDs,
    input_sha256:the registry value,
    computed_sha256:hex64,
    expected_outcome:"MATCH"|"NO_MATCH"|"IDENTITY_REJECTED",
    observed_outcome:"MATCH"|"NO_MATCH"|"IDENTITY_REJECTED",
    target_read_count:0,
    passed:boolean
  }, ...],
  target_read_count:0,
  passed:boolean
}
```

`case_results` has exactly six rows in registry order. For a passing receipt,
each computed digest equals its registry `input_sha256`, observed equals
expected, every row passes, both target-read counters are zero, and top-level
`passed` is true. A computed digest supplied without the exact fixture bytes,
a metadata-only digest injection, an omitted/extra/reordered case, or any
target read rejects.

The separately required production identity receipt has the closed shape:

```text
ProductionDenialCorpusIdentityReceiptV1 := {
  schema_version:1,
  artifact_type:"pcfl_v11_production_denial_corpus_identity_receipt",
  expected_path:CORPUS_PATH,
  observed_path:repo_relative_normalized_posix_path,
  expected_sha256:CORPUS_SHA256,
  observed_sha256:hex64,
  expected_nbytes:3880,
  observed_nbytes:u64,
  canonical_jcs_plus_one_lf:boolean,
  target_read_count:0,
  passed:boolean
}
```

Pass requires exact path, independently computed corpus hash and length, and
canonical bytes. The synthetic corpus always yields `passed:false` here.

For production candidate/member checks, the guard independently hashes each
authorized C11 byte range and first authenticates it against the later-bound
member/inventory tuple. Only that computed digest is compared with the eleven
production deny digests. Injecting a deny digest into an observation row while
the supplied bytes hash differently is an authentication rejection, not a
positive digest-match test. A real computed equality rejects, but no V7/V5
preimage or positive production payload fixture is claimed or required. The
synthetic cases are the positive algorithm tests.

## 5. Metadata production and authentication are integration-bound

The corpus supplies predicates, not trustworthy observations. It neither
produces nor authenticates resolved paths, module identities, capability
closures, candidate hashes, provenance DAGs, or embedded-member inventories.
Those authorities belong to a later human-ratified V11 source plan and guard.

Before a V11 guard can pass, that integrated packet must bind closed schemas,
producer actor identities, producer source paths and hashes, input-root and
grant hashes, canonical serialization, complete finite closure rules, and
receipt hashes for at least:

- lexical and symlink-resolved path observations;
- import/module/package/resource/subprocess identities;
- all eleven capability surfaces and their transitive target closure;
- complete candidate/member byte observations;
- the external provenance DAG; and
- `EmbeddedMemberInventoryV1` with its delimitation proofs.

The bound producer must be governance-only, operate under an exact later
grant, inspect only the C11 plan-authorized bytes/metadata, and never open,
stat, resolve through, hash, import, deserialize, or execute a denied V7/V5
target. Missing producer identity, schema, root, closure, input hash,
authentication link, surface, target, parent, or receipt; an opaque dynamic
edge; or any inconsistent duplicate fails closed with no
`V7GuardProjectionV1`. This v2 intentionally does not name those later paths,
hashes, schemas, or actors and therefore cannot itself support a production
guard pass.

## 6. Finite actor/model identity and noninterference rule

For corpus-level checking, `STATIC_PRIVATE_IDENTITY_SET_V11` is exactly the
set union of:

1. the eight `resolved_path_denials[*].path` strings;
2. the eleven `whole_artifact_sha256` strings (which already include all six
   non-null path-row hashes);
3. the sole module-rule `value`;
4. the two forbidden change-ID values and sole forbidden dependency value;
5. the twenty-three interface strings;
6. the corpus `artifact_type`, `change_id`, `decision`, and
   `coincident_value_rule` strings; and
7. `CORPUS_PATH` and `CORPUS_SHA256`.

It contains exactly 52 distinct strings; it is not enlarged by directory scan,
target discovery, substring inference, or unspecified “corpus metadata.”
`PRIVATE_GUARD_STATUS_SET_V11` is exactly
`{"SOURCE_BOUNDARY_REJECTED"}`; failure has no detail payload.

The future authenticated finite observation bundle must separately seal
`MATCHED_OBSERVED_IDENTITY_SET_V11`, containing every observed path/module/
identifier string that matched a corpus predicate. This is finite over that
closed bundle and never populated by reading a denied target. Before the final
V11 packet binds that exact bundle schema and producer, this dynamic set is
unavailable and the guard fails closed.

No string in the union of those three finite sets may enter any of the exact
twenty-two corpus-listed actor/model sinks. This literal rule is supplemented,
not replaced, by inherited noninterference: for governance-private inputs with
the same guard result and the same exact projected non-boundary path array,
every downstream semantic/public byte, length, ordering, padding, filename,
cache/index state, error surface, timing surface, tokenizer/model input, and
scientific receipt is identical. A pass-to-fail change has exactly one effect:
absence of the projection. This handles encoding and causal channels without
pretending the finite literal set detects arbitrary substrings.

The integer `1` used for schema metadata is not a denied PCFL value and is not
in the string identity set. An independently derived ordinary `1` remains
permitted when no bound denial predicate or private causal edge is true.

## 7. Exact mutation obligations introduced by v2

These are case obligations for later integration under existing V7 guard
acceptance ownership; they add no test record, condition, call, slot, root,
token allowance, endpoint, gate, or claim.

1. Projection cases independently alter every constant, array, path/hash pair,
   the five-versus-six digest split, a sort order, and the eleven-digest union;
   each rejects without boundary bytes. The exact projection above passes.
2. Provenance cases independently mutate every top and nested field, V11 kind,
   path/hash nullability, catalog binding, order, duplicate, grant hash,
   attestation, and each V7 boolean. Cross-field cases place every denial class
   in each other identity-bearing field; none is rescued by an allowed field
   or `kind`. Unknown parent, wrong hash, missing parent, cycle, and denied
   multi-hop ancestor reject.
3. The boundary provenance positive has exactly the one corpus source tuple.
   Added sources, corpus-as-manifest-member, a row for the corpus or manifest,
   self-hashing, and an embedded provenance row reject.
4. The exact six synthetic cases and both receipt schemas in section 4 are
   mandatory. Digest-field injection without matching bytes rejects as
   unauthenticated and does not count as positive hashing coverage.
5. Embedded cases cover whole file, declared `[4,30)` match, wrong offset,
   wrong length, overlap, out-of-range, missing member, unbound format schema,
   and undeclared resource. No case reads or reconstructs V7/V5 bytes.
6. Every missing or inconsistent metadata producer/schema/root/closure/grant/
   receipt field in section 5 yields no projection.
7. Each of the 52 static private strings, the one private status string, and
   every sealed observed match is injected independently into each of the
   twenty-two sinks and rejects. Equal-result/pathset private-input twins must
   have identical downstream observations.
8. Schema mutations distinguish the legal metadata integer `1` from a
   positive PCFL semantic value and independently reject a positive answer,
   score, expected-output, carrier, or model-visible corpus field.

## 8. Items deliberately left for the complete V11 successor

This advisory is an exact corpus/matcher and ratification proposal, not the
integrated V11 successor. A later packet must still define and hash-bind, with
no inference from a directory or previous version:

- exact V11 `PLAN_PATH`, `MANIFEST_PATH`, `BOUNDARY_PATH`, all source paths,
  the literal sorted non-boundary projection array, roles, media types, byte
  ceilings, member booleans, and plan/manifest counts;
- a closed plan `governance_inputs` singleton for
  `(CORPUS_PATH,CORPUS_SHA256,CORPUS_NBYTES)` and no manifest entry/member for
  the corpus;
- the exact source-authoring grant, external manifest, one external
  `SourceProvenanceRowV1[C11]` per member, governance exact-byte-review grant
  and receipt, source consensus, exact-byte ratification, later preparation
  grant, guard source, guard projection, and their actor/custody order;
- the producer/authentication schemas and finite observations required by
  sections 3, 5, and 6;
- explicit human adoption of `V11-EMBEDDED-ARTIFACT-SUPERSESSION` and exact
  human ratification of the corpus and this advisory;
- effective registry fixture mapping without adding or renaming a registered
  test, and exact inheritance of the 32 nine-field records;
- exact inheritance of the 18-condition roster, 501 slots/root, 148,224
  generated-token allowance/root, 16 DEV / 32 CONFIRMATION / 16 RESERVE split,
  24 sentinels, active totals, delayed-baseline semantics, resource schema,
  equality/accounting laws, endpoints, gates, and claim limits; and
- complete workflow contexts, directive, source plan, state, hashes, zero
  attempts/artifacts, file-size limits, and deliberation-only runner boundary.

Until every item is bound and independently preflighted, C11 is not ready for
source authoring, review, preparation, or execution. The exact V10 constants
are inherited semantic references only; blind `_v10` to `_v11` substitution
is forbidden.

## 9. Stop boundary

This v2 creates one source-only advisory and changes no corpus or predecessor
bytes. It performs no live V7/V5 read or hash, target discovery, source
authoring, import, parse, syntax check, preparation, implementation,
materialization, fixture/root/data generation, checker/test run, model or
tokenizer call, benchmark, training, LoRA/adapter/checkpoint operation,
parenting, GPU use, resource acquisition, scientific execution, claim,
release, or submission. It creates no source plan, grant, manifest, provenance
row, boundary source, receipt, ratification, guard output, prepared artifact,
or scientific artifact. Only a future exact human decision may ratify the
corpus, this advisory, and the separately named supersession.
