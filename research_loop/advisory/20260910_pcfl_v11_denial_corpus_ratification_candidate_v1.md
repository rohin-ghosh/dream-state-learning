# PCFL V11 normative-denial-corpus ratification candidate v1

Date: 2026-09-10

Status: **source-only governance proposal; not ratified**. This advisory and
the proposed corpus authorize no candidate source authoring, source import or
execution, parsing through a candidate interpreter, syntax checking,
preparation, implementation, materialization, fixture/root/data generation,
checker/test execution, model/tokenizer call, benchmark, training,
LoRA/adapter/checkpoint work, parenting, GPU use, resource acquisition,
scientific claim, release, or submission.

## 1. Exact proposed governance input

The proposed V11 governance-only input is:

```text
path:
  research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json
SHA-256:
  4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799
nbytes:
  3880
encoding:
  RFC 8785 / JCS canonical JSON plus exactly one LF
```

The object is a proposed negative governance specification derived only from
the finite paths, hashes, identifiers, and predicates already supplied in
`20260910_pcfl_v5_authority_handoff_delayed_v7_source_repair_v1.md`. No live
FeltCraft V7/V5 target was opened, read, imported, executed, or rehashed to
construct it. The historical digest strings are normative deny values, not a
claim that a live target was reread or still has those bytes.

The object contains no positive PCFL semantic value, answer, score, expected
output, fixture truth, carrier content, model-visible field, or scientific
result. `0`, `1`, `4`, `8`, and `16` are absent as positive PCFL semantic
values; `1` occurs only as the required schema-version metadata. The
coincident-value rule permits independently derived ordinary values unless a
finite bound denial predicate is true.

Human ratification, if granted, must name the exact path, SHA-256, byte length,
and canonicalization above. A semantically equal but byte-different object is
not ratified by reference to this candidate.

## 2. Recursive closed schema

All objects are recursively closed: every listed field is required and no
additional field is legal. JSON duplicate keys reject before canonicalization.
`hex64` is a lowercase 64-character hexadecimal string. Every string is NFC
UTF-8 without control characters. Every enum is case-sensitive.

```text
V11NormativeDenialCorpusV1 := {
  actor_model_exposure_denials: [ActorModelSink, ...],
  artifact_type: "pcfl_v11_normative_denial_corpus",
  change_id: "chg_20260910_pcfl_m0_mtext_bound_v11",
  coincident_value_rule: "NO_EDGE_WITHOUT_A_BOUND_DENIAL_PREDICATE",
  decision: "ZERO_RUNTIME_REUSE",
  distinctive_interface_identifiers: [DistinctiveIdentifier, ...],
  forbidden_declared_provenance_identities: [ProvenanceRule, ...],
  module_identity_denials: [ModuleRule, ...],
  reachable_capability_denials: [CapabilitySurface, ...],
  resolved_path_denials: [PathDenial, ...],
  schema_version: 1,
  whole_artifact_sha256: [hex64, ...]
}

PathDenial := {
  kind: "DENIED_PREFIX" | "DENIED_EXACT" | "GOVERNANCE_ONLY_SOURCE",
  path: repo_relative_normalized_posix_path,
  sha256: null | hex64
}

ModuleRule := {
  match: "EXACT_OR_DOT_DESCENDANT",
  value: "feltcraft_symbolic_kernel"
}

ProvenanceRule := {
  field: "change_id" | "dependency" | "identifier" | "module" | "path" |
         "sha256" | "transitive_derivation_ancestor",
  match: "EXACT" | "MEMBER_OF" | "RULESET" | "ANY_DENIED_IDENTITY",
  value: nonempty_ascii_string
}
```

There are exactly seven array-valued top-level fields and their cardinalities
are exact:

| field | length | exact content class |
|---|---:|---|
| `resolved_path_denials` | 8 | two prefix rows, five governance-only source path/hash identities, and one exact V5 golden path/hash |
| `module_identity_denials` | 1 | exact-or-dot-descendant module rule |
| `whole_artifact_sha256` | 11 | the five supplied source digests and six supplied distinctive-artifact digests |
| `forbidden_declared_provenance_identities` | 8 | two change-ID rules, dependency, interface, module, path, digest, and transitive-denial rules |
| `distinctive_interface_identifiers` | 23 | the fourteen named identifiers plus literal `SK01` through `SK09` |
| `reachable_capability_denials` | 11 | the finite capability surface census |
| `actor_model_exposure_denials` | 22 | the finite downstream sink census |

