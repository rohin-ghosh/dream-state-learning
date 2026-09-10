# FeltCraft symbolic kernel contract v5

## 1. Status, lineage, and complete registries

This is a governance proposal, not implementation authority, an executed test,
a runtime receipt, an audit receipt, compute evidence, or scientific evidence.
The protocol literal is `feltcraft_symbolic_kernel_v5`.

The standalone implementation-state base is exactly
`FELTCRAFT_UNIMPLEMENTED_PROPOSAL_BASE_V1`:

```text
nodes = []
edges = []
loops = []
claims = []
implemented_change_ids = []
```

This empty base says nothing about unrelated repository architecture. The
FeltCraft V1 change
`3f349860ec02a906caff8c735f3c8068e525dfa2bb9a3fd32aa81bef707489dd`
was proposed without consensus or ratification. V2
`cdb10a61638454ce86e54de359d09c1cdd082029b2a433209b9553d917324361`,
V3 `53fd4e0bce3360bfb649e06c3dccf85356eea45188bb1c9cea5e8afffc2b7db3`,
and V4 `fa5ef77c127b7fe614ef33875d55a4099a023bec8fc6a8a1dd98db5f0fbf2a8e`
were rework proposals whose implementation was forbidden. The V4 consensus
bytes are
`682a6b53dce625283df32b82bad559ca03e5ec77e64f36279b1da8fd119ab12e`.
All are proposal ancestors only.

V5 has standalone replacement semantics. Every following entry is an `add`
against the empty base. An absent identifier does not exist. No removal,
modification, alias, inherited operation, implicit carry-forward, V1/V2 `N*`,
`E*`, or `L*` entry, V3 renamed `SKN*` entry or
`SKL01_EXACT_SYMBOLIC_KERNEL`, or V4 operation record is active.

```text
nodes = [
  SKN01_AUTHORITY,
  SKN02_DOMAIN_ENUMERATOR,
  SKN03_PROJECTIONS,
  SKN04_TWIN_COST_BRIDGE_DELETION_CHECKER,
  SKN05_GOLDEN_REPORT_VALIDATOR
]
edges = [
  SKE01_authority_to_enumerator,
  SKE02_authority_to_projections,
  SKE03_authority_to_checker,
  SKE04_authority_to_validator,
  SKE05_enumerator_to_projections,
  SKE06_enumerator_to_checker,
  SKE07_enumerator_to_validator,
  SKE08_projections_to_validator,
  SKE09_checker_to_validator
]
loops = [SKL01_PREAPPROVAL_GOVERNANCE, SKL02_RATIFIED_CPU_CONFORMANCE]
claims = [
  C01_symbolic_conformance_only,
  C02_random_motif_information_geometry,
  C03_twin_cost_and_bridge_deletion,
  C04_atoms_or_baseline_claim,
  C05_learned_system_and_paper_claims,
  C06_report_or_audit_as_scientific_evidence
]
```

Registry equality and ID uniqueness are exact. The nine edge endpoints belong
to the five-node registry. C01 permits only symbolic implementation-conformance
wording. C02 is limited to the finite 1/4-versus-1 information geometry. C03 is
limited to the declared twin, cost algebra, and typed deletion necessity. C04,
C05, and C06 are active negative boundaries: `LOCAL` is not an atoms or fair
baseline; the kernel is not a learned system or paper result; and neither a
report nor an audit is scientific evidence.

SKL01 permits only the fresh interpretations, cross-critique, adjudicated
consensus, and separate human-authored ratification required for governance.
SKL02 does not exist as executable authority until a releasable consensus and
exact ratification validate. It then contains only the three requested scope
atoms and terminates after CPU conformance plus external human review.

## 2. Alignment algebra and inverse rendering

The literal orders and role-space recipes are:

```text
D_R = (DR0,DR1,DR2,DR3)     R = (R0,R1,R2,R3)
D_I = (DI0,DI1)             I = (I0,I1)
D_T = (DT0,DT1)             T = (T0,T1)
D = D_R || D_I || D_T
D_out = (DI0,DI1,DT0,DT1)

I0 <- R0+R1
I1 <- R2+R3
T0 <- I0+R2
T1 <- I1+R0
```

An alignment is exactly `pi : descriptors -> roles`, serialized as the
immutable eight-tuple `(pi(DR0),...,pi(DT1))` in `D` order. It is never a
role-to-descriptor tuple. Enumerate raw, then intermediate, then top
permutations in nested lexicographic order over the literal lists. If their
zero-based ranks are `r,i,t`, then `index(pi)=4*r+2*i+t`.

