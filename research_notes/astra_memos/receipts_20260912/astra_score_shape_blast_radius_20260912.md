# Score-shape blast-radius audit — 2026-09-12

## Scope and decision

Read-only source/caller audit for Main. This file is the only new artifact.
No repository edits, GPU/model calls, git, network, native-test repetition,
gate changes, historical reclassification, or launch authorization.
References below are repository-relative paths and current source line numbers,
except where explicitly marked historical. Source hashes appear at the end.
This is a bounded map of inspected implementations, not a census proving that
every historical deployment used these bytes or that every backend is safe.

**Bottom line:** the measured semantic scorer defect does not automatically
invalidate memory-dose/frame retrieval, memory-preservation evaluation, original
W0, or generated solve endpoints. Important distinctions:

1. Historical semantic carrier/writer scoring used unequal-length, separate
   complete-continuation forwards: this is the directly implicated implementation.
2. Memory-dose has both a same-prefix single-next-token fast path and a
   full-continuation, length-sorted batched slow path. Only the latter has the
   analogous candidate-dependent shape exposure; classify actual encoded rows.
3. Original W0 uses separate full-continuation forwards **but enforces equal
   complete masks/lengths and identical context IDs**. It is not the measured
   unequal-length case.
4. Memory-preservation's KL is a full-vocabulary next-token comparison, not
   candidate assembly. Its cached teacher batch-of-four versus natural-length
   singleton student is a distinct numerical-shape concern worth one small check.
5. Writer-interface calibration is generation-only. Generated solve observations
   are not products of the defective likelihood summation. Score-selected context
   can nevertheless indirectly affect generation, notably in LANDs C2r.

Main reports native localization to BF16 sequence-shape sensitivity, not missing
causal masking, on the original semantic r0-plus checkpoint. Same-length future
padding removed shared-prefix discrepancies there; FP32 reduced natural-length
discrepancies. This audit does not generalize that measurement to other models,
assays, checkpoints, batches, or historical package versions. The old semantic
likelihood interpretation remains invalid; any repaired rescore is supplementary.

## 1. Historical semantic carrier / semantic writer — direct exposure

- Historical `organism_v6/semantic_carrier_diagnostic.py:332`, `score()`:
  one full input per candidate, separate forwards, BF16 model, all-ones 2D mask,
  `use_cache=False`, FP32 full-vocabulary log-softmax, correctly shifted target
  logprobs summed through LF and EOS. Candidate response lengths are eight versus
  seven tokens in the captured semantic writer. No common total length or
  cross-candidate prefix-consistency check existed.
- Encoder: `semantic_carrier_diagnostic.py:141`, `encode_candidate()`, rejects
  boundary straddles and verifies exact prompt prefixes, but unlike W0 does not
  require equal candidate lengths. This distinction is essential.
- Carrier caller: current `semantic_carrier_diagnostic.py:462`, `worker()`, calls
  `score()` at line 487; generation separately calls `cal._generate()` at 485.
  `candidate_choice()` at 271 converts candidate sums to an argmax;
  `reduce_records()` at 284 includes recognition/score-generation agreement.
  The carrier panel has 64 scoring requests and 80 generations. Its historical
  score path is structurally exposed; this audit does not assert a measured
  numerical failure in that earlier carrier capsule.
- Writer caller: `organism_v6/semantic_writer_diagnostic.py:522`, `worker()`, calls
  `carrier.score()` at 580. `load_eval_model()` at 507 uses the frozen BF16 eager
  loader, fresh adapter loading and eval mode. `score_sums()` at 329 and
  `reduce_records()` at 342 feed per-key conditional log-q gains, raw target
  gains, target margins and conditional locality. The measured writer panel has
  832 scores across OFF and four adapters, alongside 880 separate generations.
  Families: primary held forms, missing mode, unsupported mode, neighbour key,
  wrong root; copy is generation-only.
- Generation-based BA, opposite-map BA, OFF generation gain, validity and copy
  correctness are computed from parsed generated actions, not candidate argmax
  (`semantic_writer_diagnostic.py:357`). Composite conclusions that also require
  likelihood gates cannot be rescued by this distinction.

