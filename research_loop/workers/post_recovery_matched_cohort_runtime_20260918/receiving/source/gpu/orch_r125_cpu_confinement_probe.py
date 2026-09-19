"""Disposable, trusted CPU-only confinement tests; never runs child-supplied code.

Run on a leased node with --root NEW_ABSOLUTE_DIRECTORY. Uses sudo only for a
transient systemd unit and read-only cgroup inspection. No GPU devices opened,
host security settings changed, live lanes touched or automatic tool grant.
"""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from gpu.orch_r125_bounded_capture import capture


SCHEMA = 'R125_CPU_CONFINEMENT_PROBE_V1'


def boot_identity():
    return hashlib.sha256(Path('/proc/sys/kernel/random/boot_id').read_bytes()).hexdigest()


RESOURCE_PAYLOADS = {
    'output': 'import os\nwhile True: os.write(1, b"x" * 8192)\n',
    'timeout': 'import os,time\nos.fork()\ntime.sleep(30)\n',
    'memory': 'import time\ntime.sleep(2)\nallocation = bytearray(256 * 1024 * 1024)\n',
    'files': '''import errno,json,pathlib,time
time.sleep(2)
checks = {}
try:
    pathlib.Path('/work/too-large').write_bytes(b'x' * (1048576 + 1))
except OSError as error:
    checks['file_size_limit'] = error.errno == errno.EFBIG
else:
    checks['file_size_limit'] = False
try:
    for index in range(20):
        pathlib.Path('/work/file-%s' % index).write_bytes(b'x' * 524288)
except OSError as error:
    checks['scratch_limit'] = error.errno == errno.ENOSPC
else:
    checks['scratch_limit'] = False
print(json.dumps({'checks': checks, 'passed': all(checks.values())}))
''',
}
PAYLOAD = r'''
import errno, json, os, pathlib, socket, time

outside = pathlib.Path(__OUTSIDE__)
peer = __PEER__
checks = {}
status = pathlib.Path('/proc/self/status').read_text()
fields = dict(line.split(':', 1) for line in status.splitlines() if ':' in line)
checks['nonroot_identity'] = os.getuid() > 0 and os.getgid() > 0
checks['zero_effective_caps'] = int(fields['CapEff'].strip(), 16) == 0
checks['no_new_privileges'] = fields['NoNewPrivs'].strip() == '1'
checks['seccomp_active'] = fields['Seccomp'].strip() == '2'
checks['clean_environment'] = set(os.environ) <= {'PATH', 'LANG', 'PYTHONHASHSEED', 'LC_CTYPE'}

def denied(name, operation):
    try:
        result = operation()
        if hasattr(result, 'close'):
            result.close()
    except OSError as error:
        checks[name] = error.errno in (errno.EPERM, errno.EACCES, errno.ENOENT, errno.ESRCH, errno.EROFS, errno.EAFNOSUPPORT)
    else:
        checks[name] = False

work = pathlib.Path('/work')
(work / 'allowed.txt').write_text('synthetic allowed output')
checks['private_work_write'] = (work / 'allowed.txt').read_text() == 'synthetic allowed output'
checks['readonly_input_read'] = pathlib.Path('/readonly.txt').read_text() == 'synthetic readonly input'
denied('readonly_input_write', lambda: open('/readonly.txt', 'a'))
denied('outside_canary_read', lambda: open(outside, 'rb'))
denied('outside_canary_write', lambda: open(outside, 'ab'))
(work / 'escape').symlink_to(outside)
denied('symlink_escape', lambda: open(work / 'escape', 'rb'))
denied('peer_environ', lambda: open('/proc/%s/environ' % peer, 'rb'))
denied('peer_root_escape', lambda: open('/proc/%s/root%s' % (peer, outside), 'rb'))
denied('peer_signal_permission', lambda: os.kill(peer, 0))
denied('privilege_escalation', lambda: os.setuid(0))
denied('device_zero_denied', lambda: open('/dev/zero', 'rb'))
checks['device_null_allowed'] = os.open('/dev/null', os.O_WRONLY) >= 0
for name, family in [('inet', socket.AF_INET), ('inet6', socket.AF_INET6), ('unix', socket.AF_UNIX)]:
    denied('socket_' + name, lambda family=family: socket.socket(family, socket.SOCK_STREAM))
denied('host_cgroup_hidden', lambda: open('/sys/fs/cgroup/cgroup.procs', 'rb'))
cgroup_diagnostic = {}
try:
    cgroup_processes = pathlib.Path('/sys/fs/cgroup/cgroup.procs').read_text().splitlines()
    cgroup_diagnostic = {'count': len(cgroup_processes), 'contains_peer': str(peer) in cgroup_processes,
        'contains_self': str(os.getpid()) in cgroup_processes,
        'mountinfo': [line for line in pathlib.Path('/proc/self/mountinfo').read_text().splitlines()
            if ' - cgroup2 ' in line]}
except OSError as error:
    cgroup_diagnostic = {'errno': error.errno}
descriptors = []
for path in pathlib.Path('/proc/self/fd').iterdir():
    try:
        target = os.readlink(path)
    except FileNotFoundError:
        continue
    descriptors.append((int(path.name), target))
checks['no_unexpected_inherited_fd'] = all(number <= 2 or target in ('/dev/null', '/job.py') for number, target in descriptors)
children = []
limited = False
try:
    for index in range(12):
        try:
            child = os.fork()
        except OSError as error:
            limited = error.errno == errno.EAGAIN
            break
        if child == 0:
            time.sleep(1)
            os._exit(0)
        children.append(child)
finally:
    for child in children:
        os.waitpid(child, 0)
checks['process_limit_enforced'] = limited and len(children) < 12
print(json.dumps({'checks': checks, 'uid': os.getuid(), 'gid': os.getgid(),
    'forked_children': len(children), 'cgroup_diagnostic': cgroup_diagnostic,
    'passed': all(checks.values())}), flush=True)
time.sleep(5)
'''


