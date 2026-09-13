# Additive replay after SEQ-161: independent terminal audit

**Date:** 2026-09-13  
**Disposition:** terminal negative qualification with a valid contemporaneous
descriptive contrast; native reproducibility remains unresolved  
**Scope:** read-only audit. No scorer, reducer, model, tokenizer, adapter,
training, collection, or GPU execution was rerun. No scientific artifact was
modified.

## Bottom line

The reported endpoint table is internally consistent with the frozen screen
and recovered reducer artifacts. `ADDITIVE` passes seeds 0 and 1 and fails seed
2; fresh `MEMORY_ONLY` passes seed 0 and fails seeds 1 and 2. Therefore neither
arm qualifies across all three roots. Additive replay is not a writer repair:
on seed 2 it obtains `8/8` exact recall but loses nine items that the incoming
parent answered correctly, and its `4/8` paraphrase score only ties the
evaluator-only best constant target.

The fresh pair remains useful as a contemporaneous comparison of two objective
packages. It does **not** isolate replay semantics: `ADDITIVE` has the complete
memory objective plus a separately normalized replay objective on 576 paired
forwards, consuming 2.40 times as many training tokens as `MEMORY_ONLY` and a
different dropout/RNG/optimization trajectory.

A more important problem appears in the control. Fresh `MEMORY_ONLY` does not
reproduce historical `EXTRA_MEMORY`, even though the preserved receipts say
the parent, encoded memory material, epoch schedule, nominal configuration,
and all 392 initialized LoRA tensors match. Losses differ by the first shared
logged point (step 10), the first-epoch means differ, all final tensor receipts
differ, and native outputs differ. This is real training-trajectory drift, not
the later collector bug. No evidence currently attributes it to dtype,
nondeterministic kernels, RNG state, or any other single cause. Writer tuning
should stop until the smallest native parity audit below establishes a
reproducible execution envelope.

## Evidence actually available to this audit

The locally copied, hash-verified result set is
`research_notes/astra_memos/receipts_20260912/astra_additive_replay_recovered_analysis_result_20260913_attempt1/`:

- `analysis.json`:
  `848602f01ca0596306dcb629a2e1d6896e08620cc6a67baa996853118c1cdb89`;
- `analysis.md`:
  `986028f66f62829b19f5c46e062b130f5a1e99dee860840a91255da656e67312`;
- `execution.json`:
  `f8c263aacfc61d85ecb64d253ae1b52cb372421b6117cfc3921f09b093c7387a`;
- `execution_review.json`:
  `c7e8f7eb64a42589869e6f5f903854044405eb9acfc944102d450164b12c35d1`;
- reducer stdout/stderr:
  `f46fe95b6dbfb9f4d66a1e6485a33cad2497a3466aaba8a1b939b33d14086b10`
  and the empty-file hash
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

The input manifest hash independently matches
`d975feca8197f2c09f45452101d9111afdaaa5988417cf9144fdc33089418c24`.
The protocol copy independently hashes to
`724d5a6e1aea7dca4b0ae42aec6e2fd0252b98646f7c903432927263f2c391e9`,
and the recovered reducer, original reducer, collection repair, runner, and
trainer copies match their reported hashes (`8a35836a...`, `df38efd2...`,
`9b67256c...`, `ca54e7e...`, and `3f2e73ef...`).

The native 524 MB evidence archive and extracted `/tmp` mirrors are not present
in this laptop worktree, and the formerly used paths are no longer present on
node 2. This audit therefore independently checks the committed reducer outputs
and their internal receipt joins, but does not rehash native adapter/raw-response
bytes itself. The archived receipt reports archive SHA
`1faf1f6a6482a3834f7aa4c98c34b71c29644acdc4dfec9ac7c0b3cd7c3b1d16`,
523,970,560 bytes, 1,366 members, six adapters, and all extracted bytes
verified. Those facts remain receipt-level evidence here.

