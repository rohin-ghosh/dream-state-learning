# EDITSTOP — bounded L2 access / teacher-forcing diagnostic

2026-09-13 06:31:04 UTC. CPU-tested readiness only; no native/model/network/Git
execution and no original-root/source or repository edits. Main owns launcher,
fresh reservation checks, GPU mapping, PIDs, process-group timeouts and collection.
The provisional CLI is unchanged. Main's reported 390-second worker windows are
within this worker's 400-second maximum; Main's 1200-second overall window must
also cover reduction, subprocess startup/exit and cleanup.

## Owned deliverables / SHA256

- `/tmp/astra_l2_access_probe_20260913.py`
  `633461895976b034729b71911216ec7fa5df385b922382fd67b800e9371847e5`
- `/tmp/test_astra_l2_access_probe_20260913.py`
  `eb30485487d979d0a8d95aa470966ec31c315eeca04dfd5193a83317d7347b88`
- `/tmp/astra_l2_access_probe_handoff_20260913.md`
  Its post-write SHA256 is in the final EDITSTOP response.

No edits to Main's controller, seed parameterization, manuscripts, notes or state.
The repository runtime/test hashes remain respectively
`d1965ddc571ec393ef0ec656eda8556b3db91d7de81fafa87310900706d96a3d` and
`14fbbc06b9f748685069bcb978df388791408f679e71025c7c95c324d7be4272`.

## Original immutable bindings

Native root is fixed, not an optional alternate root:
`/localhome/local-rohing/astra_diagnostics/l2_public_record_20260913_attempt1`.
Native source is the original plan's source; local CPU copy is
`/tmp/astra_l2_native_source_20260913_attempt1`.

- Runtime: `213c2a2f508815eef752c72424f5dca64b76c9edb963f7ed6f68d5522c18853e`
- Core: `0bb33988f003a0111e14cdfb53b3dc86a695e8e20656c90e71cfadb5ad28d352`
- Trainer: `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`
- Plan: `da6a2d651d152979afee1ab862ab9218ef571149705e4bff5ad1a4ebc0289125`
- Seal: `14a0e0b33998dba794642d014f1f9f5939b78e6956d1724f497660c7e239e42f`
- Collection file: `/tmp/astra_l2_collection_20260913_attempt1.json`
  `a2d80c7e1e973d102a675507fc4d0ef40a1a25acd4516729ea9ade54dd90347f`
- Base file-inventory hash: `1a28421dffcee174137818b590991ba80678b58f6c63fd8eab027a933486efd5`
- fit1 candidate: `95f7cc2489b3091537c8629aab814ed593ab44423c5303ddc7f77aae32ace286`
- fit2_PROMOTE candidate: `2e6778a24dfc72648504cbb39fc8866a4a6208330eac5dccf93bcf5431d7bf2e`
- Public helper: `59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c`
- Reflection helper: `0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc`

The original runtime revalidates its four-file inventory, interpreter, exact plan,
helpers, model binding, prepared files and frozen world. Worker checks sealed
root custody before/after, original base file hashes, original candidate file
inventories and the original helper configuration checks. No pin relaxation or
new source/plan is substituted into the original root.

## Stable worker CLI — Main only, not executed here

```sh
CUDA_VISIBLE_DEVICES=3 PYTHONDONTWRITEBYTECODE=1 ORIGINAL_PINNED_PYTHON -B /tmp/astra_l2_access_probe_20260913.py worker --source /localhome/local-rohing/astra_sources/l2_public_record_20260913_attempt1 --collection /tmp/astra_l2_collection_20260913_attempt1.json --state OFF --output /FRESH_EXTERNAL_DIRECTORY/OFF.json --deadline-unix ABSOLUTE_UNIX_DEADLINE --allow-native
```

Repeat in fresh subprocesses for `fit1` and `fit2_PROMOTE`, each with a distinct
fresh output file. Parent directory must already exist. Use the interpreter
recorded in the original plan. `CUDA_VISIBLE_DEVICES` is Main's responsibility;
the example physical index is not a replacement for the UUID/reservation check.
Copy the exact pinned collection bytes to the worker location if necessary.

Each process independently cold-loads the original HF base using the pinned
reflection helper; OFF has no LoRA. Fitted states load their original adapter
with `is_trainable=False`, no merge, no training, and no optimizer. All modules
are eval and all parameters frozen before evaluation. Saved and actual loaded
LoRA tensors are checked by full name/shape/dtype/content inventories against
the exact saved file inventory; expected dtype conversion is explicitly logged.
Actual converted tensor bytes must match exactly, and loaded tensor/file
identities are rechecked after evaluation. This is not a claim that dtype
conversion preserves the original higher-precision source bytes.

Deadline is a finite absolute wall-clock timestamp strictly after worker entry
and no more than 400 seconds later. It is checked cooperatively around loading,
between candidate forwards and before success. A blocked native call cannot be
interrupted by these checks: Main's external watchdog is authoritative. Use
`min(global_deadline, spawn_wall_time + 390)` for Main's stated contract.

Only a complete successful worker writes the requested JSON output file. It has
`state`, integer `forwards: 64`, integer `updates: 0`, PID/timing/pin fields,
adapter/tensor identities, a shared case-encoding digest and 32 rows containing
two fully scored continuations each. Stdout emits 32 pair-progress JSON lines,
then a final small `{output, sha256, state, forwards, updates}` receipt. Main must
capture stdout/stderr outside all original inputs. Failures exit nonzero;
partial progress logs are not successful worker receipts. Output paths are
fresh and disjoint from protected inputs; old root is never an output target.

