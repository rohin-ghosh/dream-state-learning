# Semantic writer: bounded local mechanistic training audit

Date: 2026-09-12 UTC. Scope: existing source, archived source, fit receipts, and supplied root1 exact-training generations. No source changes, model execution, GPU access, network access, git mutations, scorer re-audit, or experiment launch. This report is the only file created. Main retains liveprobe/manuscript work; no parenting progression is proposed here.

## Finding

**No concrete label-mask, row-routing, gradient-clearing, or optimizer-step bug was found in the inspected implementation. The evidence instead supports successful adaptation of output/termination behavior and global action preference, without demonstrated acquisition of the arbitrary key–mode binding.** This is an acquisition failure on exact training prompts, not merely a held-template generalization failure. It does not prove that no binding information exists anywhere in the adapter; greedy behavior alone cannot establish that stronger statement.

The small terminal training loss is quantitatively compatible with an essentially key-blind two-action policy. One of seven/eight supervised response tokens is the first action-choice token; the remaining tokens can be learned without the association. A key-blind policy can therefore achieve approximately **0.093 mean loss**. The four second-epoch means are **0.097–0.103**. These are online, dropout-active, pre-update losses, not final checkpoint evaluations; the comparison is mechanistic consistency, not an exact decomposition of measured final loss.

## Evidence and provenance

Original evidence root:

`/tmp/astra_semantic_writer_terminal_20260912/astra_semantic_writer_Q0_20260912_attempt1`

Additional evidence:

- `/tmp/astra_exact_train_root1_terminal_20260912/root1`
- `/tmp/astra_exact_train_root1_analysis_20260912.json`
- `/tmp/astra_semantic_writer_source_d160e0b2.tar.gz`
- `/tmp/astra_exact_train_source_4465e537.tar.gz`

I read archive members without extracting them. The original archive's writer, training helper, and carrier source hashes match the original manifest. The current writer and training-helper files are byte-identical to the original d160e0b2 versions. Comparing carrier functions finds only `score` changed; `encode_candidate` is unchanged. The corresponding three files in the 4465e537 supplementary archive match the current files. Thus the supplementary scoring repair does not constitute a retrain or a training-loop/mask repair. I did not inspect or rerun that scoring change.

Key hashes:

| Artifact | SHA-256 |
| --- | --- |
| Original `manifest.json` | `f6fa9060e9ea794309839a8651adc728989c283663070b348c3200acca57a830` |
| Original `fits.json` | `8946700f4b94078bc6d15ffd24cfe29c364783f672e90ff36a69a5b077b78aec` |
| Original/current writer source | `d6ea45ac6bfb5cabe6cbd1224f4cf101e96cbd0e07c029e934c2aa3e03e1ddb0` |
| Original/current training-helper source | `b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8` |
| Root1 supplementary report | `5b349b1b4742f061f0c884ef37b7c4f3478845d46b5f27424c97237d6d492fc2` |

### What the existing fit receipts establish

For all four fits, I independently recomputed the steps-file SHA-256 and mean loss, checked all 256 step/epoch/row coordinates, and checked every saved training encoding against its prompt, response IDs, target, and material row. All checks passed. Each fit has 128 distinct prompt-token sequences, 64 examples per action, eight templates per key–mode pair, two visits per exact prompt, and 1,920 supervised token occurrences. Four fits are four separate adapters, not 1,024 updates to one adapter.

| Fit | First 16 mean | Epoch 1 mean | Epoch 2 mean | Last 16 mean | Saved update norm |
| --- | ---: | ---: | ---: | ---: | ---: |
| r0_plus | 2.216983 | 0.391477 | 0.102662 | 0.098513 | 1.852419 |
| r0_minus | 2.228722 | 0.405064 | 0.099415 | 0.093627 | 1.862776 |
| r1_plus | 2.318376 | 0.389810 | 0.097436 | 0.094745 | 1.885763 |
| r1_minus | 2.600178 | 0.431020 | 0.103306 | 0.112982 | 1.789289 |

No logged loss is zero. Most loss reduction occurs early; the second epoch remains near the key-blind scale rather than showing continuing orders-of-magnitude reduction.

### Root1 exact-training actions: verified from raw generation records

All 384 generation prompts and their prefix IDs match the original r1 training prompts. For both adapters, the raw records' adapter and LoRA hashes agree with their original fit DONE receipts. Action counting distinguishes the action from an optional terminal LF; it does not change the existing parser or scoring rules.

| State | mem2reg | gvn | Correct W+ /128 | Correct W− /128 | Matching held /64 |
| --- | ---: | ---: | ---: | ---: | ---: |
| OFF | 127 | 1 | 65 | 63 | 31 W+; 33 W− |
| r1_plus | 0 | 128 | 64 | 64 | 32 |
| r1_minus | 113 | 15 | 65 | 63 | 34 |

