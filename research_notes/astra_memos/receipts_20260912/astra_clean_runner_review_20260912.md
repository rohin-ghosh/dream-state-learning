# Clean nursery runner: bounded read-only integration review

Date: 2026-09-12. Advisory review; no launch-pause authority.

## Scope and result

Read the actual working changes in `organism_v6/run_life_v2.py`, `ledger.py`,
`clone_coordinator.py`, `batch_loop.py`, and `reasoning_gym_gym.py`, plus their
direct lineage, generation, gate and trainer dependencies and current nursery
tests. No repository source/test edits, network access, GPU work or commits.
This file is the sole review deliverable. Temporary CPU fixtures were cleaned.

The current eight `test_clean_nursery_runner` tests passed, including main's
64-record semantic admission -> simulated trainer -> final DONE -> lineage
snapshot -> pinned-adapter reload test. Main separately reports 175 combined
tests passed at 07:19 UTC; I did not rerun that broader collection.

Two narrow fail-closed binding gaps remain. These are controlled producer-drift
reproductions, NOT claims that the normal backend currently loads the wrong
model or the normal trainer uses the wrong seed. They do not ask for stronger
external authentication or revisit the acknowledged fabricated-eligibility
limitation. The evidence already supplied by the producer contradicts the
runner's intended inputs, and the runner currently accepts that contradiction.

## F1 — P1: reported waking loader identity is not checked against the clean checkpoint

Locations: `organism_v6/run_life_v2.py:655` (`load_model`),
`organism_v6/preschool_reasoning.py:434` (`_identity_status`), and its generation
and admission checks. `prepare_clean_nursery` correctly sets both `V6_MODEL`
and the already-imported backend's `MODEL`; this is not an import-order bug.

`load_model` verifies the declared manifest and chooses its adapter, but returns
the constructed backend without comparing its `generation_identity()` to those
verified inputs. The record gate validates the identity's shape and internal
hash, not its agreement with this runner's clean base/checkpoint.

Reproduction: use main's real 64-record admission/snapshot fixture unchanged
except that the fake backend honestly reports
`model_input='/tmp/other-unpinned-base'` from `generation_identity()`. The runner
admits all 64 records, writes `lineage/sleep_0064/manifest.json`, reloads the
lineage adapter, and writes `LIFE_DONE`. The mismatching path is preserved in
the admitted notes' generation evidence; it is not hidden or falsely relabelled.

Observed output:

```text
recorded_model=/tmp/other-unpinned-base
admitted=64
clean_manifest=true
life_done=true
```

Smallest correction: in the clean-only `load_model` branch, inspect the backend
identity immediately after construction and before returning it. Require its
model input to equal the pinned checkpoint model directory, its adapter input
to equal the adapter actually selected (None at birth), and its adapter hash
inventory to match the selected checkpoint bindings. Fail on mismatch before
waking work or admission. Use the existing identity and lineage APIs; do not
add a new attestation architecture. Apply the same expected-input comparison
to clean candidate evaluation if that backend is also covered by the wrapper.
Do not compare all historical rows to the latest adapter: earlier records
legitimately came from earlier checkpoints.

## F2 — P2: completed training configuration can contradict requested controls

Locations: `organism_v6/run_life_v2.py:1137` (trainer command), the subprocess
success -> `promote_trained_adapter` path, and `run_life_v2.py:1189` (lineage
snapshot). Supporting dependency: `life_lineage._adapter_inputs` and
`_trainer_evidence` validate source/mask/hash evidence, not this runner's
requested rank, optimizer seed and learning rate.

Reproduction: retain main's simulated training test, including a real bound
trainer receipt, but change the completed config to `r=16` and native metadata
to `rank=16, seed=99, lr=0.009` BEFORE generating that receipt. The startup
requests rank 8, seed 12 and LR 0.0001. All evidence hashes remain honest and
consistent with the wrong completed configuration. The runner still writes a
clean descendant, reloads it and reaches `LIFE_DONE`.

Observed output:

```text
requested: rank=8, train_seed=12, base_lr=0.0001
completed: rank=16, seed=99, lr=0.009
clean_manifest=true
life_done=true
```

Smallest correction: after a successful clean trainer subprocess and before
staging-to-candidate promotion/evaluation, compare the actual adapter config
rank and native train metadata rank/seed/LR to `args.rank`, `args.train_seed`
and the effective `lr_`. Missing or contradictory fields must fail, leaving
the original outputs intact. Preserve the existing receipt/mask/source checks;
these comparisons supplement them. Add the realistic requested fields to the
CPU simulated trainer fixture rather than relaxing the comparison. This is
local request/result validation, not an external metadata-authentication task.

## Resolved during this review — ignored clean --base-lr

An earlier snapshot accepted `--base-lr 0.0009` but only forwarded `--lr` when
plasticity was enabled, which clean nursery forbids. Main concurrently changed
the condition to `args.plasticity or clean_nursery` and added finite-positive
validation. I reran the same 64-record fixture with command capture and observed
`--lr=0.0009`. This is resolved, not an outstanding finding. Legacy default-path
LR behavior was not altered by the clean-only addition.