For `PathDenial`, `DENIED_PREFIX` requires a trailing `/` and `sha256:null`;
`GOVERNANCE_ONLY_SOURCE` requires one of the five exact supplied source paths
and its paired non-null digest; `DENIED_EXACT` requires the exact supplied V5
golden path and paired digest. The governance-only-source classification is
deny metadata and grants no read, import, execution, provenance, or scientific
credit.

The eight provenance rules have only these legal field/match/value tuples:

```text
(change_id, EXACT, chg_20260901_feltcraft_symbolic_kernel_v5)
(change_id, EXACT, chg_20260901_feltcraft_symbolic_kernel_v7)
(dependency, EXACT, FELTCRAFT_SYMBOLIC_KERNEL_V7)
(identifier, MEMBER_OF, distinctive_interface_identifiers)
(module, RULESET, module_identity_denials)
(path, RULESET, resolved_path_denials)
(sha256, MEMBER_OF, whole_artifact_sha256)
(transitive_derivation_ancestor, ANY_DENIED_IDENTITY, DENIED_IDENTITY_UNION)
```

The 23 interfaces, 11 capability surfaces, 22 exposure sinks, eight path rows,
one module row, and 11 digests are the exact literal values in the proposed
corpus. No range abbreviation, alias, case fold, discovered value, directory
scan, current-worktree value, or later V7/V5 value may enlarge or replace an
array.

## 3. Sorting and canonical bytes

The exact serialization is RFC 8785 / JCS over this all-ASCII object, followed
by exactly one byte `0x0a`. The LF is included in the SHA-256 and byte length.
There is no BOM, CR, tab, indentation, or other insignificant whitespace.
Object member names are in JCS order; strings use the shortest required JSON
escaping; the integer is decimal `1`; and null is literal `null`.

String arrays are strictly increasing by raw UTF-8 bytes and duplicate-free.
`resolved_path_denials` is strictly increasing by
`(path,kind,sha256-or-empty)` under raw UTF-8 tuple order.
`forbidden_declared_provenance_identities` is strictly increasing by
`(field,match,value)`. Any reordering, duplicate, normalization change,
uppercase digest, alternate slash, added or removed row, or semantically equal
noncanonical byte representation rejects.

## 4. Exact finite matcher semantics

The matcher consumes only the human-bound corpus, inert C11 candidate/member
bytes, the external source manifest/provenance rows, and closed proposed
read/import/capability/embedded-member metadata. It never discovers a denial
identity from a live V7/V5 target.

### 4.1 Resolved paths

Every observed path is supplied as a normalized, repository-relative POSIX
lexical path and a normalized, symlink-resolved target in the closed capability
metadata. Absolute paths, `.`/`..`, empty components, repeated separators,
backslashes, NUL, unbound symlink hops, missing resolution, and ambiguous
resolution fail closed before matching.

For `DENIED_EXACT` or `GOVERNANCE_ONLY_SOURCE`, the target matches when it is
byte-equal to `path`. For `DENIED_PREFIX` with value `q/`, it matches when the
target equals `q` or begins with `q/`. The guard compares supplied registered
metadata; it must not invoke filesystem resolution on, open, stat, hash, or
otherwise touch a matched target.

### 4.2 Modules and access surfaces

A normalized NFC module identity matches the sole module rule iff it is exactly
`feltcraft_symbolic_kernel` or begins `feltcraft_symbolic_kernel.`. The same
rule is applied to import, package-resource, reflection, plugin, callback,
entry-point, subprocess-module, and dynamically constructed module identities.
Missing or noncanonical resolved module identity fails closed.

### 4.3 Whole artifacts and embedded members

For production checking, SHA-256 is computed only over exact C11 candidate
files and explicitly declared, length-delimited embedded members already
contained in those candidate bytes. A file or declared member matches when its
computed lowercase digest is in `whole_artifact_sha256`. The declared member
inventory is closed and binds parent path/hash, member name/type, byte offset,
byte length, and member SHA-256; overlap, out-of-range bounds, duplicate
identity, uncovered declared resource, or digest mismatch fails closed.

