# Original seed0 teach HF/SEQ100 parity — 2026-09-12 — EDIT-STOP

## Delivered / tests

Only these files were created or edited:

- `/tmp/astra_fundamental_hf_parity_20260912.py`
- `/tmp/test_astra_fundamental_hf_parity_20260912.py`
- `/tmp/astra_fundamental_hf_parity_handoff_20260912.md`

**22/22 local CPU tests PASS, zero skips; CLI help PASS.** No torch,
safetensors, or native model dependencies are installed in this local test
environment. Tests use CPU tokenizer/logit/state fixtures; native HF/PEFT
loading was NOT exercised. No GPU/network/Git, model calls, generations,
training, or repository edits were performed. Main owns native preparation,
GPU0 allocation/logging/launch and release.

Run tests from the intended immutable source snapshot's working directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python -B /tmp/test_astra_fundamental_hf_parity_20260912.py
```

Code hashes:

```
e296c7965f6e7a6ff477deafddbbbbaa42457810ca9e9522ece4421951e98b25  astra_fundamental_hf_parity_20260912.py
8f2c1c2123bb6155a1b64001d835785e567049612cc2a324f153d3d601372c5f  test_astra_fundamental_hf_parity_20260912.py
```

## Exact fixed scope

- Original seed0 **teach only**, pinned seed0 plan SHA256
  `d5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e`.
- Exact16 original memory training cases in training-ID order. Model and
  adapter paths derive from the actual seed0/SEQ100 receipts, never guessed.
- SEQ100 input is the completed **teach cell root containing its plan.json,
  reduction.json and run/data/calls/**, not the three-cell parent directory
  and not the48-case dev readout directory.
- The complete inherited vLLM request/response objects, rendered strings,
  prefix IDs, expected targets, source IDs, and actual output IDs/text are
  retained in the new plan. SEQ100 remains untouched.
- Exactly32 HF forwards: prefix-only plus full original encoded memory item
  for each of16 cases. **Zero new vLLM/OFF/confirmation/generation calls and
  zero optimizer steps.** No training/save/merge/nesting or adapter changes.
- Label: `IN_SAMPLE_HF_VLLM_PARITY_NOT_NEW_EVALUATION`. No automatic numeric
  discrepancy threshold, no scientific verdict, and no dose/rank changes.

## Main commands

Set variables using actual native paths:

- `SOURCE`: immutable compatible source snapshot; imports are checked against
  this root. It must contain the existing native memory diagnostic, V3
  warm-state helpers and dependencies. Source path is not hardcoded.
- `SEED0_ROOT`: actual `astra_fundamental_teaching_20260912_attempt1` root.
- `SEQ100_TEACH`: actual completed SEQ100 teach diagnostic cell root.
- `PARITY_ROOT`: fresh nonexistent output outside source/model/seed0/SEQ100.
- `LEASE_END`: actual Unix lease-end float, with more than750 seconds remaining
  when preparing. Existing SEQ100's old lease need not still be live.

CPU preparation, no model load or CUDA:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
python -B /tmp/astra_fundamental_hf_parity_20260912.py prepare \
  --source-root "$SOURCE" --root "$PARITY_ROOT" \
  --seed0-root "$SEED0_ROOT" --seq100-root "$SEQ100_TEACH" \
  --lease-end "$LEASE_END"
```

Prepare reuses `fundamental_memory_diagnostic.verify` and
`base.audit_native_calls` on existing receipts; it loads only the local
tokenizer and hashes real model/adapter files. It validates the original fit,
80 completed steps, finite loss, source corpus hashes, exact native training
spans/labels, all16 raw responses and capture identities, and cleanup receipts.
Changed/missing inputs fail; no silent remapping, retry or overwrite.

Only AFTER Main's CPU/native preparation and full GPU0 vacancy/allocation
checks, launch from Main's own logging/ownership wrapper:

```bash
CUDA_VISIBLE_DEVICES=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
python -B /tmp/astra_fundamental_hf_parity_20260912.py run \
  --source-root "$SOURCE" --root "$PARITY_ROOT" --allow-gpu
```

Reduce after the supervised worker completes successfully:

```bash
PYTHONDONTWRITEBYTECODE=1 python -B /tmp/astra_fundamental_hf_parity_20260912.py reduce \
  --source-root "$SOURCE" --root "$PARITY_ROOT"
```

No separate GPU selector or model/adapter override exists. The controller
requires initial CUDA_VISIBLE_DEVICES=0; the worker uses logical cuda:0.
The private `_worker` is not a direct launch interface: it requires the
owning supervisor PID/PGID/argv receipt.

