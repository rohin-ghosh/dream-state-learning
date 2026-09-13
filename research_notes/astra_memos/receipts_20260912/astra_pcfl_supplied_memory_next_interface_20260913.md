# Smallest supplied-memory interface diagnostic

2026-09-13. Read-only recommendation; only this memo written. No code, tests, model/GPU calls, remote actions, commits, or fresh outcome inspection. Sources are the current local ladder and SEQ167 failure audit, not native artifacts. This work is separate from ongoing own-write and its analyzer.

## Decision

Implement a new scoped typed-turn driver around the existing **default NativeActor**, actual registered READ service and unchanged route scorer. Do not use the LF formation actor, post-hoc route extraction, ideal answer candidates, or a LoRA. First execute the ladder's A1/A2/A3 development prefix; only after a THINK-capable rung qualifies, execute ACTIVE with both READ and THINK. This is the smallest staged implementation that separately identifies the missing READ disclosure, direct traversal, and the missing thought channel. It avoids rebuilding the800-task assay or testing reachout before routing works.

The requested failure audit is `research_notes/analysis/2026-09-13_pcfl_c0_seq167_failure_cause_audit.md` (there is no file at the inferred `...c0_dev_failure_cause_audit.md` name). It reports all64 active delayed tasks received zero rows after illegal two-line `READ <START>` / `READ <GOAL>` requests. It also finds zero correct direct positive routes under permissive punctuation scoring, including genuinely disconnected exact-syntax routes. Thus this is not merely punctuation; neither is it evidence that a disclosed service plus a real THINK channel cannot work. SEQ167 remains an engineering-only failed-finalization capture, not a clean memory/writer negative and not a retrospective pass.

## Exact preregistered cases and finite sequence

Reuse the **preserved actual opaque root wires** for `excluded/0..3`, already exposed in SEQ167. Do not regenerate inventories, reselect salts or sample easier paths. Expand all eight O/R/D cells and both goals, giving64 cases per panel: `root × old × relevant × distractor × goal`. Retain existing task ordering and `core.seed('runtime-test/' + block)` for paired tasks; add a new interface/rung namespace to call IDs. Freeze the complete roster, initial prompts and every potential turn ID before generation. Do not open `dev/0`, `dev/1`, formation roots, or final/confirmation pools.

| Stage | Cases / maximum calls | Predeclared purpose and decision |
| --- | --- | --- |
| A1_READ_DISCLOSED |64 ACTIVE /832 (13 each)|Exact READ API and row semantics; no THINK. Require zero malformed/multiple READ outputs and at least60/64 tasks with a served registered read. Report route success, but do not use it as this handshake gate. Stop later stages on handshake failure. |
| A2_DIRECT |64 EXACT /64|Same world/semantics, supplied exact witnessed graph, no READ or THINK. Report syntax, connected path and graph success;60/64 is the ladder's answer-direct ceiling, not THINK-endpoint qualification. |
| A3_THINK |same64 EXACT /448 (7 each)|Require a THINK before ROUTE; maximum6 THINKs. Require at least60/64 tasks with exact THINK and at least60/64 exact graph successes; never accept mixed thought/action responses. A2 failure does not prevent A3. |
| Selected ACTIVE confirmation of interface composition, on exposed DEV data |64 ACTIVE /1216 (19 each)|After A3 passes, use the same typed interface with both READ and THINK. This is the ladder's later ACTIVE development panel, not an additional invented control. Require60/64 exact routes,60/64 tasks with served reads, zero invalid reads and exact source joins. Report THINK counts as well. |

Initial A1/A2/A3 maximum:192 tasks,1344 physical calls. Adding selected ACTIVE after A3 pass:256 tasks,2560 physical calls. These are maxima, not required usage or new independent worlds. Use one fresh actor/process per stage, each within the native actor's existing1952-call maximum; do not put2560 calls into one actor config or relax that bound. Tasks within a stage start with fresh message histories, not the previous task's scratchpad. Zero fits/updates/adapters/parents.

If A3 fails, preserve failure and stop this first vertical slice. The ladder already describes A4, a generic traversal algorithm and optional neutral example, as its only conditional escalation; do not silently add that text to A3. Main can bind its exact bytes prospectively as a later rung (64 tasks/448 calls, same THINK gate). If A4 is selected, label every later panel as execution **under a supplied traversal procedure**. No best-of sampling or retry. The above positive panels alone do not qualify the full ladder: negative controls, remaining memory representations, reachout repair and fresh outcome-blind confirmation remain deferred requirements, not waived gates.

## Public interface and transition contract

Take the row-semantics text from the ladder unchanged. State that EDGE/EVENT are directed transitions, and LINK joins two recorded transitions without changing them. In ACTIVE only, disclose:

```text
READ EVENT <event_id>
READ EVENTS_AT <node_id>
READ LINKS_FROM <event_id>
```