- Plus changes 127 actions relative to OFF, but becomes a **constant gvn policy** and loses one matching answer. Minus changes 16 actions and has exactly OFF's matching correctness.
- Plus and minus disagree on 113 prompts. Because plus is constant, these are precisely minus's 113 mem2reg outputs. This disagreement is not evidence that either adapter recovered the complementary key assignments.
- All generations have legal action text and terminate with EOS. A useful objective-specific observation: **OFF emits no terminal LF on all 128 rows; both adapters emit the trained LF on all 128 rows.** This is direct evidence of learned response-tail behavior despite the already-valid action format. It does not measure how much of the loss decrease came from LF/EOS.
- The existing terminal audit reports native reduction equality, three cleanups, controller absence, and release PASS. Runner elapsed time is 399.4168255 seconds. I read those historical receipts; I did not query live devices or repeat cleanup/reduction.

Root0 exact-training retry results and Main's remaining liveprobe are not prerequisites for these root1 conclusions and were not treated as completed evidence here.

## Implementation audit

### Objective and masks

`organism_v6/semantic_writer_diagnostic.py:195` constructs each fit row from the candidate indexed by that material row's target. W+ and W− have identical prompts and complementary targets. The saved encodings agree with that construction for all 512 rows.

`organism_v6/semantic_carrier_diagnostic.py:141` encodes the rendered chat plus the complete target, masks the chat prefix with `-100`, and leaves every response token, LF, and appended EOS supervised. It checks token-boundary alignment and identical prompt prefixes. Saved labels are exactly `[-100] * prompt_length + response_ids`; the key/mode text remains in the model input. **Masking the prompt from the loss does not hide it from attention or prevent response gradients from depending on it.** No accidental prompt-only supervision or missing action supervision was found.

`organism_v6/multikey_writer_gateway_simple.py:1175` passes unshifted IDs and labels to the causal-LM model with an all-ones padding mask and `use_cache=False`, then uses `output.loss`. This is the ordinary causal-LM label contract: the model's loss implementation supplies the next-token shift. The all-ones 2-D mask means no padding is excluded; it is not itself proof of noncausal attention. No duplicated/manual shift appears in this training helper. I did not execute or instrument the archived Transformers runtime, so this is source/contract inspection, not a newly measured runtime loss-parity or causal-mask test.

### Ordering and exposure

`organism_v6/multikey_writer_gateway_simple.py:148` defines a deterministic hash-based permutation. `:190` applies it to the complete 8-slot × 2-mode × 8-template grid, seed 200 with a root-specific domain. This is **shuffled once deterministically**, not sorted by label. `organism_v6/semantic_writer_diagnostic.py:489` repeats the same 128-row permutation twice, with no per-epoch reshuffle, exactly as the frozen recipe says.

There is no label imbalance in the full grid and no missing key–mode coverage. For r1_plus, the mem2reg counts in consecutive 16-row blocks are `8,5,6,9,9,10,11,6`; r1_minus has their complements. Short-run imbalance and repeated order can interact with batch-one Adam momentum. **Recency/order causing the final bias is a hypothesis, not an established cause.** The global counts alone cannot establish it.

### Optimizer and updates

`organism_v6/semantic_writer_diagnostic.py:474` starts from the clean base, attaches rank-8/alpha-16 LoRA with dropout 0.05 to seven projection types, checks zero-B initialization, validates 392 trainable LoRA tensors with no trainable base parameters, and calls `model.train()`.

AdamW uses learning rate `3e-5`, betas `(0.9,0.999)`, epsilon `1e-8`, weight decay `0.01`, and non-fused/non-foreach execution. There is no scheduler, clipping, packing, or accumulation; each example gets one optimizer step. The base loader selects BF16/eager attention (`organism_v6/multikey_writer_gateway_simple.py:1149`). **The receipts do not establish the actual trainable-adapter/gradient/optimizer-state dtypes; base BF16 alone does not establish BF16 Adam state or rounded-away LoRA updates.** No precision failure is demonstrated.

The helper clears gradients after forward but before backward, which is valid for this ordinary forward/backward loop; no old gradients accumulate into the update. It checks finite loss, present/finite gradients, performs `optimizer.step()`, checks finite trainables, and synchronizes. `lora_tensors` makes detached FP32 CPU clones, so the initial/final norm is not an aliasing artifact. The fit checks a nonzero final delta and saves the adapter (`organism_v6/semantic_writer_diagnostic.py:549`). Evaluation verifies fresh reload tensor identity (`:507`).

These checks demonstrate parameter movement and saved/reloaded adapter identity, not binding-specific gradient flow. Finite gradients can be zero, and a global update norm cannot locate the learned information. The saved adapter config's `inference_mode:true` is not evidence that fitting ran in eval mode; the fit explicitly calls `train()` and the config is the saved artifact.

Existing tests cover masks, recipe facade, and step ordering; the loop and optimizer facade tests mock training (`tests/test_semantic_writer_diagnostic.py:273` and `:321`). They do not establish real-model memorization or per-token loss/gradient parity. No tests were run or added in this audit.

## Why the numerical loss can improve without binding

The saved continuations, including EOS, are:

```text
mem2reg: [6823,25,481,10536,17,1580,198,151645]  (8 tokens)
gvn:     [6823,25,481,21404,77,198,151645]       (7 tokens)
```

