# CompilerGym LLVM lifetime protocol candidate — Experience Model v6

Status: specification candidate only. This file authorizes no installation,
download, benchmark execution, model call, training, GPU use, or scientific
claim. It is intended to close the execution choices left open by the v1
KernelBench candidate. Any byte that differs from this protocol requires a new
bounded review and ratification.

## 1. Question and claim boundary

The first causal question is deliberately narrow:

> With the same frozen model, loop, public observations, action opportunities,
> and logical budgets, does a deterministic sleep compiler that writes one
> life-local LoRA from public LLVM action/outcome transitions improve later
> action on sealed, related-but-nonduplicate LLVM programs?

There are exactly two primary agents:

* `HARNESS`: the frozen base model and the fixed context/action loop. It has
  no trainable or persistent adaptive parameters.
* `EXPERIENTIAL`: the byte-identical harness plus one LoRA, initialized null
  for each life, rebuilt at fixed sleeps, and mounted on the same model during
  later ORIENT and THINK_ACT calls.

The primary scout comparison is `EXPERIENTIAL - HARNESS` at held-out action
quality. `ADAPTER_OFF` is a within-life causal fork from an authentic sealed
checkpoint; `SHUFFLED` is a separate equal-row/token training control; `TEXT`
is a same-corpus transport diagnostic. These are different estimands and must
not be pooled as if they were independent on-policy lives.

A positive scout is only a short-horizon outcome-grounded adapter mechanism
signal. It is not evidence for consciousness, creativity, general
intelligence, universal continual learning, LoRA superiority, abstraction, or
continued improvement after context saturation. A paper-ready lifetime claim
requires the confirmation protocol in section 15.

## 2. Facts fixed before any fit work

The candidate substrate is the official CompilerGym LLVM environment, release
`0.2.5`, with its LLVM 10 dependency. The repository is recorded as archived
on 2026-05-27. The first objective is the official deterministic,
platform-independent `IrInstructionCount` reward; wall-clock timing is a
resource diagnostic only, not the primary reward. These facts are inherited
from the current discussion context and must be rechecked against the pinned
local bytes before use.

CompilerGym 0.2.5 is an external dependency, not a benchmark to repair. The
agent may add only an environment adapter, context projection, ledger, sleep
compiler, trainer, and test harness. It may not alter task programs, action
semantics, LLVM passes, reward code, reference implementations, dataset
membership, or evaluation logic.

The following must be hash-bound in a run manifest before implementation is
considered complete:

* the exact 0.2.5 source/wheel bytes and license;
* Python, PyTorch, tokenizer, model, CUDA/driver (if applicable), LLVM 10,
  and every dependency version and hash;
* the official CompilerGym factory/API invocation and observation/action
  projection;
* the base-model and tokenizer revision, bootstrap prompt/schema, parser,
  attention-mask code, and all seeds;
* the selected task manifest and its static split/dedup report;
* the sleep row schema, compiler, LoRA configuration, optimizer lifecycle,
  checkpoint format, metric code, and analysis code.

If any byte above is unavailable locally, the work stops at specification;
the missing byte is not guessed from a model name or fetched from the network.

## 3. Static and offline installation canary

This canary is a gate, not part of the scout. It is run only later, in a
disposable environment, from already sealed local artifacts. No network index,
package mirror, git remote, or unpinned system installation is permitted.

### 3.1 Static gate (no process may import the package)

1. Verify the SHA-256 of the 0.2.5 source/wheel and LLVM 10 artifact manifest.
   Reject an unhashable source tree, a post-0.2.5 checkout, or a patched/forked
   benchmark tree.
2. Resolve the complete dependency closure from the local wheelhouse and
   record Python/platform/ABI constraints. A dependency that is not already
   present is `NO_LOCAL_ARTIFACT`, not an invitation to download.
3. Inspect the official package registry and manifests to enumerate LLVM task
   datasets, program IDs, public observations, legal actions, reset semantics,
   reward names, and any hidden/reference files. Record source paths and hashes.
