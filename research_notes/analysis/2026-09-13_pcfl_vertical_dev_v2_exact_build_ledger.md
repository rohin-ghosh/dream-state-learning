# PCFL vertical DEV v2.1: exact build ledger

**Date:** 2026-09-13 UTC  
**Status:** implementation ledger only; no redesign, source authoring, model use,
fit, or GPU execution  
**Controlling design:**
`2026-09-13_pcfl_vertical_dev_v2_synthesis.md` at current HEAD  
**Independent disposition:**
`2026-09-13_pcfl_vertical_dev_v2_final_skeptic.md`, final verdict `PASS`  
**Code-reuse ruling:**
`2026-09-13_pcfl_vertical_dev_v2_implementation_reuse_map.md`

This memo translates the passed protocol into an implementation work ledger. It
does not change a scientific choice. If this ledger conflicts with the passed
protocol, the protocol controls; if the skeptic's final addendum repairs earlier
text, the final addendum controls.

## 1. Frozen constants: copy these, do not infer them

```text
BASE                     Qwen2.5-7B-Instruct, exact model/tokenizer hashes bound
DEV_ROOTS                2, independently generated; realized O bits 0 and 1
EXCLUDED_ROOTS           4
CUBE_PER_ROOT            8 cells: (O,R,D) in {0,1}^3
DELAYED_GOALS_PER_CELL   2

S1_FITS_PER_ROOT         4: AUTH, ATOMS, EVENT_TWIN, LINK_PERMUTE
S2_FITS_PER_ROOT         3: FULL_R0, FULL_R1, OLD_REPLAY
TOTAL_FITS               14

SLOTS_PER_FIT            20 query-response slots
VIEWS_PER_SLOT           8
ITEMS_PER_EPOCH          160, physical packing off
BATCH / ACCUMULATION     4 / 1
EPOCHS                   5
UPDATES_PER_EPOCH        40
UPDATES_PER_FIT          200
TOTAL_UPDATES            2,800

LORA                     r8, alpha16, dropout .05, all q/k/v/o/gate/up/down
DTYPE                    bf16
OPTIMIZER                AdamW(beta1=.9,beta2=.999,eps=1e-8,wd=.01)
LR / GRAD CLIP           3e-5 / global norm 1.0
MAX_SEQUENCE             512; zero target truncation; no packing
LOSS                     response-only; wrapper and metadata masked; EOS active
INITIALIZATION           clean C0 tensors + fresh optimizer for every fit
CHECKPOINT               final only

SERVICE                  READ EVENT / READ EVENTS_AT / READ LINKS_FROM
SERVICE_LIMITS           <=12 calls, <=4096 returned tokens, <=2048 actor tokens
NATIVE_LIMIT             <=2048 generated thought/action tokens, one ROUTE
CANARY                   40 items, common-random seeds

TRAIN_CAP                30 A40-min/fit; 7 aggregate A40-hours
INFERENCE_CAP            10 aggregate A40-hours
TOTAL_CAP                17 aggregate A40-hours
```

No rank/dose/seed sweep, checkpoint selection, replacement root, scientific
retry, trained false `MISS`, per-token weighting, approximate dose matching, or
duplicated semantic request is part of this run. The first scheduled `S1_AUTH`
and, if reached, `S2_FULL_R0` are the two resource profiles and remain two of the
fourteen scientific fits.

## 2. File ownership

| file | owns | may import/reuse | must not own |
|---|---|---|---|
| `organism_v6/pcfl_vertical_dev.py` | pure dataclasses/wire, world/cube, two CPU oracles, receipts, EVENT/LINK compiler, query materializer, controls, route/service scorers, pure reducer | canonical hashing/order patterns | tokenizer/model/GPU/process logic |
| `gpu/astra_pcfl_vertical_dev.py` | preparation, real-tokenizer binding, prompt/render inventory, native generation, fits, stage DAG, budgets, rollback, sealing/custody/collection | L2 runtime architecture; trainer and Q0 audit primitives | new scientific semantics or oracle-derived model input |
| `organism_v6/train_adapter_v3.py` | explicit AdamW fields, grad clipping, optional strict per-update audit trace; defaults preserve old callers | existing encode/order/collate/LoRA | PCFL-specific arm or route logic |
| `tests/test_pcfl_vertical_dev.py` | exhaustive pure science and integrity tests | scripted/fake tokenizers only where declared | native/model tests |
| `tests/test_astra_pcfl_vertical_dev.py` | tokenizer/trainer/runtime/DAG/custody tests | scripted backends and tiny CPU model | scientific source definitions |
| `tests/test_train_adapter_v3.py` | generic optimizer/clipping/audit regressions | tiny CPU model | PCFL world tests |

