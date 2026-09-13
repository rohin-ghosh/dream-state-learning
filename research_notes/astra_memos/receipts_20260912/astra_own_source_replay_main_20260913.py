import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


specification = importlib.util.spec_from_file_location('replay_main_previous', '/tmp/astra_memory_pairs_main_20260913.py')
previous = importlib.util.module_from_spec(specification)
specification.loader.exec_module(previous)
assert previous.digest(previous.__file__) == '5df4a3c00016ad07305658e2febc642a1182d1944106d70b92b463235ede2dbe'
BASE = Path('/tmp/astra_own_source_replay_specs_20260913_attempt1')
ROOT = Path('/localhome/local-rohing/astra_diagnostics/own_source_replay_capture_20260913_attempt1')
RUNNER = Path('/tmp/astra_own_source_replay_capture_20260913.py')
RUNNER_SHA = '1142593afb544dec2344c77788f6dbb624f519897b0bb65e135a9e8eb1910107'
SOURCE = '/tmp/astra_level1_real_record_source_20260913_attempt1'
GPU_UUID = 'GPU-a064bca2-bddc-73ad-faf1-a4fbcb49fecf'


def runtime():
    return previous.load('replay_main_runtime', RUNNER, RUNNER_SHA)


def specs():
    candidate = runtime()
    inherited = json.loads(Path('/tmp/astra_memory_lower_lr_specs_20260913_attempt1/seed0.json').read_text())
    spec = dict(runner_sha256=RUNNER_SHA,
                core=dict(path='/tmp/astra_own_source_replay_core_20260913.py', sha256=candidate.CORE_PIN),
                native=dict(path='/tmp/astra_level1_real_record_run_20260913.py', sha256=candidate.NATIVE_PIN),
                public=dict(path='/tmp/astra_birth_skill_probe_run_20260913.py', sha256=candidate.PUBLIC_PIN),
                lifecycle=dict(path='/tmp/astra_real_record_memory_run_20260913.py', sha256=candidate.LIFECYCLE_PIN),
                archive=dict(path='/tmp/astra_level1_second_scores_20260913/native_archive/node2_second_perception.tar',
                             sha256='addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a'),
                source_root=SOURCE, protocol=dict(path=str(BASE / 'protocol.md'), sha256=candidate.PROTOCOL_PIN),
                gpu_index=6, gpu_uuid=GPU_UUID, expected_boot_id=inherited['expected_boot_id'], lease_end=inherited['lease_end'])
    candidate.validate_spec(spec, candidate.lifecycle())
    previous.write(BASE / 'spec.json', spec)
    print(json.dumps(dict(spec_sha256=previous.digest(BASE / 'spec.json'))), flush=True)


def prepare():
    result = runtime().prepare(str(ROOT), str(BASE / 'spec.json'), previous.digest(BASE / 'spec.json'), allow_native=True)
    assert result['status'] == 'NATIVE_CPU_PREPARED_NOT_LAUNCHED'
    previous.write(BASE / 'prepared.json', result)
    print(json.dumps(result), flush=True)


def launch():
    candidate = runtime()
    candidate.lifecycle().offline()
    batch = previous.load('replay_reservations', '/tmp/astra_level1_next_batch_20260913.py',
                          '03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2')
    prechecks = Path('/tmp/astra_level1_roster_20260913_attempt1/prechecks.json')
    assert previous.digest(prechecks) == '71e8eaa0c326ddef4414539684d20315e3752c48ce425a280438100e32815929'
    config = json.loads(prechecks.read_text())['node2']
    prepared = json.loads((BASE / 'prepared.json').read_text())
    plan, bound = candidate.verify(str(ROOT), prepared['plan_sha256'])
    assert not (ROOT / 'controller_started.json').exists()
    assert plan['gpu_index'] == 6 and plan['gpu_uuid'] == GPU_UUID
    candidate.allocation(plan)
    claim = Path(str(ROOT) + '.launcher')
    claim.mkdir()
    process = None
    try:
        previous.write(claim / 'precheck.json', batch.reservations(config, 6, GPU_UUID))
        assert bound['probe'].gpu_state(plan) is True
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'hold']
        with (claim / 'stdout.log').open('xb') as output:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=GPU_UUID, PYTHONPATH=SOURCE), start_new_session=True)
        result = dict(status='LAUNCHED_NOT_RESULT', root=str(ROOT), pid=process.pid,
                      identity=batch.identity(Path('/proc') / str(process.pid)), started_unix=time.time(),
                      gpu_index=6, gpu_uuid=GPU_UUID, plan_sha256=prepared['plan_sha256'], command=command,
                      custodian_sha256=previous.digest(__file__), automatic_once_collection=True)
        previous.write(claim / 'launched.json', result)
        print(json.dumps(result), flush=True)
    except BaseException as error:
        previous.write(claim / 'failure.json', dict(error=repr(error), controller_may_be_running=process is not None))
        raise


def hold():
    runtime()
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == GPU_UUID
    prepared = json.loads((BASE / 'prepared.json').read_text())
    claim = Path(str(ROOT) + '.launcher')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=SOURCE)
    command = [sys.executable, '-B', str(RUNNER), 'controller', '--root', str(ROOT),
               '--plan-sha256', prepared['plan_sha256'], '--allow-gpu']
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, env=environment, start_new_session=True)
    previous.write(claim / 'controller.json', dict(pid=process.pid, pgid=process.pid, command=command, started_unix=time.time()))
    result = process.wait()
    previous.write(claim / 'controller_exit.json', dict(returncode=result, completed_unix=time.time()))
    if result == 0:
        command = [sys.executable, '-B', str(RUNNER), 'collect', '--root', str(ROOT), '--plan-sha256', prepared['plan_sha256'],
                   '--completion-sha256', previous.digest(ROOT / 'capture_complete.json'), '--out', str(ROOT) + '_collected']
        collector = subprocess.Popen(command, stdin=subprocess.DEVNULL, env=environment, start_new_session=True)
        previous.write(claim / 'collector.json', dict(pid=collector.pid, command=command, started_unix=time.time()))
        result = collector.wait()
        previous.write(claim / 'collector_exit.json', dict(returncode=result, completed_unix=time.time()))
    previous.write(claim / 'exit.json', dict(returncode=result, completed_unix=time.time()))
    sys.exit(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('specs', 'prepare', 'launch', 'hold'))
    options = parser.parse_args()
    globals()[options.action]()
