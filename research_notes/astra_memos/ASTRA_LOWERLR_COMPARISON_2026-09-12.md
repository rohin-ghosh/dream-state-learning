# A1 bank0 lower-LR acquisition/spill follow-up — proposal only

September 12, 2026, independent read-only follow-up; local evidence checks completed at approximately 10:04 UTC. **Main owns the decision, resources, scheduling, and execution. Nothing is queued or launched.** This is useful parallel diagnostic work while the coached-material test runs, not a reason to interrupt it.

## 1. Smallest informative contrast

Propose **two new fits and two original full bank0 evaluations**, at learning rates **3e-5 and 1e-5**, compared with the **already-completed A1 F_r16k16 training-seed2 bank0 1e-4** result. Do not rerun the baseline, add banks/seeds, regenerate material, add negatives/replay, or search prompts. This changes only training LR. It tests whether reducing the update rate improves the acquisition/spill tradeoff at the original training duration; it is not an equal-convergence or equal-total-update experiment.

Reuse the **exact oracle-material corpus bytes**, including its original filler, lesson rows, multiplicities, order, masks, and event references. Preserve frozen Qwen2.5-7B-Instruct, fresh LoRA initialization under training seed2, rank8, three full epochs, all original optimizer/tokenization settings, and inference lambda1. No initialization from the trained baseline adapter. No new framework, scientific invariant, threshold, cue, or claim.

**The existing result does not establish a selective writer.** The recorded bank0 baseline has I_d_frame **1.921469872774875**, paired-owner 95% interval **[1.2026075500735869, 2.682502692054215]**, and frame spill **0.41553692023821664**: G9 fails. These are read from the existing frozen analysis, not recomputed here. This oracle-material test cannot establish that the current child/coached/selective writer works, qualify W0/W1, or support a clean-lineage/H1/H2 claim.

## 2. Exact recovered baseline and immutable provenance

Aliases used below:

- `BASE = /localhome/local-rohing/v6_out/astra_A1_memory_dose_S1_F_r16k16_ts2_20260912` on node2.
- Original source run: `/localhome/local-rohing/v6_out/memory_dose_S1`.
- `CORPUS_REL = corpora/bank0/F_r16k16/across/sleep4/corpus.json`.
- `ADAPTER_REL = adapters/bank0/F_r16k16/across/sleep4/r8`.
- `EVAL_REL = eval/bank0__F_r16k16__across__sleep4__r8__lam1.json`.
- Local frozen counterpart: `/tmp/astra_seed_bank0_evidence_20260912/runs/astra_A1_memory_dose_S1_F_r16k16_ts2_20260912`.
- Frozen experiment source: `/localhome/local-rohing/astra_sources/f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d`; corresponding selected source files are in the local capsule's `experiment_code/f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d/`.

Original preparation receipt: September 12, 2026, **06:31:32.988565 UTC**, source-bank seed **1**, training seed **2**, prepared banks0/1/2. Do not confuse these seeds or substitute the D32 source-bank-seed0 corpus. The separate 100-step throughput probe's default seed0 is not the scientific fit's seed.

