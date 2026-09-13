import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


DRIVER = Path('/tmp/astra_projected_rulegame_formation_run_20260913.py')
SELF = Path(__file__).absolute()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('start', '_run'))
    parser.add_argument('--phase', choices=('formation',), required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--driver-sha256', required=True)
    parser.add_argument('--native-cpu-log', type=Path, required=True)
    parser.add_argument('--native-test-count', type=int, required=True)
    parser.add_argument('--stdout', type=Path, required=True)
    parser.add_argument('--allow-gpu', action='store_true')
    return parser.parse_args()


def run(args):
    if not args.allow_gpu or digest(DRIVER) != args.driver_sha256:
        raise ValueError('explicit opt-in and frozen driver required')
    spec = importlib.util.spec_from_file_location('main_projected_formation_driver', DRIVER)
    driver = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = driver
    spec.loader.exec_module(driver)
    root, plan, role, diagnostic = driver.checked_plan(args.root, args.plan_sha256)
    if plan['phase'] != args.phase or plan['python'] != os.path.abspath(sys.executable):
        raise ValueError('phase/native interpreter mismatch')
    text = args.native_cpu_log.read_text()
    if f'Ran {args.native_test_count} tests' not in text or not text.rstrip().endswith('OK'):
        raise ValueError('native CPU acceptance missing')
    logs = root.parent / (root.name + '_launch')
    if logs.exists() or (root / 'run').exists():
        raise ValueError('existing launch/run; never retry implicitly')
    cap = plan['controller_seconds']
    end = min(plan['deadline'], plan['lease_cutoff'])
    if time.time() + cap + driver.COLLECT >= end:
        raise ValueError('full phase and collection window unavailable')
    source = Path(plan['source_root'])
    sys.path.insert(0, str(source))
    from gpu.astra_mini_sudoku_diagnostic import check_free
    gpu, xml = check_free(plan['device'])
    receipt = driver.launch_contract(root, plan, args.plan_sha256, SELF, digest(SELF))
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['device'], V6_MODEL=plan['model'],
        PYTHONPATH=str(source), ASTRA_SOURCE_ROOT=str(source), HF_HUB_OFFLINE='1',
        TRANSFORMERS_OFFLINE='1', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
        OMP_NUM_THREADS='1', VLLM_WORKER_MULTIPROC_METHOD='spawn')
    logs.mkdir()
    with (logs / 'gpu.xml').open('x') as stream:
        stream.write(xml)
    with (logs / 'controller.log').open('xb') as stream:
        started = time.time()
        if started + cap + driver.COLLECT >= end:
            raise ValueError('preflight exhausted phase and collection window')
        process = subprocess.Popen(receipt['command'], cwd=source, env=environment,
            stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    receipt.update(pid=process.pid, pgid=os.getpgid(process.pid), session=os.getsid(process.pid),
        launcher_pid=os.getpid(), launcher_pgid=os.getpgrp(), launcher_session=os.getsid(0),
        started_wall=started, gpu_uuid=gpu['gpu_uuid'])
    driver.write_json(logs / 'launch.json', receipt)
    launch_pin = digest(logs / 'launch.json')
    print(json.dumps(dict(status='CONTROLLER_LAUNCHED_NOT_COMPLETED', launch_sha256=launch_pin,
        launch_root=str(logs), controller_pid=process.pid, controller_seconds=cap,
        launcher_pid=os.getpid(), collection_seconds=driver.COLLECT,
        started_wall=started, native_cpu_sha256=digest(args.native_cpu_log))), flush=True)
    returncode = process.wait()
    driver.write_json(logs / 'exit.json', dict(launch_sha256=launch_pin,
        returncode=returncode, ended_wall=time.time()))
    print(json.dumps(dict(status='CONTROLLER_EXITED_COLLECTION_REQUIRED', returncode=returncode)), flush=True)


def main():
    args = arguments()
    if not args.allow_gpu:
        raise ValueError('explicit GPU opt-in required')
    if args.mode == '_run':
        run(args)
        return
    if args.stdout.exists():
        raise ValueError('existing launcher stdout; preserve prior attempt')
    command = [os.path.abspath(sys.executable), '-B', str(SELF), '_run', *sys.argv[2:]]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    environment.pop('CUDA_VISIBLE_DEVICES', None)
    with args.stdout.open('xb') as stream:
        process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL,
            stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    print(json.dumps(dict(status='LAUNCHER_STARTED_NOT_GPU_CONFIRMATION', launcher_pid=process.pid,
        stdout=str(args.stdout), launcher_sha256=digest(SELF))), flush=True)


if __name__ == '__main__':
    main()
