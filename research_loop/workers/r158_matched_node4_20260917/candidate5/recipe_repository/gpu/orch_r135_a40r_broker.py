"""Controller-only exact R135 queue adapter; frozen provider and claims unchanged."""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


DEPENDENCY = Path('/tmp/orch_r129_dependencies_2106')
REPOSITORY = Path('/data/home/rohing/dream-state-orch')
DATA_PARENT = Path('/data/home/rohing/courier/runtime')
LANE = 'node1_7'
HOST_SHA = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
PRINCIPLES = 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md'
PRINCIPLES_SHA = 'b7f4d6baef8158b41533d15acf0f7c924b4bc1e875a30d6ca31f874b5e1c589d'
NATIVE_SOURCE_SHA = '7950db91ab668697027c1d113daca49d2c70d278cbbc2e308935cfb0a1c8a3aa'
PINS = {
    'gpu/orch_r111_route_recovery.py': '2b96471dbb7dbfde4ca749250a21828b04643257eae217a9aa9a49b5649102c4',
    'gpu/orch_r109_route_broker.py': 'ed5a903ccddc77c791ad38ead4dfa547dad9395511560fb9dda5f7867a9bafc4',
    'organism_v6/orch_r109_route.py': '8727c558770bf8b2afbd27b88277cd8291a4607cade7f6e1b9491bc207a41555',
}
SLOTS = {
    0: dict(root='/localhome/local-rohing/orch_r109_route_20260915_node1_7_attempt2',
        uuid='GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d', floor=113, cycle=53,
        prior='overflow_r129_v1', disposition='COMPLETE',
        ready_sha='d0769d1863a7a62d76ef003635e065d49cacbf9a6ff0af8d3691f88236d47e60',
        epoch_sha='0c8d22f2202b17710266206d8ca4c918ec83eacfb8e24a65490fc9c2da90839b',
        main_sha='6980ac46726fdd4d076bf5f6c88278bec42afb41b8208c33de85a7af6a844db3'),
    2: dict(root='/localhome/local-rohing/orch_r109_route_20260915_r120_C39_fork_a40r2_attempt1',
        uuid='GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8', floor=128, cycle=60,
        prior='lease_r120_v2', disposition='MISSING',
        ready_sha='494343a40016af7c82ba75b502b3bb10472393620e08b361aa71d6075db31342',
        epoch_sha='3f879fc6ef3d31f64286c484b4627d8c7dd00731f215be8c605b5f6c0d16111d',
        main_sha='c7ec9c2746169f1ea6df2d3e78e7106f0e050e7fce3bf0a5cec66503c7d8ea48'),
}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def slot(physical):
    require(type(physical) is int and physical in SLOTS, 'exact_physical_0_or_2')
    return SLOTS[physical]


def campaign(physical, root=None, lane=LANE):
    expected = Path(slot(physical)['root'])
    require((root is None or Path(root) == expected) and lane == LANE, 'exact_root_lane_queue')
    return expected / 'overflow_r135_v2' / ('campaign_' + LANE)


def validate_request_path(physical, own_campaign, path):
    config = slot(physical)
    require(Path(own_campaign) == campaign(physical) and Path(path).parent == campaign(physical) / 'parent_queue',
        'only_exact_new_queue')
    match = re.fullmatch(r'GUIDED_SLEEP_C([1-9][0-9]*)_P([1-9][0-9]*)\.request\.json', Path(path).name)
    require(match is not None, 'exact_parent_request_name')
    cycle, number = map(int, match.groups())
    require(config['floor'] <= number <= 640 and config['cycle'] <= cycle <= 256,
        'only_new_parent_numbers_no_historical_replay')
    return cycle, number