| Artifact relative to BASE unless noted | SHA-256 |
|---|---|
| `corpora/bank0/F_r16k16/across/sleep4/corpus.json` (7,288,476 bytes) | `f2388eaf9c2285d6c5fe109445a599a4fefb5d9b1ca0ce6223ef78bede01c37d` |
| `banks/bank0.json` | `87851da0b4229c1bed9523b653845873197866f5157031846e914d44dbf8fc31` |
| `banks/bank1.json` | `b63d649fa16a2b921c694e88a379fa01b174d5c101111c0ddaaf26e9c098e362` |
| `banks/bank2.json` | `a4ca0376a7cba887d2f571083ec5f4b0aa36b8fa366c1060fb01579a803a76e4` |
| `distractor.json` | `4ad56576f6d0a9ae211207ab06daef767ccca6a3968c7d9542505406137a9fdc` |
| `manifest.json` | `b2d82e650c51f9c453f7978a56840eade533f253e732b6c897c43b690ccaf35f` |
| `seed_run_receipt.json` | `2939b7812d36f59d571659d02c2088fb727d87a59965b5cae13bef39d27dfc3d` |
| `adapters/bank0/F_r16k16/across/sleep4/r8/train_meta.json` | `b046eb082ec8bc488d202e94fc1a09108e35b00d32a45bf2464534a8b5e3493c` |
| `eval/bank0__F_r16k16__across__sleep4__r8__lam1.json` | `970e1be480133cb81d62b53e9762bd4ef77b5c0b1d11e3a85d21b7e3dab64386` |
| Frozen/current `organism_v6/memory_dose.py` | `ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3` |
| Frozen/current `gpu/memory_dose_frames.sh` | `7b535f3098c455fa4e839ce6f250b1e889539731a8f16da2cb53562aaca777ab` |
| Frozen/current `gpu/prepare_memory_seed_run.py` | `1f216a2ca7392f47cb2067121350606dc227beb8ee887a2d794169bf2cf24d9e` |
| Local full source archive `/tmp/astra_source_20260912T0631Z.tgz` | `bd5f1f418888e6dcc28bd333d4c872b33f9214a40df3809bc2567072e3c62a06` |

The source archive hash and recorded source commit agree with `research_notes/astra_memos/ASTRA_RUNS_2026-09-12.jsonl:1`. This is receipt-backed source identity, not a Git inspection. The local capsule captured node2 files at **07:17:04–07:17:07 UTC**. I verified all **eight** original receipt-listed inputs and **25** relevant capture-manifest files (selected A1 evidence, original experiment source, and job record); all matched. Current local memory-dose, runbook, and preparation-helper hashes also equal their captured frozen versions.

Capsule bindings:

- `CAPTURE_MANIFEST.json`: `3cb1c3f8b6bac72bb0e0fcfbf73c78355c4b0249964b82cab8ecb6d9a3d31d34`.
- Existing `analysis.json`: `e7bd30eef0e37d9d164e43d2badfb8e9ceebc25a55d89384659ba42a4ac5ed65`.
- Existing `ANALYSIS_RECEIPT.json`: `5ef7369b1f44ade81240087674687543ea961461154dd9f10eda5a1f3348ee7d`.

**Provenance limitation:** this capsule does not contain adapter/base weights, a saved pretraining LoRA initialization, or an execution-time dependency/model-snapshot digest. Training seed2 plus unchanged code/recipe reproduces the initialization procedure, not proof of bit-identical historical tensors across a changed runtime. Main should use the same node2 environment and cached model/tokenizer; record their resolved identity without claiming a historical seal not present in the receipts. The node paths are historical, locally evidenced paths, not newly checked remote availability.

### Original command, not an instruction to rerun it

The exact queued command body below is recovered from `queue/running/0045_astra_A1_memory_dose_S1_F_r16k16_ts2_20260912.job` in the capsule. It started at 06:31:48 UTC on node2 with queue-substituted GPU2. `{gpu}` is the original queue placeholder, not a resource assignment for this proposal.

```text
PYTHONDONTWRITEBYTECODE=1 REPO='/localhome/local-rohing/astra_sources/f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d' RUN='/localhome/local-rohing/v6_out/astra_A1_memory_dose_S1_F_r16k16_ts2_20260912' SEED=2 MODEL=hf F_RANK=8 F_CELLS=F_r16k16 CF_CELLS=F_r16k16 F_BANKS='0 1 2' F_TOKEN_BUDGET=250000 MAX_FIT_MIN=25 bash '/localhome/local-rohing/astra_sources/f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d/gpu/memory_dose_frames.sh' {gpu} fits
```

For bank0, that runbook expanded to `train --model hf --rank 8 --epochs 3 --lr 1e-4 --seed 2`, using the corpus and adapter paths above; it then ran `evaluate --bank 0 --model hf --lambdas 1 --cell F_r16k16 --arm across --sleep 4 --rank 8`. Evaluation's omitted defaults were **seed0, adjacent-subset4, batch-size16**. No training max-step cap or gradient checkpointing was supplied. Python was the runbook default `/localhome/local-rohing/v2/venv/bin/python`.

