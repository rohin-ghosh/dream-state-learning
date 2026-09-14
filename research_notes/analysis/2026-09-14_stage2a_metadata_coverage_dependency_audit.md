# Stage2A birth metadata: static coverage and bounds audit

Builder, September 14, 2026, 00:38 UTC (September 13 Pacific).
Scope: source inspection only, on checkout `da0c3b5f`. No constructor,
material, tokenizer, model, scanner run, or test suite was executed.

## What is already available

`validate_birth_source` rebuilds the entire selected BirthCase and exact
ArmRecord, including off-trace construction, and produces immutable snapshots.
Its dataclass-tagged digest tree is a source-integrity representation, not the
canonical scientific semantic object. Reusing its hash in place of the
underlying protected metadata would not supply semantic-alias coverage.

The scanner's twelve protected roots are fixed. The table below is a
**dependency checklist**, not a newly bound output schema or an assertion that
an inventory producer exists. Naming, scalar layout and duplication decisions
still need an explicit producer contract before computing canonical bytes.

| Protected root | Existing source to account for | Remaining dependency |
|---|---|---|
| `case_id` | BirthCaseDescriptor world/member and case_id property | Exact scalar/array encoding is an implementation choice; do not substitute a hash |
| `causal_pair_id` | World/member pairing, pair_type and the paired intervention construction | Declare the deterministic pair identity rather than borrowing unit identity |
| `core` | Retained public graph plus descriptor factors and target phase | Route depth, failed-STEP counting, recovery SEEK position and prior-STEP history are still owner-unbound |
| `evaluator` | Expected target plus private task/outcome facts actually consumed by checking | Account for each consumed private value; original history must not enter the public graph |
| `factors` | Descriptor pair_index/bucket/pair_type/family/family_motif/flow/recovery_subtype/terminal_class/goal_side/goal_index/skin/domain and derived family_bit/relation_slot | Bind layout without dropping inconvenient private labels |
| `future` | Accepted BirthFutureInputs candidates, disclosure provenance and future_identifiers | Universe/disclosure are already resolved; no new owner decision or second parser needed |
| `mutation` | Relation FOR swaps and mismatch predicted-versus-effective destinations in the constructor | Preserve field-level source identity and intervention meaning, not just a changed hash |
| `oracle` | Complete BirthTraceTurn sequence, BirthTraceFacts, and expected BirthTargets used for checking | Trace provenance is available; a trace ending at CONTINUE is not a total route definition |
| `recovery_match_id` | BirthCaseDescriptor recovery_match_id | Preserve tuple/null distinction in the declared encoding |
| `role_keys` | Complete reconstructed world role bindings and their source paths | Do not restrict to the selected successful trace |
| `target` | TargetUnit and corresponding BirthTarget: exact bytes/hash, command/operand, ordinal/phase, trace boundary, selection index, before/after CURRENT | Do not derive unresolved core conventions from an incidental None selection index |
| `unit_id` | Shared TargetUnit.unit_id; the two ArmRecords have separate arm/prefix identities | Keep shared supervised target identity distinct from arm receipt identity |

Additional source surfaces needing an explicit disposition, not silent
omission: task/task_text; complete construction blocks/raw registry/effective
world edges; exact retained prefix and its source-turn indices; source contract
pins, display-master and role-binding provenance. Some are public or integrity
metadata rather than protected semantic labels. Their location and duplication
must be declared. The held-case semantic schema has its own service/task/world
roots and is not permission to transplant that schema to birth cases or to
move private labels under an unprotected root.

## Concrete size risk, without fabricating an inventory

Scanner limits currently include 4,096 scalar leaves, 32,768 nodes,
32,768 aliases, depth 64 and one MiB input. The leaves/node traversal counts
the entire semantic object, including leaves outside the protected roots;
only alias emission is filtered by protected root. Alias count is not bounded
by leaf count alone: each leaf can emit a pointer, key, scalar, tagged pair,
and multiple lexer atoms, subject to deduplication and exemptions.

A directly determinable **conditional** lower bound matters for the eventual
layout. Birth construction iterates 25 states for family A or 7 for B; each
state has 24 ordinary relation blocks, each with four seven-field EVENT rows.
If those complete rows are represented as separate scalar fields once:

| Family | Ordinary EVENT rows | EVENT-field scalar leaves alone |
|---|---:|---:|
| A | 25 × 24 × 4 = 2,400 | 2,400 × 7 = 16,800 |
| B | 7 × 24 × 4 = 672 | 672 × 7 = 4,704 |

Both exceed the present 4,096-leaf bound before directories, effective edges,
role bindings, targets, core, future IDs or recovery extras. This is source
arithmetic, **not an observed scanner failure** and not proof that every valid
schema has those leaf counts. Packing rows as raw strings changes the count
but still requires full semantic coverage and lexer/byte bounds; it must not
be chosen merely to suppress findings. Do not truncate, sample, silently
drop off-trace metadata, or relax checks after inspecting results.

No safe final byte/node/alias/depth bound can be certified until the complete
schema and finite route universe are defined. Once bound, measure the full
defined source envelope prospectively, choose explicit adequate hard limits,
and validate boundary failure behavior. The separately accepted 16,384 future
identifier bound does not solve this semantic-object bound.

## What remains blocked

Bohr independently checked the latest local handoff/notebook and source
dispositions read-only: no answer to the registered-route or core questions.
Existing range/nullability validators receive caller-supplied core values;
they do not define how those values are derived. No empty route inventory or
arbitrary maximum depth is justified. The complete producer and material/
native opening remain blocked on these definitions. This audit neither adds
a formal C11 gate nor qualifies the reduced screen or any scientific claim.

Next implementation is the complete source-derived inventory adapter after
those bindings, with explicit complete-envelope bounds. Actor/runtime/custody/
continuity suites already have receipts and were not repeated for this audit.

## Inspected source pins

| File under `organism_v6/` | SHA-256 |
|---|---|
| `composition_birth_stage2a_birth.py` | `4bc75a39265950d14ed5dced277cd4430425a72ce8583c6233d0478b891d7d84` |
| `composition_birth_stage2a_targets.py` | `6ac494d8da6c684d0abe7196ab88e652389c03b890f408cb90f615ae2c86fb8a` |
| `composition_birth_stage2a_source_inputs.py` | `c0034ecbe08061157eb8525a2898de4a9c0ea3a445d40981b8b6a1c62d5a0323` |
| `composition_birth_stage2a_scanner.py` | `bc07eee278d02fbb925bae05d41ea8f98dbde0d35efe20f41574fe59c41532e2` |
| `composition_birth_stage2a_graph.py` | `6f363eba3ef3f50622b68581949f64ab9155ea91568843f6219ec9ea9c0404b5` |
| `composition_birth_stage2a_graph_inputs.py` | `12b3d0b20d7190abf29a501063ee19c281c9295e6e08a53bfe73f520ce604151` |
| `composition_birth_stage2a_future_inputs.py` | `e0b2b4572b1d4fe9f25cc861d2d08c4e3c9046d220c237560a6732ceb1335930` |
