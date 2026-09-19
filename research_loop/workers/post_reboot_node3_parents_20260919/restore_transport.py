"""Non-material repair of existing node3 CPU Unix/SSH caption transport only."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from transport_preflight import HERE, REPO, PRIOR, SHARED, SOURCE, inspect, remote

DEADLINE = 1790272760
REGISTRY_SHA = 'a14411eb727c5b9b2bdc10e259f65d2b91f4396bd57c273f69d423a84bc8005f'


def put(path, value):
    temporary = path.with_suffix('.pending')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    temporary.replace(path)


def identity(pid):
    root = Path('/proc', str(pid))
    fields = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    if fields[0] in ('Z', 'X'):
        raise ValueError('live_cpu_process_required')
    return dict(pid=pid, start_ticks=fields[19],
        command_sha256=hashlib.sha256((root / 'cmdline').read_bytes()).hexdigest())


def registry_bytes():
    registry = json.loads((REPO / 'research_loop/workers/rohin205_node3_20260918/R226_CAPTION_BINDINGS.json').read_bytes())
    receipt = next(row for row in json.loads((PRIOR / 'LEASE_TRANSPORTS_RENEWED.json').read_bytes()) if row['group'] == 'node3')
    for row in registry['rows']:
        row['minimum_origin_record_index'] = receipt['proxy']['future_frontiers'][row['session_id']]
    raw = json.dumps(registry).encode()
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA:
        raise ValueError('exact_previous_authenticated_registry_required')
    return raw


def forwarding_commands(runtime, rows, suffix):
    options = ['-N', '-o', 'ExitOnForwardFailure=yes', '-o', 'StreamLocalBindMask=0177',
        '-o', 'ServerAliveCountMax=3']
    upstream = ['bash', 'gpu/ovx4_ssh.sh', *options, '-L', str(runtime / 'shared.sock') + ':' + SHARED + '/native.sock']
    downstream = ['bash', 'gpu/ovx2_ssh.sh', *options]
    routes = []
    for row in rows:
        slot = str(row['physical'])
        target = '/tmp/n3cap-' + suffix + '-' + slot + '.sock'
        downstream += ['-R', target + ':' + str(runtime / 'proxy' / (slot + '.sock'))]
        routes.append(dict(slot=slot, alias='/tmp/r226-caption-' + slot + '.sock', target=target))
    return upstream, downstream, routes


def check_deadline(now):
    if not now < DEADLINE:
        raise ValueError('original_node3_transport_deadline_elapsed')


def snapshot_source(source):
    sources = {}
    for relative in ('gpu', 'organism_v6', 'research_loop', 'research_loop/workers',
            'research_loop/workers/rohin221_continuous_caption_20260918',
            'research_loop/workers/rohin233_ovx4_recovery_20260918'):
        destination = source / relative
        destination.mkdir(parents=True, exist_ok=True)
        for path in (REPO / relative).glob('*.py'):
            shutil.copy2(path, destination / path.name)
            sources[str(path.relative_to(REPO))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return sources


def main():
    if os.uname().nodename != 'nvl-ai' or Path('/proc/1/comm').read_text().strip() != 'systemd':
        raise ValueError('real_operator_host_namespace_required')
    check_deadline(time.time())
    lock = (HERE / 'locks/TRANSPORT.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    baseline = inspect()
    suffix = str(time.time_ns()) + uuid.uuid4().hex[:6]
    output = HERE / 'private/transport_runs' / suffix
    output.mkdir(mode=0o700, parents=True)
    runtime = Path('/tmp/n3cap-' + suffix)
    runtime.mkdir(mode=0o700)
    put(output / 'PREFLIGHT.json', baseline)
    raw = registry_bytes()
    (output / 'REGISTRY.json').write_bytes(raw)
    rows = json.loads(raw)['rows']
    source = output / 'source'
    sources = snapshot_source(source)
    config = dict(root=str(runtime / 'proxy'), registry=dict(path=str(output / 'REGISTRY.json'), sha256=REGISTRY_SHA),
        shared_forward=str(runtime / 'shared.sock'), shared_root=SHARED, native_source=SOURCE,
        scorer_source=SOURCE, deadline_unix=DEADLINE, lease_boundary_unix=1790812800)
    put(output / 'CONFIG.json', config)
    upstream, downstream, routes = forwarding_commands(runtime, rows, suffix)
    environment = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1')
    proxy_command = ['/usr/bin/python3', '-B', str(source /
        'research_loop/workers/rohin233_ovx4_recovery_20260918/transport_large_proxy.py')]
    subprocess.run([*proxy_command, '--help'], cwd=source, env=environment,
        capture_output=True, check=True, timeout=20)
    children = []
    log = (output / 'transport.log').open('ab', buffering=0)

    def start(command):
        check_deadline(time.time())
        bounded = ['timeout', '--signal=TERM', '--kill-after=5', str(int(DEADLINE-time.time())), *command]
        child = subprocess.Popen(bounded, cwd=REPO, env=environment, stdin=subprocess.DEVNULL,
            stdout=log, stderr=log, start_new_session=True, close_fds=True, pass_fds=(lock.fileno(),))
        children.append(child)
        return child

    start(upstream)
    start([*proxy_command, '--config', str(output / 'CONFIG.json')])
    stop = time.time() + 30
    while not (runtime / 'proxy/READY.json').exists() or not (runtime / 'shared.sock').exists():
        if any(child.poll() is not None for child in children) or time.time() > stop:
            for child in children:
                if child.poll() is None:
                    child.terminate()
            put(output / 'FAILED_BEFORE_ACTIVATION.json', dict(unix=time.time(),
                no_alias_changes=True, no_requests_dispatched=True))
            raise RuntimeError('cpu_transport_start_failed_see_preserved_log')
        time.sleep(.2)
    start(downstream)
    time.sleep(2)
    if any(child.poll() is not None for child in children):
        raise RuntimeError('ssh_forward_failed_no_alias_mutation')
    switched = remote('ovx2_ssh.sh', '''
from pathlib import Path
import fcntl,json,os,stat,sys,time
value=json.load(sys.stdin)
lock=Path('/localhome/local-rohing/orch_r205_node3_20260918/R233_NODE3_TRANSPORT_RECOVERY.lock').open('a')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
for row in value['routes']:
 alias=Path(row['alias']);target=Path(row['target'])
 assert alias.is_symlink() and str(alias.readlink())==value['previous'][row['slot']],'route_changed_do_not_overwrite'
 assert stat.S_ISSOCK(target.stat().st_mode) and stat.S_IMODE(target.stat().st_mode)==0o600,'new_private_forward_not_ready'
for row in value['routes']:
 alias=Path(row['alias']);pending=Path(row['target']+'.aliaspending')
 pending.symlink_to(row['target']);os.replace(pending,alias)
print(json.dumps(dict(unix=time.time(),routes=value['routes'],previous=value['previous'],native_signals=[],scorer_signals=[])))
''', dict(routes=routes, previous=baseline['native']['aliases']))
    started = dict(unix=time.time(), controller=identity(os.getpid()),
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        children=[identity(child.pid) for child in children], runtime=str(runtime), output=str(output),
        deadline_unix=DEADLINE, source_hashes=sources, switched=switched,
        registry_sha256=REGISTRY_SHA, existing_scorer=baseline['scorer'],
        status='CPU_TRANSPORT_RESTORED_FUTURE_NATURAL_ACT_RECEIPTS_PENDING',
        history_replays=0, native_signals=[], scorer_signals=[], parent_changes=0)
    put(output / 'STARTED.json', started)
    put(HERE / 'TRANSPORT_STARTED.json', started)
    print(json.dumps({key:started[key] for key in ('unix','controller','runtime','status')}), flush=True)
    while time.time() < DEADLINE and all(child.poll() is None for child in children):
        for path in (runtime / 'proxy').glob('*.json'):
            if not (output / path.name).exists():
                shutil.copy2(path, output / path.name)
        put(HERE / 'TRANSPORT_HEARTBEAT.json', dict(unix=time.time(), controller=identity(os.getpid()),
            children=[identity(child.pid) for child in children], state='RUNNING_NOT_A_SCORING_RECEIPT'))
        time.sleep(3)
    put(output / 'STOPPED.json', dict(unix=time.time(),returncodes=[child.poll() for child in children],
        status='CPU_CHILD_EXITED_NO_REPLAY_REVIEW_REQUIRED'))
    for child in children:
        child.wait()


if __name__ == '__main__':
    main()
