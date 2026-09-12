# Memory binding: read-only diagnosis and smallest parity check

Date: 2026-09-12. Status: **diagnosis handoff / EDIT-STOP**.

Only this document was written. No source changes, Git, network, GPU,
tokenizer/model loads, training, generation, compiler changes, or invariant
changes. No confirmation cases were requested. All runtime checks below are
proposals for Main, not launches or completed evidence.

## Bottom line

**Prioritize exact-training-prefix HF/PEFT versus vLLM parity before any more
dose/rank changes.** The full48-text vectors really are unchanged, not merely
their aggregate scores. However, the recorded near-zero `final_loss` is
arithmetic-only in **both** repetition views; it is not evidence that memory
binding was learned and subsequently lost at inference.

I found no concrete dropped-memory-label, corrupted-color-assignment,
prompt-ID collision, or wrong-adapter-path defect in the inspected code and
receipts. This does **not** establish backend parity: the capsules omit the
actual adapter tensor files, and configured loader hashes do not demonstrate
equivalent HF/vLLM logits.

The smallest additional native work is **one bounded HF-only evaluation of
all16 original seed0 teach memory training prefixes**, comparing its first
token logits/losses to the **already-completed, exact-prefix vLLM diagnostic**.
There is no need to rerun that seed0 vLLM diagnostic. A repetition-checkpoint
parity check can instead use the unchanged existing16-case memory diagnostic
plus one HF worker; details below.

## Evidence locations and scope

Use these abbreviations for local, read-only capsules:

```
R = /tmp/astra_repetition_terminal_20260912/astra_diagnostics/astra_fundamental_repetition_20260912_attempt1
S = /tmp/astra_fundamental_seed0_terminal_20260912/astra_fundamental_teaching_20260912_attempt1
T = /tmp/astra_fundamental_followup_terminal_20260912/astra_fundamental_memory_trainprompt_20260912_attempt1
```

`T` is the already-completed seed0 training-prompt follow-up located while
checking reusable diagnostic code. Its teach/control adapter inventories
match the corresponding original seed0 fit receipts. It is important because
it prevents recommending a redundant prompt-only explanation/check.

Read-only CPU comparisons performed:

- Recomputed `R/manifest.json`'s four material-file hashes and fit-plan seal.
- Matched the original teach/control export byte hashes against
  `R/manifest.json.source_sha256`.
- Verified every repetition row is exactly the original native context,
  response, and explicit EOS unit, once for short or16 times for long.
- Checked all four repetition readout plan seals and capture-file inventories;
  matched all192 raw requests, rendered prompts, and input-ID vectors to their
  prepared plans. All use temperature0, seed20260912, max64.
- Matched fit adapter inventories to readout inventories and identity receipts.
- Compared all48 raw response texts per repetition cell to the same seed0 arm.
- Checked `T` teach/control plan seals, capture inventories, all16 raw response
  prefixes/input IDs, exact original training-prefix bytes, targets, and
  original seed0 adapter inventories.

The reported native token/text audits remain native receipts; I did not
independently rerun tokenization or model execution here. Current inspected
trainer and repetition exporter bytes match the native repetition manifest:

```
7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7  organism_v6/train_adapter_v3.py
69a969b1f6a9c0592c92a0780fbbbe1a19475db529463a505c0206416f95c5f1  organism_v6/fundamental_repetition_corpus.py
```

All local files named by the four readout source-hash inventories also match.

## Observed outputs and losses

From `R/cells/<cell>/fit/adapter/train_manifest.json` and corresponding
`readout/reduction.json` and raw `readout/run/data/calls/`:

| Cell | Final microbatch loss | Epoch4 mean microbatch loss | Dev action/adherence | Dev memory |
| --- | ---: | ---: | --- | --- |
| teach_short | 0.0009332682 | 0.17012 | 32/32;32/32 | red16;4/16 |
| teach_long | 0.0000209293 | 0.01034 | 32/32;32/32 | red16;4/16 |
| control_short | 0.0004986991 | 0.17256 | 32/32;0/32 | red16;4/16 |
| control_long | 0.0000345002 | 0.01037 | 32/32;0/32 | red16;4/16 |

Every memory output is literally `red`, with native output IDs
`[1151, 151645]`, finish_reason=`stop`, no invalid color outputs. The four
correct devices are006,009,013,014. Each cell's **entire48-text vector is
byte-for-byte equal to its seed0 arm**. All four checkpoints nevertheless
have different recorded weight-file hashes:

```
teach_short   bf37b312aefb73369eab1816a1feb0754e3f2ceda75f4eabfdca2f33c23e113e
teach_long    b4d32ce579119953020bb893318be60c1e7a1c20b4ad7e74b8caa8c6d7c80678
control_short 3f261bc8672528fd81f65c1564535e2169ef3146cbc42a7ba14cc12a3d6a1cc4
control_long  f2e7f22a2714597057044ba65a20974e7a616cd7c1465ab2009f369174935c8b
```