def remote_code(physical, published=False):
    config = dict(slot(physical), physical=physical, campaign=str(campaign(physical)),
        host_sha=HOST_SHA, principles_sha=PRINCIPLES_SHA, native_source_sha=NATIVE_SOURCE_SHA)
    return 'config = ' + repr(config) + '\npublished_required = ' + repr(published) + '''
import hashlib,json,socket,subprocess,time
from pathlib import Path
def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    return json.loads(Path(path).read_bytes())
root=Path(config['root']); output=Path(config['campaign'])
assert root.resolve()==root and output.resolve()==output, 'canonical_remote_queue'
assert hashlib.sha256(socket.gethostname().encode()).hexdigest()==config['host_sha'], 'exact_remote_host'
identity=subprocess.check_output(['nvidia-smi','--id='+str(config['physical']),'--query-gpu=index,uuid','--format=csv,noheader,nounits'],text=True).strip()
assert [part.strip() for part in identity.split(',')]==[str(config['physical']),config['uuid']], 'exact_remote_slot_uuid'
for name,pin in [('MAIN_READY.json','main_sha'),('EPOCH.json','epoch_sha'),('READY.json','ready_sha')]:
    assert digest(output/name)==config[pin], 'exact_remote_manifest'
assert digest(root/config['prior']/('campaign_node1_7')/'READY.json')==config['ready_sha'], 'original_READY'
main=read(output/'MAIN_READY.json'); epoch=read(output/'EPOCH.json'); ready=read(output/'READY.json')
assert main['epoch']==dict(path=str(output/'EPOCH.json'),sha256=config['epoch_sha']), 'MAIN_epoch_join'
assert main['original_ready']==epoch['ready']==dict(path=str(output/'READY.json'),sha256=config['ready_sha']), 'READY_join'
assert main['source']==epoch['source'] and epoch['source']['sha256']==config['native_source_sha'], 'native_source_binding'
assert digest(epoch['source']['path'])==config['native_source_sha'], 'native_source_unchanged'
assert main['native_cpu_tests']['path']==str(output/'NATIVE_CPU_TESTS.json'), 'native_CPU_path'
assert digest(output/'NATIVE_CPU_TESTS.json')==main['native_cpu_tests']['sha256'], 'native_CPU_binding'
assert main['physical']==epoch['physical']==config['physical'] and main['uuid']==epoch['uuid']==config['uuid'], 'manifest_slot'
assert main['host_sha256']==epoch['host_sha256']==config['host_sha'], 'manifest_host'
assert main['native_CPU_ready'] is True and main['no_adapter'] is True and main['optimizer_updates']==0, 'native_ready_BASE'
assert main['next_parent_number']==epoch['next_parent_number']==config['floor'], 'parent_floor'
assert main['parent_disposition']==epoch['parent_disposition']==config['disposition'], 'original_disposition'
assert ready['principles_sha256']==config['principles_sha'] and ready['learned'] is False, 'principles_BASE'
assert ready['parent_cap']==640 and ready['native_cap']==16384 and ready['hard_deadline_unix']==1789754400.0, 'original_caps_deadline'
assert time.time()<ready['hard_deadline_unix'] and not (output/'TERMINAL.json').exists(), 'active_epoch_bound'
publication_present=(output/'PUBLICATION.json').exists()
if published_required or publication_present:
    publication=read(output/'PUBLICATION.json')
    assert publication['epoch_sha256']==config['epoch_sha'] and publication['ready_sha256']==config['ready_sha'], 'published_epoch'
    assert publication['source_sha256']==config['native_source_sha'] and publication['dated_builder_publication'] is True, 'Main_publication'
    assert publication['allocation_sha256']==digest(output/'ALLOCATION.md'), 'allocation_binding'
print(json.dumps(dict(physical=config['physical'],uuid=config['uuid'],host_sha256=config['host_sha'],campaign=str(output),main_ready_sha256=config['main_sha'],epoch_sha256=config['epoch_sha'],ready_sha256=config['ready_sha'],provider_files=ready['provider_files'],principles_sha256=ready['principles_sha256'],publication_present=publication_present,next_parent_number=config['floor'])))
'''


def remote_snapshot(repository, physical, published=False):
    require(Path(repository).resolve() == REPOSITORY.resolve(), 'existing_wrapper_repository_only')
    result = subprocess.run(['bash', str(Path(repository) / 'gpu/a40r_ssh.sh'), 'python3 -'],
        input=remote_code(physical, published), capture_output=True, text=True, timeout=90)
    require(result.returncode == 0, 'remote_manifest_verification_failed_no_provider_call')
    return json.loads(result.stdout)


def validate_snapshot(physical, snapshot):
    config = slot(physical)
    expected = dict(physical=physical, uuid=config['uuid'], host_sha256=HOST_SHA,
        campaign=str(campaign(physical)), main_ready_sha256=config['main_sha'], epoch_sha256=config['epoch_sha'],
        ready_sha256=config['ready_sha'], principles_sha256=PRINCIPLES_SHA, next_parent_number=config['floor'])
    require(all(snapshot[key] == value for key, value in expected.items()), 'exact_remote_snapshot_join')
    require(snapshot['provider_files'].get(PRINCIPLES) == PRINCIPLES_SHA, 'original_principles_provider_pin')