For role output `o`, let `ingredients(o)=(a_o,b_o)`. The normative edge is

```text
EDGE_pi(d) =
  (d, sort_D(pi^-1(a_pi(d)), pi^-1(b_pi(d))))

GRAPH(pi) = (EDGE_pi(DI0), EDGE_pi(DI1),
             EDGE_pi(DT0), EDGE_pi(DT1))
CAL(pi)   = (EDGE_pi(DI0), EDGE_pi(DI1))
TOP(pi,g) = the final two fields of EDGE_pi(g), g in (DT0,DT1)
```

Ingredients are sorted only after inverse rendering. Sorting role names first,
using `pi` instead of `pi^-1`, or reversing the stored tuple direction is
wrong. `ALIGN`, `GRAPHSET`, and `CALSET` are ordered by first occurrence and
have cardinalities 96, 48, and 6.

The independently derived governance oracle is exactly
`golden_vectors.json`, SHA-256
`9db56cbb6df4f4d481269ffc480a81b2634a0996d4d51c3612dcbd9056638dca`.
Its JSON arrays mean immutable tuples. It binds ALIGN and GRAPH at indices
`0,1,2,3,8,10,12,14,16,48`; all six first-occurrence CAL vectors at indices
`0,2,8,10,12,14`; both TOP goals for all ten alignments; 12 complete support
tables; 12 chosen pairs; and twin relations `12 -> 48` and `48 -> 12`.
These are exactly `10+10+6+20+12+12+2=72` checks and must be copied into
tests, never regenerated through a helper under test. In particular,
`GRAPH(pi_12)` is `((DI0,DR0,DR3),(DI1,DR1,DR2),(DT0,DR1,DI0),
(DT1,DR0,DI1))`, `GRAPH(pi_16)` is `((DI0,DR0,DR2),(DI1,DR1,DR3),
(DT0,DR3,DI0),(DT1,DR0,DI1))`, and they must be unequal.

## 3. Measures, constructors, and projection domains

MOTIF uses one uniform `pi`: source reveals `GRAPH(pi)` and target shares it.
RANDOM uses independent uniform `pi_s0,pi_s1,pi_t`. These are complete finite
products, never samples. For every `c in CALSET`,
`A(c)={pi in ALIGN: CAL(pi)=c}` has 16 elements and, for either goal, four
distinct pairs at count four. LOCAL and RANDOM_SOURCE therefore have reduced
value 1/4; MOTIF_SCHEMA and ORACLE have value 1. RANDOM source independence is
an integer product-count identity.

The positive domains are exactly:

```text
LOCAL_DOMAIN  = CALSET x (DT0,DT1)                              = 12
MOTIF_DOMAIN  = {(graph,graph[0:2],g): graph in GRAPHSET,
                 g in (DT0,DT1)}                                = 96
RANDOM_DOMAIN = GRAPHSET x GRAPHSET x CALSET x (DT0,DT1)        = 27648
ORACLE_DOMAIN = ALIGN x (DT0,DT1)                               = 192
```

Every public call passes through one fail-closed constructor over
`(projection_id,args_tuple)`; internal projection functions are inaccessible
to unvalidated host-language values. Validation precedence is exactly: call
and value arity; runtime tuple/type; goal literal; registered composite atoms;
pair/output ordering; alignment or CAL/GRAPH membership; RANDOM source
membership; MOTIF compatibility. Atoms are exact registered strings with no
subclass, alias, coercion, or normalization. Alignments, pairs, triples, graphs,
calibrations, arguments, and results are immutable tuples with exact recursive
structural equality. Ingredient pairs arrive strictly ordered; constructors do
not sort input. Graphs and calibrations must be structurally equal to registered
members. RANDOM validates each source separately; MOTIF requires
`cal == graph[0:2]`.

Every result is exactly
`(reduced_numerator,reduced_denominator,chosen_pair,support_table)`.
`support_table` contains every `(pair,count)` in global descriptor-index order;
`chosen_pair` maximizes count and uses that order for ties. LOCAL enumerates
`A(cal)`. MOTIF reads the requested graph pair. RANDOM validates both source
graphs but cannot use them to alter target counts. ORACLE returns the requested
TOP pair with count one. There is no filesystem, environment, cache, RNG,
dynamic import, mutable global, cross-principal reference, undeclared channel,
or normalization after construction.

