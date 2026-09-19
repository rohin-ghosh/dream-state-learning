"""Executable future C2-only registry/fence adapter; never runs on import."""

import os
from pathlib import Path
import select
import signal
import time

import common as core
from common import DEADLINE, IDENTITY, digest, file_bytes, literal, locked, pinned, pins_match, read, reference, require, sha, sync, write_once


def validate(plan, *, active=False, now=None):
    require(plan['schema'] == 'C2_OWNER_TRANSPORT_PLAN_V1' and plan['deadline_unix'] == DEADLINE,
        'explicit_C2_unchanged_deadline')
    require(plan['registry']['path'] == str(core.REGISTRY) and plan['owner_root'] == str(core.OWNER)
        and plan['old_life']['journal_root'] == core.ROOT + '/stream'
        and plan['old_life']['journal_id'] == core.JOURNAL and plan['old_life']['hard_end_unix'] == DEADLINE,
        'original_C2_only_no_P7_pair_or_native_scope')
    transaction = literal(plan['transaction_dir'])
    require(transaction.parent == core.HERE / 'transactions' and transaction.is_dir(), 'own_transaction_directory')
    require(type(plan['created_unix']) in (int, float) and type(plan['not_after_unix']) in (int, float)
        and 0 < plan['not_after_unix'] - plan['created_unix'] <= 600
        and plan['not_after_unix'] <= DEADLINE, 'bounded_explicit_owner_action_window')
    if active:
        current = time.time() if now is None else now
        require(plan['created_unix'] <= current < plan['not_after_unix'], 'owner_action_approval_expired')
    registry = pinned(plan['registry']) if not (transaction / 'DISABLED.json').exists() else read(transaction / 'ORIGINAL_REGISTRY.json')
    require(registry['name'] == 'c2-parent' and registry['kind'] == 'parent' and registry['child_native'] is False
        and registry['until_unix'] == DEADLINE and registry['singleton_lock'] == str(core.OWNER / 'C2_SERVICE.lock')
        and registry['entrypoint'] == str(core.OWNER / 'c2_service.py')
        and registry['argv'] == ['/usr/bin/python3', '-B', str(core.OWNER / 'c2_service.py')], 'original_C2_registry')
    manifest = pinned(plan['manifest'])
    config = read(manifest['config_path'])
    pins_match(manifest['local_source_sha256'])
    pins_match(plan['source_pins'])
    required = [core.OWNER / 'c2_service.py', core.OWNER / 'c2_restore.py', core.PREVIOUS / 'checkpoint_tail_parent_strong.py',
        core.PREVIOUS / 'c2_parent_continue.py', core.REPO / 'gpu/orch_r133_programme_parent.py',
        *sorted(core.HERE.glob('*.py'))]
    require(all(str(path) in plan['source_pins'] for path in required)
        and all(plan['source_pins'].get(path) == expected for path, expected in manifest['local_source_sha256'].items()),
        'original_and_adapter_source_closure_bound')
    remote = Path(plan['remote_adapter_directory'])
    require(remote.is_absolute() and '..' not in remote.parts
        and plan['remote_files'] == {str(remote / name): plan['source_pins'].get(str(core.HERE / name))
            for name in ('common.py', 'c2_owner_binding.py')}
        and all(plan['remote_files'].values()), 'same_exact_readonly_helpers_on_original_node')
    require(config['root'] == core.ROOT and config['hard_end_unix'] == DEADLINE
        and config['cadence_responses'] == 1 and config['cadence_label'] == 'PERSISTENT'
        and config.get('schedule_on', 'response') == 'response', 'unchanged_actual_C2_parent_policy')
    require(Path(plan['manifest']['path']).parent.parent == core.OWNER
        and Path(manifest['output']).parent == Path(plan['manifest']['path']).parent, 'actual_C2_owner_session')
    require(plan['locks'] == dict(service=str(core.OWNER / 'C2_SERVICE.lock'),
        controller=str(core.PREVIOUS / 'private/C2_WAIT_CONTROLLER.lock'), publisher=config['existing_parent_lock']),
        'all_three_original_C2_locks')
    service, publisher = plan['service'], plan['publisher']
    require(service['argv'] == registry['argv'] and service['cwd'] == publisher['cwd'] == str(core.REPO)
        and publisher['argv'] == ['/usr/bin/python3', '-B', str(core.PREVIOUS / 'checkpoint_tail_parent_strong.py'),
            '--manifest', plan['manifest']['path'], '--manifest-sha256', plan['manifest']['sha256']]
        and type(publisher['ppid']) is int and publisher['ppid'] > 0
        and publisher['uid'] == service['uid'], 'exact_owner_and_publisher_commands')
    require(registry['entrypoint_sha256'] == plan['source_pins'][registry['entrypoint']], 'registry_source_pin')
    started = read(Path(manifest['output']) / 'STARTED.json')
    require(started['pid'] == publisher['pid'] and started['config_sha256'] == sha(manifest['config_path']),
        'actual_started_publisher_manifest_binding')
    require(service['pid'] != publisher['pid'] and all(actor['pid'] > 1
        and actor['pid'] != plan['old_life']['pid'] and actor['uid'] != 2524 for actor in (service, publisher)),
        'only_CPU_owners_never_native')
    require(plan['lock_identities'] == {key: lock_identity(path) for key, path in plan['locks'].items()},
        'same_original_lock_objects')
    return manifest, config


