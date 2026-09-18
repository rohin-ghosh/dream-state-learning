import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

BASE = Path('/localhome/local-rohing')
PINS = {
    'C1': '4cf730d911d149c19beff7402883993f12ef1dcf13a6b4c5f584b0b4aed0edcc',
    'C2': '9567c79c1e8160c31000539db089cdbfe63674d5bf7b2de2f7bebf09cb7da17d',
    'C4': '73c3f2f047f5c9c936c2b37f44e7bf7180bc089bc9c00b9de71b2cf7b820309a',
    'C5': '4da5a46f36514b97c89b0311f8636050dc1e0da2a7beffe8fe96d7a876bb6a58',
}
SOURCE_PINS = {
    'gpu/orch_r166_retelling_handoff.py': 'ae9fec2a97cb59d1555dbf87519dffd19bfb7cf5cc3801e6ad975ecebb0e2a19',
    'tests/test_orch_r166_retelling_handoff.py': '6bca4a95d0e4461b6fb0085c6554cedb974d7f3549f2166c7bcb3321a5c43f34',
    'gpu/orch_r166_corrected_retelling.py': '9277b09ca3f312bd7afa8bbcfc94f883940652c4199fe686c2ed47d73a992bcc',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


assert socket.gethostname().split('.')[0] == '[REDACTED_HOST]'
assert sys.argv[1] in ('prepare-go', 'dispatch')
for agent, ready_sha in PINS.items():
    root = BASE / ('orch_r166_retelling_' + agent + '_20260917_activation2')
    assert sha(root / 'readiness/READY.json') == ready_sha
    for relative, expected in SOURCE_PINS.items():
        assert sha(root / 'source' / relative) == expected
    assert not (root / 'MAIN_DISPATCH_INTENT.json').exists()
    assert not (root / 'ACTIVATE_ONCE').exists()

for agent, ready_sha in PINS.items():
    root = BASE / ('orch_r166_retelling_' + agent + '_20260917_activation2')
    ready = json.loads((root / 'readiness/READY.json').read_text())
    go_path = root / 'MAIN_GO.json'
    if sys.argv[1] == 'prepare-go':
        now = time.time()
        assert now + 1800 <= 1789776000
        go = dict(schema='R166_SAVED_BOUNDARY_MAIN_GO_V1', issuer='Main', decision='GO',
                  binding=ready['required_GO_binding'], not_before_unix=now, expires_unix=now + 1800)
        write(go_path, go)
        print(json.dumps(dict(agent=agent, go_path=str(go_path), go_sha256=sha(go_path),
                              ready_sha256=ready_sha, go=go)), flush=True)
    else:
        go = json.loads(go_path.read_text())
        assert go['binding'] == ready['required_GO_binding']
        assert go['not_before_unix'] <= time.time() < go['expires_unix'] <= 1789776000
        command = [str(BASE / 'v2/venv/bin/python'), '-B', '-m', 'gpu.orch_r166_retelling_handoff',
                   'execute', '--output', str(root), '--main-go', str(go_path), '--main-go-sha256', sha(go_path)]
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                           PYTHONPATH=str(root / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        intent = dict(agent=agent, command=command, ready_sha256=ready_sha, go_sha256=sha(go_path),
                      observed_unix=time.time(), no_retry=True)
        write(root / 'MAIN_DISPATCH_INTENT.json', intent)
        with (root / 'MAIN_EXECUTE.log').open('x') as log:
            process = subprocess.Popen(command, cwd=root / 'source', env=environment,
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True, close_fds=True)
        stat = Path('/proc') / str(process.pid) / 'stat'
        ticks = stat.read_text().rsplit(')', 1)[1].split()[19]
        receipt = dict(intent, pid=process.pid, start_ticks=ticks,
                       status='CPU_OPERATOR_DISPATCHED_NOT_NATIVE_LOADED', observed_unix=time.time())
        write(root / 'MAIN_DISPATCH.json', receipt)
        print(json.dumps(receipt), flush=True)
