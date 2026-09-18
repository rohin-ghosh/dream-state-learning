"""One explicit C1 readmission after a pre-load scanner refusal; no learner replay."""

import argparse
from copy import deepcopy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
import uuid


BASE = Path('/localhome/local-rohing')
ORIGINAL = BASE / 'orch_r179_context_C1_20260917_attempt2'
FRESH = BASE / 'orch_r179_C1_readmission_20260917_attempt2'
PREVIOUS = BASE / 'orch_r179_C1_readmission_20260917_attempt1'
OPERATOR_SHA = 'c113e59cea8a7b2c40b0e76804bc0b9c850cf5c0b822c3e4b3523f20c9a21439'
RETIREMENT_SHA = '43917269fd1098490957a819dcbe59887c0d4133ff8c8820ea2e015c2f4ae436'
ADMISSION_SHA = 'f57b7acc37041a331943bd4fc6007d4d46ad27765759896da3efc9df4ba7fa25'
BOUNDARY_SHA = 'dfd724e34b5660ca1507a619c10af091dbb8d138ce03aacd4d6fa4b5013b0438'
PYTHON = str(BASE / 'v2/venv/bin/python')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    Path(path).chmod(0o444)


def operator():
    path = ORIGINAL / 'rollout_operator.py'
    require(sha(path) == OPERATOR_SHA, 'exact_original_operator')
    spec = importlib.util.spec_from_file_location('_r179_c1_original', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def eligible(failure, admission, boundary, names, owners_present):
    require(failure.get('reason') == 'original_privileged_clear_admission'
            and failure.get('retired') is True and failure.get('terminated') is True,
            'preload_admission_failure_after_recorded_retirement')
    require(admission.get('clear') is False and admission.get('scanner_euid') == 0
            and admission.get('blocking_reasons') == ['process_identity_drift:1530599'],
            'exact_preserved_original_refusal')
    require(not owners_present, 'no_original_owner_still_present')
    require(not set(names).intersection({'LAUNCH.json', 'NATIVE.log', 'NATIVE_EXIT.json',
                                       'CONTAINED_COMMAND.json', 'CONTAINMENT_VERIFIED.json'}),
            'no_prior_native_or_contained_dispatch')
    require(boundary['record']['sha256'] == BOUNDARY_SHA and boundary['cycle'] == 39
            and boundary['record']['kind'] == 'SLEEP_COMPLETE', 'same_sleep39_boundary')


def inputs():
    module = operator()
    saved, config, plan = module.validate_successor(ORIGINAL)
    require(plan['physical'] == 0 and plan['root'] == str(BASE / 'orch_r153_community_C1_20260916_attempt1/life')
            and plan['source_root'] == str(ORIGINAL / 'source'), 'only_exact_C1_successor')
    require(sha(ORIGINAL / 'OWNER_RETIRED.json') == RETIREMENT_SHA
            and sha(ORIGINAL / 'attempt/ADMISSION.json') == ADMISSION_SHA, 'original_receipt_pins')
    boundary = saved.saved_boundary(plan['root'])
    require(boundary is not None, 'current_complete_boundary_no_suffix')
    pair = read(ORIGINAL / 'READY.json')['pair']
    present = [role for role, process in pair.items() if Path('/proc', str(process['pid'])).exists()]
    eligible(read(ORIGINAL / 'EXECUTION_FAILED.json'), read(ORIGINAL / 'attempt/ADMISSION.json'),
             boundary, [path.name for path in (ORIGINAL / 'attempt').iterdir()], present)
    require(not Path('/proc/1530599').exists(), 'original_drift_process_gone')
    require(read(PREVIOUS / 'attempt/NATIVE_EXIT.json') == dict(returncode=1, no_retry=True)
            and read(PREVIOUS / 'attempt/SERVICE_EXIT.json') == dict(returncode=1, no_retry=True),
            'previous_readmission_terminal')
    require(not (PREVIOUS / 'attempt/DISPATCH_ONCE').exists()
            and (PREVIOUS / 'attempt/NATIVE.log').read_text().rstrip().endswith('ValueError: actual_timeout_parent'),
            'previous_exact_premodel_missing_marker_refusal')
    for receipt in ('OPERATOR_STARTED.json', 'attempt/LAUNCH.json'):
        require(not Path('/proc', str(read(PREVIOUS / receipt)['pid'])).exists(), 'previous_attempt_process_exited')
    return module, saved, config, plan, boundary


def validate():
    module = operator()
    saved, previous, plan = module.validate_successor(ORIGINAL)
    from gpu.orch_r125_continual_guard import validate as guard_validate
    config, new_plan = guard_validate(FRESH / 'GUARD.json')
    expected = deepcopy(previous)
    expected['attempt_dir'] = str(FRESH / 'attempt')
    expected['device_containment']['unit'] = read(FRESH / 'REQUEST.json')['new_unit']
    require(config == expected and new_plan == plan, 'attempt_and_containment_unit_only')
    request = read(FRESH / 'REQUEST.json')
    require(request['helper_sha256'] == sha(Path(__file__))
            and request['original_retirement_sha256'] == RETIREMENT_SHA
            and request['original_admission_sha256'] == ADMISSION_SHA
            and request['original_boundary_sha256'] == BOUNDARY_SHA
            and request['guard_sha256'] == sha(FRESH / 'GUARD.json'), 'bound_readmission_bytes')
    require(request['source_unchanged'] and request['wall_unchanged'] and request['no_native_previously_launched'],
            'readmission_not_new_recipe_or_replay')
    return module, saved, config, plan


def preflight():
    module, saved, previous, plan, boundary = inputs()
    require(Path(__file__).resolve() == FRESH / 'c1_readmission.py', 'receiving_helper_only')
    config = deepcopy(previous)
    config['attempt_dir'] = str(FRESH / 'attempt')
    config['device_containment']['unit'] = 'orch-r179-c1-readmit-' + uuid.uuid4().hex
    write(FRESH / 'GUARD.json', config)
    write(FRESH / 'REQUEST.json', dict(schema='R179_C1_PRELOAD_READMISSION_V1',
        helper_sha256=sha(Path(__file__)), original_retirement_sha256=RETIREMENT_SHA,
        original_admission_sha256=ADMISSION_SHA, original_boundary_sha256=BOUNDARY_SHA,
        guard_sha256=sha(FRESH / 'GUARD.json'), new_unit=config['device_containment']['unit'],
        source_unchanged=True, wall_unchanged=True, no_native_previously_launched=True,
        no_reset=True, no_consumed_call_replay=True, observed_unix=time.time()))
    validate()
    original_plan = read(read(ORIGINAL / 'INPUT.json')['plan_ref']['path'])
    command = [PYTHON, '-B', str(ORIGINAL / 'cpu_actual.py'), '--source', plan['source_root'],
        '--original', original_plan['source_root'], '--plan', str(ORIGINAL / 'PLAN.json'),
        '--boundary', str(ORIGINAL / 'ACTUAL_4755_BOUNDARY.json')]
    result = subprocess.run(command, cwd=plan['source_root'], env=module.environment(plan['source_root']),
                            text=True, capture_output=True, timeout=180)
    write(FRESH / 'CPU_STATE_PROOF.json', dict(returncode=result.returncode, stdout=result.stdout,
                                             stderr=result.stderr, command=command))
    require(result.returncode == 0, 'actual_saved_state_CPU_proof')
    require(saved.saved_boundary(plan['root']) == boundary, 'same_boundary_after_CPU_proof')
    write(FRESH / 'READY.json', dict(status='CPU_READY_NO_DISPATCH', guard_sha256=sha(FRESH / 'GUARD.json'),
        state_proof_sha256=sha(FRESH / 'CPU_STATE_PROOF.json'), observed_unix=time.time()))


def strict_command(module, saved, config, plan):
    command = module.strict_command(saved, config, plan, ORIGINAL)
    previous = [PYTHON, '-B', str(ORIGINAL / 'rollout_operator.py'), 'contained', '--output', str(ORIGINAL)]
    require(command[-len(previous):] == previous, 'original_strict_payload_suffix')
    return command[:-len(previous)] + [PYTHON, '-B', str(FRESH / 'c1_readmission.py'), 'contained']


def execute():
    inputs()
    module, saved, config, plan = validate()
    ready = read(FRESH / 'READY.json')
    require(ready['guard_sha256'] == sha(FRESH / 'GUARD.json')
            and ready['state_proof_sha256'] == sha(FRESH / 'CPU_STATE_PROOF.json')
            and read(FRESH / 'CPU_STATE_PROOF.json')['returncode'] == 0, 'receiving_state_proof_bound')
    lock = os.open(BASE / 'orch_r157_C1_HANDOFF.lock', os.O_RDWR | os.O_NOFOLLOW)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (FRESH / 'EXECUTE_ONCE').mkdir()
        inputs()
        attempt = FRESH / 'attempt'
        attempt.mkdir()
        (attempt / 'DISPATCH_ONCE').mkdir()
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + plan['source_root'], PYTHON, '-B', '-m', 'gpu.orch_r125_continual_guard',
            'scan', '--config', str(FRESH / 'GUARD.json')]
        report = json.loads(subprocess.check_output(command, cwd=plan['source_root'], text=True, timeout=100))
        write(attempt / 'ADMISSION.json', report)
        require(report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']
                and report['gpu']['uuid'] == plan['gpu_uuid'], 'fresh_original_clear_admission')
        write(attempt / 'ADMISSION_TIME.json', dict(verified_unix=time.time()))
        command = strict_command(module, saved, config, plan)
        write(attempt / 'CONTAINED_COMMAND.json', dict(command=command, no_retry=True))
        result = subprocess.run(command, check=False)
        write(attempt / 'SERVICE_EXIT.json', dict(returncode=result.returncode, no_retry=True))
        require(result.returncode == 0, 'contained_service_failed')
    except BaseException as error:
        write(FRESH / 'FAILED.json', dict(error_type=type(error).__name__, reason=str(error), no_retry=True))
        raise
    finally:
        os.close(lock)


