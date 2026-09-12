# EDITSTOP — bounded level-ZERO repetition/sequence material

2026-09-12. Owner scope: only `organism_v6/fundamental_repetition_corpus.py`,
`tests/test_fundamental_repetition_corpus.py`, and this handoff. No Git,
network, GPU, model loading, fits, trainer edits, existing corpus edits, or
evaluation-confirmation reads. This is implementation of the requested fixed
comparison, not a new architecture/scientific-claim decision.

## Delivered

- Hash-pinned loading of ACTUAL seed0 native teach/control JSON, not regeneration
  from candidate material; no response rewriting or added facts/answers.
- `build_views`: 16 independent short rows per original (1280/arm), or one
  continuous-context long row holding those same 16 copies (80/arm).
- Original groups, ordering values, views, source-event IDs and other metadata
  retained. Short copies remain contiguous. Added metadata binds each copy to
  the original row index and canonical row hash; no metadata enters token input.
- Separate EOS span after EACH response. `add_eos=False`, `chat_template=False`,
  `pack=False` are explicit. Context and response spans stay byte-identical.
- `validate_material(sources, material, tokenizer, seeds=...)` reuses existing
  V3 `normalize_items`, `encode_item_segments`, `collate`, `pack_by_group` and
  `epoch_order`. Checks exact per-copy IDs, labels and categories; no dropped
  tokens, no splits, full-length position/segment arrays, exact 16x budgets,
  arm matching and exact original-group schedules at optimizer boundaries.
- Fresh-only, deterministic output directories; existing files, directories,
  symlinks and dangling symlinks rejected. Source/output/exporter/trainer hashes
  in manifest. A supplied tokenizer is audited BEFORE any output directory is
  created; otherwise status is explicitly `NATIVE_AUDIT_PENDING`.

EOS clarification: native Qwen prompts already contain two masked
`<|im_end|>` delimiters. Those must NOT be removed. “Exactly one EOS per copy”
means exactly one **supervised response-ending EOS**, not one EOS ID anywhere
in the native input. Each copy retains two existing masked context EOS IDs plus
one supervised EOS. Literal one-total-EOS cannot coexist with unchanged native
prompt bytes. Fixture tests explicitly check this distinction.

## Actual V3 ordering verdict: SAFE for the requested group matching

Inspected `pack_by_group(pack=False)`: sorts `(group, order, item_index)` and
emits each encoded item as its own sequence. `epoch_order` shuffles whole
contiguous group blocks using `Random(seed * 1000 + epoch)`. The training loop
slices that order into `batch_size` microbatches, increments `micro`, then steps
when `micro % grad_accum == 0`. It does NOT shuffle individual short copies.

Therefore short: 16 contiguous copies/group, four identical-example copies per
microbatch, four microbatches/group, 16 microbatches/update = four original
groups/update. Long: one sequence/group, one group/microbatch, four
microbatches/update = the SAME four original groups in the SAME order.
Both have 20 updates/epoch, 80 over four epochs, with no partial accumulation.
No trainer fix is required for this inspected version. Non-finite skipped
microbatches would invalidate the planned update accounting; reject such a fit.
The manifest binds trainer source hash; rerun validation if the other worker
changes ordering. A deliberate unsafe per-item shuffle is rejected by a test.

Long is one sequence with no internal attention barrier or position reset:
each later copy can attend causally to all preceding copies. Short copies are
separate batch sequences, resetting context. V3 no-pack uses its ordinary 2-D
padding mask; the causal model supplies causal attention. Fixture checks cover
segment/position construction and the pure causal-mask helper, not model kernels.

Loss weighting: under V3's existing mean loss, each short microbatch contains
four copies of ONE original example. Four such microbatches per group under
accumulation 16 give the same nominal group weight as long accumulation 4.
This is not identical gradients: context/positions differ by design, and
microbatch/accumulation shapes and active dropout=0.05 remain explicit.

## Source and verification evidence

Actual source root inspected read-only:
`/tmp/astra_fundamental_seed0_terminal_20260912/astra_fundamental_teaching_20260912_attempt1`

Pinned source SHA256:

```text
teach.json    2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c
control.json  e6cafbf68f361af7272a02fc23f0a90f92c34cd49b0a8e84437279bb288a8fe7
```

In-memory actual-source material hashes (no durable corpus output written in
this bounded task):

```text
teach_short.json    f56defc759270580bec846264372330d0e8450a53986e4e71d2173e7f95aa844
teach_long.json     36b67c47aa5a89ee34c2df9bb0e1005ce0c46a444301c62321e0d4ee923e7859
control_short.json  dac119c965c6ec1d90cae6a78aab8065cfaeec2b32ba113135aef55a8d164873
control_long.json   6e1cbefd6d78ffe7c2e458c007ec0c5259c1a1cec3ba985bd67a51f913646d53
```

Actual-source metadata-only V3 schedule replay: seeds 0, 1, 2, 17; 80 updates
each representation/arm. This replay uses placeholder tokens and is NOT a
native tokenizer audit. Native tokenizer snapshot was not found locally;
native token verification remains PENDING. No remote fetch attempted.