This contract makes no claim to detect an arbitrary hidden substring with no
declared or syntactically length-delimited member boundary. It does prohibit
unregistered resource/import/deserialization/capability channels, and the
other six predicates remain independently mandatory. It never opens or hashes
a V7/V5 target and requires no V7 preimage.

### 4.4 Declared provenance and transitive derivation

A declared provenance identity rejects if any of its exact `change_id`,
`dependency`, `identifier`, `module`, `path`, or `sha256` fields matches its
registered rule. `MEMBER_OF` means literal membership in the named corpus
array. `RULESET` means application of the named finite matcher above.

`DENIED_IDENTITY_UNION` is exactly the finite path values and paired hashes,
the module rule/value, all whole-artifact hashes, the two denied change IDs,
the denied dependency ID, all distinctive identifiers, and the boundary
decision. Transitive derivation is the least fixed point over the declared,
finite, acyclic provenance-parent graph: a node is denied when any ancestor is
already in that union. Unknown parents, cycles, omitted parents, or a claimed
translation without its complete ancestor closure fail closed. No lexical
similarity or generic copied-constant heuristic is added.

The rule applies when the declared source would support executable semantics,
an expected value, a fixture, or a test. Governance-only citation inside the
bound corpus, boundary policy, exact-byte review, or guard evidence is the sole
custody exception and creates no candidate/runtime semantic edge.

### 4.5 Distinctive interfaces

Each of the 23 strings is denied by exact case-sensitive identity when used by
executable, test, or fixture bytes as a dependency or expected-result source.
There is no substring or case-fold match. A governance-only denylist mention
is permitted only in the corpus, boundary, review, and guard custody plane and
must never cross the guard projection.

### 4.6 Reachable capabilities

The closed capability inventory covers exactly the eleven registered surface
classes. For each surface its finite transitive target closure is supplied as
normalized path, module, and exact candidate/member-digest observations. A
surface rejects if any target matches the path, module, or whole-artifact
rules. A reachable but unregistered surface, missing target, opaque dynamic
target, ambiguous resolution, undeclared subprocess/resource/environment/
configuration input, or incomplete transitive closure fails closed. The guard
compares that metadata and never follows a denied edge.

### 4.7 Actor/model exposure and noninterference

No registered denied identity, boundary/corpus metadata, denial detail, or
guard-private decision may directly occur in or causally affect any of the 22
listed sinks. This includes encoded, indirect, ordering, length, padding,
filename, cache/index, error, receipt, timing, and claim channels even when a
literal string comparison would miss them.

For two governance-private boundary/corpus inputs with the same guard pass and
the same literal C11 non-boundary allowlist, every listed sink and every
downstream semantic byte is identical. A pass-to-fail change has exactly one
permitted downstream effect: absence of the projection. Failure emits no
partial projection or preparation-visible error detail.

## 5. Production corpus identity versus unit matcher tests

Production first rehashes this exact corpus as inert governance bytes and
requires the exact ratified path, `3880` bytes, and
`4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799`.
It then requires the same path/hash in the human-required state, plan
`governance_inputs` singleton, source-authoring grant, external manifest,
exact-byte-review grant, exact-byte ratification, and later preparation grant.
A synthetic corpus can never satisfy this production identity check.

Matcher unit tests use only synthetic harmless bytes and a synthetic temporary
matcher corpus whose path/module/interface/change/dependency values and
artifact digests are computed from those known synthetic bytes. The temporary
corpus is never installed, never substituted for the production corpus, never
enters a source manifest or grant, and carries no V7/V5 preimage. This permits
positive exact-file and explicitly length-delimited embedded-member matcher
tests without reading a denied artifact.

Production checking uses the human-ratified corpus's already supplied literal
hashes against C11 candidate/member observations. It does not recreate an
“exact V7 whole-file copy” or “embedded golden report” fixture. Any demand for
the original payload bytes would require a distinct, explicitly authorized and
human-ratified governance-only fixture input; none is supplied or authorized
here.