One chronology caveat should be explicit. The scientific protocol was durably
committed at 11:16 UTC, before launch. The document named
`additive_replay_prereveal_interpretation_freeze` was authored/committed at
12:30/12:32 UTC, after the reducer ended at 12:01 and Builder revealed SEQ-161
at 12:09. Its statement that its author had not inspected outcomes may be true,
but Git does not independently prove a pre-reveal freeze. Treat the earlier
protocol's predeclared screen and outcome table as the durable preregistration;
treat the later memo as a self-attested interpretation audit, not a
cryptographically time-ordered preregistration.

## Exact fresh endpoints and screens

The named metrics are `production_eligible` for exact recall,
`content_correct` for paraphrase, and `passed` for held/canary. They are not
strict canonical-byte metrics.

| seed | arm | exact | paraphrase | held panel | canary | lost LR0-correct held | frozen screen |
|---:|---|---:|---:|---:|---:|---:|---|
| 0 | ADDITIVE | 14/14 | 10/14 | 47/48 | 12/12 | 0 | PASS |
| 0 | MEMORY_ONLY | 10/14 | 10/14 | 47/48 | 12/12 | 0 | PASS |
| 1 | ADDITIVE | 7/8 | 7/8 | 48/48 | 12/12 | 0 | PASS |
| 1 | MEMORY_ONLY | 8/8 | 8/8 | 46/48 | 12/12 | 2 | FAIL |
| 2 | ADDITIVE | 8/8 | 4/8 | 39/48 | 12/12 | 9 | FAIL |
| 2 | MEMORY_ONLY | 3/8 | 2/8 | 47/48 | 12/12 | 1 | FAIL |

The frozen exact floors are `8/14`, `7/8`, and `5/8`, conjoined with zero
losses among the particular LR0-correct held and canary items. Gains cannot
compensate losses. The all-root result is thus `FAIL` for both arms.

For descriptive arithmetic only, `ADDITIVE` pools to exact `29/30`,
paraphrase `21/30`, held `134/144`, canary `36/36`, retaining `134/143`
LR0-correct held items. `MEMORY_ONLY` pools to exact `21/30`, paraphrase
`20/30`, held `140/144`, canary `36/36`, retaining `140/143`. The pooled
figures cannot override the rootwise screen.

The contemporaneous itemwise comparison is heterogeneous:

- seed 0: ADDITIVE gains four exact items and loses none;
- seed 1: ADDITIVE loses one exact and one paraphrase item but restores the two
  held items lost by MEMORY_ONLY;
- seed 2: ADDITIVE gains five exact and two paraphrase items, repairs the one
  MEMORY_ONLY malformed held response, and introduces nine different held
  failures (net eight worse).

All 480 new calls stopped normally and none length-terminated. Only `5/120`
fresh memory-panel outputs are strict canonical JSON; content-scored extraction
therefore must not be described as interface-perfect retrieval. Seed 2
ADDITIVE's nine held failures are all `output_variant` failures. Seed 2
MEMORY_ONLY's one held loss is malformed JSON.

## Work and resource accounting

The planned arithmetic is satisfied: six fits, 1,632 optimizer updates and 480
cold readout calls, with zero new source or teacher calls.

| all roots | updates | memory forwards/tokens | replay forwards/tokens | supervised/context tokens | total training tokens |
|---|---:|---:|---:|---:|---:|
| ADDITIVE | 816 | 816 / 141,368 | 576 / 198,552 | 39,952 / 299,968 | 339,920 |
| MEMORY_ONLY | 816 | 816 / 141,368 | 0 / 0 | 22,888 / 118,480 | 141,368 |

Readout used 111,598 prompt tokens and 10,428 output tokens. Summed nested
training time is 638.939 s and summed generation time is 437.161 s; fit-process
and readout-process sums are 763.702 s and 612.362 s. These are nested across
three parallel controllers and must not be added as GPU-allocation time. The
recorded preparation-plus-holder allocation is 0.543290 h. Controllers ran
660.238/570.774/583.234 s for seeds 0/1/2; each stayed below the 7,200 s bound.
Separate scoring repair consumed 30.245/23.559/23.829 CPU seconds and no GPU
scientific work.

