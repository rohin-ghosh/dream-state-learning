"""Explicit pre-inference route admission recovery without changing frozen actors."""

import argparse
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bound(reference):
    path = Path(reference['path'])
    require(path.is_absolute() and not path.is_symlink(), 'absolute_regular_reference')
    require(digest(path) == reference['sha256'], 'unchanged_reference')
    return json.loads(path.read_text())


def write_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def no_inference(root):
    for name in ('DISPATCH', 'SUPERVISOR', 'ACTOR_READY', 'FRESH_BOOTSTRAP',
                 'TERMINAL', 'ADMISSION'):
        require(not (root / ('R118_PARALLEL_' + name + '.json')).exists(),
                'pre_inference_only_' + name)
    require(not (root / 'R118_PARALLEL_SUPERVISOR.log').exists(), 'no_previous_supervisor_log')


def verify(request, lifecycle):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_launcher_requires_empty_CVD_at_exec')
    require(request['authorized_by_Main'] is True and request['scope'] == 'PRE_INFERENCE_STARTUP_ONLY',
            'explicit_new_startup_scope')
    require(time.time() < request['expires_unix'] <= lifecycle.boundary.TRAIN_END - 180,
            'original_startup_window')
    root = Path(request['root']).resolve(strict=True)
    require(request['plan']['path'] == str(root / lifecycle.PLAN), 'exact_original_plan')
    plan = bound(request['plan'])
    require(plan == lifecycle.verify_plan(root, gpu=False), 'frozen_plan_verified')
    for reference in request['preserved_failures']:
        bound(reference)
    require(request['failed_dispatch']['sha256'] != os.environ.get('R118_PARALLEL_SESSION_SHA256'),
            'not_original_dispatch_retry')
    previous = bound(request['failed_dispatch'])
    failure = bound(request['failed_dispatch_terminal'])
    require(failure['session_sha256'] == request['failed_dispatch']['sha256']
            and failure['retry_allowed'] is False, 'actual_failed_session_preserved')
    branch = plan['shared_learner']['branch']
    require(branch in ('F1', 'A1') and previous['owners'][branch]['bootstrap_path'] ==
            str(root / 'R118_PARALLEL_FRESH_BOOTSTRAP.json'), 'same_original_route_branch')
    require(not Path('/proc', str(failure['spawned'][branch])).exists(),
            'original_CPU_launcher_absent')
    require(digest(root / 'RESERVATIONS.jsonl') == request['reservations_sha256'], 'no_new_charges')
    old_attempt = root / 'R118_PARALLEL_LAUNCH_ATTEMPT.json'
    if request['old_attempt'] is None:
        require(not old_attempt.exists(), 'original_attempt_absent')
    else:
        require(request['old_attempt']['path'] == str(old_attempt), 'exact_failed_attempt')
        bound(request['old_attempt'])
    no_inference(root)
    lifecycle.boundary.released(root, plan['route_boundary_release'])
    lifecycle.verify_retirements(lifecycle.bound(plan['parallel_stage']['authorization']))
    lifecycle.validate_broker_binding(root, plan)
    return root, plan


def launch(request, lifecycle, backend):
    root, plan = verify(request, lifecycle)
    session_path = os.environ['R118_PARALLEL_SESSION']
    session_sha = os.environ['R118_PARALLEL_SESSION_SHA256']
    require(session_sha != request['failed_dispatch']['sha256'], 'fresh_session_required')
    session, control = backend.fresh_session(session_path, session_sha)
    branch = plan['shared_learner']['branch']
    require(os.environ['R118_PARALLEL_BRANCH'] == branch, 'same_branch')
    require(not (control / 'FAILED.json').exists() and time.time() < session['startup_deadline_unix'],
            'fresh_dispatch_not_failed')
    start = backend.read(control / 'START.json')
    require(start['session_sha256'] == session_sha, 'actual_fresh_dispatch')
    backend.live_identity(start['identity'])
    require(session['source_files'].get(str(Path(__file__).resolve())) == digest(__file__),
            'recovery_source_in_fresh_session')
    directory = Path(request['attempt_directory'])
    require(directory.is_absolute() and directory.parent.resolve() == root,
            'root_local_new_attempt_namespace')
    require(directory.name.startswith('R118_STARTUP_RECOVERY_'), 'new_namespace_only')
    with (root / 'R118_PARALLEL_LAUNCH.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify(request, lifecycle)
        directory.mkdir()
        write_new(directory / 'ATTEMPT.json', dict(request=request, session_sha256=session_sha,
                  started_unix=time.time(), launcher_CVD='', old_attempt_preserved=True))
        try:
            prefix = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                      'PYTHONPATH=' + plan['parallel_source'], 'python3', '-B', '-m', lifecycle.MODULE]
            for phase in ('service', 'scan'):
                report = subprocess.run(prefix + [phase, '--root', str(root)],
                    capture_output=True, check=False, timeout=100)
                write_new(directory / (phase.upper() + '.json'), dict(returncode=report.returncode,
                    stdout=report.stdout.decode(), stderr=report.stderr.decode()))
                require(report.returncode == 0, 'strict_' + phase + '_succeeded')
            admission = json.loads(report.stdout)
            require(admission['clear'] is True, 'fresh_privileged_UUID_minor_proc_clear_no_waiver')
            no_inference(root)
            write_new(root / 'R118_PARALLEL_ADMISSION.json', admission)
            environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'],
                PYTHONPATH=plan['parallel_source'], HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                PYTHONDONTWRITEBYTECODE='1')
            with (root / 'R118_PARALLEL_SUPERVISOR.log').open('x') as stream:
                process = subprocess.Popen([sys.executable, '-B', '-m', lifecycle.MODULE,
                    'supervise', '--root', str(root)], cwd=plan['parallel_source'], env=environment,
                    stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
                    start_new_session=True)
            result = dict(supervisor=lifecycle.boundary.prior.identity(process.pid),
                started_unix=time.time(), plan=request['plan'], native_loaded=False,
                no_recovery_loop=True, startup_recovery=str(directory))
            write_new(root / 'R118_PARALLEL_DISPATCH.json', result)
            write_new(directory / 'DISPATCH.json', result)
            return result
        except BaseException as error:
            write_new(directory / 'FAILED.json', dict(error=type(error).__name__ + ': ' + str(error),
                      failed_unix=time.time(), no_automatic_retry=True))
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--verify-only', action='store_true')
    arguments = parser.parse_args()
    request = bound(dict(path=arguments.request, sha256=arguments.request_sha256))
    require(request['source']['path'] == str(Path(__file__).resolve())
            and request['source']['sha256'] == digest(__file__), 'exact_recovery_source')
    sys.path.insert(0, request['frozen_source'])
    lifecycle = importlib.import_module('gpu.orch_r118_route_parallel_lifecycle')
    require(str(Path(lifecycle.__file__).resolve()) == request['frozen_source'] +
            '/gpu/orch_r118_route_parallel_lifecycle.py', 'actual_frozen_lifecycle_import')
    if arguments.verify_only:
        verify(request, lifecycle)
        print(json.dumps(dict(status='CPU_VERIFIED_NOT_DISPATCHED')))
    else:
        backend = importlib.import_module('gpu.orch_r118_parallel_consolidation')
        print(json.dumps(launch(request, lifecycle, backend)))


if __name__ == '__main__':
    main()
