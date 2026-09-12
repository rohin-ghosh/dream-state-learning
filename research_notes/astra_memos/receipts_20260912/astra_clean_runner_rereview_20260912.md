# Clean nursery repair re-review — 2026-09-12

Read-only, bounded review of the nursery runner and its tests. Only this report
was written; no repository source/test edits, network, GPU work or commits.
Advisory findings, not launch-pause authority. Configured-input checks are not
GPU attestation. No expansion into official pins, adult CLI, resume or probes.

## Result

Both original substitutions reject at the requested boundary. **R1 is now
REPAIRED, independently verified on 2026-09-12.** The erroneous requirement for
`deterministic_algorithms=True` was replaced by a strict boolean-type check;
the seed-only False value is accepted. This repairs the consumer expectation,
not the training recipe. The original findings and evidence below are retained
as history; the verification addendum records the final R1 status.

## Original F1: repaired

`organism_v6/run_life_v2.py:51` compares reported model path, adapter path and
adapter-file hashes to configured inputs. The waking path calls it at line 698
before returning the backend; candidate evaluation calls it at line 1209 before
the canary.

I independently reapplied the original `/tmp/other-unpinned-base` substitution
to `NurseryModelFixture.generation_identity` and ran the admitted fixture:

```text
ValueError: clean backend identity mismatch: model_input
life ledger absent or empty
LIFE_DONE absent
```

The 13-test suite also verifies independently wrong adapter paths and candidate
hash inventories. The latter fails before raw final DONE or descendant lineage.

## Original F2: repaired

`validate_clean_training` at `run_life_v2.py:60` checks the requested training
controls; the call at line 1197 occurs after trainer success and before
`promote_trained_adapter`.

I reapplied the original consistently receipted substitution: config r=16 and
native metadata rank=16, seed=99, lr=0.009 against rank8/seed12/LR0.0001:

```text
ValueError: clean training config mismatch: r
sleep_0064/adapter.train/DONE preserved
sleep_0064/adapter absent
lineage/sleep_0064 absent
```

This closes that request/result mismatch without discarding the evidence.

## R1 — REPAIRED (historical P1): seeded does not imply deterministic algorithms enabled

Locations:
- `organism_v6/run_life_v2.py:65`: expected metadata hardcodes
  `deterministic_algorithms=True`.
- `organism_v6/train_adapter.py:19`: `seed_training` calls `random.seed` and
  `torch.manual_seed`, not `torch.use_deterministic_algorithms`.
- `organism_v6/train_adapter.py:253`: native metadata records the actual
  `torch.are_deterministic_algorithms_enabled()` value.
- `tests/test_clean_nursery_runner.py:199`: simulated trainer hardcodes True.

The current trainer does not enable the condition newly required by the runner.
The subprocess's seed controls initialize RNGs; they do not establish that
deterministic algorithms are enabled. No clean CLI argument enables that mode.

Two CPU confirmations:

1. Ran the existing actual-trainer-main CPU-double test
   `ChildReceiptIntegrationTests.test_reasoning_wrapper_main_keeps_child_only_recipe_and_seed`.
   It executes real trainer main with stubbed ML modules, not a GPU. Its
   seeded native output is:

   ```text
   seed=23
   recipe=v1_frozen_child_target_seeded
   deterministic_algorithms=false
   trainer DONE=true
   ```

2. Ran the nursery's admitted 64-record fixture, replacing only the completed
   metadata's deterministic flag with False before the real receipt writer
   hashes it. All requested seed/rank/LR/config fields remain correct:

   ```text
   ValueError: clean training metadata mismatch: deterministic_algorithms
   trainer DONE=true
   candidate=false
   descendant lineage=false
   ```

Thus an ordinary seed-only fit can complete and then terminate the nursery
before promotion. The nursery's 13 green tests do not cover this actual
producer/consumer contract mismatch.

Smallest correction preserving the existing training recipe: remove the
hardcoded True expectation, require the recorded field to be a boolean, and
retain its actual value as evidence. Preserve the exact seed/rank/LR/epochs,
recipe, alpha/dropout/bias/modules checks. Make the nursery fake trainer report
the seed-only False setting and add a success regression for it while retaining
the two rejection cases. Do not silently enable deterministic algorithms just
to satisfy this test; that would change the training recipe rather than repair
the consumer expectation. An explicitly selected deterministic-algorithms
policy, if later desired, is separate work.