4. Statically inspect the environment adapter to verify that the only primary
   reward requested is `IrInstructionCount`, that it is derived from LLVM IR
   instruction count, and that no host timing, GPU timing, hidden answer, or
   scorer field reaches the model-visible observation.
5. Generate the candidate catalog and split report using only public static
   metadata. No model output, reward, optimized program, hidden test, or
   target score may influence task selection.
6. Verify that the package and selected data can be invoked without writing
   into the pinned source tree or altering benchmark/scorer bytes. Hash the
   source before and after the dry structural inspection.

Static rejection is mandatory if LLVM 10 or the official release cannot be
resolved, the catalog is not available from sealed local bytes, legal action
semantics are unclear, or no split satisfying section 4 can be constructed.

### 3.2 Offline install and semantic canary (later, separately authorized)

In a fresh disposable environment, install only from the sealed wheelhouse,
equivalent to:

```text
python -m pip install --no-index --find-links=<SEALED_WHEELHOUSE> compilergym==0.2.5
```

The exact command, environment image, and resulting lockfile are hashed; a
package resolver may not silently substitute versions. A pinned canary script
then performs, on three catalog programs selected before execution:

1. import the official package and construct the LLVM environment through the
   official factory;
2. reset twice with the same seed and assert byte-identical public initial
   observations and action-space metadata;
3. replay a fixed legal action trace twice from clean processes and assert
   byte-identical observations, terminal flags, and `IrInstructionCount`
   rewards;
4. submit one deliberately malformed/illegal action and assert that the
   official environment marks it invalid or fails it without granting a valid
   improvement;
5. exercise truncation, terminal stop, environment exception, and
   crash-before/after-ledger-seal paths; and
6. compare pre/post source, task, reward, and scorer hashes.

The canary fails on any nondeterministic reward/observation, unavailable LLVM
10 operation, silent invalid-action acceptance, hidden-data exposure, source
mutation, unrecoverable reset, or unbounded runtime. A failed canary rejects
CompilerGym for this change. It does not license patching CompilerGym or
substituting another benchmark.

## 4. Dataset discovery and related/nonduplicate split gate

The local notes support CompilerGym as a candidate substrate but do not support
a named CompilerGym dataset roster. Therefore this protocol does **not**
preselect a name such as `cBench`, `CHStone`, or `AnghaBench`. The official
0.2.5 catalog discovery in section 3 is a hard gate. If it cannot produce the
required strata, the result is `DATASET_DISCOVERY_FAIL` and a new architecture
intake is required.

The selected catalog must contain at least 32 programs: 24 acquisition and 8
held-out targets, with at least four independently identifiable public
families/feature groups. The catalog report must show, without reward or
solution access:

* at least four acquisition programs in each of three groups;
* four held-out near-family targets whose acquisition group has been seen but
  whose normalized graph/shape regime is not duplicated;
* four held-out cross-group or opposite-condition targets that require a
  combination or transfer of separately seen public structural features; and
* at least two spare candidates in every stratum for deterministic replacement
  before sealing.

If official metadata supplies family/condition labels, they may be used only
after their provenance and target blindness are recorded. Otherwise define
groups mechanically from public LLVM IR using a frozen canonicalizer:
strip identifiers, debug data, source paths, and constants where legal;
canonicalize commutative operand order; hash the module/function call graph,
CFG Weisfeiler-Lehman features, opcode/type histograms, memory-operation
categories, loop-depth bins, and data-layout metadata. This feature extractor
is a relation aid, never a target answer.

Deduplication is layered and applied before splitting:

1. exact source/program and canonical-IR hash duplicates;
2. normalized module/function graph isomorphs;
3. same opcode/CFG/type/layout/loop-shape signature with only identifier or
   constant renaming;
4. nearest-neighbor pairs above a frozen structural-similarity threshold; and
5. identical action-grammar/condition/shape regimes where the target can be
   solved by copying a source patch.

The report must include the rejected-neighbor list and prove that no held-out
program or its solution/reference/hidden distribution occurs in acquisition
records, prompts, adapter rows, text stores, caches, or bootstrap files.
Task IDs, the group algorithm, all thresholds, and the final 24/8 manifest are
sealed before the first model call. Task ordering is three fixed blocks of
eight acquisition programs, counterbalanced across lives; the held-out panel
is never used for sleep selection or training.

