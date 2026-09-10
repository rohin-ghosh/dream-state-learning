# PCFL v4 governance packet and two-freeze audit — v1

Date: 2026-09-10

Status: **source-only governance advisory**. This file does not authorize a
new deliberation run, implementation or preparation-source creation,
materialization, CPU fixture/benchmark execution, model/tokenizer use,
training, GPU use, scientific execution, claim, release, or submission.

## Verdict

The existing `chg_20260910_pcfl_m0_mtext_bound_v2` chain is valid as a
completed five-role **rework** chain, not as implementation authority. Its
consensus has `recommendation="rework"`; `architecture_intake.py` therefore
must and will reject any attempt to ratify it. Preserve those bytes and create
a new change ID for the integrated repaired proposal.

Use `chg_20260910_pcfl_m0_mtext_bound_v4` as the successor identifier. The v4
chain should first be a source-only five-role deliberation. A first human
freeze may later authorize only the exact deterministic preparation source
and one exact CPU preparation input. A second human freeze may later admit
the resulting candidate manifest as a nonclaim fixture. Neither freeze may
authorize M0 runtime implementation, M-TEXT, a model/tokenizer, GPU work, or a
scientific claim.

## 1. Controlling predecessor bytes

These were rechecked from the current repository:

| Role | Path | SHA-256 |
|---|---|---|
| v2 workflow | `research_loop/workflows/pcfl_m0_mtext_bound_v2.deliberation.json` | `dfea472726cf2b63b7d5eb66e78dae1cbdc9f3e5172fd63ed84374ae419b2c06` |
| v2 scope | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v2/scope_proposal.json` | `2492802c8a96b0445e97b1b3831c25fcd8b4c15d2bffaeb5978a1653e412933b` |
| v2 change | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v2/change.json` | `45647223d6a3763f0dcde90b68ad3c953460cb0175960ba92e6a21a615fc9321` |
| systems interpretation | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v2/interpretation_systems.json` | `eaff44379eb6398f4dc879c606d512d7814472759c0370ea459a470cc1f7fcff` |
| benchmark interpretation | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v2/interpretation_benchmark.json` | `c87b1c94335f03a91bc2a3dcefc791e1aac9a2eef6bca227d4fa31518eed0ad2` |
| critique | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v2/critique.json` | `02528c271e174cdcec27c1f255b4fb327d89530f90143fa54a2202bc4ff5e1ba` |
| consensus | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v2/consensus.json` | `d1eabe9da3bc4250e4ba08c458086f8e3f4f5f1e7808e4b3c6a0785243c96aa2` |
| intake state | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v2/intake.state.json` | `d458b6add402412b41dfb5533189a07133c0753721faf7d0c721a01e85d0116d` |
| runner state | `.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v2.deliberation.state.json` | `c2d66fddea6d31ccc7ce926c92cf991f8bf44d239d458ca325d97f0e5efb1d75` |

The v2 intake is `phase="human_required"`, `human_required=true`, and
`implementation_authorized=false`. The consensus explicitly requires a
successor for all eighteen accepted concerns. Do not edit, append to, or
ratify this chain.

## 2. Exact v4 deliberation packet

Reserve these governance paths:

```text
research_loop/workflows/pcfl_m0_mtext_bound_v4.deliberation.json
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v4/
  human_directive.txt
  scope_proposal.json
  integrated_contract.md
  normative_source_manifest.json
  change.json
  interpretation_systems.json
  interpretation_benchmark.json
  critique.json
  consensus.json
  intake.state.json
