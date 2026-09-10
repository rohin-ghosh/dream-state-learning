# RML Stage-B reuse and gap map

**Scope.** Planning advice only. It does not authorize implementation, provider calls, GPU work, training, or a science claim. Stage B here is the smallest post-Stage-A G1 gold-construct pilot: a frozen resolver gets supplied gold semantics through an explicit text reader and must execute J/P actions. It is not the G2 learned-DREAM/text stage and has no LoRA.

## Bottom line

Stage A provides a strong fluid/thermal world, exact targets, transitions, certificates, source history, and CPU isolation. The existing organism code supplies robust control-plane patterns and a typed reader/thinker core, but it is not directly an RML runner.

The hard gap is action execution. The generic ThinkerMachine has query, follow, hypothesis, predict, revise, backtrack, request-dream, release, and defer. It has no operation that validates and executes a public environment action, receives an ordinary successor state, or accounts for action cost. The scientific thinker adapter is also v03-specific: its goal compiler and scripted policy solve a one-edge causal_join recurrence probe, expressly not a final action task.

Do not wrap RML in run_v03r_recurrent_dry_run, V03RPublicAgendaCompiler, V03RGoldSemanticDreamer, V03RMechanicalSemanticAdmission, or ScriptedRecurrencePolicy. Build a small RML action-capable machine using their strict ledger/replay patterns.

The smallest substantive GPU condition is the four-cell G1 DEV factorial:

| Cell | Memory | Query policy | Necessary identification |
|---|---|---|---|
| G1_NONE_REC | none | recurrent generic anchors | no-life/prior and within-item reacquisition control |
| G1_C_OPEN | connected gold text | all anchors committed before any read | adaptive traversal, not a fixed query dump |
| G1_C_REC | connected gold text | recurrent generic anchors | positive gold-thinker gate |
| G1_A_REC | witnessed atoms only | recurrent generic anchors | P schema/connected-memory necessity |

Connected gold text is deterministic rendering of permitted local gold relations plus the allowed P schema. It is not learned text. A pass can establish only that RML is model-usable through supplied bounded text memory.

## Stage-A evidence and boundary

The Stage-A report says passed true, no failures, and CPU_STAGE_A_INSTRUMENT_CONFORMANCE. It records 0 model, GPU, and network calls; 16 pair attempts and 32 target attempts; 215,056 states; 1,230,784 transitions; about 30.5 seconds wall time; and about 66.5 MB peak RSS. It also records 16 target pairs and 32 sides, 32 certificates, twin public-byte collision with different valid plans, and run/skip isolation. [A1]

This establishes conformance of a one-pack CPU instrument. It does not establish a model-facing projection, GPU prompt, full collector, memory effect, or Stage-B authority. The rework plan explicitly says a green report cannot auto-release Stage B or a GPU/model action. [A2]

| RML-D0 source | Reuse in Stage B | Boundary |
|---|---|---|
| world.py | Direct | Closed public action decoding, pure step function, outcome rendering and action universe |
| targets.py | Direct | DEV J/P targets, twins, cuts and target fixtures |
| planner.py and certificates.py | Host/offline only | Gold corpus construction, headroom, correctness/cut audit; never model-visible |
| source.py, schema_reference.py, canonical.py, rng.py | Direct | Sealed common public history, canonical bytes, stable handles |
| isolation.py and isolation_worker.py | Pattern plus extension | New GPU process/KV/cache/source-hash isolation required |
| bayes.py and probes.py | Pre-GPU/offline only | No-life and shortcut gates; never cognition |

## Existing code reuse map

### Reuse unchanged

| Code | Use |
|---|---|
| research_loop/model_call_ledger.py | Exact model-call materials, token accounting, call scope, append-only records and reset-isolation checks |
| goal_conditioned_thinker.py: canonical JSON, checkpoint freeze, ExactCheckpointReader, typed query checks, scratch lineage, repeat blocking | Generic reader/scratch safety primitives and test patterns |
| cyclic_organism_contract.py | Provenance distinction among experiences, semantic rows, realizations/touches, checkpoints and temporary thought state |
| rml_d0 world/source/target/canonical/certificate modules | Authoritative RML environment and host-only oracle substrate |

### Partial reuse only

| Code | What is reusable | Why the runner cannot be reused |
|---|---|---|
| recurrent_text_organism.py | PublicExperience, MemoryItemView, semantic-decision validation, snapshot hashes, deterministic realization conventions, sealed trace ideas | Top-level runner has v03 fixture assumptions: 46 wake, 22 reactivation, 16 sleep, no_feedback/agenda/distractor arms and causal_join handling |
| scientific_thinker_adapter.py | One-operation model loop, strict operation parse, exact prompt/material ledger, deterministic replay | V03RPublicAgendaCompiler, compile_canonical_hardened_checkpoint and the policy are causal_join specific; no environment actions |
| scientific_dream_adapter.py | Target-blind serialization, strict parser and provider/admission separation | Its vocabulary, public witness types, route/effect parser and admission are v03-specific; Stage B needs zero DREAM calls |

