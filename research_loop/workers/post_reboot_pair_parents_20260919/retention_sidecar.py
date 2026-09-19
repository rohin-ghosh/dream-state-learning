"""Explicit CPU-only fence/rebind operations around the unchanged parent source."""

import argparse
from contextlib import contextmanager
from copy import deepcopy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import stat
import subprocess
import sys
import time

import parent_service as service
from retention_sidecar_remote import digest, require


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CEILING = 1790791200
IDENTITY_KEYS = ('pid', 'start_ticks', 'boot_id', 'uid', 'argv', 'cwd')


def file_bytes(path, durable=False):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, 'literal_absolute_file')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as handle:
        before = os.fstat(handle.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= 128 * 1024**2, 'bounded_regular_file')
        content = handle.read()
        if durable:
            os.fsync(handle.fileno())
        after = os.fstat(handle.fileno())
    current = path.stat(follow_symlinks=False)
    identity = lambda entry: (entry.st_dev, entry.st_ino, entry.st_size, entry.st_mtime_ns, entry.st_ctime_ns)
    require(identity(before) == identity(after) == identity(current), 'file_changed_during_read')
    return content


def sha(path):
    return hashlib.sha256(file_bytes(path)).hexdigest()


def read(path):
    return json.loads(file_bytes(path))


def content(document):
    return (json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_once(path, document):
    path = Path(path)
    require(path.parent.resolve() == path.parent, 'literal_receipt_directory')
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as handle:
        handle.write(content(document))
        handle.flush()
        os.fsync(handle.fileno())
    sync_directory(path.parent)


def pinned(reference):
    payload = file_bytes(reference['path'])
    require(hashlib.sha256(payload).hexdigest() == reference['sha256'], 'pinned_receipt_changed')
    return json.loads(payload)


def pins_match(pins):
    require(pins and all(sha(path) == expected for path, expected in pins.items()), 'pinned_source_or_ledger_changed')


def process_identity(process_id):
    process = Path('/proc') / str(process_id)
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=process_id, start_ticks=fields[19], state=fields[0], uid=process.stat().st_uid,
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        argv=(process / 'cmdline').read_bytes().decode().rstrip('\0').split('\0'),
        cwd=str((process / 'cwd').resolve()))


def lock_owners(path):
    identity = Path(path).stat()
    expected = (os.major(identity.st_dev), os.minor(identity.st_dev), identity.st_ino)
    owners = []
    for line in Path('/proc/locks').read_text().splitlines():
        fields = line.split()
        if len(fields) < 8 or fields[1:4] != ['FLOCK', 'ADVISORY', 'WRITE']:
            continue
        device = fields[5].split(':')
        if len(device) == 3 and (int(device[0], 16), int(device[1], 16), int(device[2])) == expected:
            owners.append(int(fields[4]))
    return owners


class LinuxCPU:
    def check(self, expected, lock, stopped=False):
        current = process_identity(expected['pid'])
        require(all(current[key] == expected[key] for key in IDENTITY_KEYS), 'exact_CPU_identity_required')
        require(current['state'] in ('T', 't') if stopped else current['state'] not in ('T', 't', 'Z', 'X'),
            'exact_CPU_stop_state_required')
        require(lock_owners(lock) == [expected['pid']], 'exact_CPU_sole_publisher_lock_owner')
        require(len(list((Path('/proc') / str(expected['pid']) / 'task').iterdir())) == 1, 'single_CPU_thread_required')
        for process in Path('/proc').iterdir():
            if not process.name.isdigit():
                continue
            try:
                fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue
            require(int(fields[1]) != expected['pid'] or fields[0] in ('Z', 'X'), 'CPU_subprocess_inflight')

    def signal_exact(self, expected, lock, operation):
        require(operation in (signal.SIGSTOP, signal.SIGKILL), 'CPU_stop_or_retire_only')
        descriptor = os.pidfd_open(expected['pid'])
        try:
            self.check(expected, lock, stopped=operation == signal.SIGKILL)
            signal.pidfd_send_signal(descriptor, operation)
        finally:
            os.close(descriptor)

    def wait_stopped(self, expected, lock):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if process_identity(expected['pid'])['state'] in ('T', 't'):
                self.check(expected, lock, stopped=True)
                return
            time.sleep(.05)
        raise ValueError('CPU_stop_timeout_no_automatic_resume')

    def wait_exited(self, expected):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                current = process_identity(expected['pid'])
                if current['start_ticks'] != expected['start_ticks'] or current['state'] in ('Z', 'X'):
                    return
            except (FileNotFoundError, ProcessLookupError):
                return
            time.sleep(.05)
        raise ValueError('CPU_exit_timeout_no_duplicate_start')


