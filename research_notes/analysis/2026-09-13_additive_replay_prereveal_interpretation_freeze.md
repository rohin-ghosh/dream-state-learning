# Additive replay: pre-reveal interpretation freeze

**Date:** 2026-09-13 UTC  
**Status:** frozen before inspecting the recovered cohort reduction or any
unrevealed additive outcome counts  
**Scope:** protocol/source/receipt audit only. No native result, model,
tokenizer, adapter, GPU, or analysis execution was inspected or changed.

## Bottom line

The experiment asks one narrow question: at the existing rank-8, `3e-5`,
eight-pass operating point, can retaining the complete `EXTRA_MEMORY` memory
schedule **and adding** the child's already admitted observation loss meet the
frozen acquisition and retention screen in all three exposed Level-1 roots?

The primary comparison is fresh `ADDITIVE` versus fresh `MEMORY_ONLY`.
Historical `EXTRA_MEMORY` is a required implementation-drift reference, not a
substitute control. Even a `3/3` ADDITIVE pass would qualify only this one
single-write objective package. It would not establish semantic replay as the
cause, equal-compute superiority, robust key binding, repeated-cycle SLEEP,
parenting, PCFL traversal, or lifetime learning.

This freeze follows the final protocol at SHA-256
`724d5a6e1aea7dca4b0ae42aec6e2fd0252b98646f7c903432927263f2c391e9`.
In particular, the run deliberately preserves the historical seed-0
`EXTRA_MEMORY` repetition imbalance. The earlier suggestion to introduce a
balanced cyclic schedule was superseded; it must not be smuggled into the
interpretation after outcomes are known.

## Exact experiment and arithmetic

For seeds `0/1/2`, the admitted memory denominators are `14/8/8`. Each epoch
contains those original memory occurrences plus the exact historical 24
extra-memory occurrences. There are eight epochs:

| seed | occurrences/epoch | updates/arm | calls/arm | paired ADDITIVE updates |
|---:|---:|---:|---:|---:|
| 0 | `14+24=38` | `304` | `2*14+48+12=88` | `192` (`63.2%`) |
| 1 | `8+24=32` | `256` | `2*8+48+12=76` | `192` (`75.0%`) |
| 2 | `8+24=32` | `256` | `76` | `192` (`75.0%`) |

Across both arms, the terminal scientific workload must remain exactly six
fits, `1,632` optimizer updates, and `480` cold readout calls. `MEMORY_ONLY`
performs `816` memory forward/backward passes. `ADDITIVE` performs the same
`816` memory passes plus `576` replay passes, or `1,392` constituent-sequence
passes total. The final report must give actual memory/replay supervised,
context, and total token counts; the sequence counts do not imply equal token
lengths.

The per-root frozen screen is noncompensatory:

- exact `production_eligible` recall at least `8/14`, `7/8`, and `5/8` for
  seeds 0, 1, and 2 respectively;
- zero regressions on the *specific* LR0-correct held items: `47`, `48`, and
  `48` items, hence `143/143` across roots; and
- zero regressions on the LR0-correct canaries: `12` per root, hence `36/36`.

All three root screens must pass. A gain on LR0's one seed-0 held error cannot
offset losing a different LR0-correct item. A pooled exact score of at least
`20/30` is neither necessary nor sufficient unless each root clears its own
floor. Paraphrase `content_correct`, distinct-target robustness, the full
confusion table, raw formats, and the evaluator-only constant-target result
must be reported, but none can rescue a failed screen. The exact and
paraphrase panels contain `14/8/8` admitted cues; held and canary contain
`48/12` rows per root. The source universe also records 16 possible records
per root, but that is not the frozen exact-read denominator.

## What the summed loss changes

On every position, `MEMORY_ONLY` takes one AdamW step on

`L_memory = mean cross-entropy over the memory response/EOS tokens`.

On the 24 extra-memory positions per epoch, `ADDITIVE` instead takes one AdamW
step after accumulating

`L_memory + L_replay`,

where `L_replay` is independently averaged over the replay response/EOS
tokens. The sum is intentionally **not** divided by two and is not a
token-weighted concatenated mean. Therefore:

1. The memory item retains unit sequence-level weight, and the replay item
   adds another unit of sequence-level weight regardless of relative target
   length. Individual memory tokens receive weight `1/T_memory`; individual
   replay tokens receive weight `1/T_replay`.
2. The gradient on a paired update is `grad(L_memory)+grad(L_replay)`. Its norm
   is not predictably double: aligned components reinforce; opposed components
   cancel; orthogonal components redirect the step. AdamW's moment state then
   makes later trajectories path-dependent.
