# PCFL V11 guard-source and plan-supersession closure v2

Date: 2026-09-10

Status: **proposal-only successor; not ratified and not authority**. Despite
the retained filename lineage, this v2 abandons the controllerless design. It
specifies one future governance-only guard source inside the ordinary C11
source-authoring/review/ratification chain. It does not author, parse, import,
review, execute, or ratify that source or any candidate byte, and authorizes
no workflow/model call, preparation, implementation, materialization,
fixture/root/data generation, checker/test/model/tokenizer/benchmark/training/
GPU work, parenting, resource acquisition, scientific claim, release, or
submission.

## 0. Exact inputs and precedence

This closure binds:

| role | path | SHA-256 |
|---|---|---|
| integration candidate v1 | `research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate.md` | `586500e72c6e03da5f9e4e9800094017888e1e4648bb656a2caad82335a8b5bc` |
| integration preflight repair v1 | `research_loop/advisory/20260910_pcfl_v11_integration_preflight_repair_v1.md` | `a9dc887e8acdf5eacb9a5eca6a2f4586e84269b8d15befd110bcf09a9f669f4e` |
| controllerless closure v1 | `research_loop/advisory/20260910_pcfl_v11_controllerless_guard_closure_v1.md` | `37b4098f7cb809a86c3217a4c1267cad62dd799f3403a75c2b871c9f7d2f8f3b` |
| integration candidate v2 | `research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate_v2.md` | `82dc79fe88dd7204898b123c02ce7cabb78761f38b0be0bfc97a248fe8579ffd` |
| source plan v1 | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan.json` | `46263de44eefccc9face8b9cf76fd48986a55e7a527cce1bd32b1bc731ae92ce` |
| source plan v2 | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan_v2.json` | `1b7d618c79379494e98a674e56cae46a8c9346412a4e68d9575b911a9c17076a` |
| current directive | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/human_directive.txt` | `42a678a04fb6be507f7f2adec781c1d9b72f3e7d205387d3fdc79945751cceff` |
| current scope proposal | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/scope_proposal.json` | `ddc4235cacdd5c2fdd27efe97d9ef76756aa8525baaa32e941afac2ba96f381b` |

For C11 only, this closure supersedes controllerless closure v1 in full and
integration preflight repair v1 sections 4--5 in full. It also supersedes only
the independent-checker/parser-disagreement clauses identified in section 4
below; integration preflight repair section 3 otherwise remains the exact
inert observation grammar. Integration candidate v2 is predecessor evidence,
not the controlling successor. Every other effective V10/V11 registry,
provenance, boundary, resource, visibility, authority, roster, and claim rule
is preserved unless this closure expressly replaces it. Any other conflict is
`REWORK`.

Let:

```text
C11 = "chg_20260910_pcfl_m0_mtext_bound_v11"
PLAN_V1_PATH_C11 =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan.json"
PLAN_V1_SHA256_C11 =
  "46263de44eefccc9face8b9cf76fd48986a55e7a527cce1bd32b1bc731ae92ce"
PLAN_V2_PATH_C11 =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan_v2.json"
PLAN_V2_SHA256_C11 =
  "1b7d618c79379494e98a674e56cae46a8c9346412a4e68d9575b911a9c17076a"
GUARD_PATH_C11 =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v7_boundary_guard_controller_v1.py"
```

## 1. Non-self-referential source-plan supersession

The current directive's exact bytes name plan v1 as a proposal packet
primitive. Those bytes remain the verbatim directive and retain only their
stated proposal-rework authority. They do not ratify a source plan or issue a
source-authoring grant. This closure therefore does not alter or silently
reinterpret the directive: it records plan v1 as predecessor evidence and
proposes plan v2 as the sole controlling source plan for a future
deliberation and any later human grant.

A future workflow's `directive_file` must remain the current directive path.
Its `context_files` must contain both exact plan paths, this closure, and the
successor candidate that adopts it. Runner-generated state then binds the
directive first and every context path/hash from the closed workflow. Fresh
five-role deliberation must explicitly adjudicate the v1-to-v2 plan change and
end at `human_required`. Only a later human `SourceAuthoringGrantV1[C11]`
whose `source_authoring_plan_sha256` equals `PLAN_V2_SHA256_C11` can make plan
v2 authoritative for source authoring. A grant naming plan v1, a transitive
reference, or the unchanged directive alone rejects.

No self hash occurs: this closure's final hash is bound later by workflow
context/state, and the successor candidate binds it only after this file is
sealed.

## 2. Exact source plan v2

Plan v2 preserves byte-for-byte all 24 v1 rows and the denial-corpus
`governance_inputs` singleton, then adds exactly one bytewise-sorted row:

```text
{
  logical_path:GUARD_PATH_C11,
  manifest_member:false,
  maximum_nbytes:262144,
  media_type:"text/x-python",
  role:"V11_V7_GUARD_SOURCE"
}
```

