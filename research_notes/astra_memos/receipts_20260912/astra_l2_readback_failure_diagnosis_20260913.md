# L2 LR readback failure — preserved-archive diagnosis

2026-09-13, Main's08:17UTC continuation. **COMPLETE, read-only artifact audit.**
Only this report is written. No native/remote/model execution, tokenization,
output regeneration, Git, archive extraction, corpus/answer edits or live-root
access. Main owns any future test. Scope is the five COMPLETE LR captures in
`gpu_artifacts_local/l2_public_record_20260913`; aborted seed0attempt1 arms and
the older `seed0_attempt1.tar` are excluded. No scientific claim is upgraded.

## Verdict

**Not a demonstrated empty-mask/EOS failure, nor evidence that every adapter
was ignored. Also not proof that more steps will fix it.**

- All200 archived training-row encodings have correct target-only masks,
  supervised EOS, intact prompt prefixes and no truncation. All15 writes
  admit8/16/16 rows with zero rejections/nonfinite batches.
- Most losses plateau near0.05, which is compatible with learning to spell
  either action while largely failing the key→action choice. Low aggregate
  teacher-forced loss is not acquisition accuracy.
- Seed2-high fit2 is different: final epoch mean0.01929, last-batch loss0.014532.
  It shows additional optimization beyond that plateau, but there is no saved
  post-fit exact-training-query acquisition measurement.
- Training and readback use DIFFERENT question wording and different token
  prefixes. In both high-LR cells, the fit1 adapter changes behavior on the
  training-style wake2 query, while paraphrased readout still returns one
  constant action. Prompt-sensitive access is a live explanation, not proven
  successful acquisition. Wake2 keys were not yet trained by fit1.

**Next: saved-checkpoint acquisition/access test before any dose or rank
change.** Start with seed2-high fit2_PROMOTE, the strongest loss signal.

## 1. What the five completed runs actually contain

Each terminal says COMPLETE, all11stages,128calls,3fits,100aggregate updates.
That is **20 fit1 +40 fit2_PROMOTE +40 fit2_SHADOW**, not100 sequential updates
to one adapter. Each fit cold-starts from frozen base with a fresh optimizer.
Each uses20epochs, batch8, rank8/alpha16/dropout0.05, all seven projection
targets, AdamW, no packing, max_len1024. Low LR=3e-5; high LR=1e-4.

| Run | fit1 final loss,20steps | fit2 last-batch loss,40steps | fit2 last epoch mean |
| --- | ---: | ---: | ---: |
| seed1-low-attempt1 | 0.05128724 | 0.05297884 | 0.04945 |
| seed1-high-attempt1 | 0.05009143 | 0.06201277 | 0.05118 |
| seed2-low-attempt1 | 0.05139469 | 0.04532487 | 0.04934 |
| seed2-high-attempt1 | 0.05009850 | 0.01453196 | 0.01929 |
| seed0-low-attempt2 | 0.05020161 | 0.05077841 | 0.05019 |

Within EACH run, fit2_PROMOTE and fit2_SHADOW have identical training items,
encoding arrays, losses and adapter-weight bytes. Their whole-directory
candidate hashes differ because manifests/provenance differ. These two fit2
writes are not independent demonstrations or a continuing optimization chain.
High-LR wake actions differ by arm, but complete public records recover the
same balanced action targets. Training target inventories are4/4 in fit1 and
8/8 in fit2, not collapsed supervision.

`train_manifest.final_loss` is the last training minibatch loss, measured by
the forward pass BEFORE its optimizer update. It is not a frozen-checkpoint
evaluation. `mean_loss_per_epoch` averages training minibatch losses.
See pinned `organism_v6/train_adapter_v3.py:806`, `:812`, `:823`, `:834`,
`:852`. Dropout is configured0.05; no archived dropout-off per-key or
per-token loss evaluation exists in these manifests.

