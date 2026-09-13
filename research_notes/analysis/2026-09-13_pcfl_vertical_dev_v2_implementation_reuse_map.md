# PCFL vertical DEV v2.1 implementation reuse map

**Date:** 2026-09-13 UTC  
**Status:** analysis only; no source, fixture, model, adapter, or GPU action  
**Repository cut inspected:** `29bcd1ed`  
**Protocol:** `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_synthesis.md`

## Bottom line

The vertical should be implemented as a **new small core plus a new runtime**, not
by extending the active L2 public-record experiment in place. Most of the hard
systems machinery already exists and can be transplanted from L2: immutable
receipt capture, exact child-span custody, native chat/EOS/mask preflight,
cold-base LoRA fitting, fresh-process GPU isolation, stage sealing, replay, and
terminal custody. What does not exist is the scientific middle of this assay:
the opaque route cube, EVENT/LINK materializer, candidate-free memory service,
route actor, route scorer, and shortcut report.

The repaired v2.1 arithmetic is consistent with the current trainer **only if
physical training packing is disabled**:

```text
20 query-response slots x 8 views = 160 items/epoch
160 items / batch 4 = 40 updates/epoch
40 x 5 epochs = 200 updates/fit
14 fits x 200 = 2,800 updates
14 fits x 30 A40-min = 420 A40-min = 7 A40-hours
```

The current trainer cannot execute the frozen recipe unchanged, however: it
does not clip gradients, does not expose AdamW betas/epsilon/weight decay as
frozen configuration, and does not preserve the required per-update
loss/gradient/RNG plus optimizer-state receipts. Those are the only trainer
changes on the critical path. The 10 A40-hour inference allowance is plausible
but is not yet mechanically enforceable from an exact request inventory; the
new preparer must enumerate every request and per-stage cap before any model
load.

## 1. Source-level implementation shape

The shortest clean layout is four new files, while importing the narrow stable
trainer helpers:

```text
organism_v6/pcfl_vertical_dev.py          pure world, compiler, scorer, reducer
gpu/astra_pcfl_vertical_dev.py            prepare, native stages, fits, custody
tests/test_pcfl_vertical_dev.py           exhaustive CPU science/integrity tests
tests/test_astra_pcfl_vertical_dev.py     runtime, trainer, lifecycle/custody tests
```

Do not edit `organism_v6/l2_public_record_dev.py` or
`gpu/astra_l2_public_record_dev.py`. They belong to a separate, hash-pinned
experiment (`0bb33988...` and `213c2a2f...`) and their binary-action/fixed-16
state machine is the wrong schema for this world. Reusing their architecture by
forking is safer and faster than adding route-specific branches to them.

`organism_v6/train_adapter_v3.py` is the one shared component worth improving
rather than cloning. Add frozen AdamW/clipping/audit fields behind defaults so
existing callers remain behaviorally unchanged, then bind the revised trainer
hash in the new runtime snapshot. If touching the shared trainer is considered
too risky while another pinned run is live, put only the optimizer loop in a
small `pcfl_vertical_train.py` wrapper and continue importing its encoding,
LoRA, ordering, and collation functions. Do not copy the full trainer.

## 2. Exact reuse map

### 2.1 Generator and collision certificate

