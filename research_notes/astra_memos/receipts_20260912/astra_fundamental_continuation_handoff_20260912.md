# Fundamental ACT-only continuation material — September 12, 2026

**EDIT-STOP.** Only these files were created:

- `/data/home/rohing/dream-state/organism_v6/fundamental_continuation_corpus.py`
- `/data/home/rohing/dream-state/tests/test_fundamental_continuation_corpus.py`
- `/tmp/astra_fundamental_continuation_handoff_20260912.md`

Released trainer/test ownership remains released: no edits to
`train_adapter_v3.py`, `test_train_adapter_v3.py`, Euler's repetition files, the
original teaching corpus, readout, or any other contributor file. No Git,
network, GPU operations, model downloads, training, inference, or orchestration
were performed. Temporary CPU test fixtures were cleaned up by their tests.

## Exact material and selection

- Generation seed **20260918** is a fixed integer seed, not the preparation date.
- Enumerate unordered pairs `(left, right)` lexicographically with
  `0 <= left <= right < 20`: 210 possible pairs.
- Exclude **all 128 original arithmetic source pairs**, including original
  training, all original evaluation, and the confirmation half. Exclusion and
  validation use unordered pairs and therefore also exclude operand reversal.
  No confirmation model outputs or scores are inspected.
- Exactly **82** pairs remain. Shuffle once with `random.Random(20260918)`, take
  the first **64**, and divide into **four consecutive blocks of 16**. The other
  18 pairs are not emitted as training or new evaluation cases.
- Ordered pair-list fingerprint, SHA256 of compact JSON with separators `,`/`:`:
  `1e88173ad878abac5782ddeb4184fce43c5bd37723e6afd0b67253d16bd2853a`.
  First four pairs: `(4,11), (11,15), (1,1), (14,15)`.
  Last four: `(6,15), (1,4), (9,9), (6,16)`.
- Phase IDs are `continuation-phase-01` through `continuation-phase-04`.
  Each phase has record IDs `PHASE-addition-000` through `PHASE-addition-015`;
  source event IDs are `source-RECORD_ID`. Sources, records, and derivations
  explicitly carry phase IDs and their source-event relationships.
- Raw context is **exactly** `original.addition_context(left, right)`:
  `Add <left> and <right>.\nSubmit the sum using ACT: <integer>.`
- The entire response is **`ACT: <sum>`**, with one space after the colon and no
  terminal newline, PREDICT, COMPUTED, reflection, parent guidance, or memory QA.
  Integer outcomes and every target are validated directly against their source.
- Material is generated once, with no rate/trainer-seed parameter. Identical
  phase files serve every rate and trainer seed. Neither outputs nor outcomes
  can select pairs, order, rates, or generation seed through this interface.

## Intended recipe — metadata, not an executed run

```text
rank=8, alpha=16, dropout=0.05, bias=none, layers=all
target_modules=q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj
optimizer=adamw
epochs_per_phase=4
batch_size=4, grad_accum=1
pack=false, max_len=512, chat_template=false, add_eos=true
max_steps=0 (the native trainer's no-cap meaning)
16 examples / 4 per batch * 4 epochs = 16 intended updates per phase
4 phases/cuts = 64 intended updates per trajectory
learning_rates=[0.0, 3e-5, 1e-4]
sentinel trainer seed=0; paired trainer seeds=[1,2] only if Main judges sound
WEIGHT_WARM_START_FRESH_OPTIMIZER at every phase
```

Main carries the prior phase's full single-adapter LoRA weights into the next
phase using the separately accepted warm-start interface. Optimizer state is
fresh at each call, not resumed. This module does not select the parent, initialize
an adapter, configure the trainer, run the sentinel, launch replicas, or schedule
the rates. Corpus files do not themselves apply CLI trainer flags: Main must
match the declared recipe, including `--no-pack` and avoiding a second chat wrap.
Update counts are intended counts assuming finite completed training, not
observed updates. Rate zero is still a specified update recipe, not a passive
time-only control by construction.

## Python API

```python
build_candidate() -> candidate
validate_candidate(candidate) -> validation
export_native(candidate, tokenizer) -> {"corpora": ..., "audit": ...}
emit_candidate(out) -> manifest
prepare(out, model=None, tokenizer=None) -> manifest
verify(root) -> validation
```

`build_candidate` and `validate_candidate` require no tokenizer, PyTorch, PEFT,
model data, or network. Candidate data contains phases, 64 sources, 64 exact
derivations, the exclusion-pair inventory, counts, recipe, and claim boundaries.
Validation checks arithmetic, keys, phase/source IDs, every target/context,
uniqueness, original-pair exclusion, and exact fixed candidate/order/recipe.

`export_native` accepts an injectable tokenizer and calls only the existing V3
pure-Python normalizer, encoder, no-pack grouping, and collator. Each exported item:

```text
spans: [[actual native-rendered context, false, "context"],
        ["ACT: <sum>", true, "authored_task_only_target"]]
group: exact record ID
view: "addition"
order: phase-local 0..15
meta: {record_id, phase_id, source_event_ids}
```