Do not modify `organism_v6/l2_public_record_dev.py` or
`gpu/astra_l2_public_record_dev.py`. Reuse their patterns, not their binary
world/schema. If shared-trainer editing is unsafe at implementation time, the
passed reuse map permits a narrow `organism_v6/pcfl_vertical_train.py` wrapper;
that file-location choice must not alter any frozen optimizer behavior or
receipt below.

## 3. Required pure data structures

The names below are the build API. All are frozen dataclasses or equivalent
closed-schema records and pass through exact JSON-safe wire encoding preserving
bytes, tuples, and type identity.

| type | minimum fields / invariant |
|---|---|
| `OpaqueInventory` | separate tuples for node, port, event, link, probe, receipt, goal, PAD IDs; fixed-width ASCII; namespace-disjoint; pinned-tokenizer token lengths |
| `RootManifest` | `root_id`, seeds, inventory, graph skeleton, realized DEV `O` if applicable, presealed primary reachout render, wrapper/order/RNG assignments, hashes |
| `WorldCell` | `root_id`, `O`, `R`, `D`, exact public graph/outcomes and private route/cut facts; no private field in public projection |
| `TaskRender` | root/cell/goal/render IDs, exact visible bytes, public/private allowlists, correct route kept private, visible-byte hash |
| `PublicReceipt` | root/branch/stage/turn, receipt ID, executed source/port/destination, previous hash, exact bytes/hash, chronology |
| `ChildGeneration` | exact prompt/messages/token receipt, raw output bytes/hash, EOS/truncation, public-input hashes |
| `ChildSpan` | generation hash, byte start/end, exact line bytes/hash, proposal kind |
| `Admission` | accepted/rejected, reason, cited receipt hashes, chronology result, semantic-field copy checks; rejected attempts retained |
| `EventRow` | exact admitted child span for one `EVENT`; never reconstructed from fields |
| `LinkRow` | exact admitted child span for one `LINK`; never reconstructed from endpoints |
| `FormationReport` | all attempts plus accepted OLD/NEW rows and fixed-denominator gate counts |
| `MemoryQuery` | one exact request: kind plus opaque address; no task/goal/history |
| `ResponseBlock` | request bytes, exact ordered child spans, exact response bytes/hash, row hashes, terminal-LF invariant |
| `CorpusSlot` | stage, arm, slot ID, semantic-or-PAD, request bytes, target bytes, evidence IDs, target hash |
| `RenderedItem` | slot/view IDs, loss-masked request wrapper, exact target block, target-token count, mask hash, sequence length |
| `CorpusManifest` | arm/root/stage, semantic and PAD counts, held-out addresses, 20 slots, 160 item hashes/order, equal stage target-token total |
| `FitReceipt` | frozen config, clean-base and initial/final LoRA hashes, optimizer hashes/defaults, five epoch orders, 200 per-update records, time/GPU/process receipt |
| `ServiceGeneration` | exact request, goal-blind LoRA worker prompt, raw response, semantic/strict/refusal/false-row scores, source identities |
| `ActorGeneration` | endpoint/condition/view, exact prompt, raw bytes, token/EOS/truncation, reads/returns, single committed ROUTE |
| `RouteScore` | strict parse, legality, graph success, OLD/NEW dependency status kept as separate booleans |
| `CanaryReport` | 40 paired outputs, legal count, C0 delta, collapse/dialect checks, accept/rollback result |
| `RootState` | phase, exact authentic ancestor, control quarantine identities, immutable pre-evaluation AUTH snapshot, branch taint |
| `StageRecord` | stage/dependency hashes, inputs, outputs, counters, device seconds, terminal/failure status |
| `RunSeal` | source/binding manifest, immutable artifact inventory, terminal witness, whole-root hash, reduction hash |

