# R210 TRAIN continuation — current evidence

Observed **2026-09-18T05:46:35.627532+00:00**, R213 follow-up; NEW actual checkpoint1000 mixed results for both candidates posted to `research_loop/COORDINATION.md`. All times UTC, September18,2026. No new node2 operation; Jason owns node2 enrichment. Current game/vision on node4 untouched. Neither current R210 job was interrupted or changed during this refresh; no hold, stop, restart, or relaunch issued. Main's separate frozen no-LoRA game control is not operated or evaluated here.

R212 criterion separation: Main owns game acceptance **50/65 plus relevance and novelty, no tau**. This operator makes no game-criterion change. The fixed600-case contrasts remain diagnostic; training checkpoint selection remains the predeclared model-selection Spearman. No midrun threshold, panel, or selection-rule change is applied.

## Live mixture and ETA

| Rank | Four ranks live | Crossed fraction | Candidate update / R210 pair draws | R210 pairs/s | Latest predicted finish UTC | ≥300s new-mixture fitting? |
|---|---|---|---|---|---|---|
| 8 | True | 16/64 = 0.25 | 1090 / 60480 | 30.435 | 2026-09-18T14:23:45.657771+00:00 | True |
| 16 | True | 16/64 = 0.25 | 1146 / 64128 | 30.125 | 2026-09-18T14:27:09.327551+00:00 | True |

ETAs use actual R210 fitting throughput and measured distributed diagnostic cost extrapolated across remaining checkpoints. Early estimates under300seconds are **provisional**, not recycled R209 pilot measurements or guarantees. Training continues automatically; no Main approval, tau, contrast or selection gate. Same600-case diagnostic cost is now approximately26seconds per checkpoint, using the already-loaded four-rank model rather than contention-heavy sidecars.

Both current ETA receipts exceed300seconds of R210 fitting: rank8 step1090,1987.199seconds at30.4348pairs/s; rank16 step1140,2116.278seconds at30.1208pairs/s. Latest actual update times are05:46:33.892795UTC(rank8 step1090) and05:46:34.892980UTC(rank16 step1146). ETAs are sampled every10updates; rank16 live progress is newer than its ETA sample. Forecasts remain conditional on sustained throughput, not completion promises. Four native processes per candidate remain present with unchanged PID/start identities: rank8 67713–67716; rank16 67117–67120. Live fraction is computed from actual per-update pair counts, not inferred from a declared recipe.

## Same-checkpoint restoration, explicit rewind

**SAME CHECKPOINT model/AdamW/RNG restoration is not uninterrupted continuity and is not a no-rollback claim.** Rank8 restores pilot145; rank16 restores pilot144. Existing raw `no_weights_or_optimizer_reset`/`optimizer_reset` fields describe restoration of those saved states only. They do not erase the discarded later R209 work. Original raw receipts remain unchanged; the machine status now records `rollback_to_saved_checkpoint=true`, `uninterrupted_continuity=false`, exact restored steps and discarded-work bounds together.

- Rank8: LOADED 2026-09-18T05:12:33.726027+00:00; first mixed update146 at 2026-09-18T05:12:37.613947+00:00; restored complete145. Documented discarded R209 suffix: 485 updates / 31040 pair draws, plus0–10 unlogged completed updates and possible partial in-flight work. Original phase/checkpoints retained. This is an **explicit checkpoint rewind**, not fresh weights or a fresh optimizer.
  Current remote root: `/localhome/local-rohing/orch_r210_ovx5_mixed1m_rank8_20260918_continuation2`.
- Rank16: LOADED 2026-09-18T05:10:12.379156+00:00; first mixed update145 at 2026-09-18T05:10:16.753515+00:00; restored complete144. Documented discarded R209 suffix: 486 updates / 31104 pair draws, plus0–10 unlogged completed updates and possible partial in-flight work. Original phase/checkpoints retained. This is an **explicit checkpoint rewind**, not fresh weights or a fresh optimizer.
  Current remote root: `/localhome/local-rohing/orch_r210_ovx5_mixed1m_rank16_20260918_continuation1`.

