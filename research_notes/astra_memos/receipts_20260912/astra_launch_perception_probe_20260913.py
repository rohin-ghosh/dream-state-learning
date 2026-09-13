"""Main-owned launch of the prepared, finite OFF perception probe."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def launch(options):
    root, driver, log = (Path(value).resolve() for value in (options.root, options.driver, options.stdout))
    if digest(driver) != options.driver_sha256 or digest(root / 'plan.json') != options.plan_sha256:
        raise ValueError('prepared source or plan changed')
    plan = json.loads((root / 'plan.json').read_bytes())
    if log.exists() or log == root or root in log.parents or (root / 'controller.started.json').exists():
        raise ValueError('existing launch/log or overlapping stdout')
    if plan['fit'] is not False or plan['adapter'] is not None or plan['scope'] != 'perception_DEV12_anchor_NO_FIT':
        raise ValueError('not the selected OFF-only probe')
    if plan['lease_end'] <= time.time() + 1080:
        raise ValueError('insufficient bounded lease window')
    if digest(options.precheck) != options.precheck_sha256:
        raise ValueError('allocation check changed')
    subprocess.run([sys.executable, '-B', options.precheck, '--gpu-index', str(plan['gpu_index']),
                    '--gpu-uuid', plan['gpu_uuid']], check=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
    command = [sys.executable, '-B', str(driver), 'controller', '--root', str(root),
               '--plan-sha256', options.plan_sha256, '--allow-gpu']
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid'], PYTHONDONTWRITEBYTECODE='1',
                       PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                       OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false',
                       CUBLAS_WORKSPACE_CONFIG=':4096:8', PYTHONHASHSEED='0')
    with log.open('xb') as stream:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
                                   cwd=driver.parent, env=environment, start_new_session=True)
    status = Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()
    return dict(status='LAUNCHED_NOT_SCIENTIFIC_RESULT', pid=process.pid, pgid=os.getpgid(process.pid),
                start_ticks=int(status[19]), launched_unix=time.time(), root=str(root), command=command,
                stdout=str(log), plan_sha256=options.plan_sha256, driver_sha256=options.driver_sha256,
                gpu_uuid=plan['gpu_uuid'], controller_seconds=900, collection_seconds=180)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('root', 'driver', 'stdout', 'driver-sha256', 'plan-sha256', 'precheck', 'precheck-sha256'):
        parser.add_argument('--' + name, required=True)
    print(json.dumps(launch(parser.parse_args()), sort_keys=True), flush=True)
