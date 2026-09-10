# RML-G1 exact GPU-runner design after G1A

**Date:** 2026-09-04  
**Status:** advisory only; no implementation, ratification, model call, network
call, GPU process, sync, or remote job is authorized or performed by this
document.

## Decision

The minimal compliant execution path is a G1-specific remote coordinator plus
a fresh four-GPU vLLM subprocess for each trajectory. It must not send the
current `RmlActionMachine.model_visible_bytes()` directly to vLLM, must not use
the generic `remote_job.run_job()` retry behavior, and must not reuse the v03r
v2e resident engine across trajectories. The v03r v2e implementation is useful
for exact token-ID input, one-use logical sessions, raw provider receipts,
telemetry, offline-only model loading, disabled prefix caching, immutable
artifacts, and process-separated scoring; its engine lifetime is not G1
compliant.

Nothing may be implemented or launched until the G1A amendment is ratified and
its exact capacity/source-lineage repair is implemented and reviewed. The
currently binding and pending bytes are:

- ratified G1 consensus SHA-256
  `1c27cbe6ac3adda14078f2cdbfe62785ce7161b4ae35c2fb96b899b40da53cb9`;
- ratified G1 ratification SHA-256
  `fa6dd830a67ba03dd336945e74759ae58ce075de201573c4037798cba2e4ab53`;
- pending G1A consensus SHA-256
  `e39f8cd52cfbb318a2eb189b6f95fdeb61f7200bc3c2c288339090e7fa807e07`.

The G1A intake currently says `phase: human_required`,
`implementation_authorized: false`. A later ratification must bind exactly that
consensus (or a newly adjudicated successor); the original broad G1 approval
cannot be used to infer approval of the repair.

## Frozen scientific shape

The runner registers, before the canary, the existing `build_roster()` order:

```text
ordinal  0..3   GOLD_REC     J_H, J_TWIN, P_H, P_TWIN
ordinal  4..7   NONE_REC     J_H, J_TWIN, P_H, P_TWIN
ordinal  8..9   ATOMS_REC    P_H, P_TWIN
ordinal 10..11  AUTH_REPLAY  J_H, P_H
ordinal 12..13  SHAM_REC     J_H, P_H
ordinal 14..15  CUT_REC      J_H, P_H
ordinal 16..17  TWIN_REC     J_H, P_H
```

Each trajectory has READ opportunities 0--3 and ENV opportunities 4--12.
There are exactly 234 immutable identities and at most 234 attempts. The fourth
return is included in slot 4's input. The ninth ENV action is applied before
terminal scoring. No opportunity is replaced, transferred, retried, or filled
after cancellation.

G1A changes no empirical predicate: GOLD is 4/4 success and 4/4 minimal timely
decisive citation; NONE is at most 1/4 success with all four outcomes
scientifically valid; P ATOMS is exactly 0/2 success with both outcomes
scientifically valid; replay, sham, cut, and twin are each 2/2. Structural
capacity is separately reported as `K_NONE/4` and `K_P_ATOMS/2`; continued
pre-GPU processing is permitted only for `K_NONE <= 1` and `K_P_ATOMS == 1`.
Capacity cannot select, rerank, reject in favor of, or replace a committed
candidate.

## Exact implementation surface

After G1A ratification, add only the following GPU-path files. Keep the CPU
scripted harness in `rml_stage_b/runner.py` provider-free.