### Exact recipe and exposure

- Corpus short identity `15adaeff18a685c0`; item-multiset identity `55e5bca9dadd19ea`; chronological, unshuffled, frames/occurrences, 16 forms ×16 repeats, zero negatives.
- **12,924 rows**: 5,376 fact, 1,344 lesson, 4,096 colour filler, 2,108 colourless filler. Preserve all of them. **249,995 corpus tokens**, 220,592 content tokens, **250,000 corpus budget**. The unchanged legacy manifest says 65,536; that is not this F corpus's cap and must not cause a rebuild or metadata rewrite.
- Frozen base `Qwen/Qwen2.5-7B-Instruct`; rank8, alpha16, dropout0.05, no bias; targets `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj` (not attention-only).
- Original ordinary weighted token NLL; joint context+target encoding; AdamW with unchanged library defaults other than LR; BF16; batch4; max-length512; in-order batches; no scheduler, clipping, gradient checkpointing, or accumulation change.
- Three full epochs: **3 × ceil(12,924/4) = 9,693 optimizer steps**; actual baseline **749,985 input tokens / 711,213 supervised tokens**, zero training boundary straddles, zero truncated items. The corpus's own token-count metadata is not interchangeable with the fit's actual supervised-token count.
- New arms must also complete 9,693 steps. Omit `--max-steps` to preserve the original full-epoch behavior; do not use the 100-step profiling cap as training. Inspect completed metadata for skipped/nonfinite work rather than assuming requested epochs imply matching steps.

## 3. CLI feasibility and a reporting trap

**No code change is needed.** Current and frozen `memory_dose.py:4332` expose `train --lr`; `train_command` passes LR to `train_hf`, which passes it to AdamW (`:2630`). I invoked current `train --help` and `evaluate --help`, and the frozen preparation helper's `--check-only --banks 0 --training-seed 2` against the captured A1 source. All exited0; check-only created no destination. No training/evaluation/report or test suite was run. Both prospective Bash blocks below passed `bash -n` syntax validation without execution.

Do **not** set an `LR` environment variable and call `memory_dose_frames.sh`: its fit command at `gpu/memory_dose_frames.sh:126` hardcodes `--lr 1e-4`. Invoke the existing Python CLI directly. Fresh roots are essential: `train_command` immediately accepts an existing `DONE`, and eval/report filenames and grouping do not encode LR. Do not mix rates under one root or copy the old `adapters/index.json`/`DONE` into a treatment root.

The separate `research_notes/analysis/astra_seed_campaign.py:227` eligibility validator **hardcodes training lr==0.0001**. It will mark genuine lower-rate fits incompatible. Do not patch it, falsify their LR, or claim its eligibility approval. Use the **original native `memory_dose evaluate` plus `memory_dose report --seed 0`**, whose G9 calculation has no LR restriction, and inspect the new source/fit receipts separately. Original manifest/receipt `source_lora.lr=0.0001` remains historical source metadata; the treatment's actual LR belongs in its fit command and `train_meta.json`.

## 4. Executable commands for main only

These are **prospective node2 commands**, not executed by this proposal. Main first checks current leases/resources and its ordinary CPU/provenance requirements, and logs the normal dated `[Builder]` receipt in `research_loop/COORDINATION.md`. No resource reservation, queue mutation, new approval gate, or pause of coached work is requested here.

Use these two **new** run roots; the preparation helper refuses any existing destination. Their current remote absence has not been asserted:

```text
/localhome/local-rohing/v6_out/astra_A1_memory_dose_S1_F_r16k16_ts2_b0_lr3e5_20260912_attempt1
/localhome/local-rohing/v6_out/astra_A1_memory_dose_S1_F_r16k16_ts2_b0_lr1e5_20260912_attempt1
```

Run the following preparation block in a node2 Bash session. It verifies the historical inputs/code and copies source bytes using the existing helper. It neither regenerates a corpus nor copies a trained adapter. Keep the same shell for the execution block, or re-establish its variables there.

