# PCFL v2.2: shortest implementation bridge to zero-fit execution

**Date:** 2026-09-13 UTC  
**Role:** fresh engineering handoff audit  
**Scope:** repository inspection only; no `organism_v6/`, `gpu/`, or test edit,
model/tokenizer call, fit, adapter, or GPU execution  
**Inspected cut:** `9577b8d075ab`

## Verdict

The shortest bridge is **not** a fresh implementation. Promote the existing
partial PCFL route fixture into a production pure core, add the one v2.2
contract materializer/validator, and fork only the lifecycle shell of the L2
runtime for the zero-fit stages.

All seven named production paths remain absent:

```text
organism_v6/pcfl_vertical_dev.py
organism_v6/pcfl_vertical_prepare.py
organism_v6/pcfl_vertical_train.py
gpu/astra_pcfl_vertical_dev.py
tests/test_pcfl_vertical_dev.py
tests/test_pcfl_vertical_prepare.py
tests/test_astra_pcfl_vertical_dev.py
```

However, the repository already contains:

- a 494-line partial PCFL CPU core with two route oracles and a 20-test suite;
- exact prospective prompt, seed, placement, and work bindings;
- mature raw-capture, process-isolation, seal, custody, and replay code; and
- response-only LoRA encoding/training machinery for the later fitted stages.

The real work is integrating those pieces under the v2.2 precedence rules.
Parenting is not a dependency.

## 1. Exact reuse map

### 1.1 Promote the partial PCFL core

Source:
`research_notes/astra_memos/receipts_20260912/astra_pcfl_world_core_20260913.py`
at `bac33dc3...580e`; tests at
`test_astra_pcfl_world_core_20260913.py`, `15fdf91e...1df4`.

Promote these algorithms/types into `organism_v6/pcfl_vertical_dev.py`:

```text
FixtureRoot, Edge, PrivateCell
build_fixture_root, validate_inventory, expand_cube, validate_cell
task_fields, format_route, parse_route
oracle_route_v1, oracle_routes_v2, score_route, RouteSession
execute_action, check_receipt
structural_projection
entropy, mutual_information, entropy_v2
shortcut_report, audit_structural_fixtures
```

This already proves the eight-cell `(O,R,D)` cube, unique full routes,
OLD/NEW cuts, one-shot execution, collision groups, exact entropy, independent
oracle agreement, and singleton shortcut rejection. It should be copied into
the production PCFL namespace, not imported from `research_notes/`; the
artifact deliberately hard-codes fixture-only IDs and a VM repository path.

### 1.2 Reuse narrow stable infrastructure

| need | exact existing source | reuse |
|---|---|---|
| closed typed JSON wire | `organism_v6/l2_public_record_dev.py`: `_pack`, `_unpack`, `to_data`, `from_data` | transplant with PCFL-only allowlisted types |
| immutable public receipt chain | same file: `make_receipt`, `_check_receipt`, `_link`, `_episode`, `_block` | transplant shape; replace binary-action fields with route EVENT fields |
| exact child-span/no-repair custody | `organism_v6/endogenous_action_relay.py`: `parse_action`, `admit_block`, `check_formation`, `build_replay` | reuse span/hash and failure-inclusive admission pattern, not compiler-pass grammar |
| canonical hashes and deterministic order | `organism_v6/multikey_writer_gateway_simple.py`: `canonical`, `digest`, `exact_keys`, `seeded_order` | copy the tiny primitives locally; do not import the whole W0 assay |
| offline tokenizer/model pinning | same file: `snapshot_inventory`, `environment_identity`, `load_local_tokenizer`, `pin_local_inputs`, `real_preflight`, `validate_prepared` | adapt for the PCFL contract and exact renderer registry |
| strict generation receipt | `organism_v6/semantic_carrier_diagnostic.py`: `strict_output`, `check_generation`, `run_bounded_worker` | reuse structure only; candidate scoring is forbidden |
| write-once lifecycle | `gpu/astra_l2_public_record_dev.py`: `encoded`, `read`, `write`, `plain_path`, `tree`, `checked_file`, `offline`, `budget`, `release_budget` | fork nearly verbatim |
| prepared/stage custody | same file: `prepare`, `verify`, `stage_dir`, `read_stage`, `worker`, `run_stage`, `finalize`, `custody`, `collect` | fork the shell; replace the L2 state machine and all constants |
| native generation | same file: `Native.generate`, `validate_response` | adapt to PCFL prompts, seeds, token limits, and optional local-reader routing |
| later trainer encoding | `organism_v6/train_adapter_v3.py`: `normalize_items`, `encode_item_segments`, `pack_by_group(..., pack=False)`, `collate`, `lora_config` | direct reuse after zero-fit closure |
| later numerical receipts | `gpu/astra_pairwise_q0_fulldose.py`: `tensor_hash`, `rng_receipt`, `tree_state`, `state_receipt`, `ordered_inventory` | transplant only when closing fits |