The R209 writer had no on-demand full-state checkpoint after its pilot. Both frozen owners were stopped only after all exact service processes were suspended and their last receipts captured. Ten-step R209 logging prevents an exact discarded suffix count; the uncertainty is retained rather than hidden. Rank8 first R210 dispatch was refused before LOADED by the unchanged exclusive-GPU scan; its failure is preserved in continuation1. A later fresh privileged scan was clear and continuation2 passed the same admission. No cause is inferred beyond the observed gate refusal. Rank16 was not restarted for this recovery.

## Same documented recipe

- Every global64-pair batch contains16 crossed-scene and48 full-gap within-contest pairs; every rank sees4/12. This is25% of **new R210 pair draws**, not a guarantee of25% normalized loss weight or25% of the entire budget including the retained R209 prefix.
- Both matched positives and donor captions come from the top20% by observed empirical rating (tie-break: vote count then stable caption-family hash) within their TRAIN contest. Donors must belong to a different original scene group; their captions are scored under the recipient scene. No held DEVELOPMENT examples enter sampling or optimizer targets.
- Crossed losses use a **constructed negative assumption**; this does not prove every cross-cartoon caption is invalid. Supervision is on the existing scene-text representation, not a new vision model.
- Same frozen Qwen7B base, rank8/alpha16 versus rank16/alpha32, LR3e-5, global batch64, source-vote reliability weights, and one million retained comparison draws per candidate. No new candidate or fresh AdamW initialization. The retained pre-switch prefixes differ by one update; do not claim perfectly matched histories.
- Every future full checkpoint includes weights plus all-rank AdamW/RNG, and **both** Spearman and exact600case contrasts whether or not it improves. New safe-stop hook is `STOP_AT_SAFE_BOUNDARY` in the current remote root. Selection chooses the best R210 Spearman checkpoint; prior R209 metrics remain explicit baselines.

## Recoverable checkpoint cadence

- Complete R210 checkpoints146/1000(rank8) and145/1000(rank16) are present, including adapter files and four nonempty optimizer/RNG files with matching public rank-step receipts. This refresh checks metadata/file presence, not a new tensor-load restore test during training.
- The unchanged running trainer saves full states on its first mixed update, each1000candidate updates, and3907/7813/11719/15625; both next scheduled checkpoints are2000. The usual1000-update interval is approximately35–36minutes at current throughput, plus diagnostic overhead. No shorter interval is claimed.
- Future intentional transitions must use the already-installed safe-boundary checkpoint hook, not terminate an unsaved suffix and rewind again. No stop marker, signal, restart, or training-code mutation was applied in this refresh. The present trainer cannot hot-change its checkpoint interval; existing periodic saves continue without interruption.
- Both remote trainer hashes match the inspected local trainer: `1a87e43ce4114c841ff37215bac0c2626b878f0d5b615ce88b848fc420e72578`.

## Diagnostics by checkpoint

R213 coverage audit: **4/4 saved full-state R210 checkpoints have completed BOTH diagnostics**; zero saved states missing diagnostic completion and zero incomplete checkpoint directories observed. NEW step1000 diagnostics completed at05:43:24.440393UTC(rank8) and05:41:26.450074UTC(rank16), after855/856 mixed updates and13680/13696 crossed pair draws respectively. These are actual post-training checkpoints, not old pilot/first-update metrics. The next scheduled checkpoint is2000; diagnostic completion forecasts are06:18:55UTC(rank8) and06:17:16UTC(rank16), conditional on current fitting rate and measured mean26second diagnostic cost. The running trainer unconditionally saves full state and executes Spearman plus all600 contrasts before marking completion, including non-improving checkpoints. No restart or training interruption is used to accelerate a diagnostic. A watcher missing a receipt is not evidence that training is absent and does not authorize a relaunch.

