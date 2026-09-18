"""Identity-bound guardian stop and matched-checkpoint source transition."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import signal
import time

from gpu import orch_combined_l1_continual_run as run
from organism_v6 import orch_combined_l1_continual as policy


def request(root, pid):
    assert root == run.ROOT and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    descriptor = os.pidfd_open(pid)
    try:
        identity = run.common.process_identity(pid)
        command = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        assert identity['uid'] == os.getuid()
        assert b'gpu.orch_combined_l1_continual_guard' in command
        assert str(root).encode() in command and b'--recover-partial' in command
        assert pid == 388193
        path = root / 'SAMPLED_UPGRADE_SIGNAL.json'
        assert not path.exists()
        run.write(path, dict(identity=identity, requested_unix=time.time(),
            action='SIGTERM_GUARDIAN_ONLY_FINISH_MATCHED_CHECKPOINT', workers_signalled=[],
            auxiliary_math_untouched=True, source_unchanged_until_workers_exit=True))
        assert run.common.process_identity(pid) == identity
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
    finally:
        os.close(descriptor)


def prepare(root, update):
    assert root == run.ROOT and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    for folder in Path('/proc').glob('[0-9]*'):
        try:
            command = (folder / 'cmdline').read_bytes().split(b'\0')
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if str(root).encode() in command:
            assert not {b'gpu.orch_combined_l1_continual_guard', b'gpu.orch_combined_l1_continual_run'}.intersection(command), 'old_native_process_live'
    assert run.read(root / 'WINDOWS' / f'{update:09d}.json')['stop'] is True
    checkpoints = {arm: root / arm / 'checkpoints' / f'{update:09d}' for arm in policy.ARMS}
    commits = {arm: policy.verify_checkpoint(path) for arm, path in checkpoints.items()}
    assert policy.pair_boundary(*(commits[arm]['metadata'] for arm in policy.ARMS)) == update
    previous = run.validate(root)
    archive = root / 'source_sampled_v2.tar'
    staged = root / 'source_sampled_v2'
    source_files = run.verify_archive(archive, staged)
    queued = root / 'SAMPLED_QUEUE_PENDING/highbudget_math_sampled_001_20260915_content_v2'
    encoder = run.read(queued / 'NATIVE_ENCODER.json')
    assert encoder['status'] == 'PASS' and encoder['packet_sha256'] == run.sha(queued / 'BOUND_PACKET.json')
    assert '105 passed' in (root / 'CPU_TESTS_SAMPLED_V2.log').read_text()
    assert '42 passed' in (root / 'REMOTE_CPU_SAMPLED_V2.log').read_text()
    backup = root / 'UPGRADES' / f'SAMPLED_{update:09d}'
    backup.mkdir(parents=True, exist_ok=False)
    for name in ('PREPARE.json', 'READY.json', 'PUBLICATION.json', 'SOURCE_TRANSITION.json', 'source.tar',
                 'CPU_TESTS.log', 'TERMINAL.json', 'INITIAL_ADMISSION_2.json', 'INITIAL_ADMISSION_3.json',
                 'INITIAL_ADMISSION_6.json', 'HUBBLE_RELEASE_BINDING.json', 'TRAIN_RELEASE_2.json',
                 'TRAIN_RELEASE_3.json', 'TRAIN_RELEASE_6.json'):
        if (root / name).exists():
            shutil.copyfile(root / name, backup / name)
    if (root / 'ADMISSION_ATTEMPTS').exists():
        os.rename(root / 'ADMISSION_ATTEMPTS', backup / 'ADMISSION_ATTEMPTS')
    os.rename(root / 'source', backup / 'source')
    os.rename(staged, root / 'source')
    shutil.copyfile(archive, root / 'source.tar')
    destination = root / 'CONTENT_QUEUE' / queued.name
    assert not destination.exists()
    os.rename(queued, destination)
    transition = dict(update=update, from_source_sha256=previous['source_sha256'],
        to_source_sha256=run.sha(root / 'source.tar'), checkpoint_sha256={arm: run.sha(path / 'COMMIT.json') for arm, path in checkpoints.items()},
        preserve_adapter_optimizer_rng_cursor=True, reset=False,
        scope='Sampled64 exact source/encoding append and supported third-rank CLI repair; no optimizer/schedule change',
        native_encoder_sha256=run.sha(destination / 'NATIVE_ENCODER.json'), created_unix=time.time())
    run.write(root / 'SOURCE_TRANSITION.json', transition)
    prepared = dict(previous, source_sha256=transition['to_source_sha256'], source_files=source_files,
        source_transition=transition, prepared_unix=time.time(), files=dict(previous['files']))
    names = ['SOURCE_TRANSITION.json', 'SAMPLED_PROTOCOL_V1.md'] + [str((destination / name).relative_to(root))
        for name in ('BOUND_PACKET.json', 'EXCLUSIONS.json', 'CPU_BOUND.json', 'NATIVE_ENCODER.json', 'MANIFEST.json', 'ROWS.json')]
    prepared['files'].update({name: run.sha(root / name) for name in names})
    run.write(root / 'PREPARE.json', prepared)
    shutil.copyfile(root / 'CPU_TESTS_SAMPLED_V2.log', root / 'CPU_TESTS.log')
    ready = dict(schema='COMBINED_CONTINUAL_READY_V1', prepare_sha256=run.sha(root / 'PREPARE.json'),
        source_sha256=prepared['source_sha256'], cpu_tests_passed=True,
        cpu_test_log_sha256=run.sha(root / 'CPU_TESTS.log'), local_tests='105passed,3localTorchskips,50subtests',
        remote_tests='42passed,15source-only fixture skips; actual3processGlooSUM executed',
        remote_cpu_test_log_sha256=run.sha(root / 'REMOTE_CPU_SAMPLED_V2.log'),
        sampled_encoder_sha256=transition['native_encoder_sha256'],
        sampled_packet_sha256=run.sha(destination / 'BOUND_PACKET.json'),
        source_transition_sha256=run.sha(root / 'SOURCE_TRANSITION.json'),
        resume_update=update, first_topology=run.TRANSITIONAL_TOPOLOGY, final_topology=run.TOPOLOGY,
        lifetime_sha256=run.sha(root / 'LIFETIME.json'), ready_utc=datetime.now(timezone.utc).isoformat(),
        no_reset=True, historical_labels_unchanged=True)
    run.write(root / 'READY.json', ready)
    for name in ('PREPARE', 'READY', 'SOURCE_TRANSITION'):
        shutil.copyfile(root / (name + '.json'), root / (name + '_SAMPLED_V2.json'))
    run.validate(root)
    print('READY checkpoint', update, 'source', prepared['source_sha256'], 'prepare', run.sha(root / 'PREPARE.json'),
          'ready', run.sha(root / 'READY.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('request', 'prepare'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--pid', type=int)
    parser.add_argument('--update', type=int)
    options = parser.parse_args()
    if options.action == 'request':
        request(options.root, options.pid)
    else:
        prepare(options.root, options.update)
