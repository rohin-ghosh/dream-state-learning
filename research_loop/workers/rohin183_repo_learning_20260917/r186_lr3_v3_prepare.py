"""Explicit new pre-native LR3 replacement with preserved admission diagnostics."""

import json
import os
from pathlib import Path
import signal
import subprocess
import tarfile

from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import digest, require, write


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
REMOTE = '/localhome/local-rohing/orch_r153_r186_c2_plasticity_20260917/lr33'


def build():
    previous = json.loads((ROOT / 'R186_ROOT_V2_LR3_SOURCE.json').read_bytes())
    files = {}
    for name, expected in previous['source_pins'].items():
        raw = (ROOT / 'r186_root_v2_lr3_source' / name).read_bytes()
        require(digest(raw) == expected, 'previous_frozen_source:' + name)
        files[name] = raw
    name = 'gpu/r184_node2_confinement.py'
    before = b"            require(report['scanner_euid']==0 and report['clear'] and not report['blocking_reasons'],'fresh_privileged_target_clear')"
    require(files[name].count(before) == 1, 'exact_unchanged_admission_predicate')
    addition = b"            write(attempt/'ALL_ADMISSION_SCAN.json',dict(report=report,observed_unix=time.time()))\n"
    files[name] = files[name].replace(before, addition + before, 1)
    source = ROOT / 'r186_lr3_v3_source'
    require(not source.exists(), 'fresh_LR3_pre_native_replacement')
    for relative, raw in files.items():
        write(source / relative, raw)
    manifest = dict(previous, source_pins={name: digest(raw) for name, raw in files.items()},
        previous_failed_manifest_sha256=digest((ROOT / 'R186_ROOT_V2_LR3_SOURCE.json').read_bytes()),
        source_delta='confinement_saves_scan_before_unchanged_admission_predicate',
        unchanged_consumed_pins={name: value for name, value in previous['source_pins'].items()
            if name != 'gpu/r184_node2_confinement.py'})
    write(ROOT / 'R186_LR3_V3_SOURCE.json', manifest)
    receive = (ROOT / 'r186_root_v2_receive.py').read_bytes()
    require(receive.count(b"(label + '2')") == 2 and receive.count(b"label + '_2.sock'") == 1,
        'fresh_root_and_socket_only_receiving_change')
    receive = receive.replace(b"(label + '2')", b"(label + '3')").replace(b"label + '_2.sock'", b"label + '_3.sock'")
    write(ROOT / 'r186_lr3_v3_receive.py', receive)
    archive_path = ROOT / 'R186_LR3_V3.tar.gz'
    with tarfile.open(archive_path, 'x:gz') as archive:
        archive.add(source, arcname='source')
        archive.add(ROOT / 'R186_LR3_V3_SOURCE.json', arcname='SOURCE.json')
        archive.add(ROOT / 'r186_lr3_v3_receive.py', arcname='receive.py')
        archive.add(ROOT / 'R186_SCOPE.md', arcname='SCOPE.md')
        archive.add(ROOT / 'R186_LR3_PRE_NATIVE_FAILURE.md', arcname='SCOPE_ADMISSION_ADDENDUM.md')
    payload = archive_path.read_bytes()
    command = 'set -eu; mkdir ' + REMOTE + '; cd ' + REMOTE + '; cat > PAYLOAD.tar.gz; ' + (
        'printf "%s  PAYLOAD.tar.gz\\n" ' + digest(payload) + ' | sha256sum -c -; tar -xzf PAYLOAD.tar.gz; ' +
        'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B receive.py prepare lr3')
    with (ROOT / 'R186_LR3_V3_RECEIVING.log').open('x') as output:
        result = subprocess.run(['bash', 'gpu/ovx_ssh.sh', command], cwd=REPO, input=payload,
            stdout=output, stderr=subprocess.STDOUT, timeout=120)
    print(json.dumps(dict(returncode=result.returncode, source_manifest_sha256=digest((ROOT / 'R186_LR3_V3_SOURCE.json').read_bytes()),
        payload_sha256=digest(payload), native_dispatched=False)))


if __name__ == '__main__':
    build()