def lock_identity(path):
    entry = literal(path).lstat()
    return dict(dev=entry.st_dev, ino=entry.st_ino, mode=entry.st_mode)


def authorize(plan, approval, operation):
    validate(plan, active=True)
    require(approval['schema'] == 'C2_OWNER_ACTION_APPROVAL_V1' and approval['plan_sha256'] == digest(plan)
        and approval['operation'] == operation and approval['deadline_unix'] == DEADLINE
        and approval['created_unix'] <= time.time() < approval['not_after_unix'] <= plan['not_after_unix'],
        'exact_Main_owner_operation_approval')


def inventory(plan):
    manifest, config = validate(plan)
    roots = []
    current = Path(manifest['output'])
    expected_started = None
    configurations = []
    seen = set()
    while current is not None:
        current = literal(current)
        require(current not in seen and len(roots) < 256, 'bounded_acyclic_ledger_ancestry')
        seen.add(current)
        started = read(current / 'STARTED.json')
        require(started['programme'] == config['programme'] and started['branch'] == config['branch'], 'same_parent_ancestry')
        if expected_started is not None:
            require(sha(current / 'STARTED.json') == expected_started, 'original_predecessor_STARTED_pin')
        configuration = plan['ancestry_configs'].get(str(current))
        require(configuration is not None and configuration['sha256'] == started['config_sha256'],
            'explicit_source_bound_ancestor_config')
        ancestor = pinned(configuration)
        configurations.append(Path(configuration['path']))
        roots.append(current)
        expected_started = ancestor.get('predecessor_started_sha256')
        current = Path(ancestor['predecessor_output']) if ancestor.get('predecessor_output') else None
    require(set(map(str, roots)) == set(plan['ancestry_configs']), 'exact_complete_ancestry_not_partial')
    files = {plan['manifest']['path'], manifest['config_path'], *map(str, configurations), *manifest['local_source_sha256']}
    reserved = config['start_after_response_count']
    publications = []
    for root in roots:
        for path in sorted(root.rglob('*')):
            require(not path.is_symlink() and not path.name.endswith(('.partial', '.tmp')), 'no_partial_or_symlink_ledger')
            if path.is_file():
                files.add(str(path))
            require(len(files) <= 100000, 'bounded_all_ledger_files')
        for directory in root.glob('parent_*'):
            require(directory.is_dir() and (directory / 'SOURCE.json').is_file()
                and (directory / 'DISPATCH_INTENT.json').is_file() and (directory / 'RESULT.json').is_file(),
                'provider_or_publication_pending_drain_required')
            source, intent, result = (read(directory / name) for name in ('SOURCE.json', 'DISPATCH_INTENT.json', 'RESULT.json'))
            require(intent['source_sha256'] == sha(directory / 'SOURCE.json')
                and result['source_response_count'] == source['response_count'], 'source_bound_provider_result')
            terminal_prepublication_failure = (result['status'] == 'MISSING'
                and result.get('error_code') == 'parent_call_or_delivery_failed'
                and type(result.get('started_unix')) in (int, float)
                and type(result.get('finished_unix')) in (int, float)
                and result['finished_unix'] >= result['started_unix']
                and 'sent_unix' not in result and 'inbox_publication' not in result)
            require(result['status'] in ('SILENT', 'PUBLISHED') or terminal_prepublication_failure,
                'ambiguous_provider_publication_requires_Main_reconciliation')
            if result['status'] == 'SILENT':
                require('sent_unix' not in result and 'inbox_publication' not in result,
                    'silent_result_cannot_hide_publication')
            reserved = max(reserved, source['response_count'])
            if result['status'] == 'PUBLISHED':
                require((directory / 'DELIVERED.json').is_file(), 'queued_publication_not_yet_consumed')
                delivered = read(directory / 'DELIVERED.json')
                require(delivered['status'] == 'COMPLETE' and delivered['result_sha256'] == sha(directory / 'RESULT.json')
                    and delivered['inbox_id'] == result['inbox_publication']['id'], 'exact_original_delivery_receipt')
                publications.append(dict(result=reference(directory / 'RESULT.json'), delivered=reference(directory / 'DELIVERED.json'),
                    publication=result['inbox_publication'], consumption=delivered['consumption']))
    return dict(ledger_pins={path: sha(path) for path in sorted(files)}, reserved_response_count=reserved,
        roots=list(map(str, roots)), publications=publications)