Authentic and non-lineage objects must be distinct closed types or carry a
fail-closed taint enum. `MECHANISTIC_FORK`, `CONTROL`, `WRONG_ROOT`,
`NONCANONICAL_R`, and `EVALUATION_FORK` can never be accepted as an authentic
ancestor.

## 4. Exact function ledger

### 4.1 Pure core: `organism_v6/pcfl_vertical_dev.py`

| function | input | output / required behavior |
|---|---|---|
| `canonical(value)` / `digest(value)` | closed wire value | JCS-like deterministic bytes / SHA-256 |
| `to_data(value)` / `from_data(payload, expected_type=None)` | closed record | exact bytes/tuple/type-preserving JSON wire; reject unknown fields/types |
| `validate_opaque_inventory(inventory, token_measurements)` | proposed IDs plus already-measured tokenization receipt | fixed-width/namespace/registered-row constraints; no tokenizer call in pure core |
| `build_root(manifest)` | sealed inventory/seeds | one `RootManifest`/base skeleton; no model use |
| `expand_cube(root)` | base root | exactly 8 `WorldCell`s, one for every `(O,R,D)` |
| `render_task(cell, goal, render_id, projection="FULL")` | cell/goal/presealed render | exact `TaskRender`; projections include FULL, OLD_ONLY, NEW_ONLY and registered cuts |
| `oracle_route_v1(cell, goal, cut=None)` | private graph | unique route or no route |
| `oracle_route_v2(cell, goal, cut=None)` | same | independent implementation; byte-equal result to v1 |
| `parse_route(raw)` | complete child bytes | exactly one `ROUTE <start> <goal> : <ports>` or rejection; no prefix/suffix/multiple route |
| `execute_route(public_graph, parsed)` | committed full route | legality and graph success with zero intermediate return |
| `audit_construct(excluded_roots)` | 4 roots × complete cube | all exact Section 5 counts and shortcut report; fail closed |
| `make_receipt(...)` / `check_receipt(...)` | action/public outcome | immutable exact public receipt chain |
| `parse_event_line(span)` | one physical child line | strict grammar, single spaces/LF, no normalization |
| `parse_link_line(span)` | one physical child line | same; exact two cited receipts |
| `admit_event(span, receipts, visible_state)` | child span and prior public state | copy/chronology/evidence checks; whole-line accept/reject |
| `admit_link(span, receipts, admitted_events, visibility_phase)` | child span and allowed causal state | endpoint/shared-node/evidence checks; no identifier repair |
| `formation_report(attempts, phase)` | all attempts | OLD or NEW denominators, precision, span custody, visibility verdict |
| `materialize_queries(rows, stage, arm)` | exact admitted/control rows | deterministic request→`ResponseBlock` map with exact arm roster below |
| `make_event_twin(root, rows)` | presealed alternate-O world and registered IDs | coherent synthetic control; never authentic lineage |
| `make_link_permute(rows, permutation_spec)` | authentic events + presealed derangement | endpoint-incompatible LINK control; never authentic lineage |
| `make_pad_slots(stage, arm, deficit_spec)` | presealed PAD namespace/token deficit | parser-disjoint PAD only; no world identifier or usable row |
| `render_views(slots, wrappers)` | exactly 20 slots × 8 wrappers | exactly 160 response-only items; wrapper/metadata masked |
| `score_memory_response(raw, registered)` | raw worker bytes and exact block | semantic exactness and strict surface exactness separately |
| `score_route_generation(raw, task)` | raw actor bytes and public graph | parse/legal/success separately; failures remain zero |
| `reduce_run(sealed_records)` | one immutable complete/failed run | ordered failure label, branch labels, every denominator/gate; deterministic |

