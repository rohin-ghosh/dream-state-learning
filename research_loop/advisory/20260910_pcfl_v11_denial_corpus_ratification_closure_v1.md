# PCFL V11 denial-corpus ratification closure v1

Date: 2026-09-10

Status: **source-only precedence and human-ratification proposal; not
ratified**. This advisory is the sole precedence index for the four-artifact
V11 denial-corpus proposal set below. It authorizes only governance-input
binding and proposal rework if, and only if, a human supplies the exact
sentence in section 3. It authorizes no candidate-source authoring, source
import, candidate parsing or syntax checking, exact-byte candidate
ratification, preparation, implementation, materialization, fixture/root/data
generation, checker or test execution, model/tokenizer call, benchmark,
training, LoRA/adapter/checkpoint work, parenting, GPU use, resource
acquisition, scientific claim, release, or submission.

## 1. Exact bound inputs and sole precedence map

The immutable proposal inputs are:

| role | path | SHA-256 |
|---|---|---|
| corpus | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json` | `4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799` |
| candidate v1 | `research_loop/advisory/20260910_pcfl_v11_denial_corpus_ratification_candidate_v1.md` | `492980e15c8c35a16adcf6067aba0acdb0877944bb3d40a53c5bacf346b54357` |
| candidate v2 | `research_loop/advisory/20260910_pcfl_v11_denial_corpus_ratification_candidate_v2.md` | `c1d109309804a6defadd1643c5259eeaec6a0471ca74bf659800e50234339f81` |
| provenance repair v1 | `research_loop/advisory/20260910_pcfl_v11_denial_corpus_provenance_repair_v1.md` | `8d0c28201cec2e695d2a615ca2d8b9230bfee28c032b887096b24332d7431e65` |

For this advisory, `C11` means exactly
`chg_20260910_pcfl_m0_mtext_bound_v11`. The corpus is exactly 3,880 bytes of
RFC 8785/JCS JSON plus one LF, with that LF included in its digest and byte
length.

This file, and no earlier advisory, is the precedence index. The controlling
clauses are exactly:

1. Candidate v1 sections 1--3 and 4.1--4.2 control **only** the corpus
   path/hash/length, recursively closed corpus schema, exact seven arrays and
   five scalars, cardinalities, path/hash row constraints, sorting,
   RFC-8785/JCS-plus-one-LF bytes, resolved-path matcher, and
   exact-or-dot-descendant module matcher. Ratification, authority, manifest,
   receipt, exposure, provenance, whole/embedded-artifact, mutation, and later
   integration wording inside or outside those sections does not control.
2. Provenance repair v1 sections 2 and 3 control the exact
   `BoundaryProjectionFromCorpusV1`, `V7BoundaryV1[C11]`, external
   `SourceProvenanceRowV1[C11]`, cross-field anti-laundering matcher, external
   placement, attestation, and the boundary row with exactly the two sorted
   `PCFL_V11_NORMATIVE` derivation sources and no third.
3. Provenance repair v1 section 4.1 controls the exact V11-only
   whole/embedded-artifact supersession, named in section 2 below.
4. Provenance repair v1 sections 4.2 and 4.3 control the four exact harmless
   byte strings, 270-byte temporary matcher corpus, 2,369-byte six-case
   registry, `SyntheticMatcherReceiptV1`, and
   `ProductionDenialCorpusIdentityReceiptV1`.
5. Provenance repair v1 section 5 controls the closed
   `AuthenticatedDenialObservationBundleV1`, completeness/rejection laws,
   analyzer authentication obligation, and no-denied-target-access rule.
6. This closure controls precedence, the named supersession, human evidence,
   exposure, authority scope, and the remaining integration boundary.

No other clause controls this proposal. In particular:

- candidate v2's one-source boundary provenance rule is superseded by the
  repair's exact two-source rule;
- candidate v2's independently worded embedded supersession is superseded by
  repair section 4.1;
- candidate v2's exposure sets and both receipt schemas are superseded by
  this closure and repair sections 4.2--4.3, respectively;
- provenance repair section 0's structured
  `V11DenialCorpusRatificationV1` prerequisite is superseded by section 3 of
  this closure;
- provenance repair sections 1 and 6 do not define the controlling exposure
  set; section 4 below does; and
- provenance repair sections 7--8 are nonauthoritative design notes except
  where section 5 of this closure restates an item as an unresolved
  integration obligation.

Candidate v2 remains hash-bound because it is part of the reviewed proposal
history and is the source from which the repair adopted the exact harmless
fixtures. Hash-binding it does not revive any superseded clause.

## 2. Exact named V11 embedded-artifact supersession

The following exact repair-section-4.1 decision is named
`V11-EMBEDDED-ARTIFACT-SUPERSESSION`:

> For C11 only, I supersede the V5 phrase “embeds one of those whole artifacts
> as a byte-for-byte member” and the corresponding production fixture meaning
> with “an entire non-governance candidate/input/output byte object, or an
> explicitly enumerated length-delimited member whose bytes are a verified
> in-bounds slice of such an object, has a SHA-256 in the ratified eleven-value
> deny array.” C11 does not claim arbitrary undeclared-substring detection.

The name denotes that whole quoted text, including both sentences and no
variation. It retains repair section 4.1's requirement that every archive,
package-data, deserialized, fixture, static-literal, or other resource exposed
by the closed capability inventory have an exact enumerated member row.
Unenumerated, opaque, overlapping, out-of-range, ambiguously delimited, or
digest-inconsistent resources fail closed. The decision supplies no V7/V5
preimage and authorizes no target read.

## 3. Exact sufficient human authorization evidence

The sole sufficient human authorization evidence for this proposal is a
human-authored occurrence of the following exact one-sentence template after
replacing its only angle-bracket token with the lowercase SHA-256 of this
closure's final bytes:

> I ratify only the negative governance input at research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json (SHA-256 4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799, 3880 bytes, RFC 8785/JCS plus exactly one LF), bind the sole precedence index research_loop/advisory/20260910_pcfl_v11_denial_corpus_ratification_closure_v1.md at SHA-256 <CLOSURE_SHA256>, and expressly adopt V11-EMBEDDED-ARTIFACT-SUPERSESSION exactly as defined there; I authorize only governance-input binding and proposal rework for a future V11 deliberation packet, and I do not authorize source authoring, exact-byte candidate ratification, preparation, implementation, materialization, fixture/root/data generation, checker/test/model/tokenizer/benchmark/training/GPU/scientific execution, resource acquisition, claim, release, or submission.

There is no other placeholder. The sentence is sufficient only when supplied
by the human authority; a model, advisory author, workflow, reviewer,
consensus, state transition, or generated file cannot issue or infer it.
Semantically similar text, a different path/hash/length/encoding, an omitted
clause, generic approval, or a sentence with added authority does not match.

The human evidence artifact's path and digest must be bound later as role
`V11_CORPUS_RATIFICATION_EVIDENCE` in section 4's census. Its exact sentence
binds this closure hash, and this closure transitively binds the corpus and all
three predecessor advisory hashes. This avoids storing this closure's own
hash in its bytes. No self-hash is present in this file.

A future JSON transcription is optional, not an authority prerequisite. If
one is created, its only allowed path is:

```text
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_denial_corpus_ratification_record.json
```

It may copy the evidence path/hash, exact sentence, closure path/hash, corpus
path/hash/length/encoding, human identity, and decision time. It must label
itself `NONAUTHORITATIVE_TRANSCRIPTION`, add no operation or authority, and
bind the already-existing human evidence. It cannot issue, replace, broaden,
or repair the sentence. Its absence does not invalidate otherwise exact human
evidence.

## 4. Closed finite exposure policy

### 4.1 Static sensitive literals

Let `PRODUCTION_DENIAL_OPERANDS_C11` be exactly the set union of:

1. the eight corpus `resolved_path_denials[*].path` strings;
2. the eleven corpus `whole_artifact_sha256` strings, which include all six
   non-null resolved-path-row hashes;
3. the sole corpus `module_identity_denials[0].value` string;
4. the two forbidden change-ID values and the one forbidden dependency value;
5. the twenty-three corpus `distinctive_interface_identifiers` strings; and
6. the corpus decision string `ZERO_RUNTIME_REUSE`.

It has exactly 47 distinct strings. `STATIC_SENSITIVE_LITERALS_C11` is exactly
that set plus these ten distinct strings:

```text
V11-DENIAL-CORPUS-PROJECTION-RULE
V11-NORMATIVE-DENIAL-CORPUS
SOURCE_BOUNDARY_REJECTED
chg_20260910_pcfl_m0_mtext_bound_v11
pcfl_v11_normative_denial_corpus
pcfl_m0_v7_boundary
pcfl_m0_source_provenance
NO_EDGE_WITHOUT_A_BOUND_DENIAL_PREDICATE
V11-EMBEDDED-ARTIFACT-SUPERSESSION
RATIFY_NEGATIVE_GOVERNANCE_INPUT_ONLY
```

It has exactly 57 distinct strings. This is a closed literal set, not shorthand
for “corpus metadata,” a directory scan, target discovery, substring
inference, case folding, aliases, schema keys, matcher enums, or numeric
schema metadata. The exact two normative-source identifiers, private failure
status, C11/change identifier, corpus/boundary/provenance artifact types,
decision, coincident rule, named supersession, and ratification decision are
therefore explicit.

### 4.2 Later bound governance role census

After all listed operational governance artifacts exist, a final
governance-only `BoundGovernanceRoleCensusV1[C11]` must bind their exact paths
and hashes without self-reference:

```text
BoundGovernanceRoleCensusV1[C11] := {
  schema_version:1,
  artifact_type:"pcfl_v11_bound_governance_role_census",
  change_id:"chg_20260910_pcfl_m0_mtext_bound_v11",
  closure_sha256:hex64,
  entries:[{
    role:GovernanceRoleV11,
    present:boolean,
    path:null|repo_relative_normalized_posix_path,
    sha256:null|hex64
  }, ...]
}
```

`GovernanceRoleV11` is exactly this bytewise-sorted enum, with exactly one
entry per line and no other role:

```text
V11_AUTHENTICATED_DENIAL_OBSERVATION_BUNDLE
V11_CORPUS_RATIFICATION_EVIDENCE
V11_CORPUS_RATIFICATION_RECORD
V11_DENIAL_CORPUS_CANDIDATE_V1
V11_DENIAL_CORPUS_CANDIDATE_V2
V11_DENIAL_CORPUS_PRECEDENCE_CLOSURE_V1
V11_DENIAL_CORPUS_PROVENANCE_REPAIR_V1
V11_EXACT_BYTE_RATIFICATION
V11_EXACT_BYTE_REVIEW_GRANT
V11_EXACT_BYTE_REVIEW_RECEIPT
V11_EXACT_BYTE_SOURCE_CONSENSUS
V11_HUMAN_DIRECTIVE
V11_HUMAN_REQUIRED_STATE
V11_INITIAL_SOURCE_ONLY_CONSENSUS
V11_NORMATIVE_DENIAL_CORPUS
V11_NORMATIVE_SOURCE_MANIFEST
V11_PREPARATION_EXECUTION_GRANT
V11_SOURCE_AUTHORING_GRANT
V11_SOURCE_AUTHORING_PLAN
V11_V7_BOUNDARY_MEMBER
V11_V7_GUARD_RECEIPT
V11_V7_GUARD_SOURCE
V11_WORKFLOW
```

There are exactly 23 entries in that order. All entries except
`V11_CORPUS_RATIFICATION_RECORD` require `present:true` and non-null path/hash.
The optional record entry is either `present:false,path:null,sha256:null` or
`present:true` with the sole path in section 3 and its computed digest. No
other null is legal. Paths are normalized repository-relative regular-file
paths; duplicates, symlinks, aliases, directories, globs, URIs, unresolved
paths, uppercase hashes, duplicate content under another role, missing roles,
or extra fields reject.

The corpus and three predecessor advisory entries must equal section 1. The
closure entry uses this file's path and the hash supplied by exact human
evidence; that hash is not stored in this file. The final census is created
only after the last listed guard artifact is sealed, is hash-bound by a later
governance state/audit, grants no authority, and is not an input to the guard
whose outputs it records. The census itself is not an entry, so it contains no
self hash. Each earlier authority stage must independently bind the exact
then-existing subset in its closed state/grant; no future hash is guessed.

Define `BOUND_GOVERNANCE_LITERALS_C11` as every non-null `role`, `path`, and
`sha256` string in a valid final census. Define
`MATCHED_OBSERVED_LITERALS_C11` as every exact path, module, identifier, or
digest string in a complete, repair-section-5
`AuthenticatedDenialObservationBundleV1` that matches a corpus predicate.
Both sets are finite, bytewise sorted, duplicate-free, and fixed by their
bound input hashes. They cannot be populated by opening a denied target.

### 4.3 Sink ban and noninterference

Direct occurrence of any member of
`STATIC_SENSITIVE_LITERALS_C11 union BOUND_GOVERNANCE_LITERALS_C11 union
MATCHED_OBSERVED_LITERALS_C11` in any of the corpus's exact twenty-two
actor/model sinks rejects. Governance-only custody in the exact human
evidence, bound advisories, source plan/state/grants, external manifest and
provenance, governance review/consensus/ratification, guard receipt,
observation bundle, and census is the only storage exception; none may cross
the guard projection.

Literal matching is supplemented by causal noninterference. For two complete
governance-private inputs with the same guard pass and the same literal
non-boundary projection path array, every downstream semantic byte and every
one of the twenty-two sink observations must be identical, including length,
ordering, padding, filename, cache/index state, public error, timing,
tokenizer/model input or state, receipt, and claim. A pass-to-fail change may
cause exactly one downstream effect: absence of the projection. Failure emits
no projection, partial pathset, public/preparation-visible error, or detail;
its sole governance-private status is `SOURCE_BOUNDARY_REJECTED`.

The later integration must bind a closed total mapping from every downstream
field to exactly one of the twenty-two sink labels and rejection fixtures for
direct, encoded, causal, second-consumer, and equal-pass/pathset twin leaks.
Missing or multiply classified fields reject. Until the exact census,
authenticated observation bundle, mapping, and fixtures are bound, exposure
closure remains `REWORK`.

## 5. Remaining V11 integration blockers

Exact human use of section 3 closes only corpus interpretation and permits
only governance-input binding/proposal rework. The following remain blockers
to source authoring, byte review, preparation, or execution:

1. No complete V11 deliberation packet yet binds the exact workflow,
   directive, all contexts, this closure and human evidence, candidate/plan/
   scope/state hashes, zero attempts/artifacts, file-size ceilings, and a
   deliberation-only runner.
2. No effective V11 integration advisory yet defines one exact sorted source
   plan, all literal source paths, roles, media types, byte ceilings,
   `manifest_member` flags, the nonmember manifest, boundary path, literal
   non-boundary projection array, or the closed governance-input singleton.
   No V10 path substitution is inferred.
3. No integrated V11 external manifest or complete one-row-per-member
   `SourceProvenanceRowV1[C11]` catalog exists; the two-source boundary row,
   normative catalog, exact attestation, grant hash, source/member hashes, and
   acyclic placement remain future bytes.
4. No human-required V11 source-authoring state or strict
   `SourceAuthoringGrantV1[C11]` exists. The sentence in section 3 is not that
   grant and cannot authorize an Authority-S write or hash.
5. No separately human-issued exact-byte-review grant, independent review
   receipt, fresh exact-byte source consensus, exact-byte ratification, or
   later preparation grant exists; no completion implies the next authority.
6. No integrated analyzer source/path/hash, authenticated observation grammar,
   repair-section-5 bundle instance, complete eleven-surface closure,
   embedded-member inventory, or guard receipt exists. No denied path may be
   opened to fill the gap.
7. No final 23-role census, total twenty-two-sink mapping, or complete direct/
   encoded/causal nonexposure fixture evidence exists.
8. The exact repair-section-4.2 fixtures and section-4.3 receipts are only
   specified; no source fixture member, separately authorized execution, or
   receipt exists. They must integrate under the existing registered test
   ownership without adding a test, condition, model call, endpoint, gate, or
   claim.
9. No V11-scoped resource schema has yet faithfully superseded or explicitly
   parameterized the C10-only `ChargedResourceV10`. The integration must
   preserve all V10 fields/types, extra-field rejection, nonomission equation,
   standalone/physical CAS law, post-origin charging, and exact roster/budget
   ceilings without drift.
10. The effective 32 full nine-field acceptance records, 18-condition roster,
    501 slots and 148,224 generated tokens per ordinary root, 16 DEV / 32
    CONFIRMATION / 16 RESERVE split, 24 sentinels, active maxima of 24,072
    slots and 7,120,896 generated tokens, delayed-baseline rules, endpoints,
    noncompensatory gates, and claim limits have not yet been bound as exact
    V11 integration inputs.
11. The exact human sentence in section 3 has not been supplied merely by
    writing this proposal. Until it is supplied and hash-bound, even
    governance-input binding/proposal rework is not authorized by this file.

## 6. Stop boundary

This advisory writes only one governance proposal. It changes no corpus or
prior advisory byte and contains no self hash. It creates no human evidence,
transcription record, source plan, state, grant, manifest, provenance row,
boundary member, review, consensus, ratification, guard source, observation,
receipt, census, projection, prepared artifact, fixture, data, or scientific
artifact. It performs no live V7/V5 read or hash, source authoring, import,
parse, syntax check, preparation, implementation, materialization,
fixture/root/data generation, checker/test run, model/tokenizer call,
benchmark, training, LoRA/adapter/checkpoint operation, parenting, GPU use,
resource acquisition, scientific execution, claim, release, or submission.