class LinuxCPU:
    def check(self, plan, role, *, stopped=False):
        expected = plan[role]
        actual = core.process_identity(expected['pid'])
        require(all(actual[key] == expected[key] for key in IDENTITY), 'exact_CPU_pid_start_UID_boot_argv_cwd')
        require(actual['state'] in ('T', 't') if stopped else actual['state'] not in ('T', 't', 'Z', 'X'), 'CPU_state')
        roles = ('service',) if role == 'service' else ('controller', 'publisher')
        for name in roles:
            require(core.lock_owners(plan['locks'][name]) == [expected['pid']], 'sole_original_lock_owner')
        require(len(list((Path('/proc') / str(expected['pid']) / 'task').iterdir())) == 1, 'single_CPU_thread')
        children = []
        for path in Path('/proc').iterdir():
            if path.name.isdigit():
                try:
                    child = core.process_identity(int(path.name))
                except (FileNotFoundError, ProcessLookupError, PermissionError):
                    continue
                if child['ppid'] == expected['pid'] and child['state'] not in ('Z', 'X'):
                    children.append(child['pid'])
        expected_children = [plan['publisher']['pid']] if role == 'service' and plan['publisher']['ppid'] == expected['pid'] else []
        require(sorted(children) == expected_children, 'no_provider_or_transport_subprocess')
        for descriptor in (Path('/proc') / str(expected['pid']) / 'fd').iterdir():
            try:
                require(not os.readlink(descriptor).startswith('/dev/nvidia'), 'CPU_owner_has_no_GPU_descriptor')
            except FileNotFoundError:
                continue
        require(plan['lock_identities'] == {key: lock_identity(path) for key, path in plan['locks'].items()}, 'original_lock_objects')

    def signal(self, plan, role, operation):
        require(role in ('service', 'publisher') and operation in ('stop', 'resume', 'retire'), 'CPU_only_operations')
        descriptor = os.pidfd_open(plan[role]['pid'])
        try:
            self.check(plan, role, stopped=operation != 'stop')
            require(not select.select([descriptor], [], [], 0)[0], 'exact_CPU_pidfd_alive')
            signal.pidfd_send_signal(descriptor, {'stop': signal.SIGSTOP, 'resume': signal.SIGCONT, 'retire': signal.SIGKILL}[operation])
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                if operation == 'retire' and select.select([descriptor], [], [], 0)[0]:
                    return
                if operation != 'retire':
                    current = core.process_identity(plan[role]['pid'])
                    require(all(current[key] == plan[role][key] for key in IDENTITY), 'same_CPU_after_signal')
                    if (current['state'] in ('T', 't')) == (operation == 'stop'):
                        require(current['state'] not in ('Z', 'X'), 'live_CPU_after_signal')
                        return
                time.sleep(.01)
            raise ValueError('C2_owner_CPU_signal_timeout_reconcile_no_retry')
        finally:
            os.close(descriptor)

    def recover(self, plan, role):
        require(role in ('service', 'publisher'), 'CPU_only_recovery')
        current = core.process_identity(plan[role]['pid'])
        require(all(current[key] == plan[role][key] for key in IDENTITY)
            and current['state'] not in ('Z', 'X'), 'same_live_CPU_for_recovery')
        if current['state'] in ('T', 't'):
            self.signal(plan, role, 'resume')
        current = core.process_identity(plan[role]['pid'])
        require(all(current[key] == plan[role][key] for key in IDENTITY)
            and current['state'] not in ('T', 't', 'Z', 'X'), 'same_CPU_verified_running_after_recovery')
        return True


def disabled(plan):
    receipt = read(Path(plan['transaction_dir']) / 'DISABLED.json')
    original = read(Path(plan['transaction_dir']) / 'ORIGINAL_REGISTRY.json')
    require(read(core.REGISTRY) == dict(original, enabled=False) and sha(core.REGISTRY) == receipt['registry_sha256'],
        'only_C2_registry_disabled_and_unchanged')


