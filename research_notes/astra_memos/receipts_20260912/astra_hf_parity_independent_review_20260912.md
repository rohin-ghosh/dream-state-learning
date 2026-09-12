# Independent bounded HF numerical / inherited-token audit

Date: 2026-09-12. **Verdict: PASS, within the evidence and claim scope below.**

The reported numerical results reproduce from the raw float32 arrays. No numerical correction is required. The result is HF internal prefix/teacher-forced consistency plus agreement with inherited vLLM first generated tokens, NOT full numerical HF–vLLM logit parity. Cost reporting must distinguish the worker window from the full reservation.

## Scope and method

Read-only, offline audit using Python standard-library CPU arithmetic, JSON, SHA-256, and in-memory tar reads. I did not import or execute the supplied model-running script, run model inference, use a GPU, access the network, edit the repository, or invoke Git. This report is the only file written. Existing artifacts were preserved.

Primary evidence:

- `/tmp/astra_fundamental_hf_parity_terminal_20260912.tgz`
- `/tmp/astra_fundamental_hf_parity_terminal_20260912.tgz.validation.json`
- Extracted root: `/tmp/astra_hf_parity_terminal_20260912/astra_diagnostics/astra_fundamental_hf_parity_20260912_attempt1`
- `/tmp/astra_fundamental_hf_parity_20260912.py`, inspected as source only.

To independently check the inherited captures rather than trust their copied summaries, I also read only the `teach/` subtree of the already-local `/tmp/astra_fundamental_memory_terminal_20260912.tgz`. No OFF/other-checkpoint results were analyzed. Its archive SHA-256 is `a3c2bc8ba3a97a4f4b7e73f0a818f7b162872675d1fd577bc0ea4be4df5da378`; its relevant 47 file hashes are pinned by the primary plan.

## Custody and loaded-state checks

- Primary archive SHA-256 independently matches the supplied value: `54ec0bf1613e67d6256062a24e1ed30fe2b49bfa73a5675d1b83c0b9d4653e32`.
- All 48 archive file hashes equal the validation inventory and corresponding extracted-file hashes. All 35 data files covered by `run/data/manifest.json` match their hashes, with exact data-file coverage excluding the manifest itself.
- Plan hash matches its seal and reduction: `05b6f8f906d1009977ba1439a5ca2db20036faed04ad2491e2a9a2f6ef7fd27f`. Data-manifest hash matches reduction capture hash: `e9d2db3cb319e8f5a730cea70c754fe53a12c1a0f7f17d955e74ed90fd025570`.
- Supplied script hash matches the plan's sidecar pin: `e296c7965f6e7a6ff477deafddbbbbaa42457810ca9e9522ece4421951e98b25`.
- Independently compared all 392 adapter tensor inventory records: source = expected-after-conversion = loaded = state-after, including names, shapes, dtypes, and SHA-256 values. All are `torch.float32`; conversion map is empty; total recorded adapter parameters are 20,185,088. Receipts declare bf16 base, frozen parameters, eval mode, exact loaded check, and zero optimizer steps. The script explicitly checks the loaded PEFT tensors and post-forward inventory.
- Qualification: these are authenticated, internally consistent execution inventories, not an independent reload or rehash of the actual model/adapter tensor bytes. Those weights are not in the primary terminal bundle. No claim is made to independently authenticate upstream model origin or the entire training history.

## Raw numerical recomputation

There are exactly 16 ordered cases, `train-memory-000` through `train-memory-015`. Each `.f32` file has 1,824,768 bytes: three little-endian float32 vectors of vocabulary width 152,064. All 7,299,072 stored values are finite. The vectors are prefix-color, full-input color, and full-input EOS; they are not all sequence-position logits.

I independently decoded every vector and computed full-vocabulary log probabilities using binary64 stable log-sum-exp with `math.fsum`, without renormalizing over only the four colors. I recomputed both color summaries, color/EOS NLL, response mean NLL, full-vocabulary argmax, gold-versus-red/vLLM logit margins, prefix/full differences, and HF reported-loss differences. These equal the saved per-case metrics and reduction rows exactly under this arithmetic; aggregate values reproduce the main summary.