### Why final_loss is not a memory measurement

`train_adapter_v3.py:809` evaluates one microbatch, divides its loss for
gradient accumulation, and at `:826` stores the **last microbatch's** loss as
`loss_val`. It does not store the accumulation-window average or a post-save
memory evaluation. The loss was computed before the corresponding update.

`R/manifest.json.audit.optimizer_update_groups["0"][-1]` is:

```
train-addition-016, train-memory-005, train-memory-011, train-addition-030
```

The memory rows have targets yellow and green. But they are **earlier
microbatches**, not part of the final forward producing `final_loss`:

- Short: batch4, accumulation16. The final microbatch is four identical,
  separately reset copies of `train-addition-030`.
- Long: batch1, accumulation4. The final microbatch is just
  `train-addition-030`, containing16 continuous copies.

Thus **neither final loss bounds the NLL of either memory row**. In
particular, treating the four update groups as one forward and deriving a
memory gold-probability lower bound from their combined target count would
be incorrect. The epoch means are averages over microbatch losses, not
per-device binding accuracies or memory-only loss measurements.

## Training encoding/mask audit

Sources: `fundamental_teaching_corpus.py:114`,
`fundamental_repetition_corpus.py:55`, `:83`, `:136`,
`train_adapter_v3.py:126`, `:152`, `:369`, `:421`.

1. There are exactly16 device-color bindings, four each red/blue/yellow/green.
   Teach and control memory rows have identical context/response/source IDs.
   No conflicting targets were found for a device. Each repetition cell
   presents each color64 times per epoch: no target-frequency advantage for red.
2. An original memory example has42 native prefix tokens and two supervised
   target tokens: one color plus EOS. Neither the color nor a source log fact
   is inserted into the user prefix. The source event is provenance, not an
   extra model-visible reminder.
3. Exported memory spans are `[[rendered_context, False, ...],
   [color, True, ...], ["<|im_end|>", True, ...]]`.
   `chat_template=False` means the already-rendered prefix is not wrapped twice.
   `add_eos=False` in repetition avoids adding a second target EOS.
4. Native audit code checks the original label/ID sequence, each short copy,
   and the16-times-repeated long sequence for exact equality; explicit EOS
   encodes to the one native EOS ID. `collate` masks the first segment token,
   which is already a masked context token, not the color.
5. Fit manifests report512 memory target tokens per epoch in every cell,
   out of14592 total supervised tokens, with zero skips, dropped tokens,
   truncation, or splitting. Saved packing is one item per sequence; no
   multi-example packing/block4d mask is used. Native HF causal target shifting
   is delegated to the model; the actual runtime per-token shift is a useful
   parity-worker assertion, not something these aggregate receipts prove.

### Concrete long-context shortcut opportunity, not a proven mechanism

Long rows repeat the **same** context, gold color, and EOS16 times in one
causal sequence, with no attention/position reset at copy boundaries. Copies
2..16 can attend to the preceding gold color for the same device. The first
copy cannot. A model could therefore perform well on15/16 copies without
learning the device-to-color binding needed from a fresh prompt. This is
visible in the data/mask structure, not proof that the model uses this route.

Memory target tokens are3.51% of raw supervised-token mass; actual color
tokens are1.75%. The16 first-copy memory color positions are only0.110% of
long-view supervised tokens. These are **token shares**, not the optimizer's
effective task weights: the trainer averages per microbatch and accumulates
losses; memory and addition sequences have different target lengths.

Illustrative, explicitly not inferred model behavior: with uniform four-color
uncertainty only at the first color, and perfect EOS/arithmetic/copying, the
mean microbatch loss would be `0.2 * log(4)/2 = 0.13863` for short and
`0.2 * log(4)/32 = 0.008664` for long. Observed epoch4 long/short mean ratios
are0.06078 and0.06010, near1/16. This shows how low loss can coexist with failed
fresh-prefix binding; it does not measure copying or prove uniform logits.
Do not change the compiler or objective based on this illustration.

## Training versus readout rendering

Example device000, same in both arms:

```
training user: Which color does the log assign to device-000?
dev user:      Recall the logged color of device-000.
```

Both use the same actual Qwen system/user/assistant-generation wrapper,
including the default system message. The user sentence differs; the
assistant prefix suffix is the same. Native training prefixes are42 tokens;
dev prefixes are41. All16 dev ID vectors are distinct, with the device digits
present. Repetition dev cases, requests, rendered strings, and input IDs all
equal the original seed0 dev plans; there is no detected wrapper drift,
added answer, loss of the device ID, or changed dev selection.