3. ADDITIVE thus changes gradient direction and effective update magnitude on
   `576/816 = 70.6%` of its optimizer steps, while leaving step count, learning
   rate, weight decay calls, and the memory occurrence schedule fixed.
4. The additional forward/backward passes consume more tokens, activations,
   wall time, and dropout/random-number draws. After the first paired update,
   even the subsequent memory gradients are evaluated at different weights.

Accordingly, the treatment is **the added, separately normalized replay-loss
package**. It is not equal-FLOP evidence, a pure content ablation, a scalar
learning-rate comparison, or proof that replay semantics rather than extra
gradient/compute caused an effect. “The full new-memory objective remains
present” is valid; “the realized memory gradients are identical” is not.

## Required terminal evidence

No scientific interpretation is allowed unless every root supplies all of the
following, byte-joined through its plan and completion hashes.

### Original scientific root

- `spec.json`, `plan.json`, `prepare_started.json`, `prepare_done.json`,
  `material.json`, `paired.json`, `calls.json`,
  `training_ADDITIVE.json`, and `training_MEMORY_ONLY.json`;
- immutable `upstream/`, `repair/`, and `sources/` snapshots, including the
  actual historical `training_EXTRA_MEMORY.json` and `training_REPLAY.json`
  file-byte bindings, original parent, histories, capture, runner, core,
  trainer, and protocol;
- `controller_started.json` and a terminal `capture_complete.json` with
  `scored=false`, the exact four-stage inventory, and the correct per-root
  fit/update/call counts;
- exactly the stages `ADDITIVE_fit`, `ADDITIVE_readout`, `MEMORY_ONLY_fit`,
  and `MEMORY_ONLY_readout`, each with launch/start/done/strict-integer-rc0/
  release receipts, stdout/stderr, process identity and GPU-vacancy custody;
- for each fit: `fit.json`, adapter files, `train_manifest.json`,
  `train_meta.json`, `steps.jsonl`, and `DONE`, proving the original parent is
  unchanged, the optimizer is fresh, base weights are frozen, the LoRA delta
  is finite and nonzero, and all prescribed occurrences execute once per
  epoch with no split, truncation, skip, or masked-context supervision; and
- for each readout: identity/readout receipts plus every declared request and
  raw response for exact, paraphrase, held, and canary calls.

### Failed collection and scoring-only repair

The collection bug is scientifically recoverable only under this exact
custody history:

- the original controller exited strict integer `0`; the original collector
  and holder exited strict integer `1/1` only because the collector hit
  `error_type="AttributeError"` and
  `error="'dict' object has no attribute 'score_row'`;
- the original `.collection_claim.json`, complete `.launcher/` inventory, and
  original `_collected/collection_failure.json` remain byte-identical. The
  original collected directory contains only that failure file;
- a distinct `.collection_repair1_claim.json` binds collection attempt 2,
  `scientific_retry=false`, and zero fits, updates, and generation calls;
- a distinct `_collected_repair1/` contains exactly `scores.json`,
  `collection.json`, and `recovery.json`; recovery is strict integer rc0,
  takes at most 180 seconds, and uses the frozen original scorer/material seam
  to rescore the preserved raw responses; and
- before/after hashes prove no original stage, adapter, response, completion,
  claim, launcher, or failure byte changed. There was no regeneration,
  refitting, source recapture, teacher call, retry, or root substitution.

The three-root recovery manifest must bind exactly seeds `0/1/2` and, for each
seed, the original root, plan/completion, repaired scores/collection, original
claim/failure and full launcher inventory, repair receipt, and new repair
claim. A fresh reducer output must contain `analysis.json` and `analysis.md`,
rehash all bindings, independently rescore every raw response, preserve all
per-item contrasts and costs, and always retain
`automatic_promotion=false`, `scientific_pass=null`, and
`fit_authorized=false`.

The recovery repairs scoring only. It adds zero scientific work and does not
convert the original rc0/1/1 chain into a fictitious all-rc0 first attempt.
The archived evidence and its archive/verification receipts should be retained
with the reducer outputs. Missing or altered evidence means **no result**, not
a failed scientific arm.

## Mandatory contemporaneous and historical comparisons

1. **Fresh ADDITIVE versus fresh MEMORY_ONLY is primary.** Both begin from the
   same original parent and share the exact memory items, occurrence order,
   masks, config, updates, and cold panel. Their designed difference is the
   added replay forward/backward loss. Because compute and RNG consumption
   differ, this identifies the objective package, not replay semantics alone.
