"""Same C2 parent policy, with explicit post-LOADED verifier and retained ancestry."""

import os
import hashlib
from pathlib import Path
import subprocess
import sys
import time
import types

import common as core
from common import DEADLINE, digest, locked, pinned, pins_match, read, reference, require, sha, write_once


CONFIG_DELTA = {'native_binding_path', 'native_binding_sha256', 'predecessor_output',
    'predecessor_started_sha256', 'start_after_response_count'}


def ported_parent_source(plan):
    original_path = core.PREVIOUS / 'checkpoint_tail_parent_strong.py'
    original = core.file_bytes(original_path)
    require(hashlib.sha256(original).hexdigest() == plan['source_pins'][str(original_path)],
        'pinned_original_parent_loop')
    before = b'from checkpoint_tail_parent_binding import verify;verify('
    require(original.count(before) == 1, 'one_exact_remote_binding_import_seam')
    return original.replace(before, b'from c2_owner_binding import verify;verify(', 1)


def validate_successor_manifest(plan, rebound, manifest_reference):
    require(rebound['schema'] == 'C2_OWNER_REBOUND_V1' and rebound['plan'] == plan
        and rebound['native_signals'] == 0, 'same_explicit_committed_rebind')
    manifest = pinned(manifest_reference)
    directory = core.literal(manifest_reference['path']).parent
    transaction = core.literal(plan['transaction_dir'])
    require(directory.parent == transaction and directory.name.startswith('session_')
        and manifest_reference['path'] == str(directory / 'MANIFEST.json')
        and manifest['config_path'] == str(directory / 'CONFIG.json')
        and manifest['output'] == str(directory / 'parent'), 'own_append_only_successor_session')
    original = pinned(plan['manifest'])
    prior_config = core.literal(manifest['predecessor_config_path'])
    if str(prior_config) == original['config_path']:
        previous = original
    else:
        require(prior_config.parent.parent == transaction and prior_config.parent.name.startswith('session_'),
            'only_original_or_own_predecessor')
        previous = read(prior_config.parent / 'MANIFEST.json')
    require(previous['config_path'] == str(prior_config), 'exact_predecessor_configuration')
    config = read(manifest['config_path'])
    sources = dict(previous['local_source_sha256'], **plan['source_pins'],
        **{manifest['config_path']: sha(manifest['config_path'])})
    expected = dict(previous, config_path=manifest['config_path'], predecessor_config_path=str(prior_config),
        output=manifest['output'], local_source_sha256=sources, remote_operator=plan['remote_adapter_directory'],
        remote_helper_sha256=dict(previous['remote_helper_sha256'], **plan['remote_files']),
        status='C2_EXPLICIT_POST_LOADED_RETENTION_OWNER_SAME_POLICY')
    require(manifest == expected, 'same_parent_manifest_except_exact_owner_relocations')
    pins_match(manifest['local_source_sha256'])
    previous_config = read(prior_config)
    require({key: value for key, value in config.items() if key not in CONFIG_DELTA}
        == {key: value for key, value in previous_config.items() if key not in CONFIG_DELTA}, 'unchanged_parent_treatment')
    require(config['native_binding_path'] == rebound['successor_binding']['path']
        and config['native_binding_sha256'] == rebound['successor_binding']['sha256']
        and config['predecessor_output'] == previous['output']
        and config['predecessor_started_sha256'] == sha(Path(previous['output']) / 'STARTED.json')
        and config['start_after_response_count'] >= max([previous_config['start_after_response_count'],
            rebound['old_inventory']['reserved_response_count']] +
            [read(path)['response_count'] for path in Path(previous['output']).glob('parent_*/SOURCE.json')]),
        'exact_rebound_native_full_ancestry_and_reserved_cursor')
    return manifest, config, previous_config


def next_manifest(plan, previous, previous_config, directory, binding, cursor):
    pins_match(previous['local_source_sha256'])
    old_output = Path(previous['output'])
    reserved = max([cursor, previous_config['start_after_response_count']] +
        [read(path)['response_count'] for path in old_output.glob('parent_*/SOURCE.json')])
    config = dict(previous_config, native_binding_path=binding['path'], native_binding_sha256=binding['sha256'],
        predecessor_output=str(old_output), predecessor_started_sha256=sha(old_output / 'STARTED.json'),
        start_after_response_count=reserved)
    require({key: value for key, value in config.items() if key not in CONFIG_DELTA}
        == {key: value for key, value in previous_config.items() if key not in CONFIG_DELTA}, 'same_parent_policy_only_binding_and_cursor')
    directory.mkdir(mode=0o700)
    config_reference = write_once(directory / 'CONFIG.json', config)
    sources = dict(previous['local_source_sha256'], **plan['source_pins'], **{config_reference['path']: config_reference['sha256']})
    manifest = dict(previous, config_path=config_reference['path'], predecessor_config_path=previous['config_path'],
        output=str(directory / 'parent'), local_source_sha256=sources,
        remote_operator=plan['remote_adapter_directory'],
        remote_helper_sha256=dict(previous['remote_helper_sha256'], **plan['remote_files']),
        status='C2_EXPLICIT_POST_LOADED_RETENTION_OWNER_SAME_POLICY')
    return write_once(directory / 'MANIFEST.json', manifest)


