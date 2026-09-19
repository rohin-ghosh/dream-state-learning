"""Independent local archive/immutability/portable CPU verification; no node I/O."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tarfile

import manifest_checks as checks
import prepare_epoch3 as prepare


def verify(output, extraction):
    output = Path(output).resolve()
    extraction = prepare.validate_output(extraction)
    ready = prepare.base.read(output / 'READY.json')
    epoch = output / 'C2/epoch3'
    manifest = prepare.base.read(epoch / 'EPOCH3_SOURCE.json')
    inputs = prepare.base.read(output / 'INPUTS.json')
    prepare.require(prepare.snapshot(prepare.EPOCH2_ROOT) == inputs['epoch2_tree'],
        'entire_epoch2_tree_still_unchanged')
    prepare.require(prepare.sha(epoch / 'EPOCH3_SOURCE.json') == ready['manifest_sha256'], 'manifest_pin')
    prepare.require(prepare.sha(ready['archive']) == ready['archive_sha256'], 'archive_pin')
    checks.verify(epoch / 'source', manifest)
    for name, expected in manifest['helper_pins'].items():
        prepare.require(prepare.sha(epoch / 'tools' / name) == expected, 'helper_pin:' + name)
    for directory in (epoch / 'source', epoch / 'tools'):
        for path in (directory, *directory.rglob('*')):
            prepare.require(path.stat().st_mode & 0o777 == (0o555 if path.is_dir() else 0o444),
                'sealed_file_directory_modes')
    for name, evidence in ready['receipts'].items():
        prepare.require(prepare.sha(evidence['path']) == evidence['sha256'], 'CPU_receipt_pin:' + name)
    member_names = set()
    with tarfile.open(ready['archive'], 'r:gz') as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            prepare.require(not path.is_absolute() and '..' not in path.parts and
                path.parts[:2] == ('C2', 'epoch3') and member.name not in member_names,
                'safe_unique_epoch3_archive_members')
            prepare.require(member.isfile() or member.isdir(), 'regular_archive_members')
            member_names.add(member.name)
            destination = extraction / path
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                content = archive.extractfile(member).read()
                prepare.require(prepare.base.checksum(content) == prepare.sha(output / path),
                    'exact_extracted_member:' + member.name)
                prepare.publish(destination, content)
    expected_names = {str(path.relative_to(output)) for path in (epoch, *epoch.rglob('*'))}
    prepare.require(member_names == expected_names, 'archive_has_every_and_only_bundle_member')
    extracted = extraction / 'C2/epoch3'
    for directory in (extracted / 'source', extracted / 'tools'):
        prepare.base.seal(directory)
    checker = prepare.load('c2_epoch3_extracted_verifier', extracted / 'tools/cpu_check.py')
    checker.verify_source(extracted / 'source', manifest)
    template = prepare.base.read(extracted / 'control/PLAN.template.json')
    reanchored = deepcopy(template)
    reanchored['checkpoint_tail_recovery'].update(complete_index=11504, complete_sha256='1' * 64)
    checker.verify_guard_template(reanchored, template, Path(manifest['new_source']))
    guard_refusals = []
    for name, value in (('hard_end_unix', 1789927201), ('physical', 0), ('learn_row_policy', 'CHANGED')):
        changed = deepcopy(reanchored)
        changed[name] = value
        try:
            checker.verify_guard_template(changed, template, Path(manifest['new_source']))
        except ValueError:
            guard_refusals.append(name)
        else:
            raise AssertionError('guard_recipe_change_accepted:' + name)
    scratch = extraction / 'scratch'
    scratch.mkdir()
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(extracted / 'source'), TMPDIR=str(scratch), OMP_NUM_THREADS='1',
        MKL_NUM_THREADS='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    results = {}
    for name, filename in (('PORTABLE_SOURCE', 'source_checks.py'), ('PORTABLE_FRONTIER', 'frontier_checks.py')):
        command = [sys.executable, '-B', str(extracted / 'tools' / filename),
            '--source', str(extracted / 'source'), '--manifest', str(extracted / 'EPOCH3_SOURCE.json')]
        results[name] = prepare.run_check(extracted, name, command, environment)
    prepare.require(prepare.snapshot(prepare.EPOCH2_ROOT) == inputs['epoch2_tree'], 'epoch2_unchanged_after_validation')
    checks.verify(extracted / 'source', manifest)
    proof = dict(schema='C2_EPOCH3_INDEPENDENT_LOCAL_VALIDATION_V1', passed=True,
        observed_utc=datetime.now(timezone.utc).isoformat(), manifest_sha256=ready['manifest_sha256'],
        archive_sha256=ready['archive_sha256'], source_sha256=checks.AFTER, epoch2_history_sha256=checks.BEFORE,
        epoch2_all_bytes_and_modes_unchanged=True, archive_members_verified=len(member_names),
        exact_source_and_helper_seals_verified=True, extraction=str(extraction),
        guard_permits_only_checkpoint_anchor_change=True, guard_recipe_mutations_refused=guard_refusals,
        portable_repeated_tests={name: result['tests_run'] for name, result in results.items()},
        unique_source_tests=164, unique_preparation_tests=12,
        preparation_test_log_sha256=prepare.sha(prepare.TOOLS / 'TESTS.log'),
        validator_sha256=prepare.sha(Path(__file__)),
        actual_C2_checkpoint_validated=False, C2_latency_validated=False,
        remote_staging_performed=False, live_handoff_authorization=False, admission_granted=False,
        native_signals=[], dispatches=[], parent_deliveries=[], bridge_changes=[], hard_end_unix=1789927200)
    prepare.document(prepare.WORKER / 'EPOCH3_VALIDATION.json', proof)
    return proof


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--extraction', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.output, args.extraction), sort_keys=True, indent=2))