The resulting plan has exactly 25 rows: the guard row; the one nonmember
manifest-output row; and the unchanged 23 `manifest_member:true` candidate
rows. It has exactly two false-member rows and 23 true-member rows. Entry
paths remain bytewise sorted. `manifest_output_path` remains
`research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/normative_source_manifest.json`.
The guard is a governance-only source by role and fixed `governance/` path; it
is not a governance input, manifest member, boundary, projected path,
preparation input, runtime input, fixture, model input, or scientific
artifact.

The original 23-role `GovernanceRoleV11` census is unchanged in membership and
order. Its existing `V11_V7_GUARD_SOURCE` role maps only to `GUARD_PATH_C11`
and the final guard-source digest. No grant, review, receipt, controller, or
plan-supersession role is added. The optional corpus ratification record
remains the sole role permitted absent/null.

## 3. Same source-authoring and exact-byte chain

### 3.1 One source grant; no guard-specific authority type

The future source-only consensus and human-required state bind plan v2 and
the exact successor candidate. The same closed
`SourceAuthoringGrantV1[C11]` schema, actor
`AUTHORITY_S_SOURCE_WRITER_HASHER`, three ordered operations, forbidden
operations, evidence, and five authority booleans inherited from the effective
authority repair apply. No guard-source grant or additional actor exists.

For plan v2 only,
`CREATE_OR_EDIT_EXACTLY_LISTED_CANDIDATE_SOURCE_PATHS` authorizes Authority S
to create/edit exactly the 23 true-member source paths plus `GUARD_PATH_C11`,
and no other path. The guard is unratified governance-only candidate source at
this stage. Authority S then performs
`COMPUTE_SHA256_AND_BYTE_LENGTH_OF_LISTED_PATHS` on those 24 source paths and
`WRITE_NONAUTHORITATIVE_NORMATIVE_SOURCE_MANIFEST` for the existing manifest
output. The manifest continues to have exactly 23 member entries and exactly
the inherited 23 external provenance rows; the nonmember guard has no
manifest entry or `SourceProvenanceRowV1[C11]`.

The writer may read the exact plan/grant/human evidence/normative scope and
the denial corpus only as already permitted. It may write/hash the guard but
may not import, parse, syntax-check, compile, invoke, or execute it or any
candidate member. Completion leaves all 24 source bytes and the manifest
unratified and nonconsumable.

### 3.2 Exact review-input binding under the existing review grant

No new review grant or receipt type exists. The existing human
`GovernanceExactByteReviewGrantV1[C11]` binds plan v2, the same source grant,
the 23-entry manifest, the corpus, and
`review_input_binding_sha256`. For C11 plan v2, that last field is exactly
`SHA256_JCS_LF(SourceReviewInputBindingV1[C11])`, where the canonical closed
value is:

```text
SourceReviewInputBindingV1[C11] := {
  schema_version:1,
  artifact_type:"pcfl_m0_source_review_input_binding",
  change_id:"chg_20260910_pcfl_m0_mtext_bound_v11",
  source_authoring_plan_sha256:
    "1b7d618c79379494e98a674e56cae46a8c9346412a4e68d9575b911a9c17076a",
  source_authoring_grant_sha256:hex64,
  normative_source_manifest_sha256:hex64,
  governance_nonmember_sources:[{
    logical_path:GUARD_PATH_C11,
    role:"V11_V7_GUARD_SOURCE",
    media_type:"text/x-python",
    nbytes:u64,
    sha256:hex64
  }]
}
```

`SHA256_JCS_LF` means lowercase SHA-256 of RFC 8785/JCS bytes followed by
exactly one LF. The canonical value is an inline review binding, not a new
governance role, source member, manifest entry, or authority artifact. Its
guard length is positive and at most 262144, and its path/role/media type equal
the plan row. Its plan/grant/manifest hashes rehash the exact named inputs.

The same `INDEPENDENT_EXACT_BYTE_REVIEWER`, under the same existing review
grant, reads and rehashes as inert bytes the plan, source grant, corpus,
manifest, its 23 member/provenance entries, and the one bound guard source.
The same `IndependentExactByteReviewReceiptV1` binds every inherited member
tuple plus the exact inline review binding and observed guard path/role/media/
length/hash. Its sole output remains that one governance-private receipt. The
reviewer may inspect source text but may not import, compile, execute, prepare,
materialize, run a checker/test/fixture, or emit a projection.

Missing guard bytes, wrong guard hash/length/path/role/media, plan-v1
substitution, an extra nonmember, a guard provenance row, a guard manifest
entry, or a reviewer execution attempt rejects the same receipt. No new
receipt or census role is created.

### 3.3 Same consensus and human exact-byte ratification

The fresh five-role exact-byte source consensus consumes the same independent
receipt, exact plan-v2 identity, manifest identity, 22 non-boundary member
bytes, and the exact guard bytes from the inline review binding. It receives
no boundary array or denial detail and stops at `human_required`. The two
candidate checker files remain inert inputs and are not executed.

