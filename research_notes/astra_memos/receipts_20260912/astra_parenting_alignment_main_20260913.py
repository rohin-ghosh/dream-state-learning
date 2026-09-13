import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


specification = importlib.util.spec_from_file_location('alignment_main_previous', '/tmp/astra_memory_pairs_main_20260913.py')
previous = importlib.util.module_from_spec(specification)
specification.loader.exec_module(previous)
assert previous.digest(previous.__file__) == '5df4a3c00016ad07305658e2febc642a1182d1944106d70b92b463235ede2dbe'
BASE = Path('/tmp/astra_parenting_alignment_specs_20260913_attempt1')
RUNNER = Path('/tmp/astra_parenting_alignment_run_20260913.py')
CORE = Path('/tmp/astra_parenting_alignment_core_20260913.py')
SOURCE = '/tmp/astra_level1_real_record_source_20260913_attempt1'
GPUS = {0: 'GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0',
        1: 'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4',
        2: 'GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05'}
PROTOCOL_SHA = '5c53d6aa850b3a3a409c255ab9b28ce3b090f7325f35688437e42a86b1cccce5'
PRIOR_IDS_SHA = 'bcfb7aed8ac07b4c90698f796046270f40bccd3a33bcf3f81e0cf51a3adfcf7e'


def root_for(seed):
    assert type(seed) is int and seed in GPUS
    return Path('/localhome/local-rohing/astra_diagnostics') / f'parenting_alignment_seed{seed}_20260913_attempt1'


def runtime(checksum):
    return previous.load('parenting_alignment_runtime', RUNNER, checksum)


def specs(checksum, core_checksum):
    candidate = runtime(checksum)
    assert previous.digest(CORE) == core_checksum == candidate.CORE_PIN
    assert previous.digest(BASE / 'protocol.md') == PROTOCOL_SHA == candidate.PROTOCOL_PIN
    assert previous.digest(BASE / 'prior_ids.json') == PRIOR_IDS_SHA
    for seed, uuid in GPUS.items():
        spec = dict(runner_sha256=checksum,
                    core=dict(path=str(CORE), sha256=core_checksum),
                    protocol=dict(path=str(BASE / 'protocol.md'), sha256=PROTOCOL_SHA),
                    capture_runtime=dict(path='/tmp/astra_own_source_replay_capture_20260913.py', sha256=candidate.CAPTURE_PIN),
                    parented_runtime=dict(path='/tmp/astra_parented_record_run_20260913.py', sha256=candidate.PARENTED_PIN),
                    parent_source=dict(path='/tmp/astra_own_source_replay_core_20260913.py', sha256=candidate.PARENT_SOURCE_PIN),
                    native=dict(path='/tmp/astra_level1_real_record_run_20260913.py', sha256=candidate.NATIVE_PIN),
                    public=dict(path='/tmp/astra_birth_skill_probe_run_20260913.py', sha256=candidate.PUBLIC_PIN),
                    archive=dict(path='/tmp/astra_level1_second_scores_20260913/native_archive/node2_second_perception.tar',
                                 sha256='addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a'),
                    source_root=SOURCE,
                    prior_task_ids=dict(path=str(BASE / 'prior_ids.json'), sha256=PRIOR_IDS_SHA),
                    seed=seed, gpu_index=seed, gpu_uuid=uuid,
                    expected_boot_id='8ff7b0dc-fbdf-4945-9044-3dffe94b5407',
                    lease_end=datetime(2026, 9, 21, 8, 43, tzinfo=timezone.utc).timestamp())
        candidate.validate_spec(spec)
        path = BASE / f'seed{seed}.json'
        previous.write(path, spec)
        print(json.dumps(dict(seed=seed, spec_sha256=previous.digest(path))), flush=True)


def prepare(seed, checksum):
    path = BASE / f'seed{seed}.json'
    result = runtime(checksum).prepare(str(root_for(seed)), str(path), previous.digest(path), allow_native=True)
    assert result['status'] in ('PREPARED_NOT_LAUNCHED', 'NATIVE_CPU_PREPARED_NOT_LAUNCHED')
    previous.write(BASE / f'seed{seed}_prepared.json', result)
    print(json.dumps(result), flush=True)


def launch(seed, checksum):
    candidate = runtime(checksum)
    candidate.runtime().offline()
    batch = previous.load('alignment_reservations', '/tmp/astra_level1_next_batch_20260913.py',
                          '03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2')
    prechecks = Path('/tmp/astra_level1_roster_20260913_attempt1/prechecks.json')
    assert previous.digest(prechecks) == '71e8eaa0c326ddef4414539684d20315e3752c48ce425a280438100e32815929'
    config = json.loads(prechecks.read_text())['node2']
    prepared = json.loads((BASE / f'seed{seed}_prepared.json').read_text())
    plan, bound = candidate.verify(str(root_for(seed)), prepared['plan_sha256'])
    assert not (root_for(seed) / 'controller_started.json').exists()
    assert plan['gpu_index'] == seed and plan['gpu_uuid'] == GPUS[seed]
    assert plan['limits']['fits'] == 0 and plan['limits']['updates'] == 0
    candidate.allocation(plan)
    claim = Path(str(root_for(seed)) + '.launcher')
    claim.mkdir()
    process = None
    try:
        previous.write(claim / 'precheck.json', batch.reservations(dict(config, gpus={str(seed): GPUS[seed]}), seed, GPUS[seed]))
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
