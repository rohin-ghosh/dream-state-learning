# Compatible two-habit corpus handoff — EDIT-STOP

UTC validation cut: 2026-09-12T19:07:43Z.

Implementation and CPU fixtures complete. **EDIT-STOP. No launch.** Main owns
Git/source publication, actual local-native CPU validation, original-parent
adapter binding, and any subsequent allocation. Launch still waits for current
plasticity completion and Main's own tests. LR is fixed at **1e-4**, not selected
from plasticity outcomes.

## Owned outputs and SHA256

Only these two repository files were created; no existing live modules or
manuscripts were edited:

| Path | SHA256 |
|---|---|
| `organism_v6/fundamental_two_habit_corpus.py` | `9f540446ca2e1c06aae2bda728d09f8bab955e0d969adf9484c9892594fa3527` |
| `tests/test_fundamental_two_habit_corpus.py` | `73b8e55bace31a2a4e95e9f5afcb301a1d0330f8799d28c39f2f90da21e4fec7` |

The only additional authored output is this `/tmp` handoff. Tests used isolated
temporary fixture directories. No Git commands, network access, GPU work,
model generation, training, or launch occurred. Existing modules were reused
without monkeypatching their globals; tests patch only the owned module's
bindings where a fixture is needed.

## Material and fixed comparison

- Each branch has exactly **80 rows: 64 original arithmetic + 16 original memory**.
  The original row/group/order/source-event inventory is retained. Memory rows
  remain identical as serialized objects, including context, target and metadata.
- `input_before.json`: `INPUT: left, right` then `PREDICT: sum` then `ACT: sum`.
- `input_after.json`: `PREDICT: sum` then `ACT: sum` then `INPUT: left, right`.
- Both branches contain the exact same sourced lines; only their order differs.
  Operands and sums come from the existing deterministic source records, not a
  model. No additional instruction, reminder, answer or example enters prompts.
- The source loader accepts only original native teaching-corpus SHA256
  `2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c`, not control,
  repetition, continuation, candidate-only or evaluation material.
- Recipe metadata fixes original teaching-parent seeds **0/1/2**, LR1e-4,
  rank8/alpha16/dropout.05, all original projections, four epochs, batch4,
  accumulation1, no packing, one supervised EOS and max length512.
  Weight-only initialization means **fresh AdamW**, not optimizer resumption.
- Six planned continuations imply **80 updates/fit; 480 updates total; 1920 row
  presentations; 288 readout calls; 18432 output-cap tokens, not measured usage**.
  No such continuation or readout was performed here.

## Native audit and explicit stop condition

`build_material(rows)` is pure. `audit_native(rows, material, tokenizer)` reuses
`fundamental_repetition_corpus.encode_rows` and the existing V3 native
encoder/collator, packing and epoch-order helpers. It checks:

- Exact original source response, metadata, order and native single-user rendering.
- Actual encoded prefix/response IDs, masked context, response plus one EOS,
  no split, zero dropped tokens, and the stricter512-token bound. The shared
  encoder helper's2048 ceiling is NOT the experiment's allowed length.
- Unchanged native memory IDs/labels/categories; exact paired prefix IDs.
- **Per-row input AND target token-count equality**, not merely aggregate totals
  or equal line inventory. Target IDs necessarily differ under permutation.
- Batch4 padding only as the ordinary masked collation operation; no corpus
  padding, added lines, label search, or compensating training content.
- Matching optimizer-update group order across both branches, four epochs,
  all three seeds. Actual IDs/labels, token totals, hashes and schedules are saved.

`prepare(teach, out, pins, model=...)` requires predeclared source/code/model-file
pins, checks local Qwen configuration and byte bindings before tokenization,
then checks source/code/model bindings again after the audit. Tokenizer loading
uses the existing local-files-only helper; it does not load model weights.

On unequal native row counts, it writes only **`token_mismatch.json`**, including
all row token evidence, line inventories and pins, and raises `TokenMismatch`.
No training corpus is exported. **Report Main before making any material or
recipe decision.** Source/model drift prevents even a misleading stale-custody
mismatch report. There is no fallback or auto-repair.

**Actual Qwen native matching is still untested here.** The successful and
deliberately unequal tokenizers used here are fixtures. Fixture exports are
explicitly `FIXTURE_ONLY_NOT_NATIVE_VALIDATION`; synthetic mismatch tests are
not a finding that the real tokenizer mismatches. Old4517/912 counts are not
reused as augmented-corpus token counts.

Successful native exports contain `input_before.json`, `input_after.json`,
`inventory.json`, `source_records.json`, `panels.json`, `token_audit.json`, and
`manifest.json`. The manifest hashes every companion file, records source/code/
model pins, recipe, limits and planned counts, and states `fits_authorized=false`.
Output must be fresh; existing exports are never overwritten.

## Frozen panel and saved-response scoring

- The original **48dev cases** and requests are preserved exactly:32 arithmetic
  and16 memory paraphrases; temperature0, seed20260912, max64. All other64
  candidate cases remain **unrequested**. The inventory records their IDs and
  content hash without creating requests. Training/dev operands are disjoint
  even under reversal. This remains a repeatedly exposed development panel.
