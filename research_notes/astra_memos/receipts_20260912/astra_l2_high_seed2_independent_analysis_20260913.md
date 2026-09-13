# SEQ151 — independent HF seed2-high receipt analysis

**EDITSTOP — original pinned reducer replay PASS, byte-for-byte.** Existing teacher-forcing receipts only:192candidate forwards,0updates, native elapsed275.985244seconds. No native/model/tokenizer calls, generation, collection or fitting in this sidecar.

## Findings

| State/view | First correct old+new /16 | First ties | Full correct old+new /16 | Full ties | Full gold mean NLL/token | First-decision gold NLL/token |
|---|---|---|---|---|---|---|
| OFF/train | 4+4 | 0 | 4+4 | 0 | 0.214222937 | 2.784746377 |
| OFF/readout | 4+4 | 0 | 4+4 | 0 | 0.159850602 | 2.077656952 |
| fit1/train | 5+4 | 3 | 6+5 | 0 | 0.050957675 | 0.661325403 |
| fit1/readout | 4+3 | 3 | 4+5 | 0 | 0.052315287 | 0.679619167 |
| fit2_PROMOTE/train | 8+7 | 0 | 8+7 | 0 | 0.014267924 | 0.185290794 |
| fit2_PROMOTE/readout | 4+4 | 0 | 4+4 | 0 | 0.146301391 | 1.901743319 |

Fit2PROMOTE strongly favors the correct legal continuation on15/16TRAIN prefixes (old8/8,new7/8) but8/16READOUT (old4/8,new4/8), by both first divergence and full likelihood sum with no ties. This supports a checkpoint-specific train-versus-readout access discrepancy; these data do not show equally weak TRAIN and READOUT. It does not identify the cause, establish generalization/internalization or demonstrate native greedy success.
TRAIN miss: index12 `slot_26be197c42658089c3496c2d`, gold first margin -0.500000030, gold full margin -0.500038057. First-choice train-correct/readout-wrong:8; reverse:1.
Fit1 saw8keys and fit2 saw16. Fit1 first choices include3exact ties in each view; full sums yield different counts with no ties. The fit1 new8prefixes were not training exposures. No tie tolerance or threshold was tuned.
Original native vLLM baseline and every PROMOTE/SHADOW report remain4/8old+4/8new. HF teacher-forced first/full legal-candidate choices are not full-vocabulary greedy generation; no HF-vLLM numerical parity or endpoint replacement is claimed.

## Length-aware evidence

Candidate token lengths including EOS: `{'move_54b50509ad73': [14], 'move_7bc22e03caee': [12]}`. First divergence index2 (zero-based); continuations have multiple differing positions and unequal12/14-token lengths. All192candidate traces pass original finite-logprob, full assistant-mask/EOS, and1024-token boundary validators.
Full likelihood sums and per-token means are different statistics. Common suffix/EOS losses condition on different action histories. Small normalized full loss can dilute decision uncertainty; ln(2)/13 is only an unmeasured reference hypothesis.

| State/view | Common gold mean NLL | Decision-span gold mean NLL | EOS gold mean NLL |
|---|---|---|---|
| OFF/train | 0.000050565 | 0.278474648 | 0.000144029 |
| OFF/readout | 0.000133538 | 0.207765721 | 0.000389654 |
| fit1/train | 0.000374489 | 0.066132630 | 0.000118347 |
| fit1/readout | 0.000159663 | 0.067961975 | 0.000161714 |
| fit2_PROMOTE/train | 0.000063923 | 0.018529124 | 0.000047770 |
| fit2_PROMOTE/readout | 0.000058153 | 0.190174363 | 0.000153611 |

First-choice action-index distributions in public order `('move_54b50509ad73', 'move_7bc22e03caee')`: `{"OFF": {"readout": {"0": 16}, "train": {"0": 16}}, "fit1": {"readout": {"0": 13, "None": 3}, "train": {"0": 3, "1": 10, "None": 3}}, "fit2_PROMOTE": {"readout": {"0": 16}, "train": {"0": 7, "1": 9}}}`. Fit2READOUT prefers the same legal action on all16slots; this is forced-candidate preference, not a native-greedy observation.

## Receipt, tensor and prompt verification