The saved seed0 training plan reports 4517 input / 912 target tokens per arm
and a 61-token maximum original example. Expected per view/arm/epoch is
72272 input / 14592 target tokens; four epochs is 289088 / 58368. Expected
long maximum is 976 tokens; short maximum 61. These are reference-derived
expectations, NOT fresh native audit results. `max_len=2048` is a pilot ceiling,
not evidence of “superlong” validation.

Tests: **27 new tests passed**, plus **11 existing teaching-corpus tests**,
**38 passed total**. No trainer-owned tests edited or run. Invocation:

```bash
PYTHONDONTWRITEBYTECODE=1 /data/home/rohing/.cache/uv/archive-v0/gQNbv0KfvnaJ_g5l/bin/python -B -m pytest -q -p no:cacheprovider tests/test_fundamental_repetition_corpus.py tests/test_fundamental_teaching_corpus.py
```

System `python` is absent; system `python3` lacks pytest. The already-cached
interpreter above was used without installation or network access.

## Exact source-hash/native-audit command for the builder (NOT run here)

Use a CPU environment with the EXISTING native tokenizer dependencies and the
original local Qwen2.5-7B-Instruct snapshot; no weight loading or downloads.
Set `SOURCE` to the actual seed0 source root on that machine, not candidate/.
The example uses the original worker paths. `OUT` must not already exist.

```bash
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
SOURCE=/localhome/local-rohing/astra_diagnostics/astra_fundamental_teaching_20260912_attempt1
TOKENIZER=/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28
OUT=/localhome/local-rohing/astra_diagnostics/astra_fundamental_repetition_20260912_attempt1
PYTHON=/localhome/local-rohing/v2/venv/bin/python
sha256sum organism_v6/fundamental_repetition_corpus.py organism_v6/train_adapter_v3.py "$SOURCE/teach.json" "$SOURCE/control.json"
sha256sum "$TOKENIZER/tokenizer.json" "$TOKENIZER/tokenizer_config.json"
"$PYTHON" -B -m organism_v6.fundamental_repetition_corpus --teach "$SOURCE/teach.json" --control "$SOURCE/control.json" --out "$OUT" --tokenizer "$TOKENIZER" --seeds 0 1 2 17
"$PYTHON" -B - "$OUT/manifest.json" <<'PY'
import json
import sys
with open(sys.argv[1]) as handle:
    manifest = json.load(handle)
assert manifest['status'] == 'TOKENIZER_AND_V3_ORDER_VALIDATED_NO_FIT'
for arm in ('teach', 'control'):
    budgets = manifest['audit']['arms'][arm]
    assert budgets['original'] == dict(rows=80, input_tokens=4517, target_tokens=912, max_sequence_tokens=61)
    assert budgets['short'] == dict(rows=1280, input_tokens=72272, target_tokens=14592, max_sequence_tokens=61)
    assert budgets['long'] == dict(rows=80, input_tokens=72272, target_tokens=14592, max_sequence_tokens=976)
print('Actual seed0 native budgets and V3 group-order audit passed; no fit performed.')
PY
```

The final assertion checks reference-native totals as well as exporter equality;
any mismatch is a stop/report, not permission to alter, pack or truncate rows.
The exporter's callable validator can also recheck already-loaded JSON by
constructing `material[arm][view]` from each output's `corpus` field and calling
`validate_material` with the hash-checked source rows and local tokenizer.

## Exact recipe suggestion only — training is outside this task

Fresh frozen Qwen2.5-7B-Instruct base for each fit; learning only in LoRA, no
`--init-adapter`. Common existing V3 CLI arguments:

```text
--rank 8 --alpha 16 --dropout 0.05 --lr 3e-4 --epochs 4
--max-len 2048 --no-pack --no-eos --overflow truncate --optimizer adamw
--layers all --target-modules q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj
--dtype bf16 --seed <SAME_INTEGER_FOR_BOTH_VIEWS_AND_ARMS>
```

- Short input `<arm>_short.json`: `--batch-size 4 --grad-accum 16`.
- Long input `<arm>_long.json`: `--batch-size 1 --grad-accum 4`.
- Keep group shuffling enabled; do NOT add `--chat-template`. Keep default
  fresh initialization, gradient checkpointing and no max-step cutoff.
- `overflow=truncate` selects V3's single-sequence encoder, NOT permission to
  truncate. Require prior audited zero drops, no splits, and unchanged
  corpus/tokenizer/trainer bytes; reject any fit manifest with dropped tokens.
- Model path, device, output directory, launch/provenance gate and any fits are
  the builder's responsibility and outside this code task. The native-audit
  shell block hides GPUs; a future authorized launcher sets its own environment.

Label strictly **continuous-context repetition versus resets**, not child
experience, sleep, or plasticity separation. Microbatch/accumulation and dropout
remain limitations. No scientific result or evaluation confirmation is asserted.

EDITSTOP.
