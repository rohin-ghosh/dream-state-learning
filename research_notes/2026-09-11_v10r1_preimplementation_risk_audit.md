# V10R1 pre-implementation risk audit

Date: 2026-09-11 PDT / 2026-09-12 UTC

Status: fresh independent read-only advisory. No source implementation,
tokenizer/model execution, fit, adapter, GPU, parenting, C11, claim, release,
or submission authority follows from this note.

## Verdict

V10R1 is implementable, but it needs the dedicated three-file experiment path
named by its exact scope. Reusing the current generic trainer or probe paths
unchanged could manufacture either a false pass or an uninformative
`OPTIMIZATION_INCONCLUSIVE` result.

This remains a supervised seen-key writer kill-gate, not a Dream--LoRA--Think
result. Even a full pass qualifies only four fitted conditional-policy
instances and advances to one identity-disjoint cumulative retention write.

## Highest-priority implementation hazards

### 1. Effective training dose can silently change

V10R1 requires, per fit, exactly 128 rows, batch size 1, two epochs, 256
optimizer steps, context-masked loss, and only `ACT: a0\n` or `ACT: a1\n`
plus EOS as supervised continuation.

Existing paths do not preserve that contract by default:

- `organism_v6/memory_dose.py` defaults to three epochs, batch size four and
  length 512, and skips non-finite batches around line 2653;
- `organism_v6/train_adapter_v21.py` can truncate prompt/answer material and
  skip non-finite batches before writing completion state;
- `organism_v6/train_adapter_v3.py` can switch packing geometry through a
  fallback path around line 577.

The CPU receipt must prove exact masks, target bytes, EOS, candidate token
counts, no skipped or truncated targets, exactly 256 planned updates, and no
packing or fallback. A non-finite training batch must abort rather than reduce
the dose.

### 2. Training and scoring can disagree at the token boundary

The current memory-dose training and scoring paths assign a boundary-straddling
token differently (`memory_dose.py` around lines 2459 and 2283). V10R1 must
use one identical joint token stream for masked training and candidate scoring,
including newline and EOS.

Fake-tokenizer fixtures must cover ordinary, multi-token,
boundary-straddling, unequal-candidate-length, missing-EOS, duplicate-EOS and
truncating cases. Only exact agreement passes. A separately authorized real
Qwen-tokenizer preflight must repeat the check before any model load.

### 3. Incomplete crossing or label leakage can create a false pass

Required deterministic facts include:

- 512 training rows total and 128 per root-map fit;
- 384 primary held items and 64 per root-condition;
- within each root, W+ and W- context bytes, order, seeds and masks identical,
  with only target bytes changed;
- identifier mutation cannot change slot orientation;
- target permutation cannot change prompts, schedules, nuisance fields, row
  order or request seeds;
- train/held templates and both roots are disjoint;
- every varying visible categorical field is inventoried and undeclared ones
  fail;
- deterministic constant, tool, mode, stratum, stratum-by-mode, declared
  covariate and covariate-by-mode policies have exact balanced accuracy 1/2;
  orientation-by-mode has 1.0.

### 4. Fit identity can be confused with corpus identity

The cross-node diagnostic established that byte-identical effective examples
can yield very different fitted artifacts under confounded executions. The
original fresh-owner comparison also silently differed in training seed.

The dry-run receipt must bind exactly four clean-base fits, explicit seed
arguments with no default fallback, full optimizer/precision/scheduler/LoRA
configuration, unique root-map adapter identities, safetensors/config/tree
hashes, and separate load receipts for generation and scoring. There is no
result-driven retry, best-rerun selection, sequential adapter fitting, or
adapter-reuse cache.

### 5. Text normalization can change the interface label

Do not pass primary outputs through `batch_loop.py`, which strips model text
before storage. The reducer needs the complete raw output bytes and the exact
V10R1 rules: ASCII outer-boundary trimming only; exact line-anchored,
case-sensitive `ACT:` counting; U+00A0 rejected; extra prose, fences, internal
newlines, empty output and truncation counted as terminal invalid outputs.
Only a true pre-output infrastructure failure may receive the one identical
retry. OFF-only multiple-ACT is diagnostic; adapter multiple-ACT is
gate-bearing.

### 6. Rounded likelihoods can flip a gate

The existing memory-dose evaluator rounds log probabilities before writing
and directly exponentiates them (`memory_dose.py` around lines 3033 and 2987).
V10R1 needs full-precision records and stable log-sum-exp arithmetic.

Golden reducer fixtures must cover full continuations including newline/EOS,
per-template NLL differences followed by the even median, fixed denominators
with invalids retained, shared OFF outputs against both maps, shared adapter
outputs against own and opposite maps, spill TV, legal-ACT-rate change, exact
thresholds and immediately-below values, all co-failure precedence cases, and
non-finite likelihood as `NONREPORTABLE_ABORT`.

### 7. Global completion markers and stale caches are insufficient

The run root must be fresh and containment-checked. Canonical JSON is sorted,
compact UTF-8 with exactly one LF. Request identity includes operation kind,
model/tokenizer, adapter hash or OFF, prompt, candidate bytes, seed and all
parameters. Cache entries cannot cross kind, adapter, payload or run.

Stage receipts and the final seal are fail-if-exists. Finality requires all
four adapter trees and every fixed-denominator request, not a global marker.
Tampering with any raw record, adapter tree or report must break replay, and
in-memory reducer replay must reproduce identical report bytes without
overwriting the original.

## Required pre-model receipt bundle

- `mwg10r1_inheritance_receipt.json`
- `mwg10r1_output_gate_receipt.json`
- `mwg10r1_cpu_suite_receipt.json`
- `mwg10r1_review_receipt.json`

Both post-implementation reviewers must inspect the same effective-scope,
source, test, manifest, dry-run and CPU-receipt hashes. Independent rejection
controls.

Eight examples per key may genuinely be too little. If all dose, mask,
tokenization and fit-identity receipts pass and the scientific run still misses
the NLL gate, the bound result is `OPTIMIZATION_INCONCLUSIVE`: not writer
incapacity and not permission to rerun until lucky.

## Evidence basis

- `research_loop/changes/chg_20260911_multikey_writer_gateway_v9_simple/exact_scope.md`
- `research_loop/changes/chg_20260911_multikey_writer_gateway_v10_simple/exact_scope.md`
- `research_loop/changes/chg_20260911_multikey_writer_gateway_v10r1_simple/exact_scope.md`
- `research_notes/2026-09-11_cross_node_writer_localization_result.md`
- `research_notes/2026-09-11_cross_node_effect_adversarial_audit.md`
- `research_notes/2026-09-11_v10r1_fit_variance_decision.md`
- current `memory_dose.py`, `train_adapter_v21.py`, `train_adapter_v3.py` and
  `batch_loop.py` source at this note's commit.