### Explicitly exclude

- public_life_from_v03r, run_v03r_recurrent_dry_run and assert_v03r_gpu_preflight_ready import the v03 world and its P1 blocker logic.
- V03RPublicAgendaCompiler constructs one v03 causal-join query from v03 public probes.
- V03RGoldSemanticDreamer and V03RMechanicalSemanticAdmission encode v03 route/effect semantics.
- ScriptedRecurrencePolicy is a recurrence-probe ceiling, not an RML action policy.
- FrozenSchedule defaults and ARM_NAMES do not match the G1 matrix.

Port or adapt the generic tests for hidden-input rejection, immutable checkpoints, bounded atomic reads, repeat blocking, fresh workspace, parser failure and exact replay. Do not rename v03 route/effect tests as RML coverage. [A4][A5][A6]

## Blocking gaps

1. **Action-capable thinker.** RML J has a real nine-action path, while G1 permits up to ten actions. The new machine must execute one legal action at a time using rml_d0.world.resolve_public_action and step_public. A RELEASE record cannot substitute for COMMIT success.

2. **RML semantic row and reader schema.** The existing generic checkpoint assumes graph-like concept/edge fields. RML needs sealed one-atom text rows for local conditioner transformation, valve relation, module provenance and bounded P schema. A read returns one local row, NOT_FOUND, or CONFLICT. It cannot return a plan, target action, proof, target handle, provenance, score, or candidate ranking.

3. **Model-facing projection.** Stage A has public records but no frozen mapping from source history/target state to model state, allowed query vocabulary, text rows, action grammar, prompt bytes and output parser. This must be new and hash-bound.

4. **Trace-level causal-use reducer.** Offline planner/certificates can score correctness, but Stage B must additionally certify returned row handles, downstream scratch/action use, terminal COMMIT, masked-cut loss, twin substitution, and zero unsupported decisive action.

5. **No learned text corpus.** Deterministic gold text is legitimate for G1. G2 would need collector, replay bundles, proposal grammar, prospective prediction, admission, compiler and controls. Stage B must not imply DREAM/SLEEP.

## Minimum new files and interfaces

Use a new isolated package; do not edit RML-D0 or v03 runtime code.

~~~text
rml_stage_b/
  __init__.py
  fixtures.py
  memory.py
  machine.py
  runner.py
  tests/
research_loop/schemas/rml_stage_b_operation.schema.json
research_loop/prompts/rml_stage_b_think.txt
research_loop/workflows/rml_stage_b_gold_text_dev_v1.json
~~~

| File | Required interface | Output / invariant |
|---|---|---|
| fixtures.py | build_dev_pair, sealed_public_history, make_jp_goals, gold_rows | Public events, target-visible goals, gold rows and host-only certificates; no hidden side in cognitive objects |
| memory.py | seal_text_snapshot(rows), read_one(query, snapshot) | Closed ROW, NOT_FOUND, or CONFLICT projection; no goal/state/plan/provenance/candidate metadata |
| machine.py | RmlThinkerMachine, RmlGoalCompiler, RmlOperationPolicy | One operation/action at a time; append-only trace; public world transition; fresh item state |
| runner.py | run_g1_cell(manifest, cell, provider) | Sealed traces, model-call/resource ledger, host-only score/cut bundle; no retry or result-selected target |
| schema/prompt/workflow | fixed grammar, exact prompt/model/tokenizer/resource bounds | Fails before dispatch on changed or missing bytes |

Use one closed model operation grammar:

~~~text
QUERY_LOCAL(query_key, optional typed object)
UPDATE_PATH(read_handle, orientation)
FORM_SUBGOAL / BACKTRACK
EXECUTE_ACTION(public_action)
DEFER / STOP
RELEASE
~~~

A public action is schema-checked, decoded and executed before the next model call. The new state/outcome is the sole environment feedback. The policy cannot emit a plan array, free-text query, target answer, durable semantic write, or direct reader key. RELEASE is legal only after a successful COMMIT and a mechanically valid cited path/cut.

The query vocabulary is host-declared before item execution and binds typed subject/relation/object templates, allowed missing field and cardinality. P must expose a local schema atom, not an answer-valued completion.

## Exact minimum call envelope

The consensus design fixes DEV at four pairs: L=8 twin sides/lives. Keeping J and P, with four targets per stratum per life, yields 64 items per G1 cell:

~~~text
items per cell = 8 lives * 2 strata * 4 targets = 64
~~~