Current repaired `score()` remains at line 332, hash
`a05da09e8f2720907eb277f928e84ec095a754119144a6b2ecbd38360a969f98`.
It aligns future EOS padding and positions, leaves original targets untouched,
and checks finite values, shared-prefix distributions and disjoint mass.
Historical deployed bytes are not changed by this source update.
Main's `gpu/astra_semantic_rescore.py:53`, `worker()`, calls the repaired scorer
at 74; `merge_records()` at 90 combines new scores with unchanged original
generations. No outcome from that running supplement is assumed here.

## 2. Original W0 — separate forwards, already equal shape

Exact path:
`organism_v6/multikey_writer_gateway_simple.py:1289 evaluation_worker()`
→ `score_request()` at 1253
→ `token_pair()` at 291
→ `encode_candidate()` at 267.

`score_request()` separately forwards the two complete strings `ACT: a0\n` and
`ACT: a1\n`, including terminal EOS, with FP32 log-softmax after BF16 eager
computation (`load_hf_model()` at 1149). However, `token_pair()` asserts the two
boolean supervision-mask **lists are identical**, which includes equal total
length and target positions, and separately asserts identical masked context IDs.
Unequal candidate tokenization must reject before model scoring. Batch size is
one for both forwards, all tokens have attention-mask value one, and neither
call uses cache. No explicit positions are supplied; inputs have no padding.

Therefore: **separate full forwards, but not separately variable-length inputs**.
There is no native numerical-failure finding for W0 in this audit. It lacks the
new full shared-prefix-distribution check, so equal shape is a structural
protection, not an all-stack numerical certification.

Assay map: `build_requests()` at 340 creates primary/spill score+generation rows,
plus OFF oracle generations. `profile_plan()` at 876 declares 384 primary and
240 spill score requests; generation counts are 384 primary, 240 spill, 256
oracle. `reduce_records()` at 489 uses score values for conditional log-q gains,
margins and spill TV; generated actions supply BA, oracle BA, validity and
multiple-ACT observations. Spill families include missing, unsupported,
neighbour and unrelated. `generate_request()` at 1271 is the separate native
generation function. The semantic-specific padding repair does not modify W0.

## 3. Memory-dose — route by actual tokens, not by assay name

Implementation: `organism_v6/memory_dose.py:2307 HFScorer` (class definition),
`_forward_last()` at 2355, `candidate_logprobs()` at 2375.
The loader uses BF16, eval mode and optional PEFT; attention implementation is
not explicitly pinned in this constructor. These settings differ from the
measured semantic stack.

### Fast path: one distribution per prompt

The exact routing predicate is that **every** candidate has `L == 1` and
`joint_ids[:-1] == independently_encoded_prompt_ids`. `_forward_last()` receives
only the prompt IDs, keeps one logits position, and all candidates for that
prompt are gathered from the same row of one next-token distribution. No
candidate future is forwarded. Prompts are length-sorted and left-padded in
batches; explicit position IDs are cumulative nonpadding positions.

This avoids cross-candidate, different-shape distribution assembly. Batch-shape
numerical sensitivity is still a general possibility across separate executions,
but not a demonstrated failure here. Exact equality of OFF/ON distributions is
not expected when an adapter is intentionally active.

Likely/intended fast-path assay rows:
- Colour/case variants (`colour_candidates()` at 778) for fact paraphrases,
  in-context/distractor and adjacent cues, repaint, similar-owner, bicycle,
  generic, base-rate, exact-short and exact-ante cues.
- `frame`, `frame_similar`, `frame_bicycle`: bare canonical completion prefixes
  with space-prefixed colour variants.
- Abstention `[" not"]`: an extra same-prefix candidate row. The deployed-token
  check in `abstain_token_check()` at 2961 verifies one token/no straddle for
  representative car/bicycle prefixes. The scorer's actual per-row routing
  predicate, not that representative check alone, is decisive.

Do not promote comments saying “single tokens” into a historical tokenizer
measurement. An unexpected split or changed prompt prefix sends the whole
candidate group to the slow path.

### Slow path: candidate rows can have different execution shapes

