"""Copy only the pinned prior source closure into the new diagnostic root."""

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time


ROOT = Path('/localhome/local-rohing/orch_r163_numerical_diagnostic_20260917_attempt2')
OLD = Path('/localhome/local-rohing/orch_r163_numerical_preparation_20260917_attempt1')
SOURCE = ROOT / 'selected_source'
CONTROL = ROOT / 'control'
LIMIT = 1024**3


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    assert socket.gethostname() == '[REDACTED_HOST]'
    assert os.getuid() == os.getgid() == 2524
    assert os.environ['CUDA_VISIBLE_DEVICES'] == ''
    assert not SOURCE.exists() and not CONTROL.exists()
    manifest_path = OLD / 'control_candidate3/SOURCE_PINS.json'
    manifest_raw = manifest_path.read_bytes()
    assert digest(manifest_raw) == '71ea6c8b9a878f81e753e09869122ca60eb493b1e3f7c48cc4de18aa957718e9'
    manifest = json.loads(manifest_raw)
    assert len(manifest['files']) == 2158
    prior_source = OLD / 'selected_source_candidate3'
    expected = {str(path) for path in prior_source.rglob('*') if path.is_file()}
    assert expected == set(manifest['files']) - {str(OLD / 'control_candidate3/admitted_probe.py')}
    total = sum(Path(name).stat().st_size for name in manifest['files'])
    assert total < 64*1024**2
    updates = json.loads((ROOT / 'INPUT_PINS.json').read_bytes())
    for name, checksum in updates.items():
        assert digest((ROOT / 'inputs' / name).read_bytes()) == checksum
    replacements = {'gpu/orch_r163_executor_probe.py': 'orch_r163_executor_probe.py',
                    'tests/test_orch_r163_executor_probe.py': 'test_orch_r163_executor_probe.py'}
    SOURCE.mkdir()
    CONTROL.mkdir()
    changes = {}
    for name, checksum in manifest['files'].items():
        path = Path(name)
        assert path.resolve() == path and not path.is_symlink() and path.stat().st_mode & 0o222 == 0
        raw = path.read_bytes()
        assert digest(raw) == checksum
        if not path.is_relative_to(prior_source):
            continue
        relative = str(path.relative_to(prior_source))
        if relative in replacements:
            raw = (ROOT / 'inputs' / replacements[relative]).read_bytes()
            changes[relative] = dict(old_sha256=checksum, new_sha256=digest(raw))
        target = SOURCE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write(raw)
        target.chmod(0o444)
    for name in ('admitted_probe.py', 'test_admitted_probe.py', 'prepare_control.py', 'CPU_attempt5.json'):
        raw = (ROOT / 'inputs' / name).read_bytes()
        with (CONTROL / name).open('xb') as handle:
            handle.write(raw)
        (CONTROL / name).chmod(0o444)
    for directory in sorted((path for path in SOURCE.rglob('*') if path.is_dir()), reverse=True):
        directory.chmod(0o555)
    SOURCE.chmod(0o555)
    lease = Path('/localhome/local-rohing/orch_r118_node3_7_grid_20260915_attempt1/lease_budget_r119_learned/LEASE_BUDGET.json')
    lease_raw = lease.read_bytes()
    assert digest(lease_raw) == '919e9fb3f9cfd6cadb57af90844319e50eb114068eb52cd75aa3ab715f9c3770'
    hardware = subprocess.check_output(['nvidia-smi', '-i', '5', '--query-gpu=index,uuid,name,memory.total,memory.used,utilization.gpu', '--format=csv,noheader'], text=True)
    assert hardware.startswith('5, GPU-bc211959-642d-664b-3581-42a0dbe434e9, NVIDIA A40,')
    assert os.minor(os.stat('/dev/nvidia5').st_rdev) == 5
    receipt = dict(schema='R163_ATTEMPT2_STAGING_V1', observed_unix=time.time(),
        hostname=socket.gethostname(), source_files=2157, manifest_files_including_operator=2158,
        predecessor_manifest=dict(path=str(manifest_path), sha256=digest(manifest_raw)),
        predecessor_files_verified=True, predecessor_bytes=total, replacements=changes,
        lease=dict(path=str(lease), sha256=digest(lease_raw), value=json.loads(lease_raw)),
        physical5=hardware, physical5_minor=5, remote_preparation_limit_bytes=LIMIT,
        source_copy_read_write_upper_bound_bytes=2*total+2*1024**2,
        no_old_writes=True, no_cuda_allocation=True, no_dispatch=True,
        provider_booking_verified=False)
    with (CONTROL / 'STAGING.json').open('x') as handle:
        json.dump(receipt, handle, sort_keys=True, indent=2)
        handle.write('\n')
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
