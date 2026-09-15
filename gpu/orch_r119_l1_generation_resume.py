"""Explicit generation-only lineage forks; frozen V3 loop, current C2 seed."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import FunctionType, SimpleNamespace

try:
    import orch_r109_l1_generation_v3 as generation
except ImportError:
    from gpu import orch_r109_l1_generation_v3 as generation
from gpu import orch_r109_l1_train as trainer
from gpu import orch_r109_l1_run as original


def identity(pid):
    directory = Path('/proc') / str(pid)
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, uid=directory.stat().st_uid, start_ticks=fields[19],
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def config(root):
    document = trainer.read(root / 'FORKS.json')
    assert trainer.sha(__file__) == document['wrapper_sha256']
    assert trainer.sha(generation.__file__) == document['generator_sha256']
    assert trainer.sha(generation.policy.__file__) == document['policy_sha256']
    assert document['hard_deadline_unix'] == document['lease_end_unix'] - 21600
    assert time.time() < document['hard_deadline_unix']
    allowed = {'a100': [2, 3, 4], 'ovx': list(range(8)), 'ovx2': [0]}
    assert document['lanes'] == allowed[document['node']]
    assert trainer.sha(Path(document['checkpoint']) / 'COMMIT.json') == document['checkpoint_commit_sha256']
    view_checkpoint = Path(document['origin_view']) / 'input' / 'checkpoint'
    assert not view_checkpoint.is_symlink(), 'checkpoint_view_must_be_physical'
    assert trainer.sha(view_checkpoint / 'COMMIT.json') == document['checkpoint_commit_sha256']
    metadata = trainer.storage.verify_checkpoint(view_checkpoint)['metadata']
    assert metadata['update'] == 15460
    assert metadata['adapter']['state_sha256'] == document['checkpoint_state_sha256']
    assert trainer.sha(Path(document['origin_view']) / 'TASKS.json') == document['tasks_sha256']
    return document


def execute(root, index, segment):
    document = config(root)
    assert index in document['lanes']
    stage = root / f'gpu{index}' / f'segment{segment:04d}'
    plan = trainer.read(stage / 'PLAN.json')
    assert os.environ['CUDA_VISIBLE_DEVICES'] == document['uuid_by_index'][index]
    prior_policy = trainer.policy

    def allocation(node, physical):
        assert node == document['node'] and physical == index and physical in document['lanes']
        return document['condition_positions'][str(index)]

    trainer.policy = SimpleNamespace(**dict(prior_policy.__dict__, allocation=allocation))
    context = dict(generation.__dict__, ROOT=stage, ORIGIN=Path(document['origin_view']),
                   END=document['hard_deadline_unix'], CUTOFF=document['hard_deadline_unix'], verify=lambda: plan)
    function = FunctionType(generation.generate.__code__, context, 'explicit_generation_fork', generation.generate.__defaults__)
    assert function.__code__ is generation.generate.__code__
    try:
        function(index)
    finally:
        trainer.policy = prior_policy


def scan(root, index):
    document = config(root)
    if document['node'] == 'ovx':
        from gpu.orch_rich_hot_node2_scan import scan as native_scan
        return native_scan(index, Path(document['service_identity']))
    if document['node'] == 'a100':
        if index in (2, 3):
            from gpu.orch_combined_l1_continual_run import scan as native_scan
        else:
            from gpu.orch_rich_hot_a100_minor_scan import scan as native_scan
        return native_scan(index, Path(document['service_identity']))
    result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + document['pythonpath'], 'python3', '-B', document['node3_scanner']],
        capture_output=True, text=True, check=True, timeout=90)
    return json.loads(result.stdout)


def supervise(root, index):
    import fcntl
    document = config(root)
    assert index in document['lanes']
    ready = trainer.read(root / 'PRE_GPU.json')
    assert ready['cpu_passed'] and ready['forks_sha256'] == trainer.sha(root / 'FORKS.json')
    assert ready['builder_line'].startswith('[Builder]')
    folder = root / f'gpu{index}'
    folder.mkdir(exist_ok=False)
    lock = (folder / 'OWNER.lock').open('x')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    trainer.write(folder / 'START.json', dict(identity=identity(os.getpid()), physical=index,
                   generation_only=True, parent_progress=document['predecessor_progress'],
                   counter_interpretation='NEW_EXPLICIT_FORK; SHARED_ANCESTRY_NOT_NEW_CALLS'))
    progress = dict(document['predecessor_progress'], batch=document['fork_batches'][str(index)], position=index % 2 - 2)
    segment = 0
    while time.time() < document['hard_deadline_unix']:
        stage = folder / f'segment{segment:04d}'
        stage.mkdir()
        plan = trainer.read(Path(document['prior_generator_plan']))
        plan.update(node=document['node'], lanes=[index], uuid_by_index=document['uuid_by_index'],
                    model_dir=document['model_dir'], generation_seed_unchanged=document['checkpoint_state_sha256'],
                    lifetime=dict(plan['lifetime'], hard_deadline_unix=document['hard_deadline_unix'],
                                  native_deadline_unix=document['hard_deadline_unix'], lease_end_unix=document['lease_end_unix']),
                    explicit_generation_fork=True, predecessor_progress=document['predecessor_progress'],
                    fork_wrapper_sha256=document['wrapper_sha256'], corpus_admission=False,
                    original_training_optimizer_untouched=True)
        trainer.write(stage / 'PLAN.json', plan)
        trainer.write(stage / f'RELEASE_{index}.json', dict(progress=progress, explicit_new_fork=True,
                      no_old_process_signals=True, all_predecessor_captures_preserved=True))
        while time.time() < document['hard_deadline_unix']:
            snapshot = scan(root, index)
            snapshot.pop('host', None)
            trainer.write(stage / f'ADMISSION_{time.time_ns()}.json', snapshot)
            if snapshot['clear']:
                assert snapshot['scanner_euid'] == 0 and snapshot['gpu']['uuid'] == document['uuid_by_index'][index]
                break
            trainer.write(folder / 'HEARTBEAT.json', dict(phase='WAIT_OWNERSHIP', physical=index,
                          blocking_reasons=snapshot['blocking_reasons'], observed_unix=time.time()))
            time.sleep(2)
        else:
            return
        command = [sys.executable, '-B', '-u', str(Path(__file__).resolve()), 'generate', '--root', str(root),
                   '--index', str(index), '--segment', str(segment)]
        with (stage / 'NATIVE.log').open('x') as log:
            child = subprocess.Popen(command, cwd=document['source_cwd'], stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True, env=dict(os.environ,
                CUDA_VISIBLE_DEVICES=document['uuid_by_index'][index], PYTHONPATH=document['pythonpath'],
                HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'))
        expected = identity(child.pid)
        trainer.write(stage / 'LAUNCH.json', dict(identity=expected, physical=index, actual_node=document['node'],
                      inherited_calls=progress['calls'], source_state=document['checkpoint_state_sha256'], observed_unix=time.time()))
        while child.poll() is None:
            trainer.write(folder / 'HEARTBEAT.json', dict(phase='generation', identity=expected, physical=index,
                          segment=segment, hard_deadline_unix=document['hard_deadline_unix'], observed_unix=time.time()))
            if time.time() >= document['hard_deadline_unix']:
                original.stop(child, expected, 'ACTUAL_LEASE_MINUS_ORIGINAL_6H_MARGIN')
                return
            time.sleep(3)
        trainer.write(stage / 'EXIT.json', dict(returncode=child.returncode, observed_unix=time.time()))
        assert child.returncode == 0, 'failed_generation_preserved_no_replay'
        progress = trainer.read(stage / f'gpu{index}' / 'PROGRESS.json')
        segment += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check', 'supervise', 'generate'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--index', type=int)
    parser.add_argument('--segment', type=int, default=0)
    options = parser.parse_args()
    if options.action == 'check':
        document = config(options.root)
        metadata = trainer.storage.verify_checkpoint(Path(document['checkpoint']))['metadata']
        assert metadata['update'] == 15460 and metadata['adapter']['state_sha256'] == document['checkpoint_state_sha256']
        print(json.dumps(dict(status='CPU_PROVENANCE_PASS', node=document['node'], lanes=document['lanes'],
                              seed_update=15460, optimizer_count=0, hard_deadline_unix=document['hard_deadline_unix'])))
    elif options.action == 'supervise':
        supervise(options.root, options.index)
    else:
        execute(options.root, options.index, options.segment)
