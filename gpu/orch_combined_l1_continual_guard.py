"""Own-process supervisor, matched corpus windows, safe topology expansion."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time

from gpu import orch_combined_l1_continual_run as run
from organism_v6 import orch_combined_l1_continual as policy


read, write, sha = run.read, run.write, run.sha
HUBBLE = Path('/localhome/local-rohing/orch_rich_hot_a100_20260915_attempt1')


def auxiliary_available(root):
    release = root / 'P64_DEFAULT/RELEASED.json'
    if not release.exists():
        return False
    report = read(release)
    return len(report['returncodes']) == 2 and report['actual_reserved_calls'] <= 128


def admit_devices(root, indexes, label, scan=None, pause=time.sleep, attempts=30):
    scan = scan or run.scan
    transient = ('process_identity_drift:', 'minor_scan_identity_changed:', 'minor_scan_process_drift:')
    for index in indexes:
        for attempt in range(attempts):
            report = scan(index, root / 'SERVICE_IDENTITY.json')
            write(root / 'ADMISSION_ATTEMPTS' / f'{label}_{index}_{attempt:03d}.json', report)
            if report['clear']:
                assert not report['blocking_reasons']
                write(root / f'{label}_{index}.json', report)
                break
            reasons = report['blocking_reasons']
            assert reasons and all(reason.startswith(transient) for reason in reasons), (
                'fresh_gpu_admission_failed', index, reasons)
            assert attempt + 1 < attempts, ('unstable_full_process_snapshot', index, reasons)
            pause(1)


def port():
    with socket.socket() as connection:
        connection.bind(('127.0.0.1', 0))
        return connection.getsockname()[1]


def take_batch(root, state):
    for path in sorted((root / 'INBOX').glob('*/BOUND_PACKET.json')):
        receipt = read(path.parent / 'CPU_BOUND.json')
        encoder = read(path.parent / 'NATIVE_ENCODER.json')
        assert receipt['status'] == encoder['status'] == 'PASS'
        assert receipt['packet_sha256'] == encoder['packet_sha256'] == sha(path)
        assert receipt['manifest_sha256'] == sha(path.parent / 'MANIFEST.json')
        assert receipt['rows_sha256'] == sha(path.parent / 'ROWS.json')
        assert receipt['exclusions_sha256'] == sha(path.parent / 'EXCLUSIONS.json')
        exclusions = read(path.parent / 'EXCLUSIONS.json')
        state = policy.append_batch(state, read(path), **{key: exclusions[key]
            for key in ('held_math', 'held_route', 'held_question_hashes')})
    for path in sorted((root / 'CONTENT_QUEUE').glob('*/BOUND_PACKET.json')):
        from gpu import orch_combined_l1_continual_content as content
        receipt, encoder = read(path.parent / 'CPU_BOUND.json'), read(path.parent / 'NATIVE_ENCODER.json')
        assert receipt['status'] == encoder['status'] == 'PASS'
        assert receipt['packet_sha256'] == encoder['packet_sha256'] == sha(path)
        assert receipt['manifest_sha256'] == sha(path.parent / 'MANIFEST.json')
        assert receipt['rows_sha256'] == sha(path.parent / 'ROWS.json')
        assert receipt['exclusions_sha256'] == sha(path.parent / 'EXCLUSIONS.json')
        state = content.append(state, read(path), read(path.parent / 'EXCLUSIONS.json'))
    return state


def launch(root, resume=0, recover_partial=False):
    prepared = run.validate(root)
    from organism_v6 import orch_combined_l1_dev as dev_policy
    dev_plan = dev_policy.validate_plan(read(root / 'DEV_PLAN.json')) if (root / 'DEV_PLAN.json').exists() else None
    dev_done = (root / 'DEV_PROGRESS.json').exists()
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '' and os.geteuid() != 0
    ready, publication = read(root / 'READY.json'), read(root / 'PUBLICATION.json')
    assert ready['prepare_sha256'] == sha(root / 'PREPARE.json') and ready['cpu_tests_passed']
    assert ready['source_sha256'] == prepared['source_sha256']
    assert ready['cpu_test_log_sha256'] == sha(root / 'CPU_TESTS.log')
    assert publication['ready_sha256'] == sha(root / 'READY.json')
    assert publication['coordination_append_verified'] is True
    assert publication['dated_builder_line'].startswith('[Builder — COMBINED_L1_CONTINUAL] ')
    assert bool(resume or recover_partial) == (root / 'LIFETIME.json').exists()
    prior_lifetime = read(run.MATH_ROOT / 'LIFETIME.json')
    started = time.time()
    controller_session = f'{os.getpid()}:{time.time_ns()}'
    original = prior_lifetime['started_unix']
    hard_end = min(original + 43200, original + 24 * 3600 / 5, run.LEASE_END - 21600)
    lifetime = dict(started_unix=started, original_started_unix=original,
        hard_deadline_unix=hard_end, native_deadline_unix=hard_end - 180,
        training_deadline_unix=hard_end - 3780, total_gpu_hours_ceiling=24,
        accounting='Conservatively charge five GPUs since original math start, including transitional math and reserved readout.',
        parent_calls=0, training_generation=0, readout_calls=1760, lease_margin_seconds=21600,
        no_retry=True, no_fixed_presentation_stop=True)
    assert lifetime['training_deadline_unix'] > started + 600
    if resume or recover_partial:
        preserved = read(root / 'LIFETIME.json')
        assert preserved['hard_deadline_unix'] == hard_end
        lifetime = preserved
        write(root / 'RESUMES' / f'{resume:09d}.json', dict(update=resume, partial_off128=recover_partial, resumed_unix=time.time(),
            lifetime_sha256=sha(root / 'LIFETIME.json'), source_sha256=prepared['source_sha256']))
    else:
        write(root / 'LIFETIME.json', lifetime)
        write(root / 'MIGRATION.json', {arm: dict(adapter=prepared['initial'],
            original_lineage='fixed route lane0 child, never score-selected',
            math_lineage='auxiliary preserved independently; never replaces this evolving child',
            optimizer_boundary='fresh AdamW only once at continual initialization',
            legacy_optimizer_available=False) for arm in policy.ARMS})
    children, logs = [], []
    topology = run.INITIAL_TOPOLOGY
    interrupted = False

    def handle_signal(signum, frame):
        nonlocal interrupted
        interrupted = True

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    def admit(indexes, label):
        admit_devices(root, indexes, label)

    def spawn(topology, update):
        for arm in policy.ARMS:
            size = len(topology[arm])
            start_update = 128 if recover_partial and update == 0 and arm == 'OFF' else update
            address = port()
            for rank, index in enumerate(topology[arm]):
                log = (root / f'{arm}_rank{rank}_from{start_update:09d}.log').open('x')
                logs.append(log)
                command = [run.PYTHON, '-B', '-m', run.PROGRAM, 'train', '--root', str(root),
                    '--arm', arm, '--rank', str(rank), '--port', str(address), '--world-size', str(size),
                    '--index', str(index)]
                if start_update:
                    command += ['--resume', str(root / arm / 'checkpoints' / f'{start_update:09d}')]
                child = subprocess.Popen(command, cwd=root / 'source',
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=run.DEVICES[index], PYTHONDONTWRITEBYTECODE='1',
                             CONTINUAL_CONTROLLER_SESSION=controller_session,
                             OMP_NUM_THREADS='2', TOKENIZERS_PARALLELISM='false'),
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                identity = run.common.process_identity(child.pid)
                children.append((child, identity))
                write(root / f'{arm}_RANK{rank}_START_{start_update:09d}.json',
                    dict(pid=child.pid, identity=identity, index=index, uuid=run.DEVICES[index],
                         world_size=size, update=start_update, started_unix=time.time(), command=command))

    def wait_children():
        for child, identity in children:
            result = child.wait(timeout=90)
            assert result == 0, ('worker_exit', child.pid, result)
        children.clear()

    status = 'FAILED'
    try:
        request = HUBBLE / 'LAPLACE_RELEASE_REQUEST.json'
        if not request.exists():
            write(request, dict(requester='Laplace', launch_ready=True, source_root=str(root),
                ready_sha256=sha(root / 'READY.json'), requested_utc=datetime.now(timezone.utc).isoformat()))
        else:
            assert read(request)['requester'] == 'Laplace'
        release_deadline = min(time.time() + 600, lifetime['training_deadline_unix'])
        while True:
            assert time.time() < release_deadline and not interrupted, 'selective_release_timeout_or_interruption'
            reports = [HUBBLE / f'FLOOR_RELEASE_{index}.json' for index in (2, 3)]
            if all(path.exists() and read(path).get('clear') is True for path in reports):
                write(root / 'HUBBLE_RELEASE_BINDING.json', {str(path): sha(path) for path in reports})
                break
            time.sleep(2)
        admit((2, 3), 'INITIAL_ADMISSION')
        initial_gpu6 = HUBBLE / 'FLOOR_RELEASE_6.json'
        if initial_gpu6.exists() and read(initial_gpu6).get('clear') is True:
            admit((6,), 'INITIAL_ADMISSION')
            topology = run.TRANSITIONAL_TOPOLOGY
        if resume:
            metadata = [policy.verify_checkpoint(root / arm / 'checkpoints' / f'{resume:09d}')['metadata']
                        for arm in policy.ARMS]
            assert policy.pair_boundary(*metadata) == resume
            corpus_path = f'CORPORA/{metadata[0]["corpus_version"]:06d}.json'
            assert sha(root / corpus_path) == metadata[0]['corpus_sha256']
            previous_window = root / 'WINDOWS' / f'{resume:09d}.json'
            assert read(previous_window)['stop'] is True
            archived = root / 'STOP_WINDOWS' / f'CODE_UPGRADE_{resume:09d}.json'
            archived.parent.mkdir(exist_ok=True)
            os.rename(previous_window, archived)
        else:
            corpus_path = 'CORPORA/000000.json'
        if recover_partial:
            assert not list((root / 'FULL/checkpoints').glob('*/COMMIT.json'))
            preserved_off = policy.verify_checkpoint(root / 'OFF/checkpoints/000000128')['metadata']
            assert preserved_off['update'] == 128 and preserved_off['corpus_version'] == 0
            assert preserved_off['corpus_sha256'] == sha(root / corpus_path)
            retirement = read(root / 'NCCL_STALL_RETIREMENT.json')
            assert retirement['off_checkpoint_sha256'] == sha(root / 'OFF/checkpoints/000000128/COMMIT.json')
        state = read(root / corpus_path)
        update = resume

        def ingest(suffix=''):
            nonlocal state, corpus_path
            newer = take_batch(root, state)
            if newer is not state:
                state = newer
                corpus_path = f'CORPORA/{state["version"]:06d}.json'
                assert not (root / corpus_path).exists()
                write(root / corpus_path, state)
                receipt = root / 'INGEST_RECEIPTS' / f'{update:09d}{suffix}.json'
                assert not receipt.exists()
                write(receipt, dict(update=update, corpus_path=corpus_path, corpus_sha256=sha(root / corpus_path),
                    ingested=state['ingested'], duplicates=state['duplicates'], rows=len(state['rows']),
                    reset=False, optimizer_retained=True, time_unix=time.time()))

        def next_end():
            return dev_policy.next_window(update, dev_plan['first_boundary_update'], dev_done) if dev_plan else update + policy.CHECKPOINT_UPDATES

        if dev_plan and not dev_done:
            ingest('_DEV_REGISTERED')
            assert len(state['rows']) == dev_plan['registered_corpus_rows']
            assert {entry['batch_id'] for entry in state['ingested']} == set(dev_plan['registered_batch_ids'])
            assert update < dev_plan['first_boundary_update'], 'registered_boundary_already_passed'
        write(root / 'WINDOWS' / f'{update:09d}.json', dict(start_update=update, end_update=next_end(),
            corpus_path=corpus_path, corpus_sha256=sha(root / corpus_path), stop=False))
        spawn(topology, update)
        while True:
            target = read(root / 'WINDOWS' / f'{update:09d}.json')['end_update']
            while True:
                assert time.time() < lifetime['native_deadline_unix'], 'global_deadline'
                for child, identity in children:
                    assert child.poll() is None, ('unexpected_worker_exit', child.pid, child.returncode)
                paths = [root / arm / 'checkpoints' / f'{target:09d}' for arm in policy.ARMS]
                if all((path / 'COMMIT.json').exists() for path in paths):
                    full, off = [policy.verify_checkpoint(path)['metadata'] for path in paths]
                    assert policy.pair_boundary(full, off) == target
                    break
                time.sleep(1)
            update = target
            write(root / 'PAIRED_BOUNDARIES' / f'{update:09d}.json', dict(update=update,
                corpus_sha256=full['corpus_sha256'], corpus_version=full['corpus_version'],
                full_sha256=sha(paths[0] / 'COMMIT.json'), off_sha256=sha(paths[1] / 'COMMIT.json'),
                reference_tokens=full['reference_tokens'], full_supervised=full['supervised_tokens'],
                off_supervised=off['supervised_tokens'], time_unix=time.time(), topology=topology))
            terminal = interrupted or time.time() >= lifetime['training_deadline_unix']
            diagnostic = bool(dev_plan and not dev_done and update == dev_plan['first_boundary_update'] and not terminal)
            auxiliary = run.MATH_ROOT / 'TERMINAL.json'
            gpu6_release = HUBBLE / 'FLOOR_RELEASE_6.json'
            gpu6_ready = gpu6_release.exists() and read(gpu6_release).get('clear') is True
            next_topology = topology
            if gpu6_ready:
                next_topology = run.TRANSITIONAL_TOPOLOGY
                if auxiliary_available(root):
                    next_topology = run.TOPOLOGY
            expand = not terminal and next_topology != topology
            if terminal or expand or diagnostic:
                write(root / 'WINDOWS' / f'{update:09d}.json', dict(stop=True,
                    reason='terminal_readout' if terminal else 'adaptive_dev_checkpoint' if diagnostic else 'preserved_checkpoint_topology_expansion'))
                wait_children()
                if terminal:
                    status = 'TRAINING_CHECKPOINTED'
                    break
                if diagnostic:
                    from gpu.orch_combined_l1_dev import launch as launch_dev
                    evaluation = launch_dev(root, 'INTERMEDIATE', update, lifetime)
                    dev_done = True
                    write(root / 'DEV_PROGRESS.json', dict(update=update, evaluation=str(evaluation),
                        adaptive_dev_not_confirmatory=True, no_score_based_training_decision=True,
                        completed_unix=time.time()))
                    if auxiliary_available(root):
                        next_topology = run.TOPOLOGY
                    expand = True
                admit(sorted({index for indexes in next_topology.values() for index in indexes}), f'EXPANSION_ADMISSION_{update:09d}')
                topology = next_topology
                write(root / 'TOPOLOGY_EXPANSIONS' / f'{update:09d}.json', dict(update=update, topology=topology,
                    adapter_optimizer_rng_cursor_preserved=True, new_rank_rng='saved rank0 shadow',
                    numerical_path_bitwise_equal_to_single_rank=False, expanded_unix=time.time()))
                resumed_window = root / 'WINDOWS' / f'{update:09d}.json'
                archived = root / 'STOP_WINDOWS' / resumed_window.name
                archived.parent.mkdir(exist_ok=True)
                os.rename(resumed_window, archived)
            if not dev_plan or dev_done:
                ingest()
            write(root / 'WINDOWS' / f'{update:09d}.json', dict(start_update=update,
                end_update=next_end(), corpus_path=corpus_path,
                corpus_sha256=sha(root / corpus_path), stop=False))
            if expand:
                spawn(topology, update)
        for index in sorted({index for indexes in topology.values() for index in indexes}):
            report = run.scan(index, root / 'SERVICE_IDENTITY.json')
            write(root / f'TRAIN_RELEASE_{index}.json', report)
            assert report['clear']
        if not interrupted:
            if dev_plan:
                from gpu.orch_combined_l1_dev import launch as launch_dev
                launch_dev(root, 'TERMINAL', update, lifetime)
            else:
                from gpu.orch_combined_l1_continual_readout import launch_readouts
                launch_readouts(root, update, lifetime)
            status = 'COMPLETE'
    except BaseException as error:
        write(root / 'ABORT.json', dict(type=type(error).__name__, message=str(error), time_unix=time.time(),
            controller_session=controller_session))
        raise
    finally:
        for child, identity in children:
            run.common.stop_owned(child, identity)
        for log in logs:
            log.close()
        write(root / 'TERMINAL.json', dict(status=status, finished_unix=time.time(),
            conservative_gpu_hours=5 * (time.time() - original) / 3600,
            inherited_deadline=hard_end, old_math_not_stopped=True, retries=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--resume', type=int, default=0)
    parser.add_argument('--recover-partial', action='store_true')
    options = parser.parse_args()
    launch(options.root, options.resume, options.recover_partial)
