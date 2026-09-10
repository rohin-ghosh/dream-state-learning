# FeltCraft symbolic kernel contract v7

## 1. Status, canonical base, and standalone registries

This is a governance proposal only. It is not implementation authority, an
executed test, a receipt, compute/benchmark evidence, or scientific evidence.
The runtime protocol literal is `feltcraft_symbolic_kernel_v7`.

The standalone base is exact canonical compact lexicographically sorted JSON
plus one LF in `base_state.json`, SHA-256
`c5468731c271bf0bd39f97f672a36ad89305304ec3f6b282a31bffa96363d7d8`.
Its protocol is `FELTCRAFT_UNIMPLEMENTED_PROPOSAL_BASE_V1`; `nodes`, `edges`,
`loops`, `claims`, and `implemented_change_ids` are each exactly empty. Before
any release, V7 verifies its bytes, hash, protocol, exact key set, and five
empty registries.

V1--V6 are proposal ancestors only; no runtime identifier or behavior is
inherited. V6 consensus SHA-256 is
`6be5b2c2da9f0f372dea38ab15177f3a357cfdbb08ca682e702bc8ed6c7cc68a`.
Every V7 registry entry is an `add` against the verified empty base. An absent
identifier does not exist.

```text
nodes = [SKN01_AUTHORITY, SKN02_DOMAIN_ENUMERATOR, SKN03_PROJECTIONS,
         SKN04_TWIN_COST_BRIDGE_DELETION_CHECKER,
         SKN06_CONFORMANCE_COMPARATOR, SKN05_GOLDEN_REPORT_VALIDATOR]
edges = [SKE01_authority_to_enumerator,
         SKE02_authority_to_projections,
         SKE03_authority_to_checker,
         SKE04_authority_to_validator,
         SKE05_enumerator_to_projections,
         SKE06_enumerator_to_checker,
         SKE07_comparator_to_enumerator_call,
         SKE08_enumerator_to_comparator_observation,
         SKE09_comparator_to_projections_call,
         SKE10_projections_to_comparator_observation,
         SKE11_comparator_to_checker_call,
         SKE12_checker_to_comparator_observation,
         SKE13_comparator_to_validator]
loops = [SKL01_PREAPPROVAL_GOVERNANCE, SKL02_RATIFIED_CPU_CONFORMANCE]
claims = [C01_symbolic_conformance_only,
          C02_random_motif_information_geometry,
          C03_twin_cost_and_bridge_deletion,
          C04_atoms_or_baseline_claim,
          C05_learned_system_and_paper_claims,
          C06_report_or_audit_as_scientific_evidence]
```

There are exactly six nodes, thirteen directed edges, two loops, and six active
claims. Every endpoint closes over the node registry. No reverse edge,
bidirectionality, callback, or authority forwarding is implicit.

## 2. Preserved exact mathematics and boundaries

The complete normative scientific construction remains V5
`science_repair.md` and `golden_vectors.json`, SHA-256 respectively
`d9599a5c7b501496f56008ab53a850f56f6e9f83bac1f0f141e7f58d77b68338`
and `9db56cbb6df4f4d481269ffc480a81b2634a0996d4d51c3612dcbd9056638dca`.
Values are copied independent governance constants, never recomputed or seen as
expectations by a candidate.

`pi` maps descriptors to roles, is serialized in descriptor order, and has
`index(pi)=4*r+2*i+t`. Render with
`EDGE_pi(d)=(d,sort_D(pi^-1(a_pi(d)),pi^-1(b_pi(d))))` after inverse
rendering. GRAPH is in `(DI0,DI1,DT0,DT1)` order; CAL is its first two triples;
TOP is the pair for the requested top descriptor. Cardinalities are ALIGN 96,
GRAPHSET 48, CALSET 6, LOCAL 12, MOTIF 96, RANDOM 27,648, and ORACLE 192.
LOCAL and RANDOM_SOURCE equal reduced 1/4; MOTIF_SCHEMA and ORACLE equal 1.
LOCAL is target-local, not atoms-only, graph/RAG, or a fair baseline. MOTIF
receives the complete persistent graph and does not learn schema induction.

The sole public projection constructor, immutable tuple/object rules,
structural equality, validation precedence, exact DomainError type/code/args
and timing, support order and tie break, all 72 vectors, and the ordered 25-call
negative registry are exactly V5. `tau=(R0 R2)(R1 R3)`, both fixed twin
relations, 96 involutions, all-four-edge and both-goal changes, exact costs
5/8/16/17, 36,864 namespace-typed bridge cases, 73,728 deletions, exact
inventory/consumption, and the spent-component remaining-budget predicate are
unchanged. This is deletion necessity only; no substitution domain or claim
exists. SK06 and SK07 are unchanged mathematically.

## 3. Independent governance oracle partitions

The immutable governance input bound directly to SKN06 is partitioned into
six typed registries:

```text
oracle.positive_call_stimuli_72
oracle.positive_expected_results_72
oracle.negative_call_stimuli_25
oracle.negative_expected_error_type_code_args_25
oracle.fixed_twin_call_stimuli
oracle.fixed_twin_expected_results
```