## 6. Exact mutation obligations

The existing V7 guard/test-01 fixture IDs remain the registered IDs; the cases
below are complete internal case matrices, not replacement or additional
acceptance-test records.

1. Corpus identity/schema cases independently mutate the production path,
   SHA-256, byte length, schema version, artifact type, change ID, decision,
   coincident rule, each top-level field, each row field/type/constant, array
   count, ordering, duplication, NFC, digest case, slash normalization, JCS
   bytes, trailing LF, and an added positive answer/score/expected/carrier
   field. Every mutation rejects before source authoring or guard use.
2. `V7V10-REJ-RESOLVED-PATH` covers every path row and separately covers a
   lexical path whose registered symlink-resolved target hits each prefix and
   the exact path. Missing/ambiguous resolution also rejects.
3. `V7V10-REJ-MODULE` crosses exact and dot-descendant matches with import,
   package resource, reflection, plugin, callback, entry point, subprocess
   module, and dynamically constructed module surfaces.
4. `V7V10-REJ-WHOLE-ARTIFACT` applies every production digest to an observed
   candidate-file row and an explicitly length-delimited declared-member row.
   The matcher algorithm is independently exercised with known synthetic bytes
   and matching synthetic temporary digests. No V7 payload is used.
5. `V7V10-REJ-DECLARED-PROVENANCE` covers each of the eight rules, including a
   multi-hop declared translation whose transitive ancestor is denied, plus
   unknown-parent, missing-parent, and cycle failures.
6. `V7V10-REJ-DISTINCTIVE-INTERFACE` covers each of the 23 identifiers as a
   dependency and as an expected-result source. The same literal in the
   governance-only corpus is the required permitted control.
7. `V7V10-REJ-CAPABILITY` covers all eleven surfaces and each path/module/hash
   target family, plus missing, opaque, ambiguous, and incomplete closures.
8. `V7V10-REJ-ACTOR-MODEL` covers every one of the 22 sinks with direct and
   indirect identity/decision influence. Equal-pass/pathset private-metadata
   twins must remain identical.
9. `V7V10-POS-COINCIDENT-SCALAR` derives ordinary short values only from bound
   V11 normative or named language/standard-library rules and must pass when no
   denial predicate is true.
10. Test-34 cases retain exact corpus/boundary binding, governance custody,
    sole guard consumption, external provenance, four-field literal allowlist,
    private-metadata twins, fail-with-no-projection, second-consumer rejection,
    no denied-target open/hash/import/execute, no self-hashing provenance, and
    no boundary/corpus metadata exposure.

Each mutation changes one named property. A compound mutation cannot replace
an individual case. Missing or nonterminal case evidence is `INCOMPLETE`; an
accepted forbidden case, rejected permitted control, target access, identity
substitution, or nonexposure failure is `INVALID`.

## 7. Required V11 binding and stop boundary

Before any V11 source-authoring decision, a successor packet must bind an exact
source plan whose closed `governance_inputs` array has one row and no extra row
or row field:

```text
{
  role: "V11_NORMATIVE_DENIAL_CORPUS",
  logical_path:
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json",
  sha256: "4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799",
  media_type: "application/json",
  access: "GOVERNANCE_ONLY"
}
```

That row is not a source-plan entry, manifest member, authored source, manifest
output, candidate/preparation/runtime input, model input, fixture, or scientific
artifact. The separately ratified corpus must also be an exact workflow/state
source binding. The source plan hash must transitively bind it into every later
grant and state. No source-plan entry count, member count, role, path, size
ceiling, condition, root, request opportunity, token allowance, endpoint,
claim, or scientific scope changes.

This proposal creates only the two source-only governance artifacts named in
the request. It performs no V7/V5 target read or hash, source authoring,
candidate parse/import/execute/check, preparation, implementation,
materialization, fixture/root/data generation, checker/test run, model or
tokenizer call, benchmark, training, LoRA/adapter/checkpoint operation,
parenting, GPU use, resource acquisition, scientific execution, claim, release,
or submission. It grants and infers no human ratification. A future packet must
bind an explicit human decision over the exact corpus bytes and still stop at
its separately authorized boundary.