Actual stdout corroborates seed2-high fit2: step20 loss0.0492, step30 loss0.0373,
step40 loss0.0145. Seed1-low fit2 step40 loss0.0530. The low-loss exception is
real in both the manifest and preserved log, not an assumed dose response.

## 2. Masks and token targets: checked, not inferred from config

Inspected all200 encodings across15fits in `run/<fit>/data/training.json`.
For every row verified:

- `input_ids` starts with the stored native prompt IDs; that entire prefix is
  labeled-100. Public prompt plus assistant header is masked.
- The complete child target token sequence is labeled at the correct positions,
  followed by exactly one supervised Qwen `<|im_end|>` token151645.
- Template trailer/padding positions are masked; ID/label lengths match and
  stay≤1024. No target dropping or splitting is evident.
- Target bytes/hash match `target_hex`, supervised spans and exported target;
  native rendered context matches the context span. Actual prompt lengths are
 131–135tokens. Supervised lengths are12 or14tokens:11/13action tokens +EOS.
- Each fit1 has104supervised tokens per epoch; each fit2 has208. All20 archived
  epoch orders cover every item exactly once. Flags `add_eos=False` and
  `chat_template=False` do NOT mean missing EOS/template: runtime preconstructs
  and audits them in `gpu/astra_l2_public_record_dev.py:429`.

Two actual targets, with archived supervised token IDs:

```
move_7bc22e03caee: [3397,62,22,8904,17,17,68,15,18,924,2127,151645]
move_54b50509ad73: [3397,62,20,19,65,20,15,20,15,24,329,22,18,151645]
```

The first two target tokens are shared. Token THREE selects22 versus20; after
that choice, teacher forcing reveals which largely predictable suffix to spell.
For balanced targets, a toy key-ignorant model assigning probability1/2 at
that choice and predicting the rest perfectly has mean target loss
`ln(2)/13 = 0.053319`. **This is an explanatory reference, not a measured
decomposition or hard lower bound for these stochastic minibatches.** It shows
why≈0.05 can coexist with50% constant-action readback. The archives do not
provide actual branch-token NLL or logits, so they cannot prove where the loss
is concentrated. Seed2-high's0.01929 epoch mean is below this reference and
deserves an acquisition check rather than blanket dismissal as identical underfit.

Additionally joined native record raw_hex to training target_hex for all40rows
in seed1-low and all40 in seed2-high: exact equality. All five archives' file
seals also verify. No teacher record replacement is indicated by this audit.

## 3. Exact training context versus readback context

Same generic system text, public law, action order, key, response instruction,
chat-template envelope and assistant generation header. Only the question
line changes:

```
TRAIN / WAKE:
Key key_0830e179d7be55f707759d95: choose the successful action.

READOUT:
For key_0830e179d7be55f707759d95, which listed action succeeds?
```

Example from seed1-low fit1 row0 versus report1_PROMOTE call00: BOTH prefixes
are135tokens, but their token sequences differ. Original wake1 prefix equals
training prefix exactly. Rendered UTF-8 prompt hashes:

- Train: `44989e6b119a0237643d3282d4295fe14621d819ac37540ffe3e54deafb55030`
- Readout: `1b73fde0f4f58f4c41802e59172337a960693070d37fe5b3cde0245e38dabe9b`

The sleep query excludes outcome and PROCESS_TAPE; target is the supported
raw child action record. Training is on one source-withdrawn query form,
while readback measures access through another. Core `action_prompt` at
`organism_v6/l2_public_record_dev.py:271` explicitly implements this distinction.
Matching token COUNTS or semantic intent does not make the prefix identical.

All400 baseline/report response records checked (5runs ×5panels ×16keys)
return exactly `move_54b50509ad73`, legally and with finish_reason=stop.
Given balanced recorded targets this is4/8 old +4/8 new, not a format failure.
There is **no post-fit exact TRAIN-prompt generation on the trained keys** in
these completed stage inventories. Wake2 has training wording, but tests the
second block BEFORE those keys enter fit2.