For each registry index, a stimulus and its expectation may be paired only
inside SKN06 after candidate return/exception observation. SKN06 constants are
independently bound governance input. They are not released, decoded, copied,
or forwarded by SKN01. SKN01 sees only real repository context path/hash/
purpose, canonical base and final registries, exact requested/forbidden scopes,
and actual ratification-chain metadata. A path/hash binding is not oracle-byte
visibility.

SKN02, each of the four SKN03 principals, and SKN04 are candidates. During one
invocation, SKN06 sends exactly one immutable addressed stimulus on exactly one
of SKE07, SKE09, or SKE11 to its named candidate surface. The candidate cannot
receive a batch, another candidate's stimulus, an expectation, expected error
type/code/args, golden receipt/value, comparator state, prior observation, or
mismatch. Candidate surfaces cannot read files, environment, configuration,
cache, RNG, dynamic imports, globals, audit inputs, or each other.

SKE08, SKE10, and SKE12 are distinct reverse observation-only edges. They carry
only the immutable return or exact raised exception for the single outstanding
addressed invocation. They carry no control, subsequent stimulus, expectation,
mismatch, receipt, authority, or capability. The directed call and observation
edges are never inferred from one another.

SKN06 alone compares each observation against its matching comparator-local
expected result or exact expected error type/code/args. Per-case expectations,
observations, and mismatch details remain SKN06-local and may be exposed only
to human governance outside runtime. The sole SKN06 successor edge is SKE13,
carrying only fixed aggregate counts and eight ordered SK01--SK08 receipts to
SKN05. It carries no stimulus, return/exception, expectation, histogram source
rows, mismatch detail, oracle byte, golden byte, or SK09 result.

SKN05 consumes only those aggregates/receipts plus its independently bound
preimplementation golden bytes. It creates SK09 solely from its exact-byte and
six-mutation checks, emits success only if all upstream aggregates and receipts
pass, otherwise exits nonzero with no successful report, and has no successor.

## 4. Exact report and ten tests

The sole all-pass byte oracle is canonical `golden_report.json`: compact
lexicographically sorted JSON plus exactly one LF. Its SHA-256 and byte length
are bound by `change.json`. Its protocol is `feltcraft_symbolic_kernel_v7`.
All scientific numeric fields, 72-vector and 25-negative totals/histogram, and
nine receipts equal V5/V6; only version-bearing identifiers advance to V7:

```text
SK01_DOMAIN_INVERSE_V7                 [96,48,4,10,10,0]
SK02_CALIBRATION_VECTORS_V7            [6,16,6,0]
SK03_RANDOM_WITNESSES_V7               [12,4,4,1,4,12,12,0]
SK04_MOTIF_WITNESSES_V7                [96,1,1,20,0]
SK05_TWIN_WITNESSES_V7                 [96,2,0,0,0]
SK06_COSTS                              [192,5,192,8,16,17,0]
SK07_BRIDGE_DELETION                    [36864,73728,0]
SK08_PROJECTIONS_CLOSED_BOUNDARY_V7     [12,96,27648,192,72,25,25,0]
SK09_REPORT                             [1,6,0]
```

SK01--SK08 additionally require a trace for every call proving exactly one
addressed stimulus traversed the appropriate call edge, exactly one return or
exception traversed only the matching observation edge, and no expectation or
mismatch entered a candidate. SK09 additionally requires all eight aggregate
receipts to have this provenance. It rejects exactly six mutations: missing
protocol, extra top-level debug, wrong protocol, unreduced 2/8, swapped first
receipts, and one extra LF. The golden is an expected oracle, not a result.

SK10 is defined only by `audit_contract.md`,
`scope_audit_request.schema.json`, and `scope_audit.schema.json`. Its
deterministic tier claims only fixed binding equality, recursive path/manifest/
byte/hash/root digest, diff path equality, request JCS/schema validation,
timestamp ordering, `ast.parse` success, and literal `Import`/`ImportFrom`
inventory and exact allowlist/local-path resolution. All forbidden AST,
CLI/options/stdin/environment/configuration, write-equivalence, dynamic/
capability/reachability, and semantic Python judgments require fresh
independent human source review and explicit human governance adjudication.
They are not deterministic and no complete proof is claimed. `passed` requires
both tiers and explicit attestations and is governance evidence only.

## 5. Ratification chain and firewall

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
authorization_evidence SHA-256/excerpt == exact separately supplied evidence
```

Before exact human approval, implementation, tests, execution, audit, review,
receipts, evidence generation, compute, promotion, and claims are forbidden.
After approval, only the exact three requested atoms may be released and all
eight forbidden atoms remain forbidden. The comparator, oracle partitions,
reports, audit inputs/outputs, reviews, and governance artifacts never become
inputs to renderer, life, agent, model/provider/tokenizer, DREAM/SLEEP/memory,
LoRA/weights, GPU/remote, benchmark, promotion, paper, or scientific-claim
stages. V7 grants no science, model, GPU, benchmark, or successor authority.