Current reusable source hashes are:

```text
0bb33988...  organism_v6/l2_public_record_dev.py
dce8cd88...  gpu/astra_l2_public_record_dev.py
7bbf165f...  organism_v6/train_adapter_v3.py
b7e48914...  organism_v6/endogenous_action_relay.py
b9fd33c7...  organism_v6/multikey_writer_gateway_simple.py
a05da09e...  organism_v6/semantic_carrier_diagnostic.py
f63c77f9...  gpu/astra_pairwise_q0_fulldose.py
```

L2 and Q0 remain separate frozen experiments. Reuse their functions or copy
their patterns; do not add PCFL branches to their source files.

## 2. Exact missing production surface

### `organism_v6/pcfl_vertical_dev.py`

Keep the promoted route algebra, then add only the scientific middle that does
not exist:

```text
OpaqueInventory, RootManifest, WorldCell, TaskRender
PublicReceipt, ChildGeneration, ChildSpan, Admission
EventRow, LinkRow, MemoryQuery, ResponseBlock, RouteScore

validate_opaque_inventory
build_root / expand_cube / render_task
audit_construct
parse_explore / parse_probe / parse_read / parse_route
parse_event_line / parse_link_line
admit_event / admit_link / formation_report
materialize_queries
make_event_twin / make_link_permute
score_memory_response / score_route_generation
reduce_run
```

The zero-fit path needs the world, exact ten projection renderers, the
deterministic text-memory service, route/probe parsers, cuts, scorers, and
reducer. EVENT/LINK child admission is needed before the disposable formation
stage, not to obtain the first zero-fit ceiling, but it belongs in this core so
the contract does not later change types.

### `organism_v6/pcfl_vertical_prepare.py`

This file is the single authority consumed by every later runtime stage:

```text
build_source_registry
build_render_registry
build_parser_registry
build_root_registry
build_slot_and_counterpart_registries
select_replays
solve_joint_batches
build_cut_registry
build_locality_registry
build_diagnostic_registry
build_calibration_state_machine
expand_work_registry
materialize_execution_contract
validate_execution_contract
seal_execution_contract
```

It must produce only:

```text
<run_root>/PREPARE/execution_contract.json
<run_root>/PREPARE/execution_contract.sha256
<run_root>/PREPARE/validation_report.json
```

The contract must be complete for both LOW-only and HIGH-used branches before
the first zero-fit model generation. Zero-fit cannot use a smaller contract
that is later mutated for S1/S2.

### `gpu/astra_pcfl_vertical_dev.py`

Fork the L2 lifecycle shell and implement the minimum zero-fit stage table:

```text
validate_spec / prepare / verify
TextMemoryService.lookup
PCFLActor.run_service_loop
run_native_actor / run_reachout
run_zero_fit_delayed / run_zero_fit_reachout
worker / run_stage / execute_zero_fit
finalize / custody / collect
```

The prepared work rows must give exactly `640` delayed and `160` reachout
tasks: `704` single-call actor tasks and `96` service-loop tasks, plus the
globally reused `40`-item C0 canary. A service actor gets at most 12 reads,
4,096 returned-memory tokens, 2,048 actor tokens, one ROUTE, no intermediate
route feedback, and no retry.

### Tests

`tests/test_pcfl_vertical_dev.py` should begin by promoting the 20 partial-core
tests, then close exact PCFL IDs, D/probe behavior, all projections,
EVENT/LINK parsing, cuts, and the 48/192 decision audits.

`tests/test_pcfl_vertical_prepare.py` should implement the closure memo's 13
fail-closed families: source/sidecar/schema, v2.1-field rejection, render and
parser snapshots, diagnostic candidates, skeleton purity, counterpart/replay,
support-overlap batches, CAL truth table, cuts/locality, both work branches,
and device-time arithmetic.

`tests/test_astra_pcfl_vertical_dev.py` should first use scripted backends to
prove the 800-task zero-fit inventory, candidate-free service isolation,
one-shot routing, common-random pairing, timeout/cleanup, tamper rejection,
and deterministic single reduction. Trainer/DAG tests can follow without
changing the already-sealed core/contract schemas.

## 3. Dependency order

```text
promote partial route algebra
  -> replace fixture ID/probe gaps and pass pure construct tests
  -> instantiate all static v2.2 registries
  -> solve replay/batch/cut/work tables on structural placeholders
  -> offline tokenizer-bind IDs and exact rendered bytes
  -> validate and seal one complete execution_contract.json
  -> scripted zero-fit runtime/replay tests
  -> native zero-fit excluded-root ceilings
  -> only then trainer closure + disposable formation/CAL + DEV
```

Do not patch the trainer before the zero-fit core, preparer, and scripted
runtime are green. Trainer work cannot repair a broken construct or ceiling.

## 4. Integration hazards most likely to waste the day