def contained():
    module, saved, config, plan = validate()
    from gpu.orch_r133_code_feedback_guard import publish_launch, reap_owned_child
    attempt = FRESH / 'attempt'
    write(attempt / 'CONTAINMENT_VERIFIED.json', module.unchanged_containment_check(config, plan))
    report = read(attempt / 'ADMISSION.json')
    admitted = read(attempt / 'ADMISSION_TIME.json')['verified_unix']
    require(report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']
            and report['gpu']['uuid'] == plan['gpu_uuid'] and 0 <= time.time() - admitted < 100,
            'fresh_original_admission_before_native')
    remaining = int(plan['hard_end_unix'] - time.time() - 10)
    require(remaining > 10, 'remaining_unchanged_wall')
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining) + 's', PYTHON,
               '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(FRESH / 'GUARD.json')]
    process = None
    try:
        with (attempt / 'NATIVE.log').open('x') as log:
            process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.PIPE,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            identity = saved.identity(process.pid)
            publish_launch(attempt / 'LAUNCH.json', dict(pid=process.pid,
                parent_start_ticks=identity['start_ticks'], started_unix=time.time(),
                admission_verified_unix=admitted, admission_sha256=sha(attempt / 'ADMISSION.json'),
                guard_sha256=sha(FRESH / 'GUARD.json'), plan_sha256=config['plan_sha256'],
                gpu_uuid=plan['gpu_uuid'], command_sha256=saved.digest(command),
                hard_end_unix=plan['hard_end_unix'], no_retry=True))
            process.stdin.write(b'LAUNCH_READY\n')
            process.stdin.close()
            result = process.wait()
        write(attempt / 'NATIVE_EXIT.json', dict(returncode=result, no_retry=True))
        require(result == 0, 'native_readmission_failed')
    except BaseException:
        reap_owned_child(process)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'execute', 'contained'))
    arguments = parser.parse_args()
    globals()[arguments.action]()


if __name__ == '__main__':
    main()