| Quantity | Independently reproduced result |
|---|---:|
| HF full-vocabulary prefix argmax | red / token 1151 on 16/16 |
| HF gold accuracy | 4/16 |
| HF first-token agreement with inherited vLLM | 16/16 |
| Mean gold-color NLL | 1.5662938430630773 |
| Mean teacher-forced EOS NLL | 0.0002199387172154843 |
| Mean two-target response NLL | 0.7832568908901464 |
| Maximum prefix/full absolute logit difference | 0.0 |
| Maximum absolute HF-loss minus recomputed loss | 5.402754261751852e-7 |

The largest HF loss discrepancy occurs on `train-memory-010`; its signed difference is negative. Correct cases are 006, 009, 013, and 014. Every prefix/full gold-logprob difference is also zero.

### Causal indexing and forward count

Every prefix has 42 tokens; each full input has 44. Full inputs equal prefix + gold color + EOS, with labels exactly 42 ignored positions followed by those two target IDs. Independently enumerating nonignored shifted labels gives color at logit index 41 and EOS at logit index 42 (zero-based). The metadata's color/EOS positions 42/43 are target positions, not predictor-logit positions. No off-by-one error was found.

The source runs one prefix-only forward and one full labeled forward per case: **16 prefix + 16 full = 32 forwards**, not 32 per mode. The manifest/plan/reduction record 32; all 16 complete raw triplets are present. This verifies the recorded execution structure, not a new independently instrumented inference trace. HF loss is compared with `(color_NLL + EOS_NLL) / 2`, not color-only NLL. EOS is conditioned on the gold color, not necessarily the generated red token.

## Actual inherited SEQ100 comparison

All 47 `teach/` files in the local inherited terminal archive match the primary plan's `seq100_files` inventory, with no missing or extra files. Its plan seal, data-manifest hashes, and backend identity binding also check out.

All 16 original request and response JSON objects equal the primary plan's embedded captures. The original plan's requests, rendered prompts, and token prefixes match case-by-case; expected labels and source event IDs match too. All 32 prompt/response value seals reproduce using the producer's sorted JSON plus terminal-newline encoding. An initial exploratory compact-JSON hash check failed; checking the actual encoding resolved that mismatch, with no artifact corruption found.

The original requests specify temperature 0.0, overriding the identity's default temperature 0.7. Every captured output is `[1151, 151645]`, text `red`, rather than an assumed or reconstructed vLLM prediction. Thus vLLM also has 4/16 accuracy, while **16/16 means agreement**, not correctness.

The inherited and HF plans have identical model paths and all 14 model-file pins, identical adapter paths and all six adapter-file pins. The adapter weights pin is `d73e8578f62de68ed657474c70fc09c09aaad50a4ff11a66773e50fc702163b2`. They identify the original seed0 teach adapter and Qwen2.5-7B-Instruct snapshot `a09a35458c702b33eeacc393d103063234e8bc28`; the HF plan pins the original seed0 plan `d5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e`. These establish captured loader-input custody and exact native-prefix equality, not independent inspection of vLLM's in-memory weights.

## Claims and cost scope

Permitted conclusion: on these 16 in-sample original training prompts and this one checkpoint, stored HF prefix and teacher-forced color logits agree exactly; HF prefers red on all cases and its first-token argmax agrees with the actual inherited vLLM generation on every case. The two-target causal loss calculation is numerically consistent to the measured residual.

Not established: numerical full-backend logit/probability parity (vLLM captures contain generated tokens, not full-vocabulary logits); complete autoregressive HF response parity; latent absence of learned information; dropped training labels; a unique cause of red preference; held-out performance; parenting efficacy or H1/H2; behavior at any other checkpoint. The present two-target label mask does not retrospectively prove all training masks were correct. Small teacher-forced EOS NLL does not diagnose the cause of color errors.

The original HF run records 32 forwards, zero new vLLM calls, and zero optimizer steps. Its supervised worker/cleanup window is **64.69976138100174 seconds**, not the full reservation. `main_release.json` records **141.936394 seconds** full reservation, independently reproduced by subtracting launch `2026-09-12T19:06:31.752098+00:00` from release `2026-09-12T19:08:53.688492+00:00`. Do not present 64.70 seconds as the complete reservation cost. Completion receipts report successful worker exit, empty owned group, absent GPU processes, and verified reservation release; this is a historical receipt audit, not a live GPU inspection. Dollar cost is not established without billing-rate evidence. Inherited vLLM generations are prior work, not new calls charged to this HF audit.

**Disposition:** PASS for the bounded numerical, causal-index, artifact-custody, and inherited-first-token checks. No scientific-claim expansion, new experiment, or other-checkpoint conclusion is authorized by this review.
