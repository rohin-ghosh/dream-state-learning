"""Physical7-only saved-boundary successor under the exact shared R157 authority."""

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
import signal
import socket
import subprocess
import sys
import time
from types import SimpleNamespace
import uuid


BASE = Path('/localhome/local-rohing')
LIFE = BASE / 'orch_r136_repo_reader_20260916_attempt1'
OLD = LIFE / 'recovery_r154_saved30_20260916_attempt2'
ROOT = LIFE / 'run1'
HOST_ROOT = OLD / 'run1'
SOURCE = OLD / 'source'
PYTHON = BASE / 'v2/venv/bin/python'
HOST = '[REDACTED_HOST]'
GPU = 'GPU-9e6cdf73-7181-4405-2aec-787cc73a3e5b'
AUTH_SHA = '05c50f8012559360221a889b26c00700a988878fbe4d32d30e3f786937dfc392'
GUARD_SHA = 'cbab72f928bbbea8ace4ebcf9dacec4fe0dbacd941c921e6dd20d608b192ed4d'
PLAN_SHA = '80c2d39c42027fd5f66481639ef36ffb711d782ac9f45f1a346e3dbe738ba175'
BROKER_SHA = 'e72e7b615464164e7f40c3338422010fd75fd17dbf9ba57265281586ca32b454'
API_SHA = '7e508166d43128a987d2f2beed598eafc5b94d2e9a05a56c6a73b53b4e4b34c5'
CAPSULE_SHA = '29e2d77dfe21a6c1b37861f52c00d2eeb858c67b60f054ab6e2d2238cc135c95'
SNAPSHOT_SHA = '565dc5676f597e0ad6ef5bbde6dd35612ee9bf2a28846a76b44768c07cc999d2'
TOOL_PINS_SHA = 'da18586f684c1fcacae0a6960083cadd6c927cc6af2a6d5c19583736e5a4169d'
SEGMENT = 'repo_reader_saved30_62fa3f7f68e44cf2a7042c4151fe4335'
OLD_WALL = 1789617240
NEW_WALL = 1789776000
CEILING = 1789776600
IDENTITIES = {'actor': (1715090, '13616712'), 'timer': (1715089, '13616712'),
              'supervisor': (1715049, '13616681'), 'broker': (1717235, '13621066')}
SIGNAL_ROLES = frozenset({'actor', 'broker'})


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def regular(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts
            and not any(part.is_symlink() for part in (path, *path.parents)), 'absolute_regular_path')
    return path


