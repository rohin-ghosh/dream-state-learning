"""Admission-only recovery before the first shared native process; no scan waivers."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from gpu import orch_math_feedback_uptake_r118_shared_run as run


def pristine(root):
    document = run.activation(root)
    run.require(not (root/'SHARED_LAUNCH.json').exists(), 'no_shared_native_relaunch')
    old = run.shared.read(root/'SHARED_GUARD_LAUNCH.json')['identity']
    run.require(not (Path('/proc')/str(old['pid'])).exists(), 'old_admission_guard_exited')
    run.require(not (root/'SHARED_MODEL_LOADED.json').exists() and not (root/'SHARED_TERMINAL.json').exists(),
        'admission_only_no_native_phase')
    return run.boundary.verify_release(root, document['release'])


def scan_until_clear(root, output, deadline, scan_call=None, pause=time.sleep):
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+str(run.SOURCE), 'python3', '-B', '-m', run.MODULE, 'scan', '--root', str(root)]
    for attempt in range(60):
        run.require(time.time() < deadline, 'bounded_admission_recovery')
        result = (scan_call or subprocess.run)(command, capture_output=True, text=True,
            timeout=min(90,max(.1,deadline-time.time())), check=True)
        report = json.loads(result.stdout)
        run.shared.write(output/f'ADMISSION_{attempt:03d}.json', report)
        if report['clear'] and not report['blocking_reasons'] and report['scanner_euid'] == 0:
            return report
        pause(min(1,max(0,deadline-time.time())))
    raise ValueError('strict_full_proc_never_clear_no_waiver')


def guard(root):
    root = Path(root)
    output = root/'R118_SHARED_ADMISSION_REPAIR'
    with (root/'SHARED_RUNNER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        saved = pristine(root)
        output.mkdir(exist_ok=False)
        child = identity = None
        status = 'FAILED'
        def interrupted(signum, frame):
            raise SystemExit(128+signum)
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        try:
            scan_until_clear(root, output, min(run.math.NATIVE-120,time.time()+180))
            run.require(pristine(root) == saved, 'no_calls_or_boundary_drift_during_admission')
            index = run.shared.read(root/'CONFIG.json')['index']
            with (root/'SHARED_RESIDENT.log').open('x') as log:
                child = subprocess.Popen([sys.executable, '-B', '-m', run.MODULE, 'resident', '--root', str(root)],
                    cwd=run.SOURCE, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True,
                    env=dict(os.environ,CUDA_VISIBLE_DEVICES=run.math.policy.DEVICES[index],PYTHONPATH=str(run.SOURCE),
                        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',
                        OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',TOKENIZERS_PARALLELISM='false'))
                identity = run.math.common.process_identity(Path('/proc')/str(child.pid))
                run.shared.write(root/'SHARED_LAUNCH.json',dict(identity=identity,uuid=run.math.policy.DEVICES[index],
                    activation_sha256=run.shared.sha(root/'SHARED_ACTIVATION.json'),started_unix=time.time(),
                    admission_only_repair=True,original_source_unchanged=True))
                run.require(child.wait(timeout=max(.01,run.math.HARD-time.time())) == 0,'shared_native_failed_no_retry')
                status = 'COMPLETE'
        except BaseException as error:
            run.shared.write(output/'FAILED.json',dict(error=str(error),type=type(error).__name__,
                native_launched=child is not None,finished_unix=time.time()))
            raise
        finally:
            if child is not None:
                if child.poll() is None:
                    run.math.common.stop_owned(child,identity)
                for path in (root/'shared_readout_bindings').glob('*.process.json'):
                    expected = run.shared.read(path)
                    directory = Path('/proc')/str(expected['pid'])
                    if directory.exists() and run.math.common.process_identity(directory) == expected:
                        descriptor = os.pidfd_open(expected['pid'])
                        try:
                            run.require(run.math.common.process_identity(directory) == expected and expected['uid'] == os.getuid(),
                                'only_owned_readout_cleanup')
                            signal.pidfd_send_signal(descriptor,signal.SIGTERM)
                        finally:
                            os.close(descriptor)
                run.shared.write(root/'SHARED_TERMINAL.json',dict(status=status,finished_unix=time.time(),
                    local_optimizer_steps=0,no_retry=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    args = parser.parse_args()
    guard(args.root)
