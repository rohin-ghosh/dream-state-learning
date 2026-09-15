"""Prepared-only, identity-bound DEV transition preserving matched checkpoints."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

from gpu import orch_combined_l1_continual_run as run
from organism_v6 import orch_combined_l1_continual as state
from organism_v6 import orch_combined_l1_dev as dev


def freeze(root):
    prepared = run.validate(root)
    corpus = run.read(root / 'CORPORA/000007.json')
    assert len(corpus['rows']) == 3260
    plan = dict(schema='COMBINED_CONTINUAL_ADAPTIVE_DEV_V1', claim='ADAPTIVE_DEV_NOT_CONFIRMATORY_H1',
        parent_access=False, training_ingestion=False, readout_total_cap=1760, reserved_all_calls=dev.total_bound(),
        registered_corpus_rows=len(corpus['rows']), registered_corpus_sha256=run.sha(root / 'CORPORA/000007.json'),
        registered_batch_ids=[entry['batch_id'] for entry in corpus['ingested']],
        first_boundary_update=dev.first_boundary(len(corpus['rows'])), route_condition='OWN_TEXT',
        math_tokens=1536, route_tokens=1536, other_tokens=160, math_system=dev.DEFAULT_MATH_SYSTEM,
        report_order=['richness', 'accuracy'], temporary_devices=[2, 3, 6],
        new_batches_during_registered_traversal='QUEUE_UNTIL_INTERMEDIATE_THEN_APPEND',
        promote_automatically=False, resume_after_readout_failure=True, maximum_diagnostic_seconds=1980,
        intermediate_finish_before_unix=datetime(2026, 9, 15, 5, 43, tzinfo=timezone.utc).timestamp(),
        cohort_sha256={name: run.sha(root / name) for name in ('COHORT.json', 'ROUTE_COHORT.json', 'LEGACY_READOUT.json')},
        p64_historical='224 calls; first-person150-400 prompt; NOT DEFAULT',
        p64_addon='128 calls; SAME frozen64 math; minimalDEFAULT; separate immutable readout',
        limitations=['Adaptive DEV, not confirmatory H1', 'Author descriptive semantic review, not certified',
            'Route existing action protocol preserved; no added richness/exhaustion prompts',
            'Corpus ingestion is not proof every row already supervised; per-update exposure log authoritative'],
        registered_unix=time.time(), prior_source_sha256=prepared['source_sha256'])
    dev.validate_plan(plan)
    assert not (root / 'DEV_PLAN_PENDING.json').exists()
    run.write(root / 'DEV_PLAN_PENDING.json', plan)
    print(dict(plan_sha256=run.sha(root / 'DEV_PLAN_PENDING.json'), boundary=plan['first_boundary_update'], calls=1760))


def transition(root, pid):
    assert root == run.ROOT and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    ready = run.read(root / 'DEV_READY.json')
    archive, staged = root / 'source_dev_ready.tar', root / 'source_dev_ready'
    assert ready['status'] == 'PASS' and ready['source_sha256'] == run.sha(archive)
    assert ready['source_files'] == run.verify_archive(archive, staged)
    assert ready['plan_sha256'] == run.sha(root / 'DEV_PLAN_PENDING.json')
    publication = run.read(root / 'DEV_PUBLICATION.json')
    assert publication['ready_sha256'] == run.sha(root / 'DEV_READY.json')
    assert publication['coordination_append_verified'] is True
    previous = run.validate(root)
    recovered_failure = pid is None
    if recovered_failure:
        failure = run.read(root / 'ABORT.json')
        assert failure['type'] == 'KeyError' and failure['message'] == "'releases'"
        run.write(root / 'DEV_TRANSITION_REQUEST.json', dict(requested_unix=time.time(),
            action='RESTORE_LAST_DURABLE_AFTER_TERMINAL_FIELD_KEYERROR', workers_signalled=[],
            failure_sha256=run.sha(root / 'ABORT.json')))
    else:
        descriptor = os.pidfd_open(pid)
        try:
            identity = run.common.process_identity(pid)
            command = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
            assert identity['uid'] == os.getuid() and str(root).encode() in command
            assert b'gpu.orch_combined_l1_continual_guard' in command
            run.write(root / 'DEV_TRANSITION_REQUEST.json', dict(identity=identity, requested_unix=time.time(),
                action='GUARDIAN_ONLY_FINISH_MATCHED_CHECKPOINT', workers_signalled=[], prepared_before_stop=True))
            assert run.common.process_identity(pid) == identity
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        finally:
            os.close(descriptor)
        while True:
            try:
                if run.common.process_identity(pid) != identity:
                    break
            except (FileNotFoundError, ProcessLookupError):
                break
            assert time.time() < run.read(root / 'LIFETIME.json')['native_deadline_unix']
            time.sleep(1)
    for folder in Path('/proc').glob('[0-9]*'):
        try:
            command = (folder / 'cmdline').read_bytes().split(b'\0')
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        assert not (str(root).encode() in command and {b'gpu.orch_combined_l1_continual_run',
            b'gpu.orch_combined_l1_continual_guard'}.intersection(command)), 'old_worker_still_live'
    assert run.read(root / 'TERMINAL.json')['status'] == ('FAILED' if recovered_failure else 'TRAINING_CHECKPOINTED')
    checkpoint = max((root / 'PAIRED_BOUNDARIES').glob('*.json'))
    update = run.read(checkpoint)['update']
    assert update < dev.validate_plan(run.read(root / 'DEV_PLAN_PENDING.json'))['first_boundary_update']
    commits = {arm: root / arm / 'checkpoints' / f'{update:09d}/COMMIT.json' for arm in state.ARMS}
    metadata = [state.verify_checkpoint(path.parent)['metadata'] for path in commits.values()]
    assert state.pair_boundary(*metadata) == update
    window = root / 'WINDOWS' / f'{update:09d}.json'
    if recovered_failure:
        assert not window.exists(), 'do_not_replace_existing_window'
        run.write(window, dict(stop=True, reason='durable1536_recovery_after_auxiliary_field_bug'))
    assert run.read(window)['stop'] is True
    backup = root / 'UPGRADES' / f'DEV_{update:09d}'
    backup.mkdir(parents=True, exist_ok=False)
    for name in ('PREPARE.json', 'READY.json', 'PUBLICATION.json', 'SOURCE_TRANSITION.json', 'source.tar',
                 'CPU_TESTS.log', 'TERMINAL.json', 'ABORT.json', 'ADMISSION_ATTEMPTS'):
        path = root / name
        if path.exists():
            os.rename(path, backup / name)
    os.rename(root / 'source', backup / 'source')
    os.rename(staged, root / 'source')
    shutil.copyfile(archive, root / 'source.tar')
    shutil.copyfile(root / 'DEV_PLAN_PENDING.json', root / 'DEV_PLAN.json')
    shutil.copyfile(root / 'DEV_CPU_TESTS.log', root / 'CPU_TESTS.log')
    transition_record = dict(update=update, from_source_sha256=previous['source_sha256'],
        to_source_sha256=ready['source_sha256'], checkpoint_sha256={arm: run.sha(path) for arm, path in commits.items()},
        preserve_adapter_optimizer_rng_cursor=True, reset=False,
        scope='DEFAULT adaptiveDEV, bound1760calls, richness-first reporting; session-bound stale-abort repair',
        created_unix=time.time())
    run.write(root / 'SOURCE_TRANSITION.json', transition_record)
    prepared = dict(previous, source_sha256=ready['source_sha256'], source_files=ready['source_files'],
        source_transition=transition_record, files=dict(previous['files']))
    for name in ('DEV_PLAN.json', 'SOURCE_TRANSITION.json'):
        prepared['files'][name] = run.sha(root / name)
    run.write(root / 'PREPARE.json', prepared)
    run.write(root / 'READY.json', dict(prepare_sha256=run.sha(root / 'PREPARE.json'),
        source_sha256=ready['source_sha256'], cpu_tests_passed=True, cpu_test_log_sha256=run.sha(root / 'CPU_TESTS.log')))
    run.write(root / 'PUBLICATION.json', dict(publication, ready_sha256=run.sha(root / 'READY.json')))
    stream = (root / f'GUARDIAN_DEV_FROM_{update:09d}.log').open('x')
    command = [run.PYTHON, '-B', '-m', 'gpu.orch_combined_l1_continual_guard', '--root', str(root), '--resume', str(update)]
    child = subprocess.Popen(command, cwd=root / 'source', env=dict(os.environ,
        CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'), stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    stream.close()
    run.write(root / 'DEV_RESUME_STARTED.json', dict(pid=child.pid, identity=run.common.process_identity(child.pid),
        update=update, source_sha256=ready['source_sha256'], started_unix=time.time(), optimizer_updates_not_yet_asserted=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--pid', type=int)
    options = parser.parse_args()
    if options.freeze:
        freeze(options.root)
    else:
        transition(options.root, options.pid)
