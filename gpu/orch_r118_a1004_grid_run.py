"""Scoped A100 physical4 portability for the unchanged resident R115 BASE grid."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time
from types import SimpleNamespace

from gpu import orch_r115_grid_native as grid
from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA, LEASE_END
from gpu.orch_r111_grid_prepare import MODEL, BUNDLE


ROOT = Path('/localhome/local-rohing/orch_r118_a1004_grid_20260915_attempt1')
SOURCE = Path(__file__).resolve().parents[1]
HOST_SHA = '6bcd6b8370cc2f2a15e1e488352b4cec96b1e137489d52c3324c199536a09ba8'
UUID = 'GPU-31583768-d90f-520c-51ed-5dac761526d0'
LIFE_ID = 'R118_A1004_ASTRA'
MANIFEST = 'R118_SOURCE_SHA256.json'
require = grid.require


def allocation(physical):
    require(physical == 4, 'only_explicitly_allocated_A100_physical4')


def validate(root, gpu=False):
    require(root == ROOT and root.resolve() == root, 'exact_new_root')
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'exact_A100_host')
    config = grid.read(root / 'CONFIG.json')
    allocation(config['physical'])
    require(config['root'] == str(root) and config['uuid'] == UUID and config['life_id'] == LIFE_ID,
            'exact_A1004_identity')
    require(time.time() < grid.END <= LEASE_END - 21600 and config['hard_end_unix'] == grid.END
            and config['lease_end_unix'] == LEASE_END, 'inherited_end_and_verified_lease_margin')
    require(grid.sha(SOURCE / MANIFEST) == config['source_manifest_sha256'], 'source_manifest_binding')
    for name, expected in grid.read(SOURCE / MANIFEST).items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
                and grid.sha(SOURCE / name) == expected, 'immutable_native_source:' + name)
    for name, expected in config['inputs'].items():
        require(grid.sha(root / name) == expected, 'immutable_input:' + name)
    require(config['base_sha256'] == grid.policy.game.BASE_SHA and config['optimizer_steps'] == 0,
            'frozen_BASE_elicitation_only')
    require(grid.sha(SOURCE / 'research_notes/R114_SHARED_JUDGE_PROMPT.md') == grid.JUDGE_SHA, 'same_judge')
    if gpu:
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == UUID and
                ('CUDA_VISIBLE_DEVICES=' + UUID).encode() in
                Path('/proc/self/environ').read_bytes().split(b'\0'), 'initial_assigned_UUID_only')
    return config


def scan(root):
    require(root == ROOT, 'exact_new_root')
    if os.geteuid() != 0:
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + str(SOURCE), 'python3', '-B', '-m', 'gpu.orch_r118_a1004_grid_run',
            'scan', '--root', str(root)]
        return json.loads(subprocess.check_output(command, text=True, timeout=100))
    grid.admission.minor.pinned.policy = SimpleNamespace(DEVICES={4: UUID}, HOST_SHA=HOST_SHA,
        require=require, allocation=allocation)
    return grid.admission.scan(4, root / 'SERVICE_IDENTITY.json')


def command(mode, root, *extra):
    return [grid.PYTHON, '-B', '-m', 'gpu.orch_r118_a1004_grid_run', mode,
            '--root', str(root), *extra]


def spawn_readout(root, cycle, scope):
    path = root / 'readout_logs' / f'{cycle:04d}_{scope}.log'
    path.parent.mkdir(exist_ok=True)
    with path.open('x') as stream:
        result = subprocess.run(command('readout', root, '--cycle', str(cycle), '--scope', scope),
            cwd=SOURCE, stdout=stream, stderr=subprocess.STDOUT)
    require(result.returncode == 0, 'readout_failure_preserved:' + scope)


def install_portability():
    grid.validate = validate
    grid.spawn_readout = spawn_readout


def prepare(root):
    import torch
    require(root == ROOT and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
            and not torch.cuda.is_initialized() and not (root / 'CONFIG.json').exists(), 'fresh_CPU_only')
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'exact_A100_host')
    broker_config = grid.read(root / 'BROKER_CONFIG.json')
    grid.broker.validate_config(broker_config)
    require(broker_config['remote_root'] == str(root) and broker_config['life_id'] == LIFE_ID,
            'new_parent_queue_binding')
    tasks = {split: grid.read(root / (split + '.json')) for split in ('TRAIN', 'DEV', 'FINAL')}
    require(grid.policy.digest(tasks) == broker_config['cohort_sha256'], 'same_frozen_grid_cohort')
    require(broker_config['train_tasks'] == {task['id']: task['task_sha256'] for task in tasks['TRAIN']}
            and set(broker_config['excluded_task_ids']) ==
            {task['id'] for split in ('DEV', 'FINAL') for task in tasks[split]}, 'exact_train_held_registry')
    base = grid.original.portable.verify_base_files(BUNDLE, MODEL, expected_manifest_sha256=BUNDLE_SHA)
    require(base['expected_base_sha256'] == grid.policy.game.BASE_SHA, 'original_BASE_files')
    tokenizer = grid.original.portable.source.native.load_local_tokenizer(MODEL)
    lengths = []
    for split, group in tasks.items():
        for task in group:
            prompt = [dict(role='system', content=grid.EPISODE if split == 'TRAIN' else grid.policy.HELD_PROMPT),
                dict(role='user', content=json.dumps(grid.policy.public_observation(task,
                    grid.policy.game.initial(task)), sort_keys=True))]
            lengths.append(len(tokenizer.apply_chat_template(prompt, tokenize=True,
                add_generation_prompt=True, return_dict=False)))
    legacy = grid.read(root / 'LEGACY_READOUT.json')
    from gpu import astra_goal_quality_train as legacy_source
    require(len(legacy['old_bank']) == 16, 'same_legacy16')
    prompts = [legacy_source.memory.memory_messages(item['event'], 0) for item in legacy['old_bank']]
    prompts += [legacy_source.memory.audit._messages(next(case for case in legacy['held']['cases']
                if case['kind'] == kind), False) for kind in ('true', 'fault')]
    lengths += [len(tokenizer.apply_chat_template(prompt, tokenize=True,
                add_generation_prompt=True, return_dict=False)) for prompt in prompts]
    require(all(0 < length + 2048 <= 16384 for length in lengths), 'native_uncropped_context')
    config = dict(schema='R118_A1004_GRID_V1', root=str(root), life_id=LIFE_ID, physical=4, uuid=UUID,
        parent_model='openai/openai/gpt-6-astra', model_dir=MODEL, base_sha256=grid.policy.game.BASE_SHA,
        optimizer_steps=0, lambda_rehearsal='N/A_FROZEN_BASE_NO_SLEEP', cohort_sha256=grid.policy.digest(tasks),
        split_sha256={split: grid.policy.digest(group) for split, group in tasks.items()},
        inputs={name: grid.sha(root / name) for name in ('TRAIN.json', 'DEV.json', 'FINAL.json',
            'LEGACY_READOUT.json', 'SERVICE_IDENTITY.json', 'BROKER_CONFIG.json', 'BROKER_LAUNCH.json')},
        source_manifest_sha256=grid.sha(SOURCE / MANIFEST), max_native=grid.MAX_NATIVE,
        max_parent=grid.MAX_PARENT, train_end_unix=grid.TRAIN_END, hard_end_unix=grid.END,
        lease_end_unix=LEASE_END, morning_final_unix=grid.policy.FINAL_UNIX,
        role='EXTRA_ASTRA_GRID_NOT_F4_A4_MATCHED_PAIR', prepared_unix=time.time())
    grid.write(root / 'CONFIG.json', config)
    for name in ('calls', 'readout_calls', 'sealed_readout_calls', 'parent_queue'):
        (root / name).mkdir(mode=0o700)
    validate(root)
    grid.write(root / 'CPU_READY.json', dict(base=base, config=grid.ref(root / 'CONFIG.json'),
        context_min=min(lengths), context_max=max(lengths), model_loaded=False,
        CUDA_initialized=torch.cuda.is_initialized(), optimizer_steps=0, native_calls=0, parent_calls=0))
    return grid.ref(root / 'CPU_READY.json')


def guard(root):
    validate(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_guard')
    (root / 'GUARD_ONCE').mkdir()
    try:
        publication = grid.read(root / 'PUBLICATION.json')
        require(publication['own_CPU_passed'] and publication['dated_builder']
                and publication['R118_allocation'], 'own_provenance_publication')
        for attempt in range(120):
            report = scan(root)
            grid.write(root / 'admission' / f'{attempt:03d}.json', report)
            if report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']:
                break
            time.sleep(2)
        else:
            raise ValueError('strict_assigned_GPU_admission_not_clear')
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=UUID, PYTHONPATH=str(SOURCE),
            PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        argv = ['timeout', '--signal=TERM', '--kill-after=5s', str(int(grid.END - time.time() - 5)) + 's',
                *command('resident', root)]
        with (root / 'NATIVE.log').open('x') as stream:
            process = subprocess.Popen(argv, cwd=SOURCE, env=environment, stdout=stream,
                stderr=subprocess.STDOUT, start_new_session=True)
        grid.write(root / 'LAUNCH.json', dict(pid=process.pid, command=argv, started_unix=time.time()))
        code = process.wait()
        grid.write(root / 'TERMINAL.json', dict(status='COMPLETE' if code == 0 else 'FAILED',
            exit_code=code, finished_unix=time.time()))
    except BaseException as error:
        if not (root / 'TERMINAL.json').exists():
            grid.write(root / 'TERMINAL.json', dict(status='FAILED', error_type=type(error).__name__,
                error=str(error), finished_unix=time.time()))
        raise
    finally:
        grid.write(root / 'FINAL_RELEASE.json', scan(root))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'scan', 'guard', 'resident', 'readout'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--cycle', type=int)
    parser.add_argument('--scope')
    args = parser.parse_args()
    install_portability()
    if args.mode in ('prepare', 'scan'):
        print(json.dumps((prepare if args.mode == 'prepare' else scan)(args.root), sort_keys=True))
    elif args.mode == 'readout':
        grid.readout(args.root, args.cycle, args.scope)
    else:
        (guard if args.mode == 'guard' else grid.resident)(args.root)
