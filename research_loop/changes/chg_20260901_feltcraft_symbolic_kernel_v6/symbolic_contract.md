# FeltCraft symbolic kernel contract v6

## 1. Status, canonical base, and exact replacement registries

This is a governance proposal only. It is not implementation authority, an
executed test, a receipt, compute evidence, benchmark evidence, or scientific
evidence. The runtime protocol literal is `feltcraft_symbolic_kernel_v6`.

The standalone implementation base is the exact 132-byte canonical compact
sorted JSON plus one-LF artifact `base_state.json`, SHA-256 `c5468731c271bf0bd39f97f672a36ad89305304ec3f6b282a31bffa96363d7d8`. Its
protocol is `FELTCRAFT_UNIMPLEMENTED_PROPOSAL_BASE_V1` and its `nodes`, `edges`, `loops`, `claims`, and
`implemented_change_ids` arrays are each exactly empty. V6 first verifies the
artifact bytes, hash, protocol, exact key set, and five empty registries.

V1--V5 are proposal ancestors only and no identifier or operation is inherited.
V5 consensus SHA-256 is
`44bbfd1075892bbc0b9cbeb460e81fc4bc57c0b63ce8ec2d4398775063b8fb71`.
V6 has standalone replacement semantics: every listed entry is an `add`
against the verified empty base; an absent identifier does not exist.

```text
nodes = [SKN01_AUTHORITY, SKN02_DOMAIN_ENUMERATOR, SKN03_PROJECTIONS,
         SKN04_TWIN_COST_BRIDGE_DELETION_CHECKER,
         SKN06_CONFORMANCE_COMPARATOR, SKN05_GOLDEN_REPORT_VALIDATOR]
edges = [SKE01_authority_to_enumerator, SKE02_authority_to_projections,
         SKE03_authority_to_checker, SKE04_authority_to_comparator,
         SKE05_authority_to_validator, SKE06_enumerator_to_projections,
         SKE07_enumerator_surface_to_comparator,
         SKE08_enumerator_to_checker,
         SKE09_projection_surfaces_to_comparator,
         SKE10_checker_surface_to_comparator,
         SKE11_comparator_to_validator]
loops = [SKL01_PREAPPROVAL_GOVERNANCE, SKL02_RATIFIED_CPU_CONFORMANCE]
claims = [C01_symbolic_conformance_only,
          C02_random_motif_information_geometry,
          C03_twin_cost_and_bridge_deletion,
          C04_atoms_or_baseline_claim,
          C05_learned_system_and_paper_claims,
          C06_report_or_audit_as_scientific_evidence]
```

There are exactly six nodes, eleven edges, two loops, and six active claims.
Edge endpoints close over the node registry. There is no stale V1--V5 runtime
entry, alias, implicit carry-forward, removal, or modification.

## 2. Preserved exact symbolic mathematics

The complete normative scientific construction remains the V5
`science_repair.md` and `golden_vectors.json`, SHA-256 respectively
`d9599a5c7b501496f56008ab53a850f56f6e9f83bac1f0f141e7f58d77b68338`
and `9db56cbb6df4f4d481269ffc480a81b2634a0996d4d51c3612dcbd9056638dca`.
Their values are copied, not recomputed by a candidate surface.

`pi` maps descriptors to roles, is serialized in descriptor order, and has
`index(pi)=4*r+2*i+t`. Render with
`EDGE_pi(d)=(d,sort_D(pi^-1(a_pi(d)),pi^-1(b_pi(d))))`, after inverse
rendering, then define GRAPH in `(DI0,DI1,DT0,DT1)` order, CAL as its first two
triples, and TOP as the pair for the requested top descriptor. Cardinalities
remain ALIGN 96, GRAPHSET 48, CALSET 6, LOCAL 12, MOTIF 96, RANDOM 27,648,
and ORACLE 192. LOCAL and RANDOM_SOURCE are 1/4; MOTIF_SCHEMA and ORACLE are 1.
LOCAL is target-local, not atoms or a fair baseline. MOTIF receives the full
persistent graph and does not learn schema induction.

The sole public projection constructor, immutable tuple/object rules,
structural equality, validation precedence, exact DomainError type/code/args,
support ordering/tie break, 72 copied vectors, and ordered 25-call negative
registry remain exactly V5. `tau=(R0 R2)(R1 R3)`, both fixed twin relations,
96 involutions, all-four-edge and both-goal changes, costs 5/8/16/17, 36,864
typed bridge cases, 73,728 deletions, exact inventory/consumption, and the
remaining-budget predicate also remain exact. This is deletion necessity only;
there is no substitution domain or claim.

## 3. Oracle-blind candidates and isolated comparator