## 4. Exact SK08 negative registry

The complete registry is the 25 distinct calls in the bound vectors, attempted
once in listed fixture-ID order. Their exact category/projection/code sequence
is:

```text
001 malformed LOCAL         SK08_E_ARITY
002 malformed MOTIF_SCHEMA  SK08_E_ARITY
003 malformed RANDOM_SOURCE SK08_E_ARITY
004 malformed ORACLE        SK08_E_ARITY
005 malformed LOCAL         SK08_E_ARITY
006 malformed MOTIF_SCHEMA  SK08_E_ARITY
007 malformed ORACLE        SK08_E_ARITY
008 malformed LOCAL         SK08_E_TYPE
009 malformed MOTIF_SCHEMA  SK08_E_TYPE
010 malformed RANDOM_SOURCE SK08_E_TYPE
011 malformed ORACLE        SK08_E_TYPE
012 noncanonical LOCAL         SK08_E_ATOM
013 noncanonical MOTIF_SCHEMA  SK08_E_ATOM
014 noncanonical LOCAL         SK08_E_ORDER
015 noncanonical MOTIF_SCHEMA  SK08_E_ORDER
016 noncanonical LOCAL         SK08_E_GOAL
017 noncanonical MOTIF_SCHEMA  SK08_E_GOAL
018 noncanonical RANDOM_SOURCE SK08_E_GOAL
019 noncanonical ORACLE        SK08_E_GOAL
020 noncanonical ORACLE        SK08_E_ALIGNMENT
021 noncanonical ORACLE        SK08_E_ALIGNMENT
022 incompatible MOTIF_SCHEMA  SK08_E_MOTIF_INCOMPATIBLE
023 incompatible MOTIF_SCHEMA  SK08_E_MOTIF_INCOMPATIBLE
024 noncanonical RANDOM_SOURCE SK08_E_SOURCE_GRAPH
025 noncanonical RANDOM_SOURCE SK08_E_SOURCE_GRAPH
```

The populations are malformed 11 = four call-arity + three value-arity + four
wrong-type; noncanonical 12 = two atom + two order + four goal + two alignment
+ two source-graph; incompatible 2. Per projection they are LOCAL 6,
MOTIF_SCHEMA 8, ORACLE 6, RANDOM_SOURCE 5. The code histogram in lexical code
order is ALIGNMENT 2, ARITY 7, ATOM 2, GOAL 4, MOTIF_INCOMPATIBLE 2, ORDER 2,
SOURCE_GRAPH 2, TYPE 4.

A rejection counts only if `type(exc) is DomainError`, `exc.code` is the bound
code, and `exc.args == (exc.code,)`. Acceptance, a different exception/code,
computation before validation, mutation, report write, filesystem/environment/
cache access, or any other side effect is a mismatch. The all-pass expectation
is 25 attempted, 25 exact rejections, and zero mismatches.

## 5. Twin, costs, and bridge deletion

`tau=(R0 R2)(R1 R3)` fixes I0,I1,T0,T1. `TWIN(pi)` maps each descriptor to
`tau(pi(descriptor))`. Across 96 alignments it round-trips, changes all four
graph triples and both top actions, and preserves costs.

```text
raw acquisition MOVE+GATHER = 2
intermediate = 5
top = 8
CONJ(old_top,new_top) = 16
BRIDGE(old_top,new_top) = 17
```

Old/new products are namespace-tagged immutable atoms. The exact bridge domain
is `ALIGN x ALIGN x (DT0,DT1) x (DT0,DT1)`, 36,864 cases. Immediately before
the final craft, inventory is exactly
`{OLD::old_goal:1,NEW::new_goal:1}`; the craft consumes both and emits
`BRIDGE::B`. Delete each product once: exactly 73,728 checks. Each deletion
disables final craft and leaves fewer than eight actions to recreate the
deleted top. This is deletion necessity only; no substitution claim or domain
exists.

## 6. Prebound successful report and acceptance receipts

The only successful runtime byte string is the 2,102-byte
`golden_report.json`, SHA-256
`f94cbc8e0fe65d4144ea7cdf849e2a98983803914576d12f3557f34061556baf`.
It is one RFC-8785/JCS-compatible UTF-8 object with lexicographically sorted
members, compact separators, and exactly one terminal LF. It combines every
unchanged V4 report field with exactly the delta in the bound vectors, including
protocol `feltcraft_symbolic_kernel_v5`, 72 vector checks, and the complete
negative-boundary counts/histogram.

