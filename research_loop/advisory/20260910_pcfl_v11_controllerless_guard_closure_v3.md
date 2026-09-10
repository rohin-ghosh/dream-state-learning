# PCFL V11 guard-plan census and review closure v3

Date: 2026-09-10

Status: **proposal-only successor; not ratified and not authority**. This file
authors no source, guard, manifest, provenance row, grant, review, receipt,
workflow, state, preparation, fixture, root, data, model output, or scientific
result. It authorizes no model call, source import/compilation/execution,
preparation, implementation, materialization, checker/test/model/tokenizer/
benchmark/training/GPU work, parenting, resource acquisition, claim, release,
or submission.

## 0. Exact predecessors and narrow precedence

This closure binds:

| role | path | SHA-256 |
|---|---|---|
| integration candidate v3 | `research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate_v3.md` | `76754fbdd3d8bba5f26924e2cc0125f0ae8f803d9559285be84275687652218a` |
| guard/plan closure v2 | `research_loop/advisory/20260910_pcfl_v11_controllerless_guard_closure_v2.md` | `a768682b68e0bbab93dc50e6ea6011894a10b75475f55c18b4df0a187678a5e1` |
| source plan v1, predecessor only | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan.json` | `46263de44eefccc9face8b9cf76fd48986a55e7a527cce1bd32b1bc731ae92ce` |
| controlling source plan v2 proposal | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan_v2.json` | `1b7d618c79379494e98a674e56cae46a8c9346412a4e68d9575b911a9c17076a` |
| effective authority/review head | `research_loop/advisory/20260910_pcfl_v10_authority_delayed_baseline_exact_repair_v2.md` | `27668f5816958342b84a322c317281dc10131732153eeee387a228f67eea86ae` |
| effective guard/custody head | `research_loop/advisory/20260910_pcfl_v10_provenance_resource_guard_exact_repair_v3.md` | `d969fca712d18affed60879be63a96b2aa5d75596d7240c615a5b647dff4337e` |

For C11 only, this v3 supersedes closure v2 only where sections 1--3 below
say so. It closes the two census path mappings and replaces the C11
`GovernanceExactByteReviewGrantV1` operation array and review-input preimage.
All closure-v2 source-authoring, guard execution, no-checker-bootstrap,
provenance, experiment, resource, visibility, authority-order, and claim
clauses remain unchanged. Candidate v3 is predecessor evidence for a future
successor. Any unlisted conflict is `REWORK`.

```text
C11 = "chg_20260910_pcfl_m0_mtext_bound_v11"
PLAN_V1_PATH_C11 =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan.json"
PLAN_V2_PATH_C11 =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan_v2.json"
PLAN_V2_SHA256_C11 =
  "1b7d618c79379494e98a674e56cae46a8c9346412a4e68d9575b911a9c17076a"
GUARD_PATH_C11 =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v7_boundary_guard_controller_v1.py"
```

## 1. Exact two-role path remapping in the original 23-role census

`GovernanceRoleV11` remains exactly the original bytewise-sorted 23-value
enum in V11 denial-corpus ratification closure v1 section 4.2. No role is
added, removed, renamed, duplicated, or reordered. Two, and only two, role
paths are superseded:

```text
V11_SOURCE_AUTHORING_PLAN ->
  research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan_v2.json

V11_V7_GUARD_SOURCE ->
  research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v7_boundary_guard_controller_v1.py
```

Every other role retains its exact effective C11 path. The final
`BoundGovernanceRoleCensusV1[C11]` row for `V11_SOURCE_AUTHORING_PLAN` must
have `present:true`, `path:PLAN_V2_PATH_C11`, and
`sha256:PLAN_V2_SHA256_C11`. A row naming `PLAN_V1_PATH_C11`, its digest,
either plan twice, a null plan, or any other plan rejects the whole census.
Plan v1 may remain a deliberation context/predecessor but is never the final
bound governance plan.

