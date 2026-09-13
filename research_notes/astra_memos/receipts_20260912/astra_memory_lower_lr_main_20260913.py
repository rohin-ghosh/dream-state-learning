import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


specification = importlib.util.spec_from_file_location('lower_lr_previous_main', '/tmp/astra_memory_pairs_main_20260913.py')
previous = importlib.util.module_from_spec(specification)
specification.loader.exec_module(previous)
assert previous.digest(previous.__file__) == '5df4a3c00016ad07305658e2febc642a1182d1944106d70b92b463235ede2dbe'
BASE = Path('/tmp/astra_memory_lower_lr_specs_20260913_attempt1')
RUNNER = Path('/tmp/astra_memory_lower_lr_run_20260913.py')
RUNNER_SHA = '80467204aa7ccb4a1cbf4f8d85c7be4e7347263f98f4f7b8fef5739980fcf413'
GPUS = {0: (4, 'GPU-d304a15c-516a-16a0-a926-a560304077cc'),
        1: (5, 'GPU-0cc84073-37a0-4f7a-e555-11671425bd03'),
        2: (6, 'GPU-a064bca2-bddc-73ad-faf1-a4fbcb49fecf')}


def root_for(seed):
    return Path('/localhome/local-rohing/astra_diagnostics') / f'memory_lower_lr_seed{seed}_20260913_attempt1'


def runtime():
    return previous.load('lower_lr_candidate_runtime', RUNNER, RUNNER_SHA)


def specs():
    for seed, (index, uuid) in GPUS.items():
        upstream = json.loads((Path('/tmp/astra_post_memory_specs_20260913_attempt1') / f'seed{seed}.json').read_text())
        history = upstream['memory']
        spec = dict(runner_sha256=RUNNER_SHA, runtime=upstream['memory_runtime'],
                    design=dict(path='/tmp/astra_memory_retention_repair_design_20260913.md', sha256='98df5e78c53921e7dae5c0210800c4ae4f1a068da69b50a1d3bebd1986c4b60c'),
                    protocol=dict(path=str(BASE / 'protocol.md'), sha256='122965224f6a72d1fb852a40dd24c02b78c733751337f37513712f0f3b45bbce'),
                    history=dict(root=history['root'], plan_sha256=history['plan_sha256'],
                                 completion_sha256=history['completion_sha256'], collection=history['collection'],
                                 scores_sha256=history['scores']['sha256']),
                    seed=seed, fit_seed=seed, gpu_index=index, gpu_uuid=uuid,
                    expected_boot_id=upstream['expected_boot_id'], lease_end=upstream['lease_end'])
        path = BASE / f'seed{seed}.json'
        previous.write(path, spec)
        print(json.dumps(dict(seed=seed, spec_sha256=previous.digest(path))), flush=True)


def prepare(seed):
    path = BASE / f'seed{seed}.json'
    result = runtime().prepare(str(root_for(seed)), str(path), previous.digest(path), allow_native=True)
    assert result['status'] == 'NATIVE_CPU_PREPARED_NOT_LAUNCHED'
    assert result['updates'] == (112, 64, 64)[seed] and result['calls'] == (88, 76, 76)[seed]
    previous.write(BASE / f'seed{seed}_prepared.json', result)
    print(json.dumps(result), flush=True)


def launch(seed):
    candidate = runtime()
    batch = previous.load('lower_lr_reservations', '/tmp/astra_level1_next_batch_20260913.py', '03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2')
    prechecks = Path('/tmp/astra_level1_roster_20260913_attempt1/prechecks.json')
    assert previous.digest(prechecks) == '71e8eaa0c326ddef4414539684d20315e3752c48ce425a280438100e32815929'
    config = json.loads(prechecks.read_text())['node2']
    prepared = json.loads((BASE / f'seed{seed}_prepared.json').read_text())
    memory, plan, bound, history = candidate.verify(str(root_for(seed)), prepared['plan_sha256'])
    memory.offline()
    assert not (root_for(seed) / 'controller_started.json').exists()
    claim = Path(str(root_for(seed)) + '.launcher')
    claim.mkdir()
    process = None
    try:
        previous.write(claim / 'precheck.json', batch.reservations(config, plan['gpu_index'], plan['gpu_uuid']))
        assert bound['probe'].gpu_state(plan)
        memory.check_allocation(plan)
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'hold', '--seed', str(seed)]
        with (claim / 'stdout.log').open('xb') as output:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid']), start_new_session=True)
        result = dict(status='LAUNCHED_NOT_RESULT', seed=seed, root=str(root_for(seed)), pid=process.pid,
                      identity=batch.identity(Path('/proc') / str(process.pid)), started_unix=time.time(),
                      plan_sha256=prepared['plan_sha256'], gpu_index=plan['gpu_index'], gpu_uuid=plan['gpu_uuid'],
                      command=command, custodian_sha256=previous.digest(__file__), controller_seconds=3600)
        previous.write(claim / 'launched.json', result)
        print(json.dumps(result), flush=True)
    except BaseException as error:
        previous.write(claim / 'failure.json', dict(error=repr(error), controller_may_be_running=process is not None))
        raise


def hold(seed):
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == GPUS[seed][1] and previous.digest(RUNNER) == RUNNER_SHA
    prepared = json.loads((BASE / f'seed{seed}_prepared.json').read_text())
    claim = Path(str(root_for(seed)) + '.launcher')
    command = [sys.executable, '-B', str(RUNNER), 'controller', '--root', str(root_for(seed)),
               '--plan-sha256', prepared['plan_sha256'], '--allow-gpu']
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
    previous.write(claim / 'controller.json', dict(pid=process.pid, command=command, started_unix=time.time()))
    try:
        result = process.wait()
    except BaseException as error:
        previous.write(claim / 'holder_failure.json', dict(error=repr(error), controller_pid=process.pid, release_unknown=True))
        raise
    previous.write(claim / 'exit.json', dict(returncode=result, completed_unix=time.time()))
    sys.exit(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('specs', 'prepare', 'launch', 'hold'))
    parser.add_argument('--seed', type=int, choices=(0, 1, 2))
    args = parser.parse_args()
    if args.action == 'specs':
        specs()
    else:
        assert args.seed is not None
        globals()[args.action](args.seed)