`materialize_queries` must reject duplicate request bytes with different
targets, missing required addresses, wrong sorting, semantic fields not present
in exact admitted spans, trained treatment-address `MISS`, or any arm roster
other than Section 5.

### 4.2 Runtime: `gpu/astra_pcfl_vertical_dev.py`

| function | input | durable output / required behavior |
|---|---|---|
| `validate_spec(spec)` | proposed run spec | exact schema, all frozen constants, no unbound source/model/tokenizer/root/prompt/control |
| `allocate_opaque_inventory(tokenizer, seed)` | pinned real tokenizer and presealed seed | first deterministic valid inventory plus complete token measurement receipt; no redraw after scientific failure |
| `prepare(spec_path, spec_sha256, root, allow_native=False)` | offline spec | sealed source snapshot, bindings, all roots/cubes/renders/wrappers/assignments, CPU audit, request/resource inventory; no model load unless explicitly allowed |
| `verify(root, plan_sha256, native=False)` | prepared root | recompute all hashes/allowlists/caps; reject extra/missing/tampered files |
| `encode_training(corpus, tokenizer, trainer)` | one 20-slot corpus | exact target-token/mask/EOS report; 160 nonempty singleton sequences; no truncation |
| `fit_stage(plan, root_state, arm)` | sealed corpus and clean C0 | one final adapter plus `FitReceipt`; 200 finite updates; fresh optimizer; hard 30-minute cap |
| `capture_formation_stage(...)` | ordinary public wake context | raw-before-feedback generation, receipt, all proposals/admissions; no hidden/checker/answer bytes |
| `run_memory_service(...)` | clean C0 actor + goal-blind LoRA worker | bounded read loop; raw uncorrected returns; exact request/return logs |
| `run_native_actor(...)` | C0 or one mounted authentic adapter | one candidate-free task generation and one ROUTE; no service injection |
| `run_reachout_primary(...)` | restored untouched S1_AUTH snapshot | exactly one native relevant/distractor probe commitment; reveal public result only after commitment |
| `fork_public_outcomes(...)` | exact sealed native pre-outcome state | two R0/R1 continuations differing only in ordinary public result; separate NEW formation |
| `run_canary(...)` | C0 and authentic candidate | 40 paired items; accept or rollback while retaining writer failure |
| `dependency_states(...)` | stage DAG and sealed records | only exact registered ancestors; taint/control fork rejection |
| `run_stage(...)` / `worker(...)` | one presealed stage ticket/GPU | fresh process group, deadline, exact work ledger, verified owned cleanup |
| `execute_dag(...)` | prepared plan | Section 6 DAG only; sibling-safe stop semantics; no resume/retry/replacement |
| `finalize(...)` / `custody(...)` / `collect(...)` | terminal tree | immutable inventory, terminal witness, external whole-root custody, one reduction |

Extend `TrainConfig` with explicit `adam_beta1`, `adam_beta2`, `adam_eps`,
`weight_decay`, `max_grad_norm`, and strict-audit enablement. In strict mode,
record every update's loss, pre/post-clip norm, row identity, and CPU/CUDA RNG
hashes; also bind initial/final trainable-tensor and optimizer-state hashes.
Receipt generation must not mutate training state.

## 5. Exact materialization ledger

### 5.1 Query blocks

```text
READ EVENT e       -> the one exact admitted EVENT span for e
READ EVENTS_AT n   -> every admitted EVENT with source n, event-ID sorted
READ LINKS_FROM e  -> every admitted LINK with first event e, link-ID sorted
absent address     -> empirical refusal/false-row gate; never a trained target
```

Multi-row separator is exactly one LF and the final child row retains its own
terminal LF. Required multi-row regression cases are:

```text
S1 READ EVENTS_AT S_L  -> e0,e6
S1 READ EVENTS_AT B    -> e4,e5
S1 READ LINKS_FROM e3  -> l2,l3
S2 READ EVENTS_AT H    -> e2,e8
S2 READ LINKS_FROM e1  -> l1,l4
```

All other registered response blocks have one row; maximum adjacency is two.

### 5.2 Arm counts