The final `V11_V7_GUARD_SOURCE` row has `present:true`,
`path:GUARD_PATH_C11`, and the exact future guard digest bound by the review/
ratification chain. Candidate `source/prepare_v4.py`, either controllerless
advisory, a temporary copy, alias, symlink, generated path, or missing guard
rejects. The guard role is the existing role, not a new actor or grant.

The existing optional `V11_CORPUS_RATIFICATION_RECORD` remains the only role
permitted absent/null. The final census still has exactly 23 rows. Both
remapped paths/hashes enter the inherited `BOUND_GOVERNANCE_LITERALS_C11` and
22-sink nonexposure rules; plan v1's path/hash may appear as deliberation
history but cannot masquerade as either current census role.

## 2. Exact C11 review-grant operation-array supersession

The same human-issued `GovernanceExactByteReviewGrantV1[C11]`, same actor
`INDEPENDENT_EXACT_BYTE_REVIEWER`, same receipt type, same four-operation
cardinality, same forbidden-operation array, same evidence requirements, and
same five false downstream-authority booleans are retained. No guard-specific
grant, actor, receipt, role, or review loop exists.

For C11 plan v2 only, the exact `authorized_operations` array is:

```text
[
  "READ_EXACTLY_BOUND_SOURCE_REVIEW_INPUTS_AS_INERT_BYTES",
  "COMPUTE_SHA256_AND_BYTE_LENGTH_OF_BOUND_MEMBERS_MANIFEST_AND_SINGLETON_GOVERNANCE_NONMEMBER_GUARD",
  "VALIDATE_CLOSED_DATA_SCHEMAS_WITHOUT_CANDIDATE_IMPORT_OR_EXECUTION",
  "WRITE_ONE_GOVERNANCE_PRIVATE_EXACT_BYTE_REVIEW_RECEIPT"
]
```

This replaces only the inherited second string
`COMPUTE_SHA256_AND_BYTE_LENGTH_OF_BOUND_MEMBERS_AND_MANIFEST`. The other
three strings and their positions are byte-identical. Extra, missing,
duplicated, reordered, old-second-string, umbrella “all inputs,” plural-guard,
guard-execution, source-edit, or unlisted operation rejects before reviewer
access.

The new second operation authorizes the same reviewer to hash and measure
exactly one governance nonmember guard in addition to the inherited 23
members and manifest. It authorizes no parsing, compilation, import,
invocation, execution, preparation, materialization, fixture/test/checker/model
run, or new output. Data-schema validation remains the third operation and
does not represent executable guard validation.

## 3. Complete review-input preimage; inherited values are not dropped

For C11 plan v2, `review_input_binding_sha256` is lowercase SHA-256 of RFC
8785/JCS bytes plus exactly one LF for this recursively closed value:

```text
SourceReviewInputBindingV1[C11] := {
  schema_version:1,
  artifact_type:"pcfl_m0_source_review_input_binding",
  change_id:"chg_20260910_pcfl_m0_mtext_bound_v11",
  source_authoring_plan_sha256:
    "1b7d618c79379494e98a674e56cae46a8c9346412a4e68d9575b911a9c17076a",
  source_authoring_grant_sha256:hex64,
  normative_source_manifest_sha256:hex64,
  normative_denial_corpus:{
    path:"research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json",
    sha256:"4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799"
  },
  member_tuples:[{
    logical_path:repo_relative_path,
    role:SourcePlanRow.role,
    media_type:"application/json"|"text/markdown"|"text/x-python",
    nbytes:u64,
    sha256:hex64
  }, ... exactly 23],
  governance_nonmember_guard:[{
    logical_path:
      "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v7_boundary_guard_controller_v1.py",
    role:"V11_V7_GUARD_SOURCE",
    media_type:"text/x-python",
    nbytes:u64,
    sha256:hex64
  }]
}
```

