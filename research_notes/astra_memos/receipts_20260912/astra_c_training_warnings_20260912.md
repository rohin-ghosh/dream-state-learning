# Two C-training warnings — bounded read-only diagnosis

**Date:** September 12, 2026. **Window:** 18:56:50–18:58:40 UTC; final receipt predicates at 18:58:39–40 UTC. This sidecar concerns only node1 R4_B_seed606_AC and node2 R4_B_seed603_AC. No inventory refresh, backup hashing, GPU queries, model calls, package operations, launches, kills, remote/repository writes, or Git operations were performed. Node3 was not contacted. The sole authored file is this report. Internal hostnames and credentials are omitted.

## Finding

**Both C fits completed successfully as unpacked, one-item-per-sequence training. Both failed the requested packed-recipe check.** The triggering condition is exactly:

```text
config.pack == true
AND packing.mode != "block4d_by_group"
```

The underlying native isolation self-test returned `NOT_ISOLATED`, so the trainer deliberately disabled packing before training. The shell wrapper then warned after the completed fit because the requested packing contract was not met. **Neither warning was caused by dropped target tokens, an empty corpus, nonfinite batches, or a Python traceback.** Existing DONE markers certify training completion, not passage of the packing acceptance check.

Both encompassing AC jobs remain **pending downstream completion**, with live C_tmem worker processes, no C_tmem DONE/manifest, no probes, and no whole-job summary at the final receipt sample. Do not report completed behavioral outcomes. Do not label either existing C adapter as a passing packed/isolated treatment; equally, do not infer that it trained with cross-example leakage, crashed, or produced universally unusable weights.

## Exact runs, ownership, and status

All paths below are remote home-relative paths on the indicated node.

| Evidence | Node1 | Node2 |
|---|---|---|
| Run | `~/v6_out/pretest_write_ab_AC/R4_B_seed606` | `~/v6_out/pretest_write_ab_AC/R4_B_seed603` |
| Queue receipt | `~/queue/running/0038_fable_fill_pretest_R4_B_seed606_AC.job` | `~/queue/running/0060_fable_fill_pretest_R4_B_seed603_AC.job` |
| Queue PID | 3262676 | 1439579 |
| Active write_ab shell PID | 3262681 | 1439584 |
| CUDA assignment read from shell environment | `CUDA_VISIBLE_DEVICES=1` | `CUDA_VISIBLE_DEVICES=1` |
| Queue start UTC | 16:44:53 | 17:14:23 |
| C fit result | `rc=0`, 5866 seconds in `timings.jsonl` | `rc=0`, 4162 seconds in `timings.jsonl` |
| C log final mtime UTC | 18:35:51.916469 | 18:35:19.827248 |
| Queue warning log mtime UTC | 18:35:53.054484 | 18:35:20.528251 |
| Current downstream C_tmem worker PID / PPID | 3843239 / 3262681 | 1909067 / 1439584 |
| Worker state at 18:58:00–01 UTC | R | S, `futex_do_wait` |
| C DONE / train_C marker | Both present | Both present |
| C_tmem DONE / train_C_tmem marker | Both absent | Both absent |
| C_tmem train_manifest / train_meta | Both absent | Both absent |
| Probe files / summary at 18:58:39–40 UTC | 0 / absent | 0 / absent |

The listed worker PIDs are **C_tmem**, not the already-exited C trainer. The sampled C timings receipt does not record its historical trainer PID; none is invented here. The audit did not claim that a sleeping live worker is hung or that a runnable worker guarantees progress.

The shell environments have `WRITE_AB_CELLS=A,C` and `WRITE_AB_OUT=~/v6_out/pretest_write_ab_AC`. `WRITE_AB_STRICT`, `WRITE_AB_MAXLEN`, and `WRITE_AB_TMEM` are unset. The inspected wrapper supplies defaults **STRICT=0, MAXLEN=7168, TMEM=1**. Readable ancestry and task-specific command arguments confirm these are the same two warning-bearing jobs, not unrelated processes.

## Error and receipt evidence

### Node1 R4_B_seed606

`~/queue/logs/fable_fill_pretest_R4_B_seed606_AC.out`, lines 17–20:

```text
[write_ab] done train_C in 5866s
[write_ab] C: steps=19726 target_tokens=1060292 total=2877234 tok/s=492.3 train_s=5844.9 packing=fallback_one_item_per_sequence (NOT_ISOLATED) isolation=NOT_ISOLATED items_split=0 truncation={'overflow': 'split', 'items_truncated': 0, 'context_tokens_dropped': 0, 'target_tokens_dropped': 0, 'items_split': 0, 'segments_from_splits': 0, 'max_segment_tokens': 522}
[write_ab]   - packing=fallback_one_item_per_sequence (NOT_ISOLATED) isolation=NOT_ISOLATED (fell back to one item per sequence)
[write_ab] WARNING train check failed for C (see above)
```

Run-relative `train_C.out:22` records `packing DISABLED: isolation check NOT_ISOLATED — falling back to one item per sequence`; line 1997 records `TRAIN_DONE`. **Zero `Traceback` occurrences** in the inspected C log. `adapters/C/train_manifest.json` records:

- `diff_first=3.1875`, `diff_second=3.1875`, tolerance `0.25` — both 12.75 times the configured tolerance.
- Negative-control difference `44.875`; `informative=true`, `ok=false`, `ran=true`, `verdict=NOT_ISOLATED`.
- `n_sequences=19726`, `mean_segments_per_sequence=1`, `n_groups=67`, `mean_fill=0.0203`.
- 19726 optimizer steps/micro-batches, one epoch, **0 nonfinite batches**, 2877234 observed training tokens. No truncation or skipped-no-target items.

### Node2 R4_B_seed603

`~/queue/logs/fable_fill_pretest_R4_B_seed603_AC.out`, lines 17–20:

```text
[write_ab] done train_C in 4162s
[write_ab] C: steps=16888 target_tokens=657954 total=2229517 tok/s=537.7 train_s=4146.3 packing=fallback_one_item_per_sequence (NOT_ISOLATED) isolation=NOT_ISOLATED items_split=0 truncation={'overflow': 'split', 'items_truncated': 0, 'context_tokens_dropped': 0, 'target_tokens_dropped': 0, 'items_split': 0, 'segments_from_splits': 0, 'max_segment_tokens': 524}
[write_ab]   - packing=fallback_one_item_per_sequence (NOT_ISOLATED) isolation=NOT_ISOLATED (fell back to one item per sequence)
[write_ab] WARNING train check failed for C (see above)
```

Run-relative `train_C.out:29` records the same packing-disabled fallback; line 1720 records `TRAIN_DONE`. **Zero `Traceback` occurrences** in the inspected C log. Its manifest records:

- `diff_first=3.1875`, `diff_second=3.1875`, tolerance `0.25`.
- Negative-control difference `45.125`; `informative=true`, `ok=false`, `ran=true`, `verdict=NOT_ISOLATED`.
- `n_sequences=16888`, `mean_segments_per_sequence=1`, `n_groups=67`, `mean_fill=0.0184`.
- 16888 optimizer steps/micro-batches, one epoch, **0 nonfinite batches**, 2229517 observed training tokens. No truncation or skipped-no-target items.

### Shared effective recipe

Both C manifests request BF16, rank 32, alpha 64 (effective), dropout 0.05, all seven listed attention/FFN projection module types across all 28 layers, AdamW, learning rate 1e-4, one epoch, batch size 1, accumulation 1, max length 7168, chat template, EOS targets, seed 0, overflow splitting, `pack=true`, and `isolation_check=auto`. Recorded library versions: torch **2.13.0+cu130**, transformers **5.5.3**, peft **0.20.0**. These are receipt values, not imports or fresh runtime-package probes.

A standalone standard-library check of the two manifest predicates at 18:58:39–40 UTC returned, for each run:

```json
{"target_tokens_dropped_failure": false, "requested_packing_mode_failure": true}
```

This diagnoses the wrapper failure exactly; it does not execute the training checker shell or load a model.

## Code path and root-cause boundary

Line anchors here refer to the **read remote source**, not the different current local trainer.