| Needed object | Existing component | Reuse ruling |
|---|---|---|
| Deterministic opaque vocabulary and public/private split | `organism_v6/l2_public_record_dev.py`: `build_world`, `public_view`, frozen dataclasses | Reuse the construction pattern, not its types. It hardcodes two actions, sixteen slots, and a binary private target. |
| Deterministic seed-domain ordering and hashing | `organism_v6/multikey_writer_gateway_simple.py`: `canonical`, `digest`, `seeded_order` | The algorithms are directly suitable. Prefer a tiny local implementation or narrow utility import; importing the entire W0 module drags unrelated model/candidate semantics into the source snapshot. |
| Collision-class enumeration and byte-equality auditing | `lands/v03.py`: `enumerate_collision_catalog`, `audit_paired_worlds` | Reuse the enumerate-all-then-audit pattern only. The pigment world and its dataclasses are not compatible. |
| Single/pairwise shortcut ceiling | `multikey_writer_gateway_simple.best_shortcut` | Reuse the grouping/counting kernel. It must be expanded to the protocol's full report: key count, coverage, minimum support, minimum labels, deterministic keys, decoded occurrences, and Bayes-best route accuracy for every named field and pair. |
| Previous PCFL D0 collision contracts | `research_loop/changes/chg_20260901_pcfl_d0_exact_v2/` | Useful specifications and golden-schema ideas only; there is no Python implementation to call. |

**New source required:** a route-world generator with independent opaque node,
port, event, link, probe, receipt, and goal namespaces; the `(O,R,D)` cube; a
public/private allowlist; exact OLD/NEW projections and cuts; two independently
implemented CPU route oracles; exact entropy/collision calculations; the
48-decision atoms/link audit; the 192-decision parser/executor audit; and the
full projection report. No existing executable constructs this world.

The opaque-ID allocator must search under the pinned Qwen tokenizer, then seal
the first valid inventory before model outputs exist. It must prove fixed-width
ASCII, namespace disjointness, equal token length in every registered row and
control replacement, and no redrawing after a scientific failure. That search
is preparation, not model execution.

### 2.2 Public receipts, authorship, and compilation provenance

| Needed object | Existing component | Reuse ruling |
|---|---|---|
| Immutable action/outcome/record chain | `l2_public_record_dev.py`: `Receipt`, `make_receipt`, `_check_receipt`, `_link`, `feedback` | Strong template. Generalize the receipt phase and route-event fields in the new core. |
| Raw generated bytes before feedback | `gpu/astra_l2_public_record_dev.py`: `capture_stage`, `replay_capture` | Reuse nearly verbatim at the runtime-architecture level. It durably writes the raw action before public feedback and verifies request/response identity on replay. |
| Exact child span and no-repair admission | `organism_v6/endogenous_action_relay.py`: `admit_block`, `parse_action`, `Receipt.raw_sha256`; `l2_public_record_dev.py`: `_episode`, `_block`, `compile_corpus` | Reuse the span-offset/hash and whole-line reject pattern. Write new strict EVENT/LINK parsers; the existing relay grammar is compiler-pass-specific. |
| Failure-inclusive formation denominator | `l2_public_record_dev.py`: `CapturedBlock`, `Rejection`, `_block`; relay `check_formation` | Direct design reuse. Store malformed and rejected proposals, not just accepted rows. |
| JSON wire and reconstruction | `l2_public_record_dev.py`: `_pack`, `_unpack`, `to_data`, `from_data` | Reusable pattern. Its type allowlist is closed to L2 classes, so add route-specific types in the new core instead of importing and weakening it. |
| Clean cumulative second sleep | `l2_public_record_dev.py`: `compile_corpus`, `complete_sleep`; `astra_l2.fit_stage` | Reuse the clean-base cumulative-corpus pattern. S2 must rebuild from C0 with OLD+NEW corpus and a fresh optimizer, not warm-start S1. |

**New source required:** strict whole-line parsers for
`EVENT ... EVIDENCE ...` and `LINK ... EVIDENCE ...`; phase-specific visibility
checks; a query-level materializer that groups accepted spans without adding
meaning; construction of EVENT_TWIN, LINK_PERMUTE, ATOMS-MISS, OLD_REPLAY-MISS,
and parser-disjoint padding controls; and a corpus ledger joining every
training item back to raw generation byte offsets, receipt hashes, wrapper,
token count, mask hash, arm, root, and stage.

The post-S1 native continuation needs a dedicated taint assertion. Its raw
prompt/token receipt must contain no OLD receipt, admitted row, roster, local
service return, compiler state, or ledger excerpt. The mechanistic-service fork
must have a distinct non-lineage type so it cannot be passed to the S2 compiler.