Registered J/P caps are 10 actions, 32 resolver operations, six text-memory reads, 256 visible tokens/read and 1,536 total read tokens per item. One resolver operation is one GPU model call.

| Resource | Per cell ceiling | Four-cell Stage-B ceiling |
|---|---:|---:|
| Resolver GPU calls | 2,048 | 8,192 |
| Deterministic text reads | 384 | 1,536 |
| Environment actions | 640 | 2,560 |
| Model output tokens, 256/call | 524,288 | 2,097,152 |
| Reader-visible tokens | 98,304 | 393,216 |

All are ceilings. Malformed, multi-operation, illegal, or truncated output consumes its registered operation and ends in fail/defer: no repair, reprompt, retry, fallback model, target replacement or extra budget. The text reader is CPU-only and must report bytes, candidate/index work and latency.

There are exactly zero DREAM calls, replay calls, SLEEP calls, LoRA fits, adapter mounts or training tokens in Stage B. Any of these expand scope into G2/G3.

A one-pair/two-cell effort can be a smoke test only. It cannot satisfy the G1 gate because it omits either adaptive-query control C_OPEN or the P atoms-versus-connected/schema control A_REC.

## Stop gates

1. **Authority and lock.** Stage-A success is insufficient. Require new human-ratified scope, reviewed exact prompt/schema/model/tokenizer/workflow hashes, four-pair manifest, independent review/advocate artifacts, and absolute resource ceilings. Any mismatch or undeclared code load is no-dispatch.

2. **CPU RML adapter.** Before GPU work, replay all RML action transitions through the new machine; prove source/run-skip hashes are unchanged; prove no TargetSpec hidden fields, twin side, planner/certificate, useful pair, valve truth or scorer field enters prompts/rows/reader returns; prove direct-record closure is zero.

3. **Reader correctness.** Every allowed query resolves exactly one sealed row or closed absence/conflict. Stop on mutable corpus, full plan/terminal-action text, goal-conditioned retrieval, query outside vocabulary, provenance leak or backend metadata exposed to the resolver.

4. **G1 gate.** Score only after every registered trace seals. Require separately for every retained stratum: G1_NONE_REC <= .35; G1_C_REC >= .85; constructive cited-path rate >= .80; G1_C_OPEN <= .45 and <= .35 overall; G1_A_REC <= .35 on P; cut masking and matched twin substitution invalidate at least .80 of credited C_REC successes; unsupported decisive release equals zero; and no visibility/parser/reset/backend/evaluation-isolation defect. [A3]

5. **Claim stop.** Even a pass permits only supplied-gold, bounded-text recurrent reconstruction in one pack at one frozen model checkpoint. It does not permit learned text, DREAM, SLEEP, parametric memory, post-native, scaling, generalization, or action-memory flywheel language.

6. **Scope stop.** No learned DREAM collector, LoRA, on-policy wake, extra mechanism pack, calibration/confirmation, or post-native claim may follow automatically.

## Required test port

| Existing test pattern | RML adaptation |
|---|---|
| hidden-input rejection | Reject hidden target/twin/planner/certificate/answer fields in all model-visible bytes |
| immutable checkpoint and exact reader | Seal row/index bytes; reject post-seal mutation; one atom per return |
| repeat and budget handling | Duplicate query/action consumes a step; malformed or over-budget output terminally fails/defer |
| fresh reset isolation | New process/KV/prompt/workspace/RNG per target; source/hash immutable afterward |
| scientific execution replay | Replay exact prompt/input/output ledger against the RML action machine |
| RML-D0 world tests | Retain world transitions, targets/twins/necessity, no-life Bayes, source-growth and canonical-rendering suites |

The workspace has neither a pytest executable nor a Python pytest module, so this advisory does not claim a new test run; it is based on static source and test inspection.

## Evidence

- [A1] rml_d0/stage_a_report.json — pass/firewall, resources, fixture counts, isolation and scope-call values.
- [A2] research_loop/plans/rml_d0_stage_a_rework_v1.md — Stage-B block and non-auto-release requirements.
- [A3] research_loop/plans/rml_g1g2_hybrid_consensus_v1.md — §§4–6 and 10–11: DEV counts, call formulas, G1 cells/gates and stop rules.
- [A4] research_loop/goal_conditioned_thinker.py and test_goal_conditioned_thinker.py — typed DFS/reader and adversarial safety tests.
- [A5] research_loop/recurrent_text_organism.py and test_recurrent_text_organism.py — generic artifact patterns and v03 schedule coupling.
- [A6] research_loop/scientific_thinker_adapter.py, scientific_dream_adapter.py and their tests — strict scientific boundary pattern and v03 coupling.
- [A7] rml_d0/world.py, targets.py, source.py, planner.py, certificates.py and isolation.py — RML action world and host-only oracle/isolation foundation.

