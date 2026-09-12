# Prior parametric-memory evidence versus level-zero device colors

2026-09-12 — bounded read-only comparison — **EDIT-STOP**.

Only this document was written. No remote access, network, Git, GPU, model
calls, source changes, reruns, or changes to current parity/fading work.
This is selective receipt inspection, not a full historical replay.

## Executive answer

The strongest recovered historical evidence is **rank8 canonical-sentence
completion probability increasing after a synthetic fact write**, with an
adapter-OFF comparison and evidence of owner discrimination. It is not
verified free-generation accuracy on instruction-style questions, and it did
not satisfy locality/selective-memory requirements. It therefore supports
the plausibility of a weight-carried association, but does not contradict
level-zero red16 or establish that the current writer/readout interface works.

Do not add dose or rank from this analogy. Finish the selected HF/vLLM parity
check first. If HF itself also fails exact-prefix device binding, the useful
next oracle contrast is **decision-position/canonical-continuation interface
versus answer-only chat recall**, with separate full-vocabulary generation,
gold probability, and candidate mass—not a larger-rank or data-split change.

## 1. SEQ056/057/058: strongest historical claim, evidence grade explicit

Provenance recovered from:

- `research_loop/COORDINATION.md:1215` (SEQ057), `:1209` (SEQ058 completion),
  and SEQ056 at`:1235`.
- `research_notes/2026-09-11_cross_node_effect_adversarial_audit.md`,
  “Terminal matched-seed closure (2026-09-12 04:53 UTC).”
- `research_notes/astra_memos/receipts_20260912/astra_node12_refresh_20260912.md:97`.

Actual reported run IDs:

- Node1 `memory_dose_conf`, bank seed1, **training seed1**.
- Node2 `memory_dose_S1_rep_seed1`, same banks/cell, **training seed1**;
  terminal report path recorded as
  `/localhome/local-rohing/v6_out/memory_dose_S1_rep_seed1/report/summary.md`.
- Cell `F_r16k16__across__r8__lam1`, terminal `sleep4`, banks0/1/2.
- Contrast: original `memory_dose_S1` and seed0 refits
  `memory_dose_S1_rep_same` / `memory_dose_conf_rep_same`.

The terminal audit reports training-seed1 frame probabilities
**0.874 / 0.882 / 0.735**, pooled **0.830**, versus seed0
**0.379 / 0.719 / 0.254** on these matched banks. Reported pooled OFF frame
probability is approximately0.252. Owner-versus-lookalike information contrast
`I_d_frame = 2.013 [1.365, 2.748]`; reported spill0.392, above the historical
0.03 locality criterion. These are not16-way or four-color generation
accuracies and the confidence interval is not an independent-seed interval.

The audit records canonical result hash
`9aadd56616ff94812cb88213935dea3a073759ed15fbe262f7f1ed1e54b4a9ce`
and cross-machine matched evaluation hashes after removing paths/timing;
bank1's canonical evaluation hash is
`4c7a604e4b4b44314252a17fe37dab7c22bbaa454d2f7098fb9a3e61c7138340`.
I did **not** locate and re-hash the original `memory_dose_S1_rep_seed1`
evaluation payloads in this bounded local pass. Those original numbers and
canonical hashes remain **attributed audit/report evidence**, not newly
verified raw data. The later refresh is report metadata, not another replay.

The measured seed-matched repetitions supersede the earlier “node effect”
interpretation. They support reproducibility of those particular stored
results, not universal deterministic training or a basin-frequency estimate.
Bank seed and optimizer seed must remain separate in any comparison.

## 2. Later locally available raw memory-dose receipts

I found a later concrete same-family run:

```
/tmp/astra_A1A2_banks_20260912T0800Z/runs/
  astra_A1_memory_dose_S1_F_r16k16_ts2_20260912/
```

This is **training seed2**, not the seed1 confirming refit above. I selectively
read its bank1/bank2 evaluation JSONs, bank1 training metadata and corpus.
The bank1/bank2 evaluation files and bank1 training metadata match their
entries in the capsule's `CAPTURE_MANIFEST.json`. The corpus is absent from
that manifest's file inventory; its locally computed SHA256
`860a67809ac67e27c850d5f1f6bd29a1256a747aa5b46c15920791b345280e96`
instead matches `SOURCE_REUSE_RECEIPT.json`, which records its original
capture path under `/tmp/astra_seed_bank0_evidence_20260912/`, copying into
this capsule, and `receipt_match: true`. This verifies consistency with the
local reuse receipt, not a fresh remote-source check.
From the actual per-cue arrays, I recomputed:

| Bank / cue kind | N at dose16 | Mean normalized gold P OFF→ON | Mean candidate mass OFF→ON |
| --- | ---: | --- | --- |
| bank1 frame | 16 | 0.240929→0.865241 | 0.010230→0.995341 |
| bank1 look-alike frame | 16 | 0.246744→0.729088 | 0.008874→0.994807 |
| bank1 bicycle frame | 16 | 0.242945→0.820226 | 0.004561→0.997355 |
| bank2 frame | 16 | 0.254242→0.833422 | 0.007354→0.997976 |
| bank2 look-alike frame | 16 | 0.253358→0.492734 | 0.009723→0.997575 |
| bank2 bicycle frame | 16 | 0.262112→0.859424 | 0.004504→0.998943 |

These are stored HF scoring receipts (`model="hf"`), marked synthetic because
the facts are researcher-planted. “Synthetic” here is explicitly a lineage/
authorship warning, not permission to promote them to autonomous learning.
I did not reload the adapters or re-execute the scorer.

Primary local evaluation hashes:

```
ea6f61c8f112212f4becd541c67fa842218682cc4fc693d26bbd6b459b8d4e08
  eval/bank1__F_r16k16__across__sleep4__r8__lam1.json
08dd3b9c91ad938d8f27f8afe42e495d4c193424fa748a00c9942f0f8524f3a1
  eval/bank2__F_r16k16__across__sleep4__r8__lam1.json
```

**No-write/control interpretation:** the historical HF scorer's `off()`
context disables the adapter on the same base, and ON uses lambda1.
That is an adapter-OFF comparison, not a separately refitted no-write model
or an active text-memory comparator. Dose0/unexposed and look-alike/wrong-
property cue families exist in the harness; the table above recomputes only
the listed dose16 families. The large bicycle/look-alike values demonstrate
why “strong completion” must not be called selective memory. No locality
gate pass is established by this comparison.

## 3. What was actually written/read: not the level-zero interface

The inspected bank1 `train_meta.json` records:

- rank8, alpha16, dropout0.05; all seven LoRA projection targets;
  lr1e-4,3 epochs,batch4,max_len512,training seed2.
- 13,016 items;9,762 optimizer steps;749,964 token presentations;
 710,916 supervised-token presentations; no truncation; final loss1.229991.
- `memory_dose_v1 (mirrors train_adapter.py v1)`, representation`frames`,
  chronological ordering; corpus ID`5829d096ba5fe302`, item ID`f48b4b4ae3704d63`.
- Model name`Qwen/Qwen2.5-7B-Instruct`, not the current experiment's full
  authenticated local snapshot inventory. Do not infer identical base bytes
  from a matching model name alone.

An actual planted owner (`T3Z2`) has256 corpus items spanning16 distinct prose
contexts;3 epochs give768 presentations. Example stored item:

```
context: I wiped the dust off owner T3Z2's car and the green finish came up clean.
target:  Owner T3Z2's car is green.
chat: false
mask_context: false
```

The corpus contains5,376 fact items,4,096 color-filler items,2,200 other filler
items and1,344 lesson items. Marginals are balanced by construction. The
`F_r16k16` name is **not simply16 repetitions of the level-zero corpus**:
for a dose16 owner,16 occurrences ×16 renderings per occurrence produces256
written items, distributed across16 forms. Repetition and distinct forms
must not be conflated.

Source semantics checked against this stored item:

- `memory_dose.py:1033` renders perception prose plus a canonical declarative
  target and documents loss on **every token** (`mask_context=False`).
- `memory_dose.py:308` defines target`Owner {owner}'s car is {colour}.` and
  read prefix`Owner {owner}'s car is`.
- `memory_dose.py:2325` loads the adapter with HF/PEFT;
  `candidate_logprobs` uses joint prompt+candidate tokenization rather than
  separate-span tokenization.
- `research_notes/analysis/eval_frame_summary.py:2` defines the reported
  frame P as `p_raw[gold] / candidate_mass`, averaged across dose16 cues.

