# RML-G1 GPU runner v2 addendum: canonical single lane

**Date:** 2026-09-04  
**Status:** narrow advisory only. No science implementation, model/network/GPU
call, sync, remote launch, or ratification was performed.

## Supersession and present authority

This addendum supersedes the following parts of
`20260904_rml_g1_gpu_runner_exact_design_v1.md`:

1. every statement that makes the unratified G1A v1 amendment the intended
   repair;
2. every statement that requires empirical P `ATOMS_REC` success exactly 0/2;
3. the optional two-lane 8xA40 schedule and its eight-GPU resource accounting;
4. the over-factored GPU file layout.

The rest of v1's exact chat/token, raw-output, no-retry, fresh-process,
intervention, freeze/review, marker, and claim-firewall requirements remains
advisory input, subject to the narrower implementation surface below.

The intended repair is now the proposed
`chg_20260904_rml_g1_control_validity_repair_v2` change, whose exact current
change bytes have SHA-256
`af878817226180556d03059e0c00a0dc4559df1d579f8b04cc0ca9fca4f5b0a8`.
It explicitly supersedes G1A v1. It is not execution authority: its intake is
currently `collecting_interpretations`, `human_required: true`, and
`implementation_authorized: false`. GPU implementation and launch remain
blocked until a final adjudicated v2 consensus and exact human ratification
exist, and the final bytes resolve the selector, stable renderer/dependency
closure, and two-layer scope-allowlist questions raised by the systems
interpretation.

The original G1 consensus and ratification remain the base authority at:

```text
consensus     1c27cbe6ac3adda14078f2cdbfe62785ce7161b4ae35c2fb96b899b40da53cb9
ratification  fa6dd830a67ba03dd336945e74759ae58ce075de201573c4037798cba2e4ab53
```

## Repaired P-ATOMS rule

The production certifier must first establish, over one shared deterministic
policy on complete byte-exact authorized visible histories:

```text
K_NONE     = 1/4
K_P_ATOMS  = 1/2
```

Both registered P-ATOMS trajectories must have `SCIENTIFIC_VALID` outcomes.
Their observed pinned-model successes are then classified exactly as:

```text
0/2  STRICT_CONTROL_CLEAN                  construct-control passes
1/2  CAPACITY_ATTAINING_QUALIFIED_CONTROL  construct-control passes
2/2  ABOVE_CERTIFIED_CAPACITY_STOP         gate fails; no retry
```

The 1/2 branch sets `strict_control_clean=false` and
`positive_method_credit=false`. It does not weaken GOLD 4/4, NONE <=1/4,
minimal timely citation, AUTH/SHAM/CUT/TWIN 2/2, typed validity, or any claim
firewall. Neither 0/2 nor 1/2 is statistical or paper evidence. A missing,
model-invalid, infrastructure/resource-failed, dependency-cancelled, or
zero-attempt P row satisfies neither allowed outcome. A 2/2 result is an
above-capacity contradiction requiring certificate, same-policy, reset,
determinism, provenance, and serving investigation; it is not automatically
labeled leakage and does not authorize a rerun.

Do not score P-ATOMS early to change later dispatch. Execute and dispose the
unchanged roster, freeze all raw evidence, then score in the no-provider
process. This preserves the original order and prevents scorer/capacity output
from controlling intervention execution or timing. A final 2/2 result is a
failed diagnostic, not a reason to erase or regenerate the remaining cells.

## Stable Stage-A context recovery

The unavailable original Stage-A report SHA-256
`346bd091e9d037b1e51c8ed735ba5ecfbee50a42d10988d02ebc28c87532855b`
must remain disclosed as unavailable. It must not be silently replaced or
claimed to have been reconstructed.

The v2 packet instead binds all of the following:

- the current exact `rml_d0/stage_a_report.json`, SHA-256
  `e36be91f7244dd483a274a1cf350e383011a707d053a02fe753c6f982e9b47c0`;
- canonical JSON after deleting exactly
  `/gate_values/resource_record` and `/resource_hash`, rendered as the final
  adjudicated compact sorted-key UTF-8 convention plus one durable-record LF;
- expected stable-projection SHA-256
  `c496535e08b72d9eb1ff0ba8f6bca4b1f42545a855a6d368e479e99a76a12b0d`
  and byte length `110366`;