The preimage preserves all four inherited grant bindings: plan, source grant,
manifest, and the exact corpus path/hash. `member_tuples` equals the manifest's
ordered 23 tuples `(logical_path,role,media_type,nbytes,sha256)` exactly; it is
not merely a digest, count, path set, 22-path projection, or non-boundary
subset. The first tuple is the bytewise-first manifest member
`source/acceptance_tests.json`; the last is boundary member
`source/v7_boundary_v4.json`. Each tuple is byte-for-byte equal to its
manifest entry excluding only the nested provenance value, and the manifest
independently retains that provenance.

`governance_nonmember_guard` is an array of exactly one tuple. Its path/role/
media type equal the plan-v2 guard row, `0 < nbytes <= 262144`, and its digest
rehashes the exact authored guard bytes. It is not inserted into
`member_tuples`, the normative manifest, the 23 provenance rows, or the
22-path projection. No second nonmember, manifest-output tuple, plan-v1 tuple,
null, or optional guard is permitted.

The same review grant directly carries the resulting
`review_input_binding_sha256`. The same independent reviewer recomputes the
complete preimage, rehashes/measures the 23 members, manifest, and singleton
guard, and emits only the existing
`IndependentExactByteReviewReceiptV1`. That receipt binds the review-grant
hash, the exact complete preimage/hash, all 23 member tuples, manifest and
boundary hashes, singleton guard tuple, reviewer identity, and pass/fail. It
adds no output type or role and contains no boundary array, denied detail,
projection, preparation result, or scientific value.

A preimage omitting or replacing the corpus, any member tuple, member order,
manifest hash, source-grant hash, plan-v2 hash, or guard tuple rejects. So do
an extra tuple, guard inside the manifest/member array, old operation array,
hash/length mismatch, or reviewer guard execution.

## 4. Final workflow binding remains external

This closure stores no SHA-256 for the live workflow path. A historical
workflow digest may be used only to verify a mechanical context-list
transformation before final sealing; it is not an input binding, current
workflow identity, governance-census value, authorization, or substitute for
the final digest.

After this closure and its successor candidate are sealed, a future workflow
may replace its predecessor closure/candidate context paths with the v3/v4
paths while retaining exactly 90 context strings. Only then may the runner
compute the final workflow SHA-256. Runner-generated state must store that
value as `workflow_sha256` and independently compute directive-first
two-field `{path,sha256}` `source_bindings`. This closure does not edit,
initialize, hash-bind, authorize, or run the workflow/state.

## 5. Preserved guard, experiment, resource, and claim contract

The plan-v2 guard source remains authored under the same future
`SourceAuthoringGrantV1[C11]`, reviewed under the same review grant/receipt,
included in the same fresh exact-byte consensus/human ratification chain, and
executable only under a later separate `PreparationExecutionGrantV1[C11]`.
The two candidate checkers and `prepare_v4.py` remain inert at guard substage
zero and do not validate the guard. The guard alone applies the exact inert
grammar and fails closed internally without claiming independent checker or
parser execution.

This closure changes no provenance-row count/source rule, acceptance-test ID,
fixture owner, condition, root, sentinel, slot, endpoint, opportunity, token,
model call, retry, resource equation, gate, or claim. It preserves the exact
22 one-source non-boundary rows plus the two-source boundary row; 32 active
nine-field acceptance records; 18 conditions; 501 slots and 148224 generated
tokens per ordinary root; 16 DEV / 32 CONFIRMATION / 16 RESERVE roots; 24
sentinels; active maxima of 24072 slots and 7120896 generated tokens; exact
V11 resource parameterization; delayed-baseline and noncompensatory gate
rules; and the fixed-policy/fixed-topology supplied-memory claim ceiling and
all exclusions.

## 6. Stop boundary

This advisory performs no workflow/state edit, source/guard/checker import,
compilation, execution, review, preparation, implementation, materialization,
fixture/root/data generation, checker/test/model/tokenizer/benchmark/training/
GPU work, parenting, resource acquisition, scientific execution, claim,
release, or submission. It creates no authority. Fresh deliberation and
explicit human decisions remain required.