1. **v2.1/v2.2 precedence.** The prospective register and build ledger still
   contain loss-active `PAD_*`, `equal_target_tokens`, generic shuffling,
   14-fit arithmetic, and a 17-hour cap. V2.2 forbids those. The validator must
   reject the obsolete fields rather than ignoring them. Ordinary post-EOS
   tensor padding remains legal only with attention 0 and label `-100`.
2. **Fixture identifiers are not scientific identifiers.** The partial core
   uses lowercase 24-hex IDs and a regex tied to them. The actual preparer uses
   the fixed uppercase base32 namespace search (`N_`, `P_`, `E_`, `L_`, `Q_`,
   `R_`, `G_`) under the pinned tokenizer. Replace the regex and allocator
   together; do not merely rename `FixtureRoot`.
3. **The partial fixture does not implement the distractor.** Its `D` bit does
   not change edges or model-visible probe outcomes. The production core must
   bind the isolated matched distractor frontier, both RA/RB renders, outcome
   frequencies, and affordance order before its shortcut report is complete.
4. **Support collision is row-level.** `READ EVENT e0` and
   `READ EVENTS_AT S_L` overlap through support `e0` even though their block
   hashes differ. The batch solver must compare support-span sets.
5. **Exact semantic bytes cannot be reconstructed.** Query blocks join exact
   admitted child spans in registered order. Rendering a fresh EVENT from
   parsed fields breaks authorship even if the text is byte-identical.
6. **L2 constants are wrong for PCFL.** L2 uses temperature 0, 32 output
   tokens, one serial GPU, binary actions, and one fixed adapter route. PCFL
   uses temperature .7, common-random seeds, much larger stage-specific caps,
   eight shards, three READ methods, and no candidate ranking.
7. **Semantic and strict parsers are different endpoints.** The semantic
   diagnostic may accept the one registered fence case; strict exactness may
   not. Extra prose, duplicate/extra rows, or any usable false row must remain
   visible and cannot be converted to `MISS`.
8. **Hard-coded VM path in the archived tests.** `construct_gate()` defaults
   to `/data/home/rohing/dream-state`; it fails locally before running tests.
   Production tests must receive the actual pinned snapshot root explicitly.
9. **The contract cannot grow after zero-fit.** Replay schedules, 15/16-fit
   branches, 960/1,024 added retention calls, W8/forward-score diagnostics,
   cold loads, and CAL_HIGH truth table must already exist in the sealed
   contract even though zero-fit executes first.
10. **Do not accidentally import candidate scoring.** Only ordinary
    generation is permitted for the local memory worker. The
    `candidate_choice`/logprob selection paths in semantic-carrier code are
    explicitly out of bounds.

## 5. Builder's first 1--2 hours

This is an Astra-speed critical slice, not a claim that the full native
campaign can be hand-built in two hours.

1. **0--20 min — establish production core.** Copy the partial fixture and its
   tests into the three named production paths; remove the hard-coded source
   root; replace fixture-only type names and ID regexes; preserve the existing
   golden route/oracle/cut tests.
2. **20--50 min — close pure assay semantics.** Add the actual opaque-ID type,
   relevant/distractor probe frontier, exact public/private projections,
   strict ROUTE/READ/PROBE parsers, independent construct audit, and literal
   renderer/parser constants from the pinned binding register and closure.
3. **50--80 min — build the contract.** Materialize root skeletons,
   counterpart/replay maps, support sets, five schedules, cuts, addresses,
   CAL truth table, and both complete work branches. Emit canonical contract,
   sidecar, and validation report; make every obsolete PAD/equality field a
   hard failure.
4. **80--105 min — fork the zero-fit runtime shell.** Bring over L2's
   write-once prepare/verify/stage/worker/seal/custody functions; add the
   deterministic text service and bounded one-shot actor; implement only the
   CPU/scripted zero-fit stage table first.
5. **105--120 min — prove the bridge.** Run the new pure/preparer/scripted
   tests. Require exact 64 delayed cells, 32 reachout cells, 800 task cells,
   96 service loops, 40 C0 canaries, no candidates, no hidden bytes, no retry,
   deterministic replay, and zero model/GPU use. Commit source only when this
   receipt is green.

If the full contract cannot be validated in that window, stop at the first
failing CPU invariant and keep the partial bridge. Do not create an incomplete
`execution_contract.json`, do not bypass the validator to run ceilings, and do
not divert into parenting or another proxy experiment.

## Handoff boundary

The zero-fit bridge is complete when the production core passes its exhaustive
construct tests, the complete v2.2 execution contract validates and seals, and
the scripted runtime deterministically replays all zero-fit work. That is the
only honest point at which native excluded-root ceilings may begin.

After those ceilings pass, the remaining critical implementation is already
localized: EVENT/LINK formation capture, the explicit-batch strict trainer,
CAL_LOW/HIGH, and the authentic/control DEV DAG. None requires another change
to the world or paper claim.