- `score_response(case_id, raw_text)` binds the original source key for one of
  these48 cases and rejects all64 unrequested IDs. Memory uses the unchanged
  `readout.score_memory`; arithmetic delegates to the new pure scorer.
- `score_addition(raw_text, left, right)` preserves raw text and reports joint,
  form-A, form-B, form-B order-only, input-copy correctness, prediction
  correctness, ACT success, field counts, and the unchanged original arithmetic
  score. It does not strip fences, repair output or search for a better action.
- Joint requires exactly three nonblank, case-sensitive numeric lines in
  INPUT→PREDICT→ACT order and a source-correct INPUT pair. Signed decimal integers
  and horizontal whitespace are allowed. Wrong PREDICT or ACT values do not
  invalidate the convention itself; their correctness remains separate.
- Form-A is valid PREDICT before the single ACT, independent of prediction
  accuracy. Form-B requires a faithful INPUT before ACT; its order-only flag
  distinguishes wrong source copies. Form metrics reject unknown/prose lines,
  malformed fields and duplicates. The original two-line parent can pass form-A.
- Missing/non-string responses raise rather than become zeros. An actually
  saved empty string is scored invalid. Malformed or duplicate first-ACT lines
  cannot be rescued by a later valid ACT. These are pure scorers, **not another
  capture/reducer framework**: Main must feed the existing custody-validated,
  complete48 raw responses rather than synthesize absent artifacts.

## Exact completed checks

System `python3 -B -m pytest ...` initially failed because pytest is not installed
in system Python. No dependency was installed; the existing cached interpreter
was used instead. Final commands and results:

```bash
PYTHONDONTWRITEBYTECODE=1 /data/home/rohing/.cache/uv/archive-v0/gQNbv0KfvnaJ_g5l/bin/python -B -m pytest -q -p no:cacheprovider tests/test_fundamental_two_habit_corpus.py
# 65 passed in 1.02s

PYTHONDONTWRITEBYTECODE=1 /data/home/rohing/.cache/uv/archive-v0/gQNbv0KfvnaJ_g5l/bin/python -B -m pytest -q -p no:cacheprovider tests/test_fundamental_two_habit_corpus.py tests/test_fundamental_teaching_corpus.py tests/test_fundamental_repetition_corpus.py tests/test_fundamental_continuation_corpus.py tests/test_fundamental_teaching_readout.py
# 145 passed, 48 subtests passed in 5.53s; no skips reported

PYTHONDONTWRITEBYTECODE=1 python3 -B -m organism_v6.fundamental_two_habit_corpus --help
# Exit 0; only the CPU export entry point is exposed.
```

Fixtures cover exact selection/order/content, line permutations, all48 sourced
scores/all64 rejected extra cases, recipe/counts, untouched memory, EOS/masks/
truncation, three-seed batch schedules, per-row unequal-token rejection,
failure preservation, source/code/model/tokenizer drift, immutable exports and
hashes, strict raw-text grammar, malformed/duplicate-first-action rejection,
and separate prediction/action correctness. These are engineering checks only.

## Main's next CPU preflight — NOT executed here

Supply an approved JSON pins file with exactly these keys:

```text
source_sha256: the fixed original teaching SHA256 above
source_code_sha256: fundamental_two_habit_corpus.source_hashes() on the published snapshot
model_files: rulegame_parenting_diagnostic.model_hashes(LOCAL_QWEN_MODEL), checked against Main's selected original model/tokenizer inventory
```

With Main's existing local tokenizer environment and fresh output directory:

```bash
PYTHONDONTWRITEBYTECODE=1 "$PYTHON" -B -m organism_v6.fundamental_two_habit_corpus \
  --teach "$ORIGINAL_TEACH_JSON" --model "$LOCAL_QWEN_MODEL" \
  --pins "$APPROVED_PINS_JSON" --out "$FRESH_EXPORT_DIR"
```

Local hashes bind bytes, not model origin. The exporter intentionally does not
select or inspect adapter weights. **Main still must bind both branches of each
seed to exactly the same original SEQ098/099 teaching adapter and base**, not
descendants, and verify the actual fresh-optimizer training configuration before
any later launch. CPU/native export success cannot grant launch permission.

This tests compatible authored conventions with rehearsal, not arithmetic
improvement, reliable memory, parenting, child sleep, H1/H2, unrehearsed retention,
or a simultaneous-versus-sequential advantage. No plasticity outcomes were read
or used to change the fixed LR.

## Unchanged shared-file spot checks

The following pre/post hashes match (no Git used):

| Existing file | SHA256 |
|---|---|
| `organism_v6/fundamental_teaching_corpus.py` | `44b1a61e10695e1e65ca3ee2e6c151eba45df1512ea3fc108402e96226ddaa13` |
| `organism_v6/fundamental_teaching_readout.py` | `d6eebc6e70f5a76fcde6c530aeacc273ae5f29a8d9a67ffe5948f04842684bb6` |
| `organism_v6/fundamental_repetition_corpus.py` | `69a969b1f6a9c0592c92a0780fbbbe1a19475db529463a505c0206416f95c5f1` |
| `organism_v6/train_adapter_v3.py` | `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7` |

**EDIT-STOP.** Main may take over the two implementation files and this receipt.