## Worker safeguards and measurements

Uses existing `base.supervise`:600-second worker ceiling,140-second cleanup
reserve, native remaining-budget/lease checks, occupied-device rejection,
fresh subprocess group, logs/process/supervision receipt and group/GPU
cleanup. Main retains external reservation and outer supervision. A worker
parent-loss/deadline watcher uses the existing native diagnostic pattern.
No full `check_free` is called inside the worker/controller.

Worker loads local HF base in bfloat16 and one PEFT adapter with
`is_trainable=False`; all parameters are frozen and model.eval() is enforced.
Saved LoRA configuration is compared against the original training recipe.
All serialized LoRA tensors are loaded on CPU and checked for complete
keys/shapes/finiteness against the actual HF/PEFT loaded state. Exact tensor
hash equality is required after explicitly recorded dtype conversion; the
unconverted source inventory is retained too. Final loaded tensor inventory
must equal initial loaded inventory. Immutable model/adapter/source/receipt
file hashes are checked again after evaluation. No parameters are saved.

Per case:

1. Assert exact native prefix string/IDs against original training and SEQ100.
2. Prefix-only forward: read logits at `P-1`.
3. Full original input `[prefix, color, EOS]` with original masked labels:
   color label atP is scored from logitsP-1; EOS label atP+1 from logitsP.
   Shapes and index shifts are hard guards. Both forwards use attention ones,
   use_cache=False, no added prompt material, and inference_mode.
4. Preserve all three vocabulary-wide float32 logit vectors, full-vocabulary
   top1/decoded token, gold logprob, all four color logits/logprobs, gold-red
   and gold-actual-vLLM-first-token margins, color/EOS losses separately,
   reported HF full-item loss and difference from recomputed loss, and
   prefix/full maximum absolute logit and gold-logprob differences.

Numerics: logit vectors are float32; derived log probabilities use a stable
float64 Python logsumexp over those saved vectors. This is explicit, not a
claim that it reproduces every native HF reduction bit. Top1 uses the full
vocabulary, not a four-color rescue. Numeric differences are reported, not
silently forced below a tolerance or converted into pass/fail.

## Artifacts / reduction

```
plan.json, plan.sha256.json
run/worker/{stdout.log,process.json,supervision.json}
run/data/load.json
run/data/state_after.json
run/data/train-memory-000.json ... train-memory-015.json
run/data/train-memory-000.f32  ... train-memory-015.f32
run/data/cleanup.json
run/data/manifest.json
reduction.json
```

Each `.f32` stores **three consecutive little-endian float32 vectors**, in
order: prefix-only next-token, full-item color-position, full-item EOS-position.
`vocab_size` is in that case's JSON. No torch pickle reader is needed to audit
these logits. The plan carries the complete original SEQ100 raw outputs.

Reducer requires successful group/GPU cleanup, exact output membership and
hashes,16 complete paired cases,32 forwards, and unchanged loaded state. It
recomputes all derived logit metrics from raw `.f32` evidence, rather than
trusting summary values. It records HF/vLLM top1 agreement count and actual
supervised reserved seconds, with `comparison_threshold=null`. No scientific
accuracy threshold or automatic diagnosis is introduced.

Missing artifacts or a failed worker/cleanup are failures, not scientific
zeros. There is no resume, overwrite or automatic replay. A failed prepare or
run can leave an intentionally unusable partial output root. Abrupt host loss
or SIGKILL still requires Main's owned-group/GPU cleanup verification; this
uses the existing process-group supervisor, not a new cgroup framework.

## Remaining native checks / limitations

- Main must validate preparation on the actual SEQ100 and seed0 files and
  run the native worker. Local tests do not exercise HF/PEFT installation or
  actual weight loading, CUDA kernels, causal HF outputs or runtime duration.
- Actual base file identity and freezing are checked; this does not serialize
  every frozen base tensor from GPU memory or resolve formal base origin.
- Source hashes must remain unchanged after prepare, including the copied
  sidecar. Do not point tests at another CWD or mix imported source roots.
- Whole SEQ100 cell inventory is bound: adding files to that completed cell
  after prepare invalidates the parity plan. Keep new launch logs under the
  parity root/Main's separate logging destination, not under SEQ100.
- This implements only Main's selected original seed0 teach parity assay.
  It does not expand to repetition checkpoints, other arms, new evaluations,
  dose/rank sweeps, or live fading interventions.

**EDIT-STOP.**