| Dimension | Prior F_r16k16 | Level-zero16 device colors |
| --- | --- | --- |
| Write | Whole plain text: colored observation plus canonical statement | Already-rendered Qwen chat question; color+EOS targets only |
| Visible training prefix | Prose can already name the color | Question contains device ID but no color/log fact |
| Read | Bare canonical sentence prefix, teacher-forced candidate continuation | Chat answer generation on paraphrase; separate exact-training-question diagnostic |
| Metric | Gold probability normalized over red/blue/green/white; mass reported separately | Full-vocabulary greedy output, strict color match; colors red/blue/green/yellow |
| Exposure | Example owner256 items/epoch,768 across3 epochs;16 forms | Seed0 one item/device/epoch,4 total; repetition16 copies/epoch,64 total |
| Optimization | Mixed13k-item corpus,9,762 steps for inspected cell | 80 steps in original and matched repetition fits; different objective/accumulation |
| Adapter/scorer | rank8 HF/PEFT scoring, OFF via disable_adapter | rank8 HF training, vLLM LoRA generation; current HF parity is checking this boundary |

The much higher historical loss is not evidence of worse memory: the losses
cover different tokens and objectives. Conversely, near-zero level-zero
final arithmetic microbatch loss is not a memory-binding measurement.

## 4. Newer exact-write evidence: do not upgrade it to a positive memory result

Locally available later capsules include
`/tmp/astra_exact_train_root1_terminal_20260912/root1`, tied by `probe.json` to
`/localhome/local-rohing/astra_diagnostics/astra_semantic_writer_Q0_20260912_attempt1`.
Its supplementary report hash matches `COMPLETED.json`:
`5b349b1b4742f061f0c884ef37b7c4f3478845d46b5f27424c97237d6d492fc2`.
I inspected a raw generation record with request, adapter and LoRA hashes,
actual token IDs, EOS and validity, but did not replay the entire reduction.

This exact-training-context diagnostic reports root1 W+ own-map generation
64/128 after write versus OFF65/128; W- own-map63/128 versus OFF63/128.
The combined analysis reports root0 W+68/128 and W-68/128 versus corresponding
OFF64/128. Root0 numbers here are **derived-summary evidence**, not an
independent raw recount. The runs have explicit OFF and complementary W+/W-
controls, but no strong exact-binding pass. Valid action formatting or very
large candidate-mass gains alone do not change that conclusion.

Accordingly, the later exact-write diagnostic is useful **negative/interface
evidence**, not a stronger positive memory precedent. Canonical manuscript
integration/review files are not themselves new write receipts.

## 5. Reusable conclusion / next oracle-memory distinction

First disambiguate “parity negative”:

- If HF and vLLM disagree materially on identical prefixes and loaded state,
  fix/understand that boundary before using any old writer analogy.
- If parity agrees that HF itself lacks correct exact-prefix binding, prior
  canonical completion is a separate interface precedent—not proof that
  more rank, dose, or a new split will solve this task.

The decisive representation difference worth isolating in a **separate,
predeclared oracle diagnostic** is completion of an exact trained declarative
prefix versus answering a masked chat question. Keep the same known16 facts,
frozen base, rank8, fixed seeds and bounded updates; do not simultaneously
import the historical13k corpus,768 presentations,16 forms and whole-text
objective and then attribute success to one ingredient. No implementation
or new experiment is authorized by this note.

For either interface, report the first decision-token gold NLL/full-vocabulary
top1 **and** the four-color candidate mass and conditional ranking. This
distinguishes “the model recognizes a color-completion surface” from “the
model associates the right color with this key.” Include adapter-OFF and
wrong-key/wrong-property controls in any newly designed oracle claim; do not
substitute a candidate-normalized gain for strict binding accuracy or fold
new probes into the frozen48-case dev endpoint. The already-running HF
parity worker is the appropriate first decision-position measurement.

### Compatibility and reuse boundary

Reusable now: metric definitions; recorded bank-vs-training-seed distinction;
raw HF OFF/ON cue comparisons; canonical serialization as a clearly labeled
alternative-interface hypothesis; warnings from spill and exact-write
failures. Reusing these does not require rerunning historical jobs.

Not reusable as current experimental data: historical adapters, planted
owner facts, old model-name-only identity, summary confidence intervals,
or their probabilities as level-zero generation accuracies. No imported
adapter/merged lineage, compiler edits, large-rank recommendations, or
split changes follow from this comparison.

**EDIT-STOP.** Original SEQ057 numbers remain attributed audit evidence;
later local per-cue recomputations are explicitly separated above. This is
not a new verified pass of the old writer or a scientific claim change.