def command(root, unit):
    root = Path(root)
    if not root.is_absolute() or not re.fullmatch(r'/[A-Za-z0-9_./-]+', str(root)) or '..' in root.parts:
        raise ValueError('trusted_absolute_root_required')
    if not re.fullmatch(r'orch-r125-cpu-[a-z0-9-]{1,40}', unit):
        raise ValueError('owned_unit_name_required')
    properties = {
        'DynamicUser': 'yes', 'RootDirectory': str(root / 'rootfs'),
        'BindReadOnlyPaths': f'/usr {root / "payload.py"}:/job.py {root / "readonly.txt"}:/readonly.txt {root / "empty"}:/sys/fs/cgroup',
        'MountAPIVFS': 'no', 'PrivateNetwork': 'yes', 'PrivateDevices': 'yes',
        'ProtectSystem': 'strict', 'ProtectHome': 'yes', 'ProtectProc': 'invisible',
        'ProcSubset': 'pid', 'NoNewPrivileges': 'yes', 'CapabilityBoundingSet': '',
        'AmbientCapabilities': '', 'ProtectKernelTunables': 'yes',
        'ProtectKernelModules': 'yes', 'ProtectKernelLogs': 'yes',
        'ProtectControlGroups': 'yes', 'RestrictNamespaces': 'yes',
        'RestrictSUIDSGID': 'yes', 'LockPersonality': 'yes',
        'MemoryDenyWriteExecute': 'yes', 'RestrictRealtime': 'yes',
        'TemporaryFileSystem': '/tmp:rw,size=8M,mode=1777 /work:rw,size=8M,mode=1777',
        'ReadWritePaths': '/tmp /work', 'WorkingDirectory': '/work',
        'InaccessiblePaths': '/sys /sys/fs/cgroup', 'MemoryMax': '128M', 'MemorySwapMax': '0',
        'TasksMax': '8', 'CPUQuota': '25%', 'RuntimeMaxSec': '15',
        'TimeoutStopSec': '2', 'KillMode': 'control-group',
        'OOMPolicy': 'kill',
        'DevicePolicy': 'strict', 'DeviceAllow': '/dev/null rw',
        'SystemCallFilter': '~@mount @network-io @privileged @reboot @swap @module @debug',
        'SystemCallErrorNumber': 'EPERM',
        'UMask': '0077', 'LimitCORE': '0', 'LimitFSIZE': '1048576',
    }
    return ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe',
        '--unit=' + unit, *['--property=' + key + '=' + value for key, value in properties.items()],
        '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'LANG=C.UTF-8', 'PYTHONHASHSEED=0',
        '/usr/bin/python3', '-I', '/job.py']


def observe(unit):
    result = subprocess.run(['sudo', '-n', 'systemctl', 'show', unit + '.service',
        '--property=ControlGroup,MainPID,MemoryMax,MemorySwapMax,TasksMax,CPUQuotaPerSecUSec,DevicePolicy'],
        capture_output=True, text=True, timeout=5, check=True)
    fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    group = fields.get('ControlGroup', '')
    if not group or fields.get('MainPID') in ('', '0', None):
        return None
    path = Path('/sys/fs/cgroup') / group.lstrip('/')
    result = dict(properties=fields, cgroup_files={})
    for name in ('memory.max', 'memory.swap.max', 'pids.max', 'cpu.max'):
        result['cgroup_files'][name] = (path / name).read_text().strip()
    bpf = subprocess.run(['sudo', '-n', '/usr/sbin/bpftool', '-j', 'cgroup', 'show',
        str(path), 'effective'], capture_output=True, text=True, timeout=5)
    result['bpf_returncode'] = bpf.returncode
    result['bpf'] = json.loads(bpf.stdout) if bpf.returncode == 0 else None
    return result