| File | Exact responsibility and public functions |
|---|---|
| `rml_stage_b/gpu_contract.py` | Dataclasses and validators for `GpuRuntimeClosure`, `RenderedRequest`, `ProviderAttempt`, `OpportunityDisposition`, `ResourceClock`, and `DispatchSchedule`; `load_runtime_closure()`, `render_request()`, `validate_token_and_byte_limits()`, `vllm_engine_kwargs()`, `sampling_params_kwargs()`, `build_dispatch_schedule()`, and `validate_complete_ledgers()`. No CUDA import. |
| `rml_stage_b/gpu_interventions.py` | `condition_snapshot()`, `extract_parent_projection_inputs()`, `build_parent_sham_projection()`, and `build_parent_cut_projection()`. These functions may read only a frozen parent transcript plus sealed store metadata. They must not import or call `rml_stage_b.reducer`, `rml_d0.planner`, a scorer, capacity evaluator, or hidden `TargetSpec` fields. |
| `rml_stage_b/vllm_provider.py` | `ExactQwenTokenizer` and `TrajectoryVllmProvider`. It loads only the pinned local tokenizer/model, accepts already rendered token IDs, produces one raw response and receipt per call, exposes active-sequence/reset telemetry, and owns exactly one trajectory process. Reuse the validation and receipt shapes from `model_provider_boundary.py`, not the v03r factory lifetime. |
| `rml_stage_b/run_gpu_trajectory.py` | `run_canary()`, `run_trajectory()`, and `main()`. One invocation runs either the single disjoint canary or exactly one registered trajectory, writes per-op immutable artifacts, disposes its suffix, shuts down vLLM, and exits. It never selects another trajectory. |
| `rml_stage_b/run_gpu_gate.py` | `prepare_gate()`, `run_gate()`, `run_lane()`, `request_global_abort()`, `finalize_raw_seal()`, and `main()`. It verifies authority/freeze/reviews, owns the wall/resource clock, launches the canary once, launches one or two fixed lanes, reconciles 234 opportunities, then starts a separate no-provider offline scoring process. |
| `rml_stage_b/gpu_remote_job.py` | `inspect_runtime()`, `verify_release()`, `start_once()`, `status()`, and `main()`. It implements G1-specific one-shot markers and refuses to start if any marker or opportunity artifact already exists. It may borrow atomic-marker code from `remote_job.py` but must not call `run_job()`. |
| `rml_stage_b/tests/test_g1_gpu_contract.py` | CPU/mock tests for exact chat/token accounting, finish-reason handling, raw-byte preservation, schedule/dependencies, two-lane merge, every cancellation type, crash/no-restart, resource boundaries, marker exclusivity, runtime/review drift, and canary disjointness. No model import or network. |
| `research_loop/prompts/rml_stage_b_canary_user_v1.json` | One canonical UTF-8/JSON user payload containing no selected target, source row, projection, condition, target key, or D0 state. Its sole allowed key is `schema:canary`; it uses the same operation grammar and asks for one READ. |
| `research_loop/schemas/rml_g1_gpu_artifacts_v1.schema.json` | Exact schemas for runtime closure, attempt receipt, raw-output row, opportunity disposition, resource report, lane schedule, and final seal. Unknown fields fail. |
| `research_loop/workflows/rml_stage_b_gold_action_fast_v1.remote.json` | The only remote spec: release verification, one canary, one gate execution, raw seal, offline score, terminal marker. It freezes every reachable file and names every required fresh artifact. |
| `gpu/a40_sync_rml_g1.sh` | One-way code/input sync to the named A40 host, excluding all job/output directories; emits a remote `sync_receipt.json` containing the reviewed lock/spec/input hashes. No model download. |
| `gpu/a40_start_rml_g1.sh` | One-shot detached launch of `rml_stage_b.gpu_remote_job start-once`; validates 64-hex run/review hashes and refuses a pre-existing remote run directory. |
| `gpu/a40_pull_rml_g1.sh` | Refuses to pull until exactly one fresh `done.json` or `failed.json` exists, then copies the immutable run directory without deleting local evidence. |

The G1A implementation itself must also replace the present open-loop
`build_slice_certificate()` with the ratified full-visible-history certifier
and independent checker, and must extend `build_pretarget_snapshot_universe()`
so `build_snapshot()` receives the exact pinned tokenizer counter and its file/
rendering hash. That is a G1A repair, not a GPU-runner convenience. The GPU
files must consume its sealed outputs and cannot recompute selection.

Do not edit the current G1 system prompt or operation schema as part of the GPU
path. Their present bytes are frozen into the future packet. The JSON schema's
`scratch.maxLength` is not sufficient enforcement; the runtime parser must
still enforce 2,048 UTF-8 bytes and 128 exact tokenizer IDs.

## Exact prompt and chat rendering

For every scientific slot, `render_request()` performs this one rendering:

1. Read `research_loop/prompts/rml_stage_b_think_v1.txt` as strict UTF-8 and
   preserve every byte, including its terminal newline. This is the sole
   `system` message.
