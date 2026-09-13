"""Main-owned detachment only; Q0 owns its closed scientific lifecycle."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def digest(filename):
    return hashlib.sha256(Path(filename).read_bytes()).hexdigest()


def launch(source, root, executor_sha256, manifest_sha256, stdout, allow_gpu=False):
    if not allow_gpu:
        raise ValueError('explicit Main GPU opt-in required')
    source, root, stdout = Path(source), Path(root), Path(stdout)
    if not all(filename.is_absolute() for filename in (source, root, stdout)):
        raise ValueError('absolute paths required')
    executor = source / 'gpu/astra_pairwise_q0.py'
    if digest(executor) != executor_sha256 or digest(root / 'manifest.json') != manifest_sha256:
        raise ValueError('executor or prepared manifest changed')
    if stdout.exists() or stdout.is_symlink() or stdout == root or root in stdout.parents:
        raise ValueError('fresh output outside immutable evidence root required')
    if (root / 'STARTED.json').exists() or (root / 'SEAL.json').exists():
        raise ValueError('existing execution; never restart implicitly')
    manifest = json.loads((root / 'manifest.json').read_bytes())
    seal = json.loads((root / 'PREPARED.json').read_bytes())
    if not manifest['ready'] or seal['manifest_sha256'] != manifest_sha256:
        raise ValueError('prepared public-model binding required')
    config = manifest['config']
    if time.time() + 2700 >= config['lease_cutoff_unix']:
        raise ValueError('complete closed runtime window unavailable')
    command = [os.path.abspath(sys.executable), '-B', str(executor), 'execute', '--out', str(root), '--allow-gpu']
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=config['gpu_uuid'], CUBLAS_WORKSPACE_CONFIG=':4096:8',
        PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
        PYTHONHASHSEED='0', TOKENIZERS_PARALLELISM='false')
    with stdout.open('xb') as stream:
        process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
            stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    return dict(status='CONTROLLER_STARTED_NOT_SCIENTIFIC_RESULT', controller_pid=process.pid,
        command=command, stdout=str(stdout), source=str(source), manifest_sha256=manifest_sha256,
        executor_sha256=executor_sha256, gpu_uuid=config['gpu_uuid'], started_wall=time.time(),
        launcher_sha256=digest(__file__), runtime_cap_seconds=2700)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'root', 'executor-sha256', 'manifest-sha256', 'stdout'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--allow-gpu', action='store_true')
    print(json.dumps(launch(**vars(parser.parse_args())), sort_keys=True))


if __name__ == '__main__':
    main()