### 2.3 Query-level writer materialization

The v2.1 repair is implementable as a deterministic dictionary from request
bytes to response bytes:

```text
READ EVENT e       -> one exact child EVENT line
READ EVENTS_AT n   -> all matching EVENT lines, event-ID sorted, LF joined
READ LINKS_FROM e  -> all matching LINK lines, link-ID sorted, LF joined
```

The final child row retains its LF. Maximum adjacency is two. At S1 the full
table has 17 scored requests (8 individual EVENT, 6 EVENTS_AT, 3 LINKS_FROM);
at S2 it has 19 (9, 6, 4). Three S1 and one S2 disjoint padding requests bring
both stages to 20 slots. The materializer should reject duplicate inputs,
contradictory targets, missing required addresses, wrong sort order, any
semantic field introduced outside an admitted span, and any `MISS` not
explicitly registered for a control.

There is no current implementation of this table. `l2.training_items` trains
one target per address and therefore must not be reused as-is. The new tests
should include the exact multi-row cases (`S_L`, `B`, S1 `e3`, and S2 `e1`)
that exposed the original contradiction.

### 2.4 Trainer

| Needed behavior | Existing component | Reuse ruling |
|---|---|---|
| Span-normalized response-only examples | `train_adapter_v3.normalize_items`, `encode_item_segments` | Direct reuse. |
| One item per physical sequence | `train_adapter_v3.pack_by_group(..., pack=False)` | Direct reuse and assert 160 singleton sequences. The protocol word “packing” refers to compiler assembly; physical trainer packing must remain off for the 200-update arithmetic. |
| Deterministic coupled order | `train_adapter_v3.epoch_order` | Direct reuse if every arm uses the same 20 slot IDs, 8 view IDs, item order, seed, and five epochs. Seal all five epoch orders. |
| Correct batching/masking | `train_adapter_v3.collate` | Direct reuse. Batch four yields exactly forty steps per epoch. |
| All-layer rank-8 LoRA | `train_adapter_v3.lora_config`, `ALL_PROJ` | Direct reuse with `rank=8`, `alpha=16`, dropout `.05`, all seven projections, every layer. |
| Exact native template + assistant terminator | `astra_l2.encode_training` | Reuse this preflight rather than trusting `chat_template=True` alone. It renders prompt and full assistant message separately, proves prefix identity, explicitly labels the target plus EOS, masks template tail, and round-trips through the real tokenizer/collator. Generalize from one row to a multi-row response block. |
| Cold clean-base fit | `astra_l2.fit_stage` plus `train_adapter_v3.run_training` | Reuse. Assert no incoming PEFT state, only LoRA A/B trainable, final finite state, and clean base hash. |

**Trainer gaps that block an exact fit:**

1. `TrainConfig` has no AdamW beta, epsilon, weight-decay, or maximum-gradient-
   norm fields. `torch.optim.AdamW(params, lr=cfg.lr)` happens to use the
   desired PyTorch defaults today, but frozen science cannot rely on implicit
   defaults.
2. The loop calls `backward()` then `opt.step()` with no
   `torch.nn.utils.clip_grad_norm_`; the required global norm `1.0` is absent.
3. The manifest records epoch-mean loss and a final loss, not the required
   per-update loss/gradient trace.
4. Clean fits do not record initial/final LoRA tensor inventories, initial and
   final optimizer-state hashes, or per-update CPU/CUDA dropout RNG hashes.
   Q0's `rng_receipt`, `tree_state`, `state_receipt`, and `ordered_inventory`
   show working implementations of these audit primitives, but its custom
   two-choice training objective is not reusable.

