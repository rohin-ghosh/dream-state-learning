"""Fresh per-process-stable admission; unchanged recovery resident and bounds."""

import argparse
import fcntl
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def scan_until_clear(scan, write, deadline, pause=time.sleep):
    for attempt in range(60):
        if time.time() >= deadline:
            raise TimeoutError('bounded_full_proc_scan')
        report = scan()
        write(attempt, report)
        if report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']:
            return report
        pause(1)
    raise ValueError('strict_full_proc_no_waiver')


def guard(source, expected):
    spec = importlib.util.spec_from_file_location('math_recovery', source/'gpu/orch_math_feedback_uptake_r118_node3_recover.py')
    recover = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recover)
    common, require = recover.common, recover.require
    output = recover.LANE/recover.DIRECTORY
    plan = recover.validate()
    require(common.sha(output/'READY.json') == expected, 'same_cpu_ready')
    require(all(not Path('/proc', str(pid)).exists() for pid in (3197262, 3254669)), 'earlier_admission_guards_gone')
    require(not (output/'LAUNCH.json').exists() and not (output/'TERMINAL.json').exists(), 'no_native_retry')
    admission = output/'THIRD_ADMISSION'
    receipt = common.read(Path(__file__).parent/'READY.json')
    require(receipt['passed'], 'new_scanner_cpu_gate')
    for name, digest in receipt['source_files'].items():
        require(Path(name).name == name and common.sha(Path(__file__).parent/name) == digest, 'immutable_scanner_source')
    def full_scan():
        result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH='+str(recover.old.LIBRARY/'source'), 'python3', '-B',
            str(Path(__file__).with_name('orch_math_feedback_uptake_r118_node3_scan.py'))],
            capture_output=True, text=True, check=True, timeout=90)
        import json
        return json.loads(result.stdout)
    with (output/'GUARD.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        admission.mkdir(exist_ok=False)
        child = identity = None
        def interrupted(signum, frame):
            raise SystemExit(128+signum)
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        status = 'FAILED'
        try:
            scan_until_clear(full_scan,
                lambda attempt, report: common.write(admission/f'ADMISSION_{attempt:03d}.json', report),
                min(time.time()+180, plan['original_activation']['native_deadline_unix']-600))
            recover.validate()
            require(not (output/'LAUNCH.json').exists(), 'no_duplicate_model')
            with (output/'RESIDENT.log').open('x') as log:
                child = subprocess.Popen([recover.old.machinery.previous.existing.PYTHON, '-B',
                    str(source/'gpu/orch_math_feedback_uptake_r118_node3_recover.py'), 'resident'],
                    cwd=recover.old.LIBRARY/'source', stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=recover.policy.DEVICES[0],
                        PYTHONPATH=str(recover.old.LIBRARY/'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                        PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false'))
                identity = common.process_identity(Path('/proc')/str(child.pid))
                common.write(output/'LAUNCH.json', dict(identity=identity, uuid=recover.policy.DEVICES[0],
                    plan_sha256=common.sha(output/'PLAN.json'), started_unix=time.time(), admission_only_repair=True))
                require(child.wait(timeout=max(.01, plan['original_activation']['hard_deadline_unix']-120-time.time())) == 0, 'native_failure_no_retry')
                status = common.read(output/'RESIDENT_TERMINAL.json')['status']
        except BaseException as error:
            common.write(admission/'FAILED.json', dict(error=str(error), type=type(error).__name__,
                native_launched=child is not None, finished_unix=time.time()))
            raise
        finally:
            if child is not None:
                common.stop_owned(child, identity)
                common.write(output/'TERMINAL.json', dict(status=status, finished_unix=time.time(), peer_processes_signalled=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--ready-sha256', required=True)
    args = parser.parse_args()
    guard(args.source, args.ready_sha256)
