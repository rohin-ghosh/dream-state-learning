"""One bounded same-state R107 continuation; immutable native trainer reused."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import orch_combined_l1_continual_run as run
from gpu import orch_combined_l1_continual_guard as guard
from gpu import orch_combined_l1_dev as dev
from organism_v6 import orch_combined_l1_continual as policy


UPDATE = 6628
SOURCE = '4859efad8a0a26ed8de120ed42fa9ac7c74d5d75786447ac9c6a255cc2c86a55'
CORPUS = 'ee2aa551ae71d271bc6cbf2101dcfef4a708f6d031fe4f2dbbd2c161dd09ce19'
COMMITS = {'FULL': '011513aaa0c9e26138ff51ccea1b737293a2427313a76b6b5144e116a3d4f580',
           'OFF': '94affb7b6cf7d082f3dbd4fb3a3a96c9cbe153a48a1580773a4c55e2d66a75e6'}
SEGMENT = 'R107_CONTINUATION_20260915'


def settling_only(report):
    reasons = report['blocking_reasons']
    transient = ('process_identity_drift:', 'minor_scan_identity_changed:', 'minor_scan_process_drift:')
    return (bool(reasons) and report['gpu']['memory_used_mib'] == 0
        and all(reason == 'device_not_idle' or reason.startswith(transient) for reason in reasons)
        and not any(entry['gpu_uuid'] == report['gpu']['uuid'] for entry in report['compute_processes']))


def admit(root, indexes, label):
    for index in indexes:
        for attempt in range(60):
            report = run.scan(index, root/'SERVICE_IDENTITY.json')
            run.write(root/SEGMENT/'ADMISSIONS'/f'{label}_{index}_{attempt:03d}.json', report)
            if report['clear']:
                assert not report['blocking_reasons']
                break
            assert settling_only(report), ('actual_gpu_ownership_or_memory_block', index, report['blocking_reasons'])
            assert attempt < 59, 'strict_clear_not_obtained'
            time.sleep(1)


def utc(value):
    return datetime.fromisoformat(value).timestamp()


def continuation_clock(previous, now, lease_end):
    training = utc('2026-09-15T08:00:00+00:00')
    hard = utc('2026-09-15T09:03:00+00:00')
    assert now < training - 600, 'not_enough_bounded_training_time'
    assert hard <= lease_end - 21600 and 5 * (hard - now) / 3600 <= 10
    return dict(previous, training_deadline_unix=training, native_deadline_unix=hard-180,
        hard_deadline_unix=hard, continuation_started_unix=now, continuation_gpu_hours_ceiling=10,
        continuation_segment=SEGMENT, continuation_once=True, terminal_calls_remaining=416,
        total_readout_calls_including_base=1824, extra_physical_off_recovery_updates=117,
        previous_lifetime_preserved=True, accounting='Prior segment retained separately; this segment <=10 GPUh.')


def no_own_workers(root):
    found = []
    for folder in Path('/proc').glob('[0-9]*'):
        try:
            arguments = (folder / 'cmdline').read_bytes().split(b'\0')
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            continue
        if str(root).encode() in arguments and any(name in arguments for name in (
                run.PROGRAM.encode(), b'gpu.orch_combined_l1_continual_guard', b'gpu.orch_combined_l1_dev')):
            found.append(folder.name)
    assert not found, ('existing_own_native_or_guard', found)


def validate(root):
    prepared = run.validate(root)
    assert prepared['source_sha256'] == SOURCE
    manifests = []
    for arm in policy.ARMS:
        checkpoint = root / arm / 'checkpoints' / f'{UPDATE:09d}'
        assert run.sha(checkpoint / 'COMMIT.json') == COMMITS[arm]
        manifests.append(policy.verify_checkpoint(checkpoint))
    full, off = [entry['metadata'] for entry in manifests]
    assert policy.pair_boundary(full, off) == UPDATE
    assert full['corpus_version'] == 13 and full['corpus_sha256'] == CORPUS
    assert run.sha(root / 'CORPORA/000013.json') == CORPUS
    assert len(run.read(root / 'CORPORA/000013.json')['rows']) == 3635
    assert [full['world_size'], off['world_size']] == [3, 2]
    assert all(entry['metadata']['source_sha256'] == SOURCE for entry in manifests)
    assert not list((root / 'ADAPTIVE_DEV').glob('TERMINAL_*/*/*/readout/CALL_*.json'))
    assert not list((root / 'ADAPTIVE_DEV').glob('TERMINAL_*/*_START.json'))
    assert run.read(root / 'WINDOWS' / f'{UPDATE:09d}.json')['stop'] is True
    assert run.read(root / 'TERMINAL.json')['status'] == 'TRAINING_CHECKPOINTED'
    no_own_workers(root)
    return dict(status='PASS', update=UPDATE, commits=COMMITS, source_sha256=SOURCE,
        corpus_sha256=CORPUS, corpus_version=13, rows=3635, topology=run.TOPOLOGY,
        optimizer_rng_cursor_exposures_retained=True, extra_physical_off_recovery_updates=117,
        full_adapter=full['adapter'], off_adapter=off['adapter'], native_calls=0,
        terminal_readout_calls_remaining=416, checked_unix=time.time())


def prepare(root, cpu_log):
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = validate(root)
    directory = root / SEGMENT
    directory.mkdir(exist_ok=False)
    receipt.update(controller_sha256=run.sha(__file__), cpu_log_sha256=run.sha(cpu_log),
        lifetime=continuation_clock(run.read(root / 'LIFETIME.json'), time.time(), run.LEASE_END))
    run.write(directory / 'READY.json', receipt)
    return receipt


def launch(root):
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '' and os.geteuid() != 0
    directory = root / SEGMENT
    ready = run.read(directory / 'READY.json')
    publication = run.read(directory / 'PUBLICATION.json')
    assert ready['controller_sha256'] == run.sha(__file__)
    assert publication['ready_sha256'] == run.sha(directory / 'READY.json')
    assert publication['board_logged'] and publication['coordination_logged']
    assert publication['topology'] == {arm:list(indexes) for arm,indexes in run.TOPOLOGY.items()}
    validate(root)
    assert not (directory / 'STARTED.json').exists(), 'one_continuation_no_restart'
    previous = run.read(root / 'LIFETIME.json')
    lifetime = continuation_clock(previous, time.time(), run.LEASE_END)
    with (directory / 'STARTED.json').open('x') as stream:
        stream.write('{}')
    run.write(directory / 'PRIOR_LIFETIME.json', previous)
    for name in ('TERMINAL.json', 'ABORT.json'):
        if (root / name).exists():
            run.write(directory / ('PRIOR_' + name), run.read(root / name))
    admit(root, sorted(run.DEVICES), 'R107_PRELAUNCH')
    run.write(root / 'LIFETIME.json', lifetime)
    stopped = root / 'WINDOWS' / f'{UPDATE:09d}.json'
    os.rename(stopped, directory / 'PRIOR_STOP_WINDOW.json')
    update, corpus_path = UPDATE, 'CORPORA/000013.json'
    corpus = run.read(root / corpus_path)
    session = f'{os.getpid()}:{time.time_ns()}'
    children, logs = [], []
    stopping = False
    status = 'FAILED'
    def interrupt(signum, frame):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGINT, interrupt)
    def window():
        run.write(root / 'WINDOWS' / f'{update:09d}.json', dict(start_update=update,
            end_update=update+128, corpus_path=corpus_path, corpus_sha256=run.sha(root / corpus_path), stop=False))
    try:
        window()
        for arm, indexes in run.TOPOLOGY.items():
            address = guard.port()
            for rank, index in enumerate(indexes):
                command = [run.PYTHON, '-B', '-m', run.PROGRAM, 'train', '--root', str(root),
                    '--arm', arm, '--rank', str(rank), '--port', str(address), '--world-size', str(len(indexes)),
                    '--index', str(index), '--resume', str(root / arm / 'checkpoints' / f'{UPDATE:09d}')]
                stream = (directory / f'{arm}_rank{rank}.log').open('x')
                logs.append(stream)
                child = subprocess.Popen(command, cwd=root/'source', stdout=stream, stderr=subprocess.STDOUT,
                    start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=run.DEVICES[index],
                        CONTINUAL_CONTROLLER_SESSION=session, PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2',
                        TOKENIZERS_PARALLELISM='false'))
                identity = run.common.process_identity(child.pid)
                children.append((child, identity))
                run.write(directory/f'{arm}_RANK{rank}_START.json', dict(pid=child.pid, identity=identity,
                    index=index, command=command, resume_update=UPDATE, started_unix=time.time()))
        while True:
            target = update+128
            paths = [root/arm/'checkpoints'/f'{target:09d}' for arm in policy.ARMS]
            while not all((path/'COMMIT.json').exists() for path in paths):
                assert time.time() < lifetime['native_deadline_unix'], 'bounded_native_deadline'
                assert all(child.poll() is None for child, identity in children), 'native_worker_failed_no_retry'
                time.sleep(1)
            full, off = [policy.verify_checkpoint(path)['metadata'] for path in paths]
            assert policy.pair_boundary(full, off) == target
            update = target
            run.write(root/'PAIRED_BOUNDARIES'/f'{update:09d}.json', dict(update=update,
                corpus_sha256=full['corpus_sha256'], corpus_version=full['corpus_version'],
                full_sha256=run.sha(paths[0]/'COMMIT.json'), off_sha256=run.sha(paths[1]/'COMMIT.json'),
                reference_tokens=full['reference_tokens'], full_supervised=full['supervised_tokens'],
                off_supervised=off['supervised_tokens'], topology=run.TOPOLOGY, time_unix=time.time(), segment=SEGMENT))
            if stopping or time.time() >= lifetime['training_deadline_unix']:
                run.write(root/'WINDOWS'/f'{update:09d}.json', dict(stop=True, reason='R107_BOUNDED_COMPLETION'))
                for child, identity in children:
                    assert child.wait(timeout=90) == 0
                status = 'TRAINING_CHECKPOINTED'
                break
            newer = guard.take_batch(root, corpus)
            if newer is not corpus:
                corpus = newer
                corpus_path = f'CORPORA/{corpus["version"]:06d}.json'
                assert not (root/corpus_path).exists()
                run.write(root/corpus_path, corpus)
                run.write(root/'INGEST_RECEIPTS'/f'{update:09d}.json', dict(update=update, rows=len(corpus['rows']),
                    corpus_path=corpus_path, corpus_sha256=run.sha(root/corpus_path), ingested=corpus['ingested'],
                    duplicates=corpus['duplicates'], reset=False, optimizer_retained=True, time_unix=time.time()))
            window()
        admit(root, sorted(run.DEVICES), 'R107_TRAIN_RELEASE')
        run.write(directory/'READOUT_SEAM.json', dict(update=update, checkpoint_paths={arm:
            str(root/arm/'checkpoints'/f'{update:09d}') for arm in policy.ARMS}, calls_remaining=416,
            independent_capability_calls=0, time_unix=time.time()))
        if not stopping:
            previous_admit = guard.admit_devices
            guard.admit_devices = admit
            try:
                dev.launch(root, 'TERMINAL', update, lifetime)
            finally:
                guard.admit_devices = previous_admit
            status = 'COMPLETE'
    except BaseException as error:
        run.write(directory/'FAILED.json', dict(type=type(error).__name__, message=str(error), time_unix=time.time()))
        run.write(root/'ABORT.json', dict(controller_session=session, type=type(error).__name__, message=str(error)))
        raise
    finally:
        for child, identity in children:
            run.common.stop_owned(child, identity)
        for stream in logs:
            stream.close()
        run.write(directory/'TERMINAL.json', dict(status=status, update=update, finished_unix=time.time(),
            additional_gpu_hours=5*(time.time()-lifetime['continuation_started_unix'])/3600,
            old_off_extra_physical_updates=117, automatic_further_extension=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare','launch'))
    parser.add_argument('--root', type=Path, default=run.ROOT)
    parser.add_argument('--cpu-log', type=Path)
    args = parser.parse_args()
    if args.phase == 'prepare':
        prepare(args.root, args.cpu_log)
    else:
        launch(args.root)
