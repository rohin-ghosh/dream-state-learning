# CompilerGym v6 first-pilot execution defaults (candidate)

Status: proposal-only defaults for deliberation. This memo grants no
installation, import, execution, model call, training, GPU, or scientific
authority. The values below become operative only if the already-local
unchanged artifacts pass the proposal's static/offline fit gates, are bound in
a run manifest, independently reviewed, and separately human-authorized at
each required transition.

## 1. Reward and score

Use the official LLVM environment reward-space identifier
`IrInstructionCountOz`, with higher reward meaning a larger reduction in LLVM
IR instruction count relative to the official `-Oz` baseline. The official
documentation defines baseline-normalized reward as

```text
R_k = (I_{k-1} - I_k) / (I_0 - I_Oz)
```

where `I_k` is the `IrInstructionCount` cost after action `k`, `I_0` is the
post-reset initial cost, and `I_Oz` is the cost after the pinned official
`-Oz` baseline. The documentation identifies `IrInstructionCountOz` as
deterministic and platform-independent, while warning that IR instruction
count is not lowered object-code size. See the [official LLVM reward
definition](https://compilergym.com/llvm/index.html#reward-spaces) and the
[official v0.2.5 release](https://github.com/facebookresearch/CompilerGym/releases/tag/v0.2.5).

Request `IrInstructionCount` and the four instruction-count values (`I_0`,
`I_Oz`, current `I_k`, and best-so-far `I_best,k`) as audit-only public cost
observations. Do not use runtime, build-time, `ObjectTextSize*`, or host
timing as the pilot reward; the official documentation marks those paths as
platform-dependent or experimental where applicable.

For the held-out descriptive endpoint, define the six-decision target score

```text
S_{i,k} = 0                                          if no valid state exists through k
S_{i,k} = (I_0 - min_{j<=k, valid} I_{i,j}) / (I_0 - I_Oz) otherwise
G_i     = (1/6) * sum_{k=1..6} S_{i,k}
```

Invalid, malformed, timeout, and environment-error operations preserve the
last valid best state for later `S_{i,k}` but are separately counted as
invalid; a target with no valid state has `G_i=0`. Do not clamp `S` at 1:
beating `-Oz` is possible and should remain visible. Reject a target from fit
if `I_0-I_Oz <= 0`, the denominator is non-finite, or reset/baseline values
are not reproducible. Retain the raw official per-step reward and counts so
the derived `G` cannot conceal a semantic mismatch.

The primary one-life contrasts are unweighted means over the four sealed
targets (the life, not a target row, is the descriptive replication unit):

```text
D_off  = mean_i(G_authentic,i - G_adapter_off,i)
D_shuf = mean_i(G_authentic,i - G_binding_shuffled,i)
D_zero = mean_i(G_authentic,final,i - G_authentic,checkpoint0,i)
```

Report target strata separately but do not form inferential target-level
replicates. Report validity/parse/terminal rates separately from `G`; a gain
from merely emitting fewer malformed actions is not an outcome-learning
claim.

## 2. Observation projection and token envelope

The first pilot should expose a compact deterministic public projection, not
variable-length raw IR or a filesystem path:

```text
ENVIRONMENT = {
  observation: Autophase[56] int64,
  instruction_features: InstCount[70] int64,
  current_cost: IrInstructionCount int64,
  legal_actions: canonical ordered LLVM pass-name list,
  terminal/action_effect status,
  task-local public best and outcome summary
}
```

CompilerGym documents `Autophase` as a 56-dimensional integer summary and
`InstCount` as a 70-dimensional integer observation. Both are deterministic,
platform-independent summaries. The [official observation-space
reference](https://compilergym.com/llvm/index.html#observation-spaces)
documents these shapes and the `Ir`/`BitcodeFile` alternatives. Do not expose
`BitcodeFile`: it is a temporary path and would create a cache/file visibility
channel. Do not expose full `Ir` in this first pilot; retain full source/IR
only in the static split/dedup audit. A variable IR prompt would make
truncation, source memorization, and context parity hard to distinguish from
experience.

Freeze these caps:

* canonical model input: 4,096 tokens under the pinned tokenizer, including
  labels and all packet fields;
* `RECENT_TAIL`: at most 512 tokens, complete-event suffix only;
* ORIENT output: at most 256 generated tokens and at most two recall queries;
* THINK_ACT output: at most 256 generated tokens and exactly one typed
  operation;
* six ORIENT/THINK_ACT pairs per task, with an output ceiling of 3,072 tokens
  per task (unused budget is not silently reused);
* one rendered sleep row: at most 768 tokens, with a fixed truncation rule;
* training input sequence length: 768 tokens; loss mask is one only on the
  typed focus/action targets;
* selected cumulative corpus: 192 rows, at most 64 per ORIENT/ACT/REVISE
  view, 50:50 retained-old/new capacity where both are available; and
* 24 effective target-token touches per retained row, with a fixed total
  touch/token receipt and no early stop or content-dependent retry.

The 768-token row cap is intentionally above the compact vector projection's
expected rendering while remaining bounded. Before adoption, the static
tokenizer audit must record the maximum canonical packet and row lengths for
all 8 acquisition and 4 target candidates. If any selected packet cannot fit
4,096 or any selected row cannot fit 768 without dropping a required public
field, this default is not fit: do not increase caps after seeing outcomes;
return the cell for a new bound decision. If the intended requirement is to
carry full textual POJ104 IR, these defaults do not claim to do so; a separate
predeclared IR cap and a new leakage/truncation review would be required.

## 3. Deterministic POJ104 family and split constructor

Use only the already-local official `benchmark://poj104-v1` catalog and
public static bytes. The official catalog documentation lists POJ104-v1, but
also marks it non-validatable; therefore “valid” below means the official
LLVM environment accepted the action and returned the deterministic IR cost,
not that POJ104 program behavior was independently executed. No claim of
functional correctness may be made without a separate validation path.

The frozen constructor is:

1. Enumerate catalog URIs in canonical byte/lexicographic order. Hash every
   source/IR and public metadata record. Abort if the exact release/catalog
   bytes, LLVM version, source encoding, or provenance cannot be established.
2. Canonicalize each program using only public static source/IR: remove module
   IDs, debug data, source paths, and identifier numbering; canonicalize
   commutative operand ordering; preserve types, opcodes, constants, call
   edges, CFG edges, memory-operation categories, and loop-depth bins. Record
   exact source hash, canonical-IR hash, normalized module/function callgraph
   hash, CFG Weisfeiler–Lehman hashes for iterations 0–3, opcode/type/layout
   histogram, and loop-shape signature.
3. Build duplicate components before selecting any task: exact source or IR;
   normalized graph isomorphism; same normalized opcode/CFG/type/layout/
   loop-shape signature under identifier/constant renaming; and a frozen
   nearest-neighbor threshold on the public signature distance. A candidate
   target is excluded if it or any component member is linked to an
   acquisition candidate. Record every rejected pair/component.
4. Define relation groups mechanically from the official public POJ104
   problem-family token only if that token is present in the immutable catalog
   with provenance; never expose it to the model. If the token is absent or
   provenance is unclear, use deterministic clustering of the public feature
   vector above with fixed lexical tie breaks and a manifest-bound threshold.
   No reward, model output, optimized result, hidden file, or target score may
   enter grouping.
5. Require four relation groups, each with two acquisition candidates, one
   held-out target, and at least two unused static spares. Select the first
   legal candidate in each cell after sorting by
   `(group_key, canonical_IR_hash, URI)`; select spares by the same order.
   The result is exactly 8 acquisition programs and 4 targets. Counterbalance
   the two paired on-policy agents with two fixed acquisition permutations
   derived from the manifest hash; never choose order from an outcome.
6. Seal the 8/4 manifest, all duplicate/near-neighbor reports, group
   algorithm, thresholds, spare substitutions, and hashes before any model
   call. Target outcomes, action traces, reward values, model output,
   reference/solution files, hidden scorer data, and evaluation descendants
   are forbidden inputs to this constructor.

The group relation is a transfer aid, not an answer label. If four groups,
four target cells, two acquisition examples per group, and two spares per cell
cannot be obtained after all duplicate exclusions, reject CompilerGym/POJ104
for this change. Do not substitute cBench, Jotaibench, another POJ104 copy, or
a repaired/forked dataset.

## 4. First pilot counts and lifecycle

The recommended Stage-C pilot is exactly one paired on-policy life:

* HARNESS and EXPERIENTIAL start from the same frozen base/bootstrap and null
  adapter, with identical packet, ledger, bounded notebook/retriever, tools,
  public task order, six-pair task budget, and deterministic sleep schedule;
* acquisition consists of 8 programs, in two fixed blocks of 4;
* SLEEP occurs only after acquisition programs 4 and 8, rebuilding the
  cumulative rank-16, alpha-16, dropout-0 q/v LoRA from clean base with a
  fresh reset AdamW optimizer;
* the target panel has 4 sealed public-static related/nonduplicate targets;
  every target is evaluated at checkpoints 0, 4, and 8, in a fixed
  counterbalanced order, with 6 ORIENT/THINK_ACT pairs (12 model calls) and
  at most 6 public environment actions;
* authentic and adapter-off forks run at all three checkpoints; the final
  checkpoint additionally runs the equal-budget compatible-stratum
  binding-shuffled fork; and
* every evaluation process is cold-started and then destroyed/quarantined;
  target outcomes never return to acquisition, retrieval, compiler, trainer,
  later targets, or the on-policy ledger.

These counts are a wiring/mechanism assay, not a lifetime experiment. The
context-cap crossing, multiple-life replication, post-context checkpoints,
strong external-memory controls, and powered slope model belong to a new
Stage-D ratification. If the static packet audit cannot show the relation
panel or if the offline canary cannot replay the official service, the pilot
does not run.

## 5. One-life descriptive stop/go rule

Use the frozen default margin

```text
m = max(0.05, 2 * s_canary)
```

where `s_canary` is the pre-target, acquisition-only standard deviation of
the same normalized `G` construction under the fixed canary's independent
clean-process repeats. `s_canary` and `m` must be sealed before target
opening; if no independent canary estimate exists, use `m=0.05` and label the
result a single-realization wiring observation.

Record exactly one disposition:

* `STOP_FOR_THIS_RECIPE` if any static/offline/lifecycle/visibility/budget
  gate fails, a target denominator is invalid, any primary fork is
  indeterminate, `D_off < m`, `D_zero < m`,
  `D_shuf < max(m, 0.5*D_off)`, authentic validity is more than 0.05 below
  HARNESS, or fewer than three of four targets have nonnegative
  authentic-minus-adapter-off score;
* `MECHANISM_GO_ONLY` (descriptive, non-claim) only if all gates and all of
  the preceding numeric conditions pass and style/validity/neighbor/text/
  wrong-life diagnostics do not explain the contrast; and
* `MECHANISM_GO_ONLY_WITH_DIAGNOSTIC_EXPLANATION` if those numeric conditions
  pass but the diagnostic decomposition attributes the signal to validity,
  style, neighbor reuse, text transport, or another simpler factor. This
  remains a stop for any outcome-learning claim.

The last label is intentionally diagnostic rather than a scientific claim.
No p-value, confidence interval, slope, saturation inference, or target-level
replication is produced from this one life. A later directional scout must
start with a new hash-bound manifest and at least three fresh paired lives;
paper-level claims require a separately powered life-clustered design with
strictly post-context checkpoints, demonstrated headroom, and declared
native/external-memory/raw-LoRA controls.

## 6. Resource and fairness ledger

Record per condition and per boundary: model input/output tokens, packet and
retrieval/notebook tokens, ORIENT/THINK_ACT calls, public environment actions,
invalid/retry/crash counts, sleep candidate/retained rows, views, target-token
touches, trainer steps/tokens/FLOPs where available, adapter bytes, wall time,
peak memory, and compiler/LLVM cache events. HARNESS executes the same
deterministic sleep work as a sham and quarantines the resulting bytes; this
matches declared work but does not imply identical physical adapter-load cost.

Publish both (a) model-visible logical parity—identical caps, counters,
operations, retrieval allowance, and packet schema—and (b) total natural and
compute-normalized resource ledgers. Do not expose wall latency, condition,
checkpoint identity, row counts, training duration, cache warmth, or adapter
origin to the model. Do not pad a baseline with useful information merely to
equalize an incidental physical cost.

Same-corpus text, raw-trajectory LoRA, organized RAG, native-long-context,
wrong-life, rank/capacity, and no-memory controls are not silently folded into
HARNESS. If omitted from Stage C, report that omission and defer any practical
carrier-superiority claim to Stage D.

## 7. Defaults that remain unchoosable before local inspection

The following cannot be certified by this memo or by upstream documentation:

* whether the local package/wheel and all LLVM 10 runtime/dependency artifacts
  are present, hashable, importable offline, and unchanged;
* whether local 0.2.5 exposes the documented `llvm-v0`/`llvm-ic-v0` factory,
  `IrInstructionCountOz` semantics, POJ104-v1 catalog, legal action projection,
  reset behavior, and deterministic replay exactly as specified;
* the actual POJ104 source/IR token-length distribution and whether the four
  relation groups survive all duplicate and nearest-neighbor exclusions;
* the true denominator `I_0-I_Oz`, per-program headroom, invalid-action and
  terminal behavior, and the canary variance needed to finalize `m`;
* whether every selected canonical packet fits 4,096 and every rendered row
  fits 768 under the exact model tokenizer; and
* model/bootstrap/sampling bytes, deterministic bf16/training behavior,
  optimizer receipts, hardware capacity, and any implementation-specific
  resource overhead.

Any unresolved item is a fit failure or an explicit new design decision, not
an invitation to download, patch, substitute, execute, or tune after target
outcomes are visible.