def run(root, mode='basic'):
    if mode not in ('basic', *RESOURCE_PAYLOADS):
        raise ValueError('trusted_probe_mode_only')
    root = Path(root).absolute()
    unit = 'orch-r125-cpu-' + hashlib.sha256(str(root).encode()).hexdigest()[:16]
    invocation = command(root, unit)
    root.mkdir(mode=0o755, parents=False, exist_ok=False)
    root.chmod(0o755)
    filesystem = root / 'rootfs'
    filesystem.mkdir(mode=0o755)
    (root / 'empty').mkdir(mode=0o755)
    for name in ('usr', 'etc', 'proc', 'dev', 'sys', 'run', 'tmp', 'work'):
        (filesystem / name).mkdir(mode=0o755)
    for name in ('bin', 'lib', 'lib64'):
        (filesystem / name).symlink_to('usr/' + name)
    canary = root / 'outside-canary.txt'
    canary.write_text('synthetic secret; never a real credential')
    (root / 'readonly.txt').write_text('synthetic readonly input')
    peer = subprocess.Popen(['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', '/usr/bin/sleep', '30'],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
    payload = PAYLOAD if mode == 'basic' else RESOURCE_PAYLOADS[mode]
    payload = payload.replace('__OUTSIDE__', repr(str(canary))).replace('__PEER__', str(peer.pid))
    (root / 'payload.py').write_text(payload)
    receipts = dict(schema=SCHEMA, observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        command=invocation, source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        boot_id_sha256=boot_identity(),
        capture_source_sha256=hashlib.sha256(Path(sys.modules[capture.__module__].__file__).read_bytes()).hexdigest(),
        payload_sha256=hashlib.sha256(payload.encode()).hexdigest(), mode=mode, child_code_executed=False,
        GPU_devices_opened=False, tool_access_enabled=False)
    process = None
    try:
        process = subprocess.Popen(invocation, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, close_fds=True)
        for attempt in range(20):
            if process.poll() is not None:
                break
            observation = observe(unit)
            if observation is not None:
                receipts['host_observation'] = observation
                break
            time.sleep(0.1)
        def stop_job():
            subprocess.run(['sudo', '-n', 'systemctl', 'stop', unit + '.service'],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=True)

        captured = capture(process, stop_job, timeout=2 if mode == 'timeout' else 25)
        stdout = captured.pop('stdout').decode('utf-8', errors='replace')
        stderr = captured.pop('stderr').decode('utf-8', errors='replace')
        receipts.update(returncode=process.returncode, stdout=stdout, stderr=stderr, capture=captured)
        outcome = subprocess.run(['sudo', '-n', 'systemctl', 'show', unit + '.service',
            '--property=Result,ExecMainCode,ExecMainStatus,ActiveState,SubState'],
            capture_output=True, text=True, timeout=5)
        receipts['unit_outcome'] = dict(line.split('=', 1) for line in outcome.stdout.splitlines() if '=' in line)
        if process.returncode == 0 and mode in ('basic', 'files'):
            receipts['payload_result'] = json.loads(stdout)
        observation = receipts.get('host_observation', {})
        limits = observation.get('cgroup_files', {})
        receipts['verified_limits'] = limits.get('memory.max') == '134217728' and limits.get('memory.swap.max') == '0' \
            and limits.get('pids.max') == '8' and limits.get('cpu.max') == '25000 100000'
        behavior_passed = receipts.get('payload_result', {}).get('passed', False)
        if mode in ('output', 'timeout'):
            behavior_passed = captured['limit_reason'] == {'output': 'OUTPUT_LIMIT', 'timeout': 'TIMEOUT'}[mode] \
                and captured['teardown_called'] and captured['teardown_error'] is None and process.returncode is not None
        elif mode == 'memory':
            behavior_passed = receipts['unit_outcome'].get('Result') == 'oom-kill' and process.returncode != 0
        receipts['passed'] = behavior_passed and receipts['verified_limits'] \
            and any(entry.get('attach_type') == 'cgroup_device' for entry in (observation.get('bpf') or []))
    except Exception as error:
        receipts.update(error_type=type(error).__name__, error=str(error), passed=False)
    finally:
        subprocess.run(['sudo', '-n', 'systemctl', 'stop', unit + '.service'],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        if process is not None and process.poll() is None:
            process.communicate(timeout=5)
        group = receipts.get('host_observation', {}).get('properties', {}).get('ControlGroup')
        receipts['cgroup_removed_after_stop'] = bool(group) and not (Path('/sys/fs/cgroup') / group.lstrip('/')).exists()
        receipts['passed'] = receipts.get('passed', False) and receipts['cgroup_removed_after_stop']
        subprocess.run(['sudo', '-n', 'systemctl', 'reset-failed', unit + '.service'],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        peer.terminate()
        peer.wait(timeout=5)
        (root / 'RECEIPT.json').write_text(json.dumps(receipts, indent=2, sort_keys=True))
    return receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--mode', choices=('basic', *RESOURCE_PAYLOADS), default='basic')
    arguments = parser.parse_args()
    result = run(arguments.root, arguments.mode)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