2. Obtain `machine.model_visible_bytes()` and preserve its canonical terminal
   newline. Decode it as strict UTF-8 without trimming. This is the sole `user`
   message.
3. Call the pinned tokenizer's `apply_chat_template()` on exactly
   `[system, user]`, with `tokenize=True` and
   `add_generation_prompt=True`. There are no tools, assistant history,
   default system message, generation prompt suffix, or provider-added text
   outside that template.
4. Independently render with `tokenize=False`, encode strict UTF-8, and encode
   that text with `add_special_tokens=False`. Require the resulting IDs to be
   byte-for-byte identical to step 3's IDs. A mismatch is
   `INFRASTRUCTURE_FAILURE` before dispatch.
5. Pass those IDs to vLLM through `TokensPrompt`; never pass text to vLLM and
   never permit provider-side tokenization or truncation.

The canary uses the identical system message and chat-template procedure but
the fixed canary user payload. It is in a separate ID domain and is not in the
234-opportunity registry. Its unrendered and rendered hashes must differ from
every scientific slot-0 user/request hash. More importantly, its construction
module may not import fixtures, selected cases, stores, candidate manifests,
or reducers; hash inequality alone is not a provenance proof.

No guided decoding, JSON logits processor, repair prompt, prefilling,
best-of sampling, fallback parser, or extraction of a JSON substring is
allowed. The entire decoded generation is the parser input. Decode generated
IDs with `skip_special_tokens=False` and
`clean_up_tokenization_spaces=False`, then UTF-8 encode it. A `length` finish
reason is `MODEL_INVALID/TRUNCATED_OUTPUT` even if the visible prefix happens
to parse. A stop/EOS finish is still required to pass the strict one-object,
duplicate-key-rejecting parser.

## Exact tokenizer accounting

The tokenizer must be `Qwen/Qwen2.5-32B-Instruct` at revision
`5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`, `use_fast=True`,
`trust_remote_code=False`, `local_files_only=True`. The runtime closure records
the class, chat-template bytes, special-token map, vocabulary hash, every
tokenizer file hash, and the ordered token-ID hashes below.

- `input_tokens`: length of the final chat-template token IDs actually supplied
  to vLLM.
- `input_bytes`: length of the final rendered chat request UTF-8 bytes, not the
  smaller machine payload.
- `output_tokens`: length of vLLM's generated token-ID sequence.
- `output_bytes`: length of the complete decoded raw response bytes.
- `history_tokens/history_bytes`: exact tokenization and bytes of
  `canonical_bytes(model_visible_value()["history"])`, without chat wrapping.
- `row_tokens/row_bytes`: exact no-special-token encoding and bytes of each
  returned row; sum the four actual returns per trajectory, including
  `NOT_FOUND`.
- `scratch_tokens/scratch_bytes`: exact no-special-token encoding and bytes of
  the current emitted scratch string.

Before dispatch, require input tokens <= 16,384, input bytes <= 131,072,
history <= 8,192 tokens/65,536 bytes, current row/scratch limits, and
`input_tokens + 256 <= 16,640`. The last check prevents a configured generation
from exceeding context even if it would stop early. After dispatch, enforce
generated tokens <= 256 and bytes <= 4,096 before parsing. Enforce the ratified
per-trajectory and gate totals over the same definitions. Never use
`conservative_cpu_token_count()` in a GPU artifact or seal.

Each attempt receipt stores the complete supplied/generated token-ID arrays and
their hashes, rendered request/raw response as hex, exact byte counts, config
bytes/hash, vLLM request ID, globally unique logical session ID, finish reason,
and monotonic/Unix timing. This is the v03r v2e receipt pattern, with G1's
larger input ceiling and fresh-trajectory process boundary.

## Exact vLLM closure on the 8xA40 host