`candidate_logprobs()` at 2395 constructs all slow `(prompt,candidate)` pairs,
sorts them by full joint-input length, and chunks globally by batch size. Each
chunk's `_forward_last()` uses `T=max(row lengths)` and
`keep=max(candidate lengths)+1`; candidates are full teacher-forced continuations,
left-padded with masked pads and reset nonpadding positions. Target indexing
uses the final `L` shifted predictions. No common shape is enforced **per original
candidate group**: its rows may land in different chunks, with different batch
size, T, keep and/or left-pad offsets. Even a shared chunk is not identical to
semantic future-only padding when original lengths differ.

Analogous exposure, **not an established numerical defect**:
- `textfit_short` / `textfit_ante`, generated by `textfit_candidates()` at 2789:
  full researcher-provided target-sentence likelihoods. Used for training-text
  fit / storage-versus-extraction interpretation, not actual generation.
- `lesson_trigger`, `lesson_notrigger`, `lesson_reversed`, `lesson_exact`:
  complete action strings/casings from `action_candidates()` at 2779, terminated
  by IM_END for chat or period for completion. Token lengths must be inspected;
  multi-token execution does not itself imply unequal lengths.
- Any ostensibly single-token cue failing the fast-path predicate.

Separate conditioning caveat: `joint_candidate_ids()` at 2283 allows tokens
straddling the prompt/answer boundary and counts them as answer tokens; its slow
tokenizer fallback separately encodes prompt and answer. Such rows must not be
assumed to share the exact same token history simply because their prompt text
matches. This is independent of BF16 shape sensitivity.

### Callers and what records can establish

- `generate_run()` at 928 → `measure_off()` at 752 → `candidate_logprobs()`:
  OFF priors are measured before bank assignment; `assign_colours()` at 722
  consumes priors. If any of these actual rows took the slow path, exposure could
  reach prior stratification/assignment, not just post-fit reporting. No such
  routing failure is asserted here.
- `evaluate_command()` at 2999 → `build_cues()` at 2810 → `score_cues()` at 2923
  → `candidate_logprobs()` for OFF and each lambda. `colour_probs()` at 785 and
  `_probs_generic()` at 2987 collapse variants; `summarize_eval()` at 3148 and
  `evaluate_gates()` at 3420 produce memory, lesson, locality and frame metrics.
- These retrieval/lesson “probabilities” are not generated solve observations.
  `MockScorer.candidate_logprobs()` at 2252 is synthetic and cannot diagnose
  native BF16 effects.
- Eval serialization at 3033 stores rounded aggregate per-answer `p_raw`, mass,
  logp, and candidate token counts, but omits prompt/candidate text from each row
  and does not preserve individual token-logprob vectors or actual batch
  assignments. Counts can flag multi-token groups, not prove unchanged token
  prefixes or recover divergent-token probabilities. Exact old source, tokenizer,
  bank/distractor, ordering and batch configuration are needed to reconstruct
  routing; a new model call is needed for missing numerical evidence.

## 4. Memory-preservation — distinguish evaluation from KL training

**Evaluation inherits memory-dose routing.**
`gpu/astra_memory_preservation_diagnostic.py:122` invokes
`memory_dose.py evaluate` with batch size 16, cell F_r16k16, lambda 1 and the
preserved adapter. `memory_preservation_analysis.py:231 reduce_evaluation()`
calls native `summarize_eval()` and `evaluate_gates()`, emphasizing G9 frame
binding, G11 abstention, dose curves and frame spill. The full evaluation also
contains text-fit and lesson rows. Do not label all 1,313 cues or G9/G11 as
variable-length likelihood assembly: frame/abstention can take the fast path.

**KL training is a different comparison, with a concrete shape mismatch.**
`organism_v6/memory_preservation.py:312 cache_off()` calls `last_logits()` at 271
on chunks of four anchor prefixes. It right-pads to the chunk maximum, masks pads,
and selects each row's last real-token logits. No candidate continuation is
scored. `optimizer_step()` at 236 forwards the selected anchor as a natural-length
singleton at 249, and compares its full-vocabulary next-token distribution to
the cached row using `full_forward_kl()` at 202. `train()` chooses
`anchor_index=steps % N_ANCHORS` at 414. `preservation_mode()` at 188 switches to
eval mode while preserving gradients, avoiding an intentional dropout mismatch.