The same human `ExactByteRatificationV1[C11]` binds plan v2, source grant,
manifest, independent receipt, consensus, and human-required state. Because
the receipt/consensus bind the exact guard tuple, the ratification covers the
guard bytes together with the candidate bytes without adding a field, grant,
receipt, role, or second authoring loop. Ratification authorizes no guard or
candidate execution.

Only a later, separate human `PreparationExecutionGrantV1[C11]` may authorize
one guard invocation as substage zero. It directly binds the plan-v2 hash,
manifest, source exact-byte ratification, exact guard path/hash from the
receipt, corpus, boundary, parser-runtime executable/grammar-library hashes,
one attempt, and the four-field pass-only projection. No prior completion or
favorable consensus implies it.

## 4. Exact guard behavior; no checker bootstrap

At substage zero, the authority-side runner imports or otherwise invokes only
the exact ratified script at `GUARD_PATH_C11`. The script is the existing
`V11_V7_GUARD_SOURCE` actor artifact and performs the inherited
`V7_BOUNDARY_GUARD` governance authority-controller operation. It reads the
exact grant-bound corpus, boundary, manifest/provenance, and 22 non-boundary
members as inert bytes and applies the complete deterministic grammar in
integration preflight repair v1 section 3.

The guard never imports, compiles, invokes, or executes a candidate member.
`source/prepare_v4.py` remains inert until pass and may run only in a later
substage already named by the same preparation grant. Likewise
`source/check_axiomatic_v4.py` and `source/check_constructive_v4.py` remain
inert at substage zero. They neither implement, validate, corroborate, vote
on, nor override the guard.

For C11, delete these requirements from the otherwise inherited repair
section 3:

1. section 3.3's phrase requiring disagreement with either independent
   checker to reject; and
2. section 3.5's sentence requiring the two existing independent checkers to
   separately implement the grammar and agree without guard helpers.

No checker-agreement or parser-disagreement receipt is required. The guard
script must instead fail closed internally on any parser exception, parser or
runtime hash mismatch, unrecognized syntax, missing/extra classification,
unresolved dynamic observation, incomplete eleven-surface graph, denial
match, or failure of any exact repair-section-3 equality. This establishes a
single deterministic gate; it does not claim independently executed guard
implementations or independent runtime validation.

The detailed guard receipt stores the exact guard path/hash, preparation
grant, plan, manifest, corpus, boundary, parser/runtime hashes,
`AuthenticatedDenialObservationBundleV1` hash, pass/failure, and projection
hash or null. The bundle's `analyzer_logical_path` and
`analyzer_source_sha256` are `GUARD_PATH_C11` and the exact ratified guard
digest. This supersedes only provenance repair v1 section 5's requirement
that the analyzer be one of the 22 manifest members; its closed schema and all
other completeness laws remain unchanged. The guard is the sole
candidate/preparation/runtime semantic consumer of the boundary.

On pass, the only downstream output is the inherited four-field projection
with the exact sorted 22-path non-boundary allowlist. On failure, the sole
governance-private status is `SOURCE_BOUNDARY_REJECTED`; no projection,
partial pathset, public/preparation-visible error, retry, or reserve
substitution exists.

## 5. Provenance, experiment, resource, and claim preservation

The exact provenance domain remains 23 manifest rows: each of the 22
non-boundary members has exactly the one human-bound successor-candidate
`PCFL_V11_NORMATIVE` source specified by the successor, and the boundary has
exactly the two sorted corpus/projection-repair sources and no third. The
guard nonmember has no provenance row. All false V7 flags, cross-field
anti-laundering, attestation, external placement, embedded-object, finite
exposure, 23-role census, 22-sink, and fail-closed rules remain unchanged.

This closure changes no acceptance-test ID or fixture owner, condition, root,
sentinel, slot, endpoint, read/action opportunity, token allowance, model
call, retry, resource equation, gate, or claim. It preserves exactly 32
active nine-field acceptance records; 18 conditions; 501 registered slots and
148224 generated tokens per ordinary root; 16 DEV, 32 CONFIRMATION, and 16
RESERVE roots; 24 sentinels; active maxima of 24072 slots and 7120896
generated tokens; the exact `ChargedResourceV11` parameterization and
standalone/physical CAS, nonomission, post-origin, and numerical-metering
rules; delayed tests 13/29 and test-28 dependencies; noncompensatory gates;
and the narrow fixed-policy/fixed-topology supplied-memory claim ceiling with
all existing exclusions.

## 6. Stop boundary

This advisory and plan v2 are proposal bytes only. No current directive
ratifies plan v2; only a future workflow may deliberate the supersession after
directly binding the unchanged directive, both plans, this closure, and the
successor candidate. No source grant, review grant, receipt, consensus,
ratification, preparation grant, source, manifest, provenance row, guard,
fixture, state, model call, or scientific artifact is created here.

No source/checker/controller import, compilation, execution, preparation,
implementation, materialization, fixture/root/data generation,
checker/test/model/tokenizer/benchmark/training/GPU work, parenting, resource
acquisition, scientific execution, claim, release, or submission is performed
or authorized.
