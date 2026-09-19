"""Lease-bound custody of the unchanged VM-only Astra HTTP provider and ledger."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import tempfile
import threading
import time
from types import FunctionType


ROOT = '/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_4_attempt1'
TERMINAL = 'R118_PARALLEL_TERMINAL.json'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.partial.' + str(os.getpid()))
    with temporary.open('x') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def reference(path):
    return dict(path=str(path), sha256=sha(path))


def process_identity():
    directory = Path('/proc') / str(os.getpid())
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=os.getpid(), uid=directory.stat().st_uid, start_ticks=fields[19],
        ppid=int(fields[1]), command_sha256=sha(directory/'cmdline'),
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        cwd=os.readlink(directory/'cwd'))


def verify_control(control):
    require(control['root'] == ROOT and control['terminal'] == TERMINAL,
            'only_actual_A1_parallel_root')
    require(control['plan']['path'] == ROOT + '/R118_PARALLEL_PLAN.json'
            and control['parent_wait_seconds'] == 120
            and control['deadline_unix'] == 1789596240
            and control['lease_policy']['sha256'] == 'a1aa51349c1784ec9f78e6411912576be43b55942c5fcdf1858ca391fd81c510',
            'fixed_PLAN_wait_and_actual_common_lease_bound')
    require(control['native_source']['sha256'] == sha(__file__), 'exact_custody_source')


def validate_heartbeat(document, control, now):
    require(document['control_sha256'] == control['control_sha256']
            and document['config_sha256'] == control['config_sha256']
            and document['plan'] == control['plan'], 'actual_VM_worker_bindings')
    require(document['exclusive_queue_lock_acquired'] is True
            and 0 <= now - document['time_unix'] <= 30, 'fresh_actual_VM_worker_heartbeat')
    require(document['identity_role'] == 'VM_HTTP_PROVIDER_WORKER'
            and document['identity']['pid'] > 0 and len(document['host_binding_sha256']) == 64,
            'truthful_remote_provider_identity')


def serve(args):
    from gpu import orch_r111_route_astra_broker as astra
    transport = astra.transport
    control = read(args.control)
    verify_control(control)
    control['control_sha256'] = sha(args.control)
    require(sha(args.config) == control['config_sha256'], 'same_original_broker_config')
    config = read(args.config)
    require(config['remote_root'] == ROOT, 'same_original_queue')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_provider_worker')
    for relative in ('gpu/ovx3_ssh.sh', 'gpu/ovx3_scp.sh'):
        require(transport.sha(args.repository / relative) == transport.sha(transport.ROOT / relative),
                'existing_authorized_wrapper_bytes')
    identity = process_identity()
    host_binding = hashlib.sha256(Path('/etc/machine-id').read_bytes()).hexdigest()
    original = transport.Store
    lock_path = Path(ROOT) / 'parent_claude/RUNNER.lock'
    heartbeat_path = Path(control['directory']) / 'VM_WORKER_HEARTBEAT.json'

    class Store(original):
        def __init__(self, unused):
            super().__init__(args.repository)
            self.owned_lock = False
            self.last_heartbeat = 0
            self.heartbeat_lock = threading.Lock()
            self.heartbeat_error = None

        def shell(self, script, check=True):
            result = super().shell(script, check=check)
            if script == 'mkdir ' + shlex.quote(str(lock_path)) and result.returncode == 0:
                self.owned_lock = True
                threading.Thread(target=self.heartbeat_loop, daemon=True).start()
            if script == 'rmdir ' + shlex.quote(str(lock_path)):
                self.owned_lock = False
            return result

        def heartbeat(self):
            with self.heartbeat_lock:
                self.publish_heartbeat()

        def heartbeat_loop(self):
            while self.owned_lock and time.time() < control['deadline_unix']:
                try:
                    self.heartbeat()
                except Exception as error:
                    self.heartbeat_error = type(error).__name__
                    return
                time.sleep(5)

        def publish_heartbeat(self):
            if not self.owned_lock or time.monotonic() - self.last_heartbeat < 5:
                return
            require(self.hash(control['plan']['path']) == control['plan']['sha256'], 'actual_staged_PLAN')
            require(self.hash(Path(ROOT) / 'parent_claude/CONFIG.json') == control['config_sha256'],
                    'unchanged_original_ledger_config')
            document = dict(identity_role='VM_HTTP_PROVIDER_WORKER', identity=identity,
                host_binding_sha256=host_binding, plan=control['plan'],
                config_sha256=control['config_sha256'], control_sha256=control['control_sha256'],
                exclusive_queue_lock_acquired=True, time_unix=time.time())
            with tempfile.TemporaryDirectory(prefix='orch_r118_route_heartbeat_') as temporary:
                local = Path(temporary) / 'HEARTBEAT.json'
                write(local, document)
                partial = str(heartbeat_path) + '.partial'
                self.copy(local, 'NODE:' + partial)
                self.shell('mv ' + shlex.quote(partial) + ' ' + shlex.quote(str(heartbeat_path)))
            self.last_heartbeat = time.monotonic()

        def exists(self, path):
            if Path(path) == Path(ROOT) / 'TERMINAL.json':
                require(self.heartbeat_error is None, 'custody_heartbeat_failed_no_new_dispatch')
                self.heartbeat()
                return time.time() >= control['deadline_unix'] or super().exists(Path(ROOT) / TERMINAL)
            return super().exists(path)

    namespace = dict(transport.serve.__globals__, Store=Store, evaluate=astra.evaluate,
                     validate_launch=astra.authorize)
    namespace['process_request'] = FunctionType(transport.process_request.__code__, namespace,
        'process_request', transport.process_request.__defaults__)
    FunctionType(transport.serve.__code__, namespace, 'serve', transport.serve.__defaults__)(
        args.config, args.launch_receipt, args.prompt_root, args.principles)


def custodian(args):
    control = read(args.control)
    verify_control(control)
    control['control_sha256'] = sha(args.control)
    root, directory = Path(ROOT), Path(control['directory'])
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_node_custodian')
    require(sha(control['plan']['path']) == control['plan']['sha256'], 'actual_staged_PLAN')
    heartbeat = directory / 'VM_WORKER_HEARTBEAT.json'
    deadline = min(time.time() + 90, control['deadline_unix'])
    while not heartbeat.exists() and time.time() < deadline:
        time.sleep(1)
    document = read(heartbeat)
    validate_heartbeat(document, control, time.time())
    binding = dict(root=ROOT, plan=control['plan'], terminal=TERMINAL, parent_wait_seconds=120,
        identity=process_identity(), identity_role='NODE_BROKER_CUSTODIAN',
        provider_worker_identity=document['identity'], provider_worker_location='VM_NOT_NODE',
        provider_worker_host_binding_sha256=document['host_binding_sha256'],
        exclusive_queue_lock_verified_by=reference(heartbeat), source=control['native_source'],
        provider=control['provider'], control=reference(args.control), created_unix=time.time())
    target = root / 'R118_PARALLEL_BROKER_BINDING.json'
    require(not target.exists(), 'no_binding_overwrite')
    write(target, binding)
    try:
        while time.time() < control['deadline_unix'] and not (root / TERMINAL).exists():
            require(sha(control['plan']['path']) == control['plan']['sha256'], 'PLAN_unchanged')
            validate_heartbeat(read(heartbeat), control, time.time())
            time.sleep(3)
        write(directory / 'CUSTODIAN_COMPLETE.json', dict(finished_unix=time.time(), GPU_signals=0))
    except BaseException as error:
        write(directory / 'CUSTODIAN_FAILED.json', dict(type=type(error).__name__, error=str(error),
            finished_unix=time.time(), GPU_signals=0, no_provider_retry=True))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('serve', 'custodian'))
    parser.add_argument('--control', type=Path, required=True)
    for name in ('config', 'launch-receipt', 'prompt-root', 'principles', 'repository'):
        parser.add_argument('--' + name, type=Path)
    args = parser.parse_args()
    (serve if args.phase == 'serve' else custodian)(args)


if __name__ == '__main__':
    main()