## Collection repair custody

The scientific work was not rerun. For every root, the native controller
returned 0, then the original collector and holder recorded 1/1 because a
paired-material dictionary shadowed the retention-scorer module, raising
`AttributeError: 'dict' object has no attribute 'score_row'`. The original
failure, first claim, launcher inventory, stage outputs, adapters, and raw
responses remain separately bound in the reducer. Seed 1 additionally retains
a launcher `BrokenPipeError(32, 'Broken pipe')` and
`holder_may_be_running=true`; this transport anomaly is not silently erased.

Each root then has a distinct attempt-2 repair claim and rc0 recovery receipt
with `scientific_retry=false`, `fits=0`, `updates=0`, and
`generation_calls=0`. The repair invokes the original scorer against preserved
raw responses and writes a different `_collected_repair1` directory. The
single recovery-aware reducer ran once, rc0, for 4.265 s with empty stderr and
kept `automatic_promotion=false`, `scientific_pass=null`, and
`fit_authorized=false`.

This is coherent scoring-only recovery custody, not an all-rc0 first attempt.
Because this audit lacks the native archive, the claim that every original byte
was unchanged is supported by the repair/reducer hash joins and archive receipt,
not by a second independent byte traversal here.

## Fresh MEMORY_ONLY versus historical EXTRA_MEMORY

| seed | historical EXTRA_MEMORY exact/para/held | fresh MEMORY_ONLY exact/para/held | raw changed exact/para/held | old -> fresh last loss |
|---:|---|---|---|---|
| 0 | 13/14, 10/14, 47/48 | 10/14, 10/14, 47/48 | 5, 0, 0 | .005188 -> .014876 |
| 1 | 7/8, 6/8, 46/48 | 8/8, 8/8, 46/48 | 1, 2, 0 | .074396 -> .036297 |
| 2 | 7/8, 7/8, 42/48 | 3/8, 2/8, 47/48 | 5, 5, 7 | .003048 -> .043440 |

Canaries remain `12/12` with zero raw changes in every root. Equal endpoint
counts do not imply equal raw behavior: seed 0 exact has five raw changes even
though some remain content-correct, and seed 2 has seven changed held outputs.
All three final tensor inventories differ. Old and fresh mean loss traces are
already distinct in epoch 1; their step-10 logged losses differ beyond the old
four-decimal rounding interval in all roots. Thus the drift precedes scoring.

### Did the inputs and initialization really match?

At the strongest preserved receipt level, **yes for the declared training
state, with two audit qualifications**:

- The fresh `ADDITIVE` and `MEMORY_ONLY` executed journals contain exactly
  304/256/256 memory positions, and projecting away `replay_row_id` makes the
  complete per-position memory schedules equal in every root. ADDITIVE alone
  has 192 paired replay positions per root.
- The bounded drift audit directly found fresh `paired.json.primary`
  deep-equal to the entire historical `training_EXTRA_MEMORY.json`; strings,
  token IDs, labels, masks, EOS, rows, encoding, all eight epoch-order arrays,
  token counts, training-item hash and epoch-order hash match.
- Parent inventories, model files, package versions, config, seed, GPU UUID,
  AdamW defaults, target-module set, and actual trainable-name order match.
  All 392 historical/fresh source and initialized LoRA tensor hash entries,
  shapes and dtypes match; initialized LoRA tensors are float32 while the base
  load is bf16. Fresh-arm initial L2 norms also match within each root.

Qualification one: this audit reads the committed receipt comparison rather
than recomputing those 392 tensor hashes from the absent native mirror.
Qualification two: the old fit has no per-step `steps.jsonl`; its frozen epoch
order and completed step count are preserved, but historical execution order is
not independently journaled at every step. Therefore “same encoded schedule and
completed dose” is proved more strongly than “every old kernel consumed every
item in byte-identical runtime state.”

## What is known and what remains hypothesis

Known:

- drift exists by the first mutually observable logged point and affects the
  training trajectory, final tensors, and decoded outputs;