1. `organism_v6/train_adapter_v3.py:434` compares each of two truncated-to-48-token segments run alone with a packed block-masked run; a no-block packed run is the negative control. `to_tensors` at line 420 uses a 2-D mask for solo calls, but a 4-D block mask plus explicit reset positions for the packed call. The decision is maximum absolute logit difference, not a training exception.
2. At line 582, zero/default `isolation_tol` resolves to **0.25 for BF16**. At lines 584–587, failed isolation switches both `mask_mode` and `pack` to **2d / false**, before the optimizer loop. The manifest at lines 598–604 records the fallback. Therefore `NOT_ISOLATED` describes the **rejected packed path**, not proof that the subsequently used one-item-per-sequence path mixed examples.
3. The trainer saves the adapter, manifest, metadata, and DONE at lines 653–667. These steps still succeed for the deliberate fallback. The generic recipe label `v3_masked_packed` remains present, so it cannot override the more specific `packing.mode` evidence.
4. `gpu/write_ab.sh:65` creates the successful subprocess step marker; `check_train` at lines 87–98 subsequently rejects nonzero dropped targets or a requested-but-unmet block4d mode. `warn_or_fail` at lines 67–69 exits only if `WRITE_AB_STRICT=1`. Here it is 0, so the workflow advances to C_tmem at line 170.
5. Importantly, the native trainer's `--isolation-check strict` still **falls back**, rather than aborting the fit, for `NOT_ISOLATED`; it additionally treats an inconclusive check as fallback-worthy. It is not by itself a pre-fit fail-closed execution gate. The shell's `WRITE_AB_STRICT=1` would stop only **after** the expensive completed fit/check, and could stop earlier on a different warning.

**What remains unlocalized:** whether the rejected native comparison reflects BF16/attention-backend numerical-path differences, mask/position handling, or another native-path incompatibility. The first segment also differs by 3.1875, which makes attributing everything specifically to second-segment cross-boundary attention unwarranted. The negative control is informative, but it does not distinguish these causes. The loader at remote lines 757–759 does not explicitly pin an attention implementation, and the receipt does not identify the actual selected backend. Do not assert a library bug or claim that increasing tolerance would fix isolation. No model-based reproduction was attempted.

## Downstream C_tmem status — separate from the C warning

The next stage intentionally uses `--no-pack`, rank/alpha 6, dropout 0, FFN last four layers, SVD-initialized frozen A, SGD 5e-4, five epochs, batch 16, chat template, max length 2048. It is not an automatic retry of C and does not require packed block4d mode when `config.pack=false`.

Both live workers have allocator OOM **warnings** in `train_C_tmem.out`, but no Python traceback, terminal return-code receipt, completed manifest, or DONE. Examples, with device ordinal as printed:

- Node1 **18:45:04 UTC**: allocation of **5081399296 bytes**, free **1561919488**, total **47695331328**; log mtime 18:45:04.936395 UTC. Five allocator-warning lines were observed, starting 18:36:49.
- Node2 **18:39:26 UTC**: allocation of **5100273664 bytes**, free **551354368**, total **47697690624**; log mtime 18:39:26.006265 UTC. Three allocator-warning lines were observed, starting 18:36:11.

The logs say “device 0”; that is consistent with the process-local ordinal under `CUDA_VISIBLE_DEVICES=1`, **not evidence of a claim on physical GPU0**. No GPU API was called to investigate it.

Exact SVD initialization is a plausible pressure point: remote `lora_svd_init.py:48` makes float32 weights, line 56 performs full reduced `torch.linalg.svd`, and `train_adapter_v3.py:559` runs SVD initialization before optimizer training. There was no `[svd-init]` completion or training-step line visible in the sampled C_tmem logs. **This is a hypothesis, not a native-stack diagnosis:** logging defaults to buffered `print`, and neither log silence nor a single process state establishes zero optimizer progress or a hang. The allocator warnings must not be promoted to an unhandled OOM/crash verdict while the processes remain live.

## Outcome classification

| Question | Answer for both runs |
|---|---|
| Did C training finish? | Yes: TRAIN_DONE, rc=0, adapter DONE, one epoch, zero recorded nonfinite batches. |
| Did C meet its requested packed-isolation contract? | **No. Failed acceptance condition remains attached to these exact artifacts.** |
| Was target loss caused by truncation? | No recorded dropped target/context tokens or truncated/split items in these C manifests. |
| Are behavioral results available? | **No. Zero probe files and no summary in each run at the final sample.** |
| Is the entire AC job terminal/failed? | No terminal failure is evidenced; C_tmem workers and queue running receipts persist. |
| Is C_tmem itself invalid for packing? | Not established; it deliberately requests no packing and has no terminal manifest yet. |
| Can these C adapters be relabeled as successful packed controls? | **No.** An unpacked diagnostic interpretation must retain the deviation and revisit comparison/budget matching; no retrospective gate pass. |

