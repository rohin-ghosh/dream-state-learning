import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


BASE = Path('/tmp/astra_memory_pairs_20260913_attempt1')
RUNNER = Path('/tmp/astra_real_record_memory_run_20260913.py')
RUNNER_SHA = '7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e'
PROTOCOL = BASE / 'protocol.md'
GPUS = {0: (1, 'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4'),
        1: (2, 'GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05'),
        2: (3, 'GPU-c9450d3d-0455-f034-b9bf-7f8956e44733')}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write('\n')


def load(name, path, expected):
    assert digest(path) == expected
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def root_for(seed):
    return Path('/localhome/local-rohing/astra_diagnostics') / f'real_record_memory_seed{seed}_20260913_attempt1'


def make_specs():
    assert digest(PROTOCOL) == 'c056a0fb6c97d1ba93b4d2a0fa07cb70f806cfa64fef2df1769d78e80334a716'
    for seed, (index, uuid) in GPUS.items():
        specification = dict(
            runner_sha256=RUNNER_SHA,
            memory=dict(path='/tmp/astra_real_record_memory_core_20260913.py', sha256='2c5538f5b63cbb4e592f40822561b4d62595ab3c9d7d193f084b91f9a064e8ef'),
            formation_runtime=dict(path='/tmp/astra_level1_real_record_run_20260913.py', sha256='3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e'),
            formation=dict(root='/localhome/local-rohing/astra_diagnostics/level1_real_record_20260913_attempt2',
                           plan_sha256='039f8cc66ecae40ed9cbee649011b34e4e4654fec68f5e7d51a37f5a5a5374bd',
                           completion_sha256='51b09f9a553cfe561ae8613e299a6d4926d8df3286265498927573b41dae1274',
                           collection=dict(path='/localhome/local-rohing/astra_diagnostics/level1_real_record_20260913_attempt2_collected/collection.json', sha256='77260fe6d540beb65cd4f9717a76fc827cb3e441a23663077f72dbdbd7a70a4c')),
            protocol=dict(path=str(PROTOCOL), sha256=digest(PROTOCOL)), seed=seed, fit_seed=seed,
            gpu_index=index, gpu_uuid=uuid, expected_boot_id='8ff7b0dc-fbdf-4945-9044-3dffe94b5407',
            lease_end=datetime(2026, 9, 21, 8, 43, tzinfo=timezone.utc).timestamp())
        path = BASE / f'seed{seed}.json'
        write(path, specification)
        print(json.dumps(dict(seed=seed, spec=str(path), spec_sha256=digest(path), root=str(root_for(seed)))), flush=True)


def prepare(seed):
    runtime = load('memory_main_runtime', RUNNER, RUNNER_SHA)
    runtime.offline()
    spec = BASE / f'seed{seed}.json'
    result = runtime.prepare(str(root_for(seed)), str(spec), digest(spec), allow_native=True)
    assert result['status'] == 'NATIVE_CPU_PREPARED_NOT_LAUNCHED'
    assert result['admitted'] == (14, 8, 8)[seed]
    assert result['updates'] == (224, 128, 128)[seed]
    assert result['calls'] == (176, 152, 152)[seed]
    write(BASE / f'seed{seed}_prepared.json', result)
    print(json.dumps(result), flush=True)


def launch(seed):
    runtime = load('memory_main_runtime', RUNNER, RUNNER_SHA)
    batch = load('memory_main_reservations', '/tmp/astra_level1_next_batch_20260913.py', '03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2')
    prechecks = Path('/tmp/astra_level1_roster_20260913_attempt1/prechecks.json')
    assert digest(prechecks) == '71e8eaa0c326ddef4414539684d20315e3752c48ce425a280438100e32815929'
    config = json.loads(prechecks.read_text())['node2']
    prepared = json.loads((BASE / f'seed{seed}_prepared.json').read_text())
    root = root_for(seed)
    assert not (root / 'controller_started.json').exists()
    runtime.offline()
    plan, bound = runtime.verify(root, prepared['plan_sha256'], native=False)
    claim = Path(str(root) + '.launcher')
    claim.mkdir()
    process = None
    try:
        write(claim / 'precheck.json', batch.reservations(config, plan['gpu_index'], plan['gpu_uuid']))
        assert bound['probe'].gpu_state(plan)
        runtime.check_allocation(plan)
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'hold', '--seed', str(seed)]
        with (claim / 'stdout.log').open('xb') as output:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid']), start_new_session=True)
        result = dict(status='LAUNCHED_NOT_RESULT', seed=seed, root=str(root), pid=process.pid,
                      identity=batch.identity(Path('/proc') / str(process.pid)), started_unix=time.time(),
                      gpu_index=plan['gpu_index'], gpu_uuid=plan['gpu_uuid'], plan_sha256=prepared['plan_sha256'],
                      command=command, custodian_sha256=digest(__file__), controller_seconds=3600)
        write(claim / 'launched.json', result)
        print(json.dumps(result), flush=True)
    except BaseException as error:
        write(claim / 'failure.json', dict(error=repr(error), controller_may_be_running=process is not None))
        raise


def hold(seed):
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == GPUS[seed][1]
    assert digest(RUNNER) == RUNNER_SHA
    prepared = json.loads((BASE / f'seed{seed}_prepared.json').read_text())
    command = [sys.executable, '-B', str(RUNNER), 'controller', '--root', str(root_for(seed)),
               '--plan-sha256', prepared['plan_sha256'], '--allow-gpu']
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
    write(Path(str(root_for(seed)) + '.launcher') / 'controller.json', dict(pid=process.pid, command=command, started_unix=time.time()))
    result = process.wait()
    write(Path(str(root_for(seed)) + '.launcher') / 'exit.json', dict(returncode=result, completed_unix=time.time()))
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
