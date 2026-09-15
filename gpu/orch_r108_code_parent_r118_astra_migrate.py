"""Exact-identity A3 broker migration after all claimed responses are published."""

import argparse
import json
import os
from pathlib import Path
import select
import shlex
import signal
import subprocess
import time

from gpu import orch_r108_code_parent_r115_astra as astra
from gpu.orch_rich_hot_a100_scan import identity


REMOTE_ROOT = '/localhome/local-rohing/orch_r108_code_parent_r115_node5_6_20260915_attempt1'


def owned_command(command, old_root):
    return ('gpu.orch_r108_code_parent_r115_astra' in command
        or str(old_root/'source/gpu/orch_r108_code_parent_r115_astra.py') in command) \
        and str(old_root/'CONFIG.json') in command


def settled(snapshot, config_sha256):
    return snapshot.get('config_sha256') == config_sha256 \
        and snapshot.get('lock_present') is True \
        and snapshot.get('unpublished') == [] and snapshot.get('partial') == [] \
        and type(snapshot.get('claims')) is int and snapshot['claims'] >= 0


def boundary(store):
    source = '''import hashlib,json,pathlib,time
root=pathlib.Path(ROOT)
sha=lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
ledger=root/'parent_claude'
claims=sorted(ledger.glob('*.claim'))
unpublished=[]
files={}
for claim in claims:
    publication=claim/'PUBLISHED.json'
    response=root/'parent_queue'/(claim.name.removesuffix('.claim')+'.response.json')
    if not publication.is_file() or not response.is_file():
        unpublished.append(claim.name)
        continue
    record=json.loads(publication.read_text())
    if record.get('response_sha256')!=sha(response):
        unpublished.append(claim.name)
    files[claim.name]={'publication_sha256':sha(publication),'response_sha256':sha(response)}
config_sha256=hashlib.sha256(json.dumps(json.loads((ledger/'CONFIG.json').read_text()),
    sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
print(json.dumps(dict(config_sha256=config_sha256,claims=len(claims),
    unpublished=unpublished,partial=[path.name for path in (root/'parent_queue').glob('*.partial')],
    lock_present=(ledger/'RUNNER.lock').is_dir(),files=files,observed_unix=time.time())))
'''.replace('ROOT', repr(REMOTE_ROOT))
    return json.loads(store.shell('python3 -c ' + shlex.quote(source)).stdout)


def migrate(old_root, new_root, expected_path, *, wait_seconds=180):
    old_root, new_root = Path(old_root).resolve(), Path(new_root).resolve()
    require = astra.transport.require
    require(old_root.is_relative_to('/tmp') and new_root.is_relative_to('/tmp')
        and old_root != new_root, 'separate_immutable_tmp_sources')
    expected = json.loads(Path(expected_path).read_text())
    process = Path('/proc') / str(expected['pid'])
    require(expected['uid'] == os.getuid() and identity(process) == expected, 'exact_owned_broker')
    command = (process/'cmdline').read_bytes().decode().strip('\0').split('\0')
    require(owned_command(command, old_root), 'only_owned_A3_broker')
    config = json.loads((new_root/'CONFIG.json').read_text())
    require(config['remote_root'] == REMOTE_ROOT and config['family'] == 'code', 'exact_A3_only')
    require((old_root/'CONFIG.json').read_bytes() == (new_root/'CONFIG.json').read_bytes(),
        'same_ledger_caps_cutoffs_memory_floor')
    astra.authorize(config, json.loads((new_root/'LAUNCH.json').read_text()), time.time())
    manifest = json.loads((new_root/'SOURCE_SHA256.json').read_text())
    require(all(astra.transport.sha(new_root/'source'/path) == value for path, value in manifest.items()),
        'frozen_successor_source')
    environment = dict(item.split('=', 1) for item in (process/'environ').read_bytes().decode().split('\0') if item)
    environment.update(PYTHONPATH=str(new_root/'source'), CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
    store = astra.transport.Store(new_root/'source')
    descriptor = os.pidfd_open(expected['pid'])
    stopped = False
    try:
        deadline = min(time.time()+wait_seconds, config['deadline_unix']-30)
        while time.time() < deadline:
            require(identity(process) == expected, 'broker_identity_drift')
            if (process/'task'/str(expected['pid'])/'children').read_text().strip():
                time.sleep(3)
                continue
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            stopped = True
            try:
                for attempt in range(100):
                    if (process/'stat').read_text().rsplit(')', 1)[1].split()[0] in ('T', 't'):
                        break
                    time.sleep(.01)
                else:
                    raise RuntimeError('broker_stop_not_observed')
                require(identity(process) == expected, 'stopped_identity_drift')
                if (process/'task'/str(expected['pid'])/'children').read_text().strip():
                    continue
                snapshot = boundary(store)
                if not settled(snapshot, astra.transport.digest(config)):
                    continue
                preserved = dict(identity=expected, snapshot=snapshot, raw_stays_node=True,
                    old_stdout_sha256=astra.transport.sha(old_root/'BROKER.log'),
                    old_config_sha256=astra.transport.sha(old_root/'CONFIG.json'),
                    new_source_manifest_sha256=astra.transport.sha(new_root/'SOURCE_SHA256.json'),
                    native_child_untouched=True, provider_retry=False, observed_unix=time.time())
                astra.transport.write(new_root/'MIGRATION_BEFORE.json', preserved)
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                stopped = False
                require(bool(select.select([descriptor], [], [], 10)[0]), 'old_broker_exit_not_verified')
                after = boundary(store)
                require(settled(after, astra.transport.digest(config)) and after['files'] == snapshot['files'],
                    'boundary_still_settled_unchanged')
                store.copy(new_root/'MIGRATION_BEFORE.json', 'NODE:'+REMOTE_ROOT+'/R118_ASTRA_MIGRATION_BEFORE.json')
                store.shell('rmdir ' + shlex.quote(REMOTE_ROOT+'/parent_claude/RUNNER.lock'))
                successor = [part.replace(str(old_root), str(new_root)) for part in command]
                with (new_root/'BROKER.log').open('xb') as output:
                    child = subprocess.Popen(successor, cwd=new_root/'source', env=environment,
                        stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
                receipt = dict(old_identity=expected, new_identity=identity(Path('/proc')/str(child.pid)),
                    started_unix=time.time(), config_sha256=astra.transport.digest(config),
                    source_manifest_sha256=astra.transport.sha(new_root/'SOURCE_SHA256.json'),
                    native_child_untouched=True, raw_stays_node=True, reset=False)
                astra.transport.write(new_root/'MIGRATION_LAUNCH.json', receipt)
                return receipt
            finally:
                if stopped:
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                    stopped = False
                    time.sleep(3)
        raise TimeoutError('no_safe_broker_boundary_original_left_live')
    finally:
        os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old-root', type=Path, required=True)
    parser.add_argument('--new-root', type=Path, required=True)
    parser.add_argument('--expected', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(migrate(args.old_root, args.new_root, args.expected), sort_keys=True))