Teacher and student histories match, but execution B/T and padding differ.
FP32 softmax on BF16-produced logits does not itself eliminate that discrepancy.
An unchanged-model teacher-versus-student KL baseline could therefore have a
numerical floor. This is an **unmeasured potential confound**, not evidence that
training was noncausal, the preservation effect was false, or the adapters must
be retrained. Each KL operand remains a normalized full-vocabulary distribution;
the semantic two-candidate mass contradiction is not the correct test here.
Coefficient-zero training omits these KL forwards.

## 5. Generation and additional source-discovered paths

### Writer-interface calibration and neutral solves

`organism_v6/writer_interface_calibration.py:103 build_requests()` selects 64
paired original oracle prompts across five rendering/instruction/token-cap
conditions (320 requests). `worker()` at 251 calls `_generate()` at 236, which
uses greedy native `model.generate()`. `reduce_records()` at 209 measures
correct/valid/truncated/multiple-ACT outputs. It does **not** call W0 or carrier
candidate scoring. Original-oracle selection is structural, not candidate-score
ranking in this code.

Neutral reasoning runs use generated text and strict environment verification
(`organism_v6/reasoning_neutral_probe.py:150 run_probe()` and `_counts()` at 123;
`organism_v6/model_backend.py:51 VLLMBackend.batch()` calls `llm.generate()` at 67;
`organism_v6/run_reasoning_neutral.py:180 run_condition()` binds this backend).
These solve/accepted-action counts, and parent-correction generated ACT outcomes,
are not constructed by the inspected full-candidate scorers. This does not prove
all generation kernels numerically invariant, nor certify unrelated provenance
or scientific claims. Composite gates and any scorer-selected upstream context
must still be described separately.

### LANDs C2r recognition: additional direct structural exposure

`alchemy/run_lands_c2r.py:57 score_candidate()` independently tokenizes and forwards
each full `prompt + " " + candidate`, without common padding. It computes a
**length-normalized** mean token logprob, without appending EOS; log-softmax is
not explicitly promoted to FP32 there. `alchemy/lora_mem.py:8 load_base()` uses
BF16 on CUDA, FP32 on CPU, FP16 on MPS. This is not the same estimator or pinned
stack as semantic writer.

`main()` at 67 → `candidates_for()` at 23 → candidate-score argmax around 111:
witnessed/resolved colours, animal positions, land rotations, palettes,
meta-parent combinations/operators, public source rules and pigment-map variants.
Unequal actual candidate lengths are possible and not rejected. Boundary safety
is not verified beyond separately measuring prompt length. Recognition/read
fidelity is directly score-dependent. Selected answers form the memory blocks
fed to subsequent clean-base generation, so downstream generated composition
accuracy has **indirect** exposure through its input, unlike independent neutral
solve probes. No native failure is established here; do not apply a disjoint
sequence-mass test to these length-normalized scores.

### V3 isolation check: not an answer scorer

`organism_v6/train_adapter_v3.py:434 isolation_check()` compares solo-segment
logits with packed block-masked/reset-position logits and a no-block negative
control. Solo versus packed changes sequence shape. A discrepancy in this check
could mix numerical shape effects with isolation behavior; no measured V3
failure follows from the semantic result. It does not assemble candidate
probabilities or supply neutral solve scores. No change to this check is proposed.

## 6. Smallest decisive follow-ups — proposals only

Do not start a new curriculum, fit, blanket rerun, or gate framework. Keep prior
records and prospective supplementary outputs distinct.

1. **CPU inventory first:** reconstruct exact memory-dose fast/slow routing and
   slow-chunk membership for one existing eval using its pinned tokenizer/source,
   bank, distractor, batch size and order. Record candidate IDs, common token
   histories, L, full length, B/T/keep and pad offsets. Separate frame/abstention
   from text-fit/lesson rows. This can narrow the relevant claims without inference.
2. **If preserving the storage/extraction claim:** select one text-fit row and one
   lesson row structurally (first qualifying unequal-shape group, not largest
   effect), one retained adapter and OFF. Compare original batching with common
   future-aligned shapes and an FP32 reference. Capture full next-token vectors
   at shared histories and original target logprobs. No new fit. Memory-dose
   currently lacks these per-token artifacts, so existing rounded evals cannot
   settle the question.
