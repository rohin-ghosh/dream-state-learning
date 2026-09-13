# EDITSTOP — supplied-memory typed-turn DEV core

2026-09-13. Only NEW `gpu/astra_pcfl_interface_dev.py`, NEW `tests/test_astra_pcfl_interface_dev.py`, and this handoff were written. Frozen core, default/LF actors, own-write, old drivers, analyzers and other workers' files were not edited. No CLI, remote/native/GPU/model actions, commits, training or release implementation.

## Callable interface

```python
from gpu import astra_pcfl_interface_dev as interface

roster = interface.build_roster(preserved_root_wires, "ACTIVE_THINK")
interface.validate_roster(roster, roster["sha256"])

# Main prepares the actor config and actual tokenizer separately.
# Add interface.source_pins() to actor_config['source_files'].
# Pass an unstarted, fresh default NativeActor; do not call start/count_tokens first.
report = interface.run_stage(
    roster, roster["sha256"], actor, tokenizer, stage_directory,
    actor_config=actor_config, deadline=absolute_monotonic_deadline,
)
replay = interface.replay_validate(roster, roster["sha256"], report, tokenizer)
```

`run_stage` optionally takes `receipt_reader=read_capture` and `clock=time.monotonic` for injection/testing. Main owns actor construction, installed shutdown, close, outer timing/timeout, GPU/resource release, source transfer and collection. This core never starts an actor explicitly, closes one, declares native custody, or launches another stage. Generation itself uses the existing actor's lazy start.

Additional exports: `SCHEMA`, finite `STAGES`, exact public `ROW_SEMANTICS`, `READ_API`, `THINK_API`, `CONTINUE`, `source_pins`, `read_capture`, and `summarize`. No native CLI is present.

## Fixed roster / provenance

Schema: `pcfl.supplied_memory_interface_dev.v1/roster`, sealed with `sha256` over its canonical body. Input must be the four preserved root wires in exact `excluded/0`, `excluded/1`, `excluded/2`, `excluded/3` order. The implementation calls `core.from_data`, `expand_cube`, `ideal_rows`, `materialize_queries`, and `render_task` on those wires. It does not call an allocator or choose new salts/root inventories. All64 cases are enumerated per stage: four roots × eight O/R/D cells × two goals. No narrower case selection parameter exists.

Seeds preserve `core.seed('runtime-test/' + root/O/R/D/goal)`. A2 and A3 have byte-identical supplied graph/goal user text, rows and seeds; the interface system text and prospective request IDs differ. All possible per-task slot IDs are fixed before any generation. Root provenance includes the canonical `roots_sha256`; Main must additionally pin the actual original root-file bytes in its preparation manifest (that file hash is not guessed from canonical JSON).

Roster fields include stage, exact preserved roots, source hashes, full task records, caps, continuation, material origin, zero fits/updates, and `full_assay_qualified=False`. Tasks contain private evaluator cell/goal and registered query/source rows separately from their public messages. Requests passed to the actor contain only id, messages, seed and C0 mount. Exact graph projection deliberately supplies existing witnessed edges; ACTIVE initially supplies only the existing task, not its registered query list or bank. Source rows are **RESEARCHER_AUTHORED_EXCLUDED_ROOT_CEILING_NOT_CHILD**, never actual child experience or eligible training material.

| Stage | READ cap | THINK cap | Slots/task | Stage possible calls |
| --- | ---: | ---: | ---: | ---: |
| A1_READ_DISCLOSED |12|0|13|832|
| A2_DIRECT |0|0|1|64|
| A3_THINK |0|6|7|448|
| ACTIVE_THINK |12|6|19|1216|

Each stage's actor config must cover its full possible calls (within the existing native1952 bound) and at least256 output tokens. Every call is actually limited to min(256,2048 minus prior actual actor tokens). Maximum4096 returned-memory tokens,14336 input tokens (or stricter actor cap), existing engine context limit, separate READ/THINK counters, and caller's finite deadline apply. No final call is added after budget exhaustion. A terminal action completing within the last allowed budget is eligible only with actual stop finish.

## Execution and raw receipt contract

THINK is an exact whole-response `THINK [^\r\n]+` match. Its raw text remains in history; only the fixed two-line `CONTINUE` is added. A THINK body is opaque reasoning, not an embedded executable command. Valid READs use unchanged `core.parse_read` and `core.read_query`; exact source-return bytes or MISS enter history. Multiple READ lines, unknown syntax, fences or thought/newline/action combinations fail without extraction. Direct stages reject THINK; non-read stages reject READ. THINK-capable stages require at least one THINK before a final ROUTE.

Final ROUTE is scored by unchanged `core.score_route` on the entire raw response. No field or path repair, output normalization, trailing-LF removal, feedback, retry or resumed partial response. Wrong-but-exact routes remain wrong. `finish_reason='length'` always fails the task, even if its raw text would parse. Per-task histories reset to their sealed initial two messages.