Its nine receipts, in immutable order, are:

```text
SK01_DOMAIN_INVERSE_V5                 [96,48,4,10,10,0]
SK02_CALIBRATION_VECTORS_V5            [6,16,6,0]
SK03_RANDOM_WITNESSES_V5               [12,4,4,1,4,12,12,0]
SK04_MOTIF_WITNESSES_V5                [96,1,1,20,0]
SK05_TWIN_WITNESSES_V5                 [96,2,0,0,0]
SK06_COSTS                              [192,5,192,8,16,17,0]
SK07_BRIDGE_DELETION                    [36864,73728,0]
SK08_PROJECTIONS_CLOSED_BOUNDARY_V5     [12,96,27648,192,72,25,25,0]
SK09_REPORT                             [1,6,0]
```

SK09 mechanically rejects: removed `protocol_id`; added top-level `debug`;
wrong protocol; unreduced random value 2/8; swapped first two receipts; and one
additional LF. The mutations target the complete V5 bytes. Any invariant or
implementation failure writes no successful report and exits nonzero. The
prebound all-pass object is an expected oracle only: no runtime result is
claimed at proposal time.

## 7. External SK10 source-bound audit

SK10 is `SK10_SCOPE_AUDIT_MANIFEST_V5`, external and post-freeze. Its normative
contract is `audit_contract.md`, SHA-256
`529bb737778679f8d4f528c06552d2cd4566e6da9b173bd7996ceb8d4b0799ea`;
its strict Draft-2020-12 receipt schema is `scope_audit.schema.json`, SHA-256
`115f1ce1efe996537adcfa57c452fbd7d2d5b349cbcdf4a210cc947ec840099a`.
The repository root is `.`, recursive audit root is
`feltcraft_symbolic_kernel`, and exact diff-base commit is
`742f8bfa4bf4e530fdf264150bff962506fe449f`. The complete tree is exactly five
real regular files in UTF-8 byte order:

```text
feltcraft_symbolic_kernel/__init__.py
feltcraft_symbolic_kernel/kernel.py
feltcraft_symbolic_kernel/report.py
feltcraft_symbolic_kernel/run.py
feltcraft_symbolic_kernel/test_kernel.py
```

No extra file, directory, symlink, device, ignored/generated path, deletion,
case collision, non-UTF-8 or noncanonical path is permitted. Every manifest
entry binds path, byte length, and raw-byte SHA-256. For each entry encode
`uint32be(len(path_utf8)) || path_utf8 || uint64be(size) || sha256_raw32` and
hash `b"feltcraft-scope-manifest-v1\0"` plus all entries. With rename detection
off, the union of NUL-delimited changed and untracked paths relative to the
bound base must equal the manifest paths exactly.

All manifested files parse with CPython 3.9 grammar. Local imports resolve to
the manifest. Allowed nonlocal modules are exactly `collections`, `fractions`,
`itertools`, `json`, `pathlib`, and `sys`. Dynamic imports, star imports,
vendoring, native extensions, dependencies, namespace extension, and unresolved
imports fail. The only CLI is
`python3 -I -m feltcraft_symbolic_kernel.run`, with no arguments, options,
stdin, environment, configuration, hooks, or alternate entrypoint.

The rule registry is exactly `feltcraft_scope_rules_v1`: F01 import closure;
F02 dynamic/reflection exclusion; F03 ingress/filesystem exclusion; F04
capability-token plus reachable-capability exclusion; and F05 complete local
call/reachability closure. Every unresolved indirect call fails. The only
optional filesystem effect is the resolved equivalent of
`Path("golden_report.json").write_bytes(exact_success_bytes)`. Runtime reads,
audit/review/manifest/receipt/scientific-artifact reads, and all other file
operations fail. The receipt records complete explicit inventories; the future
evaluator sets `passed` to the conjunction of all thirteen checks, and the
schema validates the resulting branch.

After implementation freeze, human governance creates the JCS-plus-one-LF
`scope_audit.request.json`. It binds the future architecture-change hash,
contract/schema hashes, bound diff base, frozen manifest root, request and
requester identities, sorted unique implementation-author identities, and
freeze/create times. A fresh reviewer starts in a new context after the request,
differs from every author, did not author or modify subject paths, had no
pre-request conversation context, and binds repository-relative identity
evidence. Times satisfy `frozen <= request-created <= context-created <=
review-started <= review-completed`. The future request, manifest, reviewer,
times, and receipt remain unresolved and no pass is predicted.

