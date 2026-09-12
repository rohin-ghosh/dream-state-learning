# Parent material writer preparation — 2026-09-12

Completed initially approximately 08:49 UTC; relocation compatibility repair frozen at approximately 08:52 UTC. Owned NEW files only:

- `organism_v6/parent_material_write.py`
- `tests/test_parent_material_write.py`

No existing source/test edits, Git, network/remote activity, GPU/model execution, training, or changes to calibration. No new general guard, clean gate, lineage certificate, or eligibility manifest.

## Ready API / command

```python
from organism_v6.parent_material_write import prepare_write

report = prepare_write(
    formation_out, preparation_out,
    adapter_dir=future_adapter_out,
    trainer_log=external_future_trainer_log,
    python_executable=existing_python,
)
```

CLI, CPU/tokenizer preparation only:

```bash
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  "$PY" -B -m organism_v6.parent_material_write \
  --formation-out "$FORMATION_OUT" --out "$PREPARATION_OUT" \
  --adapter-out "$FUTURE_ADAPTER_OUT" --trainer-log "$EXTERNAL_TRAINER_LOG" \
  --python "$PY"
```

All three destinations must be fresh, nonsymlink paths with existing parents. The prep directory, future adapter directory and trainer log must be disjoint from one another and from the formation/model inputs. No adapter directory or trainer log is created. There is no execute flag or subprocess execution.

## Formation handoff / API coordination

Imports and calls James's actual `parent_material_diagnostic.summarize(out)`, requiring exact equality with `results.json` reconstructed as `status="COMPLETE", mode=config.mode, **summarize(out)`.

Required completed formation files are config, local pins, base-after check, results, schedule, ledger, lesson deliveries, generations, teaching dose and the diagnostic's `artifact_hashes.json`. Every recorded artifact hash is checked; failed/incomplete/extra artifacts reject. The fixed schedule, recorded protocol, original source hashes, config/model path, local inventory and before/after pins must agree. Model hashes remain explicitly local identity, not authentication.

James's module changed while this task ran: it added actual NOTE-output matching/hash checks and then the clock-neutral `DiagnosticDriver`. The public judgment API remained stable (`record_line`, `source_line`, `execution_id`, `unique_grounded`). The helper calls the updated implementation directly; no source-join implementation was copied. Tested current diagnostic SHA256:

```text
bbda9f086f3070cee5f708ad71772a99a7a65715dfb08ff32d97927d7f5b2d5d
```

Further byte changes to the formation module/policy/recorded sources after real formation intentionally fail preparation's source comparison. Main should freeze those producer bytes for material being consumed, not refresh their recorded hashes after the fact. Identical source bytes relocated to a later checkout are supported by the repair below. This is a handoff note, not a request for additional formal guard work.

### Deployment relocation repair

Removed the invalid requirement that producer absolute-path dictionaries equal the executing checkout's absolute-path dictionaries. `_producer_sources` now:

1. Reads and hashes every ORIGINAL recorded producer path; missing/changed original files reject, even if the executing checkout has matching replacements.
2. Separately verifies the executing producer paths against their actual hashes.
3. Maps both inventories uniquely to this explicit repo-relative set: `organism_v6/parent_material_diagnostic.py`, `organism_v6/preschool_reasoning.py`, `organism_v6/batch_loop.py`, `organism_v6/reasoning_gym_families.json`.
4. Requires exact byte-hash equality for every corresponding dependency. Unknown, missing, duplicate/ambiguous or noncanonical source identities reject. No basename-only comparison or allowed byte drift.
5. Preserves the original `source_hashes` unchanged and records original paths, executing paths and the relative-name/hash correspondence under `formation_inputs.json:producer_sources`, covered by the prep artifact hash inventory.

The exact relocation regression creates a synthetic old producer checkout named `astra_sources/911e08877bac83613a62ca58bdb032f22cc61681`, records its real identical copied source paths when generating the formation fixture, then prepares using the current checkout. It verifies READY and both path inventories, and confirms every original formation artifact remains byte-identical. No old frozen checkout or real formation artifact was edited/resealed. Additional regressions reject changed original bytes, missing original sources, changed executing bytes even with an updated executing hash, duplicate identities, and incomplete/unknown dependencies.

## Fixed extraction and tokenizer behavior

