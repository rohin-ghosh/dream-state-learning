import argparse
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time


specification = importlib.util.spec_from_file_location('contrastive_main_previous', '/tmp/astra_memory_pairs_main_20260913.py')
previous = importlib.util.module_from_spec(specification)
specification.loader.exec_module(previous)
assert previous.digest(previous.__file__) == '5df4a3c00016ad07305658e2febc642a1182d1944106d70b92b463235ede2dbe'
BASE = Path('/tmp/astra_contrastive_full_dose_specs_20260913_attempt2')
RUNNER = Path('/tmp/astra_contrastive_full_dose_run_20260913_v2.py')
GPUS = {0: 'GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0',
        1: 'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4',
        2: 'GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05'}
BOOT = '8ff7b0dc-fbdf-4945-9044-3dffe94b5407'


def root_for(seed):
    return Path('/localhome/local-rohing/astra_diagnostics') / f'contrastive_full_dose_seed{seed}_20260913_attempt2'


def runtime(checksum):
    return previous.load('contrastive_full_dose_runtime', RUNNER, checksum)


def make_specs(checksum):
    candidate = runtime(checksum)
    original_path = Path('/tmp/astra_contrastive_spec_20260913_attempt1.json')
    assert previous.digest(original_path) == '56970a4b5f4637564b4fdfba344e9c72cffeabb3be93ad0e8353b9bb5781d12a'
    original = json.loads(original_path.read_text())
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip() == BOOT
    for seed, uuid in GPUS.items():
        spec = {key: original[key] for key in ('binding', 'encoder', 'material', 'model', 'public', 'reflection', 'source', 'source_files', 'lease_end')}
        spec.update(runner_sha256=checksum, original=dict(path=str(candidate.ORIGINAL), sha256=candidate.ORIGINAL_SHA),
                    protocol=dict(path=str(BASE / 'protocol.md'), sha256=candidate.PROTOCOL_SHA),
                    original_protocol=original['protocol'],
                    historical_archive=dict(path='/localhome/local-rohing/astra_diagnostics/contrastive_perception_20260913_attempt1_archive.tar', sha256=candidate.ARCHIVE_SHA),
                    learner_seed=seed, node='node2', expected_hostname=socket.gethostname(), expected_boot_id=BOOT,
                    gpu_index=seed, gpu_uuid=uuid)
        reservation_path = BASE / f'seed{seed}_reservation.json'
        reservation = dict(scope=candidate.SCOPE, root=str(root_for(seed)), **{field: spec[field] for field in ('node', 'expected_hostname', 'expected_boot_id', 'gpu_index', 'gpu_uuid', 'lease_end', 'learner_seed')})
        candidate.write(reservation_path, reservation)
        spec['reservation'] = dict(path=str(reservation_path), sha256=candidate.digest(reservation_path))
        path = BASE / f'seed{seed}.json'
        candidate.write(path, spec)
        candidate.validate_spec(spec)
        print(json.dumps(dict(seed=seed, spec_sha256=candidate.digest(path))), flush=True)


def prepare(seed, checksum):
    candidate = runtime(checksum)
    path = BASE / f'seed{seed}.json'
    result = candidate.prepare(str(root_for(seed)), str(path), candidate.digest(path), allow_native=True)
    assert result['status'] == 'PREPARED_NOT_GPU_APPROVAL' and result['budget']['updates'] == 672 and result['budget']['calls'] == 96
    candidate.write(BASE / f'seed{seed}_prepared.json', result)
    print(json.dumps(result), flush=True)


def launch(seed, checksum):
    candidate = runtime(checksum)
    candidate.offline()
    batch = previous.load('contrastive_reservations', '/tmp/astra_level1_next_batch_20260913.py', '03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2')
    prechecks = Path('/tmp/astra_level1_roster_20260913_attempt1/prechecks.json')
    assert previous.digest(prechecks) == '71e8eaa0c326ddef4414539684d20315e3752c48ce425a280438100e32815929'
    config = json.loads(prechecks.read_text())['node2']
    prepared = candidate.read(BASE / f'seed{seed}_prepared.json')
    root = root_for(seed)
    plan, probe = candidate.verify(str(root), prepared['plan_sha256'])
    assert not (root / 'controller_started.json').exists()
    candidate.allocation(plan['specification'], root, launch=True)
    claim = Path(str(root) + '.launcher')
    claim.mkdir()
    process = None
    try:
        candidate.write(claim / 'precheck.json', batch.reservations(config, seed, GPUS[seed]))
        assert probe.gpu_state(plan) is True
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'hold', '--seed', str(seed), '--runner-sha256', checksum]
        with (claim / 'stdout.log').open('xb') as output:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=GPUS[seed]), start_new_session=True)
        result = dict(status='LAUNCHED_NOT_RESULT', seed=seed, root=str(root), pid=process.pid,
                      identity=batch.identity(Path('/proc') / str(process.pid)), started_unix=time.time(),
                      gpu_index=seed, gpu_uuid=GPUS[seed], plan_sha256=prepared['plan_sha256'], command=command,
                      custodian_sha256=previous.digest(__file__), runner_sha256=checksum, controller_seconds=7200)
        candidate.write(claim / 'launched.json', result)
        print(json.dumps(result), flush=True)
    except BaseException as error:
        candidate.write(claim / 'failure.json', dict(error=repr(error), controller_may_be_running=process is not None))
        raise


def hold(seed, checksum):
    candidate = runtime(checksum)
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == GPUS[seed]
    prepared = candidate.read(BASE / f'seed{seed}_prepared.json')
    claim = Path(str(root_for(seed)) + '.launcher')
    command = [sys.executable, '-B', str(RUNNER), 'controller', '--root', str(root_for(seed)),
               '--plan-sha256', prepared['plan_sha256'], '--allow-gpu']
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''), start_new_session=True)
    candidate.write(claim / 'controller.json', dict(pid=process.pid, pgid=process.pid, command=command, started_unix=time.time()))
    try:
        result = process.wait()
    except BaseException as error:
        candidate.write(claim / 'holder_failure.json', dict(error=repr(error), controller_pid=process.pid, release_unknown=True))
        raise
    candidate.write(claim / 'exit.json', dict(returncode=result, completed_unix=time.time()))
    sys.exit(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('specs', 'prepare', 'launch', 'hold'))
    parser.add_argument('--seed', type=int, choices=(0, 1, 2))
    parser.add_argument('--runner-sha256', required=True)
    options = parser.parse_args()
    if options.action == 'specs':
        make_specs(options.runner_sha256)
    else:
        assert options.seed is not None
        globals()[options.action](options.seed, options.runner_sha256)