- the removed volatile resource receipt separately, with its own exact hash;
- a mechanically closed transitive D0 semantic dependency manifest rooted at
  Stage-A generation and every D0 authority consumed by G1. The five hashes in
  `governance_context_recovery.md` are mandatory minimum entries, not an
  assertion of complete closure;
- a fresh 16/16 D0 test result and mutations proving volatile wall/RSS changes
  preserve the stable projection while any semantic field, exclusion,
  renderer, newline, code, or dependency change fails.

This recovery is amendment-only governance work. None of the removed volatile
values may enter stores, selection, capacity, prompts, model service, G1
scoring, dispatch order, or timing decisions.

## Scientifically safest execution shape

Use one strict canonical lane only:

```text
CUDA_VISIBLE_DEVICES=0,1,2,3
tensor_parallel_size=4
one trajectory subprocess at a time
fresh vLLM/model process for every trajectory
```

GPUs 4--7 are not visible to the runner, are not fallback capacity, do not
create a second lane, and are irrelevant to G1 resource accounting. No
scientific process may change its visible device set after canary.

Dispatch in the exact existing `build_roster()` order, without concurrency:

```text
 0 GOLD_REC:J_H             9 ATOMS_REC:P_TWIN
 1 GOLD_REC:J_TWIN         10 AUTH_REPLAY:J_H
 2 GOLD_REC:P_H            11 AUTH_REPLAY:P_H
 3 GOLD_REC:P_TWIN         12 SHAM_REC:J_H
 4 NONE_REC:J_H            13 SHAM_REC:P_H
 5 NONE_REC:J_TWIN         14 CUT_REC:J_H
 6 NONE_REC:P_H            15 CUT_REC:P_H
 7 NONE_REC:P_TWIN         16 TWIN_REC:J_H
 8 ATOMS_REC:P_H           17 TWIN_REC:P_H
```

Each subprocess owns all remaining sequential slots for exactly that one
trajectory, then fully exits with no CUDA/vLLM descendants before the next
ordinal starts. Prefix caching is disabled; active sequences are zero before
and after every call; each call receives the complete rendered history; every
trajectory gets a new reader, machine, scheduler, KV arena, CUDA context, and
engine. The canary uses the same selected four GPUs in its own fresh process
and must fully exit before ordinal 0 starts.

This path removes the v1 order ambiguity. Ratified R09 hash-binds target and
condition order; a single lane literally realizes that total order. Parallel
completion labels, logical-order reinterpretation, cross-lane abort races, and
cross-lane parent dependencies disappear.

## Prospective three-hour feasibility

The one-lane choice makes wall time, not A40-hours, the binding resource.
Conservatively charge the selected four GPUs for the entire canary-start to
raw-seal interval:

```text
at 3 hours: 4 GPUs * 3 hours = 12 A40-GPU-hours < 24 A40-GPU-hours
```

Unused GPUs do not count. The 24-GPU-hour ceiling therefore has 2x slack, but
the unchanged 10,800-second wall ceiling has none. The actual path performs 19
fresh engine loads inside that wall: one canary load plus 18 scientific
trajectory loads. It then performs at most 234 sequential deterministic calls.
Fresh-load time is the dominant uncertainty.

Let:

```text
C0 = observed canary process wall time, including its load, call, shutdown,
     descendant exit, and selected-GPU-clean verification
L  = mean future trajectory load + final shutdown/reset time
Q  = mean scientific call time
S  = fixed finalization reserve, exactly 600 seconds
```

A necessary planning inequality is:

```text
C0 + 18*L + 234*Q + S <= 10,800 seconds
```

For illustration only, if `C0=180s`, the largest possible mean call time after
different fresh-load costs is:

| Fresh load/reset `L` | Maximum mean call `Q` |
|---:|---:|
| 60 s | 38.2 s |
| 120 s | 33.6 s |
| 180 s | 29.0 s |
| 300 s | 19.7 s |
| 480 s | 5.9 s |

Thus the run is prospectively plausible if a local-NVMe TP=4 fresh load is a
few minutes and the recurrent calls remain well below tens of seconds, but the
repository contains no A40 measurement proving either premise. Eighteen loads
can fit; they are not presently certified to fit. A load/reset near nine
minutes makes the wall infeasible even before meaningful call time. The
decisive current feasibility verdict is **conditional GO only after the single
canary passes the estimator below; otherwise NO-GO with no scientific call**.

### One-canary reducing estimator

The one target-disjoint canary must be predeclared, schema-valid, use identical
model/tokenizer/chat/decoding/TP/reset bytes, and provide timing telemetry for:

```text
Lc = process spawn through engine ready
Rc = post-receipt engine shutdown through descendant/GPU-clean proof
Fc = fixed request scheduling/receipt overhead
Pc = observed prefill tokens per second
Dc = observed decode tokens per second after the first token
Ic = exact rendered canary input tokens
Oc = exact generated canary tokens
```

To support extrapolation, its frozen target-independent padding must make
`Ic >= 8192`, and a valid receipt must contain `Oc >= 16`. It remains one
non-scientific grammar canary and consumes zero registered opportunities. If
either bound or the separated vLLM timing telemetry is absent, the estimate is
NO-GO; do not infer rates from total wall time alone.

Use an exact 2x adverse derating:

```text
L_bound    = 2 * (Lc + Rc)
call_bound = 2 * (Fc + 16384/Pc + 256/Dc)
E          = C0 + 18*L_bound + 234*call_bound + 600
```

All divisions use upward rounding to whole milliseconds. `Pc` and `Dc` must be
positive finite values computed from exact token IDs and monotonic vLLM timing;
otherwise NO-GO. The per-call maxima deliberately equal the whole-gate maxima
when multiplied by 234: 3,833,856 input and 59,904 output tokens.

Proceed to ordinal 0 only if `E <= 10,800`. At that moment freeze:

```text
seal_deadline     = canary_start_monotonic + E
dispatch_deadline = seal_deadline - 600 seconds
gpu_hour_limit    = 4 * E / 3600   # necessarily <= 12, never raised toward 24
```

The watchdog stops dispatch at `dispatch_deadline` and kills/marks the current
attempt resource-failed at `seal_deadline`; all undispatched identities receive
the ratified global cancellation. Actual per-call/trajectory/gate token, byte,
artifact, and cost checks still apply. A passing estimate is not evidence the
run will fit and does not relax any gate. A failed estimate cannot cause a
second canary, two-lane execution, resident-engine reuse, smaller prompts,
truncation, fewer registered cells, changed max tokens, fallback runtime, or a
longer clock. This estimator can only decline or shorten the already authorized
envelope.

The 2x estimator is deliberately conservative but not a mathematical runtime
upper bound from one observation. The hard watchdog remains authoritative. If
final adjudication requires an empirical confidence claim rather than this
one-way operational screen, one canary is insufficient and new authority is
needed; do not manufacture a confidence interval from one load/call.

## Minimum code surface

V1 split the path into six Python modules, a new artifact schema, three shell
wrappers, and a separate canary file. That is unnecessary for a one-lane run.
The minimum original-scope GPU addition is:

| File | Required contents |
|---|---|
| `rml_stage_b/gpu_runner.py` | One module with lazy-imported subcommands `inspect-runtime`, `canary`, `trajectory`, `run`, `score`, and `status`. The non-CUDA coordinator owns exact roster order, resource clock, one-shot markers, immutable raw/opportunity files, parent-derived mask preparation, global abort, and final seal. The child owns exact chat/token rendering and one TP=4 vLLM engine for one canary or trajectory. `score` runs in a new process and imports no vLLM/provider code. Reuse `model_provider_boundary.py`, `io.py`, `freeze.py`, `freeze_closure.py`, and `review_binding.py`; do not wrap `remote_job.run_job()`. Embed and hash the fixed canary bytes here rather than adding another asset. |
| `rml_stage_b/tests/test_g1_gpu_runner.py` | CPU fake-provider tests of all 18 ordinals/234 identities, exact state/opportunity binding, chat/token counts, raw receipts, terminal/dependency/global cancellation, resource durability, one-shot crash refusal, canary estimator boundaries, and strict one-lane process sequencing. |
| `research_loop/workflows/rml_stage_b_gold_action_fast_v1.remote.json` | Frozen inputs, exact commands, timeouts, required fresh artifacts, and the sole A40 remote route. |
| `gpu/a40_rml_g1.sh` | One small `sync`, `start`, `status`, and `pull` wrapper using the existing `a40_ssh.sh` host. Sync excludes job/output/model-cache directories; start is exclusive; pull requires one verified terminal marker. |

Do not add v1's separate `gpu_contract.py`, `gpu_interventions.py`,
`vllm_provider.py`, `run_gpu_trajectory.py`, `run_gpu_gate.py`,
`gpu_remote_job.py`, new artifact-schema bundle, or three separate A40 scripts
unless implementation proves a concrete test or import-cycle need. Exact
dataclasses and validators can remain private in `gpu_runner.py`; the existing
operation schema remains the model-output schema.

