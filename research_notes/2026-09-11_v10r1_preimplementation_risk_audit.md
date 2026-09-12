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

## Historical exact human boundary after the final consensus

**Superseded execution boundary (2026-09-12 05:50 UTC).** The paragraph and
copyable sentence below preserve the boundary that applied when this audit was
written. Rohin's later standing builder authorization, committed in
`AGENTS.md` at `6e1fb96c`, now permits the Astra builder to design, implement,
test and execute in-scope experiments without per-experiment ratification,
subject to the invariants recorded there. This does not enlarge V10R1's
scientific claim or authorize a laptop watcher to launch competing work.

At the time of the audit, implementation remained forbidden. The final
consensus required human ratification to bind the inherited V9 and V10 scopes,
the V10 adjudication,
and all immutable V10R1 proposal/review artifacts. A shorter sentence that
names only the three exact scopes is insufficient under
`architecture_consensus.json` resolution MWG10R1-D1-PROPOSAL-EQUIVALENCE.

The complete implementation-only ratification sentence is:

> I ratify the V10R1 effective contract composed of V9 exact scope SHA-256
> eac3e25c93230f3788612b3d0a25c0dac3609d49b4a5d9e28cf853ba806c0955,
> V10 exact scope SHA-256
> 12a077950730c3abaef32b04a861d901ef4bae25a22e640b152472f5f364f549,
> V10 consensus SHA-256
> 147aebaaf0b974a37897acc724c6fe27c8e82c6f94db0c1e775eba3d57a1ce7e,
> and V10R1 exact scope SHA-256
> 6cba6518184e7c8d12d7c23088895a565b84ae5ee067eaa63aac4440b91ea1aa;
> I also bind V10R1 architecture-change SHA-256
> 149e346901cabb3a0cee76b8b2280f9e40f97f466ef6316fed8e914f6b4187de,
> scope-proposal SHA-256
> 019731c8cdd8bd66c64bccc489b18836a0e3da1c241a9cbf0b73385a215d168b,
> scientific-interpretation SHA-256
> c95614a39a642688b35b62332c30ee73dce0d3e1ee771861b06ef4b94014a6ad,
> systems-interpretation SHA-256
> e2b4b807c197aee23fd098238f331119a21bb5b8520dba63da6a997c22fcfcd5,
> critique SHA-256
> f3388c870e7f37aa37b537acde84b40e4ea7b07486787b9d7ce868bee6a88fae,
> and consensus SHA-256
> 5792ec9acbf9e2da26f34ff8303bce06a496a3c9f5010162b0e4491db93ea9a2.
> I authorize implementation only of
> gpu/multikey_writer_gateway_simple.sh,
> organism_v6/multikey_writer_gateway_simple.py, and
> tests/test_multikey_writer_gateway_simple.py, plus deterministic CPU tests
> and receipts and the two required V10R1-local reviews, with every tracked
> receipt/review written only inside
> research_loop/changes/chg_20260911_multikey_writer_gateway_v10r1_simple/.
> No other source file may be edited. This does not authorize tokenizer or
> model execution, training, adapters/checkpoints, benchmark or GPU execution,
> parenting, lineage mutation, resource acquisition, C11 work, scientific
> claims, release, or submission.

## Evidence basis

- `research_loop/changes/chg_20260911_multikey_writer_gateway_v9_simple/exact_scope.md`
- `research_loop/changes/chg_20260911_multikey_writer_gateway_v10_simple/exact_scope.md`
- `research_loop/changes/chg_20260911_multikey_writer_gateway_v10r1_simple/exact_scope.md`
- `research_notes/2026-09-11_cross_node_writer_localization_result.md`
- `research_notes/2026-09-11_cross_node_effect_adversarial_audit.md`
- `research_notes/2026-09-11_v10r1_fit_variance_decision.md`
- current `memory_dose.py`, `train_adapter_v21.py`, `train_adapter_v3.py` and
  `batch_loop.py` source at this note's commit.
