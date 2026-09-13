import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


specification = importlib.util.spec_from_file_location('repair_main_previous', '/tmp/astra_memory_pairs_main_20260913.py')
previous = importlib.util.module_from_spec(specification)
specification.loader.exec_module(previous)
assert previous.digest(previous.__file__) == '5df4a3c00016ad07305658e2febc642a1182d1944106d70b92b463235ede2dbe'
BASE = Path('/tmp/astra_own_replay_repair_specs_20260913_attempt1')
RUNNER = Path('/tmp/astra_own_replay_repair_run_20260913.py')
CORE = Path('/tmp/astra_own_replay_repair_core_20260913.py')
SOURCE = '/tmp/astra_level1_real_record_source_20260913_attempt1'
GPUS = {0: 'GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0',
        1: 'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4',
        2: 'GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05'}


def root_for(seed):
    return Path('/localhome/local-rohing/astra_diagnostics') / f'own_replay_repair_seed{seed}_20260913_attempt1'


def runtime(checksum):
    return previous.load('own_replay_repair_runtime', RUNNER, checksum)


def binding(root, content, content_key):
    collection = Path(str(root) + '_collected') / 'collection.json'
    return dict(root=str(root), plan_sha256=previous.digest(root / 'plan.json'),
                completion_sha256=previous.digest(root / 'capture_complete.json'),
                collection=dict(path=str(collection), sha256=previous.digest(collection)),
                **{content_key: previous.digest(collection.parent / content)})


def specs(checksum, core_checksum):
    candidate = runtime(checksum)
    assert previous.digest(CORE) == core_checksum
    capture_root = Path('/localhome/local-rohing/astra_diagnostics/own_source_replay_capture_20260913_attempt1')
    capture = binding(capture_root, 'replay_report.json', 'report_sha256')
    assert capture['plan_sha256'] == '7b008f95a21ca7e01b1e72d83cf3ed8e319fbee9cc5b8af60320e65159c9c882'
    assert capture['completion_sha256'] == '81b94e4f4b3c43ba7e0dc96e42fb8bfd6b58d090e3944b97eb1d68b5e3a4f876'
    assert capture['report_sha256'] == '6648c0bc85589dea4e2a7ea498bf547f5313bd38efcd14c15a7d3eee228124c4'
    for seed, uuid in GPUS.items():
        inherited = json.loads((Path('/tmp/astra_memory_lower_lr_specs_20260913_attempt1') / f'seed{seed}.json').read_text())
        lower_root = Path('/localhome/local-rohing/astra_diagnostics') / f'memory_lower_lr_seed{seed}_20260913_attempt1'
        spec = dict(runner_sha256=checksum,
                    runtime=dict(path='/tmp/astra_real_record_memory_run_20260913.py', sha256=candidate.RUNTIME_PIN),
                    lower_runtime=dict(path='/tmp/astra_memory_lower_lr_run_20260913.py', sha256=candidate.LOWER_PIN),
                    capture_runtime=dict(path='/tmp/astra_own_source_replay_capture_20260913.py', sha256=candidate.CAPTURE_PIN),
                    core=dict(path=str(CORE), sha256=core_checksum),
                    protocol=dict(path=str(BASE / 'protocol.md'), sha256=candidate.PROTOCOL_PIN),
                    memory_history=inherited['history'], lower_history=binding(lower_root, 'scores.json', 'scores_sha256'),
                    capture=capture, seed=seed, fit_seed=seed, gpu_index=seed, gpu_uuid=uuid,
                    expected_boot_id=inherited['expected_boot_id'], lease_end=inherited['lease_end'])
        candidate.validate_spec(spec)
        path = BASE / f'seed{seed}.json'
        previous.write(path, spec)
        print(json.dumps(dict(seed=seed, spec_sha256=previous.digest(path))), flush=True)


def prepare(seed, checksum):
    path = BASE / f'seed{seed}.json'
    result = runtime(checksum).prepare(str(root_for(seed)), str(path), previous.digest(path), allow_native=True)
    assert result['status'] == 'NATIVE_CPU_PREPARED_NOT_LAUNCHED'
    previous.write(BASE / f'seed{seed}_prepared.json', result)
    print(json.dumps(result), flush=True)


def launch(seed, checksum):
    candidate = runtime(checksum)
    candidate.runtime().offline()
    batch = previous.load('own_replay_reservations', '/tmp/astra_level1_next_batch_20260913.py',
                          '03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2')
    prechecks = Path('/tmp/astra_level1_roster_20260913_attempt1/prechecks.json')
    assert previous.digest(prechecks) == '71e8eaa0c326ddef4414539684d20315e3752c48ce425a280438100e32815929'
    config = json.loads(prechecks.read_text())['node2']
    prepared = json.loads((BASE / f'seed{seed}_prepared.json').read_text())
    memory, plan, bound = candidate.verify(str(root_for(seed)), prepared['plan_sha256'])
    assert plan['status'] == 'READY'
    assert not (root_for(seed) / 'controller_started.json').exists()
    assert plan['gpu_index'] == seed and plan['gpu_uuid'] == GPUS[seed]
    candidate.allocation(plan)
    assert bound['probe'].gpu_state(plan) is True
    config = dict(config, gpus={str(seed): plan['gpu_uuid']})
    claim = Path(str(root_for(seed)) + '.launcher')
    claim.mkdir()
    process = None
    try:
        previous.write(claim / 'precheck.json', batch.reservations(config, seed, GPUS[seed]))
        assert bound['probe'].gpu_state(plan) is True
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'hold', '--seed', str(seed), '--runner-sha256', checksum]
        with (claim / 'stdout.log').open('xb') as output:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=GPUS[seed], PYTHONPATH=SOURCE), start_new_session=True)
        result = dict(status='LAUNCHED_NOT_RESULT', seed=seed, root=str(root_for(seed)), pid=process.pid,
                      identity=batch.identity(Path('/proc') / str(process.pid)), started_unix=time.time(),
                      gpu_index=seed, gpu_uuid=GPUS[seed], plan_sha256=prepared['plan_sha256'], command=command,
                      custodian_sha256=previous.digest(__file__), runner_sha256=checksum, automatic_once_collection=True)
        previous.write(claim / 'launched.json', result)
        print(json.dumps(result), flush=True)
    except BaseException as error:
        previous.write(claim / 'failure.json', dict(error=repr(error), controller_may_be_running=process is not None))
        raise


def hold(seed, checksum):
    runtime(checksum)
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == GPUS[seed]
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
        command = [sys.executable, '-B', str(RUNNER), 'collect', '--root', str(root), '--plan-sha256', prepared['plan_sha256'],
                   '--completion-sha256', previous.digest(root / 'capture_complete.json'), '--out', str(root) + '_collected']
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
    parser.add_argument('--runner-sha256', required=True)
    parser.add_argument('--core-sha256')
    options = parser.parse_args()
    if options.action == 'specs':
        assert options.core_sha256
        specs(options.runner_sha256, options.core_sha256)
    else:
        assert options.seed is not None
        globals()[options.action](options.seed, options.runner_sha256)
