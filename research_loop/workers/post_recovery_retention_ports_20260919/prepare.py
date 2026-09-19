"""Materialize hash-verified inventory preimages in this sidecar only."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROLLOUT = HERE.parent / 'post_recovery_retention_rollout_20260919'
PHASE2 = HERE.parent / 'post_recovery_pair_evidence_20260918/phase2'
VARIANTS = dict(C0='node2', Astra7='node2', P7='node4', P3='node4', C2='node5')
FILES = ('gpu/orch_r184_think_act_learn.py', 'organism_v6/orch_r124_train_history.py',
    'organism_v6/orch_r125_continual_stream.py')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_once(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('immutable_preparation_conflict: ' + str(path))
        return
    with path.open('xb') as stream:
        stream.write(raw)


def main():
    inventory_receipts, variants = {}, {}
    for life, node in VARIANTS.items():
        inventory_path = ROLLOUT / (node + '_INVENTORY2.json')
        inventory_raw = inventory_path.read_bytes()
        inventory = json.loads(inventory_raw)
        matches = [row for row in inventory['results'] if row['life'] == life]
        if len(matches) != 1:
            raise ValueError('one_exact_variant_inventory')
        row = matches[0]
        if set(row['files']) != set(FILES) or len(row['source_pins']) != row['source_files']:
            raise ValueError('exact_three_files_and_full_source_pins')
        before = {}
        for relative in FILES:
            entry = row['files'][relative]
            raw = entry['text'].encode()
            if sha(raw) != entry['sha256'] or row['source_pins'][relative] != entry['sha256']:
                raise ValueError('preimage_and_full_source_pin_must_match')
            write_once(HERE / life / 'preimage' / relative, raw)
            destination = HERE / life / 'fork' / relative
            if not destination.exists():
                write_once(destination, raw)
            before[relative] = entry['sha256']
        write_once(HERE / life / 'SOURCE_PINS.before.json',
            (json.dumps(row['source_pins'], indent=2, sort_keys=True) + '\n').encode())
        for name in ('test_retention.py', 'run_checks.py'):
            write_once(HERE / life / name, (PHASE2 / name).read_bytes())
        variants[life] = dict(node=node, inventory_file=inventory_path.name,
            observed_unix=row['observed_unix'], source_root=row['native']['cwd'],
            guard_path=row['guard_path'], guard_sha256=row['guard_sha256'],
            journal_id=row['journal_id'], source_files=row['source_files'], before=before)
        inventory_receipts[inventory_path.name] = sha(inventory_raw)
    receipt = dict(scope='local-only exact retention ports; no source staging or adoption',
        inventory_sha256=inventory_receipts, variants=variants,
        phase2_sha256={name: sha((PHASE2 / name).read_bytes()) for name in
            ('REPAIR.patch', 'test_retention.py', 'run_checks.py')},
        native_signals=[], live_writes=[], dispatches=[], parent_deliveries=[])
    write_once(HERE / 'INPUT_RECEIPT.json', (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode())
    legacy_tests = {}
    for name in ('test_orch_r125_continual_stream.py', 'test_orch_r124_train_history.py'):
        raw = (HERE.parents[2] / 'tests' / name).read_bytes()
        write_once(HERE / 'legacy_tests' / name, raw)
        legacy_tests[name] = sha(raw)
    write_once(HERE / 'TEST_INPUTS.json', (json.dumps(legacy_tests, indent=2, sort_keys=True) + '\n').encode())
    dependency = 'organism_v6/orch_r125_plain_context.py'
    origin = HERE.parent / 'rohin233_recovery_20260918/private/p3_retry/original' / dependency
    raw = origin.read_bytes()
    pins = json.loads((HERE / 'P7/SOURCE_PINS.before.json').read_bytes())
    if sha(raw) != pins[dependency]:
        raise ValueError('exact_p7_presentation_dependency_required')
    write_once(HERE / 'P7/test_support' / dependency, raw)
    support = {dependency: dict(source_path=str(origin.relative_to(HERE.parents[2])),
        sha256=sha(raw), scope='unchanged_pinned_test_dependency_not_part_of_overlay')}
    write_once(HERE / 'P7/TEST_SUPPORT.json', (json.dumps(support, indent=2, sort_keys=True) + '\n').encode())
    print('Five isolated preimages and full pin sets verified; phase2 test harness copied unchanged.')


if __name__ == '__main__':
    main()