**Already completed exact-training-prefix check:** `T/teach` and `T/control`
each contain16 raw vLLM responses, all literally red,4/16. Their rendered
prefixes exactly equal `S/teach.json` and `S/control.json` native training
prefixes; their adapter inventories match the seed0 fits. OFF is0/16 invalid.
Therefore changing the question phrasing cannot be the sole explanation for
seed0 failure. Repetition exact-training-prefix performance is not present
in `R`; do not assume it from either seed0 or repetition dev counts.

## Adapter loader audit and unresolved parity

Sources: `model_backend.py:13`, `:34`,
`rulegame_parenting_diagnostic.py:294`, `:303`.

- Each repetition readout binds its own fit adapter directory and exact
  adapter inventory, not the seed0 adapter. All four recorded weight hashes
  differ. Capture identity and configured adapter hashes agree with fit/plan.
- `VLLMBackend` sets `enable_lora=True` when an adapter is supplied.
  `NativeBackend.generate` passes `LoRARequest("life", 1, adapter_path)` into
  `llm.generate`; this is not an unused adapter argument in the shown code.
- Worker logs confirm enable_lora and max_lora_rank32. Saved rank8/alpha16/
  dropout0.05/bias-none target all seven projections. Native readout logs show
  vLLM0.27.1; fit manifests record torch2.13.0+cu130,
  transformers5.5.3, peft0.20.0.
- The identity's default temperature0.7/max_tokens400 are defaults only;
  raw request settings and `SamplingParams` use the actual0/max64.
- Base-tokenizer warnings do not by themselves identify a mismatch: both
  training and readout here intend the pinned base tokenizer, and the
  rendering/token receipts match. Do not add an adapter tokenizer or change
  model paths to silence a warning.
- Teach versus control adherence differs32 versus0 while OFF lacks the
  learned answer style. This is evidence against a universal adapter-OFF
  explanation, not proof all LoRA tensors or backend computations match.

**Open:** actual saved-tensor-to-PEFT reload equality; first-color logits from
the saved adapter on exact training IDs; HF/vLLM numerical/generation parity;
EOS versus color loss decomposition. No LoRA weights are included in the
local capsules, so none of these can be settled with local metadata alone.
Neither identical generations nor different file hashes resolves them.

## Smallest decisive check — proposed, not executed

### Minimum new work: one HF worker, no new vLLM calls

Use the exact actual **seed0 teach** adapter from `S/fit_teach/result.json`,
on the native host where its bound weights exist. This choice minimizes new
work because `T/teach` already has all16 exact-training-prefix vLLM responses.
It is not a best-checkpoint or best-seed selection. No dose/rank changes.

Freeze all16 original memory cases in training-ID order before launch.
For each case, the HF worker should:

1. Bind base path/model hashes from the original plan; adapter path and full
   file inventory from its actual fit result; tokenizer/source versions;
   original native training context/target and the paired `T/teach` raw call.
   Reject mismatches rather than replacing paths, cases, targets, or manifests.
2. Load one fresh frozen HF base and exactly one PEFT adapter, no merge,
   nesting, optimizer, updates, saving, or training mode. Check full loaded
   LoRA key/shape/finite-tensor/hash correspondence to the serialized state;
   record any dtype conversion explicitly. `model.eval()`, all requires_grad
   false, inference/no-grad context. Hash immutable inputs before/after.
3. Reconstruct the **exact** training prefix from the native exported span.
   Its rendered bytes and42 input IDs must match `T/teach`'s actual request
   rendering/response input IDs. No appended hint, answer, log fact, or
   extra chat templating. Verify each color is one native token and EOS is
   separate. Do not guess non-red token IDs from memory.
4. For a prefix of lengthP=42, compare the native next-token distribution at
   logits positionP-1=41 to the gold color ID and to the actual vLLM first
   output ID1151. Record full-vocabulary argmax/decoded token, all four color
   logits/log-probabilities, gold-color NLL, gold-minus-red margin, and the
   complete float32 logit vector or a saved raw tensor artifact with hash.
   Closed-set four-color argmax is supplementary, not a rescued answer.
5. Also replay the original encoded memory item `[prefix, color, EOS]` with
   the original labels. Assert the color is labeled at index42 and predicted
   from logits41; EOS is at43 and predicted from42. Report color NLL and EOS
   NLL **separately**, plus full-response mean. Gold input at position42 must
   never be used to score that same position's color: that would be leakage.

For strongest render/causal parity, use separate prefix-only and exact-item
forwards,16 of each, no generated continuations. This is one bounded model
load and32 singleton forwards, not32 independent scientific replications.
Both routes should agree at the color-prediction position within recorded
numeric differences. Preserve raw results; do not force equality by changing
dtype/backend settings or silently adjusting a tolerance after inspecting
outputs. If only the minimum16 exact-item forwards fit the budget, explicitly
label prefix-only parity as untested.