```

The runner owns the last six artifact/state files after initialization. Before
initialization, the exact integrated contract and every declarative schema,
table, registry, golden/preparation rule, and eventual inert source-bundle
byte needed by the proposal must already be listed in
`normative_source_manifest.json` and in the workflow context. A placeholder,
glob, directory digest, future materializer promise, or path without actual
bytes is not an exact source freeze.

The workflow must contain exactly the fields enforced by
`architecture_deliberation.py`:

```text
schema_version, workflow_kind, name, workspace, change_id,
directive_file, context_files, output_dir, state_path,
intake_state_path, run_dir, roles
```

`roles` must contain exactly `advocate`, `systems`, `benchmark`, `critique`,
and `consensus`; each contains only a nonempty `executors` array. Systems and
benchmark are the two independently fresh interpretations and must have
different perspectives and canonical IDs
`<change_id>.systems`/`<change_id>.benchmark`.

For provenance, list the v4 workflow itself as one of its own context paths.
This does not create a hash cycle: the workflow contains only that path, not
its own digest. It makes the exact executor configuration transitively visible
to `change.json`, consensus, and later ratification. Also list the v4
`scope_proposal.json`, integrated contract, normative manifest and every
manifested source file directly. Do **not** list the v4 mutable intake state or
runner state as context.

Bind at least this predecessor/rework closure in `context_files`:

- `AGENTS.md` and `research_notes/64_iclr_paper_core_and_benchmark_v2.md`;
- the exact v2 workflow, scope proposal, change, both interpretations,
  critique, consensus, intake state, and runner state named in section 1;
- `20260910_pcfl_m0_exact_contract_repair_fresh_v1.md`;
- `20260910_pcfl_mtext_supplied_exact_contract_repair_fresh_v1.md`;
- `20260910_pcfl_authority_durability_exact_repair_fresh_v1.md`;
- `20260910_pcfl_m0_semantic_consistency_fresh_audit_v1.md`;
- `20260910_pcfl_mtext_arithmetic_and_consistency_fresh_audit_v1.md`; and
- `20260910_pcfl_v3_repairs_adversarial_cross_critique_v1.md`.

Freeze that list before `architecture_deliberation ... init`; initialization
records its exact path/hash pairs. Any later source or workflow change must
fork a new chain rather than refresh hashes in place.

### Required artifact fields and bindings

`scope_proposal.json` must have exactly:

```text
schema_version=1, change_id, state="proposal_only",
human_ratification_required=true, requested_scope (sorted, unique, nonempty),
forbidden_scope (sorted, unique, disjoint), authorization_effect
```

Include `scope_proposal.json` directly in the workflow context because the
intake state does not otherwise record its hash. Its requested scope must be
the eventual first-freeze scope, not a vague implementation grant: exact
preparation-source realization, one deterministic CPU materialization input,
its two checkers/receipts, and fresh read-only review only. Explicitly forbid
M0 runtime, M-TEXT, model/tokenizer calls, data/root selection, retry or
replacement, training, LoRA, GPU, science, claim, publication, and successor
autopromotion.

`change.json` must satisfy all required schema fields:

```text
schema_version, artifact_type, change_id, title, summary, system_thesis,
state="proposed", context_files, graph_delta, loop_delta, claim_delta,
visibility_matrix, acceptance_tests, human_boundary
```

Its `context_files` must equal every and only the workflow's directive plus
context paths, with exact SHA-256. The visibility cells must be the complete
information-item x stage Cartesian product. Test IDs must be unique, and the
integrated v4 must register every corrected or newly required test rather than
asking consensus to invent tests.

Each interpretation must bind `architecture_change_sha256`, the same exact
context closure, every and only acceptance-test ID, a unique perspective and
ID, ambiguities/disagreements, and the human boundary. Neither interpretation
may see the other.

`critique.json` must bind the change and both exact interpretation hashes,
review every and only registered test, assign unique concern IDs, and name all
missing tests/visibility failures. `consensus.json` must bind the exact change,
both interpretations, and critique; disposition every and only critique
concern, upstream disagreement, and acceptance test; and resolve each required
concern through a real top-level disagreement ID.

The consensus is first-freeze releasable only when:

```text
recommendation == "proceed_to_implementation"
every disagreement resolution.status == "resolved"
no concern/upstream disposition.status == "unresolved"
no test is removed
every modified test has a nonempty replacement_test_id
state == "human_required"
human_decision.implementation_forbidden == true
```

Even then, it authorizes nothing until exact human ratification.

## 3. Cycle-free first freeze: exact preparation source

The current advisory formula must be repaired so no object names its own hash.
After a releasable v4 consensus and before human ratification, create one
canonical `pre_authority_binding.json` payload containing:

```text
schema_version, artifact_type, change_id,
workflow_sha256, scope_proposal_sha256, architecture_change_sha256,
interpretation_hashes, critique_sha256, consensus_sha256,
human_required_intake_state_sha256,
normative_source_manifest_sha256,
semantic_spec_root, transition_table_sha256,
failure_precedence_sha256, object_schema_manifest_root,
materializer_source_root, constructive_checker_source_root,
axiomatic_checker_source_root, runtime_manifest_root,
requested_scope, forbidden_scope
```

The payload has **no** `pre_authority_binding_sha256`, ratification hash,
approved-state hash, preparation-input root, run ID, output hash, or future
field. Its raw canonical bytes are hashed externally as
`pre_authority_binding_sha256`. Rohin's authorization evidence must quote that
exact digest and the exact requested/forbidden scope.

Then create `human_preparation_ratification.json` using the existing strict
architecture-ratification schema:

```text
schema_version=1,
artifact_type="architecture_human_ratification",
ratification_id, change_id, state="human_approved",
consensus_sha256, human_required_state_sha256,
ratifier, authority_statement, decision_statement, decided_at,
authorized_scope, forbidden_scope,
authorization_evidence={path,sha256,excerpt},
implementation_authorized=true
```

The authorized and forbidden arrays must exactly equal the canonical v4 scope
proposal. The evidence bytes and excerpt must contain the exact human decision;
model agreement or a general instruction to continue is not ratification.
Run `architecture_intake ratify` only after the artifact exists. The command
binds the ratification to the pre-transition `human_required` state, then
records the ratification hash in the transitioned `human_approved` state.

After that transition, mechanically create `preparation_input_binding.json`
with:

```text
schema_version, artifact_type, change_id,
pre_authority_binding_sha256,
human_preparation_ratification_sha256,
human_approved_intake_state_sha256
```

It contains no digest of itself. Define:

```text
preparation_input_root =
  SHA256("PCFL-M0-PREPARATION-INPUT-v1\0" ||
         canonical_preparation_input_binding_bytes)