The reviewed runtime manifest must show exactly eight `NVIDIA A40` devices,
stable PCI order, eight unique UUIDs, bf16 support, and no foreign compute
process. Missing local model/tokenizer files fail before canary; the gate is
offline (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`) and may not populate or
update a cache.

Each trajectory child sees exactly one fixed four-device group and constructs
one engine with these semantic arguments; the reviewed manifest must pin the
installed vLLM version and verify that its actual constructor supports every
named argument before model load:

```text
model=<resolved local snapshot directory for the pinned revision>
tokenizer=<the same resolved local snapshot directory>
revision=5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd
tokenizer_revision=5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd
tokenizer_mode=auto
skip_tokenizer_init=False
dtype=bfloat16
tensor_parallel_size=4
max_model_len=16640
gpu_memory_utilization=0.90
max_num_seqs=1
max_num_batched_tokens=16640
enable_prefix_caching=False
enable_chunked_prefill=False
enforce_eager=True
disable_custom_all_reduce=True
distributed_executor_backend=mp
swap_space=0
cpu_offload_gb=0
kv_cache_dtype=auto
quantization=None
load_format=safetensors
trust_remote_code=False
seed=0
generation_config=vllm
```

Do not silently drop an argument for version compatibility. If the pinned
vLLM uses a different API, the exact equivalent mapping and package version
must be put in the implementation packet and reviewed; otherwise T04 fails.
The engine receives already tokenized prompts, so it does not own tokenizer
state.

The per-call `SamplingParams` semantic lock is:

```text
n=1, best_of=1, temperature=0.0, top_p=1.0, top_k=-1, min_p=0.0,
seed=0, max_tokens=256, ignore_eos=False, detokenize=False,
stop=[], stop_token_ids=[151645], include_stop_str_in_output=False,
logprobs=None, prompt_logprobs=None
```

`do_sample=false`, `num_beams=1`, `num_return_sequences=1`, and
`fallback=false` are contract semantics, not vLLM keyword arguments: the
adapter validates that the mapping above provides one greedy sequence with no
beam/best-of/fallback path. The tokenizer preflight must assert that 151645 is
the pinned `<|im_end|>`/EOS token; mismatch fails rather than substituting a
new stop ID.

Both lane coordinators set and hash-bind:

```text
CUDA_DEVICE_ORDER=PCI_BUS_ID
PYTHONHASHSEED=0
CUBLAS_WORKSPACE_CONFIG=:4096:8
NCCL_ALGO=Ring
NCCL_PROTO=Simple
TOKENIZERS_PARALLELISM=false
VLLM_WORKER_MULTIPROC_METHOD=spawn
OMP_NUM_THREADS=1
```

The CUDA, driver, NCCL, torch, transformers, tokenizers, safetensors, vLLM,
Python, OS/container, library-path, GPU UUID/order, model-file, and tokenizer-
file closure is hash-bound. `torch.use_deterministic_algorithms(True)` must be
enabled before engine creation; an unsupported/nondeterministic kernel is a
failure, not permission to disable the check.

## Process, KV, reader, and cache reset

`FRESH_PROCESS_PER_TRAJECTORY` is literal:

- the remote coordinator and lane processes never import CUDA, torch, vLLM, or
  transformers;
- for each trajectory they spawn a new process group running
  `run_gpu_trajectory`, which creates a new tokenizer object, memory service,
  machine, CUDA context, vLLM engine, scheduler, block manager, and KV arena;
- the same engine may serve that trajectory's remaining sequential slots, but
  every call supplies the full rendered history and begins with zero active
  vLLM sequences; no KV handle is reused between calls;
- prefix caching is disabled and no request/cache key is supplied;
- at child exit the engine is shut down, all vLLM worker descendants exit, and
  NVML must show no compute PID on that four-GPU group before the next child;
  failure to prove this is `INFRASTRUCTURE_FAILURE`;
- the sealed on-disk HF snapshot and read-only OS page cache are immutable
  runtime inputs, not semantic request caches. No generated row, prompt,
  output, KV state, reader lookup, or intervention state may be written there.

A unique empty per-trajectory work directory is supplied for temporary vLLM,
Triton, and torch artifacts. `enforce_eager=True` forbids compile-graph reuse.
Any unavoidable precompiled kernel cache must be read-only, hash-bound as part
of the runtime closure, and demonstrated independent of requests; otherwise it
does not satisfy `EMPTY_READER_AND_BACKEND_CACHE`.

This deliberately rejects direct reuse of
`run_v03r_recurrence_closure_v2e.ResidentModelFactory`, whose one engine spans
many logical sessions. Reuse its `TokensPrompt`, receipts, telemetry, active-
sequence checks, and raw-byte preservation as code patterns only.

## Condition mounting and intervention dependencies

All GOLD, ATOMS, and TWIN base stores, source DAG/lineage, query universe,
aliases, indexes, canonical order, handles, cache/derived views, exact tokenizer
counts, selector order/trace, and four-side manifest are sealed before the
capacity evaluator receives hidden truth and before the canary. The online
service receives only `(sealed_projection_id, emitted_key)`.

Mounts are fixed as follows:

- `GOLD_REC`: the target side's presealed GOLD projection;
- `NONE_REC`: the same presealed empty/null-return projection for all four
  sides;
- P `ATOMS_REC`: the same presealed `H:ATOMS` projection on both P sides;
- `AUTH_REPLAY`: the parent's identical initial target, GOLD projection,
  prompt/renderer/config bytes, in a clean process; no parent output is input;
- `SHAM_REC`: a parent-conditioned projection that removes the pre-certified
  nondecisive equivalence classes matching the parent's cited-class count and
  exact serialized row byte/token budget;
- `CUT_REC`: a parent-conditioned projection removing the complete forward,
  reverse, alias, index, cache, and derivable-view closure of the parent's
  emitted citation handles;
- `TWIN_REC`: the presealed registered twin GOLD projection while D0 continues
  to execute the actual J_H or P_H world; no actual/twin answer or parent trace
  enters the request.

Run all four GOLD parents before their children. `extract_parent_projection_inputs()`
is a scorer-free transcript projection: it may check that a cited handle was
actually returned and belongs to the sealed parent store, but cannot decide
semantic entailment, minimality, success, continuation, score, or intervention
effect. No child dispatch decision may depend on capacity, D0 truth, a reducer
result, or whether the parent succeeded. Those judgments occur only after all
234 opportunities have dispositions.

`AUTH_REPLAY` and `TWIN_REC` need only a frozen parent artifact and their
presealed inputs. SHAM/CUT additionally need a nonempty, well-formed parent
citation projection and a unique pre-certified match/closure. If that purely
constructive dependency is absent, cancel all 13 identities of only that child
as `CANCELLED_DEPENDENCY_FAILED`; do not invent expected decisive handles from
`TargetCase`. A parent infrastructure/resource failure aborts the whole run.
A parent model-invalid or scientific nonsuccess does not itself authorize
score-conditioned cancellation; constructible siblings still run and later
fail the exact scientific predicate.

This is a required correction to the current scripted pattern:
`runner.py` presently calls `decisive_handles(case, snapshot)` to build SHAM
and CUT. That uses target/scorer-owned expectations rather than the parent's
actual citations and is forbidden in the GPU path.

## Dispatch ordering and two safe four-GPU lanes

The canonical logical order is always the 18 ordinals above, and final ledgers,
hashes, reports, and offline scoring are merged by that ordinal and slot, never
by completion time. The simplest conforming execution is one four-GPU lane in
strict ordinal order.

Two concurrent four-GPU workers are permissible only if the pre-GPU reviewed
schedule explicitly defines physical lanes as an implementation of, rather
than a change to, the frozen logical order:

```text
lane A / CUDA_VISIBLE_DEVICES=0,1,2,3
  0 GOLD:J_H; 1 GOLD:J_TWIN; 4 NONE:J_H; 5 NONE:J_TWIN;
  8 ATOMS:P_H; 10 AUTH:J_H; 12 SHAM:J_H; 14 CUT:J_H; 16 TWIN:J_H

lane B / CUDA_VISIBLE_DEVICES=4,5,6,7
  2 GOLD:P_H; 3 GOLD:P_TWIN; 6 NONE:P_H; 7 NONE:P_TWIN;
  9 ATOMS:P_TWIN; 11 AUTH:P_H; 13 SHAM:P_H; 15 CUT:P_H; 17 TWIN:P_H
```

Each lane has nine trajectories and keeps each canonical parent's four
children on the same lane. Lane completion order and timing are host-only and
cannot enter a prompt, projection, selector, or scorer. The coordinator starts
both lanes only after the canary process has fully exited and both GPU groups
are clean. Each lane runs one child at a time. No worker may spill to the other
group, and CUDA/NVML UUID checks must prove the mapping.

There is a real contract ambiguity here: ratified R09 says target/condition
order is hash-bound, while the current `build_roster()` expresses a total
order, not merely a report order. If independent review concludes that actual
dispatch must follow that total order, the two-lane schedule is incompatible
and must not run; use the single lane or obtain a new adjudicated/ratified
parallel schedule. Calling concurrent completion order “logically ordered” is
not enough. G1A cannot silently change this because R06 requires target and
condition order to remain byte-identical.

## Raw-output and opportunity ledgers

Before canary, write `opportunity_registry.json` once with all 234 identities,
trajectory ordinal, condition, target, parent, slot, and phase. During the run,
never append to one shared JSONL file from two workers. Each opportunity gets
an `O_EXCL`/atomic file:

```text
job/raw_attempts/<opportunity_id>.json       # attempted calls only
job/opportunity_events/<opportunity_id>.json # exactly one final disposition
```

An attempted raw row contains the complete request/config/response/receipt and
token arrays described above, process/lane/GPU UUIDs, snapshot seal, machine
input/output state hashes, and timing. It is written and fsynced before the
machine transition can authorize a next call. The disposition is then written
once. A crash between reservation and receipt leaves a sunk attempted identity
and makes the run infrastructure-failed; it is never retried.

Authorized opportunity dispositions are:

```text
COMPLETED_NONTERMINAL                  attempted=true
TERMINAL_SCIENTIFIC_VALID_SUCCESS      attempted=true
TERMINAL_SCIENTIFIC_VALID_NONSUCCESS   attempted=true
TERMINAL_MODEL_INVALID                 attempted=true
TERMINAL_INFRASTRUCTURE_FAILURE        attempted=true or reserved/in-flight
TERMINAL_RESOURCE_CEILING_EXCEEDED     attempted=true or predictable zero-attempt
CANCELLED_AFTER_TERMINAL               attempted=false
CANCELLED_DEPENDENCY_FAILED            attempted=false
CANCELLED_GLOBAL_ABORT                 attempted=false
```

Every terminal trajectory immediately writes zero-token/zero-byte/zero-wall
`CANCELLED_AFTER_TERMINAL` rows for its undispatched suffix. A dependency-
failed child writes 13 zero-attempt rows. Infrastructure/resource failure
writes its terminal row, atomically creates the global abort request, kills any
other in-flight process group, records that already-dispatched in-flight
identity as infrastructure-failed, and cancels every remaining identity. A
model-invalid result is a registered failure but does not globally abort.

The finalizer requires exactly one event per registered ID, at most one raw
attempt per ID, no raw row for a never-attempted ID, and:

```text
234 registered = attempted + zero-attempt disposed/cancelled
attempted <= 234
raw_attempt_count = attempted
```

It emits per-trajectory and per-condition registered, attempted, cancelled,
scientific-valid, success, model-invalid, infrastructure-failed, dependency-
failed, tokens, bytes, and wall time. It then hashes the ordered registry,
events, raw attempts, frozen traces, store/target/runtime/review bindings, and
resource report into `raw_gate_seal.json`. Only a different no-provider process
may import `rml_stage_b.reducer` and score that immutable seal. Scoring output
can never feed execution.

## Crash and no-retry semantics

The remote run directory is created with exclusive semantics. Presence of any
`started.json`, `failed.json`, `done.json`, raw attempt, reservation, or event
for the run ID makes every later `start-once` invocation refuse. A prior
`done.json` is evidence to inspect, not permission to return success and run
again. A prior `failed.json` is terminal. `started.json` without a terminal
marker after the recorded PID/process group is gone is a permanent crash/
infrastructure failure; do not resume from the next opportunity and do not
relaunch under a new run ID.

This is why the generic `remote_job.run_job()` cannot be used unchanged: it
returns success when `done.json` exists and permits a new run when both
`started.json` and `failed.json` exist. Both behaviors are too permissive for
G1's one-run/no-retry authority.

`SIGTERM`, `SIGINT`, child nonzero exit, OOM, NCCL error, lost process, lost
receipt, hash/reset failure, filesystem error, or coordinator exception is
`INFRASTRUCTURE_FAILURE`. Signal handlers make a best-effort atomic failure
marker and ledger disposal, but absence of that cleanup never authorizes a
retry. There is no resume mode.

## Resource enforcement

The canary-start monotonic timestamp is the single epoch. It begins immediately
before spawning the one canary process and ends only after `raw_gate_seal.json`
is fsynced. The hard ceilings remain exactly 10,800 seconds, 24 aggregate A40
GPU-hours, 2 GiB of run artifacts, and USD 0.00 incremental external spend.

For the 8xA40 two-lane mode, conservatively charge all eight reserved A40s for
the entire canary-to-seal interval, including idle lane time. Thus GPU-hours are
`8 * elapsed_seconds / 3600`, and the 24-GPU-hour and three-hour walls coincide.
This cannot undercount. Single-lane mode may use exact four-device process
intervals, but using the same conservative eight-device charge is simpler and
safer.

After the canary, freeze a reduced operational deadline using only canary
load/generation time, the two nine-trajectory lanes (or one 18-trajectory lane),
and a fixed final-seal reserve. If the prospective schedule cannot fit, stop
before the first scientific attempt. This is the R09 permission for first-call
timing to reduce, never enlarge, the ceiling. Once scientific dispatch starts,
a watchdog terminates all process groups before the earlier wall/GPU-hour
deadline; the current attempt is resource-failed and the undispatched registry
is cancelled.

Before every call, enforce all predictable per-call, trajectory, and gate
token/byte limits using exact IDs. Before every atomic artifact write, include
the prospective file and fixed final-marker/seal reserve in the 2-GiB total.
An unforeseen post-call overflow preserves the raw attempt, marks
`RESOURCE_CEILING_EXCEEDED`, and aborts globally. There is no truncation,
elision, compression, log deletion, artifact deletion, fallback hardware, or
arm-specific shortening. The local model cache is pre-existing and outside the
run-artifact budget; every new run file, including logs and temporary files,
is inside it.

## Freeze, review, canary, and post-run binding

The exact pre-GPU sequence is:

1. Verify the original G1 and ratified G1A intake states and hashes. Run all six
   original replacement tests plus the three additive G1A tests. Require the
   exact committed manifest, `K_NONE <= 1`, `K_P_ATOMS == 1`, source-lineage/
   ambient-denial audit, complete history capacity certificate, and independent
   upper-bound checker. Zero model/GPU/network calls.
2. Sync code and already-present model inputs to the A40 host. Run only
   `gpu_remote_job inspect-runtime`: hash packages, libraries, GPU inventory,
   model/tokenizer snapshot, chat template, system/canary prompts, schema,
   parser, stop IDs, roster/schedule, stores, manifests, source, reducer,
   runner, reset/failure policy, and full reachable import closure. It may load
   the tokenizer locally; it may not load/generate with the model.
3. Build one canonical `implementation_packet.json` and repository lock that
   include the remote runtime/sync receipts and exact allowlist diff against
   the original G1 consensus/ratification. `freeze_closure` must report no
   reachable local Python omission.
4. Obtain exactly two pre-GPU approvals bound to the packet/run ID: one fresh
   independent implementation reviewer and one distinct author-side scientific
   advocate. `review_binding.py` file hashes are reusable, but the G1 verifier
   must additionally check role, actor ID, no overlap, run ID, verdict, packet
   hash, original/G1A authority hashes, and freshness. Any rejection, drift, or
   malformed receipt stops.
5. Re-sync only the reviewed lock/packet/review receipts, obtain and verify the
   remote sync receipt, and re-hash all inputs on the remote host immediately
   before canary.
6. Start the monotonic/resource clock and execute exactly one target-disjoint
   canary in a fresh four-GPU process. Require exact model/tokenizer hashes,
   schema-valid whole output, token/byte limits, unique receipt, empty active
   sequences, clean process exit, zero scientific IDs, and clean GPUs. Canary
   failure is terminal and has no retry.
7. Execute the reviewed one- or two-lane schedule once. Seal raw outputs, then
   run offline scoring in a new process with no model/provider imports. Publish
   exactly one `done.json` for operational completion, even if the scientific
   gate predicate is false; use `failed.json` for infrastructure/resource/
   sealing failure.
8. Pull only after a terminal marker and verify every hash locally. Fresh
   post-run independent-review and advocate receipts bind the immutable output
   seal. No result interpretation or claim string is released before both pass.
   The exact existing claim whitelist remains the maximum statement, and G2 or
   any successor requires new authority.

## Remote paths and markers

Use the existing `gpu/a40_ssh.sh` host only; do not use the v2 H100-NVL address,
bootstrap, DREAM workflow, or v03r workflow. The G1 wrappers should use:

```text
remote repository:  /home/local-rohing/dream-state
remote job root:    /localhome/local-rohing/rml_g1/jobs/<run_id>/
local pulled copy:  gpu_artifacts_local/rml_g1/<run_id>/
```

The remote run directory contains immutable `sync_receipt.json`,
`started.json`, `canary.json`, `progress.json`, `raw_gate_seal.json`, and
exactly one terminal `done.json` or `failed.json`. `progress.json` is an atomic
snapshot derived from immutable per-op files; it is never completion evidence.
Process existence, launcher exit, `started.json`, and a copied partial ledger
are not completion evidence. The pull wrapper verifies marker run ID, packet
hash, start time freshness, and raw-seal hash before copying.

## Current incompatibilities that must block launch

1. **G1A is unratified.** Its intake forbids implementation, and the current
   open-loop capacity code does not satisfy its full-history exactness or
   independent upper-bound obligation.
2. **The current GPU seam does not render chat.** `dispatch_one()` sends only
   canonical machine payload bytes; no system/user chat template is applied.
3. **Current accounting is not exact-token accounting.** It uses
   `conservative_cpu_token_count`, records payload bytes rather than rendered
   request bytes, and does not precheck input IDs plus the 256-token output
   allowance.
4. **The present snapshot seal says `cpu-bound-token-rendering-v1`.** It cannot
   be the R09 tokenizer rendering lock, and current universe construction does
   not inject the exact tokenizer counter.
5. **Current intervention construction uses expected truth.** The scripted
   runner obtains decisive handles from `TargetCase`; GPU CUT/SHAM must derive
   their inputs only from the frozen parent's emitted citations and sealed
   source-certified metadata. The present sham ordering is not itself a proof
   that candidates are independently pre-certified nondecisive.
6. **The current provider return type loses required evidence.** It returns
   `(raw, accounting)` rather than rendered request/config bytes, token IDs,
   receipt, finish reason, reset telemetry, and raw-output binding.
7. **The current opportunity ledger is not crash-safe or two-writer-safe.** An
   over-ceiling append raises before a retained final ledger is available, and
   no on-disk reservation/raw-attempt protocol exists.
8. **The present canary validator is self-attested.** Arbitrary component
   hashes and a Boolean `backend_deterministic` pass; it does not bind real
   files, prompt/token IDs, finish reason, target-independent provenance, or
   reset telemetry.
9. **One canary call cannot empirically prove repeatability.** The ratified
   scope authorizes one canary, while behavioral determinism normally requires
   at least two identical generations. Under the design above, T04 can prove
   only exact deterministic configuration, deterministic-algorithm enforcement,
   and one conforming emission. If reviewers require empirical identical-run
   evidence, this is a genuine authority incompatibility: do not add a second
   call; obtain a newly adjudicated/ratified canary protocol.
10. **Fresh logical sessions are not fresh trajectory processes.** The v03r
    resident provider and `model_provider_boundary.py` are valuable precedents
    but do not by themselves satisfy `FRESH_PROCESS_PER_TRAJECTORY`.
11. **The generic remote runner permits restart-like behavior.** Its marker
    semantics are incompatible with G1's crash/no-retry rule.
12. **Two-lane physical order is not explicitly ratified.** It is safe only if
    exact-byte pre-GPU review accepts the fixed lane schedule as preserving the
    hash-bound logical target/condition order; otherwise parallel execution is
    forbidden.

Until every item except the explicitly accepted one-canary limitation is
closed in a frozen implementation packet—and that limitation is positively
disposed by both reviewers—the correct GPU action is no launch.
