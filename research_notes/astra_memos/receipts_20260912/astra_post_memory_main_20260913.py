import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import importlib.util


specification = importlib.util.spec_from_file_location('memory_previous_main', '/tmp/astra_memory_pairs_main_20260913.py')
previous = importlib.util.module_from_spec(specification)
specification.loader.exec_module(previous)
assert previous.digest(previous.__file__) == '5df4a3c00016ad07305658e2febc642a1182d1944106d70b92b463235ede2dbe'
BASE = Path('/tmp/astra_post_memory_specs_20260913_attempt1')
RUNNER = Path('/tmp/astra_post_memory_formation_run_20260913.py')
RUNNER_SHA = 'c8ca3444c604aebbf5cd0b134f98a86cf79c3521332fff841e371a9986c41942'
COMPLETIONS = ('08deffd0a0baa3bcad110884d250893f8470ae320afd13a3d71e20a651da4972',
               '56d19072b3f9474631c4b0d61ca23a21fde490ad80a9dd197f310ecd7023ff92',
               'e7ef9be2d572251e64c5973305fdcad0112d9569498c79c6646848049850987f')


def root_for(seed):
    return Path('/localhome/local-rohing/astra_diagnostics') / f'post_memory_formation_seed{seed}_20260913_attempt1'


def runtime():
    return previous.load('post_memory_main_runtime', RUNNER, RUNNER_SHA)


def specs():
    for seed in range(3):
        origin = json.loads((previous.BASE / f'seed{seed}.json').read_text())
        local = Path('/tmp/astra_memory_collected_20260913_attempt1') / f'real_record_memory_seed{seed}_20260913_attempt1_collected'
        scores = json.loads((local / 'scores.json').read_text())
        assert scores['seed'] == seed and scores['completion_sha256'] == COMPLETIONS[seed]
        native = Path(str(previous.root_for(seed)) + '_collected')
        spec = dict(runner_sha256=RUNNER_SHA,
                    core=dict(path='/tmp/astra_post_memory_formation_core_20260913.py', sha256='030c97c57a962a74a5b97bd66550096dedc2bab288d690b2c89808d2ec84474b'),
                    memory_runtime=dict(path=str(previous.RUNNER), sha256=previous.RUNNER_SHA),
                    memory=dict(root=str(previous.root_for(seed)), plan_sha256=scores['plan_sha256'],
                                completion_sha256=COMPLETIONS[seed],
                                collection=dict(path=str(native / 'collection.json'), sha256=previous.digest(local / 'collection.json')),
                                scores=dict(path=str(native / 'scores.json'), sha256=previous.digest(local / 'scores.json'))),
                    seed=seed, node='node2', **{key: origin[key] for key in ('gpu_index', 'gpu_uuid', 'expected_boot_id', 'lease_end')})
        path = BASE / f'seed{seed}.json'
        previous.write(path, spec)
        print(json.dumps(dict(seed=seed, spec_sha256=previous.digest(path))), flush=True)


def prepare(seed):
    spec = BASE / f'seed{seed}.json'
    result = runtime().prepare(str(root_for(seed)), str(spec), previous.digest(spec), allow_native=True)
    assert result['status'] == 'POST_MEMORY_NATIVE_CPU_PREPARED_NOT_LAUNCHED' and result['outcome_gate'] is None
    previous.write(BASE / f'seed{seed}_prepared.json', result)
    print(json.dumps(result), flush=True)


def launch(seed):
    active = runtime()
    active.offline()
    batch = previous.load('post_memory_main_reservations', '/tmp/astra_level1_next_batch_20260913.py', '03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2')
    prechecks = Path('/tmp/astra_level1_roster_20260913_attempt1/prechecks.json')
    assert previous.digest(prechecks) == '71e8eaa0c326ddef4414539684d20315e3752c48ce425a280438100e32815929'
    config = json.loads(prechecks.read_text())['node2']
    prepared = json.loads((BASE / f'seed{seed}_prepared.json').read_text())
    plan, bound = active.verify(str(root_for(seed)), prepared['plan_sha256'])
    assert not (root_for(seed) / 'controller_started.json').exists()
    claim = Path(str(root_for(seed)) + '.launcher')
    claim.mkdir()
    process = None
    try:
        previous.write(claim / 'precheck.json', batch.reservations(config, plan['gpu_index'], plan['gpu_uuid']))
        assert bound['probe'].gpu_state(plan)
        active.check_allocation(plan)
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'hold', '--seed', str(seed)]
        with (claim / 'stdout.log').open('xb') as output:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid']), start_new_session=True)
        result = dict(status='LAUNCHED_NOT_RESULT', seed=seed, root=str(root_for(seed)), pid=process.pid,
                      identity=batch.identity(Path('/proc') / str(process.pid)), started_unix=time.time(),
                      plan_sha256=prepared['plan_sha256'], gpu_index=plan['gpu_index'], gpu_uuid=plan['gpu_uuid'],
                      command=command, custodian_sha256=previous.digest(__file__), controller_seconds=1800)
        previous.write(claim / 'launched.json', result)
        print(json.dumps(result), flush=True)
    except BaseException as error:
        previous.write(claim / 'failure.json', dict(error=repr(error), controller_may_be_running=process is not None))
        raise


def hold(seed):
    spec = json.loads((BASE / f'seed{seed}.json').read_text())
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == spec['gpu_uuid'] and previous.digest(RUNNER) == RUNNER_SHA
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