The smallest trainer patch is to expose those four AdamW/clipping fields,
clip immediately before each optimizer step, and optionally enable a strict
audit trace that hashes (not serializes) gradients, optimizer state, trainable
tensors, and RNG at the declared points. The vertical manifest then requires
exactly 200 finite executed steps; a skipped nonfinite batch is a failed fit,
not a smaller-dose adapter.

Target-token equalization must happen **after real tokenizer rendering** and
must count the assistant EOS as loss-active, matching L2's current preflight.
Each stage gets one target-token budget equal to its longest arm plus the fixed
reserve. Do not use sample weights: the current trainer has no weighted-loss
path, and whole-token padding already gives exact equality. Assert zero target
truncation and sequence length `<512` before loading a model.

### 2.5 Native runner and stage scheduler

| Needed behavior | Existing component | Reuse ruling |
|---|---|---|
| Offline pinned preparation | `astra_l2.validate_spec`, `prepare`, `verify`, `load_apis`, `offline` | Reuse the design almost verbatim: fresh non-git source snapshot, exact source inventory, model-binding receipt, tokenizer/chat hash, environment and Python identity. |
| One native load per isolated worker | `astra_l2.worker`, `run_stage`, `budget`, `release_budget` | Reuse. Each fit or evaluation stage runs in a fresh process group with a hard deadline and verified owned cleanup. |
| Base/LoRA vLLM generation and raw token receipts | `astra_l2.Native`, `validate_response` | Reuse the engine pattern, not the fixed class. The new backend needs request-level choice between no adapter and one sealed LoRA plus 2048-token generation. |
| Stage state and no-resume | `astra_l2.stage_dir`, `read_stage`, `dependency_states`, `execute_loop` | Reuse the closed-stage/replay pattern with a new DAG and route-specific state machine. |
| Explicit work caps | `astra_l2.CAPS`, `check_work` | Reuse, expanded to calls, returned memory tokens, actor tokens, fits, updates, A40-seconds, retries, and intermediate world returns. |

The current L2 controller is serial and binds one `gpu_uuid`. The new protocol
requires four S1 fits per surviving root and three S2 fits per root to run in
parallel. The runtime therefore needs a small deterministic DAG scheduler and
a presealed list of GPU UUID/model identities. A worker still owns exactly one
GPU and one stage; concurrency changes only the controller. With two roots,
peak fit concurrency is eight at S1 and six at S2 if both roots progress
together. A scientifically valid serial fallback is possible, but it would not
implement the frozen parallel schedule and may miss the wall-clock objective.

For the mechanistic endpoint, use one LoRA-enabled vLLM engine per worker and
route requests explicitly: the clean actor's generations have no LoRA request;
the goal-blind memory worker's local requests use the sealed LoRA request.
This realizes “C0 actor plus C0+LoRA memory worker” without two resident base
models. Log the two prompt projections separately and assert that memory-worker
prompts contain only one local request. Never feed task/goal/history bytes into
the mounted memory call.

Do not reuse `organism_v6/batch_loop.EpisodeDriver` as the route actor. Its
PREDICT/ACT/NOTE/RECALL/DONE grammar and immediate gym feedback are wrong for a
one-shot route with no intermediate response. Its lockstep batching and
common-random `_seed_for` are useful patterns. Implement a smaller route state
machine that accepts only READ calls until a single complete ROUTE, enforces 12
reads/4096 returned tokens/2048 actor tokens, gives no route feedback, and
records zero retry.

### 2.6 Reader and actor endpoints

No existing reader implements the required candidate-free API. Build two
backends behind the same three-call surface:

1. **Text/ceiling backend:** deterministic dictionary lookup over the exact
   registered query-response table, returning complete sorted blocks or MISS.
2. **Parametric backend:** one goal-blind C0+LoRA generation per exact local
   request, with no answer candidates, logprob ranking, task context, or repair.

