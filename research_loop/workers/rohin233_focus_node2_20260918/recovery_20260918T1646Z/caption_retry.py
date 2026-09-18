"""Preserve failed pre-native attempt, then use supported saved-wall extension."""

import argparse
import shutil
import subprocess
import sys
import time

import recover
from c0_lease_parent import HORIZON
from recover import HERE, LEASE_SOURCE, LEASE_SHA, PYTHON, absent, environment, locations, read, require, sha, write


def prepare():
    absent('CAPTION')
    root, source, control, preserved = locations('CAPTION')
    require(sha(LEASE_SOURCE) == LEASE_SHA, 'proven_existing_node2_lease')
    authority = read(LEASE_SOURCE)
    require(time.time() < HORIZON <= authority['hard_deadline_unix'], 'conservative_authorized_horizon')
    require(read(control / 'OUTER_EXIT.json')['status'] == 1 and not (control / 'NATIVE.log').exists(),
        'exact_failed_pre_native_dispatch_only')
    failed = preserved / 'failed_guard_seam_1727'
    failed.mkdir()
    control.rename(failed / 'control')
    shutil.copytree(source, failed / 'source')
    control.mkdir()
    for name in ('RECOVERY.json', 'RECOVERY_APPENDED.json', 'ARCHIVE_REPLAY.json',
            'CACHE_RESTORED.json', 'CACHE_CHECK.json', 'TAIL_ARTIFACTS_PRESERVED.json'):
        shutil.copy2(failed / 'control' / name, control / name)
    shutil.copy2(HERE / 'runtime.py', source / 'gpu/r233_node2_recovery.py')
    shutil.copy2(HERE / 'test_recovery.py', source / 'tests/test_r233_node2_recovery.py')
    configure()


def configure():
    absent('CAPTION')
    root, source, control, preserved = locations('CAPTION')
    failed = preserved / 'failed_guard_seam_1727'
    require(not (control / 'PLAN.json').exists() and sha(LEASE_SOURCE) == LEASE_SHA,
        'configuration_not_published_original_lease_bound')
    authority = read(LEASE_SOURCE)
    plan = read(failed / 'control/PLAN.json')
    recovery = read(control / 'RECOVERY.json')
    plan.update(hard_end_unix=HORIZON, lease_end_unix=authority['lease_end_unix'],
        authorized_wall_extension=dict(schema='R131_AUTHORIZED_WALL_EXTENSION_V1',
            previous_deadline_unix=recovery['new_deadline_unix'],
            previous_stream_sha256=recovery['restored_state_sha256'], new_deadline_unix=HORIZON,
            lease_end_unix=authority['lease_end_unix'], safety_margin_seconds=21600))
    sys.path.insert(0, str(source))
    from gpu.orch_r125_stream_journal import WALL_EXTENSION_SCHEMA
    from gpu.orch_r125_continual_native import prepare_wall_extension
    from organism_v6.orch_r125_continual_stream import ContinualStream
    plan['authorized_wall_extension']['schema'] = WALL_EXTENSION_SCHEMA
    proof = read(control / 'RECOVERY_APPENDED.json')
    record = read(root / 'raw/stream/records' / f'{proof["index"]:020d}.json')
    require(record['sha256'] == proof['sha256'], 'unchanged_original_recovery_head')
    saved = record['document']['state']
    stream = ContinualStream.restore(saved, expected_sha256=saved['sha256'])
    write(control / 'PLAN.json', plan)
    extension = prepare_wall_extension(plan, stream, resume=True, plan_sha256=sha(control / 'PLAN.json'))
    write(control / 'WALL_EXTENSION_CPU.json', dict(validated=True, deadline_only=True,
        prior_state_sha256=saved['sha256'], new_state_sha256=extension['state']['sha256'],
        new_deadline_unix=HORIZON, lease_source_sha256=LEASE_SHA, native_was_never_started=True))
    lease = read(failed / 'control/LEASE.json')
    lease.update(lease_end_unix=authority['lease_end_unix'], hard_end_unix=HORIZON,
        physical_lease_changed=False, authoritative_source_sha256=LEASE_SHA)
    write(control / 'LEASE.json', lease)
    recover.check('CAPTION')


def publish(commit):
    root, source, control, preserved = locations('CAPTION')
    cpu, plan = read(control / 'RECEIVING_CPU.json'), read(control / 'PLAN.json')
    require(cpu['passed'] and len(commit) == 40, 'tested_pushed_builder_gate')
    write(control / 'ALLOCATION.json', dict(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        gpu_uuid=plan['gpu_uuid'], physical=2, builder_entry_logged=True, builder_entry_pushed=True,
        builder_entry_commit=commit, cpu_receipt_path=str(control / 'RECEIVING_CPU.json'),
        cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'), declared_unix=time.time()))
    guard = read(preserved / 'failed_guard_seam_1727/control/GUARD.json')
    guard.update(source_pins=cpu['source_pins'], plan_sha256=sha(control / 'PLAN.json'),
        hard_end_unix=HORIZON, lease_sha256=sha(control / 'LEASE.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'), next_reserved_unix=read(LEASE_SOURCE)['hard_deadline_unix'])
    write(control / 'GUARD.json', guard)
    subprocess.run([PYTHON, '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], cwd=source, env=environment(source), check=True)
    write(control / 'READY.json', dict(passed=True, same_journal=True, builder_commit=commit,
        deadline_only_supported_resume=True, prior_failed_attempt_preserved=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'configure', 'publish'))
    parser.add_argument('--commit')
    arguments = parser.parse_args()
    publish(arguments.commit) if arguments.mode == 'publish' else globals()[arguments.mode]()