## Minimal next diagnostic or repair — proposed only

1. **Immediate, no GPU/no code change:** retain this receipt-based failed-packed-contract label with the two existing artifacts. Preserve C DONE/markers and warning logs. Let Main/owner manage the existing processes; do not change their scripts, environments, markers, or queue state. Read eventual terminal manifests/return codes once available rather than waiting in this sidecar. Adjacent log lines also mention A_v3 warnings; they were not separately audited or given an inferred validity verdict in this bounded C-only task.
2. **For the packing mismatch:** the smallest future diagnostic is a separately authorized, immutable, bounded comparison of the same two segments across solo 2-D, solo explicit 4-D, and packed-reset 4-D paths, with recorded selected backend, dtype, positions, mask shape, and the existing negative control. It would require model calls and was **not run here**. CPU-only inspection of mask geometry and receipt schemas can precede it, but cannot establish native logit equivalence. Preserve the existing 0.25 tolerance; do not disable the check or inflate tolerance to turn these artifacts green.
3. **For fail-closed behavior on future work:** the existing `WRITE_AB_STRICT=1` is a configuration option, not a repair of these adapters and not an early cheap gate. If packed mode is required, propose a fresh-source pre-optimizer abort on failed required isolation, with a regression test separating `NOT_ISOLATED`, `mask_refused`, and inconclusive checks; preserve the explicitly allowed fallback path only where the declared recipe permits it. Changing acceptance behavior requires the applicable project authorization/review; no source change is made by this report.
4. **If the intended diagnostic does not need packing:** an explicitly declared no-pack future recipe can avoid requesting an unmet packed guarantee. It is not retroactive validation and must account for altered sequence batching, optimizer steps, token weighting, and wall time against its controls. The generic wrapper currently requests packing for C, so merely passing unrelated environment variables or re-running in the same marked directory is not a repair. No duplicate run is recommended now.
5. **For pending C_tmem allocator warnings:** first obtain the eventual terminal/progress evidence. If a real terminal memory failure is confirmed, diagnose exact-SVD allocation separately in a fresh bounded task. Switching to randomized low-rank SVD, changing batch size, or moving/reusing initialization changes numerical or training behavior; none should be silently applied to active sources or justified solely from the present warning. An exact-initialization-preserving allocation/caching approach would also need provenance and numerical checks before use.

No historical results should be deleted, no running source edited, and no adapter automatically retrained or promoted from this diagnosis.

## Evidence identity and limits

Only small warning-related files were hashed; no backup or model-weight hashing was performed.

- Node1 C manifest SHA256: `386552eb40184295332cca022f97a1091aa923142e1d774290ab604d1a432f79`.
- Node2 C manifest SHA256: `885587bfaf56acc52bcd10312672c9e0c38b754c1b9a596f244801d18f2bf395`.
- Both nodes' currently read `gpu/write_ab.sh`: `f4a0ecce4ae8330cdb4ec6a1527fee5f353d338b25a5fec262c906275e8acfc6` — matches local wrapper at audit time.
- Both nodes' currently read `organism_v6/train_adapter_v3.py`: `02f47008c676f6aa361a7e18bf30f5010391174d7a0dd9e648532e16cd55e169`.
- Local current trainer differs: `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`. Relevant remote code was read directly rather than assuming local/native parity.
- Node1 currently read `organism_v6/lora_svd_init.py`: `af98ffa4bc10bc7a6a25d89399ed846df6995245067c82011e1caf7cc1af98f6`. Node2 SVD source was not separately hash-verified.
- The manifest key set has no source-code hash binding. Current mutable checkout bytes plus consistent receipts explain the observed control flow, but do not prove exact launch-time source identity. No Git provenance was read or modified. Corpus hashes exist in the C manifests; training examples, sealed panels, and model weights were not opened.

**Resolution:** warning condition localized and independently reproduced from existing JSON. Native numerical root cause and downstream completion remain open. No operational action or scientific acceptance is implied.