| arm, per root | semantic blocks | exact decomposition | PAD | slots |
|---|---:|---|---:|---:|
| `S1_AUTH` | 17 | 8 EVENT + 6 EVENTS_AT + 3 LINKS_FROM | 3 | 20 |
| `S1_ATOMS` | 14 | 8 EVENT + 6 EVENTS_AT; LINK addresses held out | 6 | 20 |
| `S1_EVENT_TWIN` | 17 | alternate-O 8 + 6 + 3 | 3 | 20 |
| `S1_LINK_PERMUTE` | 17 | authentic EVENT 8 + 6; deranged LINK 3 | 3 | 20 |
| `S2_FULL_R0` | 19 | 9 EVENT + 6 EVENTS_AT + 4 LINKS_FROM | 1 | 20 |
| `S2_FULL_R1` | 19 | 9 EVENT + 6 EVENTS_AT + 4 LINKS_FROM | 1 | 20 |
| `S2_OLD_REPLAY` | 17 | old 8 + 6 + 3; NEW addresses held out | 3 | 20 |

Per root this is 120 semantic blocks + 20 PAD = 140 slots. Across two roots it
is 240 semantic blocks + 40 PAD = 280 slots. Each fit materializes 160 unique
rendered items and presents them once per epoch for 800 item-presentations.
Across fourteen fits: 2,240 unique rendered items, 11,200 presentations, and
2,800 optimizer updates.

Stage-level loss-active target-token totals must be identical across arms only
after real chat-template rendering and inclusion of assistant EOS. All deficits
go only into registered PAD targets. Context-token totals may differ but must
be reported.

## 6. Exact stage DAG

```text
PREPARE
  -> CPU_CONSTRUCT_GATE[4 excluded roots, 32 worlds, 64 tasks]
  -> ZERO_FIT_DELAYED[10 conditions x 64 tasks]
  -> ZERO_FIT_REACHOUT[5 conditions x 32 tasks]
  -> FORMATION_ONLY_ROOT[grammar/parser tuning; zero fits]
  -> FREEZE_GRAMMAR_PARSER
       |-> ROOT_0_OLD_FORMATION[realized O=0]
       `-> ROOT_1_OLD_FORMATION[realized O=1]

For each surviving root independently:

OLD_FORMATION
  -> MATERIALIZE_S1
  -> {FIT_S1_AUTH, FIT_S1_ATOMS, FIT_S1_EVENT_TWIN, FIT_S1_LINK_PERMUTE}
  -> EVAL_S1_AUTH[progression] + EVAL_S1_CONTROLS[diagnostic]
  -> CANARY_S1_AUTH
  -> RESTORE_IMMUTABLE_PRE_EVAL_S1_AUTH
  -> REACHOUT_PRIMARY_NATIVE[one action]
  -> REACHOUT_NATIVE_PANEL[8]
  -> REACHOUT_SERVICE_PANEL_AND_CUTS[8 each condition]
  -> FORK_EXACT_PRE_OUTCOME_STATE
       |-> PUBLIC_R0 -> NEW_FORMATION_R0[1 EVENT + 2 LINK]
       `-> PUBLIC_R1 -> NEW_FORMATION_R1[1 EVENT + 2 LINK]
  -> MATERIALIZE_S2
  -> {FIT_S2_FULL_R0, FIT_S2_FULL_R1, FIT_S2_OLD_REPLAY}
  -> EVAL_S2_SERVICE_NATIVE_CUTS_CROSSMOUNTS
  -> CANARY_S2_FULL_R0 + CANARY_S2_FULL_R1

all launched/failed records
  -> QUARANTINE_CONTROLS
  -> FINALIZE_ONCE
  -> EXTERNAL_WHOLE_ROOT_CUSTODY
  -> REDUCE_ONCE
```

Only S1_AUTH progresses. Its pre-evaluation snapshot—not any evaluation fork—
is restored before reachout. Post-S1 native prompts contain no OLD receipt,
row, roster, ledger, service return, or compiler state. Both NEW branches start
from the exact same sealed native pre-outcome state and differ only in the
ordinary public R result. Every S2 fit starts from clean C0 and a fresh optimizer
over the cumulative OLD+NEW or OLD-only corpus; no S1 weights are warm-started.