`read_capture(actor_directory, global_call_index)` preserves original sidecar UTF8 text plus byte SHA: config, identity, request, render, raw and response (including partial error sidecars on failure). `_verify` joins request/hash/limits, source/model/environment/C0 identity, exact unconstrained default sampling, actual chat rendering, token IDs/decode equality, raw hex/hash, finish/stop, and chronological timings. The actor's public response lacks finish_reason; it is taken only from the matched raw sidecar. Identity remains stable across the stage. No reuse of LF actor sampling is accepted.

Returned-memory token IDs are recorded using the supplied tokenizer, bound by path/template/probe and joined against native prompt/output token receipts. This core does not add actor.count_tokens calls. Main must supply the actual tokenizer whose files are in the actor config; the default actor performs the existing model/tokenizer/source identity verification. Continuation text cannot be pre-enumerated: every actual full history is rendered and bounded before generation, never truncated.

The fresh stage directory receives `roster.json`, `binding.json`, write-once request/attempt files and sealed `report.json`. Default NativeActor retains its independent original sidecars. The actor output directory must be fresh and distinct from the stage directory (it may be a child whose parent the stage creates). An existing stage/output is never reused. Host clock observations support deterministic replay, not hardware attestation.

Report schema is `pcfl.supplied_memory_interface_dev.v1/report`: exact actor config/deadline/timing, roster hash,64 result records, all attempted captures, every possible slot's RETURNED/ATTEMPTED/UNCALLED status, raw rejects, services/source hashes/token IDs/delivered status, counters, stage summary, and any stage error. Malformed child output fails that task without aborting unrelated tasks. Backend/custody failure aborts the stage and preserves current/uncalled tasks. A returned block exceeding4096 is recorded as undelivered; it never enters the public next prompt or delivered-token total.

Replay reconstructs the same driver transitions, message prefixes, limits, service rows/token counts and original route scoring using only archived attempts and clock observations. It verifies all results and attempt/clock counts against the sealed report. Preserved failure reports can replay as failures. It never means native execution/release is certified: `native_custody_verified=False`, `outer_release_required=True`, `full_assay_qualified=False` always.

## Gates and what remains Main-owned

Summaries retain64 denominators. A1 gates zero invalid READ tasks and at least60 served-read tasks, not route accuracy. A2 gates60 exact graph successes. A3 adds at least60 THINK tasks, with premature final actions ineligible. ACTIVE adds60 served-read tasks and zero invalid reads. All require an engineering-complete stage; a failed-custody report cannot pass. Gates are descriptive stage decisions, not automatic progression or whole-assay qualification.

Main's command must bind stage order/prerequisites, original root-file bytes, actual tokenizer preparation, source/environment/model pins, native actor config, deadlines and fresh output paths. No prerequisite receipts are inferred here; each callable stage is independent. Main also supplies installed engine shutdown and outer owned-process/release checks, immutable archive/collection, and any later A4/remaining panels/confirmation decisions. A4 is not implemented; unknown stages are rejected. No own-write targets, fit path, parenting or promotion decision is present.

SEQ167 remains immutable failed-finalization evidence. These are exposed-root prospective developmental interface results, not confirmation, memory acquisition, retention, LoRA qualification or a full-assay pass.

## CPU checks / exact hashes

```sh
PYTHONDONTWRITEBYTECODE=1 timeout 180 python3 -m unittest discover -s tests -p test_astra_pcfl_interface_dev.py -q
```

Final suite: **20 PASS,43.665s**. AST/trailing-whitespace: PASS for both owned files. Tests use synthetic fixture roots/emissions/tokenizers through the actual default NativeActor with an injected loader; no native model. The initial18-test suite also passed before adding cumulative/returned cap cases.

Coverage includes four fixed rosters, paired graph/seed identity, exact READ disclosure without query enumeration, bad root/plan rejection, THINK→READ→THINK→ROUTE with genuine service joins, all three READ families and MISS, history separation, raw malformed/length preservation, required/disabled THINK and READ, wrong routes,6/12/19 turn bounds,2048 actor and4096 returned caps,256 per-turn limits, input/deadline failure, no retries, source/capture drift, backend failure, and replay tampering. Synthetic padding tokenizers in two tests exercise exact budget boundaries; they are not actual model token measurements.

| File | SHA256 |
| --- | --- |
| `gpu/astra_pcfl_interface_dev.py` | `0cb07c0a02770ee8d9aeae0e105957eff1bff56042c4daf7ab7401a1ee3f68b3` |
| `tests/test_astra_pcfl_interface_dev.py` | `1298fe2ec390b0564407113d022f53a95871f2e5c6d7b2cdf8c78dc6c3c38b25` |

Read-only dependencies rehashed unchanged: default actor `915b27d4dfe51623535bae588e54e1e35654a956f164aa23eba74a925a4a23ff`; world/parser/scorer `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e`. `source_pins()` binds these two exact imported paths plus the new driver. Ownership is released to Main at EDITSTOP.