## 5. One loop and context-state contract

`ORIENT` and `THINK_ACT` are invocation states of one recurrent loop and call
the same frozen model, tokenizer, bootstrap family, and (for treatment) the
same mounted LoRA. There is no learned scheduler, critic, planner, dreamer,
router, second adapter, or base-model update.

Every invocation reconstructs a bounded packet with a hard `C = 4096` input
token cap under the pinned tokenizer:

```text
ANCHOR       immutable bootstrap, objective, action grammar, safety rules
CLOCK        logical calls/tokens/actions remaining; no wall-clock or condition ID
LIFE         opaque life ID, task ID, checkpoint, public progress
FOCUS        current subgoal and selected context request
ENV          current public LLVM observation, legal action summary, outcomes
RECALLED     bounded life-memory result or TEXT diagnostic result
RECENT_TAIL  verbatim public suffix, maximum 512 tokens
```

`ORIENT` chooses a typed focus and at most two bounded recalled records;
`THINK_ACT` emits at most one typed operation: `APPLY(pass)`, `INSPECT`,
`REFLECT_PUBLIC`, or `STOP`. Only `APPLY` changes the CompilerGym state.
Private rationale text is never a target, endpoint, or memory authority.
Every field is reconstructed from an allowlist. The model cannot forge the
clock, read hidden correctness/reference data, read future targets, or access
the full lifetime ledger.

Each acquisition or evaluation task has exactly eight ORIENT/THINK_ACT pairs,
maximum 256 generated tokens per call, one legal environment action per pair,
and no hidden retry. Malformed, repeated, timeout, and invalid operations
consume the pair. The fixed logical budgets are identical across conditions:
8 pairs, 16 model calls, 4,096 input-token cap per call, 4,096 output tokens
per task, and one environment action per pair. External wall time, peak memory,
and CPU/GPU utilization are logged out-of-band; they are never shown to the
model and never used to stop a task early.

## 6. Public acquisition ledger and sleep rows

After every operation append an immutable public record containing:

```text
life/task/checkpoint, public-state hash, prior observation hash,
selected focus/recalled-record IDs, typed operation and normalized arguments,
public observation, official IrInstructionCount, validity/terminal status,
logical resource counters, and next-state hash when available
```

No hidden test case, reference implementation, scorer internals, future target,
private rationale, or evaluation outcome enters the acquisition ledger.

The first scout uses a deterministic compiler with no model calls. To make the
outcome shuffle identifiable, row eligibility is outcome-independent:

* for each adjacent public transition with a known next operation, emit one
  `NEXT_OP` candidate row whose input is `(pre_state, typed_action,
  public_outcome_bucket)` and whose loss-bearing target is the next typed
  operation;
* emit one terminal `STOP` row for each task; and
* emit fixed bootstrap/instruction-preservation rows at every sleep.

The public outcome bucket is a deterministic rendering of the official result:
`IMPROVED`, `UNCHANGED`, `WORSE`, `INVALID`, `TIMEOUT`, or `TERMINAL`, with the
raw instruction count retained only in the audit record. The compiler never
selects a row because it improved. It cannot train on its own free-form
hypothesis; `REFLECT_PUBLIC` text is audit-only. This is a modest
outcome-conditioned next-operation objective, not a claim that all useful
credit assignment has been solved.

For each sleep, select rows by a predeclared round-robin over task strata and
chronological order, independent of outcome values. Deduplicate exact rows,
cap at 512 cumulative rows, and use a fixed 50:50 old/new replay quota when
both exist. If a quota has too few rows, pad with fixed bootstrap rows rather
than duplicate useful experience. Render exactly four views per row (canonical
state, reordered public fields, outcome wording variant, and terse state),
with only the typed-operation target tokens unmasked. The view mapping is
fixed and provenance IDs remain audit-only.

At checkpoints 8, 16, and 24, rebuild the cumulative adapter from the clean
base with a reset optimizer. Use this frozen scout recipe:

```text
LoRA rank=64, alpha=128, dropout=0.05
target modules=q_proj,k_proj,v_proj,o_proj
bf16 forward/backward where supported; gradient clip=1.0
AdamW, learning rate=2e-4, batch=32, max sequence length=512
exactly 24 effective touches per retained row; no early stopping/retry
```

Optimizer moments, trainer RNG, caches, and temporary files die at every sleep;
only the serialized LoRA bytes persist within that life. A trainer receipt
records rows, views, masks, tokens, steps, seeds, adapter hash, and failure
state. Numerical overflow, missing rows, or a crash seals the cell as failed;
content-dependent repair is forbidden.

## 7. Scout life, checkpoints, and independent replication

The minimal meaningful scout has three independent lives (`L0`, `L1`, `L2`),
not three checkpoints counted as lives. Each starts from the same clean base and
null adapter, uses one of three presealed acquisition permutations, and has no
shared optimizer, cache, filesystem, retrieval index, RNG, or public progress.
Each life traverses 24 acquisition programs in blocks of eight. Sleep occurs
after each block and evaluation checkpoints are `0, 8, 16, 24`.

The static fit report must verify that the canonical public ledger reaches at
least `2C` tokens by checkpoint 24 and crosses `C` before the final block. If
not, the run may be labelled only a wiring/mechanism assay; it cannot support a
post-context observation, and no prompt or C value may be tuned after seeing
results.

At every checkpoint, freeze acquisition and fork a clean evaluation process.
Evaluate all eight held-out targets in a fixed, sealed counterbalanced order
under `HARNESS`, authentic `EXPERIENTIAL`, and `ADAPTER_OFF`. Evaluate
`SHUFFLED` from its separately trained checkpoint using identical row/token
budgets. Run `TEXT` only as a final-checkpoint diagnostic using the identical
authentic compiled rows through a bounded target-blind text reader and no
LoRA; it is not a causal replacement for HARNESS.

For life specificity, perform reciprocal opaque final-checkpoint swaps:
`L0` adapter on `L1`'s evaluation fork and `L1` on `L0`, with task IDs and
origin metadata hidden from the model. The swap is diagnostic and never feeds
back into acquisition. A missing or failed swap is reported, not silently
removed.

## 8. Strong harness and sterile evaluation controls

The harness control receives the same anchor, task projection, context cap,
logical counters, 16 calls, 8 actions, parser, and failure semantics. It may
use the current task's public tail but has no lifetime text/adapter. A sham
write may execute compiler/trainer work and pay its tokens/steps while never
mounting an adapter; report it separately if included. The scout must not call
the sham a strong ordinary-agent baseline.

Every evaluation fork is cold-started from an allowlisted base/model image and
sealed checkpoint. It has fresh KV/prefix caches, RNG stream, workspace,
retrieval state, process environment, compiler/LLVM cache, shell history, and
temporary directory. Evaluation can read only its target packet and assigned
adapter/text diagnostic. Its outcomes, generated files, compiler artifacts,
timings, and logs are quarantined and destroyed or cryptographically denied
before acquisition resumes. Interrupted unsealed calls are indeterminate and
are not regenerated under the same identity.

The adapter-only cold-load test starts a fresh process from the clean base and
serialized adapter bytes, reproduces the same final checkpoint, and compares
it with the in-process fork. This locates any treatment effect in declared
adapter bytes rather than model-server state. All conditions hide condition
names, adapter origin, row counts, checkpoint labels, elapsed wall time, cache
warmth, and retry status. Logical counters are identical by schedule.

## 9. Held-out action metrics

CompilerGym's instruction count is the objective. For target `i`, let `I0` be
the count immediately after reset and `Ik` the count after operation `k`.
Lower is better. Invalid or nonterminally failed submissions have zero valid
score. Define:

```text
g_i,k = 1[any valid state through k]
        * max(0, I0 - min(valid counts through k)) / max(1, I0)
```

An invalid or worse later action therefore cannot erase a previously verified
best state; its failure is still retained in the validity and repeat-rate
diagnostics. A target with no valid state has `g_i,k = 0` for every `k`.

