# Fork assignment and phase-split contract

Status: proposal-only repair for `CONS_D02_CONTENT_BLIND_FORK_ASSIGNMENT` and `CONS_D04_PREMODEL_POSTDEV_PHASE_SPLIT`. This contract grants no implementation, execution, model/provider call, CPU, GPU, training, scientific, claim, publication, promotion, Stage-C, Stage-D, or successor authority.

## 1. Repair boundary and retained fork semantics

V1 allowed one fork assigner to own the treatment-to-branch registry while also seeing authentic-prior or treatment semantics. Fixed RNG equality is not a least-privilege proof. This repair separates a content-blind randomizer from a fixed-shape semantic installer, with a nonreifiable fixed-shape capability as their only bridge.

It retains all valid V1 fork obligations. Every registered post-native checkpoint/twin side forks byte-identical pre-fork state into exactly three isolated clones. AUTH, TWIN, and NULL are each installed once; a diagnostic actor receives one opaque reader and executes one nonretried legal probe. The exploration treatment is then completely unmounted/reset. Only the ordinary public action/outcome may vary at the target-blind delta compiler; it is combined with the common authentic prior and precommitted Dream-1 bytes. Evaluation receives only common authentic prior plus sealed delta in a fresh sterile process. P1 compiler RNG excludes treatment, branch, opaque label, lane, order, capability, registry, and assignment descendants; cut/sham draws are not resampled; failures are assigned zero-valued observations. This is a directional offline-compilation diagnostic, not formal mediation or generic online learning.

## 2. Separate roles

No process, service, shared cache, credential, log, exception path, or human-visible debug interface may combine a role's prohibited capabilities.

| Role | May receive | Must never receive | Sole output |
|---|---|---|---|
| `FORK_CONTENT_BLIND_RANDOMIZER` | protocol hash; root/side/checkpoint; presealed randomizer namespace; three fixed-shape opaque capability tokens; fixed clone-slot set | authentic-prior bytes; AUTH/TWIN/NULL semantic bytes or names; TWIN provenance; NULL contents; reader returns; target/truth/score; installation status/error/timing; compiler/evaluation data | opaque branch-label/order registry and opaque install-capability routes |
| `FIXED_SHAPE_SEMANTIC_INSTALLER` | canonical treatment input ports; three write-only opaque install capabilities; fixed installation schedule | branch labels/order; randomizer registry/map; capability-to-label relation; target/truth/score; diagnostic action/outcome; compiler/evaluation data | three same-shape sealed acknowledgements to reset/audit only |
| `DIAGNOSTIC_READER_ACTOR` | public fork opportunity and one opaque read interface | treatment identity; label/order/map; capability; prior/other-treatment internals; target/truth/results | exactly one legal probe action |
| `METADATA_ONLY_RESETTER` | declared metadata handles and process/cache registry needed to prove deletion | semantic memory, semantic interpretation, reader returns, target/truth/score | fixed-shape absence receipt to audit only |
| `DELTA_COMPILER` | common authentic prior, common Dream-1 bytes, public branch action/outcome, pre-fork paired-seed manifest | assignment/capability/registry/receipt/lifecycle/error/timing/handle descendants and future target/truth | target-blind sealed delta |
| `TERMINAL_AUDITOR` | sealed artifacts after terminal seal | any live cognitive write channel | failure-inclusive audit record only |

The randomizer's slot tokens are not treatment names. It may permute three uninterpreted token positions and three opaque labels/order positions, but cannot inspect or infer which token is later filled with AUTH, TWIN, or NULL. The installer sees canonical treatment input ports but cannot recover any token's branch label, execution order, or registry relationship. Thus the randomizer lacks content, while the installer lacks the branch map.

## 3. Capability semantics and one-time installation

An install capability is a nonserializable, unforgeable, write-only object whose only operation is `install_once(fixed_shape_memory_port)`. Its public representation is fixed-size but is not an identifier usable by cognition, a compiler, or the installer to recover a label or execution position.