run_id =
  SHA256("PCFL-M0-RUN-v1\0" || preparation_input_root_raw32)
```

This is acyclic:

```text
exact sources -> change -> interpretations -> critique -> consensus
  -> paused intake state -> pre-authority binding -> human ratification
  -> approved intake state -> preparation-input binding -> run ID
```

The human ratification does not hash itself, and the pre-authority binding
does not anticipate the human ratification.

## 4. Cycle-free second freeze: actual candidate fixture

The authorized deterministic preparation may produce candidate CAS objects,
one manifest, one terminal candidate receipt, constructive/axiomatic checker
receipts, and a fresh independent review. None is consumable yet.

Create `fixture_freeze_preimage.json` containing exact hashes/roots for:

```text
preparation_input_binding and preparation_input_root,
human preparation ratification and approved intake state,
candidate output manifest and semantic manifest root,
terminal candidate receipt,
constructive checker source and receipt,
axiomatic checker source and receipt,
fresh independent review,
fixture frozen scope and forbidden scope
```

It contains no human-fixture-freeze hash and no freeze ID. Hash its raw
canonical bytes externally as `fixture_freeze_preimage_sha256`. Human evidence
must explicitly approve that exact digest.

`human_fixture_freeze.json` needs its own strict schema, fixed in the v4 source
packet, with at least:

```text
schema_version, artifact_type="pcfl_m0_human_fixture_freeze",
freeze_decision_id, change_id, state="fixture_frozen_nonclaim",
fixture_freeze_preimage_sha256,
preparation_ratification_sha256, human_approved_intake_state_sha256,
output_manifest_sha256, output_manifest_root,
candidate_receipt_sha256,
constructive_checker_receipt_sha256,
axiomatic_checker_receipt_sha256,
independent_review_sha256,
ratifier, authority_statement, decision_statement, decided_at,
frozen_scope, forbidden_scope,
authorization_evidence={path,sha256,excerpt},
implementation_authorized=false,
model_execution_authorized=false,
scientific_claim_authorized=false
```

Do not force this through `architecture_intake ratify`: that state machine has
one approval transition and its schema requires
`implementation_authorized=true`. The fixture freeze is a nonclaim evidence
admission, not implementation permission. Its strict schema and validator must
be part of the first source freeze.

After the human fixture-freeze bytes exist, compute:

```text
freeze_id =
  SHA256("PCFL-M0-FREEZE-v1\0" ||
         fixture_freeze_preimage_sha256_raw32 ||
         human_fixture_freeze_sha256_raw32)
```

Then install the deterministic immutable reference `frozen/<freeze_id>.json`.
That reference may contain `freeze_id`, the preimage hash, the human-freeze
hash, and the upstream manifest/receipt roots because `freeze_id` is not
defined as the reference file's own hash. No circular field exists.

A later, separate architecture change must explicitly request M0 runtime
implementation and bind this one `freeze_id`. The fixture freeze itself grants
no source, execution, model, GPU, or claim authority.

## 5. Work boundary now

Permitted under the present source-only continuation:

- preserve and cite the v2 chain as negative evidence;
- author source-only governance advisories, an integrated contract, closed
  declarative schemas/tables/registries, test IDs, a v4 directive, workflow,
  context manifest, and proposed exact scopes;
- compute hashes of already-authored source-only files; and
- prepare an approval packet for a new five-role deliberation.

Not currently authorized:

- run the new five-role workflow or any unlisted model role;
- write materializer, checker, runtime, M0, M-TEXT, renderer, reader, reducer,
  fixture, root, or data source under the current v2 scope;
- materialize or check candidate bytes;
- create either human-ratification artifact by inference;
- load a tokenizer/model, execute a benchmark, train, use GPUs, or release a
  claim.

Before exact preparation source exists, Rohin must explicitly resolve whether
an inert exact patch bundle may be authored as source-only proposal content.
The current v2 scope forbids materializer/checker source creation, while the
two-freeze design requires their exact bytes before first-freeze ratification.
A general “continue” instruction is sufficient to continue analysis, but is
not an exact selection of the two-freeze exception, zero V7 runtime reuse,
source paths, source bytes, or execution scope.

## 6. Minimal stop/go checklist

1. Preserve v2; do not ratify it.
2. Obtain exact human authority for the named v4 deliberation workflow and,
   if needed, inert preparation-source authoring only.
3. Complete one integrated v4 contract; eliminate amendment precedence.
4. Add exact source bytes/manifests and all v3 cross-critique tests before
   initializing deliberation.
5. Run the five roles to a new `human_required` consensus.
6. If consensus is not technically releasable, rework under another change ID.
7. If releasable, build the acyclic pre-authority binding and ask Rohin to
   ratify its exact bytes/scope.
8. Only then realize/run one deterministic CPU preparation input.
9. Bind candidate, two checker receipts, and fresh review in the fixture-freeze
   preimage; ask Rohin for the second exact nonclaim freeze.
10. Only a later separate approved change may implement M0 against that
    immutable `freeze_id`.