def replace_registry(expected, proposed):
    require(read(core.REGISTRY) == expected, 'registry_compare_and_swap_preimage')
    temporary = core.REGISTRY.with_name('.c2-parent.' + str(time.time_ns()) + '.tmp')
    write_once(temporary, proposed)
    require(read(core.REGISTRY) == expected, 'registry_changed_before_replace')
    os.replace(temporary, core.REGISTRY)
    sync(core.REGISTRY.parent)


def disable(plan, approval):
    authorize(plan, approval, 'disable')
    transaction = Path(plan['transaction_dir'])
    with locked(transaction / 'ACTION.lock', create=True):
        original = pinned(plan['registry'])
        require(original['enabled'] is True, 'disable_only_original_enabled_C2')
        write_once(transaction / 'DISABLE_CLAIM.json', dict(plan_sha256=digest(plan), approval=approval))
        write_once(transaction / 'ORIGINAL_REGISTRY.json', original)
        replace_registry(original, dict(original, enabled=False))
        return write_once(transaction / 'DISABLED.json', dict(registry_sha256=sha(core.REGISTRY), native_signals=0))


def fence(plan, approval, cpu, remote):
    authorize(plan, approval, 'fence')
    transaction = Path(plan['transaction_dir'])
    with locked(transaction / 'ACTION.lock', create=True):
        disabled(plan)
        before = inventory(plan)
        remote('drain', plan, before)
        cpu.check(plan, 'service')
        cpu.check(plan, 'publisher')
        write_once(transaction / 'FENCE_CLAIM.json', dict(plan_sha256=digest(plan), approval=approval, before=before))
        attempted = []
        try:
            for role in ('service', 'publisher'):
                attempted.append(role)
                cpu.signal(plan, role, 'stop')
            for role in attempted:
                cpu.check(plan, role, stopped=True)
            after = inventory(plan)
            require(after == before, 'owner_raced_during_idle_fence_resume_same_CPUs')
            disabled(plan)
            remote('drain', plan, after)
            receipt = dict(schema='C2_OWNER_FENCE_RECEIPT_V1', plan_sha256=digest(plan),
                plan_path=str(transaction / 'PLAN.json'), life_binding_sha256=digest(plan['old_life']),
                source_epoch=plan['source_epoch'], service=plan['service'], publisher=plan['publisher'],
                locks=plan['locks'], inventory=after, registry_sha256=sha(core.REGISTRY),
                delivery_fenced=True, inflight_deliveries=0, native_signals=0, observed_unix=time.time())
            return write_once(transaction / 'DEPENDENCY.json', receipt)
        except BaseException as error:
            recovered, uncertain = [], {}
            for role in reversed(attempted):
                try:
                    require(cpu.recover(plan, role) is True, 'verified_CPU_recovery_required')
                    recovered.append(role)
                except BaseException as recovery_error:
                    uncertain[role] = dict(error_type=type(recovery_error).__name__, detail=str(recovery_error)[:500])
            write_once(transaction / 'FENCE_REFUSED.json', dict(same_CPU_owners_resumed=not uncertain,
                recovered_roles=recovered, uncertain_roles=uncertain, stop_attempted_roles=attempted,
                error_type=type(error).__name__, native_signals=0, retry_requires_new_Main_review=True))
            raise


def verify_fence(dependency, cpu):
    receipt = pinned(dependency)
    plan = read(receipt['plan_path'])
    validate(plan)
    require(receipt['schema'] == 'C2_OWNER_FENCE_RECEIPT_V1' and receipt['plan_sha256'] == digest(plan), 'exact_fence_plan')
    require(not (Path(plan['transaction_dir']) / 'REBIND_CLAIM.json').exists(), 'rebind_started_old_dependency_invalid')
    disabled(plan)
    for role in ('service', 'publisher'):
        cpu.check(plan, role, stopped=True)
    require(inventory(plan) == receipt['inventory'] and receipt['delivery_fenced'] is True
        and type(receipt['inflight_deliveries']) is int and receipt['inflight_deliveries'] == 0
        and receipt['native_signals'] == 0, 'same_drained_all_ledger_inventory')
    return dict(schema='C2_OWNER_FENCE_RECHECK_V1', dependency=dependency, plan_sha256=digest(plan),
        life_binding_sha256=receipt['life_binding_sha256'], source_epoch=receipt['source_epoch'],
        delivery_fenced=True, inflight_deliveries=0, ledger_pins_verified=True,
        native_signals=0, observed_unix=time.time())