1. **One use, one destination.** A capability admits exactly one attempted installation into its sealed clone slot. It has no read, enumerate, compare, copy, rebind, retry, or destination-discovery operation.
2. **No semantic observation.** The randomizer can create/route a capability but cannot open its treatment input or inspect installed content. The installer can write the designated port but cannot inspect the branch label/map. Neither may receive semantic-derived hash, byte length, token count, serializer variant, error text, or timing result.
3. **Fixed observable lifecycle.** Handle count, route count, installation call count, acknowledgement shape, omission marker, status code, error surface, timeout, retry count, schedule position, and public latency bucket are identical across branches. A failure uses the registered fixed-shape failure port, consumes its one attempt, and cannot trigger semantic repair or reordering.
4. **Sealed routing.** A routing fabric may transfer a write-only token from the randomizer's sealed route to an installer port, but exposes no map to the installer and no content to the randomizer. It is not cognitive and may not write prompts, seeds, targets, results, or pre-terminal-audit logs.
5. **Destruction.** At probe exit, capabilities, routes, installer workspace, treatment objects, local reader state, labels/order, caches, errors, and timing descendants are destroyed. The resetter may verify removal metadata only; its fixed-shape receipt is never input to Dream-2, compiler, installer, or evaluation.

The sealed composition is therefore: the content-blind randomizer maps opaque clone slots to opaque labels/order; the semantic installer writes AUTH, TWIN, and NULL through corresponding write-only capability routes on its canonical schedule. The map is hidden from the installer and content hidden from the randomizer. Any attempt to observe/serialize the composition is assignment-derived metadata and forbidden from positive cognition by the field ontology.

## 4. Randomization and mutation noninterference

The label/order permutation remains presealed and root-local, derived only from the frozen protocol hash, root, side, checkpoint, and dedicated randomizer namespaces. It is neither a population-balance claim nor an input to the actor, compiler, target allocator, scorer, or evaluator. The assignment record is sealed for terminal audit and never seeds a model/provider call.

A newly registered content-blind-assignment acceptance gate (no identifier is invented here) must mutate AUTH, TWIN, and NULL treatment semantics while holding protocol/root/side/checkpoint, opaque capability tokens, randomizer draws, public opportunity, and all allowed public inputs fixed. Each mutation must prove byte equality of:

```text
branch-label assignment and execution order
capability public shape, route count, and externally visible registry state
installation call, acknowledgement, lifecycle, error, timing, omission, and retry shape
all P1 compiler seeds and canonical field encodings
common Dream-1 bytes
all nonintervened compiler inputs, outputs, and downstream bytes
```

After a successful probe, the ordinary public action/outcome and its valid target-blind descendants are the only permitted branch difference. If treatment-semantic mutation changes any listed invariant—or a filename, path, handle, count, order, cache, provider request, exception, latency, resource abort, seed, label, schedule, or reset receipt visible outside the allowed role—the gate fails. It must exercise failed, NULL, malformed, timeout, reset, and crash paths; success-only equality is insufficient.

This gate is additive to retained `PAS_T03_RANDOMIZED_UNMOUNTED_MEDIATION`, `PAS_T07_DESCENDANT_VISIBILITY_TAINT_RESET`, and `PAS_T12_PREMODEL_COGNITION_BYTE_FREEZE`. It does not replace paired-RNG, unmount, sterility, failure-inclusive, mutation, or independent-review duties.

## 5. Strict A2 / post-B3 phase split

`DEV_FROZEN_CONFIGURATION` is retired as a mixed class. A later V2 bundle must use exactly these distinct classes and may not alias, nest, or derive one from the other inside B3.