```bash
set -euo pipefail
REPO=/localhome/local-rohing/astra_sources/f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d
BASE=/localhome/local-rohing/v6_out/astra_A1_memory_dose_S1_F_r16k16_ts2_20260912
PY=/localhome/local-rohing/v2/venv/bin/python
RUN3=/localhome/local-rohing/v6_out/astra_A1_memory_dose_S1_F_r16k16_ts2_b0_lr3e5_20260912_attempt1
RUN1=/localhome/local-rohing/v6_out/astra_A1_memory_dose_S1_F_r16k16_ts2_b0_lr1e5_20260912_attempt1
CORPUS_REL=corpora/bank0/F_r16k16/across/sleep4/corpus.json
ADAPTER_REL=adapters/bank0/F_r16k16/across/sleep4/r8
TAG=bank0__F_r16k16__across__sleep4__r8
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
export V6_MODEL=Qwen/Qwen2.5-7B-Instruct
test -x "$PY"
test ! -e "$RUN3"
test ! -e "$RUN1"
cat <<HASHES | sha256sum --check --strict
ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3  $REPO/organism_v6/memory_dose.py
1f216a2ca7392f47cb2067121350606dc227beb8ee887a2d794169bf2cf24d9e  $REPO/gpu/prepare_memory_seed_run.py
f2388eaf9c2285d6c5fe109445a599a4fefb5d9b1ca0ce6223ef78bede01c37d  $BASE/$CORPUS_REL
87851da0b4229c1bed9523b653845873197866f5157031846e914d44dbf8fc31  $BASE/banks/bank0.json
b63d649fa16a2b921c694e88a379fa01b174d5c101111c0ddaaf26e9c098e362  $BASE/banks/bank1.json
a4ca0376a7cba887d2f571083ec5f4b0aa36b8fa366c1060fb01579a803a76e4  $BASE/banks/bank2.json
4ad56576f6d0a9ae211207ab06daef767ccca6a3968c7d9542505406137a9fdc  $BASE/distractor.json
b2d82e650c51f9c453f7978a56840eade533f253e732b6c897c43b690ccaf35f  $BASE/manifest.json
2939b7812d36f59d571659d02c2088fb727d87a59965b5cae13bef39d27dfc3d  $BASE/seed_run_receipt.json
b046eb082ec8bc488d202e94fc1a09108e35b00d32a45bf2464534a8b5e3493c  $BASE/$ADAPTER_REL/train_meta.json
970e1be480133cb81d62b53e9762bd4ef77b5c0b1d11e3a85d21b7e3dab64386  $BASE/eval/${TAG}__lam1.json
HASHES
for RUN in "$RUN3" "$RUN1"; do
  "$PY" -B "$REPO/gpu/prepare_memory_seed_run.py" \
    --source "$BASE" --destination "$RUN" --training-seed 2 \
    --cell F_r16k16 --banks 0 --check-only
done
for RUN in "$RUN3" "$RUN1"; do
  "$PY" -B "$REPO/gpu/prepare_memory_seed_run.py" \
    --source "$BASE" --destination "$RUN" --training-seed 2 \
    --cell F_r16k16 --banks 0
  mkdir "$RUN/logs" "$RUN/provenance"
  cp "$BASE/seed_run_receipt.json" "$RUN/provenance/baseline_seed_run_receipt.json"
  cp "$BASE/$ADAPTER_REL/train_meta.json" "$RUN/provenance/baseline_train_meta.json"
  cp "$BASE/eval/${TAG}__lam1.json" "$RUN/provenance/baseline_eval.json"
  cp "$REPO/organism_v6/memory_dose.py" "$RUN/provenance/memory_dose.py"
  cp "$REPO/gpu/prepare_memory_seed_run.py" "$RUN/provenance/prepare_memory_seed_run.py"
done
```

Required source copies are **manifest + distractor + all three bank JSONs + only bank0's original F corpus**. The helper verifies source identities/event joins and writes copies and its new receipt read-only. All three bank JSONs remain because source validation and native reporting load the manifest's three-bank roster. This does **not** fit or score banks1/2. No child `generations.json` is required for oracle F material. Baseline output copies stay under `provenance/`, never `eval/`, avoiding the native report's first-file-per-slot deduplication.