`semantic_carrier_diagnostic.py` is useful only for its strict separation of
ordinary generation from candidate scoring, raw token/EOS/truncation receipt,
bounded worker, and model/tokenizer pins. Its `candidate_choice`/`score` path is
explicitly forbidden here. `model_backend.VLLMBackend.batch` can inform batched
throughput, but it lacks the strict source/custody checks and per-request LoRA
routing; the L2 native runtime is the safer base.

The mounted native endpoint uses the same ordinary task prompt and route parser
but sends the whole actor generation through the personal adapter, with no
local service. It needs a distinct stage and receipt from the modular endpoint;
one cannot compensate for the other.

### 2.7 Scorers and reducer

| Needed score | Existing component | Reuse ruling |
|---|---|---|
| One-shot strict parse, raw text, EOS/truncation | `semantic_carrier_diagnostic.strict_output`, `check_generation`; `astra_l2.validate_response` | Reuse structure; write route/EVENT/LINK-specific parsers. |
| Deterministic graph execution and dependency cuts | None | New source, implemented twice independently for the CPU gate. |
| Semantic versus strict memory exactness | Q0's semantic/surface split in `semantic_carrier_diagnostic.reduce_records` | Reuse score layout only. Semantic parsing may tolerate fences; strict exactness never does. Preserve raw malformed output in both columns. |
| Failure-inclusive fixed-denominator reduction | `l2_public_record_dev.reduce_pair`, `astra_l2.collect` | Reuse the fail-closed reducer/replay pattern, replacing L2's binary readout metrics. |
| Ordered labels and noncompensatory progression | `astra_l2.execute_loop` state-machine pattern | New route-specific reducer implementing the exact Section 13 order. Branch labels do not rescue root failure. |

The route executor must accept exactly one
`ROUTE <start> <goal> : <ports>` line, reject prefixes/suffixes/multiple routes,
execute the entire command only after commitment, and produce no intermediate
node/error/score. Keep parse, legality, and graph success separate. The exact
graph oracle is CPU-only and must never become a model-visible candidate or
repair service.

### 2.8 Canary, rollback, custody, and isolation

| Needed guard | Existing component | Reuse ruling |
|---|---|---|
| Real-context marker canary | `run_life_v2.format_canary` and `group_gate` | Reuse the lesson: test the real action interface and brevity, not a synthetic prompt. The current function is four CompilerGym programs and cannot serve as the frozen 40-item route-generic canary. Build a sealed 40-item panel. |
| Candidate accept/reject and prior-snapshot restore | `run_life_v2` staged adapter promotion and `group_gate`; L2 `complete_sleep` | Reuse the candidate-directory/commit-marker pattern. A rejected candidate remains a writer failure even after rollback. |
| Write-once trees and link rejection | `astra_l2.write`, `plain_path`, `tree`, `checked_file` | Direct architecture reuse. Tests already cover symlink/hardlink, extra/missing file, tamper, launch-log separation, and no resume. |
| Terminal seal, witness, custody, replay | `astra_l2.finalize`, `custody`, `collect` | Reuse this version. It prospectively excludes `SEAL.json`, `FINALIZED.json`, and `FINALIZATION_ABORT.json` from the sealed data inventory and separately binds terminal witnesses. |
| Detailed model/optimizer/RNG tensor custody | `astra_pairwise_q0_fulldose.py`: `tensor_hash`, `rng_receipt`, `tree_state`, `state_receipt`, `ordered_inventory` | Generalize these primitives into the trainer receipt. Do not reuse Q0's candidate-prefix objective or dynamic gate. |
| External control quarantine | No exact component | New custody namespaces and taint types. Retain control corpora/adapters through reduction; do not delete them and do not allow them as a parent of authentic stages. |

`lineage_guard.py`, `life_lineage.py`, and `neutral_pair_custody.py` should not be
used directly. Their schemas and allowlists are tied to preschool/reasoning or
fixed probe artifacts; `lineage_guard` even treats PCFL-like markers as a
forbidden deployment contamination. Borrow their no-follow/hash patterns only.
The vertical needs its own closed lineage manifest.