A root stops at its first progression failure. Safe sibling roots and already
launched diagnostics may finish. No later outcome is revealed to a stopped
root, and no failed root is replaced.

## 7. Named test ledger with exact denominators

### 7.1 `tests/test_pcfl_vertical_dev.py`

| test | exact pass condition |
|---|---|
| `test_cube_has_32_worlds_and_64_delayed_tasks` | 4 excluded roots × 8 cells = 32; ×2 goals = 64 |
| `test_entropy_and_preoutcome_collisions_16_of_16` | all 16 `(root,O,G)` quartets byte-collide; each contains 00/01/10/11 and exact `(1,1,1,0)` bits |
| `test_full_routes_and_old_new_cuts_64_of_64` | FULL unique success 64/64; OLD cut failure 64/64; NEW cut failure 64/64 |
| `test_old_only_collision_groups_32_of_32` | all 32 groups byte-identical across R with exactly two labels; no singleton |
| `test_new_only_collision_groups_32_of_32` | all 32 groups byte-identical across O with exactly two labels; no singleton |
| `test_native_prompt_groups_8_of_8` | 8 `(root,G)` groups each have 8 identical prompts and 4 commands at exactly 2/8 each |
| `test_atoms_link_audit_has_48_exact_decisions` | 16 old tasks × 3 projections = 48 recorded; EVENT-only expected 16/16 |
| `test_link_derivability_audit_has_32_instances` | 4 roots × 2 O × 4 links = 32, each with enumerated K; no future-selected authentic target |
| `test_candidate_free_parser_executor_has_192_decisions` | oracle 64/64 succeeds; OLD-cut 64/64 fails; NEW-cut 64/64 fails; zero retry/intermediate return |
| `test_projection_report_covers_every_64_occurrences` | every named singleton and pair covers 64/64, min support>=2, min labels>=2, zero deterministic keys/decoded occurrences; frozen Bayes accuracy present |
| `test_independent_oracles_agree_exhaustively` | agreement on all 64 routes, 128 cut results, all collision memberships and 16 entropy quartets |
| `test_event_grammar_and_child_span_custody` | exact spaces/LF only; corrupt each field/receipt/order/span fails without repair |
| `test_link_grammar_and_child_span_custody` | exact fields/endpoints/two evidence IDs; corrupt each fails without repair |
| `test_old_formation_denominators_per_root` | accepted exact EVENT 8/8, LINK 4/4, LINK precision>=.80 over all attempts; rejected attempts retained |
| `test_new_formation_denominators_per_branch` | each R branch EVENT 1/1 and LINK 2/2; no OLD textual input; reproduced OLD IDs trace to child output |
| `test_post_s1_visibility_is_sterile` | zero OLD receipt/row/roster/ledger/service/compiler bytes in every native continuation prompt |
| `test_mechanistic_fork_cannot_enter_lineage` | all attempted fork/control ancestry rejected |
| `test_query_materializer_exact_counts` | exact 17+3,14+6,19+1,17+3 rosters and 20 slots each |
| `test_query_materializer_multirow_bytes` | five registered two-row cases, sorted IDs, exactly one joining LF, retained final LF |
| `test_controls_never_train_treatment_miss` | ATOMS LINK and OLD_REPLAY NEW addresses absent from targets; zero trained `MISS` in every arm |
| `test_pad_namespace_is_parser_disjoint` | all PAD targets rejected by EVENT/LINK/read/route parsers and contain zero world identifiers |
| `test_route_parser_is_one_shot_strict` | prefixes, suffixes, multiple ROUTEs, illegal port, wrong endpoints all rejected separately |
| `test_reducer_orders_failure_labels_1_through_16` | synthetic failure at every stage returns first applicable Section 13 label; branch label cannot rescue |

### 7.2 `tests/test_train_adapter_v3.py`

