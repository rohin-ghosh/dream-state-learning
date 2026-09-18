import hashlib
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

BASE = Path('/localhome/local-rohing')
PINS = {
    'C1': '223a6320d922c5cd3e1b825f0503ad663a792bf159e76d09d8427a12583e09b2',
    'C2': 'b963ac8f2593dd6a3ec0ad4c9fd761456c0d649d36cae1324cbbc5106c673fac',
    'C4': 'dcf1709709f0cd12528f21e933f0dda1b2a4b8bc9eb96a09f5881112a6d642a2',
}
SOURCE_PINS = {
    'gpu/orch_r166_retelling_handoff.py': '655e72c553c934538b47e12987ffb9d493505f668721e0c432275b4617233681',
    'tests/test_orch_r166_retelling_handoff.py': 'a6ae913da890680b387d5b3568bea97667988777b8254493909c80316b9b5660',
    'gpu/orch_r166_corrected_retelling.py': '9277b09ca3f312bd7afa8bbcfc94f883940652c4199fe686c2ed47d73a992bcc',
    'tests/test_orch_r166_corrected_retelling.py': 'b6f4ef8a65c09fa93b9b9fa705fd73f6f0ee589375eafa75024aa1f91f88132e',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), 0o444)


def validate_go(go, binding):
    require(go.get('schema') == 'R166_SAVED_BOUNDARY_MAIN_GO_V1'
            and go.get('issuer') == 'Main' and go.get('decision') == 'GO'
            and go.get('binding') == binding, 'exact_Main_GO')
    start, end = go.get('not_before_unix'), go.get('expires_unix')
    require(all(type(value) in (int, float) and math.isfinite(value) for value in (start, end)),
            'finite_GO_times')
    require(start <= time.time() < end <= min(1789776000, binding['hard_end_unix'])
            and 0 < end - start <= 1800, 'fresh_bounded_GO')


def main(action):
    require(socket.gethostname().split('.')[0] == '[REDACTED_HOST]', 'exact_node5')
    require(action in ('prepare-go', 'dispatch'), 'explicit_action')
    candidates = []
    for agent, ready_sha in PINS.items():
        root = BASE / ('orch_r166_retelling_' + agent + '_20260917_activation4')
        require(sha(root / 'readiness/READY.json') == ready_sha, 'exact_READY')
        for relative, expected in SOURCE_PINS.items():
            require(sha(root / 'source' / relative) == expected, 'exact_source_pin_' + relative)
        for name in ('MAIN_DISPATCH_INTENT.json', 'MAIN_DISPATCH.json', 'MAIN_EXECUTE.log', 'ACTIVATE_ONCE'):
            require(not (root / name).exists(), 'no_retry_' + name)
        ready = json.loads((root / 'readiness/READY.json').read_text())
        go_path = root / 'MAIN_GO.json'
        if action == 'prepare-go':
            require(not go_path.exists(), 'fresh_GO_only')
            require(time.time() + 1800 <= min(1789776000, ready['required_GO_binding']['hard_end_unix']),
                    'original_wall')
        else:
            validate_go(json.loads(go_path.read_text()), ready['required_GO_binding'])
        candidates.append((agent, root, ready_sha, ready, go_path))

    for agent, root, ready_sha, ready, go_path in candidates:
        if action == 'prepare-go':
            now = time.time()
            go = dict(schema='R166_SAVED_BOUNDARY_MAIN_GO_V1', issuer='Main', decision='GO',
                      binding=ready['required_GO_binding'], not_before_unix=now, expires_unix=now + 1800)
            validate_go(go, ready['required_GO_binding'])
            write(go_path, go)
            print(json.dumps(dict(agent=agent, go_path=str(go_path), go_sha256=sha(go_path),
                                  ready_sha256=ready_sha, go=go)), flush=True)
        else:
            validate_go(json.loads(go_path.read_text()), ready['required_GO_binding'])
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


if __name__ == '__main__':
    require(len(sys.argv) == 2, 'one_explicit_action_required')
    main(sys.argv[1])
