import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write('\n')


def main():
    helper = Path('/tmp/astra_level1_next_batch_20260913.py')
    assert digest(helper) == '03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2'
    spec = importlib.util.spec_from_file_location('batch_reservations', helper)
    batch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(batch)
    smoke = Path('/tmp/astra_a100_native_readiness_20260913.py')
    assert digest(smoke) == '1d971c12e27ca00c4f1dcfb6158267b48b7944a142e62e64b9b3eab83b5a171d'
    prechecks = Path('/tmp/astra_a100_full_readiness_20260913T0752Z.prechecks.json')
    assert digest(prechecks) == '256fd5ba7a98f320ae8fea7bf014c82d8a213f3bffd1a8250ba5cb311ac47cc5'
    config = json.loads(prechecks.read_text())['a100']
    gpu_uuid = 'GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6'
    root = Path('/localhome/local-rohing/astra_diagnostics/a100_native_readiness_20260913_attempt1')
    claim = Path(str(root) + '.launcher')
    assert not root.exists()
    claim.mkdir()
    process = None
    try:
        write(claim / 'reservations.json', batch.reservations(config, 0, gpu_uuid))
        result = subprocess.run(['nvidia-smi', '-q', '-x'], capture_output=True, check=True, timeout=30)
        devices = ET.fromstring(result.stdout).findall('gpu')
        assert devices[0].findtext('uuid') == gpu_uuid
        assert not devices[0].findall('processes/process_info')
        write(claim / 'gpu.json', dict(time=time.time(), gpu_uuid=gpu_uuid, processes=[],
                                       query_sha256=hashlib.sha256(result.stdout).hexdigest()))
        command = ['timeout', '--signal=TERM', '--kill-after=10s', '580s', sys.executable,
                   '-B', str(smoke), '--allow-gpu', '--output', str(root)]
        with (claim / 'stdout.log').open('xb') as output:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output,
                                       stderr=subprocess.STDOUT, start_new_session=True,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=gpu_uuid))
        receipt = dict(status='LAUNCHED_NOT_RESULT', pid=process.pid, pgid=process.pid,
                       identity=batch.identity(Path('/proc') / str(process.pid)),
                       started_unix=time.time(), root=str(root), gpu_index=0, gpu_uuid=gpu_uuid,
                       command=command, infrastructure_only=True, total_cap_seconds=590)
        write(claim / 'launched.json', receipt)
        print(json.dumps(receipt, sort_keys=True), flush=True)
    except BaseException as error:
        write(claim / 'failure.json', dict(error=repr(error), retry=False,
                                          controller_may_be_running=process is not None))
        raise


if __name__ == '__main__':
    main()