| test | exact pass condition |
|---|---|
| `test_explicit_adamw_contract` | defaults receipt equals beta(.9,.999), eps1e-8, wd.01 and configured lr3e-5 |
| `test_global_grad_clip_one` | pre/post norms recorded; every finite post norm<=1.0; clip occurs before `step` |
| `test_strict_trace_is_observational` | enabling receipt trace leaves final tensors byte-identical under same seed |
| `test_nonfinite_batch_fails_strict_fit` | no skipped batch can produce DONE/accepted fit |
| `test_exact_200_update_tiny_fit` | 160 singleton items ×5 epochs / batch4 = exactly 200 finite steps and five complete orders |

### 7.3 `tests/test_astra_pcfl_vertical_dev.py`

| test | exact pass condition |
|---|---|
| `test_real_template_target_and_eos_mask` | wrappers/metadata all IGNORE; exact response+EOS active; zero target truncation; every sequence<512 |
| `test_each_arm_has_20_slots_160_singletons` | all seven arm shapes/root encode to 20 slots, 160 nonempty physical sequences; packing off |
| `test_stage_target_tokens_are_exactly_equal` | S1 four arms equal and S2 three arms equal after tokenizer; only PAD absorbs deficits |
| `test_zero_fit_delayed_inventory_is_640` | 10 declared conditions ×64 tasks; no candidate arrays; each useful/cut control scored at its table gate |
| `test_zero_fit_reachout_inventory_is_160` | 5 conditions ×32 tasks; useful>=30/32; none/wrong<=18/32; each position 16/32 |
| `test_s1_local_read_panels` | EVENT semantic>=15/16 and strict>=14/16; arm semantic spread<=1/16; eligible LINK semantic+strict>=7/8 |
| `test_s1_absence_panels` | ATOMS LINK calls yield 0 usable false rows; 8 unseen+8 wrong-root give >=15/16 refusal and 0/16 false rows |
| `test_s1_service_and_native_routes` | AUTH service>=14/16 (>=7/8 each goal); native>=14/16, legal>=15/16; ATOMS scored same budgets |
| `test_s1_source_binding_and_goal_swap` | TWIN donor route>=12/16 and authentic score >=4/16 below AUTH; 8/8 goals change route; trace diverges by second sensitive read>=7/8 |
| `test_s1_critical_cut` | replacing critical authentic local result with MISS lowers service success>=6/16 |
| `test_reachout_primary_and_panels` | primary relevant 1/1; AUTH native>=7/8 and service>=7/8; cut/OFF/wrong-root each<=4/8 and AUTH gap>=3/8 |
| `test_new_rows_and_retention` | each FULL has NEW semantic>=5/6 with EVENT+LINK represented; every critical OLD read and OLD route within1/16 of S1_AUTH |
| `test_s2_full_service_and_native` | each FULL service>=14/16 legal>=15/16; native>=14/16 legal>=15/16 |
| `test_s2_old_replay_and_crossmount` | pooled FULL-OLD_REPLAY>=8/32; OLD_REPLAY<=20/32; donor redirect each>=12/16, pooled>=24/32 |
| `test_s2_old_and_new_service_cuts` | each cut reduces success>=6/16 for each FULL arm |
| `test_s2_off_wrongroot_controls` | every registered service/native OFF and wrong-root cell<=2/16 and zero usable false memory rows |
| `test_canary_and_rollback_40_items` | authentic candidate legal>=38/40, delta from C0 no worse than -2/40, no collapse/dialect substitution; failure restores exact parent but root remains failed |
| `test_dag_has_exactly_14_fits_and_2800_updates` | 2×(4 S1+3 S2)=14; every fit 200; profile fits included, never extra |
| `test_resource_ledger_enforces_7_plus_10_hours` | training device time<=7 A40h; other native device time<=10 A40h; total<=17; actual GPU product reported |
| `test_no_retry_resume_or_replacement` | failed/missing/timeout stage never reruns; no new root; invalid output stays in denominator |
| `test_control_and_branch_quarantine` | only restored S1_AUTH advances; no control/eval/noncanonical branch becomes authentic parent |
| `test_terminal_seal_custody_and_replay` | extra/missing/symlink/hardlink/tamper rejected; one terminal witness; external whole-root hash; deterministic single reduction |