def rebind(plan, approval, dependency, binding, cpu, remote):
    from owner import authorize, disabled, inventory, verify_fence
    authorize(plan, approval, 'rebind')
    require(approval['dependency'] == dependency and approval['successor_binding'] == binding, 'exact_Main_dependency_and_loaded_binding')
    transaction = Path(plan['transaction_dir'])
    with locked(transaction / 'ACTION.lock', create=True):
        verify_fence(dependency, cpu)
        before = inventory(plan)
        proof = remote('loaded', plan, binding)
        require(proof['schema'] == 'C2_ACTUAL_POST_LOADED_REBIND_VERIFIED_V1'
            and proof['binding_sha256'] == binding['sha256'] and proof['source_epoch'] == plan['source_epoch']
            and proof['life_binding_sha256'] == digest(plan['old_life'])
            and proof['native']['pid'] != plan['old_life']['pid'], 'actual_source_bound_LOADED_successor_required')
        require(inventory(plan) == before, 'old_ledgers_unchanged_before_owner_transfer')
        write_once(transaction / 'REBIND_CLAIM.json', dict(approval=approval, dependency=dependency, binding=binding, proof=proof))
        disabled(plan)
        cpu.signal(plan, 'service', 'retire')
        cpu.signal(plan, 'publisher', 'retire')
        with ExitLocks(plan):
            require(inventory(plan) == before, 'old_ledgers_unchanged_after_owner_exit')
            remote('loaded', plan, binding)
            previous = pinned(plan['manifest'])
            manifest = next_manifest(plan, previous, read(previous['config_path']), transaction / 'session_000001',
                binding, before['reserved_response_count'])
            return write_once(transaction / 'REBOUND.json', dict(schema='C2_OWNER_REBOUND_V1', plan=plan,
                dependency=dependency, successor_binding=binding, actual_loaded_proof=proof, manifest=manifest,
                old_inventory=before, native_signals=0, started=False, parent_rebind_actual_LOADED_required=True))


class ExitLocks:
    def __init__(self, plan):
        self.plan = plan

    def __enter__(self):
        from contextlib import ExitStack
        self.stack = ExitStack()
        try:
            for role in ('service', 'controller', 'publisher'):
                self.stack.enter_context(locked(self.plan['locks'][role]))
        except BaseException:
            self.stack.close()
            raise
        return self

    def __exit__(self, *arguments):
        return self.stack.__exit__(*arguments)


def publisher(rebound_reference, manifest_reference):
    rebound = pinned(rebound_reference)
    plan = rebound['plan']
    pins_match(plan['source_pins'])
    manifest, config, previous = validate_successor_manifest(plan, rebound, manifest_reference)
    from transport import Remote
    Remote()('loaded', plan, rebound['successor_binding'])
    original_path = core.PREVIOUS / 'checkpoint_tail_parent_strong.py'
    candidate = ported_parent_source(plan)
    sys.path.insert(0, str(core.PREVIOUS))
    sys.path.insert(0, str(core.REPO))
    module = types.ModuleType('explicit_C2_same_policy_parent')
    module.__file__ = str(original_path)
    exec(compile(candidate, str(original_path), 'exec'), module.__dict__)
    original_validate = module.validate_config
    def validate_manifest(value):
        require(value == manifest, 'same_exact_successor_manifest')
        pins_match(value['local_source_sha256'])
        normalized = dict(config, native_binding_path=previous['native_binding_path'],
            native_binding_sha256=previous['native_binding_sha256'])
        original_validate(previous, normalized)
        require(not Path(value['output']).exists(), 'append_only_new_parent_output')
        return config
    module.validate_manifest = validate_manifest
    sys.argv = [str(original_path), '--manifest', manifest_reference['path'], '--manifest-sha256', manifest_reference['sha256']]
    module.main()