The Q0 full-dose runtime is the stronger source for numerical receipts and
fresh-stage tickets, but its historical seal needed external terminal custody.
Use the L2 terminal witness pattern and add an external whole-root custody
receipt after collection; do not copy Q0's old seal boundary blindly.

## 3. Code-reality audit of the frozen arithmetic

### 3.1 Fits and optimizer updates: exact pass

The repaired 20-slot materialization removes the old contradictory per-row
training unit. With `pack=False`, 160 items is exactly 160 sequences. The
current training loop slices those sequences by `batch_size=4` and increments
`steps` once per batch because `grad_accum=1`; therefore it executes 40 steps
per epoch and 200 across five epochs. There is no tail batch. Four S1 plus
three S2 fits per root, times two roots, is fourteen fits and 2,800 updates.

The runtime must assert all of the following before accepting that arithmetic:

- exactly 20 response slots and 8 views per slot;
- exactly 160 encoded, nonempty items and singleton physical sequences;
- five complete epoch orders containing every item once;
- batch size four, accumulation one, `max_steps=0`;
- zero split, truncation, skipped target, and nonfinite batch;
- exactly 200 optimizer steps in the durable manifest; and
- equal target-token totals, item counts, batches, update order, initial
  tensors, optimizer state, and dropout RNG across arms in the same stage.

Context-token counts can differ across the eight neutral wrappers unless the
protocol intends full FLOP equality; the frozen rule explicitly equalizes
loss-active target tokens, examples, batches, and updates. Record context and
total tokens so that any material imbalance remains visible.

### 3.2 Fit time: cap is coherent but unproven

Fourteen fits at thirty A40-minutes is arithmetically seven aggregate A40-hours
regardless of parallelism. No repository receipt yet proves that the revised
200-step, max-length-512, batch-four, all-layer rank-8 fit completes in thirty
minutes. The active L2 runtime budgets ten minutes for only 20/40-step fits,
and Q0's 128-update custom objective is not the same workload. Follow the
protocol: profile exactly one fully materialized S1 and one S2 fit before the
DEV outputs are opened, and fail `VS_RESOURCE_CAP` rather than increasing the
cap.

The runner must also verify the actual GPU product. Its current `gpu_uuid`
check proves identity and vacancy, not that the device is an A40. If execution
uses an A100, report actual device-hours and do not silently label them
“A40-hours”; either reserve A40s or prospectively amend the resource unit.

### 3.3 Inference: budget plausible, exact inventory still required

The zero-fit delayed table alone contains `10 x 64 = 640` actor tasks. The
reachout certificate adds `5 x 32 = 160` actor tasks. ACTIVE_LINKED_TEXT can
consume at most 768 memory calls for delayed tasks and 384 for reachout if
every actor spends all twelve reads. Formation, S1/S2 carrier panels, cuts,
wrong-root/OFF/native panels, and the 40-item canaries add further work.

The fixed 10 A40-hour inference ceiling can be enforced by aggregate measured
GPU seconds, but the fastest fail-closed implementation should also materialize
an exact per-stage request ledger before launch:

- actor episodes;
- maximum and actual local service generations;
- actor and returned-memory token ceilings;
- native mounted generations;
- formation calls;
- canary calls; and
- zero retries/intermediate route returns.

The current L2 `CAPS` mechanism is suitable once these counts are enumerated.
Preparation should reject a plan whose worst-case requested work exceeds the
10-hour cap under the profiled per-request bounds. Every worker contributes
device seconds to one aggregate ledger; summing controller wall time would
undercount parallel work.

## 4. Shortest staged implementation and test order

This order front-loads the parts that can invalidate the assay without spending
GPU time.

1. **Pure route core.** Implement opaque namespaces, cube expansion, public/
   private projections, route parser/executor, OLD/NEW cuts, two independent
   oracles, entropy/collision/shortcut reports, and deterministic JSON wire.
   Test all 32 excluded worlds/64 tasks plus deliberate one-field corruptions.