The tokenizer receives exactly one user message containing the original context,
with `tokenize=False, add_generation_prompt=True`. No expected answer, source
event, phase ID, reminder, or example is passed to the template. The exact native
template rendering is retained. In particular, “no answer in prefix” means no
appended answer: operands can naturally equal the sum in zero-operand cases.

Both spans are encoded with `add_special_tokens=False`; the native EOS ID is
appended once to the target. Prefix labels are all `-100`. The exact input and
label arrays are compared to native V3 encoding/collation, and all split/dropped
tokens or examples exceeding 512 tokens cause rejection. No content padding or
truncation is introduced. Ordinary batch-of-four right padding is audited, uses
the actual pad token (or actual EOS when pad is absent), and has labels `-100`.
It is not packing. Example IDs/groups remain distinct, one example per sequence.

## Emitted artifacts and audit evidence

Raw `emit` writes `candidate.json` and `manifest.json` only. Native/token-fixture
preparation writes these **seven** files:

```text
candidate.json
continuation-phase-01.json
continuation-phase-02.json
continuation-phase-03.json
continuation-phase-04.json
token_audit.json
manifest.json
```

Each phase file has the existing `{"corpus": [16 V3 items]}` shape. The token
audit retains per-record rendered context, response, messages, source IDs, phase
IDs, actual prefix/response/input token IDs, EOS ID, full label vector, vector
hashes, and input/context/target counts. It reports **per-epoch**, **four-epoch
per-phase**, and **four-phase/four-epoch total** token counts separately.
Counts exclude masked batch padding; seed-dependent group shuffling may change
padding cost but does not change the material or nonpadding token totals.

All artifact bytes have SHA256 hashes in the manifest, together with source
hashes for this generator, the original corpus, V3 trainer and native helper
dependencies. Actual-model preparation hashes local model/tokenizer files both
before and after the CPU audit and refuses drift; source drift also fails.
Output roots and file writes are exclusive. Existing files/directories/dangling
symlinks are refused. A collision preserves the other writer's file and never
creates a success manifest. Failed pre-write token audits leave no output root.

`verify` checks recorded source hashes, exact artifact membership/content hashes,
and regenerates/validates the raw candidate. It is not a rerun of the native
tokenizer or a scientific review; Main should bind the accepted manifest hash
externally and retain the token audit. No completed model run is claimed.

## Commands

CPU tests, executed locally with **20/20 passing and no skips**:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s tests -p test_fundamental_continuation_corpus.py
```

Optional raw material emission into a fresh root:

```bash
python -B -m organism_v6.fundamental_continuation_corpus emit \
  --out /tmp/astra_fundamental_continuation_raw_20260912_attempt1
```

**Native CPU token-audit/export command for Main**, using the local frozen base
and a fresh material root (no GPU allocation, inference, or training):

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
python -B -m organism_v6.fundamental_continuation_corpus audit-native \
  --model "$PINNED_LOCAL_QWEN_BASE" \
  --out /tmp/astra_fundamental_continuation_native_20260912_attempt1

python -B -m organism_v6.fundamental_continuation_corpus verify \
  --root /tmp/astra_fundamental_continuation_native_20260912_attempt1
```

`prepare(out, model=...)` loads the local tokenizer through the existing native
helper (`local_files_only=True`); it never constructs a generation/training model.
Use the phase paths from `manifest["phase_corpora"]`. Freeze source bytes before
preparing; later trainer/generator changes correctly invalidate the source audit.

For injectable CPU fixtures, use `prepare(out, tokenizer=fixture)` instead.
That manifest explicitly says
`INJECTED_TOKENIZER_AUDIT_NOT_AUTHENTICATED_NATIVE_EVIDENCE`, with
`native_token_audit=false`. Model and injected tokenizer are mutually exclusive.

## Limits and interpretation

Required label is retained verbatim:
**TASK_ONLY_INTERFERENCE_NOT_PASSIVE_FADING_NOT_CHILD_SLEEP**.

ACT-only competing targets can overwrite the prediction habit. Do not infer
forgetting from time alone, passive fading, child sleep, prediction intelligence,
or absence of pretraining exposure. New operand pairs need not have new sums or
new constituent operands. These are training examples, not new evaluation cases.
No confirmation requests or readout changes are introduced.

Local tests use token fixtures, including a mocked local-loader path to test
hash binding. **No actual Qwen native-token audit was performed here**, and no
native token totals are claimed from those fixtures. Main's command must produce
the actual totals before any use. The original teaching epoch's 4,517/912 token
counts are not reused or assumed for these new 16-row ACT-only phases.

The tests cover fixed pair order/counts, all original pairs including confirmation
and reversal, exact source keys/phases/targets, no old memory facts, immutable
recipe/reproducibility, template inputs, native V3 mask/EOS/batch fixtures,
truncation rejection, source/model-byte drift, fresh roots, hashes, file races,
and CLI behavior. An inherited import emitted a ResourceWarning for an existing
unclosed `parent_prompt.txt` read; it did not fail tests and was not changed.

**EDIT-STOP. Main owns native audit acceptance, warm-start parent bindings,
recipe application, sentinel/replication decisions, budgets, and launches.**
