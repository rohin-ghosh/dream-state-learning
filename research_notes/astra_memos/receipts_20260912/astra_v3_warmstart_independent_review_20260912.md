# Independent V3 optional weight warm-start review

Date: 2026-09-12, completed approximately 18:20 UTC.

## Verdict

**PASS — bounded static code review; no required corrections found.** This is advisory parallel review, not a launch veto or a claim that native integration tests passed. Main retains native CPU validation, experiment selection, source publication, and launch ownership.

Reviewed only the optional warm-start change in `organism_v6/train_adapter_v3.py` and its tests in `tests/test_train_adapter_v3.py`, against `/tmp/astra_v3_warmstart_handoff_20260912.md`. No Git, network, GPU/model calls, test execution, repository edits, numerical-capsule review, or SEQ099 review was performed. The only file written is this report.

## Evidence-bound findings

### 1. PASS: default configuration and original behavior preserved

- Independently compared Python ASTs against the corresponding files read directly from `/tmp/astra_fundamental_source_06c90d1b.tgz`, without extracting or executing them. `TrainConfig` and `config_from_args` are identical; all nine original test functions are identical. This is a comparison to the named local archive, not an independent authentication of its historical commit label.
- `organism_v6/train_adapter_v3.py:657` appends `init_adapter=None` after the existing arguments. The no-init branch at line 660 delegates with the original arguments. The original training loop, optimizer selection, and default save branch remain; new checks/receipt fields are warm-only. The fresh default still allows existing output directories and retains its original empty-corpus behavior.
- `organism_v6/train_adapter_v3.py:915` adds the CLI option outside `TrainConfig`; `organism_v6/train_adapter_v3.py:943` retains default CLI behavior and adds local-only tokenizer/base loading only when warm-start is requested. `tests/test_train_adapter_v3.py:431` tests config/delegation identity.
- Smallest required fix: none.

### 2. PASS: parent is read-only and child ownership is explicit

- `organism_v6/train_adapter_v3.py:501` inventories all parent files by SHA256 and rejects symlinks/special entries. `organism_v6/train_adapter_v3.py:524` requires a fresh, resolved child path disjoint from parent and local base, rejects aliased paths, and checks completion/configuration/one weight artifact.
- `organism_v6/train_adapter_v3.py:665` actually passes the resolved child path into training. Child creation at line 681 is exclusive for warm starts; ownership is recorded only after successful creation. Parent bytes are never saved over.
- Parent inventories are compared after loading (`organism_v6/train_adapter_v3.py:644`), before/after child save (`organism_v6/train_adapter_v3.py:846`), and on function exit including failure (`organism_v6/train_adapter_v3.py:666`). Failure removes DONE only for an owned child. This detects observed parent mutation; it does not claim an external-writer lock or authenticated origin.
- `tests/test_train_adapter_v3.py:456`, `tests/test_train_adapter_v3.py:477`, and `tests/test_train_adapter_v3.py:494` cover incomplete/aliased/overlapping artifacts, parent mutation, and another writer winning output creation.
- Smallest required fix: none.

### 3. PASS: complete matching weights are loaded, not silently freshly initialized

- `organism_v6/train_adapter_v3.py:599` compares the saved native LoRA configuration to the intended configuration, including structural defaults; unknown structural fields and incompatible rank/alpha/targets/bias/advanced modes fail closed. Parent recipe and actual loaded base identity/layer-count checks supplement this (`organism_v6/train_adapter_v3.py:547`, `organism_v6/train_adapter_v3.py:619`).
- `organism_v6/train_adapter_v3.py:617` rejects prewrapped/adapted inputs. One adapter is injected at line 633, then the saved state is loaded through the native state setter at line 638. There is no load-error fallback to fresh weights.
- Exact nonempty source/destination key equality, A/B-only keys, shapes, floating type and finiteness are required (`organism_v6/train_adapter_v3.py:564`, `organism_v6/train_adapter_v3.py:578`). The post-load full state must equal the explicitly converted full source inventory before training. Ignoring the setter's return object does not hide a missing load here: the actual entire loaded state is independently compared.
- Native tests at `tests/test_train_adapter_v3.py:605`, `tests/test_train_adapter_v3.py:643`, and `tests/test_train_adapter_v3.py:703` inspect pre-update loaded tensors, zero-update/follow-on checkpoints, and malformed/partial/extra/nonfinite/corrupt weights. These are implemented tests, not passes observed by this reviewer.
- Smallest required fix: none.