- Complete original reduction reproduced every saved report byte, including per-slot likelihood margins, loss decompositions, OFF contrasts and original CLI metadata. No alternate reducer/protocol or generation was substituted.
- Three distinct fresh-worker PIDs369565/369832/370075,64forwards/0updates each; sequential nonoverlapping times, controller/worker deadlines, launch PID/UUID receipts and archived precheck/release returncode0 checks agree. Native complete275.985244seconds is inside the1200second envelope. No current process/reservation checks made.
- Frozen local source inventory matches all4SOURCE_FILES pins. Collection COMPLETE128calls/3fits/100updates, seed2/LR1e-4, original plan/seal/base/world and candidate file pins verified. All527files in the original training-root seal rehashed from preserved tar. Worker hashes join terminal/report.worker_files.
- Independently parsed both saved safetensors files and verified all392tensor shapes/dtypes/source byte hashes per adapter (784total). Standard-library arrays independently reproduced F32→BF16 round-to-nearest-even byte hashes and matched both converted and actual-loaded receipt entries for all784tensors. No torch/model/safetensors framework import. Saved adapter inventories also match original candidate hashes. This strengthens receipt joins but is not a fresh inspection of native model memory.
- All32paired-candidate cases have a shared cross-worker encoding hash. Verified64original native request/response prompt joins across wake1/wake2_PROMOTE and baseline/report1_PROMOTE/report2_PROMOTE, against prepared calls.json and unchanged core.action_prompt plus the exact original runtime.messages system/user wrapper. wake==train. All16TRAIN candidate input_ids/labels/native prefixes match saved fit2 training audits; original fit1 overlap target bytes agree on8keys. EOS and target masks validated by unchanged reducer. No tokenizer/encoder rerun.
- A preliminary local audit assertion mistakenly compared prepared messages to a user-only list. The pinned runtime actually supplies a generic system message plus user message. The final check uses the exact frozen messages function and passes; no receipt/prompt/scorer was altered to make it pass.

## Exact pins

| Artifact | SHA256 |
|---|---|
| Diagnostic tar `gpu_artifacts_local/l2_public_record_20260913/astra_l2_access_high_seed2_20260913_attempt1.tar` | `6865c968dbef113e12570ced2333b74fbd79379a4a6f30b16f65a3ef4c6df527` |
| Saved report `/tmp/astra_l2_access_high_seed2_report_20260913.json` | `9cb95809b5ff658c45e39a21a522433d666b2696af8feda698ef2d951604346b` |
| Original diagnostic/reducer `/tmp/astra_l2_access_high_seed2_20260913.py` | `d319c53aeeaf45743d77e87af30eafe1ae8e2f111d35e440c8c0b1402b4b2525` |
| Probe handoff `/tmp/astra_l2_access_high_seed2_20260913_handoff.md` | `6b803ff37166ed1c616652bdb2d007ec6e6755722b1241fb7e3faffd6935ec6a` |
| Original training tar `gpu_artifacts_local/l2_public_record_20260913/astra_l2_lr_seed2_high_attempt1.tar` | `d5f91bc56a57a48aad204e1dd3dd8b972c58b97f16d518627e726f8f8cf7082c` |
| Original collection `/tmp/l2_lr_seed2_high_20260913_attempt1_collected` | `24f6e79530b575a8923e5b1145f2e26d7cd95590ceebf9d12b6fd79013ebbd7e` |
| Original plan | `74569b1e8c3e0330e0c4f387120fedd4d9f71406366d8b5459088a35ab1a3593` |
| Original seal | `c5ddc5585d33e1ffd6f1bcce46d9b6a2b23bfed334e7117c5e83586cf9fb9a2d` |
| Shared cases | `4644578efc36a24f181a1adffd31fabdcac07e936723b435c72b532c87eeea21` |
| Worker OFF | `b563e15cb37c670cb3ecb71ecab39d9884ddc04801a4a268315e0ac8fbaaabe9` |
| Worker fit1 | `da4f812c9d41ba4d26a89523a19bd9256fa04088bdc5928b8f84842aa346c58f` |
| fit1 adapter safetensors | `ab021e17fec623fd77d36adf441b8869b06413d892f7fa2c53a4105287994d32` |
| Worker fit2_PROMOTE | `70543fe22f65a9d58b5efbdc15a593acf49164ac359be4028d86695b115d56b7` |
| fit2_PROMOTE adapter safetensors | `94e2bb58cff753dd8500f227b8172a59e51122a9bb556d9e230f8e9812946c63` |

## Reproduction and limits

Local-only method: check probe hash; frozen_source(local pinned snapshot); collection_metadata(local receipt); load pure core and build_world(2026091301,2026091302); read three JSON receipts from tar; reduce_receipts unchanged; append original_vllm_reports/original_plan_sha256/worker_files exactly as original CLI; compare encoded bytes with saved report. Hash every sealed original file, inspect saved safetensor byte ranges and conversion hashes, and join recorded prepared/captured/assistant-mask data. No worker(), native_model(), hf_forward(), prepare(), tokenizer or collection invocation.
Recorded native routing/frozen-eval/logit/tensor assertions were not independently rerun on a model. Base weights, GPU environment and full tokenizer/encoder/epoch-order replay were not newly audited. The native worker’s original guard receipts remain authoritative; this is deterministic reduction and source/custody consistency, not independent numerical reproduction of HF forward passes.
This is a different saved learner-seed2/high-LR checkpoint, not isolated causal evidence for LR versus seed or a specific access mechanism. No G1/H1/H2, general learning, parenting, internalization, original endpoint promotion, or native greedy claim. No new outputs or target/selection tuning. SEQ151 reserved, not150.
Only `/tmp/astra_l2_high_seed2_independent_analysis_20260913.md` created; it is the final handoff. SEQ149 files remain frozen at their previously reported hashes. All original inputs unchanged.