Main supplies an available GPU index as `GPU` under its own allocator. The following block deliberately has no GPU-selection/default/queue logic; it fails if no assignment is supplied. It executes the two arms sequentially on that assigned GPU, with separate roots and no separate throughput fits. The first100 steps' normal training throughput log remains available.

```bash
: "${GPU:?Main must provide the assigned node2 GPU index}"
export CUDA_VISIBLE_DEVICES="$GPU"
export CUDA_HOME=/usr/local/cuda-13.0
export PATH=/usr/local/cuda-13.0/bin:/localhome/local-rohing/v2/venv/bin:$PATH
for SPEC in "$RUN3:3e-5" "$RUN1:1e-5"; do
  IFS=: read -r RUN RATE <<< "$SPEC"
  (
    set -euo pipefail
    set -x
    date -u '+%Y-%m-%dT%H:%M:%SZ'
    sha256sum "$REPO/organism_v6/memory_dose.py" "$RUN/$CORPUS_REL"
    "$PY" -B "$REPO/organism_v6/memory_dose.py" train \
      --run-dir "$RUN" --corpus "$RUN/$CORPUS_REL" --out "$RUN/$ADAPTER_REL" \
      --model hf --rank 8 --epochs 3 --lr "$RATE" --seed 2 --no-reuse
    test -f "$RUN/$ADAPTER_REL/DONE"
    jq -e --argjson rate "$RATE" \
      '.lr == $rate and .seed == 2 and .rank == 8 and .epochs == 3
       and .steps == 9693 and .total_steps == 9693 and .n_items == 12924
       and .tokens == 749985 and .supervised_tokens == 711213
       and .boundary_straddles == 0 and .truncated_items == 0
       and .measure_only == false and .throughput.grad_checkpoint == false
       and .corpus_sha == "15adaeff18a685c0" and .items_sha == "55e5bca9dadd19ea"' \
      "$RUN/$ADAPTER_REL/train_meta.json"
    "$PY" -B "$REPO/organism_v6/memory_dose.py" evaluate \
      --run-dir "$RUN" --bank 0 --adapter "$RUN/$ADAPTER_REL" --tag "$TAG" \
      --model hf --lambdas 1 --adjacent-subset 4 --batch-size 16 --seed 0 \
      --cell F_r16k16 --arm across --sleep 4 --rank 8
    jq -e '.n_cues == 1313 and .template_check == true and .abstain_check.ok == true' \
      "$RUN/eval/${TAG}__lam1.json"
    "$PY" -B "$REPO/organism_v6/memory_dose.py" report --run-dir "$RUN" --seed 0
    sha256sum "$RUN/seed_run_receipt.json" "$RUN/$CORPUS_REL" \
      "$RUN/$ADAPTER_REL/train_meta.json" "$RUN/eval/${TAG}__lam1.json" \
      "$RUN/report/report.json" > "$RUN/provenance/result_sha256.txt"
    date -u '+%Y-%m-%dT%H:%M:%SZ'
  ) > "$RUN/logs/lowerlr_execution.out" 2>&1
done
```

Do not re-execute either block on a partly/completely used root: preserve failures and choose a new attempt root if main elects to retry. The assertions check the requested match, not new scientific acceptance criteria. If tokenization/steps/cue inventory differ, preserve the discrepancy and do not label that arm LR-only. Revalidate source hashes at execution if preparation and execution are separated. The commands assume the recorded node2 Python environment, cached base/tokenizer, `jq`, and CUDA installation are still present; none was remotely installed or verified here.

If original node paths have disappeared, recover the exact source-input files from the verified local capsule and use the hash-bound full source archive above. Do not substitute a newly generated S1/D32 corpus. Main can transport them under its existing operational authorization; this follow-up performed no transport.

## 5. Original evaluator, controls, and interpretation

Preserve **all 1,313 existing cues**, including the original question/lesson controls, and use the original HF OFF/ON scoring at **lambda1**. No lambda sweep, standalone OFF-only GPU run, prompt variant, cue filtering, new negatives, or replay ablation. Evaluation already measures adapter-disabled OFF and adapter-enabled ON; keep both per arm. Compare OFF values and source/cue identities with the baseline to detect runtime drift; do not silently substitute baseline OFF scores into a new evaluation.

