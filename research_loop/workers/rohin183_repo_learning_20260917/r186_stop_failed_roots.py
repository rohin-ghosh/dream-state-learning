"""One TERM request per exact owned first-attempt unit and external bridge."""

import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


BASE = Path('/localhome/local-rohing/orch_r186_c2_plasticity_20260917')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def process_fields(pid):
    return Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()


def main():
    targets = []
    for label, physical in (('p4', 0), ('p32', 1), ('lr03', 5), ('lr3', 6)):
        root = BASE / (label + '1')
        started = json.loads((root / 'STARTED.json').read_bytes())
        assert started['physical'] == physical and started['raw_root'] == str(root / 'raw')
        guard_hash = sha(root / 'control/GUARD.json')
        assert guard_hash == started['guard_sha256']
        unit = 'orch-r186-c2-' + label + '-child-' + guard_hash[:16]
        proof = json.loads((root / 'control/CONFINEMENT_CHILD.json').read_bytes())
        assert proof['unit'] == unit and proof['target_minor'] == physical
        loaded = json.loads((root / 'raw/stream/records/00000000000000005129.json').read_bytes())
        native_pid = loaded['document']['pid']
        assert Path('/proc', str(native_pid), 'cgroup').read_text().strip() == '0::/system.slice/' + unit + '.service'
        command = Path('/proc', str(native_pid), 'cmdline').read_bytes().split(b'\0')
        assert str(root / 'control/GUARD.json').encode() in command
        bridge = started['processes']['cpu_bridge']
        pidfd = os.pidfd_open(bridge['pid'])
        assert process_fields(bridge['pid'])[19] == bridge['startticks']
        bridge_command = Path('/proc', str(bridge['pid']), 'cmdline').read_bytes().split(b'\0')
        assert b'gpu.r184_cpu_bridge' in bridge_command and str(root / 'BRIDGE.json').encode() in bridge_command
        manifest = json.loads((root / 'SOURCE.json').read_bytes())
        assert all(sha(root / 'source' / name) == expected for name, expected in manifest['source_pins'].items())
        assert not (root / 'raw/community_cpu').exists()
        targets.append((label, unit, native_pid, pidfd, bridge, guard_hash))
    with (BASE / 'ROOT_FAILURE_STOP_STARTED.json').open('x') as stream:
        json.dump(dict(started_unix=time.time(), labels=[item[0] for item in targets], no_retry=True,
            reason='pre_IO_tool_root_validation_failure_preserve_all_attempts'), stream)
    results = []
    for label, unit, native_pid, pidfd, bridge, guard_hash in targets:
        issued = time.time()
        result = subprocess.run(['sudo', '-n', 'systemctl', 'kill', '--kill-whom=all', '--signal=TERM', unit + '.service'],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15)
        signal.pidfd_send_signal(pidfd, signal.SIGTERM)
        os.close(pidfd)
        results.append(dict(label=label, unit=unit, native_pid=native_pid, bridge_pid=bridge['pid'],
            guard_sha256=guard_hash, requested_signal='SIGTERM', requested_unix=issued,
            systemctl_status=result.returncode, result=result.stdout, source_unchanged_before_stop=True,
            tool_attempt_directory_absent=True))
    deadline = time.time() + 20
    while time.time() < deadline and any(Path('/proc', str(item['native_pid'])).exists() for item in results):
        time.sleep(0.2)
    for item in results:
        item['native_exists_after'] = Path('/proc', str(item['native_pid'])).exists()
        item['bridge_exists_after'] = Path('/proc', str(item['bridge_pid'])).exists()
    receipt = dict(observed_unix=time.time(), results=results, no_GPU_2_3_4_7_action=True,
        sources_modified=False, artifacts_deleted=False, sigkill_requested=False)
    with (BASE / 'ROOT_FAILURE_STOP_RECEIPT.json').open('x') as stream:
        json.dump(receipt, stream, sort_keys=True)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