SK10 does not consume a runtime report, runtime result, scientific artifact, or
success claim. Runtime consumes no SK10 input or output. The receipt is evidence
for human governance only and is not a security proof, implementation result,
benchmark result, promotion token, or scientific result.

## 8. Exact visibility and ratification chain

The following audit items are visible only to
`SK10_EXTERNAL_SCOPE_AUDITOR` and `HUMAN_GOVERNANCE_REVIEW`, forbidden to
SKN01--SKN05, and permanently forbidden to every successor renderer, life,
agent, model, tokenizer, DREAM/SLEEP/memory, LoRA, GPU/remote, benchmark,
promotion, or scientific-claim stage:

```text
audit.contract_bytes_and_sha256
audit.schema_bytes_and_sha256
audit.repository_and_recursive_root
audit.diff_base_and_changed_paths
audit.frozen_file_bytes
audit.per_file_manifest
audit.manifest_root_sha256
audit.import_resolution_closure
audit.dependency_closure
audit.cli_options_hooks_closure
audit.forbidden_rule_registry
audit.capability_and_reachability_closure
audit.review_request_bytes_and_sha256
audit.reviewer_identity
audit.reviewer_freshness_evidence
audit.reviewer_independence_evidence
audit.scope_audit_receipt
```

The receipt is derived only at SK10. SK10 and human review are external stages,
not runtime nodes or edges. Audit inputs are not audit-subject source ingress.
No runtime output enters the audit, and no runtime or audit output enters
successor science.

There is no valid `ratification.change_sha256`. Authority validates exactly:

```text
ratification.change_id == intake.change_id
  == consensus.change_id == change.change_id
ratification.consensus_sha256 == SHA256(consensus bytes)
consensus.architecture_change_sha256 == SHA256(change bytes)
ratification.human_required_state_sha256 == SHA256(paused-state bytes)
paused_state.artifacts.architecture_change.sha256 == SHA256(change bytes)
paused_state.artifacts.architecture_consensus.sha256 == SHA256(consensus bytes)
approval_transition.source_state_sha256
  == ratification.human_required_state_sha256
approval_transition.artifact_sha256 == SHA256(ratification bytes)
```

The corresponding visibility IDs are exactly:

```text
authority.ratification.change_id
authority.ratification.consensus_sha256
authority.consensus.change_id
authority.consensus.architecture_change_sha256
authority.ratification.human_required_state_sha256
authority.paused_state.artifacts.architecture_change.sha256
authority.paused_state.artifacts.architecture_consensus.sha256
authority.approval_transition.source_state_sha256
authority.approval_transition.artifact_sha256
authority.ratification.authorized_scope
authority.ratification.forbidden_scope
authority.scope_proposal.requested_scope
authority.scope_proposal.forbidden_scope
```

They are visible to SKN01, SK10, and human governance and forbidden to
SKN02--SKN05 except for immutable constants released by SKN01 after the complete
valid chain. Intake revalidates the full change, interpretation, critique,
consensus, paused-state, ratification, authorization evidence,
approval-transition, and exact scope-equality chain. No current ratification
exists and approval is never inferred.

## 9. Authority and terminal firewall

The requested scope is exactly the sorted three atoms in `scope_proposal.json`:

```text
pure_cpu_symbolic_alignment_enumerator
symbolic_golden_report_and_scope_audit
symbolic_kernel_unit_and_property_tests
```

The forbidden scope is exactly its sorted eight atoms:

```text
benchmark_or_scientific_claims
dream_sleep_reader_or_memory_implementation
gpu_or_remote_actions
lora_model_or_weight_operations
model_provider_or_tokenizer_calls
promotion_to_rendered_or_model_stage
random_or_rendered_world_generation
source_life_or_target_agent_execution
```

Before exact human approval, implementation, tests, kernel execution, audit
execution, receipts, evidence generation, compute, promotion, and claims are
forbidden. After approval, only exact scope equality releases the requested
atoms. There is no adjacent or transitive authority. Runtime report bytes,
audit sources, audit receipts, reviewer evidence, and governance artifacts are
terminal and never become runtime input, audit input from runtime, or successor
benchmark/model/scientific input.
