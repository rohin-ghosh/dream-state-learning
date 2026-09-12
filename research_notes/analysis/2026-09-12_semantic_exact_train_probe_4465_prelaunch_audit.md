# Exact-training-row probe at `4465e537`: fresh prelaunch audit

Date: 2026-09-12

Scope: read-only audit of commit
`4465e5374d50bc1843dd5802d053c0d10ece1ae2`, specifically
`gpu/astra_semantic_train_probe.py`, its focused test, the prospective
`ASTRA_EXACT_TRAINING_ROW_PROBE_2026-09-12.md`, and directly invoked
generation, scoring, original-verification, model-load, and worker-supervision
code. I did not load a model, access a GPU, launch or alter a job, or edit
builder code. This memo is the only repository file changed.

## Verdict

**GO. Exact blockers: none.** The implementation is fit for the prospective,
supplementary, inference-only diagnostic as bounded in the memo. It must not be
used to replace the original gates or to support retention, unseen-key,
population, parenting, clean-lineage, or H1/H2 claims.

## Findings

- **No target leakage into generation.** Each generation call receives only the
  recorded prompt token IDs and generation controls. Targets remain in audit
  metadata, and target-bearing candidate encodings are attached only to score
  requests. `_generate` consumes only `prompt_input_ids` and the token cap; the
  request digest is returned as provenance but is not model input. There is no
  output-conditioned selection or retry.
- **All exact rows are compulsory.** For each selected root, both opposed fits
  must contain 128 rows. The code requires exactly one instance of every
  `(slot, mode, template)` in the 8 x 2 x 8 training geometry, identical ordered
  W+/W- prompts and token prefixes, complementary targets, valid recorded
  masks/continuations, and 128 distinct prefixes. Every one of those indices is
  crossed with OFF, W+, and W- for generation and scoring.
- **The denominators are complete and nonselective.** Per root the reducer
  requires exactly 768 unique records: 384 greedy generations and 384
  two-candidate score requests (768 candidate forwards). Each state contributes
  128 generation plus 128 score records. Missing, duplicate, wrong-root,
  wrong-adapter, nonfinite, or excessive-mass records fail closed. Across the
  prospectively committed two roots this is 768 generations, 768 score requests,
  and 1,536 candidate forwards, with zero fits and zero optimizer steps.
- **Original and adapter custody is strong.** The known original manifest and
  terminal seal hashes are fixed. Sealed `fits.json`, `material.json`,
  `report.json`, fit receipts, and held-generation raw records are checked at
  use. ON adapter trees are matched to the sealed fit receipts and their loaded
  LoRA tensors must match the recorded tensor digests; OFF must freshly load a
  LoRA-free pinned base. Model, tokenizer, environment, source, and report
  identities are inherited from and rechecked against the original evidence;
  only the explicitly recorded runtime GPU UUID changes.
- **Generation is primary and scoring stays secondary.** Greedy dynamic-length
  generation is parsed with the existing strict one-action/EOS/truncation
  contract. The repaired scorer separately runs equal-total-shape BF16 forwards,
  checks common-prefix equality and complete-candidate mass, and reports scores,
  margins, and gains without changing the generation result or any gate. Its
  LF+EOS and numeric/backend limitations remain explicit in the prospective
  memo.
- **Fresh-load and failure boundaries are adequate.** OFF, W+, and W- execute in
  three sequential supervised worker processes. Each loads a fresh base; ON
  then loads only its bound adapter. The controller and workers require the
  reserved UUID, exactly one visible GPU, the pinned A40/driver, deterministic
  settings, and explicit `--allow-gpu`. A root has a prospective 60--3,600
  second deadline, each worker is capped at the lesser of 900 seconds and the
  remaining root budget, partial roots cannot reduce, there is no retry, and a
  worker failure preserves `FAILED.json`. The supervisor always attempts
  owned-process-group cleanup and refuses success unless that group and the GPU
  process table are empty.
- **The primary comparison answers the narrow question.** Matching-map exact-row
  strict-generation accuracy/BA, validity, 16 key summaries, and row-level
  template details are compared with the sealed 64-form held-generation BA and
  OFF under both mappings. Because the prompts are identical across
  complementary fits and labels are opposed and balanced, high exact-row
  performance with poor held-form performance is valid evidence of behavior
  confined to seen forms in these instances; poor performance on both does not
  establish usable storage. This comparison cannot uniquely identify a memory
  mechanism, and the design correctly supplies no new pass threshold.

## Launch-owner conditions and residual limits

These are not code blockers, but remain Main-owned conditions stated by the
prospective memo: precommit and launch both roots before inspecting either;
freshly establish exclusive GPUs and the required CUDA environment before the
first worker; preserve continuous reservation between state workers; and bind
the final source/reduction/cleanup evidence before release. The root-local CLI
does not by itself enforce joint two-root selection or perform the initial
queue/free-GPU check. Its deadline fails closed but is not an independent
hard-kill guard for a wedged controller outside a worker; worker GPU lifetimes
are the independently supervised portion.

The exact focused CPU suite was exported from `4465e537` and run without model
or GPU access: **13 tests passed**. Its mocked orchestration test establishes the
three intended loads and counts; actual subprocess-group cleanup behavior rests
on the directly invoked, source-pinned supervisor implementation and its wider
test suite, plus Main's required terminal resource check.