Explain that these respectively return the matching EVENT, all EVENTs with that AT/source node, or all LINKs with that first event; a miss returns exactly `MISS`. One request per response. Do not enumerate registered addresses or useful queries, show a worked path with scored IDs, identify a first hop or path length, or disclose a hidden graph/answer. The grammar metavariables are not answer candidates.

THINK-capable stages permit `THINK <one nonempty physical line>`; proposal for the new protocol parser is fullmatch `THINK [^\r\n]+`, with no terminal LF. READ and ROUTE use the existing fullmatch parsers unmodified. Reject unknown commands, multiple physical lines, fences, surrounding prose and mixed final/thought output. Treat a THINK body as opaque child reasoning: text mentioning READ/ROUTE is not itself an executed command. Do not inspect or repair its reasoning. A valid THINK gets exactly this fixed two-line user message from the ladder, with no additional world text:

```text
CONTINUE: think again, issue one permitted READ if reads are enabled, or
commit the final action.
```

Append the exact assistant THINK before that constant. A valid READ instead gets only the actual `core.read_query` return. Do not append hints, acknowledgments about correctness, or the pending goal again. A ROUTE is terminal with no feedback: send the **entire raw ROUTE response**, unchanged, to `core.score_route`; never search a scratchpad for a last line. A3 must reject a terminal response before the required THINK rather than ask again. A malformed child response fails that task and preserves unused slots; it need not abort all other tasks. Backend, source or lifecycle failures stop the stage and preserve uncalled tasks.

Use ladder limits: at most256 generated tokens per turn,2048 cumulative actor tokens,4096 returned-memory tokens,12 READs,6 THINKs; active maximum19 generations, non-read maximum7. A1 permits13 with no THINK; A2 permits1. Give each call `max_tokens=min(256,2048-actual_actor_tokens)`. Count READs separately from THINKs; no extra final call after exhaustion. A final action using the last allowed tokens is eligible only with actual stop completion; `length` is failure even if the text happens to parse. Retained thought/history increases input length: measure every actual full chat prefix and fail on the unchanged context cap, never truncate or summarize it.

## Existing code that already works; exact missing scope

**World/service/scoring — reuse unchanged.** `organism_v6/pcfl_vertical_dev.py`: `expand_cube`, `render_task`, `materialize_queries`, `parse_read`, `read_query`, `parse_route`, `execute_route`, `score_route`. `read_query` checks the exact block hash, operation/address, order/support and returns raw bytes/source hashes or MISS. Count a served registered read separately from a syntactically valid MISS. The supplied rows originate from `ideal_rows` in this ceiling planner: preserve `RESEARCHER_AUTHORED_EXCLUDED_ROOT_CEILING_NOT_CHILD` and `CEILING_SERVICE_ONLY` provenance. They must never become authentic child formations, writer targets, parent data or memory-repair material.

**Case enumeration — reuse without treating it as native authorization.** `gpu/astra_pcfl_vertical_dev.py:62`, `prepare_scripted_plan`, deterministically defines all current800 cases and query tables. A new preparer can call it for the supplied wires and select only the exact delayed ACTIVE/EXACT panels specified above, with assertions for64 unique case keys each. It must build its own native manifest: the helper explicitly identifies its result as scripted-only. `gpu/astra_pcfl_zero_fit_dev.py:51`, `build_tasks`, is not directly reusable as the new native plan because it asserts800 tasks/1952 slots and the old continuation.

**Actor — reuse default unchanged.** `gpu/astra_pcfl_native_actor.py`, `NativeActor.generate`, already binds exact public request, rendered prompt/token IDs, sampling, raw text/output IDs/finish/stop, timings and source/environment/model identity; `count_tokens` verifies actual memory-return cost. Use that default actor, not `LFNativeActor`. The public response dictionary lacks finish_reason: the new driver must join the corresponding immutable `.raw.json` sidecar to its request/hash and consume the actual finish reason; it must not infer stop from parseability. No actor API enlargement is required.

**Missing driver — one new scoped module plus tests is sufficient initially.** Proposed `gpu/astra_pcfl_supplied_memory_dev.py` and `tests/test_astra_pcfl_supplied_memory_dev.py`: implement pure build/typed-dispatch/replay functions and minimal `measure`, `prepare`, `run` CLI entry points in that module. This is proposed code, not an existing executable. Reuse the actual-tokenizer `_render` pattern and source checks from the zero-fit driver, but use a new schema, explicit roster/rung limits, neutral continuation, and strict task-local state machine. Do not subclass the old `_task` unchanged: it breaks on every non-READ response and uses physical turn number as reads consumed. Do not import the old collector or mutate its globals to pretend800 tasks ran.

**Token preparation.** Reuse model/tokenizer/14-file binding and actual L8 opaque inventories. Measure all new initial prompts, exact READ API/CONTINUE constants and possible registered service blocks using actual encode/template equality. Actual THINK text is unknowable pre-output; do not invent exhaustive continuation measurements. Each generated history must instead be rendered, measured and archived before the next call; output/returned/history limits fail closed. Initial/continuation source exposure checks must ensure query tables and private task data remain outside generation requests.