SKN02, each of the four SKN03 principals, and SKN04 are candidates under test.
They never read or receive copied expected ALIGN/GRAPH/CAL/TOP/support/chosen/
twin values, negative expected codes, golden receipt values, mismatch details,
or comparator state. Their authority edges contain only definitions, legal
domain constants, signatures, validation rules, tau/cost/bridge rules, and
opaque artifact path/hash bindings. Candidate surfaces cannot read files,
environment, cache, RNG, dynamic imports, globals, audit inputs, or each other.

SKN06 is a distinct pure-CPU comparator. It alone among executable stages sees
the copied independent 72-vector registry, ordered 25 negative calls and
expected exceptions, and the two fixed twin expectations. It invokes only the
public enumerator, projection-constructor, and checker surfaces, passing call
inputs but never expected outputs, expected exception codes, receipts, or
mismatch state into a candidate. It observes immutable candidate returns or
exact exceptions, compares outside the candidates, and retains per-case
mismatch details only for human governance. Its only runtime output is fixed
aggregate counts and eight SK01--SK08 receipts to SKN05. It has no edge to a
candidate, no file/report/audit/science write, and no successor endpoint.

SKN05 consumes only comparator aggregates/SK01--SK08 receipts plus the prebound
golden bytes. It cannot see per-case candidate results, oracle values, negative
calls, or mismatch details. It creates SK09 only from its own exact-byte and
mutation checks and emits the successful report only if every comparison and
invariant passes; otherwise it exits nonzero without a successful report. This
realizes SK01--SK05 and SK08/SK09 without oracle leakage.

## 4. Exact report and tests

The sole all-pass byte oracle is the 2102-byte canonical
`golden_report.json`, SHA-256 `c83c779698abb3873c563c6547e0d56b1bbe7fa2289c0d122188c0f0f9d4cc97`: compact lexicographically sorted
JSON and exactly one LF. It has protocol `feltcraft_symbolic_kernel_v6`, the
same exact scientific fields, 72-vector totals, 25-negative totals/histogram,
and nine receipts as V5, with only the version-bearing receipt identifiers
advanced to V6. The immutable receipt vectors are:

```text
SK01_DOMAIN_INVERSE_V6                 [96,48,4,10,10,0]
SK02_CALIBRATION_VECTORS_V6            [6,16,6,0]
SK03_RANDOM_WITNESSES_V6               [12,4,4,1,4,12,12,0]
SK04_MOTIF_WITNESSES_V6                [96,1,1,20,0]
SK05_TWIN_WITNESSES_V6                 [96,2,0,0,0]
SK06_COSTS                              [192,5,192,8,16,17,0]
SK07_BRIDGE_DELETION                    [36864,73728,0]
SK08_PROJECTIONS_CLOSED_BOUNDARY_V6     [12,96,27648,192,72,25,25,0]
SK09_REPORT                             [1,6,0]
```

SK09 rejects exactly six mutations: missing protocol, extra top-level debug,
wrong protocol, unreduced 2/8, swapped first receipts, and one extra LF. These
bytes are a preimplementation expected oracle, not an executed result.

SK10 is the exact five-file post-freeze external audit defined by
`audit_contract.md` and `scope_audit.schema.json`. It deterministically checks
paths/bytes/hashes/manifest/diff, parsing/imports/direct forbidden AST, static
CLI, bindings, and time order, then requires a fresh independent review of the
same five files against all eight forbidden atoms and explicit human
adjudication. It does not claim a complete Python call graph or capability
proof. `passed` requires every deterministic check and human attestation and is
governance evidence only.

## 5. Actual ratification chain and firewall

There is no `ratification.change_sha256`. Authority validates exactly:

```text
ratification.change_id == intake.change_id == consensus.change_id == change.change_id
ratification.consensus_sha256 == SHA256(consensus bytes)
consensus.architecture_change_sha256 == SHA256(change bytes)
ratification.human_required_state_sha256 == SHA256(paused-state bytes)
paused_state.artifacts.architecture_change.sha256 == SHA256(change bytes)
paused_state.artifacts.architecture_consensus.sha256 == SHA256(consensus bytes)
approval_transition.source_state_sha256 == ratification.human_required_state_sha256
approval_transition.artifact_sha256 == SHA256(ratification bytes)
ratification scopes == exact sorted scope_proposal scopes
authorization_evidence SHA-256/excerpt == the exact separately supplied evidence
```

Before exact human approval, implementation, tests, execution, audit, receipts,
evidence generation, compute, promotion, and claims are forbidden. After it,
only the exact three requested atoms are released and all eight forbidden atoms
remain forbidden. The comparator, report, audit inputs/outputs, governance
artifacts, and reviewer evidence never become inputs to renderer, life, agent,
model, tokenizer, DREAM/SLEEP/memory, LoRA, GPU/remote, benchmark, promotion,
or scientific-claim stages. No approval or scientific authority is inferred.