## 4. Routing, initialization and actual behavioral movement

All15 `fit_intent.json` records declare fresh_base/fresh_optimizer, and fit
results bind initialization to base:
`1a28421dffcee174137818b590991ba80678b58f6c63fd8eab027a933486efd5`.
No initial birth adapter or prior fit warm-start is used. Runtime `fit_stage`
at`:528` requires cold native base; there is no accidental promise here that
fit2 continues fit1's state.

For all400 audited baseline/report responses, native system text, returned
prompt token IDs, text/decoded/raw_hex and stop completion agree. Baseline and
SHADOW have route=null. PROMOTE report1 binds fit1 candidate; PROMOTE report2
binds fit2_PROMOTE candidate. All15 saved adapter-weight file hashes and
candidate directory hashes recompute correctly using the runtime's newline-
terminated JSON encoding (`gpu/astra_l2_public_record_dev.py:91`).

Crucially, with IDENTICAL wake2 PROMOTE/SHADOW input token IDs:

- seed1-high:7/8 actions differ, PROMOTE chooses action1 on7, SHADOW on0.
- seed2-high:6/8 actions differ, PROMOTE chooses action1 on6, SHADOW on0.
- All low arms choose action0 for all8 wake2 actions in both routes.

Thus high-LR saved-adapter routing has a visible effect under wake wording;
“every write moved nothing” is too broad. These are NEW keys at this point,
so the shifts are not evidence of learned key associations or successful
transfer. They do support a prompt-sensitive action bias/access difference.
Raw route metadata/hash evidence alone would not prove kernels used LoRA;
the paired high-LR behavior is stronger evidence against universal adapter
omission. It still does not establish correct per-key recall.

## 5. Smallest decisive next test — BEFORE dose escalation

Main can use the existing strongest checkpoint, seed2-high fit2_PROMOTE:
candidate directory hash
`8e79df460e52e94b342de285bcc85ef69cc5fb468a8904d443c665af37bc8ff4`.
Train manifest SHA256
`6f30f54fe899d6b83af2a5b14dfc4aa4840df7721fb2155ba27adbd519fe445b`.

**No new fit first.** Freeze a2×2 diagnostic: base vs this saved checkpoint,
each queried on the SAME16already-experienced keys under (a) EXACT archived
training prefix/token IDs and (b) EXACT existing readout prefix/token IDs.
That is64greedy responses at the existing output cap, with matched systems,
adapter routing and native prefix checks. Reuse unchanged admitted raw child
targets; do not change/relabel old readout results or train on readout answers.
If exactly matching archived prefixes is impossible, stop and report an
interface mismatch instead of quietly substituting a template.

On that same matrix, obtain dropout-off teacher-forced target-token NLL and
separately the third-token22-vs20 log-odds/rank. Report whole-record greedy
accuracy, per-key choice accuracy, branch loss, suffix/EOS loss and full
target loss. This directly separates the aggregate-loss illusion from actual
choice acquisition. These are future measurements, not outputs generated by
this audit; the current archives cannot supply them.

| New diagnostic result | Interpretation / next move |
| --- | --- |
| Exact TRAIN recall/branch discrimination strong, READOUT weak | Acquisition exists but prompt access/transfer is deficient. Do not prescribe more dose first. Any later prompt-coverage intervention must be a fresh declared training experiment, not a hot repair of these answers. |
| Both forms weak; branch NLL near chance while suffix/EOS loss low | Choice binding remains underacquired;≈0.05 aggregate loss was misleading. No evidence yet that capacity is the cause. |
| Teacher-forced exact-prefix choice strongly correct, but native greedy still wrong | Inspect inference/prefix/adapter/termination discrepancy before fitting more. If needed compare dropout-off saved-checkpoint evaluation with native reload on the same literal prefix. |
| Exact TRAIN and READOUT both strong after verified reload | Existing captured failure is not reproduced; investigate runtime/artifact provenance before changing recipe. Do not overwrite the historical result. |

