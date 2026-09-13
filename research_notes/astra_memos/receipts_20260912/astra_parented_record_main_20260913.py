import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


specification = importlib.util.spec_from_file_location('parented_main_previous', '/tmp/astra_memory_pairs_main_20260913.py')
previous = importlib.util.module_from_spec(specification)
specification.loader.exec_module(previous)
assert previous.digest(previous.__file__) == '5df4a3c00016ad07305658e2febc642a1182d1944106d70b92b463235ede2dbe'
BASE = Path('/tmp/astra_parented_record_specs_20260913_attempt1')
RUNNER = Path('/tmp/astra_parented_record_run_20260913.py')
RUNNER_SHA = '54cad8a6eeb5ae8af08213efe60f4c8047879991ca77f7a30d8be548659699f8'
SOURCE = '/tmp/astra_level1_real_record_source_20260913_attempt1'
GPUS = {0: (3, 'GPU-c9450d3d-0455-f034-b9bf-7f8956e44733'),
        1: (4, 'GPU-d304a15c-516a-16a0-a926-a560304077cc'),
        2: (5, 'GPU-0cc84073-37a0-4f7a-e555-11671425bd03')}


def root_for(seed):
    return Path('/localhome/local-rohing/astra_diagnostics') / f'parented_record_seed{seed}_20260913_attempt1'


def runtime():
    return previous.load('parented_main_runtime', RUNNER, RUNNER_SHA)


def make_specs():
    candidate = runtime()
    assert previous.digest(BASE / 'prior_ids.json') == '1d4d9b4b4122de32bd3bab5bd4157c338fe4e58879f5652636dd7085888fceaf'
    for seed, (index, uuid) in GPUS.items():
        inherited = json.loads((Path('/tmp/astra_memory_lower_lr_specs_20260913_attempt1') / f'seed{seed}.json').read_text())
        spec = dict(runner_sha256=RUNNER_SHA,
                    core=dict(path='/tmp/astra_parented_record_core_20260913.py', sha256=candidate.CORE_PIN),
                    protocol=dict(path=str(BASE / 'protocol.md'), sha256=candidate.PROTOCOL_PIN),
                    memory_runtime=dict(path='/tmp/astra_real_record_memory_run_20260913.py', sha256=candidate.MEMORY_PIN),
                    lower_runtime=dict(path='/tmp/astra_memory_lower_lr_run_20260913.py', sha256=candidate.LOWER_PIN),
                    memory=dict(root=inherited['history']['root'], plan_sha256=inherited['history']['plan_sha256']),
                    prior_episode_ids=dict(path=str(BASE / 'prior_ids.json'), sha256=previous.digest(BASE / 'prior_ids.json')),
                    seed=seed, gpu_index=index, gpu_uuid=uuid, expected_boot_id=inherited['expected_boot_id'], lease_end=inherited['lease_end'])
        path = BASE / f'seed{seed}.json'
        previous.write(path, spec)
        candidate.validate_spec(spec)
        print(json.dumps(dict(seed=seed, spec_sha256=previous.digest(path))), flush=True)


def prepare(seed):
    candidate = runtime()
    path = BASE / f'seed{seed}.json'
    result = candidate.prepare(str(root_for(seed)), str(path), previous.digest(path), allow_native=True)
    assert result['status'] == 'PREPARED_NOT_LAUNCHED'
    previous.write(BASE / f'seed{seed}_prepared.json', result)
    print(json.dumps(result), flush=True)


def launch(seed):
    candidate = runtime()
    candidate.runtime().offline()
    batch = previous.load('parented_reservations', '/tmp/astra_level1_next_batch_20260913.py', '03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2')
    prechecks = Path('/tmp/astra_level1_roster_20260913_attempt1/prechecks.json')
    assert previous.digest(prechecks) == '71e8eaa0c326ddef4414539684d20315e3752c48ce425a280438100e32815929'
    config = json.loads(prechecks.read_text())['node2']
    prepared = json.loads((BASE / f'seed{seed}_prepared.json').read_text())
    plan, bound = candidate.verify(str(root_for(seed)), prepared['plan_sha256'])
    assert not (root_for(seed) / 'controller_started.json').exists()
    candidate.check_allocation(plan['specification'])
    claim = Path(str(root_for(seed)) + '.launcher')
    claim.mkdir()
    process = None
    try:
        previous.write(claim / 'precheck.json', batch.reservations(config, plan['gpu_index'], plan['gpu_uuid']))
        assert bound['probe'].gpu_state(plan) is True
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'hold', '--seed', str(seed)]
        with (claim / 'stdout.log').open('xb') as output:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid'], PYTHONPATH=SOURCE), start_new_session=True)
        result = dict(status='LAUNCHED_NOT_RESULT', seed=seed, root=str(root_for(seed)), pid=process.pid,
                      identity=batch.identity(Path('/proc') / str(process.pid)), started_unix=time.time(),
                      gpu_index=plan['gpu_index'], gpu_uuid=plan['gpu_uuid'], plan_sha256=prepared['plan_sha256'],
                      command=command, custodian_sha256=previous.digest(__file__), automatic_once_collection=True,
                      deadline_monotonic=plan['deadline_monotonic'])
        previous.write(claim / 'launched.json', result)
        print(json.dumps(result), flush=True)
    except BaseException as error:
        previous.write(claim / 'failure.json', dict(error=repr(error), controller_may_be_running=process is not None))
        raise


def hold(seed):
    runtime()
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == GPUS[seed][1]
    prepared = json.loads((BASE / f'seed{seed}_prepared.json').read_text())
    root = root_for(seed)
    claim = Path(str(root) + '.launcher')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=SOURCE)
    command = [sys.executable, '-B', str(RUNNER), 'controller', '--root', str(root),
               '--plan-sha256', prepared['plan_sha256'], '--allow-gpu']
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, env=environment, start_new_session=True)
    previous.write(claim / 'controller.json', dict(pid=process.pid, pgid=process.pid, command=command, started_unix=time.time()))
    result = process.wait()
    previous.write(claim / 'controller_exit.json', dict(returncode=result, completed_unix=time.time()))
    if result == 0:
        complete = root / 'capture_complete.json'
        command = [sys.executable, '-B', str(RUNNER), 'collect', '--root', str(root), '--plan-sha256', prepared['plan_sha256'],
                   '--completion-sha256', previous.digest(complete), '--out', str(root) + '_collected']
        collector = subprocess.Popen(command, stdin=subprocess.DEVNULL, env=environment, start_new_session=True)
        previous.write(claim / 'collector.json', dict(pid=collector.pid, command=command, started_unix=time.time()))
        result = collector.wait()
        previous.write(claim / 'collector_exit.json', dict(returncode=result, completed_unix=time.time()))
    previous.write(claim / 'exit.json', dict(returncode=result, completed_unix=time.time()))
    sys.exit(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('specs', 'prepare', 'launch', 'hold'))
    parser.add_argument('--seed', type=int, choices=(0, 1, 2))
    options = parser.parse_args()
    if options.action == 'specs':
        make_specs()
    else:
        assert options.seed is not None
        globals()[options.action](options.seed)
