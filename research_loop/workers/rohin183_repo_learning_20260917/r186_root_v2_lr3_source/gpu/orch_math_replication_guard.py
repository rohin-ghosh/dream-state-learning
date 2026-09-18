"""Independent physical allocation scanner and bounded owned-process guardian."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


ALLOWED = {2, 3, 4}
LEASE_END = int(datetime(2026, 9, 20, 3, 3, tzinfo=timezone.utc).timestamp())


def require_lease(now, seconds=2700):
    if not 0 < seconds <= 2700 or now + seconds >= LEASE_END - 21600:
        raise ValueError('lease_margin_or_runtime_violation')


def evaluate_snapshot(snapshot, index, uuid):
    reasons = []
    if index not in ALLOWED or snapshot['gpu']['index'] != index or snapshot['gpu']['uuid'] != uuid:
        reasons.append('physical_allocation_mismatch')
    if snapshot['gpu']['memory_used_mib'] > 32:
        reasons.append('unexplained_device_memory')
    if snapshot['gpu']['utilization_percent'] != 0:
        reasons.append('device_not_idle')
    for process in snapshot['compute_processes']:
        if process['gpu_uuid'] == uuid:
            reasons.append('active_compute_pid:' + str(process['pid']))
    for process in snapshot['processes']:
        if process.get('vanished'):
            continue
        if process.get('unreadable'):
            reasons.append('unknown_process_visibility:' + str(process['pid']))
            continue
        devices = process.get('cvd')
        if devices not in (None, '', '-1'):
            selections = [selection.strip() for selection in devices.split(',')]
            if uuid in selections or str(index) in selections:
                reasons.append('reserved_cvd_pid:' + str(process['pid']))
            elif any(not selection.startswith('GPU-') for selection in selections):
                reasons.append('unknown_numeric_or_special_cvd:' + str(process['pid']))
        if process.get('target_device_open') and not process.get('verified_persistence_service'):
            reasons.append('open_device_pid:' + str(process['pid']))
    return sorted(set(reasons))


def command_output(command):
    return subprocess.check_output(command, text=True, timeout=20).strip()


def scan(index, uuid, service_identity=None):
    if index not in ALLOWED or not uuid.startswith('GPU-'):
        raise ValueError('only_assigned_physical_uuid_scan_allowed')
    if os.geteuid() != 0:
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                   'python3', str(Path(__file__).resolve()), '--snapshot-only',
                   '--index', str(index), '--uuid', uuid]
        if service_identity:
            command.extend(['--service-identity', str(service_identity)])
        snapshot = json.loads(subprocess.check_output(command, text=True, timeout=30))
        if snapshot['blocking_reasons'] != evaluate_snapshot(snapshot, index, uuid):
            raise ValueError('privileged_snapshot_policy_mismatch')
        return snapshot
    expected_service = json.loads(service_identity.read_text()) if service_identity else None
    fields = command_output(['nvidia-smi', '-i', str(index),
              '--query-gpu=index,uuid,memory.used,utilization.gpu', '--format=csv,noheader,nounits']).split(',')
    snapshot = dict(created_utc=datetime.now(timezone.utc).isoformat(), scanner_pid=os.getpid(),
                    gpu=dict(index=int(fields[0]), uuid=fields[1].strip(),
                             memory_used_mib=int(fields[2]), utilization_percent=int(fields[3])),
                    compute_processes=[], processes=[])
    raw = command_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'])
    for line in raw.splitlines():
        device, process_id = line.split(',')
        snapshot['compute_processes'].append(dict(gpu_uuid=device.strip(), pid=int(process_id)))
    for directory in sorted(Path('/proc').iterdir()):
        if not directory.name.isdigit() or int(directory.name) == os.getpid():
            continue
        entry = dict(pid=int(directory.name))
        try:
            commandline = (directory / 'cmdline').read_bytes()
            if not commandline:
                continue
            entry['uid'] = directory.stat().st_uid
            entry['command_sha256'] = hashlib.sha256(commandline).hexdigest()
            entry['start_ticks'] = (directory / 'stat').read_text().rsplit(')', 1)[1].split()[19]
            environment = (directory / 'environ').read_bytes().split(b'\0')
            entry['cvd'] = next((part.split(b'=', 1)[1].decode() for part in environment
                                 if part.startswith(b'CUDA_VISIBLE_DEVICES=')), None)
            entry['target_device_open'] = False
            for descriptor in (directory / 'fd').iterdir():
                try:
                    entry['target_device_open'] |= os.readlink(descriptor) == f'/dev/nvidia{index}'
                except FileNotFoundError:
                    pass
            if expected_service and entry['pid'] == expected_service['pid']:
                executable = (directory / 'exe').resolve()
                entry['executable'] = str(executable)
                entry['executable_sha256'] = hashlib.sha256(executable.read_bytes()).hexdigest()
                entry['verified_persistence_service'] = bool(
                    str(executable) == '/usr/bin/nvidia-persistenced'
                    and entry['cvd'] is None
                    and all(entry.get(key) == expected_service.get(key) for key in
                            ('pid', 'uid', 'start_ticks', 'command_sha256', 'executable', 'executable_sha256')))
        except (FileNotFoundError, ProcessLookupError):
            entry['vanished'] = True
        except (PermissionError, OSError) as error:
            entry['unreadable'] = type(error).__name__
        snapshot['processes'].append(entry)
    snapshot['blocking_reasons'] = evaluate_snapshot(snapshot, index, uuid)
    snapshot['clear'] = not snapshot['blocking_reasons']
    snapshot['scanner_euid'] = os.geteuid()
    snapshot['service_identity_sha256'] = hashlib.sha256(service_identity.read_bytes()).hexdigest() if service_identity else None
    return snapshot


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def verify_sources(source, inventory):
    entries = json.loads(inventory.read_text())
    for relative, expected in entries.items():
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('unsafe_source_path')
        actual = source / relative
        if actual.is_symlink() or hashlib.sha256(actual.read_bytes()).hexdigest() != expected:
            raise ValueError('source_changed:' + relative)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', type=int, choices=sorted(ALLOWED), required=True)
    parser.add_argument('--uuid', required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--snapshot-only', action='store_true')
    parser.add_argument('--service-identity', type=Path)
    parser.add_argument('--launch', action='store_true')
    for name in ('source', 'inventory', 'python', 'bundle', 'model-dir', 'tasks', 'prepared', 'publication'):
        parser.add_argument('--' + name, type=Path)
    options = parser.parse_args()
    require_lease(time.time())
    if options.snapshot_only:
        if options.launch or os.geteuid() != 0:
            raise ValueError('privileged_readonly_snapshot_only')
        print(json.dumps(scan(options.index, options.uuid, options.service_identity), sort_keys=True))
        return
    if options.output is None:
        raise ValueError('output_required')
    options.output.mkdir(parents=True, exist_ok=False)
    if not options.launch:
        snapshot = scan(options.index, options.uuid, options.service_identity)
        save(options.output / 'PHYSICAL_SCAN.json', snapshot)
        raise SystemExit(0 if snapshot['clear'] else 3)
    required = (options.source, options.inventory, options.python, options.bundle,
                options.model_dir, options.tasks, options.prepared, options.publication)
    if any(value is None for value in required):
        raise ValueError('complete_launch_provenance_required')
    if os.geteuid() == 0:
        raise ValueError('native_guardian_must_run_unprivileged')
    verify_sources(options.source, options.inventory)
    prepared = json.loads(options.prepared.read_text())
    publication = json.loads(options.publication.read_text())
    if (prepared['status'] != 'PREPARED_CPU_ONLY' or prepared['model_calls'] != 0
            or not prepared['base_verification']['verified']
            or prepared['tasks_sha256'] != hashlib.sha256(options.tasks.read_bytes()).hexdigest()
            or publication.get('remote_verified') is not True
            or publication.get('pre_gpu_evidence_complete') is not True
            or len(publication.get('commit', '')) != 40
            or publication.get('source_inventory_sha256') != hashlib.sha256(options.inventory.read_bytes()).hexdigest()
            or publication.get('service_identity_sha256') != (
                hashlib.sha256(options.service_identity.read_bytes()).hexdigest() if options.service_identity else None)
            or publication.get('prepared_sha256') != hashlib.sha256(options.prepared.read_bytes()).hexdigest()):
        raise ValueError('published_cpu_provenance_required')
    for key, relative in (('driver_sha256', 'gpu/orch_math_replication_native.py'),
                          ('policy_sha256', 'organism_v6/orch_math_replication.py')):
        if prepared[key] != hashlib.sha256((options.source / relative).read_bytes()).hexdigest():
            raise ValueError('prepared_source_mismatch')
    snapshot = scan(options.index, options.uuid, options.service_identity)
    save(options.output / 'PHYSICAL_SCAN.json', snapshot)
    if not snapshot['clear']:
        raise SystemExit(3)
    require_lease(time.time())
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=options.uuid, PYTHONPATH=str(options.source),
                       HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
                       MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1')
    command = [str(options.python), '-B', '-m', 'gpu.orch_math_replication_native',
               '--phase', 'native', '--bundle', str(options.bundle), '--model-dir', str(options.model_dir),
               '--tasks', str(options.tasks), '--output', str(options.output / 'native'),
               '--shard', str(options.index - 2), '--gpu-uuid', options.uuid, '--seconds', '2640']
    started = time.monotonic()
    with (options.output / 'native.log').open('x') as log:
        child = subprocess.Popen(command, env=environment, cwd=options.source, stdout=log,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        save(options.output / 'OWNED_PROCESS.json', dict(pid=child.pid, guardian_pid=os.getpid(),
             gpu_uuid=options.uuid, index=options.index, launch_unix=time.time(),
             lease_end=LEASE_END, hard_limit_seconds=2700))
        try:
            status = child.wait(timeout=2670)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=10)
            status = 124
    save(options.output / 'TERMINAL.json', dict(exit_code=status, elapsed_seconds=time.monotonic() - started,
                                               finished_utc=datetime.now(timezone.utc).isoformat()))
    raise SystemExit(status)


if __name__ == '__main__':
    main()
