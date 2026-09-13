import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


DRIVER = Path('/tmp/astra_level1_skill_run_20260913.py')
DRIVER_PIN = '6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e'
TRANSPORT_SHA = '33000acd013adbf8dbb593c9baf3f7acaa8911db00e85f90a5abc6cd25afcc44'
NODES = ('node1', 'node2', 'a100')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(process):
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=int(process.name), comm=(process / 'comm').read_text().strip(),
                ppid=int(fields[1]), start_ticks=int(fields[19]), uid=process.stat().st_uid,
                cmdline_sha256=digest(process / 'cmdline'))


def selected(value, index, uuid):
    return bool({part.strip() for part in value.split(',')} & {str(index), uuid, 'all'})


def known_exception(record, config, ancestors):
    return (record in config['daemon_identities'] or
            record['pid'] in ancestors and record['comm'] == 'sshd' and
            record['uid'] == config['uid'] and record['cmdline_sha256'] == TRANSPORT_SHA)


def reservations(config, index, uuid):
    if Path('/proc/sys/kernel/random/boot_id').read_text().strip() != config['host_boot_id'] or os.getuid() != config['uid']:
        raise ValueError('node boot/user binding changed')
    if config['gpus'].get(str(index)) != uuid:
        raise ValueError('not a roster allocation')
    ancestors, parent = set(), os.getpid()
    while parent > 1 and parent not in ancestors:
        ancestors.add(parent)
        parent = identity(Path('/proc') / str(parent))['ppid']
    occupied, unresolved = [], []
    for process in Path('/proc').glob('[0-9]*'):
        try:
            if process.stat().st_uid != os.getuid():
                continue
            try:
                fields = (process / 'environ').read_bytes().split(b'\0')
            except PermissionError:
                record = identity(process)
                if not known_exception(record, config, ancestors):
                    unresolved.append(record)
                continue
            visibility = next((field.split(b'=', 1)[1].decode() for field in fields if field.startswith(b'CUDA_VISIBLE_DEVICES=')), '')
            if selected(visibility, index, uuid):
                occupied.append(int(process.name))
        except FileNotFoundError:
            continue
    if occupied or unresolved:
        raise ValueError(json.dumps(dict(reservations=occupied, unresolved=unresolved)))
    queue = Path('/localhome/local-rohing/queue')
    if any(list((queue / name).iterdir()) for name in ('pending', 'running')):
        raise ValueError('shared queue gained pending/running work; reconcile before launch')
    return dict(time=time.time(), gpu_index=index, gpu_uuid=uuid, reservations=[], unresolved=[])


def component(value):
    if type(value) is not str or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', value) is None:
        raise ValueError('batch/cell name must be one safe path component')
    return value


def read_request(roster_path, roster_sha256, node, batch_name):
    component(batch_name)
    if node not in NODES:
        raise ValueError('node must be node1/node2/a100')
    if type(roster_sha256) is not str or re.fullmatch(r'[0-9a-f]{64}', roster_sha256) is None:
        raise ValueError('explicit lowercase full roster SHA256 required')
    roster_path = Path(roster_path).resolve(strict=True)
    if digest(roster_path) != roster_sha256 or digest(DRIVER) != DRIVER_PIN:
        raise ValueError('frozen roster/runtime pin differs')
    roster = json.loads(roster_path.read_text())
    if digest(roster['prechecks']['path']) != roster['prechecks']['sha256']:
        raise ValueError('precheck identity pin differs')
    prechecks = json.loads(Path(roster['prechecks']['path']).read_text())
    if node not in prechecks:
        raise ValueError('Main must supply pinned precheck config for ' + node)
    config = prechecks[node]
    if (type(config) is not dict or set(config) != {'daemon_identities', 'gpus', 'host_boot_id', 'uid'} or
            type(config['daemon_identities']) is not list or type(config['gpus']) is not dict or
            type(config['host_boot_id']) is not str or not config['host_boot_id'] or
            type(config['uid']) is not int or config['uid'] < 0):
        raise ValueError('node precheck schema differs')
    entries = [entry for entry in roster['entries'] if entry['node'] == node]
    if not entries:
        raise ValueError('roster has no cells for selected node')
    names, roots, indices, uuids = set(), set(), set(), set()
    for entry in entries:
        name = component(entry['name'])
        root = Path(entry['root'])
        index, uuid = entry['gpu_index'], entry['gpu_uuid']
        if (not root.is_absolute() or type(index) is not int or index < 0 or
                type(uuid) is not str or not uuid or config['gpus'].get(str(index)) != uuid):
            raise ValueError('entry root/allocation differs from pinned node config')
        resolved_root = str(root.resolve())
        if name in names or resolved_root in roots or index in indices or uuid in uuids:
            raise ValueError('duplicate selected name/root/GPU allocation')
        names.add(name)
        roots.add(resolved_root)
        indices.add(index)
        uuids.add(uuid)
    return roster_path, config, entries