2. **Fresh MEMORY_ONLY versus historical EXTRA_MEMORY is a drift audit.** The
   historical endpoint used the same intended memory file and order but is
   noncontemporaneous. Synthetic tiny-model tensor parity validates code, not
   native-scale identity. Source/order/mask/config/parent/optimizer/step/token
   mismatches are hard invalidations. With all receipts equal, raw-output or
   endpoint differences may still arise from native numerical or decoding
   realization and must be itemized through `raw_changed_ids`, losses, norms,
   and manifests.
3. Historical `EXTRA_MEMORY` achieved exact/paraphrase `27/30`/`23/30`, kept
   `135/143` LR0-correct held items and `36/36` canaries, and passed the exact
   floor in every root while failing retention in roots 1 and 2. Historical
   `REPLAY` achieved `21/30`/`19/30`, kept `143/143` and `36/36`, and passed
   only `2/3` root screens. These diagnose the prior tradeoff; they are not
   fresh causal controls and incur zero current cost.
4. If fresh MEMORY_ONLY changes a root's screen disposition relative to
   historical EXTRA_MEMORY, the fresh ADDITIVE comparison remains usable only
   as a contemporaneous objective-package comparison after receipt integrity
   passes. It cannot be described as “repairing EXTRA_MEMORY's historical
   losses” until the drift is explained. Historical agreement strengthens the
   bridge to SEQ159 but never replaces the fresh control.

## Claims frozen for every possible outcome

| terminal state | allowed claim | prohibited inference / action |
|---|---|---|
| Any source, parent, schedule, mask, fit, raw-response, recovery, or reducer integrity check fails | No valid result; name the custody or implementation failure | Do not score around it, drop a root, recollect again, or count it as a scientific failure |
| ADDITIVE passes `3/3`; MEMORY_ONLY fails at least one root; fresh MEMORY_ONLY is historically coherent or its drift is explained | At this fixed single-write operating point, adding the replay-loss package is sufficient to reach the joint exact-acquisition/LR0-retention feasibility screen where the matched fresh memory-only package is not | Do not call this pure semantic replay, equal-compute superiority, robust retrieval, qualified SLEEP, or a repeated-life result; it only justifies a separately specified next-cycle test |
| Both ADDITIVE and MEMORY_ONLY pass `3/3` | Both packages are feasible here; the experiment does not show replay is necessary. Itemwise margins may be reported as exploratory | Do not promote ADDITIVE merely because it has a larger pooled score or preferred narrative |
| ADDITIVE fails at least one root; MEMORY_ONLY passes `3/3` | This additive recipe fails the predeclared qualification and is unnecessary or harmful at this point; MEMORY_ONLY is the feasible fresh package | No replay-weight, seed-specific, rank, rate, epoch, or best-checkpoint rescue |
| Both arms fail at least one root | Neither package repairs the writer across roots. Directional acquisition/retention movement may localize the remaining tradeoff | No adoption, pooled compensation, or further scalar sweep on this proxy; proceed to objective-matched PCFL |
| ADDITIVE and MEMORY_ONLY have the same screen count, but ADDITIVE restores some historical losses or improves recall | Exploratory itemwise evidence about the tradeoff only | Restoration of some rows cannot offset any LR0-correct regression or failed root floor |
| ADDITIVE passes but the fresh MEMORY_ONLY arm or historical-drift audit is invalid/unresolved | ADDITIVE independently reached its frozen one-arm screen, if its own custody is intact | No causal replay-benefit claim and no claim that it repaired the old EXTRA_MEMORY condition |
| Any exact-screen success has weak paraphrase, low distinct-target robustness, constant-target behavior, malformed outputs, or concentrated confusions | Exact-cue feasibility with the named diagnostic limitation | No general extractability, associative binding, compression, connection, traversal, or task-use claim |

Every valid outcome remains subordinate to PCFL. This proxy contains exposed,
harness-authored Level-1 observations that the original parents had already
encountered; it tests re-consolidation and retention geometry, not learning new
experience or using connected memories under goals. It must not delay, waive,
or qualify PCFL's own acquisition, locality, retention, traversal, expansion,
and lifetime gates.

## Frozen sources read

- `research_notes/astra_memos/ASTRA_ADDITIVE_REPLAY_DEV_2026-09-13.md`
- `research_notes/analysis/2026-09-13_writer_replay_acquisition_tradeoff_adjudication.md`
- `research_notes/analysis/2026-09-13_own_source_replay_repair_terminal_audit.md`
- archived additive core, trainer, runner, launcher, tiny-test, collection
  repair, and recovery-reducer sources/tests/handoffs under
  `research_notes/astra_memos/receipts_20260912/`

No recovered additive cohort report, native mirror, evidence archive contents,
or unrevealed current outcome counts were read while producing this freeze.