The scripted-backend suite must additionally inject failure at every DAG edge,
wrong adapter mounts, prompt taint, EOS/truncation, timeout/orphan process, GPU
occupancy, and budget exhaustion. These are integrity tests, not new scientific
cells.

## 8. Runtime gate ledger

The reducer implements these noncompensatory checkpoints in order:

1. CPU audit exact -> otherwise `VS_ASSAY_INVALID`.
2. Required zero-fit delayed/reachout ceilings ->
   `VS_ASSAY_INVALID_MODEL_CEILING`.
3. any aggregate/per-fit cap -> `VS_RESOURCE_CAP`.
4. OLD exact 8 EVENT +4 LINK and precision ->
   `VS_CHILD_OLD_FORMATION_FAIL`.
5. S1 carrier/source/traversal/native gates -> ordered labels 5–9.
6. native primary plus native/service/cut/OFF/wrong-root reachout ->
   `VS_REACHOUT_FAIL`; do not reveal R on failure.
7. both R continuations exact 1 EVENT +2 LINK ->
   `VS_CHILD_NEW_FORMATION_FAIL`.
8. S2 NEW carriage, OLD retention, joint use, native endpoint -> ordered labels
   12–15.
9. custody/canary/nonreportable -> `VS_UNSAFE_OR_NONREPORTABLE`.

`LINK_ORGANIZATION_ADDED_VALUE` is endpoint-specific and requires
`AUTH-ATOMS>=4/16` at that endpoint. Otherwise use
`EVENT_COMPOSITION_ONLY`. `LINK_PERMUTE>=12/16` donor redirection may support
false-pointer influence; failure is only `LINK_DERANGEMENT_IGNORED`.

## 9. Pre-source questions not resolved by the passed documents

These are implementation inputs, not invitations to alter the assay. They must
be fixed and hash-bound before source/model output exists. The controlling
documents do not supply their exact bytes or algorithms:

1. The eight neutral wrapper strings and their ordering.
2. The global task, READ, EVENT/LINK commitment, and native ROUTE prompt bytes.
3. The deterministic `LINK_PERMUTE` derangement mapping.
4. The PAD request/target bytes and fixed feasible token reserve.
5. The forty generic canary items and common-random seed list.
6. The two balanced reachout surface/order renders and the one primary render.
7. The exact opaque-ID inventory/search seed and token-equality acceptance
   function.
8. Exact DEV/excluded/disposable root seeds, fit/dropout/shuffle seeds, and GPU
   UUID schedule.
9. The complete native request inventory and profiled per-request bound needed
   to prove the 10-hour worst-case cap before native launch.
10. Whether the current physical GPUs are A40s; A100 use must be recorded as
    A100-hours and cannot silently satisfy an A40-labelled receipt.

Do not resolve any item using DEV outputs, an oracle route, a future goal, a
hidden bit, or favorable model behavior. If token-equal materialization is
infeasible after these bytes are frozen, stop `VS_ASSAY_INVALID`; do not add a
fallback. Once these preparation bytes are registered, the implementation has
no remaining scientific discretion.

## 10. Definition of implementation-ready

Source/model execution may start only when the implementation produces durable
evidence for all seven checks below:

1. two CPU oracles agree on all routes/cuts/collisions/entropy;
2. projection audit has no forbidden deterministic key;
3. real-tokenizer corpora exactly realize 17+3 / 14+6 / 19+1 / 17+3,
   20×8 items, equal stage target tokens, no trained MISS, and no truncation;
4. trainer receipt proves the exact optimizer, clipping, and 200 updates;
5. predeclared request/device ledger fits 7+10 aggregate GPU-hour caps;
6. Linux CPU suite and all source/model/tokenizer/environment pins are sealed;
7. custody tests prove sterile post-S1 lineage, fork/control quarantine, no
   retry/replacement, terminal witness, whole-root custody, and one reduction.

After that, the native order is fixed: excluded-root zero-fit ceilings,
disposable formation root, then the two-root fourteen-fit DEV. Q0, parenting,
compression, rank sweeps, and unrelated diagnostics are not dependencies.