The target score is `G_i = mean_k(g_i,k)` over the eight fixed operations;
`G_i^best = max_k(g_i,k)` and `G_i^first` (gain after the first valid action)
are secondary diagnostics. `AUC` is the trapezoidal area of the checkpoint
mean `G_i^best` curve against cumulative acquisition tokens, including the
zero-experience checkpoint. No target's later score can influence training.

Report separately: validity rate, instruction-count gain, first-action gain,
operations to first valid improvement, stop/invalid/repeat rate, text versus
adapter transport, same-family versus cross-group/opposite-condition transfer,
early-panel retention, adapter bytes, training tokens/steps, model tokens,
environment calls, wall time, peak memory, and crashes. Free-form thought or
hypothesis similarity is never scored.

The primary scout contrasts are predeclared as paired life means:

```text
D_off  = G(EXPERIENTIAL_final) - G(ADAPTER_OFF_final)
D_shuf = G(EXPERIENTIAL_final) - G(SHUFFLED_final)
D_base = G(EXPERIENTIAL_final) - G(HARNESS_final)
```

Report both all-target and cross-group/opposite-condition values. Do not pool
the eight targets as eight independent replications; targets are repeated
within a life.

## 10. Slope, AUC, uncertainty, and scout decision rule

For each life, fit a preregistered descriptive line to checkpoint means versus
`x = cumulative acquisition tokens / C`. Also fit a piecewise exploratory line
with a knot at `x=1`; the post-context slope is undefined if a life never
crosses `C`. The confirmation estimator is a hierarchical model with fixed
condition, `x`, condition-by-x interaction, pre/post-context indicator, and
condition-by-post-context interaction; life is the replication cluster and
target is a repeated-measure random effect. Bootstrap or permutation intervals
resample whole lives, never target rows or checkpoints.

The three-life scout reports point estimates and life-clustered intervals only;
it uses no p-value and no population claim. A scout `MECHANISM_GO` requires all
of the following, frozen before output inspection:

1. no static/install/sterility/budget/leakage failure;
2. `D_off >= 0.05` and `D_shuf >= 0.05` at the final checkpoint in at least
   two of three lives, with pooled point estimates positive;
3. authentic validity is not lower than `HARNESS` by more than 0.05, and the
   cross-group/opposite-condition contrast is positive in at least two lives;
4. the authentic curve has positive final-minus-initial `G^best` in at least
   two lives; and
5. `TEXT` and wrong-life diagnostics are reported, even if they explain or
   eliminate the apparent gain.

Failure is `STOP_FOR_THIS_RECIPE`; it forbids tuning prompts, rows, split,
rank, thresholds, or life order on the same lives. A clean causal signal with
no text/external-memory comparison is `MECHANISM_GO_ONLY`, never paper-ready.

## 11. Information and resource accounting

The ledger reports every model input/output token, context token count, model
call, CompilerGym action, reward observation, sleep row/view/touch, optimizer
step, adapter byte, retrieval/text token, wall-clock duration, peak memory,
crash, and retry. Treatment and shuffled conditions have identical row counts,
views, effective touches, trainer steps, and logical task/action budgets.

No condition receives a larger visible clock. Since adapter loading and text
retrieval have different physical latency, report both natural wall-time and a
compute-normalized view, but do not expose elapsed time to the model or use it
as a stopping criterion. If a condition has a failed call, it consumes the
scheduled budget and is scored missing/invalid under the predeclared rule; it
is not regenerated for convenience.

## 12. Pre-scout rejection checklist

Reject CompilerGym for this protocol if any item holds:

* 0.2.5/LLVM 10/dependency bytes are missing, altered, or only network
  retrievable;
* official reset/replay is nondeterministic, `IrInstructionCount` is absent or
  platform-dependent, or illegal actions can earn reward;
* the official catalog cannot provide 24/8 sealed related/nonduplicate tasks,
  four public structural groups, both transfer strata, and spare candidates;
* graph/shape/action-solution deduplication or future-target leakage cannot be
  audited before model calls;