def verify_dependencies(provider_files):
    require(DEPENDENCY.resolve() == DEPENDENCY, 'exact_pinned_dependency_root')
    for relative, expected in list(PINS.items()) + list(provider_files.items()) + [(PRINCIPLES, PRINCIPLES_SHA)]:
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'relative_dependency_file')
        path = DEPENDENCY / relative
        require(path.resolve() == path and sha(path) == expected, 'frozen_provider_dependency_hash')


def validate_data_device(target_device, data_device, root_device):
    require(target_device == data_device and target_device != root_device, 'raw_storage_on_data_not_VMroot')


def storage(physical):
    slot(physical)
    target = DATA_PARENT / f'r135_broker_a40r{physical}_v1'
    alias = Path(f'/tmp/orch_r135_broker_a40r{physical}_v1')
    require(DATA_PARENT.resolve() == DATA_PARENT and DATA_PARENT.is_dir(), 'canonical_data_runtime_parent')
    validate_data_device(DATA_PARENT.stat().st_dev, Path('/data').stat().st_dev, Path('/').stat().st_dev)
    require(target.resolve() == target and not target.is_symlink(), 'canonical_data_buffer_target')
    if alias.exists() or alias.is_symlink():
        require(alias.is_symlink() and os.readlink(alias) == str(target), 'exact_tmp_compatibility_parent')
    return target, alias


@contextmanager
def queue_owner(physical):
    target, alias = storage(physical)
    target.mkdir(mode=0o700, exist_ok=True)
    lock_path = target / 'QUEUE.lock'
    require(not lock_path.is_symlink(), 'regular_queue_lock')
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not alias.is_symlink():
            alias.symlink_to(target, target_is_directory=True)
        storage(physical)
        require(not (target / 'buffer').exists() and not (target / 'buffer').is_symlink()
            and not (target / 'receipts').exists() and not (target / 'receipts').is_symlink(),
            'new_bounded_buffer_receipts_only_no_restart')
        yield alias / 'buffer', alias / 'receipts'


def request_gate(store, physical, path, ready_sha):
    cycle, number = validate_request_path(physical, campaign(physical), path)
    require(ready_sha == slot(physical)['ready_sha'], 'request_original_READY')
    config = dict(root=slot(physical)['root'], path=str(path), cycle=cycle, number=number, ready_sha=ready_sha)
    code = 'config = ' + repr(config) + '''
import json
from pathlib import Path
path=Path(config['path'])
assert path.resolve()==path, 'no_request_redirect'
request=json.loads(path.read_bytes()); payload=request['payload']
assert request['id']==path.name.removesuffix('.request.json'), 'actual_request_id'
assert request['ready_sha256']==config['ready_sha'], 'original_request_READY'
assert payload['cycle']==config['cycle'] and payload['split']=='TRAIN', 'actual_TRAIN_cycle'
rows=[json.loads(line) for line in (Path(config['root'])/'RESERVATIONS.jsonl').read_bytes().splitlines() if line.strip()]
intents=[row for row in rows if row['kind']=='PARENT' and row['number']==config['number']]
assert len(intents)==1, 'single_actual_new_parent_intent'
intent=intents[0]
assert intent['lane']=='node1_7' and intent['cycle']==config['cycle'] and intent['mode']==payload['mode'] and intent['turn']==payload['turn'], 'actual_parent_charge_join'
print('R135_REQUEST_SCOPE_OK')
'''
    result = store.shell('python3 -c ' + shlex.quote(code), check=False)
    require(result.returncode == 0 and result.stdout.strip() == 'R135_REQUEST_SCOPE_OK',
        'new_request_provenance_failed_before_claim')