- encoded examples, labels, masks, schedule, nominal recipe, parent selection,
  initialized LoRA tensor receipts, recorded optimizer defaults, versions, and
  recorded GPU identity do not explain it;
- both paths use bf16 base computation, float32 LoRA tensors, dropout 0.05,
  gradient checkpointing, and fresh AdamW; and
- the tiny CPU test is exactly equal, but it uses fp32, eager attention, two
  layers, no checkpointing, one CPU thread and deterministic algorithms. It
  cannot certify the native regime.

Not known:

- CPU/CUDA RNG states at matching lifecycle boundaries;
- the effective attention/SDPA kernel, checkpoint reentrancy behavior,
  TF32/matmul settings, deterministic-algorithm status, or resolved AdamW
  `foreach`/`fused` path;
- whether allocation/synchronization differences between the two runner paths
  perturb dropout/checkpoint recomputation or another CUDA trajectory; or
- the exact first divergent update, because historical logs begin at step 10.

The new runner encodes and validates replay material before its seed reset,
clones initial trainable tensors to CPU, runs extra finite/target checks and
synchronizing scalar reads, and journals each step. The old runner has a
different allocation/object-lifetime pattern. These are genuine seams, not
demonstrated causes. Likewise “bf16 instability,” “nondeterministic CUDA
kernels,” “thread count,” “target-module set ordering,” and “dropout RNG” are
hypotheses only. There is no observed dtype mismatch: mixed-precision
sensitivity remains possible, but the recorded dtypes agree.

## Minimum reproduction audit before any more writer tuning

Do not rerun the six-cell science cohort and do not change rank, rate, replay
weight, or corpus while this is unresolved. Run one diagnostic root only
(seed 2 is the highest-information choice because it has the largest endpoint
drift; this post-outcome selection is diagnostic, never confirmatory):

1. Execute the exact frozen historical `EXTRA_MEMORY` path twice and the exact
   fresh `MEMORY_ONLY` path twice, each in a new process on the same GPU, from
   the same original parent and initialized adapter. Use the first ten frozen
   memory positions only, no generation/readout, and save no scientific
   adapter.
2. Before initialization, after initialization, before/after every forward and
   backward, and after every step, record Python/CPU/CUDA RNG hashes; all 392
   trainable tensor hashes; input/label/mask/position-ID hashes; loss; all
   gradient hashes; optimizer moment hashes; effective dtypes, train/eval and
   dropout states; resolved attention/SDPA and checkpoint modes; TF32/matmul and
   deterministic flags; and resolved AdamW `foreach`/`fused` behavior.
3. First preserve each path's natural seeded lifecycle. If RNG hashes diverge
   before the first forward, the seed/lifecycle seam is localized. Then run a
   separately labeled scratch comparison with the identical captured RNG state
   restored immediately before the forward; do not substitute that forced
   result for the historical recipe.
4. Require within-path repeat equality before interpreting cross-path equality.
   If old-old or new-new diverges, seal a future deterministic runtime
   (`CUBLAS_WORKSPACE_CONFIG`, deterministic algorithms, explicit SDPA backend,
   TF32 off, explicit checkpoint reentrancy, explicit AdamW foreach/fused) and
   require two ten-step repeats to match before tuning. If within-path repeats
   match but old-new differs, the first differing state hash localizes an
   implementation/lifecycle seam. If all four match through step 10, the known
   early drift has not reproduced; only then is a longer stepwise comparison
   warranted.

Ten updates, four scratch processes, and zero readout calls are the smallest
audit that simultaneously tests within-path repeatability and old-vs-new path
parity at the point by which the preserved runs are already known to differ.
A single forward is cheaper but insufficient: it cannot distinguish
within-path nondeterminism from a path effect, and it cannot rule out divergence
introduced by optimizer/checkpoint state over the first ten steps.

Until that audit passes, the only safe scientific reading is: additive replay
caused large, parent-dependent acquisition/retention changes relative to its
fresh control, but neither package qualifies and the native writer is not yet
demonstrably reproducible enough for finer objective tuning or a causal SLEEP
claim.