### 4. PASS: frozen base, one adapter, truthful precision scope

- `organism_v6/train_adapter_v3.py:587` requires exactly the active default adapter, every LoRA A/B parameter trainable, and every other parameter frozen; trainable/state coverage is checked at line 643. The optimizer receives only trainable parameters, and trainability is checked again before saving.
- `organism_v6/train_adapter_v3.py:636` computes explicit source-to-destination dtype conversions, rejects nonfinite converted values, and compares hashes of shape/dtype/raw bytes against the actual loaded state. The receipt at line 645 correctly qualifies equality as after conversion and records actual conversions. It does not falsely promise preservation of source precision.
- `tests/test_train_adapter_v3.py:531` exercises tensor validation/inventories and a BF16 source inventory; `tests/test_train_adapter_v3.py:554` exercises trainability. The native warm tests use an FP32 tiny model, so they should not be described as an executed native mixed-precision conversion test. Static conversion/load verification is present in the implementation.
- Frozen parameters are also compared with their pre-run values in the native zero-update and finite-update tests. Code checks frozen trainability; full base-byte provenance remains externally supplied, not established by a model name.
- Smallest required fix: none.

### 5. PASS: optimizer reset and scientific scope are explicit

- `organism_v6/train_adapter_v3.py:787` always creates a fresh SGD/AdamW optimizer from current parameters. Warm receipts require empty initial optimizer state, record class/defaults/current phase seed, and explicitly state that optimizer state is neither restored nor saved (`organism_v6/train_adapter_v3.py:645`, `organism_v6/train_adapter_v3.py:794`). There is no optimizer/RNG/data-cursor resume path.
- Phase/cumulative steps are distinguished at `organism_v6/train_adapter_v3.py:850`. Zero epochs on target-bearing input can produce a zero-update child; empty/no-target warm writes fail at line 726. `max_steps=0` retains the original uncapped meaning.
- The change is an optional weight-loading seam. It does not implement a continuation schedule, adapter merge/nesting, evaluation or benchmark change, parenting, child sleep, or a new learning/generalization endpoint. Treating it as weight-only warm start rather than true training resume matches the code and handoff.
- Smallest required fix: none.

## Validation boundary

Main's native CPU run of all 21 tests without skips is outstanding from this review's perspective. I did not run the suite or duplicate Main's work. The handoff explicitly reports the VM's 14 fully exercised functions, one partly exercised function, six wholly skipped functions, and seven skip notices; that is not 21 native passes. Native PEFT/Transformers loading and saving remain runtime validation obligations, not inferred from AST inspection.

Parent inventories bind the supplied checkpoint bytes. Compatibility checks bind identity strings, layer count, and adapter structure, not authenticated base provenance or official origin. Main's external base/model/source custody pins remain necessary for those separate claims. No new architecture/hypothesis closure is established by this PASS.

## Reviewed-byte bindings (SHA256)

- `organism_v6/train_adapter_v3.py`: `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`
- `tests/test_train_adapter_v3.py`: `9b50c013ea64f9899b1295bcdfe707b4ab59c310f464e975ba377445b86bd534`
- `/tmp/astra_v3_warmstart_handoff_20260912.md`: `f1ee7f2db1f435ffddf728f2683c2ea76dd6041266c6dd0fffde7e0ef894f178`

This verdict applies to those bytes. No required minimal correction was identified within the assigned scope.
