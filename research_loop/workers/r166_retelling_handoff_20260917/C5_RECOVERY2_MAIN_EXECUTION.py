import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

root = Path('/localhome/local-rohing/orch_r166_retelling_C5_20260917_recovery2')
pins = {
    'readiness/READY.json': '2fb6e99746f81451c1563c0c5a14d0b9ec4fb491070dbc6cb686525cbf151718',
    'source/gpu/orch_r166_retelling_handoff.py': '655e72c553c934538b47e12987ffb9d493505f668721e0c432275b4617233681',
    'source/tests/test_orch_r166_retelling_handoff.py': 'a6ae913da890680b387d5b3568bea97667988777b8254493909c80316b9b5660',
    'source/gpu/orch_r166_corrected_retelling.py': '9277b09ca3f312bd7afa8bbcfc94f883940652c4199fe686c2ed47d73a992bcc',
    'source/tests/test_orch_r166_corrected_retelling.py': 'b6f4ef8a65c09fa93b9b9fa705fd73f6f0ee589375eafa75024aa1f91f88132e',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), 0o444)


assert socket.gethostname().split('.')[0] == '[REDACTED_HOST]'
assert len(sys.argv) == 2 and sys.argv[1] in ('prepare-go', 'dispatch')
assert all(sha(root / name) == checksum for name, checksum in pins.items())
assert not any((root / name).exists() for name in ('MAIN_DISPATCH_INTENT.json', 'ACTIVATE_ONCE', 'attempt'))
ready = json.loads((root / 'readiness/READY.json').read_text())
binding = ready['required_GO_binding']
assert binding['boundary_rule'] == 'EXACT_RETIRED_C5_SAVED28_NO_NEW_RECORDS'
go_path = root / 'MAIN_GO.json'
if sys.argv[1] == 'prepare-go':
    now = time.time()
    assert now + 1800 <= binding['hard_end_unix'] == 1789776000
    go = dict(schema='R166_C5_RETIRED_RECOVERY_MAIN_GO_V1', issuer='Main', decision='GO',
              binding=binding, not_before_unix=now, expires_unix=now+1800)
    write(go_path, go)
    print(json.dumps(dict(go_path=str(go_path), go_sha256=sha(go_path), go=go, observed_unix=time.time())), flush=True)
else:
    go = json.loads(go_path.read_text())
    assert go['schema'] == 'R166_C5_RETIRED_RECOVERY_MAIN_GO_V1' and go['issuer'] == 'Main' and go['decision'] == 'GO'
    assert go['binding'] == binding and go['not_before_unix'] <= time.time() < go['expires_unix'] <= 1789776000
    assert 0 < go['expires_unix'] - go['not_before_unix'] <= 1800
    command = ['/localhome/local-rohing/v2/venv/bin/python', '-B', '-m', 'gpu.orch_r166_retelling_handoff',
               'execute-recovery', '--output', str(root), '--main-go', str(go_path), '--main-go-sha256', sha(go_path)]
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                       PYTHONPATH=str(root / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    intent = dict(command=command, go_sha256=sha(go_path), ready_sha256=pins['readiness/READY.json'],
                  observed_unix=time.time(), no_retry=True, no_retirement=True)
    write(root / 'MAIN_DISPATCH_INTENT.json', intent)
    with (root / 'MAIN_EXECUTE.log').open('x') as log:
        process = subprocess.Popen(command, cwd=root / 'source', env=environment,
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True, close_fds=True)
    ticks = (Path('/proc') / str(process.pid) / 'stat').read_text().rsplit(')', 1)[1].split()[19]
    receipt = dict(intent, pid=process.pid, start_ticks=ticks, status='CPU_RECOVERY_DISPATCHED_NOT_LOADED',
                   observed_unix=time.time())
    write(root / 'MAIN_DISPATCH.json', receipt)
    print(json.dumps(receipt), flush=True)