**Capacity is presently unresolved, not demonstrated insufficient.** The
writer declares20,185,088 trainable LoRA parameters for16binary associations;
that count alone does not establish effective capacity or guarantee easy
optimization. The seed2-high loss decline weakens a universal hard-capacity
claim. A read-only checkpoint audit cannot uniquely separate optimization,
generalization and representational capacity.

Only if the exact-prefix acquisition test fails, consider a fresh, bounded
stronger-fit diagnostic on the SAME16rows/targets: preserve rank8, LR1e-4,
batch8, all masks and prompt bytes, and predeclare checkpoints at40/80/160
updates (20/40/80epochs), fixed ceiling160. Measure branch NLL and exact-prefix
acquisition at each, not just full-string loss. This tests dose rather than
assuming it works. No checkpoint or budget is chosen from readout success;
report the entire trajectory. If this still cannot acquire, only then isolate
an alternate optimizer/rank with matched data/dose as a separate hypothesis.
Do not call the160-update check SEQ113 replication or a closed-loop advance.

## Integrity, paths and reproducibility limits

Archive roots follow `l2_lr_seed{seed}_{low|high}_20260913_attempt{attempt}/`,
e.g. `l2_lr_seed2_high_20260913_attempt1/`. Relevant members under each root:
`plan.json`, `terminal.json`, `SEAL.json`, `FINALIZED.json`;
`run/{fit1,fit2_PROMOTE,fit2_SHADOW}/data/{training,fit_intent,result}.json`;
`run/<fit>/data/adapter/{train_manifest,train_meta,adapter_config}.json`;
`run/<fit>/stdout.log`; native `run/<stage>/data/NN.{request,response}.json`.

Verified527sealed members per archive (2,635 total), finalization links to
plan/terminal/seal, and all15candidate/weight hashes. All finalizations record
within_deadline=true. This establishes preserved-byte consistency, not a new
native run or independent verification of the training kernels. An initial
scratch candidate-hash calculation omitted the runtime's terminal newline;
corrected to the pinned encoding, all candidate hashes match. No artifact was
changed or treated as corrupt because of that audit-code mistake.

Whole archive SHA256 (directory prefix as in the scope):

- `astra_l2_lr_seed1_low_attempt1.tar`:
  `1401d59cee11e5ff97cfdb1c2f0ba01f5a20e1fefcfc2726032b0a04ef0c37c4`
- `astra_l2_lr_seed1_high_attempt1.tar`:
  `2628dcd977700af08b551bc058bf69a48ef6b0c328fa9b7216d7cf60c921ffde`
- `astra_l2_lr_seed2_low_attempt1.tar`:
  `433516532555360424ef3765d8a936ba6502014924db2c0e3b652e944140675c`
- `astra_l2_lr_seed2_high_attempt1.tar`:
  `d5f91bc56a57a48aad204e1dd3dd8b972c58b97f16d518627e726f8f8cf7082c`
- `astra_l2_lr_seed0_low_attempt2.tar`:
  `fe93ceaecfd5504db8d9a76959cba66b2f3d8afb59c17058a5fbf9255c99c62a`

All five plans bind the same source hashes, matching local files inspected:

- `organism_v6/l2_public_record_dev.py`:
  `0bb33988f003a0111e14cdfb53b3dc86a695e8e20656c90e71cfadb5ad28d352`
- `gpu/astra_l2_public_record_dev.py`:
  `dce8cd88b82bd51ec4f12e482ce70dc220453cb85dcaeb758206c7b5200a4277`
- `organism_v6/train_adapter_v3.py`:
  `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`

EDITSTOP. Owned output only:
`/tmp/astra_l2_readback_failure_diagnosis_20260913.md`.