### If Main wants repetition-specific parity first

Predeclare `teach_short` as one checkpoint to avoid the within-row long-copy
confound; do not pick a cell after new outputs. Use the same16 HF cases above,
plus **one** unchanged `fundamental_memory_diagnostic` run on that exact
repetition adapter:16 calls, temperature0, seed20260912, max64, no retries,
1024-token output ceiling. Its selected contexts already match the original
training prefixes; verify those against the actual repeated native spans.
Then compare the same checkpoint's HF metrics, exact-prefix vLLM responses,
and its existing dev responses. Do not compare one checkpoint's HF logits
to another checkpoint's vLLM outputs as a backend-parity claim.

### Reusable bounded path; no new framework

- **Supervisor:** `rulegame_parenting_diagnostic.supervise` at`:714` is the
  existing arbitrary-command owner:600-second worker ceiling,140-second
  cleanup reserve, lease/budget checks, logs/process receipt and owned-group/
  GPU cleanup. Main handles full vacancy/allocation beforehand and initializes
  CUDA_VISIBLE_DEVICES before controller spawn. Do not interfere with live
  fading/repetition readouts.
- **HF worker shape:** reuse the ownership/process-receipt/parent-loss watcher
  pattern at `fundamental_memory_diagnostic.py:138`, replacing only the body
  in a future explicitly scoped sidecar with frozen HF loading and finite
  per-memory forwards. Do not change that existing module now.
- **Reload pattern:** `semantic_writer_diagnostic.py:507` already demonstrates
  fresh base -> `PeftModel.from_pretrained(..., is_trainable=False)` -> tensor
  identity checks -> freeze/eval. Its function is hardwired to its own stages
  and cannot directly consume this capsule; reuse the small pattern, not its
  experiment harness or its scientific gates.
- **Metrics pattern:** `gpu/astra_semantic_objective_probe.py:169`
  (`forward_metrics`) shows the correct `logits[index-1]`, float32
  log_softmax, decision CE versus nondecision NLL separation. Its experiment
  CLI is pinned to unrelated semantic fits and MUST NOT be launched here.
- **vLLM path:** unchanged `fundamental_memory_diagnostic.prepare/run/reduce`
  already supplies fixed16 exact-training questions, native capture/audits,
  supervision, cleanup, and a separate in-sample diagnostic label.

There is no located drop-in fundamental HF-logit worker CLI. A small worker
body and bound request/receipt sidecar would require a subsequent scoped code
task; **none has been written or launched in this task**. Do not launch the
broader semantic/objective experiment to obtain these16 logits.

### Interpretation rules fixed before any new output

| Evidence | Narrow interpretation |
| --- | --- |
| HF gold-color top1/confidence differs substantially from exact-prefix vLLM red, with identical loaded state/IDs | Concrete saved-model/backend parity discrepancy. Audit runtime LoRA application, dtype, and generation settings before more fitting; hashes alone did not certify equivalence. |
| HF next-token top1 is also red across16; loaded state and prefix match | vLLM-only failure is not needed to explain those outputs. Saved adapter in the training stack does not demonstrate correct greedy binding on those prefixes. Inspect per-color loss versus EOS/copy loss before proposing learning changes. |
| HF exact-item color logits differ from prefix-only logits beyond documented numerical effects | Target shift, mask/causal, padding/position, or execution parity needs resolution first; do not treat low teacher-forced loss as binding. |
| Repetition exact-prefix HF/vLLM both correct, while its dev remains red | Evidence of training-surface-specific recall for that checkpoint, not heldout transfer; original seed0's exact-prefix failure remains a separate fact. |
| Some near-tied or mixed logits | Report per-device margins and disagreements without turning four-color ranking into a correct generated answer or a new threshold. |
| Missing weights, partial receipts, source/model mismatch, or failed cleanup | Non-diagnostic/incomplete; not zero accuracy and not permission to tune or retry automatically. |

## Key artifact hashes

```
eba01c800d4bf6e9772cefec413be8c6f41b26f0d6e9ab0ced66862d7f348160  R/manifest.json
8786be46beb9d5c6948f407b39ac25526dee4d4d1a5b9192d49c6ba9b579a67f  R/fit_plan.json
d5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e  S/plan.json
ba2f9807de7b6398102eab199563837dc4d0bee044d922349e37ad491eecdc9b  T/teach/reduction.json
267947221b1ba58aacef16553c39570f8f521c728c0b712a424819e7c41dc355  T/control/reduction.json
```

This report establishes artifact-level observations and a bounded discriminating
check, not a causal diagnosis, a scientific claim change, a compiler change,
or evidence of passive fading/child sleep. **EDIT-STOP.**