2. **Receipt and formation compiler.** Implement action/outcome receipts,
   exact EVENT/LINK span capture, chronology/evidence validation, failed-
   attempt denominators, and the post-S1 no-OLD visibility taint. Test raw
   durability before feedback, no repair, wrong/cross-root evidence, byte
   offsets, and native/mechanistic fork noninterchangeability.
3. **Query-response materializer and controls.** Implement the 17/19 scored
   tables, sorted multi-row blocks, ATOMS/OLD_REPLAY MISS, EVENT_TWIN,
   LINK_PERMUTE, and 20-slot padding. Test duplicate-input contradictions,
   multi-row addresses, parser-disjoint padding, query-shape matching, and
   exact target-token feasibility with a fake tokenizer first.
4. **Real-tokenizer preparation only.** Reuse L2's native template/EOS/mask
   preflight. Search and seal opaque IDs, render all 14 arm corpora, equalize
   stage target tokens, assert 160 singleton sequences and 200 planned steps,
   and emit the immutable request/resource manifest. No model load yet.
5. **Trainer closure.** Add explicit AdamW fields, global clipping, and strict
   numerical receipts. Extend `test_train_adapter_v3.py` with a tiny CPU model
   proving clipping, exact defaults, deterministic 200-step accounting,
   optimizer/RNG/tensor hashes, and nonfinite rejection. Then run one S1 and
   one S2 resource profile only.
6. **Zero-fit text/graph/service harness.** Implement deterministic text
   service, finite READ/ROUTE actor loop, semantic/strict scorers, and exact
   graph/text ceilings. Run all CPU or scripted fake-backend tests before any
   native ceiling.
7. **Native runtime and custody.** Fork L2 prepare/verify/worker/run-stage/
   finalize/custody/collect; add the multi-GPU DAG, per-request LoRA routing,
   stage work ledger, authentic/control taint, rollback, 40-item canary, and
   one reduction. Test every stage with scripted backends, including failure at
   each progression gate, timeout, cleanup, tamper, extra/missing artifact,
   wrong mount, wrong prompt visibility, and no resume/retry.
8. **Native zero-fit gate.** Only after the source snapshot and Linux CPU-test
   receipt are sealed, run the mandatory model ceilings on excluded roots.
   Failure repairs the task/read protocol on fresh excluded roots, not DEV.
9. **Disposable formation root.** Tune only the grammar instruction/parser,
   then freeze both. Never use this child in DEV.
10. **Two-root DEV DAG.** Generate OLD concurrently; launch four S1 fits per
    root; progress only AUTH; perform native and mechanistic reachout; restore
    the sealed pre-outcome state into R0/R1; launch three S2 fits per root;
    quarantine every control; seal once; reduce once.

The fastest coding split is therefore not “one module per scientific arm.” It
is one pure core, one materializer, one shared trainer patch, and one runtime
whose stage table supplies arm-specific data. This keeps the fourteen fits
configuration, not source-code duplication.

## 5. Minimum new test inventory

The existing L2 and trainer suites provide templates, not coverage of this new
world. Before native work, the new tests must explicitly close:

- all cube cardinalities, collision hashes, entropy values, OLD/NEW ambiguity,
  unique FULL routes, and both dependency cuts;
- every named singleton/pairwise projection and its frozen Bayes ceiling;
- EVENT/LINK exact grammar, terminal LF, evidence copying, chronology, span
  offsets, no canonicalization/repair, and malformed denominators;
- initial versus post-S1 visibility, including a proof that OLD bytes cannot
  enter the native S2 prompt and service forks cannot enter lineage;
- query-level one-row and multi-row materialization, deterministic sorting,
  MISS policy, and response-shape-matched controls;
- 20 slots, 8 views, 160 items, exact target tokens, singleton sequences,
  five epoch covers, and 200 actual updates for every arm shape;