* the frozen task/action projection, base model, tokenizer, bootstrap, row
  schema, LoRA recipe, metrics, or analysis bytes remain unspecified;
* the harness cannot deny evaluation writes, cache/RNG/file carryover, or
  adapter-origin visibility; or
* the canary leaves no objective headroom above floor or below ceiling.

Any rejection is terminal for this candidate. Benchmark repair, dataset
curation using outcomes, or replacement with KernelBench/another gym requires a
new architecture change and review.

## 13. What the scout can and cannot establish

If `MECHANISM_GO` survives all audits, the strongest defensible statement is:

> In three bounded, independently reset CompilerGym LLVM lives, under one
> pinned recipe, public action/outcome transitions compiled into a life-local
> adapter produced a directional held-out action signal that disappeared or
> weakened under adapter removal and outcome binding shuffle.

Even that statement is limited by base-model pretraining exposure, the fixed
deck, three-life sample, and short horizon. It does not establish that the
agent learned a human-like concept, that the adapter is superior to text,
that ordinary agents saturate, or that a flywheel compounds indefinitely.

## 14. Confirmation protocol (paper-ready only)

Confirmation requires a new hash-bound preregistration after a scout signal,
fresh task assignments, fresh human authorization, and independent review. It
must use at least 12 independent lives, with life as the replication unit, at
least four held-out checkpoints strictly after `C` and at least two additional
checkpoints beyond `2C`. The acquisition stream must reach `8C` so a sustained
post-context slope is estimable; repeated filler is disallowed.

Confirmation must include, under matched visible action/thought/context and
consolidation budgets:

* no persistent memory, honest recent/full/native-long-context control, raw
  episodic RAG, organized/linked memory, reflection/lesson memory, direct-QA
  LoRA, raw-trajectory LoRA, same-corpus text, authentic LoRA,
  outcome-shuffled LoRA, adapter-off, wrong-life, and end-of-life batch arms;
* fixed common-deck and separately labeled on-policy cohorts, because a common
  deck tests representation/use while on-policy selection tests the flywheel;
* predeclared rank/capacity points and retained-compute accounting;
* target-blind graph/shape/identifier/nearest-neighbor and pretraining-exposure
  audits; instruction-preservation, schema-validity, output-length, and
  generic-domain-SFT controls; and
* primary post-context condition-by-slope interaction, post-context AUC,
  terminal action quality, early-panel retention, and correction after a
  public rule/condition change. A lower confidence bound and practical margin
  must be registered before outputs are seen.

Paper claims are rejected if authentic gains occur only before `C`, only on
same-family recall, disappear on cross-group/opposite-condition transfer,
survive outcome shuffling or wrong-life substitution, are matched by the
strongest ordinary/external-memory baseline, are explained by validity/style
or extra resources, or fail to persist across independent lives. A positive
confirmation supports only the measured outcome-grounded continual action
claim in this LLVM task family; broader claims require separate evidence.

## 15. Required immutable artifacts and authorization boundary

Before implementation: this protocol, its context hashes, dataset-discovery
algorithm, and acceptance tests are reviewed and human-ratified. Before the
offline install: the sealed package/dependency/model artifacts and canary
manifest are separately authorized. Before any GPU or timing canary: the
canary run manifest is separately authorized. Before the scout: static fit,
offline semantic canary, split seal, lifecycle tests, independent review, and
the exact three-life run manifest are green. Before confirmation or any paper
sentence: a new preregistration, fresh review, and human claim authorization
are required.

Minimum evidence files are:

```text
compiler_gym_static_fit_report.json
compiler_gym_offline_canary.json
dataset_catalog_and_split_seal.json
one_loop_one_lora_audit.json
sleep_row_authority_and_determinism.json
life_file_process_cache_isolation.json
sterile_eval_and_cold_adapter_load.json
budget_time_visibility_ledger.json
scout_raw_targets_and_metrics.json
scout_life_clustered_analysis.json
scout_stop_go_disposition.json
```

No passing static test, model agreement, or scout direction silently expands
the scope to installation, additional lives, benchmark repair, scale, or a
paper claim.