Report **bank0 only**, each LR separately, from `report/F_r16k16__across__r8__lam1.md` and `report/report.json`. The report's single-bank “pooled” value is just that one bank, not additional replication. Do not import other eval files or pool the three LRs as independent evidence.

Unchanged **G9_frame_binding** (`memory_dose.py:3069`, `:3353`, and native `evaluate_gates` at `:3420`): mean dose16 owner-frame ON–OFF log-odds gain minus its same-owner look-alike-frame gain, with the original **2,000-resample paired-owner percentile95% interval, bootstrap seed0**, whose lower bound must be **>0**, **and frame spill <=0.03**. There are **16 dose16 owners**. Spill is the equal-weight mean of the absolute conditional-probability-change means over **48 exposed look-alike controls, 16 unexposed car owners, and 48 exposed bicycle controls**. It is not a pooled mean over112 rows. Retain all64 owners, 16 at each dose0/1/4/16. `frame_similar` is an unseen look-alike control, not an exposed-partner swapped-ID experiment. Preserve the original question-cue swapped-owner controls as well; do not relabel them as a new frame assay.

For each of the three rates, show the existing outputs side by side:

- Dose16 owner-frame conditional P OFF/ON and change, candidate mass OFF/ON, I_d_frame and its original within-fit owner interval.
- All three spill components and total spill, plus unchanged G9 pass/fail. Retain original abstention/G11 outputs, without making them a new selection endpoint.
- Dose0/1/4/16 acquisition pattern, actual training steps/tokens, LR, fit/eval wall time, and source hashes.

The existing baseline dose16 owner-frame conditional P is **0.2596495149075415 OFF / 0.6853229710498591 ON**; candidate mass is **0.00873765625 OFF / 0.99815843125 ON**. Its spill components are **0.41657727683077644 similar / 0.3213085371998146 unexposed / 0.5087249466840589 bicycle**. These contextualize what the lower-rate arms retain or lose; conditional probability alone can hide candidate-mass changes.

Interpret without inventing a new cutoff: lower spill with collapsed acquisition is weaker writing/under-acquisition, not evidence of selectivity. Lower spill with retained acquisition but G9 failure is only a descriptive tradeoff improvement. Even an unchanged-G9 pass would be a one-bank, one-initialization, oracle-material diagnostic result, not a working learned selective writer, independent-seed confidence, or headline claim. The two LRs are exploratory follow-ups, not confirmatory replicates; no winner-dependent extra sweep is included.

## 6. Cost and bounded handoff

Exact baseline metadata: **1,327.3s training +199.0s evaluation =1,526.3s**, approximately **25.44 A40-minutes per arm**. Two matched arms predict **3,052.6s =50.88 A40-minutes =0.848 A40-hours** of measured core fit/eval work. LR does not change the requested step count, so no runtime saving is assumed. Training wall_seconds excludes initial model/tokenizer load/encoding and final adapter save; queue, custody, startup, and contention add overhead. A reasonable same-node planning allowance is **about60–70 minutes total on one available A40**, not a guarantee or reservation. The historical100-step estimate was23.2min per fit versus22.12min observed. `MAX_FIT_MIN=25` in the old runbook was a projection check, not a watchdog; the direct commands add no timeout or kill behavior.

The baseline is read-only: **zero baseline retraining/re-evaluation**, zero extra profiler fits, zero three-bank reruns. Main may schedule the two independent roots separately if resources warrant; each fit still uses only one assigned GPU. Nothing here authorizes a lease/extension or displacement of coached-material work.

**Work actually performed for this proposal:** read the decision memo/current CLI/frozen source/receipts; SHA-256 and source-only validation; CLI help; write this `/tmp` document. No repo/source edits, Git commands, remote wrappers, model calls, scientific metric replay, GPU launches/kills, queue actions, or changes to existing evidence. Local evidence was sufficient. Main decides whether to run the diagnostic and owns any subsequent documentation, provenance capture, and resource use.