- global clipping and the complete numerical receipt without diagnostic state
  mutation;
- READ budget, returned-token budget, actor-token budget, one ROUTE, no
  intermediate feedback, no candidate bank, and raw malformed retention;
- semantic versus strict response scoring and all Section 12 boundaries;
- 40-item common-random canary, rollback identity, and rejection remaining a
  writer failure;
- DAG dependency/order, authentic/control taint, wrong-root isolation, exact
  work/device-time caps, worker cleanup, no retry/resume, final witness, whole-
  root seal, and deterministic replay/reduction.

Most L2 runtime regressions can be copied and parameterized: its current suite
already exercises raw-before-feedback, invalid retention, EOS/mask exposure,
no packing, cumulative branch locality, source pin drift, report
noncontamination, symlink/hardlink rejection, stage/file tamper, missing/late
witnesses, worker timeout/cleanup, no resume, explicit native authorization,
and occupied-GPU refusal.

## 6. What is reusable versus what is scientifically new

Approximately two thirds of the **runtime discipline** is already present,
but most of the **assay semantics** is new:

- Reuse: receipt-chain shape, raw capture/custody, native tokenizer preflight,
  response-only SFT encoding, all-layer LoRA setup, deterministic ordering,
  fresh-process lifecycle, GPU cleanup, write-once stages, seals, replay, and
  reduction discipline.
- New: route cube, two oracles, collision/projection audit, EVENT/LINK parser,
  cross-SLEEP visibility seam, query-level memory materializer, all controls,
  candidate-free reader/actor, route scorer, 40-item canary, authentic/control
  taint graph, and parallel stage DAG.

This is still the shortest implementation path. Building on the old PCFL D0
specification or recurrent-text organism would import more semantic machinery
than it saves. Building on L2 preserves the pieces already proven under native
custody while leaving the route assay small enough to audit exhaustively.

## 7. Go/no-go before source execution

Scientifically, v2.1 needs no further broad architecture round. This memo is
not source-authoring authority; once that authority exists, the single path in
Section 1 is the implementation target. Native/model execution should remain
blocked until all of these are durable:

1. both pure CPU oracles agree on the complete cube and every cut;
2. the projection report has no forbidden deterministic key;
3. the real-tokenizer materializer produces exact token-matched 20-slot arms
   with no target truncation;
4. the trainer manifest proves explicit AdamW/clipping and complete numerical
   receipts at exactly 200 updates;
5. the exact native request/resource inventory fits the 7+10 A40-hour caps;
6. the Linux CPU suite and source/model/tokenizer/environment pins are sealed;
7. custody tests prove no OLD reinjection, no service-fork promotion, no
   control-to-authentic ancestry, and one terminal reduction.

After those gates, the only permitted native order is the protocol's own:
zero-fit ceilings, disposable formation root, then two DEV roots. No Q0,
parenting, rank sweep, or compression result is a prerequisite.

## Inspected implementation evidence

The principal source hashes at this repository cut were:

```text
0bb33988...  organism_v6/l2_public_record_dev.py
213c2a2f...  gpu/astra_l2_public_record_dev.py
7bbf165f...  organism_v6/train_adapter_v3.py
b7e48914...  organism_v6/endogenous_action_relay.py
a05da09e...  organism_v6/semantic_carrier_diagnostic.py
b9fd33c7...  organism_v6/multikey_writer_gateway_simple.py
f63c77f9...  gpu/astra_pairwise_q0_fulldose.py
4d950036...  organism_v6/run_life_v2.py
821471f4...  organism_v6/batch_loop.py
6a4b1ae5...  lands/v03.py
```

The relevant test templates are
`tests/test_l2_public_record_dev.py`,
`tests/test_astra_l2_public_record_dev.py`,
`tests/test_train_adapter_v3.py`,
`tests/test_endogenous_action_relay.py`, and
`tests/test_astra_pairwise_q0_fulldose.py`.