Their first three tokens are shared. The first divergent token is `10536` versus `21404`. Once that gold token is supplied by teacher forcing, the suffix can be predicted from the gold action prefix without knowing the key's association. Shared formatting and LF/EOS also require no arbitrary key binding. Thus there are only 256 first-choice supervision occurrences per fit among 1,920 supervised token occurrences; the whole response is not 1,920 independent binding lessons.

Under standard per-example mean-token causal cross entropy, consider an idealized key-blind model that assigns mem2reg branch probability `p`, gvn probability `1-p`, and predicts all other supervised tokens perfectly. With the actual 64/64 row balance:

```text
L_blind(p) = -0.5 * [log(p)/8 + log(1-p)/7]
L_blind(0.5) = 0.0928322117
argmin_p L_blind(p) = 7/15
min L_blind(p) = 0.0925343718
```

This is an illustrative **key-blind optimum**, not a lower bound for a model that learns the labels; correct binding could drive loss lower. Unequal target lengths mildly favor gvn under the mean-token objective even with balanced rows. That small weighting effect cannot, by itself, explain the opposite majority behavior of the two adapters. Moreover, near-tie probabilities can produce a constant greedy action without confident predictions. The raw action counts do not reveal confidence.

**Evidence:** loss rapidly approaches this scale; response-tail behavior changes; root1 remains chance-like on exact trained contexts while action priors change dramatically. **Interpretation:** output-distribution calibration without demonstrated conditional acquisition is sufficient to explain the results. **Unresolved hypotheses:** interference from nondecision gradients, repeated-order/momentum effects, insufficient exposure for the key–mode interaction, or an uninstrumented runtime/numerical problem. The receipts cannot rank those causes decisively.

The association is an interaction: `orientation[slot] XOR mode XOR mapping_bit` (`organism_v6/multikey_writer_gateway_simple.py:152`). Key alone and mode alone are balanced. A learner can improve formatting and its global prior while failing to learn this interaction. Neither better loss nor large plus/minus disagreement is a substitute for the conditional behavioral result.

## One recommended next bounded test — not a demonstrated repair

**Run one paired, instrumented full-response-versus-first-choice loss ablation on the unchanged root1 W+ task.** This directly tests whether the present response objective is obstructing conditional acquisition, without simplifying the dataset, changing the base, increasing the step budget, or adjusting a success threshold. Proposal only: no implementation or launch is authorized or performed by this audit.

1. Use two fresh, identically initialized seed-1 adapters, the exact pinned base/tokenizer, all original 128 r1_plus rows in their original order, and exactly 256 updates each. Keep LoRA, dropout, optimizer, precision, and input sequences unchanged. Arm A reproduces the original full-response labels. Arm B changes **only the label mask**: supervise the first divergent action token and mask all other positions. With prompt length P, that label is at `P+3` and is predicted from logits at `P+2`. Keep ordinary full-vocabulary causal CE; do not substitute a two-candidate scorer or generate/insert a binding table.
2. Before any launch, CPU-check every decision index against both saved candidate sequences, unchanged row/prompt/target hashes, one live label in arm B, identical initialization and optimizer membership, and the shifted-label convention. Put any future implementation in a separately versioned supplementary harness; do not modify the frozen Q0 recipe, original masks, artifacts, or report. Follow Main's applicable provenance/pre-GPU process.
3. From each training forward, log first-choice CE, the original full-response mean CE, nondecision-token NLL, and the signed gold-versus-other action-token logit margin. Record actual adapter/gradient/Adam-state dtypes and first/last-step gradient/update norms by projection type. This distinguishes real conditional learning from lower aggregate loss or a global offset; it does not duplicate Main's scorer/liveprobe audit.
4. At initialization and after step 256, record dropout-off first-choice margins and ordinary unprefilled greedy generations on the same 128 exact prompts, grouped by all 16 key–mode cells and eight templates, including action counts and format validity. The initialization control can be shared after confirming identical initial tensor hashes. No held/sealed result should select a checkpoint or tune this test. Hard cap: **two fits, 512 total updates, at most 384 exact-prompt generations, one 30-minute wall-clock bound including evaluation/cleanup, no automatic retry or extension**. A timeout is incomplete evidence, not permission to broaden the test.
5. Interpret the contrast prospectively: improvement confined to global action frequency is still not binding. Conditional margin/output improvement in B but not A supports this objective as a limiting factor under the same data/update budget; it does not identify whether removing tail gradients or removing length weighting mattered more. If both remain near chance, this particular objective explanation is weakened, not a proof of absent adapter capacity or a specific optimizer defect. If the control fails to reproduce the qualitative original behavior, resolve that reproducibility discrepancy before attributing an arm difference.

Multiplying the original scalar loss by seven/eight is **not** the proposed repair: Adam is approximately invariant to a uniform gradient rescaling. Removing nondecision gradient contributions and unequal per-action token normalization is a substantive objective ablation, not guaranteed to help. The original Q0 outcome and acceptance criteria remain unchanged regardless of its result. Do not relabel this supplementary diagnostic as Q0 success, parenting, retention, or a broader storage claim.