def sha(path):
    result = hashlib.sha256()
    with regular(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(regular(path).read_bytes())


def write(path, document):
    with regular(path).open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def ref(path):
    return {'path': str(regular(path)), 'sha256': sha(path)}


def load_api(filename, checksum):
    path = Path(__file__).resolve().parent / filename
    require(sha(path) == checksum, 'pinned_CPU_dependency:' + filename)
    spec = importlib.util.spec_from_file_location('r157_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def confinement():
    capsule = load_api('CONFINEMENT_API.py', CAPSULE_SHA)
    capsule.DEVICES = {7: GPU}
    return capsule


def authority(path):
    require(sha(path) == AUTH_SHA, 'exact_Main_shared_authorization')
    document = read(path)
    require(document['host'] == HOST and 'repo_reader' in document['lives']
            and 7 in document['physical_devices'] and document['reset'] is False
            and document['learning_recipe_change'] is False and document['visibility_change'] is False
            and document['authorization_is_runtime_budget_not_provider_booking'] is True
            and document['purchase_or_lease_transaction_authorized'] is False
            and document['must_abort_on_conflicting_real_reservation'] is True,
            'same_life_runtime_only_authority')
    return document


def conflict_check(path, now=None):
    document = read(path)
    now = time.time() if now is None else now
    observed = datetime.fromisoformat(document['observed_utc'].replace('Z', '+00:00')).timestamp()
    require(document['schema'] == 'R157_NODE5_TARGETED_RESERVATION_AUDIT_V1'
            and document['host'] == HOST and document['authorization_sha256'] == AUTH_SHA
            and document['conflicting_real_reservation_found'] is False
            and document['numeric_cutoff_is_not_booking'] is True
            and document['purchase_performed'] is False and 0 <= now - observed <= 10800,
            'fresh_shared_actual_reservation_check')
    for receipt in document['actual_reservation_receipts']:
        require(sha(receipt['path']) == receipt['sha256'], 'actual_reservation_receipt_pin')
        actual = read(receipt['path'])
        require(actual['host'] == HOST and actual['reservation_end_unix'] >= CEILING,
                'conflicting_real_reservation_blocks_extension')
    return document


def scope(plan, config):
    require(type(plan['physical']) is int and plan['physical'] == 7
            and plan['gpu_uuid'] == GPU and plan['root'] == str(ROOT)
            and plan['source_root'] == str(SOURCE) and config['resume'] is True,
            'only_recovered_repo_reader_physical7')
    require(config['device_containment']['uid'] == config['device_containment']['gid'] == 2524
            and config['device_containment']['minor'] == 7, 'same_UID_GID_minor')


def namespace():
    require(socket.gethostname() == HOST and os.getuid() == os.getgid() == 2524, 'exact_host_owner')
    logical, physical = ROOT.stat(), HOST_ROOT.stat()
    require((logical.st_dev, logical.st_ino) == (physical.st_dev, physical.st_ino)
            == (66307, 40503107), 'same_recovered_mount_not_archival_root')


def original_modules():
    require(sha(OLD / 'GUARD.json') == GUARD_SHA and sha(OLD / 'PLAN.json') == PLAN_SHA,
            'unchanged_R154_control_bytes')
    config, plan = read(OLD / 'GUARD.json'), read(OLD / 'PLAN.json')
    scope(plan, config)
    require({str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
            == config['source_pins'], 'entire_original_source_closure')
    sys.path.insert(0, str(SOURCE))
    modules = {}
    for label, name in (('guard', 'gpu.orch_r125_continual_guard'),
                        ('native', 'gpu.orch_r125_continual_native'),
                        ('journal', 'gpu.orch_r125_stream_journal')):
        module = importlib.import_module(name)
        require(Path(module.__file__).resolve() == SOURCE / (name.replace('.', '/') + '.py'),
                'frozen_source_import_only')
        modules[label] = module
    return config, plan, SimpleNamespace(**modules)


def cpu_gate(path):
    gate = read(path)
    require(gate['status'] == 'PASS' and gate['tests'] >= 20
            and gate['operator_sha256'] == sha(Path(__file__).resolve())
            and sha(gate['test']['path']) == gate['test']['sha256']
            and sha(gate['log']['path']) == gate['log']['sha256']
            and gate['builder_entry'].strip(), 'posted_exact_CPU_provenance')
    return gate


def output_scope(output):
    output = regular(output)
    require(output.parent == BASE and output.name.startswith('orch_r157_repo_reader_wall_'),
            'new_R157_control_only')
    return output


def identity(role, api):
    require(role in IDENTITIES, 'known_owned_role')
    pid, ticks = IDENTITIES[role]
    record = api.identity(pid)
    require(record['start_ticks'] == ticks and record['uid'] == 2524, 'pinned_pid_start_UID')
    helper = str(BASE / 'orch_r154_repo_reader_tools_20260916t2312z/gpu/orch_r154_repo_reader_recover.py')
    actor = [str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(OLD / 'GUARD.json')]
    expected = {'actor': actor,
                'timer': ['timeout', '--signal=TERM', '--kill-after=5s', '16623s', *actor],
                'supervisor': [str(PYTHON), '-B', helper, '--action', 'contained', '--output', str(OLD)],
                'broker': [str(PYTHON), '-B', helper, '--action', 'broker', '--output', str(OLD)]}
    require(record['argv'] == expected[role] and record['cwd'] == ('/' if role == 'broker' else str(SOURCE)),
            'exact_owned_argv_cwd')
    require(record['parent'] == {'actor':1715089, 'timer':1715049, 'supervisor':1, 'broker':1}[role],
            'exact_parent_custody')
    unit = ('orch-r154-reader-broker-8146f9777077469db3934e161db32071' if role == 'broker'
            else 'orch-r136-native-97ad8dff17e34953b48554cdfecb416d')
    require(record['cgroup'] == '0::/system.slice/' + unit + '.service', 'exact_owned_cgroup')
    return record


def send(role, descriptor, signum):
    require(role in SIGNAL_ROLES and signum in (signal.SIGSTOP, signal.SIGCONT, signal.SIGTERM),
            'only_actor_broker_narrow_nonKILL_signals')
    signal.pidfd_send_signal(descriptor, signum)


def boundary_plan(old_plan, saved, resource_ceiling=CEILING):
    state = saved['state']
    require(state['pending'] is None and state['sleep_frontier'] == len(state['rows'])
            and state['sleep_receipts'] and state['sleep_receipts'][-1]['status'] == 'COMPLETE',
            'exact_completed_saved_boundary')
    require(digest(state) == saved['state_sha256'] and state['deadline_unix'] == OLD_WALL
            and old_plan['hard_end_unix'] == OLD_WALL and resource_ceiling == CEILING,
            'exact_old_state_and_new_resource_ceiling')
    require(old_plan.get('preupdate_recovery') is None, 'no_replay_or_preupdate_recovery')
    plan = deepcopy(old_plan)
    plan.update(hard_end_unix=NEW_WALL, lease_end_unix=resource_ceiling,
                authorized_wall_extension=dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1',
                    previous_deadline_unix=OLD_WALL, previous_stream_sha256=saved['state_sha256'],
                    new_deadline_unix=NEW_WALL, lease_end_unix=resource_ceiling, safety_margin_seconds=600))
    require({key for key in plan if plan[key] != old_plan.get(key)}
            <= {'hard_end_unix', 'lease_end_unix', 'authorized_wall_extension'}, 'wall_only_plan_delta')
    return plan


def broker_reconciliation(directory, cursor, head_index, head_sha, journal_root):
    require(cursor['index'] == head_index and cursor['next_index'] == head_index + 1
            and cursor['record_sha256'] == head_sha, 'broker_caught_up_exact_saved_head')
    pending, receipts = {}, []
    for intent in sorted(directory.glob('INTENT_*.json')):
        require((directory / intent.name.replace('INTENT_', 'READ_', 1)).is_file(), 'no_unresolved_broker_INTENT')
    for path in sorted(directory.glob('READ_*.json')):
        receipt = read(path)
        require(receipt['manifest_sha256'] == SNAPSHOT_SHA, 'same_snapshot_publication')
        publication = receipt['publication']
        require(publication['id'] not in {item['publication_id'] for item in receipts}, 'unique_prior_publications')
        inbox = journal_root / 'inbox' / (publication['id'] + '.json')
        require(sha(inbox) == publication['sha256'], 'retained_published_inbox_bytes')
        consumed_path = directory / path.name.replace('READ_', 'CONSUMED_', 1)
        item = dict(read=ref(path), publication_id=publication['id'], publication_sha256=publication['sha256'])
        if consumed_path.exists():
            consumed = read(consumed_path)
            record = read(journal_root / 'records' / f"{consumed['record_index']:020d}.json")
            require(consumed['record_index'] <= head_index and consumed['inbox_id'] == publication['id']
                    and record['kind'] == 'INBOX' and record['sha256'] == consumed['record_sha256']
                    and record['document']['message']['id'] == publication['id']
                    and record['document']['source_sha256'] == publication['sha256'], 'consumed_publication_hash_join')
            item['consumed'] = ref(consumed_path)
        else:
            pending[publication['id']] = path.stem.removeprefix('READ_')
        receipts.append(item)
    return dict(start_index=head_index + 1, previous_sha256=head_sha, inherited_pending=pending,
                reconciled_reads=receipts, replay_past_reads=False, publish_initial_connection=False)


def snapshot_tools():
    require(sha(OLD / 'BROKER_CONFIG.json') == BROKER_SHA
            and sha(LIFE / 'snapshot1/MANIFEST.json') == SNAPSHOT_SHA
            and sha(LIFE / 'SIDECAR_SOURCE_PINS_V2.json') == TOOL_PINS_SHA, 'original_snapshot_and_broker_pins')
    expected = read(LIFE / 'SIDECAR_SOURCE_PINS_V2.json')
    require({str(path.relative_to(LIFE / 'toolsource2')): sha(path)
             for path in (LIFE / 'toolsource2').rglob('*.py')} == expected, 'entire_original_broker_closure')


def prepare(output, authority_path, cpu_path, conflict_path):
    namespace()
    authority(authority_path)
    cpu_gate(cpu_path)
    conflict_check(conflict_path)
    config, plan, original = original_modules()
    require(original.guard.validate(OLD / 'GUARD.json') == (config, plan), 'original_live_guard_validation')
    require(time.time() < OLD_WALL - 300, 'old_timer_headroom')
    snapshot_tools()
    api = load_api('BOUNDARY_API.py', API_SHA)
    actors = {role:identity(role, api) for role in IDENTITIES}
    output = output_scope(output)
    output.mkdir(mode=0o700)
    for name in ('broker', 'file_receipts'):
        (output / name).mkdir(mode=0o700)
    write(output / 'REQUEST.json', dict(authority=ref(authority_path), cpu=ref(cpu_path),
        conflict=ref(conflict_path), operator=ref(Path(__file__).resolve()), identities=actors,
        source_root=str(SOURCE), host_root=str(HOST_ROOT), logical_root=str(ROOT),
        segment_id=SEGMENT, physical=7, gpu_uuid=GPU, prepared_unix=time.time(), stop_or_launch_attempted=False))
    write(output / 'LEASE_BUDGET.json', dict(schema='R157_EXPLICIT_RUNTIME_BUDGET_V1',
        hard_end_unix=NEW_WALL, lease_end_unix=CEILING, safety_margin_seconds=600,
        compatibility_lease_end_is_resource_ceiling_not_provider_expiry=True,
        provider_reservation_expiry_verified=False, purchase_or_lease_transaction=False,
        authorization=ref(authority_path), previous_budget=ref(config['lease_path'])))
    return dict(status='PREPARED_NO_SIGNAL', output=str(output))


def request_gate(output):
    namespace()
    request = read(output / 'REQUEST.json')
    for name in ('authority', 'cpu', 'conflict', 'operator'):
        require(sha(request[name]['path']) == request[name]['sha256'], 'unchanged_request:' + name)
    require(request['operator']['sha256'] == sha(Path(__file__).resolve()), 'exact_prepared_operator')
    authority(request['authority']['path'])
    cpu_gate(request['cpu']['path'])
    conflict_check(request['conflict']['path'])
    return request


def stage_boundary(output, saved, original, old_config, old_plan, evidence):
    plan = boundary_plan(old_plan, saved)
    write(output / 'PLAN.json', plan)
    allocation = deepcopy(read(old_config['allocation_path']))
    allocation.update(plan_sha256=sha(output / 'PLAN.json'), declared_unix=time.time(),
        builder_entry=read(read(output / 'REQUEST.json')['cpu']['path'])['builder_entry'],
        builder_entry_pushed=True, cpu_tests_passed=True, checkpoint_resume=True)
    write(output / 'ALLOCATION.json', allocation)
    config = dict(old_config, plan_path=str(output / 'PLAN.json'), plan_sha256=sha(output / 'PLAN.json'),
        allocation_path=str(output / 'ALLOCATION.json'), allocation_sha256=sha(output / 'ALLOCATION.json'),
        lease_path=str(output / 'LEASE_BUDGET.json'), lease_sha256=sha(output / 'LEASE_BUDGET.json'),
        hard_end_unix=NEW_WALL, next_reserved_unix=CEILING, attempt_dir=str(output), resume=True,
        device_containment=dict(uid=2524, gid=2524, minor=7, unit='orch-r136-native-' + uuid.uuid4().hex))
    write(output / 'GUARD.json', config)
    require(original.guard.validate(output / 'GUARD.json') == (config, plan), 'successor_original_guard_validation')
    stream = original.native.ContinualStream.restore(dict(state=saved['state'], sha256=saved['state_sha256']),
                                                   expected_sha256=saved['state_sha256'])
    before = stream.checkpoint()
    transition = original.native.prepare_wall_extension(plan, stream, resume=True, plan_sha256=config['plan_sha256'])
    after = deepcopy(transition['state']['state'])
    after['deadline_unix'] = OLD_WALL
    require(after == saved['state'] and stream.checkpoint() == before, 'only_deadline_changes_exact_context')
    write(output / 'BOUNDARY_CPU.json', dict(status='PASS', evidence=evidence,
        expected_new_state_sha256=transition['state']['sha256'], config=ref(output / 'GUARD.json'),
        source_recipe_unchanged=True, no_optimizer_reset=True, checked_unix=time.time()))


def watchdog(descriptors, pipe, seconds):
    ready = select.select([pipe], [], [], seconds)[0]
    if ready and os.read(pipe, 1) == b'D':
        return
    for descriptor in descriptors:
        try:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        except ProcessLookupError:
            pass


def handoff(output, seconds):
    request = request_gate(output)
    require(type(seconds) is int and 1 <= seconds <= 5400, 'bounded_wait')
    config, plan, original = original_modules()
    api = load_api('BOUNDARY_API.py', API_SHA)
    descriptors, paused = {}, []
    reader = writer = None
    monitor = None
    (output / 'HANDOFF_ONCE').mkdir()
    try:
        for role in IDENTITIES:
            require(identity(role, api) == request['identities'][role], 'prepared_identity_unchanged')
            descriptors[role] = os.pidfd_open(IDENTITIES[role][0])
            require(identity(role, api) == request['identities'][role], 'identity_after_pidfd')
        deadline = min(time.monotonic() + seconds, time.monotonic() + OLD_WALL - time.time() - 180)
        attempts = 0
        while time.monotonic() < deadline:
            saved = api.sleep_boundary(ROOT)
            if saved is None:
                time.sleep(.2)
                continue
            attempts += 1
            snapshot = output / f'SNAPSHOT_{attempts:04d}'
            snapshot.mkdir(mode=0o700)
            evidence = api.saved_evidence(plan, saved, original)
            shutil.copytree(ROOT / 'stream', snapshot / 'stream')
            try:
                api.verify_snapshot(snapshot / 'stream', ROOT, saved['state_sha256'], original)
                shutil.copytree(Path(evidence['checkpoint_path']).parent, snapshot / 'checkpoint')
                for path in (snapshot / 'checkpoint').rglob('*'):
                    if path.is_file():
                        require(sha(path) == sha(Path(evidence['checkpoint_path']).parent /
                                               path.relative_to(snapshot / 'checkpoint')), 'checkpoint_copy_exact')
                require(api.sleep_boundary(ROOT) == saved, 'boundary_moved_before_pause')
            except (ValueError, FileNotFoundError) as error:
                write(snapshot / 'MOVED.json', dict(status='NO_SIGNAL', error=str(error)))
                continue
            reader, writer = os.pipe()
            command = [str(PYTHON), '-B', str(Path(__file__).resolve()), 'watchdog', '--seconds', '240',
                       '--pipe', str(reader), '--fds', str(descriptors['actor']), str(descriptors['broker'])]
            monitor = subprocess.Popen(command, pass_fds=(reader, descriptors['actor'], descriptors['broker']),
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.close(reader)
            reader = None
            paused.append('actor')
            api.pause_exact(request['identities']['actor'], descriptors['actor'])
            require(api.sleep_boundary(ROOT) == saved, 'no_new_charge_after_pause')
            pause_deadline = time.monotonic() + 150
            readout_plan = dict(plan, _plan_path=str(OLD / 'PLAN.json'))
            while time.monotonic() < pause_deadline:
                status = api.readout_status(readout_plan, saved, IDENTITIES['actor'][0], original)
                if status and status['complete_marker'] and not status['active_pids']:
                    break
                time.sleep(.2)
            else:
                raise TimeoutError('readout_not_complete_keep_original')
            name = original.native.readout_name(plan, saved['cycle'])
            complete = read(ROOT / 'readouts' / name / 'COMPLETE.json')
            require(complete['status'] == 'COMPLETE'
                    and complete['checkpoint_commit_sha256'] == evidence['checkpoint_file_sha256'],
                    'successful_saved_checkpoint_readout_metadata')
            while time.monotonic() < pause_deadline:
                cursors = sorted((OLD / 'broker').glob('CURSOR_*.json'))
                if cursors and read(cursors[-1])['index'] == int(Path(saved['path']).stem):
                    break
                time.sleep(.1)
            paused.append('broker')
            api.pause_exact(request['identities']['broker'], descriptors['broker'])
            cursor = read(sorted((OLD / 'broker').glob('CURSOR_*.json'))[-1])
            reconciliation = broker_reconciliation(OLD / 'broker', cursor,
                int(Path(saved['path']).stem), saved['record_sha256'], ROOT / 'stream')
            require(api.sleep_boundary(ROOT) == saved and api.saved_evidence(plan, saved, original) == evidence,
                    'final_exact_saved_state_no_update')
            request_gate(output)
            stage_boundary(output, saved, original, config, plan, evidence)
            broker = deepcopy(read(OLD / 'BROKER_CONFIG.json'))
            broker.update(reconciliation, hard_end_unix=NEW_WALL, output=str(output / 'broker'),
                          receipts=str(output / 'file_receipts'), predecessor_broker=str(OLD / 'broker'))
            write(output / 'BROKER_CONFIG.json', broker)
            write(output / 'BOUNDARY.json', dict(saved=evidence, snapshot=str(snapshot),
                broker_reconciliation=reconciliation, readout_complete=ref(ROOT / 'readouts' / name / 'COMPLETE.json'),
                stop_unix=time.time(), state_unchanged=True, source_unchanged=True))
            require(time.monotonic() < pause_deadline, 'pause_budget_before_exit')
            for role in ('broker', 'actor'):
                require(identity(role, api) == request['identities'][role], 'exact_identity_before_TERM')
                send(role, descriptors[role], signal.SIGTERM)
                send(role, descriptors[role], signal.SIGCONT)
                require(bool(select.select([descriptors[role]], [], [], 20)[0]), 'owned_' + role + '_exit')
            for role in ('timer', 'supervisor'):
                require(bool(select.select([descriptors[role]], [], [], 20)[0]), 'natural_' + role + '_exit')
            require(api.sleep_boundary(ROOT) == saved, 'postexit_no_extra_work')
            write(output / 'RETIRED.json', dict(status='EXACT_ACTOR_BROKER_EXITED_PARENTS_NATURAL',
                boundary=ref(output / 'BOUNDARY.json'), identities=request['identities'], finished_unix=time.time()))
            return dict(status='SAVED_BOUNDARY_READY_FOR_FRESH_ADMISSION', cycle=saved['cycle'],
                        optimizer_steps=evidence['optimizer_steps'])
        write(output / 'WAIT_EXPIRED.json', dict(status='NO_SIGNAL_NO_RESTART', finished_unix=time.time()))
        return dict(status='WAIT_EXPIRED')
    except BaseException as error:
        write(output / ('FAILED_' + str(time.time_ns()) + '.json'), dict(error=str(error),
            error_type=type(error).__name__, retired=(output / 'RETIRED.json').exists(), finished_unix=time.time()))
        raise
    finally:
        for role in reversed(paused):
            try:
                send(role, descriptors[role], signal.SIGCONT)
            except ProcessLookupError:
                pass
        if writer is not None:
            try:
                os.write(writer, b'D')
            except BrokenPipeError:
                pass
            os.close(writer)
        if monitor is not None:
            monitor.wait(timeout=5)
        for descriptor in descriptors.values():
            os.close(descriptor)


def successor_gate(output):
    request_gate(output)
    require(read(output / 'RETIRED.json')['boundary'] == ref(output / 'BOUNDARY.json'), 'retired_boundary_binding')
    config, plan = read(output / 'GUARD.json'), read(output / 'PLAN.json')
    scope(plan, config)
    require(plan['hard_end_unix'] == NEW_WALL and plan['lease_end_unix'] == CEILING
            and read(output / 'BOUNDARY_CPU.json')['config'] == ref(output / 'GUARD.json'), 'bound_successor_CPU')
    unused_config, unused_plan, original = original_modules()
    require(original.guard.validate(output / 'GUARD.json') == (config, plan), 'fresh_guard_validation')
    return config, plan, original


def native_command(config, plan, output):
    capsule = confinement()
    payload = [str(PYTHON), '-B', str(Path(__file__).resolve()), 'contained', '--output', str(output)]
    command = capsule.device_containment_command(7, 7, 2524, 2524,
        config['device_containment']['unit'], SOURCE, payload, int(NEW_WALL - time.time()))
    command = [value.replace('KillMode=control-group', 'KillMode=process') for value in command]
    position = command.index('/usr/bin/env')
    command[position:position] = ['--property=SendSIGKILL=no', '--property=BindPaths=' + str(HOST_ROOT) + ':' + str(ROOT)]
    command.insert(command.index('/usr/bin/env') + 2, 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True')
    return command


def launch(output):
    config, plan, original = successor_gate(output)
    api = load_api('BOUNDARY_API.py', API_SHA)
    saved = api.sleep_boundary(ROOT)
    expected = read(output / 'BOUNDARY.json')['saved']
    require(saved is not None and saved['state_sha256'] == expected['state_sha256']
            and sha(saved['path']) == expected['record_sha256'], 'postexit_boundary_before_admission')
    (output / 'DISPATCH_ONCE').mkdir()
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + str(SOURCE), str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard',
        'scan', '--config', str(output / 'GUARD.json')]
    report = json.loads(subprocess.check_output(command, text=True, timeout=100))
    write(output / 'ADMISSION.json', report)
    require(report['scanner_euid'] == 0 and report['clear'] and not report['blocking_reasons']
            and report['gpu']['uuid'] == GPU, 'fresh_privileged_exclusive_admission')
    write(output / 'ADMISSION_TIME.json', dict(verified_unix=time.time()))
    command = native_command(config, plan, output)
    write(output / 'CONTAINED_COMMAND.json', dict(command=command))
    with (output / 'SUPERVISOR.log').open('x') as log:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
    write(output / 'DISPATCHED.json', dict(pid=process.pid, started_unix=time.time(), no_retry=True))
    return dict(status='DISPATCHED_NOT_YET_LOADED', pid=process.pid)


def contained(output):
    config, plan, original = successor_gate(output)
    capsule = confinement()
    proof = capsule.verify_device_containment(config, plan)
    write(output / 'CONTAINMENT_VERIFIED.json', proof)
    report = read(output / 'ADMISSION.json')
    admitted = read(output / 'ADMISSION_TIME.json')['verified_unix']
    require(report['scanner_euid'] == 0 and report['clear'] and not report['blocking_reasons']
            and report['gpu']['uuid'] == GPU and 0 <= time.time() - admitted < 100,
            'fresh_admission_before_child')
    require(os.environ.get('PYTORCH_CUDA_ALLOC_CONF') == 'expandable_segments:True', 'retained_allocator')
    command = ['timeout', '--foreground', '--signal=TERM', str(int(NEW_WALL - time.time() - 10)) + 's',
               str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(output / 'GUARD.json')]
    with (output / 'NATIVE.log').open('x') as log:
        process = subprocess.Popen(command, cwd=SOURCE, stdin=subprocess.PIPE, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        ticks = (Path('/proc') / str(process.pid) / 'stat').read_text().rsplit(')', 1)[1].split()[19]
        original.guard.publish_launch(output / 'LAUNCH.json', dict(pid=process.pid, parent_start_ticks=ticks,
            guard_sha256=sha(output / 'GUARD.json'), plan_sha256=config['plan_sha256'], gpu_uuid=GPU,
            hard_end_unix=NEW_WALL, admission_verified_unix=admitted,
            admission_sha256=sha(output / 'ADMISSION.json'), command_sha256=digest(command),
            started_unix=time.time(), no_retry=True))
        process.stdin.write(b'LAUNCH_READY\n')
        process.stdin.close()
        status = process.wait()
    write(output / 'EXIT.json', dict(exit_code=status, finished_unix=time.time(), no_retry=True))


def broker_command(output):
    return ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe',
        '--unit=orch-r157-reader-broker-' + uuid.uuid4().hex,
        '--property=User=2524', '--property=Group=2524', '--property=NoNewPrivileges=yes',
        '--property=CapabilityBoundingSet=', '--property=AmbientCapabilities=', '--property=DevicePolicy=strict',
        '--property=ProtectSystem=strict', '--property=ProtectControlGroups=yes', '--property=PrivateNetwork=yes',
        '--property=KillMode=process', '--property=SendSIGKILL=no',
        '--property=RuntimeMaxSec=' + str(int(NEW_WALL - time.time())),
        '--property=BindPaths=' + str(HOST_ROOT) + ':' + str(ROOT), '--property=ReadOnlyPaths=' + str(ROOT),
        '--property=ReadWritePaths=' + ' '.join(str(path) for path in
            (output / 'broker', output / 'file_receipts', ROOT / 'stream/inbox')),
        '--property=InaccessiblePaths=' + str(ROOT / 'readouts') + ' ' + str(HOST_ROOT / 'readouts')
            + ' -/localhome/local-rohing/.ssh -/localhome/local-rohing/.aws',
        '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'HOME=' + str(BASE), 'CUDA_VISIBLE_DEVICES=',
        'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + str(LIFE / 'toolsource2'),
        str(PYTHON), '-B', str(Path(__file__).resolve()), 'broker', '--output', str(output)]


def broker_dispatch(output):
    successor_gate(output)
    require((output / 'LAUNCH.json').is_file() and (output / 'CONTAINMENT_VERIFIED.json').is_file(),
            'native_launched_before_broker')
    (output / 'BROKER_DISPATCH_ONCE').mkdir()
    command = broker_command(output)
    with (output / 'BROKER.log').open('x') as log:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
    write(output / 'BROKER_DISPATCHED.json', dict(pid=process.pid, command=command, started_unix=time.time()))
    return dict(status='BROKER_DISPATCHED', pid=process.pid)


def future_request(request, response, committed):
    require(request is not None and response is not None, 'future_request_response_required')
    request = {key:value for key, value in request.items() if key != 'resume_state'}
    require(request['split'] == 'TRAIN' and response['request_sha256'] == digest(request)
            and committed['source_sha256'] == digest(response)
            and committed['segment'] == request['segment'], 'future_committed_TRAIN_hash_join')
    return response['response']['raw']


def reader_parent_resume_source(original_raw, spec_reference):
    import ast
    from gpu import orch_r157_community_service_keepalive as keepalive
    require(sha(Path(keepalive.__file__).resolve()) ==
            '2f039d47e91d71fe822943799e44cb7ae775f1a86772e157eadf6fb62dce05a7',
            'pinned_parent_resume_machinery')
    source = keepalive.programme_resume_source(original_raw, spec_reference)
    tree = ast.parse(source)
    guard = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == '_r157_guard')
    matches = [node for node in ast.walk(guard) if isinstance(node, ast.Compare)
               and ast.unparse(node.left) == "config['root']"
               and len(node.ops) == 1 and isinstance(node.ops[0], ast.In)]
    require(len(matches) == 1, 'single_parent_root_guard')
    matches[0].comparators = [ast.Tuple(elts=[ast.Constant(str(HOST_ROOT))], ctx=ast.Load())]
    guard.body.insert(0, ast.parse(
        "require(config['programme'] == 'repo_reader' and config['branch'] == "
        "'R136_repo_reader_seed0', 'exact_reader_parent_only')").body[0])
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + '\n'


def broker(output):
    namespace()
    config = read(output / 'BROKER_CONFIG.json')
    require(config['root'] == str(ROOT) and config['host_root'] == str(HOST_ROOT)
            and config['hard_end_unix'] == NEW_WALL and config['segment_id'] == SEGMENT
            and config['snapshot'] == str(LIFE / 'snapshot1')
            and config['manifest_sha256'] == SNAPSHOT_SHA and config['replay_past_reads'] is False
            and config['publish_initial_connection'] is False, 'same_snapshot_future_cursor_broker')
    snapshot_tools()
    from gpu.orch_r136_repo_reader import deliver, requests, verify
    from gpu.orch_r125_stream_console import _open_stream_directory, _read_record
    require(Path(sys.modules['gpu.orch_r136_repo_reader'].__file__).resolve()
            == LIFE / 'toolsource2/gpu/orch_r136_repo_reader.py', 'original_broker_source_import')
    verify(config['snapshot'], SNAPSHOT_SHA)
    directory = output / 'broker'
    (directory / 'BROKER_ONCE').mkdir()
    for minor in range(8):
        try:
            descriptor = os.open('/dev/nvidia' + str(minor), os.O_RDWR | os.O_CLOEXEC)
        except PermissionError:
            continue
        os.close(descriptor)
        raise ValueError('broker_GPU_not_denied')
    try:
        descriptor = os.open(ROOT / 'stream/JOURNAL.json', os.O_WRONLY | os.O_CLOEXEC)
    except OSError as error:
        require(error.errno in (13, 30), 'expected_history_write_denial')
    else:
        os.close(descriptor)
        raise ValueError('broker_history_not_readonly')
    write(directory / 'SANDBOX_VERIFIED.json', dict(all_GPUs_denied=True, history_write_denied=True,
        snapshot_sha256=SNAPSHOT_SHA, checked_unix=time.time()))
    index, previous = config['start_index'], config['previous_sha256']
    pending = deepcopy(config['inherited_pending'])
    request = response = response_index = None
    write(directory / 'STARTED.json', dict(pid=os.getpid(), start_index=index, previous_sha256=previous,
        hard_end_unix=NEW_WALL, segment_id=SEGMENT, inherited_pending=pending,
        initial_connection_republished=False, historical_READs_replayed=False, started_unix=time.time()))
    while time.time() < NEW_WALL:
        with _open_stream_directory(config['root'], 'records') as (descriptor, unused):
            record = _read_record(descriptor, index)
        if record is None:
            time.sleep(1)
            continue
        require(record['previous_sha256'] == previous and record['journal_id'] == config['journal_id'],
                'future_broker_chain')
        if record['kind'] == 'REQUEST':
            request = record['document']
        elif record['kind'] == 'RESPONSE':
            response, response_index = record['document'], index
        elif record['kind'] == 'COMMITTED' and response is not None:
            text = future_request(request, response, record['document'])
            try:
                names = requests(text)
            except ValueError:
                write(directory / f'REJECTED_{response_index:020d}.json', dict(reason='invalid_read_request'))
                names = []
            for name in names:
                key = f'{response_index:020d}_' + hashlib.sha256(name.encode()).hexdigest()[:12]
                provenance = dict(actor='child', split='TRAIN', record_index=response_index,
                                  source_sha256=digest(response), segment_id=SEGMENT)
                write(directory / ('INTENT_' + key + '.json'), dict(request=provenance, file=name))
                receipt = deliver(config['root'], config['snapshot'], SNAPSHOT_SHA, name, config['receipts'], provenance)
                write(directory / ('READ_' + key + '.json'), receipt)
                pending[receipt['publication']['id']] = key
            request = response = response_index = None
        elif record['kind'] == 'INBOX':
            identifier = record['document']['message']['id']
            if identifier in pending:
                key = pending.pop(identifier)
                write(directory / ('CONSUMED_' + key + '.json'), dict(inbox_id=identifier,
                    record_index=index, record_sha256=record['sha256']))
        write(directory / f'CURSOR_{index:020d}.json', dict(index=index, record_sha256=record['sha256'],
                                                          next_index=index + 1, observed_unix=time.time()))
        previous, index = record['sha256'], index + 1
    write(directory / 'EXIT.json', dict(reason='authorized_runtime_wall', finished_unix=time.time()))


def readmit(prior, output, cpu_path):
    namespace()
    cpu_gate(cpu_path)
    prior = output_scope(prior)
    require(not (prior / 'LAUNCH.json').exists() and not (prior / 'CONTAINMENT_VERIFIED.json').exists(),
            'readmit_only_failed_before_native_launch')
    prior_request = read(prior / 'REQUEST.json')
    for key in ('authority', 'conflict', 'operator', 'cpu'):
        require(sha(prior_request[key]['path']) == prior_request[key]['sha256'], 'prior_receipt_preserved:' + key)
    authority(prior_request['authority']['path'])
    conflict_check(prior_request['conflict']['path'])
    retired = read(prior / 'RETIRED.json')
    require(retired['boundary'] == ref(prior / 'BOUNDARY.json'), 'prior_actual_retirement_proof')
    prior_config = read(prior / 'GUARD.json')
    unit = prior_config['device_containment']['unit']
    require(unit.startswith('orch-r136-native-') and len(unit.removeprefix('orch-r136-native-')) == 32,
            'prior_owned_native_unit')
    raw = subprocess.check_output(['systemctl', 'show', unit + '.service', '-p', 'MainPID',
                                  '-p', 'ActiveState', '-p', 'ExecMainStatus'], text=True, timeout=10)
    state = dict(line.split('=', 1) for line in raw.splitlines() if '=' in line)
    require(state.get('MainPID') == '0' and state.get('ActiveState') == 'failed'
            and state.get('ExecMainStatus') not in (None, '0'), 'prior_service_failed_no_process')
    config, plan, original = original_modules()
    api = load_api('BOUNDARY_API.py', API_SHA)
    saved = api.sleep_boundary(ROOT)
    expected = read(prior / 'BOUNDARY.json')['saved']
    require(saved is not None and saved['state_sha256'] == expected['state_sha256']
            and sha(saved['path']) == expected['record_sha256'], 'unchanged_stopped_saved_boundary')
    evidence = api.saved_evidence(plan, saved, original)
    require(evidence == expected, 'full_saved_bundle_unchanged_after_failed_start')
    output = output_scope(output)
    output.mkdir(mode=0o700)
    for name in ('broker', 'file_receipts'):
        (output / name).mkdir(mode=0o700)
    request = deepcopy(prior_request)
    request.update(cpu=ref(cpu_path), operator=ref(Path(__file__).resolve()),
        prior_request=ref(prior / 'REQUEST.json'), readmitted_unix=time.time(),
        prior_failed_service=state, no_repeat_retirement=True)
    write(output / 'REQUEST.json', request)
    shutil.copyfile(prior / 'LEASE_BUDGET.json', output / 'LEASE_BUDGET.json')
    shutil.copyfile(prior / 'BOUNDARY.json', output / 'BOUNDARY.json')
    stage_boundary(output, saved, original, config, plan, evidence)
    broker = read(prior / 'BROKER_CONFIG.json')
    broker.update(output=str(output / 'broker'), receipts=str(output / 'file_receipts'))
    write(output / 'BROKER_CONFIG.json', broker)
    write(output / 'RETIRED.json', dict(status='PRIOR_ACTUAL_RETIREMENT_REUSED_NO_SIGNAL',
        boundary=ref(output / 'BOUNDARY.json'), original_retirement=ref(prior / 'RETIRED.json'),
        prior_failed_service=state, derived_unix=time.time()))
    return dict(status='READMIT_PREPARED_NO_SIGNAL', output=str(output), cycle=saved['cycle'],
                optimizer_steps=evidence['optimizer_steps'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'readmit', 'handoff', 'launch', 'contained', 'broker-dispatch', 'broker', 'watchdog'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--prior', type=Path)
    parser.add_argument('--authority', type=Path)
    parser.add_argument('--cpu', type=Path)
    parser.add_argument('--conflict', type=Path)
    parser.add_argument('--seconds', type=int, default=3600)
    parser.add_argument('--pipe', type=int)
    parser.add_argument('--fds', type=int, nargs='+')
    arguments = parser.parse_args()
    if arguments.action == 'watchdog':
        watchdog(arguments.fds, arguments.pipe, arguments.seconds)
        return
    output = output_scope(arguments.output)
    if arguments.action == 'prepare':
        result = prepare(output, arguments.authority, arguments.cpu, arguments.conflict)
    elif arguments.action == 'readmit':
        result = readmit(arguments.prior, output, arguments.cpu)
    elif arguments.action == 'handoff':
        result = handoff(output, arguments.seconds)
    else:
        result = {'launch':launch, 'contained':contained, 'broker-dispatch':broker_dispatch,
                  'broker':broker}[arguments.action](output)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