def load_runtime(physical, provider_files):
    config = slot(physical)
    verify_dependencies(provider_files)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(DEPENDENCY))
    for name in ('gpu', 'organism_v6'):
        package = __import__(name)
        package.__path__ = [str(DEPENDENCY / name)] + list(package.__path__)
    source = DEPENDENCY / 'gpu/orch_r111_route_recovery.py'
    spec = importlib.util.spec_from_file_location('r135_controller_frozen_recovery', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for relative in set(PINS) | set(provider_files):
        if relative.endswith('.py'):
            name = relative[:-3].replace('/', '.')
            require(name not in sys.modules or Path(sys.modules[name].__file__).resolve() == DEPENDENCY / relative,
                'no_unpinned_provider_import_shadowing')
    return bind(module, physical)


def bind(module, physical):
    config = slot(physical)
    require(not hasattr(module.old_broker, '_r135_bound_physical'), 'one_exact_queue_binding_per_process')
    policy = module.old.policy
    require(policy is module.old_broker.policy and policy.PRINCIPLES_SHA == PRINCIPLES_SHA
        and policy.HOSTS['node1'] == dict(wrapper='gpu/a40r_ssh.sh', scp='gpu/a40r_scp.sh', sha256=HOST_SHA),
        'unchanged_provider_host_wrapper_principles')
    policy.LANES[LANE] = dict(policy.LANES[LANE], host='node1', physical=physical, uuid=config['uuid'])
    policy.DEVICES[LANE] = config['uuid']
    require(policy.LANES[LANE]['learned'] is False, 'frozen_BASE_lane')
    module.directory = lambda root, lane: campaign(physical, root, lane)
    original = module.old_broker.process

    def process(store, own_campaign, path, buffer, receipts, ready_sha, principles, deadline):
        validate_request_path(physical, own_campaign, path)
        target, alias = storage(physical)
        require(Path(buffer) == alias / 'buffer' and Path(receipts) == alias / 'receipts', 'exact_bounded_data_paths')
        request_gate(store, physical, path, ready_sha)
        return original(store, own_campaign, path, buffer, receipts, ready_sha, principles, deadline)

    module.old_broker.process = process
    module.old_broker._r135_bound_physical = physical
    return module


def preflight(physical, repository, published=False):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'controller_CPU_only')
    snapshot = remote_snapshot(repository, physical, published)
    validate_snapshot(physical, snapshot)
    verify_dependencies(snapshot['provider_files'])
    target, alias = storage(physical)
    return snapshot, dict(schema='R135_CONTROLLER_BROKER_CPU_READY_V1', physical=physical,
        campaign=str(campaign(physical)), uuid=slot(physical)['uuid'], host_sha256=HOST_SHA,
        next_parent_number=slot(physical)['floor'], main_ready_sha256=slot(physical)['main_sha'],
        epoch_sha256=slot(physical)['epoch_sha'], ready_sha256=slot(physical)['ready_sha'],
        broker_source_sha256=sha(Path(__file__).resolve()), dependency_root=str(DEPENDENCY),
        data_directory=str(target), compatibility_parent=str(alias), buffer=str(alias / 'buffer'),
        receipts=str(alias / 'receipts'), queue_lock=str(target / 'QUEUE.lock'),
        provider_files_verified=len(snapshot['provider_files']), publication_present=snapshot['publication_present'],
        provider_calls=0, broker_started=False, launch_authorized=False)


def serve(physical, repository):
    snapshot, receipt = preflight(physical, repository, published=True)
    with queue_owner(physical) as (buffer, receipts):
        module = load_runtime(physical, snapshot['provider_files'])
        verify_dependencies(snapshot['provider_files'])
        receipt.update(broker_pid=os.getpid(), started_unix=time.time(), broker_started=True)
        with (receipts.parent / 'BROKER_START.json').open('x') as stream:
            json.dump(receipt, stream, sort_keys=True, indent=2)
        print(json.dumps(receipt, sort_keys=True), flush=True)
        module.broker(Path(repository), Path(slot(physical)['root']), LANE, buffer, receipts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('check', 'serve'))
    parser.add_argument('--physical', type=int, choices=tuple(SLOTS), required=True)
    parser.add_argument('--repository', type=Path, default=REPOSITORY)
    arguments = parser.parse_args()
    if arguments.phase == 'check':
        snapshot, receipt = preflight(arguments.physical, arguments.repository)
        load_runtime(arguments.physical, snapshot['provider_files'])
        receipt['frozen_imports_verified'] = True
        print(json.dumps(receipt, sort_keys=True))
    else:
        serve(arguments.physical, arguments.repository)


if __name__ == '__main__':
    main()