## Historical R1 reproduction before repair (no longer expected to reject)

Run at repository root with `PYTHONDONTWRITEBYTECODE=1 python3 -B -`:

```python
import json
import runpy
from pathlib import Path
from unittest.mock import patch

ns = runpy.run_path('tests/test_clean_nursery_runner.py', run_name='rereview')
case = ns['CleanNurseryRunnerTests'](
    'test_admitted_fixture_binds_before_reloading_lineage_adapter')
trainer = ns['train_adapter']
original = trainer.write_training_receipt

def seed_only_metadata(receipt_path, adapter_dir, *args, **kwargs):
    path = Path(adapter_dir) / 'train_meta.json'
    metadata = json.loads(path.read_text())
    metadata['deterministic_algorithms'] = False
    path.write_text(json.dumps(metadata))
    return original(receipt_path, adapter_dir, *args, **kwargs)

case.setUp()
try:
    with patch.object(trainer, 'write_training_receipt', seed_only_metadata):
        try:
            case.run_admitted_fixture()
        except ValueError as error:
            print(error)
        else:
            raise AssertionError('rejection no longer reproduces; inspect repair')
    assert (case.life / 'sleep_0064/adapter.train/DONE').is_file()
    assert not (case.life / 'sleep_0064/adapter').exists()
finally:
    case.doCleanups()
```

## Validation and scope limits

- Current nursery suite: 13/13 passed, using stdlib unittest through runpy.
- Original F1 and F2 independently rerun: both rejected as above.
- Additional focused actual trainer-main CPU-double case passed and emitted False.
- No actual Torch installation or GPU execution was used; the metadata behavior
  is supported by the inspected real trainer code and its existing CPU doubles.
- No other concrete repair regression was established in this bounded pass.
  The new checks are guarded by clean nursery mode; no all-flags-off behavior
  changes were found in those call sites. No broad suite certification claimed.
- Main's freeze/log and W0 planning are outside this report.

## Reviewed hashes

```text
organism_v6/run_life_v2.py
c11e8e9ec7876582f10b47d52b68822c2fec7628a757424eb3c4baf377bd3316
tests/test_clean_nursery_runner.py
3a74a4e89e1452e2d970568c29c6bfc815d2509ceb4eef9d13aece8188b7d29d
organism_v6/train_adapter.py
9e39b6b6816f00ce2a78476f16e784daf31d7b26c673cbcddaf6ab508cf09caf
```

## R1 repair verification addendum — 2026-09-12

Status: **REPAIRED.** Verification was limited to this repair. No source/test
edits, network, GPU work, commits or additional review scope.

Inspected changes:
- `validate_clean_training` no longer expects True. It requires
  `type(metadata.get("deterministic_algorithms")) is bool`.
- Nursery simulated training and the standalone control fixture now emit False.
- The trainer's seed-only implementation is unchanged, including its file hash.
  There is no new deterministic-algorithms setting and no training-recipe change.
- The other requested-control checks remain in place.

Independent verification through stdlib unittest/runpy: **3 focused tests passed**:
1. `test_admitted_fixture_binds_before_reloading_lineage_adapter` — the False
   metadata now completes the admitted lifecycle, receipt, snapshot and reload.
2. `test_training_metadata_and_recipe_fields_are_independently_checked` — missing
   expected fields still reject, including the determinism field.
3. `test_reasoning_wrapper_main_keeps_child_only_recipe_and_seed` — actual trainer
   main with CPU doubles preserves the seeded child-only recipe.

Additional direct checks against the validator: both False and True accepted;
None, integer 0, integer 1, string, list and dict rejected with the determinism
metadata mismatch error. All temporary fixtures cleaned up.

Main reports 42 combined runner/actual-trainer CPU tests passed; I did not rerun
that broader set. F1/F2 remain recorded as repaired from the preceding review;
this addendum does not reopen them. Main's merge/preservation work and the
independent NOTE repair remain outside scope.

Verified repair hashes:

```text
organism_v6/run_life_v2.py
1f41f5899f6ad6fbe4230e0e1dd32c5eef3b639d91fe8b108ed87bcbe1cbbe89
tests/test_clean_nursery_runner.py
a36b06065646c739bef38ba5cd530a22de5c200b4c4d91a43d08f04c7b8ff940
organism_v6/train_adapter.py (unchanged)
9e39b6b6816f00ce2a78476f16e784daf31d7b26c673cbcddaf6ab508cf09caf
```
