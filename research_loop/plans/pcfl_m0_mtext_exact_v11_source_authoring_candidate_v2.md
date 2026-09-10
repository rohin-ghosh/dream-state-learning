# PCFL M0 + M-TEXT-SUPPLIED V11 — integration successor candidate v2

Date: 2026-09-10

Status: **precedence-closed source-only proposal eligible for a future
five-role architecture deliberation; not source-authoring authority**. This
file creates no workflow, state, source plan, source, manifest, provenance
row, grant, review, consensus, ratification, guard result, preparation,
fixture, root, data, model output, or scientific result. It authorizes no
workflow/model call, source import or execution, source or controller
authoring, preparation, implementation, materialization, fixture/root/data
generation, checker/test/model/tokenizer/benchmark/training/GPU work,
parenting, resource acquisition, scientific claim, release, or submission.

## 0. Exact identities and non-self-reference

```text
C11 = "chg_20260910_pcfl_m0_mtext_bound_v11"
CANDIDATE_V2_PATH_C11 =
  "research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate_v2.md"
WORKFLOW_PATH_C11 =
  "research_loop/workflows/pcfl_m0_mtext_bound_v11.deliberation.json"
```

`CANDIDATE_V2_SHA256_C11` means the lowercase SHA-256 independently computed
only after these bytes are sealed. It is not stored in this file. The future
workflow and its zero-attempt initialized state must store and rehash the
actual final value, and every later consensus/state/grant/provenance use must
equal that bound value. A placeholder, guessed value, path-only reference,
workflow-only value absent from state, or author-selected replacement
rejects. This avoids self-reference while leaving exactly one value.

## 1. Exact bound stack and precedence

This candidate binds the following existing bytes directly:

| role | path | SHA-256 |
|---|---|---|
| integration candidate v1 | `research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate.md` | `586500e72c6e03da5f9e4e9800094017888e1e4648bb656a2caad82335a8b5bc` |
| integration preflight repair v1 | `research_loop/advisory/20260910_pcfl_v11_integration_preflight_repair_v1.md` | `a9dc887e8acdf5eacb9a5eca6a2f4586e84269b8d15befd110bcf09a9f669f4e` |
| controllerless guard closure v1 | `research_loop/advisory/20260910_pcfl_v11_controllerless_guard_closure_v1.md` | `37b4098f7cb809a86c3217a4c1267cad62dd799f3403a75c2b871c9f7d2f8f3b` |
| source-authoring plan proposal | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan.json` | `46263de44eefccc9face8b9cf76fd48986a55e7a527cce1bd32b1bc731ae92ce` |
| deliberation scope proposal | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/scope_proposal.json` | `ddc4235cacdd5c2fdd27efe97d9ef76756aa8525baaa32e941afac2ba96f381b` |
| human directive | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/human_directive.txt` | `42a678a04fb6be507f7f2adec781c1d9b72f3e7d205387d3fdc79945751cceff` |
| normative denial corpus | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json` | `4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799` |
| corpus ratification evidence | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_denial_corpus_ratification_evidence.txt` | `3934b01d022ff6b463def3003408d2fb5822c9991764b4bc386aa5bcc2385b58` |
| sole corpus precedence closure | `research_loop/advisory/20260910_pcfl_v11_denial_corpus_ratification_closure_v1.md` | `a540470046064196d04dfa9602ab5aa9f8090706bf3e5e266ee630945ef580c2` |
| controlling corpus/provenance repair | `research_loop/advisory/20260910_pcfl_v11_denial_corpus_provenance_repair_v1.md` | `8d0c28201cec2e695d2a615ca2d8b9230bfee28c032b887096b24332d7431e65` |

The exact C11 precedence is:

1. controllerless guard closure v1 controls guard identity, bundle analyzer
   identity, custody, original 23-role census, pass/failure behavior, and its
   express supersession of integration preflight repair v1 sections 4--5;
2. integration preflight repair v1 sections 1 and 3 control direct workflow
   binding and the complete deterministic inert observation grammar, as
   clarified by the controllerless closure;
3. integration preflight repair v1 section 2 controls the exact 22-path
   provenance-catalog domain and boundary two-source rule, but its one-source
   non-boundary entry is replaced only by section 3 below;
4. integration candidate v1 controls every other integration, experiment,
   resource, registry, authority, visibility, and claim clause, except where
   this v2 candidate expressly replaces it; and
5. the corpus closure and provenance repair retain their own stated
   precedence except for the controllerless bundle-analyzer supersession
   expressly named in controllerless closure v1.

No other advisory, draft guard design, unbound workflow context, V10 candidate
or plan, implementation file, live repository value, or implementer choice
controls C11. Any remaining conflict is `REWORK`.

## 2. Direct workflow, plan, scope, directive, and state binding

Before any deliberation model call, the workflow at `WORKFLOW_PATH_C11` and
its zero-attempt initialized state must each bind these exact eleven distinct
rows:

```text
WorkflowBoundInputV1 := {
  role:WorkflowInputRoleV11,
  path:exact_repo_relative_path,
  sha256:exact_lowercase_hex64,
  access:"DELIBERATION_CONTEXT_ONLY"
}
```

`WorkflowInputRoleV11` is exactly this bytewise-sorted enum:

```text
V11_CONTROLLERLESS_GUARD_CLOSURE_V1
V11_CORPUS_RATIFICATION_EVIDENCE
V11_DENIAL_CORPUS_PRECEDENCE_CLOSURE_V1
V11_DENIAL_CORPUS_PROVENANCE_REPAIR_V1
V11_HUMAN_DIRECTIVE
V11_INTEGRATION_CANDIDATE_V1
V11_INTEGRATION_CANDIDATE_V2
V11_INTEGRATION_PREFLIGHT_REPAIR_V1
V11_NORMATIVE_DENIAL_CORPUS
V11_SCOPE_PROPOSAL
V11_SOURCE_AUTHORING_PLAN
```

The first role maps to the controllerless closure row in section 1; the
candidate-v2 role maps to `CANDIDATE_V2_PATH_C11` and the externally computed
`CANDIDATE_V2_SHA256_C11`; and the other nine roles map one-to-one to the
same-named section-1 rows. Rows are sorted by `(role,path,sha256)`,
duplicate-free, independently rehashed, and closed.

In particular, the plan at SHA-256
`46263de44eefccc9face8b9cf76fd48986a55e7a527cce1bd32b1bc731ae92ce`
and scope at SHA-256
`ddc4235cacdd5c2fdd27efe97d9ef76756aa8525baaa32e941afac2ba96f381b`
must appear as separate direct workflow rows and separate direct initialized-
state rows. Neither may be supplied transitively through this candidate, the
directive, a context manifest, an advisory, or the other object. The directive
and corpus likewise require their own direct rows. A stale current workflow
hash does not validate a revised workflow; the closed revised workflow and
state receive their own future hashes only after all rows are present.

The workflow also directly binds its exact context-manifest digest, exact
five role/model specifications, deliberation-only runner, `attempt_count:0`,
empty output/artifact slots, and terminal `human_required` boundary. No state
currently exists, and this candidate does not create one. Authoring a workflow
or zero-attempt state is not running it. A model call still requires separate
exact human authorization over the final workflow/state bytes.

## 3. Complete exact per-member provenance catalog

### 3.1 Sole non-boundary normative source

For each of the exact 22 non-boundary member paths below, the future external
`SourceProvenanceRowV1[C11].derivation_sources` array has exactly one entry:

```text
{
  kind:"PCFL_V11_NORMATIVE",
  identifier:"PCFL-M0-MTEXT-V11-INTEGRATION-CANDIDATE-V2",
  path:CANDIDATE_V2_PATH_C11,
  sha256:CANDIDATE_V2_SHA256_C11
}
```

The `sha256` is not chosen by the source author. It is the sole exact value
first established by independent rehash after this file is sealed and then
stored identically in the directly bound workflow and zero-attempt state,
fresh five-role consensus, human-required state, and later exact human
`SourceAuthoringGrantV1[C11]`. If any binding is absent or differs, this
candidate is not a human-bound V11 normative source and no source member may
be written.

There is no language-standard, standard-library, v1-candidate, V10,
controllerless-closure, repair, second normative, null, alias, optional,
author-supplied, or third entry. The exact bytewise-sorted catalog domain is:

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

The manifest has exactly one external provenance row for each of the 23
members, in plan-member order. For every path in this domain, the row's
`derivation_sources` is byte-for-byte equal to the one-entry array above.
Every other field, false V7 flag, anti-laundering rule, external placement,
sort, and exact `<G>`-interpolated attestation remains the controlling
`SourceProvenanceRowV1[C11]` rule.

### 3.2 Boundary remains exactly two-source

The boundary path is excluded from the 22-row catalog. Its
`derivation_sources` remains exactly these two sorted entries and no third:

```text
{
  kind:"PCFL_V11_NORMATIVE",
  identifier:"V11-DENIAL-CORPUS-PROJECTION-RULE",
  path:"research_loop/advisory/20260910_pcfl_v11_denial_corpus_provenance_repair_v1.md",
  sha256:"8d0c28201cec2e695d2a615ca2d8b9230bfee28c032b887096b24332d7431e65"
}
{
  kind:"PCFL_V11_NORMATIVE",
  identifier:"V11-NORMATIVE-DENIAL-CORPUS",
  path:"research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/governance/v11_normative_denial_corpus.json",
  sha256:"4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799"
}
```

A missing/extra/duplicate catalog path, boundary insertion, v1-candidate
source, wrong candidate-v2 hash, path/hash mismatch, different identifier,
one-source boundary, candidate-v2 boundary source, optional language source,
or catalog/manifest inequality rejects atomically before any source use.

## 4. Exact controllerless grammar and guard

Integration preflight repair v1 section 3 is incorporated without
abbreviation: its canonical `SourceSpanV1`, observation-ID construction,
lexical no-symlink path normalization, total JSON key/scalar classification,
complete Python syntax/call/JSON-consumer census, Markdown token grammar,
embedded-object inventory, provenance reconstruction, eleven capability
surfaces, graph closure, independent agreement, and fail-closed behavior are
the exact inert grammar. Candidate `source/provenance_contract_v4.json` may
declare classifications but cannot define, select, or amend that grammar.

Controllerless guard closure v1 controls how the grammar is applied:
`V7_BOUNDARY_GUARD` is the inherited governance authority-controller
operation; its normative procedure/source path and bundle analyzer path are
the controllerless Markdown advisory at SHA-256
`37b4098f7cb809a86c3217a4c1267cad62dd799f3403a75c2b871c9f7d2f8f3b`.
It is nonexecutable, outside the plan/manifest/projection, and occupies the
existing `V11_V7_GUARD_SOURCE` census role without adding a role or grant.
The original census remains exactly 23 roles.

The operation may parse only exact reviewed bytes using parser-runtime
executable and grammar-library hashes directly named by a later preparation
grant. It never imports, compiles, invokes, or executes any candidate member
at substage zero. `source/prepare_v4.py` remains an inert
`PREPARATION_ENTRYPOINT` until exact guard pass and may run only in a later
substage separately named by the same grant. Candidate checkers do not
validate the guard before pass. Any missing, dynamic, opaque, ambiguous,
unclassified, mismatched, cyclic, denial-matching, or parser-disagreeing
observation emits only governance-private `SOURCE_BOUNDARY_REJECTED`, no
projection, no retry, and no reserve substitution. Pass emits only the exact
inherited four-field projection and bytewise-sorted 22-path allowlist.

No executable guard file, controller source-authoring grant, controller
review chain, extra census role, or 27-role expansion is part of C11.

## 5. Preserved V11 integration contract

Except for the exact precedence changes in sections 1--4, integration
candidate v1 remains controlling in full. In particular C11 preserves:

- the exact 24-row source plan at the section-1 plan hash, with one nonmember
  manifest output, 23 true members, the exact denial-corpus governance-input
  singleton, one boundary, and exact 22-path pass projection;
- the complete ordered 32-record, closed nine-field acceptance registry,
  exact fixture ownership, terminal receipts, delayed test-13/test-29 split,
  test-28 dependency set, and test-01/test-34 guard ownership;
- the exact two-source boundary projection/provenance, embedded-artifact
  supersession, 47/57 finite sets, original 23-role census, total 22-sink map,
  and direct/encoded/causal nonexposure law;
- `ChargedResourceV11`, `CasObjectChargeV11`, and `ResourceMeterEventV11` as
  the exhaustive C11-only parameterization of the effective V10 field tree,
  including standalone/physical CAS, nonomission, post-origin charging, and
  the metered numerical CPU/latency/wall/GPU/peak-memory exception;
- exactly 18 conditions, 501 registered slots and 148,224 generated-token
  allowance per ordinary root, 16 DEV / 32 CONFIRMATION / 16 RESERVE roots,
  24 sentinels, and active maxima of 24,072 slots and 7,120,896 generated
  tokens; and
- the exact source grant -> inert Authority-S write/hash/manifest -> separate
  human review grant -> independent byte-review receipt -> fresh source
  consensus ending `human_required` -> human exact-byte ratification ->
  separate preparation grant -> controllerless guard substage-zero order.

No source-authoring completion, review, consensus, ratification, or guard pass
implies the next human authority. The scientific claim remains limited to
supplied grounded local atom-plus-connection memory, supplied public
calibration, and the model-independent supplied old-plus-new carrier under one
fixed model, topology, and policy. The exclusions of DREAM authorship, SLEEP,
LoRA/parametric transport, compression, online learning, self-write,
retention, parenting, recurrence, generalization, scale/lifetime improvement,
baseline saturation, text-versus-LoRA efficiency, and whole-organism behavior
remain unconditional.

## 6. Deliberation eligibility and stop boundary

Sections 1--5 close the known design choices without creating an executable
guard or a second source-authoring loop. The exact candidate-v2 bytes are
eligible to be added to the V11 five-role deliberation packet. The packet is
eligible for actual deliberation only after a revised workflow and zero-
attempt state directly bind all eleven section-2 rows, all required context
hashes, the exact five roles/models, deliberation-only runner, and empty prior
attempt/artifact state, and a human separately authorizes those exact workflow
bytes. The deliberation must use fresh interpretations, adversarial
cross-critique, complete concern disposition, and stop at `human_required`.
Its maximum recommendation is that a human consider a later exact C11
source-authoring grant.

This candidate is not such a workflow, state, consensus, ratification, or
grant. It does not authorize a model call or source authoring. It changes no
source, plan, scope, directive, workflow, state, manifest, provenance row,
grant, review, fixture, receipt, controller, parser, preparation, root, data,
resource, model, or scientific artifact, and it performs no import, execution,
materialization, checker/test/model/tokenizer/benchmark/training/GPU work,
parenting, resource acquisition, claim, release, or submission.