3. **If preserving the KL interpretation:** choose one anchor whose four-row
   cache chunk contains a longer peer. On unchanged OFF weights compare the
   cached-path row with the exact singleton student path; report full-distribution
   KL and logit/logprob differences, then same-shape/FP32 controls if needed.
   This tests the zero-learning numerical floor without optimizing anything.
4. **W0 is lower priority:** its equal-mask guard already excludes the measured
   length mismatch. First inspect saved candidate traces against that guard;
   only if a W0 likelihood claim needs stronger assurance, perform one same-shape
   shared-prefix check on a retained checkpoint. Do not classify it as broken
   merely because its loop contains two forwards.
5. **LANDs C2r only if its recognition/composition results enter the paper:** one
   unequal-token-length candidate group under the original checkpoint, compare
   original mean-logprob ranking to a shape-controlled computation of that same
   estimator. Do not silently switch to summed/EOS scores or assume a generated
   composition endpoint is independent of score-selected reads.

Mass checks require genuinely distinct, prefix-free/terminated continuations
under one token history; verify that condition and deduplicate candidate aliases
before interpreting a sum as probability mass. A sum below one is not a
prefix-invariance certificate. Normalizing inconsistent candidate values does not
repair them. None of these suggestions authorizes automatic execution.

## 7. Suggested paper limitation

“We identified a BF16 sequence-shape sensitivity in the semantic writer's
separately scored unequal-length continuations, despite causal attention masks.
Original likelihood-based results from that assay are not treated as valid
probability estimates; repaired inference-only rescoring is reported separately.
The implementation audit distinguishes this path from same-prefix next-token
retrieval, equal-length W0 candidate scoring, and directly verified generated
actions. Other full-continuation and cross-shape KL paths have structural exposure
that has not yet been numerically characterized; no blanket invalidity or global
cleanliness claim is made.”

## Source identity at inspection

| Repository path | SHA256 |
|---|---|
| organism_v6/semantic_carrier_diagnostic.py | a05da09e8f2720907eb277f928e84ec095a754119144a6b2ecbd38360a969f98 |
| organism_v6/semantic_writer_diagnostic.py | d6ea45ac6bfb5cabe6cbd1224f4cf101e96cbd0e07c029e934c2aa3e03e1ddb0 |
| organism_v6/multikey_writer_gateway_simple.py | b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8 |
| organism_v6/memory_dose.py | ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3 |
| organism_v6/memory_preservation.py | 9a5ad83a246c07e0bf2094bafc9473c66952d56071d7a9cc75e93c2000bdf574 |
| organism_v6/memory_preservation_analysis.py | 25f03513e6092790337849282cdc780b4305518f760e08afcb7e81b2f28e4754 |
| organism_v6/writer_interface_calibration.py | 9ab582ebc935ae36b88bd412fd06d799044661612f89a0770e46b92ab1b066c7 |
| organism_v6/train_adapter_v3.py | 02f47008c676f6aa361a7e18bf30f5010391174d7a0dd9e648532e16cd55e169 |
| organism_v6/reasoning_neutral_probe.py | 28431b85d8df5c348b484476e7ad921f2c2e5d795ee203b8e2cc0498c03c5607 |
| organism_v6/model_backend.py | 93feee1cb30720b565aac8f570d368cad8e137789b39f228fbd8ed264123a3f5 |
| gpu/astra_memory_preservation_diagnostic.py | 33611bfb9b66c8ce26e6aed3b017b1179cfe4bdc912dc25fa76b738b10ec9c4f |
| alchemy/run_lands_c2r.py | 758d2aaa7e167566a7f2ad9c28485934361a1cbf0372d6b15d1ad526e1f15ad0 |
| alchemy/lora_mem.py | ff573bf1aaaf2d1c1af918fb95954bece44af4154498c8ed28c87b00a315d89d |

Historical semantic carrier source SHA256:
`fd31dc722f7a1a4b65a2fb597811e2598d603c650e8f6fe4e852915fc38c7392`,
as pinned by the original d160 semantic-writer manifest. Original manifest:
`/tmp/astra_semantic_writer_terminal_20260912/astra_semantic_writer_Q0_20260912_attempt1/manifest.json`,
SHA256 `f6fa9060e9ea794309839a8651adc728989c283663070b348c3200acca57a830`.
This is historical source attribution, not a claim that the current repaired
carrier is byte-identical to that source.