def registry_disabled(plan):
    manifest = pinned(plan['disabled_registry'])
    require(manifest['enabled'] is False and manifest['name'] == 'pair-curriculum-' + plan['arm']
        and manifest['argv'] == plan['old_parent']['argv'] and manifest['until_unix'] == CEILING
        and str((REPO / manifest['singleton_lock']).resolve()) == plan['lock'], 'exact_owner_disabled_registry_required')


def validate_plan(plan, active=False):
    require(plan['schema'] == 'PAIR_PARENT_FENCE_PLAN_V1' and plan['arm'] in ('learner', 'frozen'), 'fence_plan_schema')
    require(re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', plan['transaction_id']) is not None, 'bounded_transaction_id')
    require(plan['directory'] == str(HERE / 'private' / plan['arm']) and
        plan['lock'] == str(Path(plan['directory']) / 'PUBLISHER.lock'), 'exact_existing_parent_directory')
    require(plan['transaction_dir'] == str(HERE / 'retention_transactions' / plan['transaction_id']), 'scoped_transaction_directory')
    require(plan['until_unix'] == CEILING == plan['life_binding']['hard_end_unix'], 'unchanged_parent_deadline')
    require(plan['owner'] and 0 < plan['not_after_unix'] - plan['created_unix'] <= 600
        and plan['not_after_unix'] <= CEILING, 'bounded_ten_minute_activation_window')
    if active:
        require(plan['created_unix'] <= time.time() < plan['not_after_unix'], 'activation_window_expired')
    original = pinned(plan['old_process_receipt'])
    for key in ('pid', 'start_ticks', 'boot_id', 'argv', 'cwd'):
        require(original[key] == plan['old_parent'][key], 'original_parent_process_receipt')
    require(plan['old_parent']['argv'] == ['/usr/bin/python3', '-B', str(HERE / 'parent_service.py'), '--arm', plan['arm']]
        and plan['old_parent']['cwd'] == str(REPO), 'only_legacy_CPU_parent_can_be_fenced')
    require(plan['old_parent']['pid'] not in (493500, 471737, plan['life_binding']['pid']), 'never_signal_a_native')
    require({key: value for key, value in plan['old_native'].items() if key != 'uid'} == original['native'],
        'unchanged_old_native_binding')
    boundary = plan['life_binding']
    require(all(boundary[key] == plan['old_native'][key] for key in ('pid', 'start_ticks', 'boot_id', 'uid', 'journal_id'))
        and boundary['journal_root'] == plan['old_native']['root'] + '/raw/stream'
        and boundary['command'] == plan['old_native']['argv'], 'same_exact_boundary_life')
    require(all(plan['source_pins'].get(path) == expected for path, expected in original['sources'].items()), 'same_source_successor_only')
    required = [HERE / name for name in ('retention_sidecar.py', 'retention_sidecar_remote.py', 'remote_io.py', 'parent_service.py')]
    require(all(str(path) in plan['source_pins'] for path in required), 'sidecar_and_original_source_pins_required')
    require(plan['transport_source_path'] == str(HERE / 'remote_io.py'), 'original_transport_only')
    pins_match(plan['source_pins'])
    require(str(Path(plan['old_native']['root']) / 'parent_io.py') in plan['remote_transport_pins'], 'original_remote_transport_pin_required')
    return plan


def ledger_pins(directory, durable=False):
    directory = Path(directory)
    paths = sorted(directory.rglob('*'))
    require(len(paths) <= 10000, 'bounded_parent_ledger_inventory')
    result = {}
    for path in paths:
        require(not path.is_symlink(), 'ledger_symlink_forbidden')
        require(not path.name.endswith('.partial'), 'partial_ledger_write_requires_operator')
        if path.is_file() and path.name != 'PUBLISHER.lock' and path.suffix != '.log':
            result[str(path)] = hashlib.sha256(file_bytes(path, durable=durable)).hexdigest()
    require(str(directory / 'STATE.json') in result, 'existing_STATE_required_no_seed')
    if durable:
        for parent in sorted({Path(path).parent for path in result}, key=str):
            sync_directory(parent)
    return result


def drained(plan, expected_sha=None):
    directory = Path(plan['directory'])
    state_path = directory / 'STATE.json'
    if expected_sha is not None:
        require(sha(state_path) == expected_sha, 'parent_state_changed_not_drained')
    state = read(state_path)
    require(state['native'] == {key: value for key, value in plan['old_native'].items() if key != 'uid'}, 'old_ledger_native_binding')
    for field in ('pending_turn', 'provider_inflight', 'provider_blocked', 'publication_blocked', 'transport_blocked'):
        require(field in state and state[field] is None, 'unresolved_' + field)
    require(state['first_turn'] is False and not service.turn_due(state), 'parent_not_idle_or_opening_replay')
    require(type(state['next_index']) is int and state['next_index'] > 0 and state['previous_sha256'], 'preserved_cursor_required')
    return state, delivery_inventory(state, directory, strict=True)


def delivery_inventory(state, directory, strict=False):
    directory = Path(directory)
    deliveries = []
    delivered_directories = set()
    identifiers = set()
    for delivery in state['deliveries']:
        turn = Path(delivery['directory'])
        require(turn.parent == directory and turn.is_dir(), 'existing_delivery_directory')
        require(read(turn / 'PUBLICATION.json') == delivery['receipt'], 'publication_not_committed_in_ledger')
        result = read(turn / 'RESULT.json')
        require(result['response']['message'] == delivery['text'], 'same_result_text')
        identifier = sha(turn / 'RESULT.json')
        require(identifier not in identifiers, 'duplicate_existing_delivery_id')
        identifiers.add(identifier)
        deliveries.append(dict(delivery_id=identifier, receipt=delivery['receipt'],
            text_sha256=hashlib.sha256(delivery['text'].encode()).hexdigest(),
            provider_response_sha256=sha(turn / 'stdout.json')))
        delivered_directories.add(turn)
    for turn in directory.glob('turn_*') if strict else []:
        if turn in delivered_directories:
            continue
        require(not (turn / 'PUBLICATION.json').exists() and not (turn / 'RESULT.json').exists(), 'orphan_result_or_publication')
        if (turn / 'DISPATCH.json').exists():
            disposition = read(turn / 'FAILURE_DISPOSITION.json')
            error = read(turn / 'http_error_response.txt')
            require(disposition['explicit_429'] is True and str(error.get('error', {}).get('code')) == '429',
                'unknown_provider_attempt_no_replay')
    return deliveries


class Remote:
    def __call__(self, plan, action, state=None, deliveries=None, approval=None, dependency_sha256=None, request=None):
        envelope = dict(plan=plan, request=request or dict(action=action))
        if state is not None:
            envelope.update(cursor={key: state[key] for key in ('next_index', 'previous_sha256')}, deliveries=deliveries)
        if approval is not None:
            envelope.update(approval=approval, dependency_sha256=dependency_sha256,
                transport_source=file_bytes(HERE / 'remote_io.py').decode())
        command = 'PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= /localhome/local-rohing/v2/venv/bin/python -B -c ' + \
            shlex.quote(file_bytes(HERE / 'retention_sidecar_remote.py').decode())
        child = subprocess.run(['bash', str(REPO / 'gpu/ovx4_ssh.sh'), command], input=json.dumps(envelope),
            text=True, capture_output=True, timeout=90)
        if child.returncode == 2:
            raise service.BindingError('remote_receipt_or_identity_refused')
        require(child.returncode == 0, 'remote_refusal_or_unknown_outcome_no_redispatch')
        return json.loads(child.stdout)


def fence(plan, cpu, remote):
    validate_plan(plan, active=True)
    registry_disabled(plan)
    directory = Path(plan['transaction_dir'])
    require(not (directory / 'FENCE_CLAIM.json').exists(), 'fence_claim_exists_reconcile_no_retry')
    cpu.check(plan['old_parent'], plan['lock'])
    state, deliveries = drained(plan, plan['state_sha256'])
    status = read(Path(plan['directory']) / 'STATUS.json')
    require(status['health'] == 'OBSERVING' and status['caught_up'] is True
        and 0 <= time.time() - status['observed_unix'] <= 10, 'fresh_idle_caught_up_parent_required')
    remote(plan, 'fence_check', state, deliveries)
    validate_plan(plan, active=True)
    registry_disabled(plan)
    cpu.check(plan['old_parent'], plan['lock'])
    drained(plan, plan['state_sha256'])
    write_once(directory / 'FENCE_CLAIM.json', dict(plan_sha256=digest(plan), attempted_unix=time.time(),
        old_parent=plan['old_parent'], automatic_resume=False, native_signals=0))
    try:
        cpu.signal_exact(plan['old_parent'], plan['lock'], signal.SIGSTOP)
        cpu.wait_stopped(plan['old_parent'], plan['lock'])
        state, deliveries = drained(plan, plan['state_sha256'])
        pins = ledger_pins(plan['directory'], durable=True)
        remote(plan, 'fence_check', state, deliveries)
        cpu.check(plan['old_parent'], plan['lock'], stopped=True)
        registry_disabled(plan)
        pins_match(pins)
        validate_plan(plan, active=True)
        write_once(directory / 'STATE_BEFORE.json', state)
        receipt = dict(schema='PAIR_RETENTION_PARENT_DEPENDENCIES_V1', life_binding_sha256=digest(plan['life_binding']),
            source_epoch=plan['source_epoch'], owner=plan['owner'], delivery_fenced=True, inflight_deliveries=0,
            durable=True, preserve_existing_ledgers=True, automatic_pid_adoption=False, replay_delivered_messages=False,
            ledger_pins=pins, old_parent=plan['old_parent'], plan_sha256=digest(plan), transaction_id=plan['transaction_id'],
            fence_kind='EXACT_PIDFD_STOP_OLD_CPU_RETAINS_PUBLISHER_LOCK', native_signals=0, observed_unix=time.time())
        write_once(directory / 'PARENT_DEPENDENCIES.json', receipt)
        return receipt
    except Exception as error:
        write_once(directory / 'FENCE_BLOCKED.json', dict(reason=type(error).__name__ + ':' + str(error),
            old_CPU_may_remain_stopped=True, automatic_resume=False, dependency_proof_issued=False, native_signals=0))
        raise


@contextmanager
def publisher_lock(path):
    descriptor = os.open(path, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield descriptor
    finally:
        os.close(descriptor)


def validate_approval(plan, approval, dependency):
    require(approval['schema'] == 'PAIR_PARENT_POST_LOADED_APPROVAL_V1'
        and approval['transaction_id'] == plan['transaction_id'] and approval['plan_sha256'] == digest(plan)
        and approval['dependency_sha256'] == sha(Path(plan['transaction_dir']) / 'PARENT_DEPENDENCIES.json'), 'exact_rebind_approval')
    require(approval['owner'] == plan['owner'] and approval['source_epoch'] == plan['source_epoch']
        and approval['until_unix'] == CEILING, 'same_rebind_owner_epoch_deadline')
    require(0 < approval['not_after_unix'] - approval['created_unix'] <= 600
        and approval['created_unix'] <= time.time() < approval['not_after_unix'] <= CEILING, 'bounded_rebind_window')
    require(dependency['plan_sha256'] == digest(plan) and dependency['delivery_fenced'] is True
        and dependency['inflight_deliveries'] == 0 and dependency['ledger_pins'], 'actual_fence_dependency_required')
    gate = pinned(approval['checkpoint_gate_receipt'])
    require(approval['checkpoint_gate_passed'] is True and isinstance(gate, dict), 'main_checkpoint_gate_required')
    require(approval['guard_path'] in approval['receiver_pins'] and approval['new_native']['uid'] == plan['life_binding']['uid'],
        'exact_receiver_guard_and_uid')


def rebind(plan, approval, cpu, remote):
    validate_plan(plan)
    registry_disabled(plan)
    directory = Path(plan['transaction_dir'])
    dependency = read(directory / 'PARENT_DEPENDENCIES.json')
    validate_approval(plan, approval, dependency)
    require(not (directory / 'REBIND_CLAIM.json').exists(), 'rebind_claim_exists_reconcile_no_retry')
    cpu.check(plan['old_parent'], plan['lock'], stopped=True)
    pins_match(dependency['ledger_pins'])
    require(ledger_pins(plan['directory']) == dependency['ledger_pins'], 'ledger_inventory_changed_while_fenced')
    state, deliveries = drained(plan, plan['state_sha256'])
    remote(plan, 'rebind_check', state, deliveries, approval, approval['dependency_sha256'])
    validate_approval(plan, approval, dependency)
    registry_disabled(plan)
    write_once(directory / 'REBIND_CLAIM.json', dict(approval_sha256=digest(approval), old_parent=plan['old_parent'],
        observed_unix=time.time(), automatic_retry=False, native_signals=0))
    try:
        cpu.signal_exact(plan['old_parent'], plan['lock'], signal.SIGKILL)
        cpu.wait_exited(plan['old_parent'])
        with publisher_lock(plan['lock']):
            pins_match(dependency['ledger_pins'])
            remote(plan, 'rebind_check', state, deliveries, approval, approval['dependency_sha256'])
            validate_approval(plan, approval, dependency)
            registry_disabled(plan)
            carried = rebound_state(state, approval['new_native'])
            write_once(directory / 'REBIND_PREPARED.json', dict(plan=plan, approval=approval,
                before_state_sha256=plan['state_sha256'], after_state_sha256=hashlib.sha256(content(carried)).hexdigest(),
                sole_change='STATE.native', native_signals=0))
            temporary = Path(plan['directory']) / 'STATE.retention.partial'
            write_once(temporary, carried)
            os.replace(temporary, Path(plan['directory']) / 'STATE.json')
            sync_directory(plan['directory'])
            receipt = dict(schema='PAIR_PARENT_REBIND_COMMITTED_V1', plan=plan, approval=approval,
                before_ledger_pins=dependency['ledger_pins'], after_state_sha256=sha(Path(plan['directory']) / 'STATE.json'),
                successor_source_pins=plan['source_pins'], observed_unix=time.time(),
                old_CPU_retired=True, successor_started=False, native_signals=0, duplicate_sends=0)
            write_once(directory / 'REBIND_RECEIPT.json', receipt)
            return receipt
    except Exception as error:
        write_once(directory / 'REBIND_BLOCKED.json', dict(reason=type(error).__name__ + ':' + str(error),
            old_CPU_may_be_retired=True, automatic_retry=False, native_signals=0))
        raise


def rebound_state(state, native):
    carried = deepcopy(state)
    carried['native'] = deepcopy(native)
    require({key: value for key, value in carried.items() if key != 'native'} ==
        {key: value for key, value in state.items() if key != 'native'}, 'only_native_binding_may_change')
    return carried


def verify_fence(dependency_path, dependency_hash, cpu):
    dependency = pinned(dict(path=str(dependency_path), sha256=dependency_hash))
    plan = read(Path(dependency_path).parent / 'PLAN.json')
    validate_plan(plan)
    require(time.time() < CEILING, 'existing_deadline_expired')
    require(Path(dependency_path) == Path(plan['transaction_dir']) / 'PARENT_DEPENDENCIES.json'
        and dependency['plan_sha256'] == digest(plan) and dependency['delivery_fenced'] is True,
        'exact_dependency_receipt_path_and_plan')
    require(not (Path(plan['transaction_dir']) / 'REBIND_CLAIM.json').exists(), 'fence_transfer_started_no_old_proof')
    registry_disabled(plan)
    cpu.check(plan['old_parent'], plan['lock'], stopped=True)
    require(ledger_pins(plan['directory'], durable=True) == dependency['ledger_pins'], 'complete_dependency_ledger_inventory')
    drained(plan, plan['state_sha256'])
    return dict(schema='PAIR_PARENT_FENCE_RECHECK_V1', dependency_path=str(dependency_path),
        dependency_sha256=dependency_hash, life_binding_sha256=dependency['life_binding_sha256'],
        source_epoch=dependency['source_epoch'], old_parent=plan['old_parent'],
        delivery_fenced=True, inflight_deliveries=0, ledger_pins_verified=True, observed_unix=time.time(), native_signals=0)


def guarded_publication(plan, approval, request, remote):
    identifier = request['delivery_id']
    require(re.fullmatch(r'[0-9a-f]{64}', identifier) is not None, 'exact_RESULT_delivery_id')
    directory = Path(plan['transaction_dir']) / 'publication_attempts'
    directory.mkdir(mode=0o700, exist_ok=True)
    require(directory.resolve() == directory, 'literal_publication_attempt_directory')
    sync_directory(directory.parent)
    dispatch = directory / (identifier + '.dispatch.json')
    acknowledgement = directory / (identifier + '.ack.json')
    intent = dict(request_sha256=digest(request), native=approval['new_native'], delivery_id=identifier)
    if dispatch.exists():
        require(read(dispatch) == intent, 'publication_intent_changed')
        require(acknowledgement.exists(), 'unknown_sidecar_publication_outcome_no_retry')
        saved = read(acknowledgement)
        require(saved['intent'] == intent, 'publication_ack_identity')
        return saved['receipt']
    require(not acknowledgement.exists(), 'publication_ack_without_dispatch')
    write_once(dispatch, intent)
    receipt = remote(plan, 'publish', approval=approval, request=request)
    write_once(acknowledgement, dict(intent=intent, receipt=receipt))
    return receipt


def serve(receipt_path, receipt_hash, remote):
    receipt = pinned(dict(path=str(receipt_path), sha256=receipt_hash))
    require(receipt['schema'] == 'PAIR_PARENT_REBIND_COMMITTED_V1', 'committed_rebind_receipt_required')
    plan, approval = receipt['plan'], receipt['approval']
    validate_plan(plan)
    require(Path(receipt_path) == Path(plan['transaction_dir']) / 'REBIND_RECEIPT.json', 'exact_committed_receipt_path')
    require(time.time() < CEILING and receipt['successor_source_pins'] == plan['source_pins'], 'same_source_before_deadline')
    actual_argv = process_identity(os.getpid())['argv']
    registry = read(plan['disabled_registry']['path'])
    if registry['enabled']:
        require(registry['argv'] == actual_argv and registry['until_unix'] == CEILING
            and str((REPO / registry['singleton_lock']).resolve()) == plan['lock'], 'supervisor_must_target_exact_successor')
    else:
        registry_disabled(plan)
    original_remote, original_write = service.remote, service.write
    admitted = False

    def bound_remote(arm, request, native=None):
        nonlocal admitted
        require(arm == plan['arm'] and (native is None or native == approval['new_native']), 'receipt_bound_successor_only')
        pins_match(plan['source_pins'])
        if not admitted:
            require(request['action'] == 'bind' and lock_owners(plan['lock']) == [os.getpid()], 'successor_sole_lock_before_admission')
            state = read(Path(plan['directory']) / 'STATE.json')
            require(state['native'] == approval['new_native'] and state['first_turn'] is False, 'preserved_rebound_STATE_required')
            admission_path = Path(plan['transaction_dir']) / 'SUCCESSOR_ADMISSION.json'
            if not admission_path.exists():
                require(sha(Path(plan['directory']) / 'STATE.json') == receipt['after_state_sha256'], 'exact_first_successor_ledger')
            remote(plan, 'rebind_check', state, delivery_inventory(state, plan['directory']),
                approval, approval['dependency_sha256'])
            result = remote(plan, 'bind', approval=approval, request=request)
            if not admission_path.exists():
                write_once(admission_path, dict(rebind_receipt_sha256=receipt_hash, argv=actual_argv,
                    pid=os.getpid(), observed_unix=time.time(), preserved_ledger=True))
            else:
                require(read(admission_path)['rebind_receipt_sha256'] == receipt_hash, 'same_successor_admission_receipt')
            admitted = True
            return result
        if request['action'] == 'publish':
            return guarded_publication(plan, approval, request, remote)
        return remote(plan, request['action'], approval=approval, request=request)

    def receipt_write(path, document):
        if Path(path).name.startswith('PROCESS_'):
            document = dict(document, argv=actual_argv, rebind_receipt=dict(path=str(receipt_path), sha256=receipt_hash),
                successor_wrapper_source_pins=plan['source_pins'])
        return original_write(path, document)

    def fatal_remote(arm, request, native=None):
        try:
            return bound_remote(arm, request, native)
        except Exception as error:
            if request['action'] == 'publish':
                state_path = Path(plan['directory']) / 'STATE.json'
                state = read(state_path)
                state['publication_blocked'] = dict(reason='sidecar_publication_outcome_requires_read_only_reconciliation',
                    error_type=type(error).__name__, pending_turn=state.get('pending_turn'))
                service.save(state_path, state)
            if isinstance(error, (ValueError, service.BindingError)):
                raise service.BindingError('receipt_bound_IO_refused:' + str(error)) from error
            raise

    service.remote, service.write = fatal_remote, receipt_write
    try:
        service.run(plan['arm'])
    finally:
        service.remote, service.write = original_remote, original_write


def prepare(arguments):
    process_reference = dict(path=str(Path(arguments.process_receipt).resolve()), sha256=sha(Path(arguments.process_receipt).resolve()))
    process = pinned(process_reference)
    identity = process_identity(process['pid'])
    boundary = read(Path(arguments.life_binding).resolve())
    directory = HERE / 'private' / arguments.arm
    transaction = HERE / 'retention_transactions' / arguments.transaction_id
    require(re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', arguments.transaction_id) is not None, 'bounded_transaction_id')
    require(not transaction.exists(), 'transaction_already_exists')
    source_pins = dict(process['sources'])
    additional = [HERE / 'retention_sidecar.py', HERE / 'retention_sidecar_remote.py',
        service.ORIGINAL / 'birth_spec.py', service.ORIGINAL / 'BIRTH_SPEC_SOURCE.md',
        service.ORIGINAL / 'r232_pair/BIRTH_SPEC_R232.md', REPO / 'gpu/ovx4_ssh.sh']
    source_pins.update({str(path): sha(path) for path in additional})
    registry = Path(arguments.disabled_registry).resolve()
    plan = dict(schema='PAIR_PARENT_FENCE_PLAN_V1', arm=arguments.arm, transaction_id=arguments.transaction_id,
        owner=arguments.owner, directory=str(directory), lock=str(directory / 'PUBLISHER.lock'), transaction_dir=str(transaction),
        old_parent={key: identity[key] for key in IDENTITY_KEYS}, old_process_receipt=process_reference,
        old_native=dict(process['native'], uid=boundary['uid']), life_binding=boundary, source_epoch=arguments.source_epoch,
        state_sha256=sha(directory / 'STATE.json'), source_pins=source_pins, transport_source_path=str(HERE / 'remote_io.py'),
        remote_transport_pins=read(Path(arguments.transport_pins).resolve()),
        disabled_registry=dict(path=str(registry), sha256=sha(registry)),
        until_unix=CEILING, created_unix=time.time(), not_after_unix=arguments.not_after_unix)
    validate_plan(plan, active=True)
    registry_disabled(plan)
    LinuxCPU().check(plan['old_parent'], plan['lock'])
    drained(plan, plan['state_sha256'])
    transaction.mkdir(parents=True, mode=0o700)
    write_once(transaction / 'PLAN.json', plan)
    return dict(path=str(transaction / 'PLAN.json'), execute_sha256=sha(transaction / 'PLAN.json'), no_signals=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    planned = commands.add_parser('prepare', help='Read-only host checks and a new pinned plan; no signals or fence')
    for name in ('arm', 'transaction-id', 'process-receipt', 'life-binding', 'source-epoch', 'owner', 'transport-pins', 'disabled-registry'):
        planned.add_argument('--' + name, required=True)
    planned.add_argument('--not-after-unix', type=float, required=True)
    for name in ('fence', 'rebind', 'serve', 'verify-fence'):
        command = commands.add_parser(name)
        command.add_argument('--receipt' if name in ('serve', 'verify-fence') else '--plan', required=True)
        command.add_argument('--execute-sha256', required=True)
        if name == 'rebind':
            command.add_argument('--approval', required=True)
    arguments = parser.parse_args()
    os.umask(0o077)
    if arguments.command == 'prepare':
        result = prepare(arguments)
    elif arguments.command == 'serve':
        serve(Path(arguments.receipt).resolve(), arguments.execute_sha256, Remote())
        return
    elif arguments.command == 'verify-fence':
        result = verify_fence(Path(arguments.receipt).resolve(), arguments.execute_sha256, LinuxCPU())
    else:
        plan_path = Path(arguments.plan).resolve()
        plan = (pinned(dict(path=str(plan_path), sha256=arguments.execute_sha256))
            if arguments.command == 'fence' else read(plan_path))
        require(Path(arguments.plan).resolve() == Path(plan['transaction_dir']) / 'PLAN.json', 'exact_plan_path')
        if arguments.command == 'fence':
            result = fence(plan, LinuxCPU(), Remote())
        else:
            approval = pinned(dict(path=str(Path(arguments.approval).resolve()), sha256=arguments.execute_sha256))
            result = rebind(plan, approval, LinuxCPU(), Remote())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