## CPU reducer CLI

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/astra_l2_access_probe_20260913.py reduce --source /tmp/astra_l2_native_source_20260913_attempt1 --collection /tmp/astra_l2_collection_20260913_attempt1.json --worker /COPIED/OFF.json EXACT_OFF_SHA256 --worker /COPIED/fit1.json EXACT_FIT1_SHA256 --worker /COPIED/fit2_PROMOTE.json EXACT_FIT2_SHA256 --output /FRESH_EXTERNAL_DIRECTORY/access_summary.json
```

On node3, `--source` may instead point to its original pinned source directory.
Reducer imports only the frozen pure core, not torch/HF. It requires all three
states, distinct PIDs, matching case encodings, exact input-file hashes, original
pins, 64 forwards per worker, zero updates, valid finite scores/masks and worker
timings within a 1200-second span. Main additionally accounts for controller
overhead and cleanup. Output is a new JSON summary with `forwards: 192`,
`updates: 0`, diagnostic-only scope, and original vLLM reports separately labeled.
Reducer trusts caller-pinned native worker evidence; it does not independently
deserialize remote tensor files or retokenize with a native tokenizer.

## Prompt, mask and length contract

Two views only: exact wake/train (the frozen core makes these identical) and the
original held readout paraphrase, for all 16 slots. Prepared prompts and actual
wake1/wake2_PROMOTE and baseline/report1_PROMOTE/report2_PROMOTE requests/native
token boundaries are compared with the original sealed artifacts.

Both legal actions come from the frozen public world. Each slot's optional
terminal newline comes from its actual archived child target; it is applied
equally to both candidates, never selected using truth labels. Original fit1
and fit2_PROMOTE training encodings are recomputed using the archived encoder
and checked byte-for-byte against archived JSON. Full assistant native masks
are checked, including exact target plus EOS, masked context/template tail,
no splitting/dropping/truncation, and at most 1024 input tokens.

Main's tokenizer audit reports unequal lengths INCLUDING EOS (12 and 14) and
first divergence at zero-based index 2, with multiple differing positions.
This sidecar did not rerun a native tokenizer. The worker derives all lengths
and boundaries dynamically; it does NOT assert equal lengths or a single
undecided token. Toy CPU fixtures explicitly cover the corrected 12/14 case.

Each candidate gets one causal forward, no HF generation, no label tensor or
loss/backward/optimizer call. Logits at `target_position - 1` score each native
target token, including EOS, via float32 log-softmax. Output retains token IDs,
absolute target positions, full labels/masks and every token log probability.
Exactly 3 states x 2 views x 16 slots x 2 actions = 192 candidate forwards.

## Reading the result without overclaiming

The reducer uses frozen world labels only for evaluation. It reports per-action
token lengths, complete log-likelihood sums and mean NLL; full likelihood and
first-divergent-token margins; length-normalized mean-logprob margins separately;
and old/new correct counts and exact ties for full/first-token choices.
Unequal-length sum ranking can disagree with first-token or normalized ranking.

Loss decomposition uses the longest shared token prefix and non-overlapping
shared suffix. The remaining contiguous middle spans are the multi-token
decision spans, possibly different lengths per action. It reports micro-weighted
NLL/count/mean for full, common, decision, first-decision and EOS tokens, with
prefix and suffix separately visible. Shared suffix/EOS scores are conditional
on different action histories, not evidence of identical conditional contexts.

Compare train versus readout per slot AND their changes versus OFF. Weak/mixed
first and full gold margins in BOTH views does not isolate a paraphrase access
gap; stronger correct train scores with degraded readout scores is consistent
with a possible access gap but is not causal proof. Exact numeric scores are
reported without a tuned ambiguity threshold or automated promotion.
`ln(2)/13 ~= 0.053319` is only an unmeasured reference hypothesis, never a measured
likelihood or evidence of one undecided token. Existing low fit losses and
unchanged 4/8 old + 4/8 new generation do not settle this question.

This is teacher-forced conditional evaluation, not a replay/replacement of
original vLLM generation or original endpoint promotion. No general G1/H1/H2,
learning-success, replication-success or scientific-pass claim is made.

## CPU evidence / limitations

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s /tmp -p 'test_astra_l2_access_probe_20260913.py' -v
```

Final: 17 tests PASS in 2.423 seconds. Includes native-boundary-shaped toy
tokenization, unequal lengths, causal logit shift through an explicitly injected
mock torch API, nonfinite rejection, 64-forward coverage, frozen tensor record
comparison, exact archived-mask/prompt replay using synthetic fixture artifacts,
receipt/pin/PID/time/mask rejection, tie behavior and a scripted access contrast.
Tests do not import torch/HF or instantiate real models. The pure summarizer's
three-state test deliberately uses toy scores; real fitted worker tensor/file
receipts cannot be positively certified without Main's native evidence.

Both CLI help commands passed. Both Python files passed AST parsing and
trailing-whitespace checks; AST audit found no generate/run_training/backward/
step/save_pretrained calls in the diagnostic. Original source/collection and
repository runtime/test hashes were rechecked unchanged.

Native loading, PEFT API integration, actual saved tensor conversion, numerical
results, device performance and completion within Main's envelope remain
unvalidated here. Main's first bounded native execution must fail closed on
any loader/identity/mask/finite/deadline problem; do not weaken pins or substitute
generation. No new fits or replications are part of this diagnostic.