Public mixed-only receipt `R213_PUBLIC_CROSSED_CHECKPOINT_RECEIPT_20260918T054635Z.json` excludes all R209 pilot metrics and includes actual update timestamps/rates, live native identities, checkpoint-specific mixed-update counts, aggregate diagnostics, diagnostic coverage, finish/next-checkpoint forecasts, and explicit source-checkpoint path/hash and rewind disclosure. The same public results and paths are posted in COORDINATION under `[Builder/ovx5 R213 PUBLIC CHECKPOINT1000 RECEIPT]`; no private captions or per-example scores are included. Actual latest remote sources are the current arm roots' `training/checkpoint_diagnostics/step_001000/COMPLETE.json`, with full paths in that immutable receipt.

All six contrast columns are wins plus half ties out of100 scored comparisons/type;600 total on the SAME20 held DEVELOPMENT contests. No skipped cases in the receipts below. Spearman is macro within-contest correlation against empirical mean rating on the fixed model-selection panel. These are repeated DEVELOPMENT diagnostics, not fresh confirmatory validation or human humor judgments.

| Rank | Phase | Checkpoint update | Spearman | Other cartoon | Mid-tier | Truncated | Shuffled | Scene description | Nonsense |
|---|---|---|---|---|---|---|---|---|
| 8 | R210_MIX | 146 | 0.273879 | 52.5% | 75.5% | 94.0% | 100.0% | 100.0% | 100.0% |
| 8 | R210_MIX | 1000 | 0.234368 | 85.0% | 59.5% | 84.0% | 100.0% | 100.0% | 97.0% |
| 16 | R210_MIX | 145 | 0.277172 | 48.5% | 71.5% | 95.0% | 100.0% | 100.0% | 100.0% |
| 16 | R210_MIX | 1000 | 0.250950 | 86.0% | 64.0% | 89.0% | 100.0% | 100.0% | 98.0% |

Step1000 shows a repeated-DEVELOPMENT diagnostic tradeoff versus first-mixed checkpoints146/145: other-cartoon accuracy increases to85/86%, while Spearman, mid-tier, truncation and nonsense scores decline. This is not an overall quality improvement or a new promotion/acceptance criterion; higher other-cartoon accuracy does not override unchanged Spearman selection. Current live updates1090/1146 are NOT assigned step1000 scores. Historical R209 baselines remain preserved in `R210_STATUS.json` and immutable earlier observations, omitted from this current mixed-only table to prevent confusion. Complete case-ID hash: `6763a62cf349e969c1dd7ecad0637c8718fef45572eced5a07a50406e3de66ba`. Only aggregates are exported here; private rows and per-example scores remain evaluator-only.

## Files and verification

- Current bounded evidence: `R210_STATUS.json`; immutable observations: `R210_OBSERVATION_*.json`; recipe: `R210_RECIPE.json`.
- Training: `r210_mixed_train.py`; staging: `prepare_r210.py`; explicit preserved transition: `r210_transition.py`; rank8 admission recovery: `recover_r210_rank8.py`; observer: `observe_r210.py`.
- Five focused real receiving CPU tests PASS for each arm with no skips: exact global/local fractions, different groups/strong donor/presented scene, sampler RNG continuation/raw immutability, token-cache scene binding, and real AdamW moment/RNG restoration. All four actual saved optimizer states per arm hash-checked and step-checked. Six admission/arithmetic tests PASS. Actual confinement, loaded state, per-step mixture and checkpoint diagnostics provide the GPU receipts.
- Initial receiving-test preparation with CUDA visibility mistakenly open was preserved and repaired by clearing CVD for CPU checks; no initial-test pass or R210 training was claimed.
- Non-material reporting clarification: seven CPU-only observer regressions previously PASS for explicit rewind terminology, preserving raw receipts, actual-count fractions, distinct LOADED/mix timestamps, and reporting missing/incomplete checkpoint diagnostics rather than silently omitting them. No code, training implementation, or live configuration changed in this R213 refresh. Latest immutable receipt: `R210_OBSERVATION_20260918T054635Z.json`.