| Class | Created / sealed | Contents | B3 consumers | Forbidden consumers / effects |
|---|---|---|---|---|
| `A2_PREMODEL_CONFIGURATION` | before B0 and every scientific model call; immutable through B3 | reviewed hashes and exact frozen bytes for prompts; models/tokenizer/template/sampler; DSL/parser/serializer; renderer/packet catalog; cadence/clocks/ties; SELF aggregation/unique-instance/equivalence/addition rules; reader/lifecycle/cursor/shape rules; cuts/shams; RNG/CRN; target/action/resource envelopes; failure rules; roster; and the two separately named AS-EXT candidate configurations | B0/B1/B2/B3 components only through declared frozen inputs | selector outputs; result-driven retuning; candidate substitution; root/target/arm/lane/retry changes |
| `POST_B3_DEV_DISPOSITION` | exactly once only after every B3 root, cell, failure record, resource record, and **both AS-EXT candidate series** seal | aggregate root summaries, completeness/failure/resource status, and reporting/planning-only designation among already executed series | terminal reporting and a future planning handoff only | every B3 actor, Dream-1, Dream-2, sleep/compiler, reader, randomizer, installer, resetter, delta compiler, evaluator, target allocator, scorer, resource-abort logic, root-completion logic, or live provider/model call |

The A2 package must bind both AS-EXT candidates' exact native interfaces, identities, resource policies, and B3 rows before B0. Both candidates execute all predeclared B3 cells under the same immutable pre-B3 A2 bytes, and both are reported with complete failures and resources. No selector may use an early result to skip, replace, retune, or silently suppress either candidate.

After every B3 seal, a one-time selector may apply only its already frozen tie rule to designate an *already executed* series for a predeclared report view or future planning handoff. It cannot make the designation a general winner, independent result, confirmation, resource-normalized claim, cognition change, or authority for a next stage. The nondesignated series remains reported; selection may not delete or hide it. Any future design needs new deliberation, review, and exact human ratification.

## 6. Phase-order and non-reachability acceptance semantics

A newly registered phase-split acceptance gate (no identifier is invented here) must prove from the hash-bound bundle and event ledger:

```text
seal(A2_PREMODEL_CONFIGURATION) < first_B0_model_or_provider_call
first_B0_model_or_provider_call <= every_B3_cognitive_or_target_event
seal(each_required_B3_cell, including both_AS_EXT_series) < create(POST_B3_DEV_DISPOSITION)
count(create(POST_B3_DEV_DISPOSITION)) = 1
```

It must prove graph non-reachability: no data, control, serialization, cache, seed, error, timing, resource-abort, or retry path from `POST_B3_DEV_DISPOSITION` reaches a B3 component or root-completion logic. Every B3 configuration dependency must resolve to the sealed `A2_PREMODEL_CONFIGURATION` hash, never a selector field, alias, mutable environment value, or post-hoc report configuration. Mutation of selected identity/disposition must leave every B3 input byte, model call, target, score, seed, fork route, compiler result, failure mapping, and root receipt unchanged. Mutation of either AS-EXT result before all cells seal must not alter pre-B3 bytes or suppress the other candidate's execution.

Missing chronological evidence, an early selector, second selector emission, unsealed B3 cell, selector-visible live cognition, or post-B3-to-B3 route is `NOT_RUN`/failure, never a fallback. The gate preserves and supplements `PAS_T05_TEXT_BASELINES_AND_DEV_SELECTION`, `PAS_T07_DESCENDANT_VISIBILITY_TAINT_RESET`, `PAS_T08_RESOURCE_CALENDAR_AND_STAGE_LOCK`, `PAS_T11_INDEPENDENT_REPRODUCTION_AND_CLAIM_FIREWALL`, and `PAS_T12_PREMODEL_COGNITION_BYTE_FREEZE`.

## 7. Later implementation boundary

This is a protocol specification only. Exact capability implementation, serializer fields, role/process isolation, ledger schema, test code, fixtures, and golden vectors may be added only by the separately reviewed, hash-bound A2 implementation package defined by the field ontology contract. No opaque backend can weaken the fixed-shape or non-reachability requirements.

Until the later bundle, review, tests, and exact human scope exist, every described gate is absent prospective work. Missing evidence is `NOT_RUN`, with no automatic B0/B3 execution, planning launch, Stage C/D transition, LoRA work, or scientific claim.