- Sort genuinely `unique_grounded=True` judgments by physical ledger position; choose **first 64**, no ranking, replacement or lower-count fallback.
- Fewer than 64 publishes `SKIPPED_INSUFFICIENT_MATERIAL`, selected count zero, no corpus/command and no tokenizer load. Skip directories cannot be reused.
- Exact corpus recipe is `preschool_records_v1`, with `principles=[]`, `n_new=64`, `n_dropped_legacy=0`. Every item is the existing `Situation {eid}.\nMy measured action record: {unchanged child text}`. It must reference an actual earlier ACT and a training-schedule episode. Source map records zero-based physical row indexes and hashes of the LF-inclusive ACT/NOTE_AFTER rows, child text and corpus item.
- Loads the actual local tokenizer with `AutoTokenizer.from_pretrained(model_path, local_files_only=True)`. Uses trainer-sized batches of four, the same pad-token fallback, attention masks, offsets, `child_record_prefix_length`, `child_target_mask`, and `child_label_counts`.
- Uses **no truncation**. Any selected row exceeding 512 tokens or lacking valid causal-shift child/prefix masking rejects preparation; it does not select a later shorter record.
- Emits per-row and aggregate input/child supervision counts. Equal examples and steps are asserted; exact child-token-budget equivalence is explicitly NOT asserted.

## Output artifacts

Successful READY prep contains:

```text
formation_inputs.json
local_base_pins.json
source_hashes.json
source_map.json
corpus.json
tokenizer_preflight.json
training_command.json
write_prep.json
artifact_hashes.json
```

Files are exclusively written and chmod 0444; final directory is 0555. The independent artifact hash inventory covers the corpus, source map, pins, command, checks and other prep files. These are ordinary immutable-by-convention local artifacts, not adversarial filesystem immutability or an ancestry certificate.

`training_command.json` contains a shell-free argv, trusted checkout cwd, local-model/offline env overlay, external stdout path, stderr=STDOUT and exclusive log open mode. It specifies existing `train_adapter` with **rank 8, epochs 3, LR 1e-4, seed 6102**. All four optional clean gate/lineage/trainer-receipt arguments are omitted. Expected 64 examples × batch size 4 × 3 epochs = **48 steps**. It does not select/reserve a GPU or execute anything.

Before any later execution, main still checks that adapter/log paths are fresh and input/prep hashes match, then uses its already-owned reservation. Do not reuse the log/adapter path on failure or replace the fixed first64 set after observing a result.

## Returned post-training checks

`write_prep.json` and the returned report provide `metadata_equals`: expected seeded child-only recipe, corpus hash, source recipe, loss target, 64 texts, 48 steps, rank/epochs/LR/seed, actual-tokenizer-derived total tokens, supervised tokens and masked nonpadding tokens across three epochs.

Also require actual DONE, no EMPTY_CORPUS, finite final loss, matching train_meta values, and capture actual adapter config/weight hashes. The standalone trainer does **not** emit a bound trainer receipt; the report explicitly says so. DONE is not an admission, efficacy, clean-origin or lineage result.

## Tests / results

Final focused command:

```text
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' PYTHONPATH=tests:. python3 -B -m unittest test_parent_material_write -v
25 tests passed in 12.685s
/tmp/astra_parent_material_write_tests.log
```

Final focused+trainer-mask command:

```text
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' PYTHONPATH=tests:. python3 -B -m unittest test_parent_material_write test_child_receipt_integration.ChildReceiptIntegrationTests.test_both_exact_wrappers_mask_prefix_crossing_and_padding test_child_receipt_integration.ChildReceiptIntegrationTests.test_actual_transferred_mask_must_agree_with_cpu_preflight -v
27 tests passed in 12.921s
/tmp/astra_parent_material_write_combined.log
```

Coverage: actual formation/source join and exact export; first64 determinism; 63-count skip; teacher-example exclusion; result/source/generation tampering; local model/source/schedule drift; failed formation; recipe mismatch; missing child labels; >512-token rejection without replacement; output/log conflicts; immutable outputs/reuse refusal; shell-free argv with clean arguments absent; child-token accounting; offline-only tokenizer loader.

Tests use actual formation run/summarize and policy joins with synthetic local weights, an offset-tokenizer CPU double, and a one-tick diagnostic-driver fixture to keep tests small. They are not GPU or real tokenizer-vocabulary measurements. The production default does load the actual tokenizer. Initial tests timed out at 120 seconds while the evolving producer used full 16-tick fixtures, and a fixture double quoted already-JSON-quoted actions, correctly causing source-judge rejection. Those fixture issues were corrected (JSON decode of action and explicit short CPU driver); production source validation was not relaxed. An existing unrelated unclosed-bootstrap ResourceWarning remains untouched.

## Frozen source hashes

```text
57025d725e0825deaa795ee334864fa36bb6c5ed3a3ba17cc51931dc2d9d197a  organism_v6/parent_material_write.py
25abb9db3167fc5f40f1e4044f5681d16dec240d9dc1f5cd21bdc80ea261e377  tests/test_parent_material_write.py
```

Ready for main's real formation handoff. No actual formation result was consumed or training launched by this worker; tests only. Source/tests frozen pending main review.