**Lifecycle — reuse functions, not hard-coded old entry points.** `gpu/astra_pcfl_zero_fit_outer.py` already supplies `identity`, `group_members`, `cleanup_owned`, `check_node`, `check_queue`, `check_cvd`, and `check_gpu`. Its `_inputs`, `_report` and `finalize` are tied to the old command/schema and800-task inventory, so a small new Main-owned command/report binding is required; do not weaken those checks in place. Likewise the existing own-write outer has formation/fit/readout-specific stages, not a ready route CLI. Reuse its bounded stage pattern and explicit installed shutdown discipline without importing a fit path or editing ongoing own-write files. Bind the installed `llm.llm_engine.engine_core.shutdown` source/method and record shutdown before actor.close; old default close alone is not a verified engine/group release.

Set a finite prospective per-stage controller cap (Main allocation decision;3600s plus a separately bounded180s collection is a reasonable initial ceiling, not an adopted protocol here), with at most120s cleanup inside the controller cap and lease margin. Begin timing at controller entry so tokenizer/model cold load, validation and cleanup are included. Only owned PID/startticks/boot/PGID cleanup; finalization requires group gone, GPU compute vacant and all holder/CVD reservations released or honestly reported. Preserve raw query evidence separately from the exact release attestation, crosslink hashes, and perform one local replay/reduction after release. A scientific task failure can coexist with a valid completed stage; a release/custody failure cannot be called usable evidence. No retry/recollection.

## Minimal CPU acceptance before Main execution

1. Exact64-case factorial per rung, preserved root wires/IDs/rows/seeds, stable seals and source hashes; A2/A3 identical supplied memory and goals. No output-dependent selection. Direct/read/THINK service permissions are explicit per rung.
2. Disclosed three-command API matches real `parse_read`/`read_query`; exercise each family against an actual registered block and a MISS. Hash/source/order checks reject tampered service blocks. No address enumeration in prompts.
3. Scripted `THINK → READ → THINK → ROUTE` traverses the new driver and real scorer; every prefix is exact. The only feedback after THINK is the fixed constant; only READ returns memory. Multiple READ lines, thought plus a newline-final answer, fences, altered IDs, or extra final bytes fail without salvage. Wrong but syntactically exact paths fail the original graph scorer.
4. Independent THINK/READ counters,256/2048/4096 token limits,7/13/19 call maxima, stop versus length, no final retry, no task-to-task history leakage, and unused/malformed slots retained. Token counts come from the injected actor/tokenizer seam, not guessed lengths. No signal of graph correctness returns to the actor.
5. Replay joins every request/render/raw response/service source and reproduces transitions and scoring; disagreement is failure, not repair. Mock lifecycle tests cover cold-load-inclusive timeout, owned-only cleanup, holder reservation release, final attestation/hash and preserved failures. Existing native actor and unchanged scorer tests remain regressions; do not run training or own-write tests as part of this sidecar.

## Frozen sources inspected

| Source | SHA256 |
| --- | --- |
| `research_notes/analysis/2026-09-13_pcfl_c0_dev_interface_repair_ladder.md` | `85e2cec3cb0c5f1a38d08171b201078b733eb7743735209c3a222e8932f6a6e2` |
| `research_notes/analysis/2026-09-13_pcfl_c0_seq167_failure_cause_audit.md` | `5ecd35965964c4a216a6981f6c49f26782a2bb7061df2c7ebcc6076d81dcd95a` |
| `gpu/astra_pcfl_zero_fit_dev.py` | `7bcc99f89b661f2f77202c3cc5aa61533bad2daff25f5b548ed8e1ecd1c1b5d5` |
| `gpu/astra_pcfl_vertical_dev.py` | `026c6a8c50f551d874a605e1975f5fe2189643fcbd5e6694c0ad2d2fea0544b1` |
| `organism_v6/pcfl_vertical_dev.py` | `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e` |
| `gpu/astra_pcfl_native_actor.py` | `915b27d4dfe51623535bae588e54e1e35654a956f164aa23eba74a925a4a23ff` |
| `gpu/astra_pcfl_zero_fit_command.py` | `172f49a4a104f63920c5a7d139b793954706cf221604792fbeced20ef151d169` |
| `gpu/astra_pcfl_zero_fit_outer.py` | `fdd29c64bc73b1602998e6509da9f6d3132b90f9a5d50dceb1ad20ce86128f19` |

Bottom line: the next mechanism is an explicit typed THINK/READ/ROUTE conversation, not extra decode allowance. Positive results on these exposed roots would be supplied-memory interface development only. Original failures, strict route truth, full qualification gates, future confirmation roots and authentic own-write provenance stay separate.