Small changes to existing Stage-B files are still necessary. They must be
typed by authority rather than mixed into “the GPU work.”

### Original-scope mandatory closure

These implement requirements already present in ratified G1 and do not change
scientific meaning:

- `machine.py`: bind opportunity trajectory/target/slot/phase to the current
  machine; enforce strict ordinal/slot order; accept exact tokenizer accounting
  and finish reason; durably retain a resource-failed current event before
  raising or cancelling.
- `reducer.py`: independently replay serialized actions through unchanged D0,
  validate every stored transition, and tie each decisive citation to its
  predeclared action-support boundary rather than allowing final-COMMIT
  citation laundering.
- `memory.py` and `runner.py`: require pretarget seal capability before target
  selection; use exact pinned-tokenizer row counts; construct SHAM/CUT from the
  frozen parent's actually returned/cited handles and certified source-only
  metadata, never `decisive_handles(TargetCase, ...)` in the GPU path.
- `runtime.py` and `review.py`: recompute real closure/file/model/tokenizer/chat/
  stop/runtime/reset hashes and verify persisted distinct-role review bindings;
  do not accept arbitrary hash-looking strings or a self-attested
  `backend_deterministic` Boolean.
- `run_cpu_preflight.py` and existing tests: distinguish local scripted checks
  from satisfied GPU prerequisites and close every original T01--T06
  counterexample. Keep prompt, model, decoding, roster/order, resources,
  interventions, typed failure meanings, retry policy, and claims unchanged.

### Amendment-only work

Only finally ratified v2 authority may add or change:

- a complete shared-visible-history capacity certificate and a separately
  implemented upper-bound checker, including the exact selector commitment and
  no-feedback edge;
- `reducer.py` fields and predicates for P-ATOMS 0/2 strict-clean, 1/2
  capacity-attaining qualified, and 2/2 above-capacity stop, with no positive
  credit;
- the exact stable Stage-A projection/volatile-receipt/dependency-closure
  artifact and its mutation tests;
- affirmative per-row source lineage, evaluator-only capability isolation, the
  store-versus-authorized-public-interface byte partition, and their tests;
- a machine-readable v2 semantic allowlist against original G1, separately
  listing behavior-preserving original-scope conformance repairs.

Do not classify citation replay, opportunity binding, durable resource
failure, exact tokenization, pretarget ordering, or the missing GPU runner as
new v2 scientific semantics. Conversely, do not use “conformance repair” to
change the P rule, selector, capacity domain, target, prompt, order, or claim.

## One-shot remote and evidence path

The single `gpu_runner.py run` command must verify both ratified intakes,
stable-context/capacity/source artifacts, the freeze closure, two distinct
pre-GPU review bindings, the selected four A40 UUIDs, local-only pinned model
files, and absence of a prior run marker before it creates `started.json`.
It then runs the canary and reducing estimate once, followed by ordinals 0--17
in order. Every attempted call preserves exact request/config/token IDs/raw
response/finish reason/receipt before transition; every terminal suffix and
constructive dependency failure receives zero-attempt typed rows; any
infrastructure/resource failure aborts and cancels globally without retry.

`done.json` means the 234-row ledger and immutable raw/scored seals were
completed, even if a scientific predicate failed. `failed.json` is reserved
for infrastructure/resource/sealing failure. `started.json` without a terminal
marker after process loss is permanently failed and cannot resume. Status or
PID is never completion evidence. Pull only a terminal hash-verified directory,
then require fresh independent and author-side post-run reviews bound to the
immutable output seal before releasing even the narrow allowed result string.

## Decisive risk statement

The one-lane plan is scientifically safer and removes the only serious
ordering ambiguity in v1. Its 24-A40-hour budget is ample; its three-hour wall
is the sole compute risk. The risk is credible because strict process freshness
requires 19 total Qwen-32B TP=4 loads, while no repository artifact measures
fresh A40 load, long-context prefill, or decode latency. The run should be
considered feasible-but-unproven, not GPU-ready. A single maximum-envelope,
target-disjoint canary with the frozen 2x reducing estimate is the earliest
permitted decisive measurement. Until final v2 ratification, original-scope
closure, exact reviews, and that estimate all pass, the only compliant action
is no launch.
