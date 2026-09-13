import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

SOURCE = Path('/localhome/local-rohing/astra_sources/q0_readout_supplement_20260913_attempt1')
ROOT = Path('/localhome/local-rohing/astra_diagnostics/q0_R1_readout_supplement_20260913_attempt2')
PRECHECK = Path('/tmp/astra_node2_prelaunch_20260913.py')
EXPECTED = 'c7705a6843055d30c6582279779a0cc80a2603dbe4eb09781618d2eed2cfeb49'
GPU = 'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def check(root, source, precheck):
    if set(path.name for path in root.iterdir()) != {'manifest.json', 'prepared.json', 'requests.json', 'custody.json', 'PREPARED.json'}:
        raise ValueError('prepared-only root, no retry')
    if digest(root / 'manifest.json') != EXPECTED:
        raise ValueError('prepared manifest pin')
    plan = json.loads((root / 'manifest.json').read_bytes())
    if plan['version'] != 'astra-q0-final-readout-supplement-v1' or plan['config']['gpu_uuid'] != GPU:
        raise ValueError('fixed supplement/GPU')
    if plan['admission']['original_primary_label'] != 'NONREPORTABLE_RUNTIME_ABORT':
        raise ValueError('original primary abort must remain')
    if time.time() + 3780 > plan['config']['lease_cutoff_unix']:
        raise ValueError('lease margin')
    if digest(precheck) != 'b3aa9e36b5e12893f9602a61d4b4575874f23dec58eddacdcab92c2a1b079bff':
        raise ValueError('targeted checker pin')
    for name, expected in plan['source_pins'].items():
        if digest(source / name) != expected:
            raise ValueError('source pin: ' + name)
    return plan


def launch(root=ROOT, source=SOURCE, precheck=PRECHECK):
    plan = check(root, source, precheck)
    claim = root.with_name(root.name + '.launcher')
    claim.mkdir()
    stdout = Path('/tmp/astra_q0_R1_supplement_20260913_attempt2.controller.log')
    command = [sys.executable, '-B', '-m', 'gpu.astra_q0_readout_supplement', 'execute', '--out', str(root), '--allow-gpu']
    write(claim / 'claimed.json', dict(root=str(root), source=str(source), manifest_sha256=EXPECTED, command=command, time=time.time()))
    process = None
    try:
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', CUBLAS_WORKSPACE_CONFIG=':4096:8', PYTHONDONTWRITEBYTECODE='1',
                           HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONPATH=str(source))
        vacancy = subprocess.run([sys.executable, '-B', str(precheck), '--gpu-index', '1', '--gpu-uuid', GPU],
                                 env=environment, capture_output=True, text=True, timeout=130)
        write(claim / 'precheck.json', dict(returncode=vacancy.returncode, stdout=vacancy.stdout, stderr=vacancy.stderr, checked=time.time()))
        if vacancy.returncode != 0:
            raise ValueError('GPU1 vacancy/reservation check failed; no launch')
        if check(root, source, precheck) != plan:
            raise ValueError('prepared plan changed')
        with stdout.open('xb') as stream:
            process = subprocess.Popen(command, cwd=source, env=dict(environment, CUDA_VISIBLE_DEVICES=GPU),
                                       stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        fields = Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()
        if process.poll() is not None or os.getpgid(process.pid) != process.pid or fields[0] in ('Z', 'X'):
            raise ValueError('controller identity not confirmed; reconcile, never retry')
        receipt = dict(status='LAUNCHED_NOT_RESULT', pid=process.pid, pgid=os.getpgid(process.pid), start_ticks=int(fields[19]),
                       root=str(root), source=str(source), command=command, stdout=str(stdout), gpu_index=1, gpu_uuid=GPU,
                       time=time.time(), seconds_cap=3600, collection_seconds=180, original_primary_label='NONREPORTABLE_RUNTIME_ABORT',
                       manifest_sha256=EXPECTED, launcher_sha256=digest(__file__))
        write(claim / 'detached.json', receipt)
        print(json.dumps(receipt, sort_keys=True))
        return receipt
    except BaseException as error:
        write(claim / 'failure.json', dict(error=repr(error), pid=None if process is None else process.pid,
                                         controller_may_be_running=process is not None, retry=False, time=time.time()))
        raise


if __name__ == '__main__':
    if sys.argv[1:] != ['--allow-gpu']:
        raise ValueError('Main explicit --allow-gpu required')
    launch()
