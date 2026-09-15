"""Nonmaterial scanner-failure recovery; never retry an entered native phase."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time


REMAINING = ((7, 'readout'), (8, 'experience'), (8, 'readout'))
UUID = 'GPU-f0405a96-813d-7ac7-d641-3ec31d103037'
HOST_SHA = '6bcd6b8370cc2f2a15e1e488352b4cec96b1e137489d52c3324c199536a09ba8'
REPAIR = 'feedback_uptake_creative_guard_v1'


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.write('\n')


def original(root):
    path = root / 'orch_math_pipeline_l2_r102_run.py'
    specification = importlib.util.spec_from_file_location('creative_original_driver', path)
    driver = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(driver)
    driver.validate(root, 'creative7')
    return driver


def completed_prefix(campaign):
    sequence = [(cycle, phase) for cycle in range(1, 9) for phase in ('experience', 'readout')]
    boundary = sequence.index(REMAINING[0])
    bindings = {}
    calls = 0
    for cycle, phase in sequence[:boundary]:
        output = campaign / 'GUIDED_SLEEP' / f'cycle{cycle}' / phase
        complete, after = read(output / 'COMPLETE.json'), read(output / 'AFTER.json')
        require(complete['status'] == 'COMPLETE', 'prefix_not_complete')
        require(after['actual_mounted_identity_verified'] and after['frozen_base_verified'], 'prefix_after')
        require(complete['process'] == after['process'], 'prefix_process')
        require(complete['output_adapter'] == after['output_adapter'], 'prefix_adapter')
        require(not (output / 'FAILED.json').exists(), 'prefix_failure_conflict')
        records = sorted(output.glob('CALL_*.json'))
        require(len(records) == (4 if phase == 'experience' else 8), 'prefix_denominator')
        calls += len(records)
        paths = records + [output / 'COMPLETE.json', output / 'AFTER.json', output / 'REQUEST.json']
        if phase == 'experience':
            paths += [output / 'ROWS.json']
        for path in paths:
            bindings[str(path)] = sha(path)
    require(calls == 76, 'original_call_counter')
    for cycle, phase in REMAINING:
        require(not (campaign / 'GUIDED_SLEEP' / f'cycle{cycle}' / phase).exists(), 'entered_phase_never_retried')
        require(not (campaign / f'LAUNCH_C{cycle}_{phase}.json').exists(), 'prior_dispatch_never_retried')
    return bindings


def checked_report(report):
    require(report['gpu']['index'] == 7 and report['gpu']['uuid'] == UUID, 'pinned_physical_uuid')
    require(report['host_sha256'] == HOST_SHA and 'device_minor' in report, 'host_minor_binding')
    return report['clear'] is True and report['scanner_euid'] == 0 and not report['blocking_reasons']


def admit(common, root, destination, label, deadline, clock=time.time, wait=time.sleep):
    until = min(clock() + 180, deadline)
    attempt = 0
    while clock() < until:
        path = destination / f'ADMISSION_{label}_{attempt}.json'
        try:
            report = common.scan(7, root / 'SERVICE_IDENTITY.json')
        except subprocess.CalledProcessError as error:
            write(path, dict(status='SCANNER_ERROR_BLOCKED', returncode=error.returncode,
                stderr=error.stderr, stdout=error.stdout, no_waiver=True))
        else:
            write(path, report)
            if checked_report(report):
                require(clock() < deadline, 'native_deadline_after_scan')
                return report
        attempt += 1
        wait(2)
    raise TimeoutError('strict_scanner_admission_blocked_no_native_dispatched')


def prepare(root, tests):
    driver = original(root)
    campaign = root / 'campaign_04_r102_creative7'
    failure = read(campaign / 'LANE_FAILED.json')
    require(read(campaign / 'LANE_TERMINAL.json')['status'] == 'FAILED', 'original_failure_preserved')
    require(failure['type'] == 'CalledProcessError' and 'orch_math_pipeline_l2_scan' in failure['message'], 'exact_scanner_failure')
    identity = read(campaign / 'LANE_STARTED.json')['identity']
    require(not (Path('/proc') / str(identity['pid'])).exists(), 'original_guardian_not_released')
    bindings = completed_prefix(campaign)
    saved = campaign / 'GUIDED_SLEEP/cycle7/experience'
    complete = read(saved / 'COMPLETE.json')
    driver.common.verify_saved(complete['output_adapter'])
    require(sha(saved / 'optimizer.pt') == complete['optimizer_sha256'], 'genuine_c7_optimizer')
    for name, digest in complete['output_adapter']['files']:
        path = Path(complete['output_adapter']['path']) / name
        require(sha(path) == digest, 'genuine_c7_adapter')
        bindings[str(path)] = digest
    bindings[str(saved / 'optimizer.pt')] = complete['optimizer_sha256']
    for path in (campaign / 'LANE_FAILED.json', campaign / 'LANE_TERMINAL.json', campaign / 'LANE_STARTED.json',
                 campaign / 'R102_READY.json', root / 'LIFETIME.json', root / 'SERVICE_IDENTITY.json',
                 Path(__file__), tests, Path(__file__).with_name('orch_math_feedback_uptake_creative_guard_test.py')):
        bindings[str(path)] = sha(path)
    require('OK' in tests.read_text() and 'FAILED' not in tests.read_text(), 'cpu_test_receipt')
    destination = root / REPAIR
    destination.mkdir(exist_ok=False)
    ready = dict(kind='NONMATERIAL_SCANNER_GUARDIAN_REPAIR', source_bindings=bindings,
        remaining=list(REMAINING), prior_native_calls=76, remaining_native_calls=68,
        prior_parent_calls=7, remaining_parent_calls=1, original_native_cap=144,
        original_parent_cap=8, original_lifetime=read(root / 'LIFETIME.json'),
        saved_c7_adapter=complete['output_adapter'], saved_c7_optimizer_sha256=complete['optimizer_sha256'],
        no_new_budget=True, no_native_retry=True, no_prompt_dose_state_change=True,
        cpu_tests_passed=True, prepared_unix=time.time())
    write(destination / 'READY.json', ready)
    print(json.dumps(dict(path=str(destination / 'READY.json'), sha256=sha(destination / 'READY.json'))))


def guard(root, expected_ready):
    driver = original(root)
    common = driver.common
    campaign = root / 'campaign_04_r102_creative7'
    destination = root / REPAIR
    require(sha(destination / 'READY.json') == expected_ready, 'bound_ready')
    ready = read(destination / 'READY.json')
    publication = read(destination / 'PUBLICATION.json')
    require(publication['ready_sha256'] == expected_ready and publication['builder_entry_sha256'] == sha(destination / 'BUILDER_ENTRY.md'), 'pre_gpu_receipt')
    require(ready['remaining'] == [list(stage) for stage in REMAINING], 'exact_remaining_sequence')
    for path, digest in ready['source_bindings'].items():
        require(sha(path) == digest, 'immutable_history_and_sources')
    completed_prefix(campaign)
    identity = read(campaign / 'LANE_STARTED.json')['identity']
    require(not (Path('/proc') / str(identity['pid'])).exists(), 'old_guardian_absent')
    lifetime = read(root / 'LIFETIME.json')
    require(time.time() < lifetime['native_deadline_unix'], 'original_native_deadline')
    write(destination / 'ACTIVATION.json', dict(ready_sha256=expected_ready,
        process=common.process_identity(Path('/proc') / str(os.getpid())), started_unix=time.time(),
        original_lifetime=lifetime, no_counter_reset=True))
    child = identity = log = None
    status = 'FAILED'
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for cycle, phase in REMAINING:
            driver.validate(root, 'creative7')
            require(sha(root / 'LIFETIME.json') == ready['source_bindings'][str(root / 'LIFETIME.json')], 'unchanged_lifetime')
            output = campaign / 'GUIDED_SLEEP' / f'cycle{cycle}' / phase
            require(not output.exists(), 'entered_native_phase_never_retried')
            label = f'C{cycle}_{phase}'
            admit(common, root, destination, label, lifetime['native_deadline_unix'])
            require(not output.exists(), 'concurrent_phase_dispatch')
            write(destination / f'DISPATCH_{label}.json', dict(started_unix=time.time(), uuid=UUID))
            log = (destination / f'{label}.log').open('x')
            child = subprocess.Popen([common.PYTHON, '-B', str(root / 'orch_math_pipeline_l2_r102_run.py'),
                'native', '--root', str(root), '--variant', 'creative7', '--cycle', str(cycle), '--native-phase', phase],
                cwd=root / 'source', env=dict(os.environ, CUDA_VISIBLE_DEVICES=UUID,
                    PYTHONPATH=str(root / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                    OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'),
                start_new_session=True, stdout=log, stderr=subprocess.STDOUT)
            identity = common.process_identity(Path('/proc') / str(child.pid))
            write(destination / f'LAUNCH_{label}.json', dict(identity=identity, started_unix=time.time(), uuid=UUID))
            while child.poll() is None:
                require(time.time() < lifetime['hard_deadline_unix'] - 150, 'original_hard_deadline')
                time.sleep(2)
            require(child.returncode == 0, 'native_failure_no_retry')
            complete, after = read(output / 'COMPLETE.json'), read(output / 'AFTER.json')
            require(complete['status'] == 'COMPLETE', 'phase_complete')
            require(complete['process'] == [identity['boot_id'], identity['pid'], int(identity['start_ticks'])], 'actual_process')
            require(after['actual_mounted_identity_verified'] and after['frozen_base_verified'], 'actual_after')
            require(after['process'] == complete['process'] and after['output_adapter'] == complete['output_adapter'], 'after_process_adapter')
            require(len(list(output.glob('CALL_*.json'))) == (4 if phase == 'experience' else 56 if cycle == 8 else 8), 'phase_denominator')
            write(destination / f'COMPLETE_{label}.json', dict(complete_sha256=sha(output / 'COMPLETE.json'),
                after_sha256=sha(output / 'AFTER.json'), finished_unix=time.time()))
            log.close()
            child = identity = log = None
        status = 'COMPLETE'
    except BaseException as error:
        write(destination / 'FAILED.json', dict(type=type(error).__name__, message=str(error), observed_unix=time.time()))
        raise
    finally:
        if child is not None:
            common.stop_owned(child, identity)
        if log is not None:
            log.close()
        write(destination / 'TERMINAL.json', dict(status=status, finished_unix=time.time(),
            original_failed_terminal_preserved=True, peer_processes_signalled=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('prepare', 'guard'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--tests', type=Path)
    parser.add_argument('--ready-sha256')
    options = parser.parse_args()
    if options.command == 'prepare':
        prepare(options.root, options.tests)
    else:
        guard(options.root, options.ready_sha256)