def load_runtime():
    specification = importlib.util.spec_from_file_location('level1_batch_runtime', DRIVER)
    runtime = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(runtime)
    return runtime


def main(roster_path, roster_sha256, node, batch_name):
    roster_path, config, entries = read_request(roster_path, roster_sha256, node, batch_name)
    directory = roster_path.parent / batch_name
    directory.mkdir()
    runtime = load_runtime()
    runtime.offline()
    runtime.write(directory / 'started.json', dict(pid=os.getpid(), time=time.time(), roster_sha256=roster_sha256,
                  roster=str(roster_path), node=node, batch_name=batch_name, runtime=str(DRIVER), runtime_sha256=DRIVER_PIN))
    for entry in entries:
        cell = directory / entry['name']
        cell.mkdir()
        process = None
        try:
            command = [sys.executable, '-B', str(DRIVER), 'prepare', '--root', entry['root'],
                       '--spec-path', entry['spec']['path'], '--spec-sha256', entry['spec']['sha256'], '--allow-native']
            result = subprocess.run(command, capture_output=True, text=True, timeout=180,
                                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
            with (cell / 'prepare.log').open('x') as stream:
                stream.write(result.stdout + result.stderr)
            if result.returncode:
                raise ValueError('native preparation failed; inspect cell prepare.log')
            receipt = json.loads(result.stdout.strip().splitlines()[-1])
            plan, probe = runtime.verify(entry['root'], receipt['plan_sha256'], native=False)
            if plan['gpu_index'] != entry['gpu_index'] or plan['gpu_uuid'] != entry['gpu_uuid']:
                raise ValueError('roster/plan allocation mismatch')
            runtime.write(cell / 'precheck.json', reservations(config, entry['gpu_index'], entry['gpu_uuid']))
            if not probe.gpu_state(plan):
                raise ValueError('all-process XML vacancy failed')
            if plan['lease_end'] <= time.time() + 5400 + 180 + 21600:
                raise ValueError('lease finish margin unavailable')
            command = [sys.executable, '-B', str(DRIVER), 'controller', '--root', entry['root'],
                       '--plan-sha256', receipt['plan_sha256'], '--allow-gpu']
            with (cell / 'controller.log').open('xb') as output:
                process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                    start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=entry['gpu_uuid']))
            record = dict(status='LAUNCHED_NOT_RESULT', node=node, name=entry['name'], root=entry['root'],
                          pid=process.pid, pgid=process.pid, identity=identity(Path('/proc') / str(process.pid)),
                          time=time.time(), plan_sha256=receipt['plan_sha256'], gpu_index=entry['gpu_index'],
                          gpu_uuid=entry['gpu_uuid'], cap_seconds=5400, command=command)
            runtime.write(cell / 'launched.json', record)
            print(json.dumps(record, sort_keys=True), flush=True)
        except BaseException as error:
            runtime.write(cell / 'failure.json', dict(error=repr(error), pid=None if process is None else process.pid,
                          controller_may_be_running=process is not None, retry=False))
            raise
    runtime.write(directory / 'finished.json', dict(time=time.time(), status='ALL_CONTROLLERS_SUBMITTED_NOT_RESULTS'))


def cli(argv=None):
    parser = argparse.ArgumentParser(description='Fresh explicit-roster batch; no resume or retry.')
    parser.add_argument('--roster', type=Path, required=True)
    parser.add_argument('--roster-sha256', required=True)
    parser.add_argument('--node', choices=NODES, required=True)
    parser.add_argument('--batch-name', required=True)
    args = parser.parse_args(argv)
    main(args.roster, args.roster_sha256, args.node, args.batch_name)


if __name__ == '__main__':
    cli()