## Reproduction recipe for F1/F2

From the repository root, run the following with
`PYTHONDONTWRITEBYTECODE=1 python3 -B -`. It uses the existing CPU test fixtures,
real semantic gate and real receipt/snapshot helpers; the backend, optimizer
work, probes and canary are the test's explicit simulations. No source files
are changed. These were run as two separate executions during review; the
combined recipe below expresses the same substitutions.

```python
import json
import runpy
from unittest.mock import patch

ns = runpy.run_path('tests/test_clean_nursery_runner.py', run_name='review')
Case = ns['CleanNurseryRunnerTests']
Fixture = ns['NurseryModelFixture']
trainer = ns['train_adapter']
method = 'test_admitted_fixture_binds_before_reloading_lineage_adapter'

original_identity = Fixture.generation_identity
def mismatched_identity(self):
    identity = original_identity(self)
    identity['model_input'] = '/tmp/other-unpinned-base'
    return identity

case = Case(method)
case.setUp()
try:
    with patch.object(Fixture, 'generation_identity', mismatched_identity):
        getattr(case, method)()
    rows = [json.loads(line) for line in
            (case.life / 'ledger.jsonl').read_text().splitlines()]
    note = next(row for row in rows if row['kind'] == 'note_after')
    print('F1', note['generation']['backend_identity']['model_input'],
          (case.life / 'lineage/sleep_0064/manifest.json').is_file())
finally:
    case.doCleanups()

original_receipt = trainer.write_training_receipt
def mismatched_training(receipt_path, adapter_dir, *args, **kwargs):
    path = adapter_dir / 'adapter_config.json'
    config = json.loads(path.read_text())
    config['r'] = 16
    path.write_text(json.dumps(config))
    path = adapter_dir / 'train_meta.json'
    metadata = json.loads(path.read_text())
    metadata.update(rank=16, seed=99, lr=0.009)
    path.write_text(json.dumps(metadata))
    return original_receipt(receipt_path, adapter_dir, *args, **kwargs)

case = Case(method)
case.setUp()
try:
    with patch.object(trainer, 'write_training_receipt', mismatched_training):
        getattr(case, method)()
    path = case.life / 'lineage/sleep_0064/adapter/train_meta.json'
    metadata = json.loads(path.read_text())
    print('F2', {name: metadata[name] for name in ('rank', 'seed', 'lr')},
          (case.life / 'LIFE_DONE').is_file())
finally:
    case.doCleanups()
```

## Checks that did not produce an additional finding

- Initial actual model files are checked/copied by `prepare_birth`; pinned base
  path reaches both ordinary backend construction and trainer environment.
- The normal fixture sequence makes a raw CANDIDATE, evaluates it, writes final
  DONE, records lineage, then mounts the copied lineage adapter. A failed
  snapshot raises before that reload; fresh-only startup rejects implicit resume.
- Clean context bypasses waking/parent brief reads. Static lesson treatment is
  explicitly allowed in nursery and logged as teacher influence; the current
  tests verify it does not enter admitted loss text.
- ProvenanceLedger now returns its augmented stored action to the post-outcome
  slot, eliminating the raw-vs-stored ACT mismatch. The ledger JSON write itself
  is unchanged. Strict verifier exceptions/nonfinite/out-of-range outcomes fail
  closed only in clean mode; its legacy behavior test passes.
- No additional concrete all-flags-off default-path regression was established
  in this bounded review. This is not a full regression-suite certification.

No neutral-probe, resume, adult-CLI, mechanism-success or real-clean-launch claim.
No new official-pin/metadata work requested. H1/H2 unchanged.

## Reviewed final working snapshot

Source is changing concurrently; locations refer to the final inspected bytes.

```text
run_life_v2.py            4b67a9d4178c7d937c9c56e3ec3b7acb67729f7b8b122303447b4d1d5653b2f9
ledger.py                 e99b606ea6ec81759189f7e70f343e15d95e4d516675fe61c6273b7f4a0e12c1
clone_coordinator.py      468eff236192efe3ae4c1bce1772d8c742bb110dc4938f2535ce88acd92db8ce
batch_loop.py             821471f4ddd136f64c7151a5fa0a4b1c2cc0d5be00c9febb73d5b215dccb7605
reasoning_gym_gym.py      da9879537d33923c9702b1a5b3d63d6a2fcb396a64e110a886bd445c33e1c084
test_clean_nursery_runner.py 61554a2def97cdfa8524440787a9e37c37141b2925879f8233cdb4f4c3080476
life_lineage.py           916276f3572e45e1f8e187c7a8aa1cb6ced3fde04e98b09c32665237b0168c5f
train_adapter.py          9e39b6b6816f00ce2a78476f16e784daf31d7b26c673cbcddaf6ab508cf09caf
```
