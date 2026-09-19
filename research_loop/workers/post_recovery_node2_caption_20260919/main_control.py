"""Prepare fresh caption-only controls; never dispatch or load a model."""

import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent if '__file__' in globals() else None
REPO = HERE.parents[2] if HERE is not None else None


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def write_once(path, raw):
    import os
    with path.open('xb') as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def remote_prepare(payload):
    import os
    import socket
    manifest = payload['manifest']
    requirements = payload['requirements']
    original = payload['original_guard']
    source = Path(manifest['source'])
    control = Path(manifest['control'])
    require(source.parent == control.parent and control.name == 'control_checkpoint_tail_20260919_v2',
        'exact_reviewed_caption_control')
    require(not control.exists(), 'fresh_unused_control_required')
    plan_raw = base64.b64decode(payload['plan_b64'], validate=True)
    cpu_raw = base64.b64decode(payload['cpu_b64'], validate=True)
    plan = json.loads(plan_raw)
    cpu = json.loads(cpu_raw)
    fields = requirements['derivable']
    require(digest(plan_raw) == fields['plan_sha256'] and plan['source_root'] == str(source),
        'reviewed_plan_bytes')
    actual = {str(path.relative_to(source)): digest(path.read_bytes()) for path in source.rglob('*.py')}
    require(actual == manifest['source_pins'] == fields['source_pins'] == cpu['source_pins']
        and cpu['passed'] is True, 'actual_source_and_CPU_provenance')
    require(digest(socket.gethostname().encode()) == fields['host_sha256'], 'original_host')
    require(plan['physical'] == 2 and plan['gpu_uuid'] == 'GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05'
        and plan['hard_end_unix'] == 1789927200, 'same_GPU_and_deadline')
    require(digest(Path(original['lease_path']).read_bytes()) == original['lease_sha256'],
        'original_lease_bytes')
    require(os.statvfs('/').f_bavail * os.statvfs('/').f_frsize >= 24 * 1024 ** 3,
        'repaired_disk_headroom_required')
    processes = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
        '--format=csv,noheader'], text=True)
    require(not any(line.split(',')[0].strip() == plan['gpu_uuid'] for line in processes.splitlines()),
        'original_caption_device_must_be_idle')
    records = Path(fields['copy_raw']) / 'stream/records'
    indices = sorted(int(path.stem) for path in records.glob('*.json') if path.stem.isdigit())
    require(indices[-1] == 8528, 'exact_exited_caption_head')
    head = json.loads((records / '00000000000000008528.json').read_bytes())
    require(head['sha256'] == '58177fb38f89c7ab66cfa79a4f7d1a8c30d4eb1e8385dc410fb8abcc70a45c39',
        'same_caption_head')
    guard_source = (source / 'gpu/orch_r125_continual_guard.py').read_text()
    require("allocation['builder_entry_logged'] is True" in guard_source
        and "allocation['builder_entry_pushed'] is True" not in guard_source,
        'caption_original_logged_provenance_predicate')
    line = payload['builder_line']
    require('[Builder 2026-09-19] Pre-GPU non-material repair, extra node2 caption player ONLY:' in line
        and payload['builder_line_sha256'] == digest(line.encode()), 'logged_builder_line')
    control.mkdir(mode=0o700)
    write_once(control / 'PLAN.json', plan_raw)
    write_once(control / 'RECEIVING_CPU.json', cpu_raw)
    write_once(control / 'BUILDER_ENTRY.json', encoded(dict(line=line,
        line_sha256=payload['builder_line_sha256'], local_notebook='research_loop/COORDINATION.md',
        pushed=False, source_manifest_sha256=payload['manifest_sha256'])))
    allocation = dict(plan_sha256=digest(plan_raw), cpu_tests_passed=True,
        gpu_uuid=plan['gpu_uuid'], physical=plan['physical'], builder_entry_logged=True,
        builder_entry_path=str(control / 'BUILDER_ENTRY.json'),
        builder_entry_sha256=digest((control / 'BUILDER_ENTRY.json').read_bytes()),
        cpu_receipt_path=str(control / 'RECEIVING_CPU.json'), cpu_receipt_sha256=digest(cpu_raw),
        declared_unix=time.time())
    write_once(control / 'ALLOCATION.json', encoded(allocation))
    guard = dict(fields, allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=digest((control / 'ALLOCATION.json').read_bytes()),
        lease_path=original['lease_path'], lease_sha256=original['lease_sha256'])
    write_once(control / 'GUARD.json', encoded(guard))
    sys.path.insert(0, str(source))
    from gpu.orch_r125_continual_guard import validate
    validate(control / 'GUARD.json')
    return dict(observed_unix=time.time(), control=str(control), source=str(source),
        guard_sha256=digest((control / 'GUARD.json').read_bytes()),
        plan_sha256=digest(plan_raw), fresh_guard_validated=True,
        original_guard_changed=False, builder_entry_pushed=False,
        model_loaded=False, native_signals=[], dispatch_performed=False)


def main():
    if sys.argv[1:] == ['--remote']:
        print(json.dumps(remote_prepare(json.load(sys.stdin)), sort_keys=True, indent=2))
        return
    require(not sys.argv[1:], 'no_implicit_launch_or_other_mode')
    require(HERE is not None, 'local_control_frontend_required')
    manifest_raw = (HERE / 'prepared_v2/MANIFEST.json').read_bytes()
    builder = [line for line in (REPO / 'research_loop/COORDINATION.md').read_text().splitlines()
        if line.startswith('[Builder 2026-09-19] Pre-GPU non-material repair, extra node2 caption player ONLY:')]
    require(len(builder) == 1, 'one_actual_logged_builder_entry')
    payload = dict(manifest=json.loads(manifest_raw), manifest_sha256=digest(manifest_raw),
        requirements=json.loads((HERE / 'prepared_v2/GUARD_REQUIREMENTS.json').read_bytes()),
        original_guard=json.loads((HERE / 'original/GUARD.json').read_bytes()),
        builder_line=builder[0], builder_line_sha256=digest(builder[0].encode()),
        plan_b64=base64.b64encode((HERE / 'prepared_v2/PLAN_CANDIDATE.json').read_bytes()).decode(),
        cpu_b64=base64.b64encode((HERE / 'CPU_TEST_RECEIPT.json').read_bytes()).decode())
    command = '/localhome/local-rohing/v2/venv/bin/python -B -c ' + shlex.quote(Path(__file__).read_text()) + ' --remote'
    result = subprocess.run(['bash', str(REPO / 'gpu/ovx_ssh.sh'), command], input=encoded(payload),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    receipt = dict(returncode=result.returncode, stdout=result.stdout.decode(), stderr=result.stderr.decode(),
        observed_unix=time.time(), helper_sha256=digest(Path(__file__).read_bytes()))
    write_once(HERE / ('MAIN_CONTROL_' + str(time.time_ns()) + '.json'), encoded(receipt))
    print(result.stdout.decode(), end='')
    print(result.stderr.decode(), file=sys.stderr, end='')
    require(result.returncode == 0, 'control_preparation_failed_preserve_no_retry')


if __name__ == '__main__':
    main()