def serve(rebound_reference):
    rebound = pinned(rebound_reference)
    require(rebound['schema'] == 'C2_OWNER_REBOUND_V1' and rebound['native_signals'] == 0, 'explicit_committed_rebind')
    plan = rebound['plan']
    pins_match(plan['source_pins'])
    transaction = Path(plan['transaction_dir'])
    verify_successor_registry(plan, rebound_reference)
    from transport import Remote
    with locked(plan['locks']['service']):
        Remote()('loaded', plan, rebound['successor_binding'])
        write_once(transaction / ('SERVICE_' + str(os.getpid()) + '.json'), dict(identity=core.process_identity(os.getpid()),
            rebound=rebound_reference, service_lock=plan['locks']['service']))
        manifests = [path for path in transaction.glob('session_*/MANIFEST.json')
            if (Path(read(path)['output']) / 'STARTED.json').exists()]
        manifest_reference = reference(max(manifests, key=lambda path: path.stat().st_mtime_ns)) if manifests else rebound['manifest']
        while time.time() < DEADLINE:
            manifest, config, previous_config = validate_successor_manifest(plan, rebound, manifest_reference)
            output = Path(manifest['output'])
            if output.exists():
                require((output / 'STARTED.json').exists(), 'incomplete_successor_start_requires_Main_reconciliation')
                with locked(plan['locks']['controller']):
                    manifest_reference = next_manifest(plan, manifest, read(manifest['config_path']),
                        transaction / ('session_' + str(time.time_ns())), rebound['successor_binding'],
                        read(manifest['config_path'])['start_after_response_count'])
                manifest = pinned(manifest_reference)
            Remote()('loaded', plan, rebound['successor_binding'])
            command = ['/usr/bin/python3', '-B', str(core.HERE / 'cli.py'), 'publisher',
                '--receipt', rebound_reference['path'], '--receipt-sha256', rebound_reference['sha256'],
                '--manifest', manifest_reference['path'], '--manifest-sha256', manifest_reference['sha256']]
            session = Path(manifest['output']).parent
            with (session / 'CPU_PARENT.log').open('xb') as log:
                child = subprocess.Popen(command, cwd=core.REPO, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
                write_once(session / 'SPAWNED.json', dict(pid=child.pid, native_signals=0))
                code = child.wait()
            write_once(session / 'EXIT.json', dict(code=code, native_signals=0))
            time.sleep(10)


def successor_registry(plan, rebound_reference):
    from owner import read
    original = read(Path(plan['transaction_dir']) / 'ORIGINAL_REGISTRY.json')
    argv = ['/usr/bin/python3', '-B', str(core.HERE / 'cli.py'), 'serve', '--receipt', rebound_reference['path'],
        '--receipt-sha256', rebound_reference['sha256']]
    return dict(original, enabled=True, argv=argv, entrypoint=str(core.HERE / 'cli.py'),
        entrypoint_sha256=plan['source_pins'][str(core.HERE / 'cli.py')])


def verify_successor_registry(plan, rebound_reference):
    actual = read(core.REGISTRY)
    original = read(Path(plan['transaction_dir']) / 'ORIGINAL_REGISTRY.json')
    require(actual in (dict(original, enabled=False), successor_registry(plan, rebound_reference)),
        'only_disabled_original_or_exact_approved_successor_registry')


def enable_successor(plan, approval, rebound_reference, service_receipt):
    from owner import authorize, disabled, replace_registry
    authorize(plan, approval, 'enable-successor')
    require(approval['rebound'] == rebound_reference and approval['service_receipt'] == service_receipt,
        'explicit_exact_successor_service_admission')
    rebound = pinned(rebound_reference)
    require(rebound['schema'] == 'C2_OWNER_REBOUND_V1' and rebound['plan'] == plan
        and rebound['native_signals'] == 0, 'enable_only_same_explicit_rebound_owner')
    started = pinned(service_receipt)
    actual = core.process_identity(started['identity']['pid'])
    expected = successor_registry(plan, rebound_reference)
    require(started['rebound'] == rebound_reference and all(actual[key] == started['identity'][key] for key in core.IDENTITY)
        and actual['argv'] == expected['argv'] and actual['state'] not in ('T', 't', 'Z', 'X')
        and core.lock_owners(plan['locks']['service']) == [actual['pid']], 'actual_new_CPU_service_holds_original_lock')
    with locked(Path(plan['transaction_dir']) / 'ACTION.lock', create=True):
        disabled(plan)
        write_once(Path(plan['transaction_dir']) / 'ENABLE_SUCCESSOR_CLAIM.json', dict(approval=approval, actual_service=actual))
        replace_registry(read(core.REGISTRY), expected)
        return write_once(Path(plan['transaction_dir']) / 'SUCCESSOR_REGISTRY.json', dict(registry_sha256=sha(core.REGISTRY),
            actual_service=actual, native_signals=0))
