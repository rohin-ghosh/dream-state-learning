"""All mutation, process, provider, transport and native actions are simulated."""

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import common as core
sys.path.insert(0, str(core.REPO))
import owner
import successor
import transport
from common import DEADLINE, digest, read, reference, sha, write_once


class FakeCPU:
    def __init__(self):
        self.stopped = set()
        self.actions = []
        self.race = None

    def check(self, plan, role, *, stopped=False):
        if (role in self.stopped) != stopped:
            raise ValueError('CPU_state')

    def signal(self, plan, role, operation):
        self.actions.append((role, operation))
        if operation == 'stop':
            self.stopped.add(role)
            if role == 'publisher' and self.race:
                self.race()
        else:
            self.stopped.discard(role)

    def recover(self, plan, role):
        if role in self.stopped:
            self.signal(plan, role, 'resume')
        self.check(plan, role)
        return True


class OwnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        self.here = self.repo / 'worker/owner_transport'
        self.owner_root = self.repo / 'old-owner'
        self.previous = self.repo / 'previous'
        self.registry = self.repo / 'services.d/c2-parent.json'
        for path in (self.here, self.owner_root, self.previous, self.registry.parent):
            path.mkdir(parents=True)
        for name, value in dict(REPO=self.repo, HERE=self.here, OWNER=self.owner_root,
                PREVIOUS=self.previous, REGISTRY=self.registry).items():
            patcher = patch.object(core, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(owner.time, 'time', return_value=DEADLINE - 1000)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(patch.stopall)
        patch('signal.pidfd_send_signal', side_effect=AssertionError('NO_ACTUAL_SIGNAL')).start()
        patch('os.kill', side_effect=AssertionError('NO_ACTUAL_SIGNAL')).start()
        self.cpu = FakeCPU()
        self.remote = Mock(side_effect=self.remote_result)
        sources = [self.owner_root / 'c2_service.py', self.owner_root / 'c2_restore.py',
            self.previous / 'checkpoint_tail_parent_strong.py', self.previous / 'c2_parent_continue.py',
            self.repo / 'gpu/orch_r133_programme_parent.py', self.repo / 'gpu/ovx3_ssh.sh', self.here / 'cli.py',
            self.here / 'common.py', self.here / 'c2_owner_binding.py']
        for path in sources:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('synthetic-source\n')
        session = self.owner_root / 'c2_session1'
        session.mkdir()
        self.output = session / 'parent'
        self.output.mkdir()
        self.parent_lock = self.repo / 'historic/PARENT.lock'
        self.parent_lock.parent.mkdir()
        self.parent_lock.touch()
        config = dict(root=core.ROOT, source_root='/legacy/unchanged', hard_end_unix=DEADLINE,
            cadence_responses=1, cadence_label='PERSISTENT', start_after_response_count=7,
            existing_parent_lock=str(self.parent_lock), programme='raw_parented', branch='C2',
            native_binding_path='/old/binding', native_binding_sha256='b' * 64, node='ovx3')
        write_once(session / 'CONFIG.json', config)
        write_once(self.output / 'STARTED.json', dict(pid=202, programme='raw_parented', branch='C2',
            config_sha256=sha(session / 'CONFIG.json')))
        manifest = dict(config_path=str(session / 'CONFIG.json'), predecessor_config_path=str(session / 'CONFIG.json'),
            output=str(self.output), local_source_sha256={str(path): sha(path) for path in sources},
            remote_helper_sha256={}, policy_addendum='/unchanged-policy')
        write_once(session / 'MANIFEST.json', manifest)
        for path in (self.owner_root / 'C2_SERVICE.lock', self.previous / 'private/C2_WAIT_CONTROLLER.lock'):
            path.parent.mkdir(exist_ok=True)
            path.touch()
        registry = dict(enabled=True, name='c2-parent', kind='parent', child_native=False, until_unix=DEADLINE,
            singleton_lock=str(self.owner_root / 'C2_SERVICE.lock'), entrypoint=str(self.owner_root / 'c2_service.py'),
            entrypoint_sha256=sha(self.owner_root / 'c2_service.py'),
            argv=['/usr/bin/python3', '-B', str(self.owner_root / 'c2_service.py')])
        write_once(self.registry, registry)
        transaction = self.here / 'transactions/test'
        transaction.mkdir(parents=True)
        self.plan = dict(schema='C2_OWNER_TRANSPORT_PLAN_V1', deadline_unix=DEADLINE,
            registry=reference(self.registry), owner_root=str(self.owner_root), transaction_dir=str(transaction),
            created_unix=DEADLINE - 1010, not_after_unix=DEADLINE - 600,
            old_life=dict(pid=1139778, journal_root=core.ROOT + '/stream', journal_id=core.JOURNAL, hard_end_unix=DEADLINE),
            manifest=reference(session / 'MANIFEST.json'), source_pins={str(path): sha(path) for path in sources},
            ancestry_configs={str(self.output): reference(session / 'CONFIG.json')}, source_epoch='C2-epoch4',
            service=dict(pid=101, uid=158984, start_ticks='10', boot_id='boot', argv=registry['argv'], cwd=str(self.repo)),
            publisher=dict(pid=202, ppid=101, uid=158984, start_ticks='20', boot_id='boot', cwd=str(self.repo),
                argv=['/usr/bin/python3', '-B', str(self.previous / 'checkpoint_tail_parent_strong.py'),
                    '--manifest', str(session / 'MANIFEST.json'), '--manifest-sha256', sha(session / 'MANIFEST.json')]),
            locks=dict(service=str(self.owner_root / 'C2_SERVICE.lock'),
                controller=str(self.previous / 'private/C2_WAIT_CONTROLLER.lock'), publisher=str(self.parent_lock)),
            remote_adapter_directory='/new/readonly', remote_files={'/new/readonly/common.py': sha(self.here / 'common.py'),
                '/new/readonly/c2_owner_binding.py': sha(self.here / 'c2_owner_binding.py')})
        self.plan['lock_identities'] = {key: owner.lock_identity(path) for key, path in self.plan['locks'].items()}
        write_once(transaction / 'PLAN.json', self.plan)

    def approval(self, operation):
        return dict(schema='C2_OWNER_ACTION_APPROVAL_V1', plan_sha256=digest(self.plan), operation=operation,
            deadline_unix=DEADLINE, created_unix=DEADLINE - 1001, not_after_unix=DEADLINE - 700)

    def remote_result(self, action, plan, value):
        if action == 'drain':
            return dict(schema='C2_DRAIN_REMOTE_VERIFIED_V1', life_binding_sha256=digest(plan['old_life']),
                inventory_sha256=digest(value), native_signals=0, journal_writes=0)
        return dict(schema='C2_ACTUAL_POST_LOADED_REBIND_VERIFIED_V1', binding_sha256=value['sha256'],
            life_binding_sha256=digest(plan['old_life']), source_epoch=plan['source_epoch'], native=dict(pid=999),
            native_signals=0, journal_writes=0)

    def disable(self):
        return owner.disable(self.plan, self.approval('disable'))

    def fence(self):
        self.disable()
        return owner.fence(self.plan, self.approval('fence'), self.cpu, self.remote)

    def test_disable_changes_only_C2_enabled(self):
        before = read(self.registry)
        other = self.registry.parent / 'p7-parent.json'
        other.write_text('unchanged')
        self.disable()
        self.assertEqual(read(self.registry), dict(before, enabled=False))
        self.assertEqual(other.read_text(), 'unchanged')
        self.assertEqual(self.cpu.actions, [])

    def test_wrong_owner_operation_approval_refused(self):
        with self.assertRaises(ValueError):
            owner.disable(self.plan, self.approval('fence'))

    def test_native_PID_cannot_be_fenced(self):
        self.plan['publisher']['pid'] = self.plan['old_life']['pid']
        with self.assertRaises(ValueError):
            owner.validate(self.plan)

    def test_orphaned_preexisting_publisher_is_supported(self):
        self.plan['publisher']['ppid'] = 1
        owner.validate(self.plan)

    def test_lock_inode_replacement_refused(self):
        path = self.parent_lock
        path.rename(path.with_suffix('.old'))
        path.touch()
        with self.assertRaisesRegex(ValueError, 'lock_objects'):
            owner.validate(self.plan)

    def test_non_sibling_ancestor_config_and_reserved_cursor(self):
        ancestor = self.repo / 'preserved-ledger'
        ancestor.mkdir()
        config_path = self.repo / 'separate-config.json'
        manifest = read(self.plan['manifest']['path'])
        config = read(manifest['config_path'])
        write_once(config_path, dict(config, start_after_response_count=1))
        write_once(ancestor / 'STARTED.json', dict(programme=config['programme'], branch=config['branch'],
            config_sha256=sha(config_path)))
        call = ancestor / 'parent_000017'
        call.mkdir()
        write_once(call / 'SOURCE.json', dict(response_count=19))
        write_once(call / 'DISPATCH_INTENT.json', dict(source_sha256=sha(call / 'SOURCE.json')))
        write_once(call / 'RESULT.json', dict(status='SILENT', source_response_count=19))
        config.update(predecessor_output=str(ancestor), predecessor_started_sha256=sha(ancestor / 'STARTED.json'))
        Path(manifest['config_path']).write_text(json.dumps(config))
        started = read(self.output / 'STARTED.json')
        started['config_sha256'] = sha(manifest['config_path'])
        (self.output / 'STARTED.json').write_text(json.dumps(started))
        self.plan['ancestry_configs'] = {str(self.output): reference(manifest['config_path']),
            str(ancestor): reference(config_path)}
        observed = owner.inventory(self.plan)
        self.assertEqual(observed['reserved_response_count'], 19)
        self.assertIn(str(config_path), observed['ledger_pins'])
        del self.plan['ancestry_configs'][str(ancestor)]
        with self.assertRaisesRegex(ValueError, 'ancestor_config'):
            owner.inventory(self.plan)

    def test_parent_source_tamper_refused(self):
        (self.owner_root / 'c2_service.py').write_text('changed')
        with self.assertRaises(ValueError):
            owner.validate(self.plan)

    def test_provider_inflight_blocks_before_signal(self):
        (self.output / 'parent_000001').mkdir()
        self.disable()
        with self.assertRaisesRegex(ValueError, 'pending_drain'):
            owner.fence(self.plan, self.approval('fence'), self.cpu, self.remote)
        self.assertEqual(self.cpu.actions, [])

    def call(self, status):
        directory = self.output / 'parent_000001'
        directory.mkdir()
        write_once(directory / 'SOURCE.json', dict(response_count=12))
        write_once(directory / 'DISPATCH_INTENT.json', dict(source_sha256=sha(directory / 'SOURCE.json')))
        result = dict(status=status, source_response_count=12)
        if status != 'SILENT':
            result['inbox_publication'] = dict(id='message')
        write_once(directory / 'RESULT.json', result)
        return directory

    def test_terminal_prepublication_failure_preserves_reserved_cursor(self):
        directory = self.call('MISSING')
        result = dict(status='MISSING', source_response_count=12,
            error_code='parent_call_or_delivery_failed', started_unix=1, finished_unix=2)
        (directory / 'RESULT.json').write_text(json.dumps(result))
        self.assertEqual(owner.inventory(self.plan)['reserved_response_count'], 12)
        result['sent_unix'] = 1.5
        (directory / 'RESULT.json').write_text(json.dumps(result))
        with self.assertRaisesRegex(ValueError, 'reconciliation'):
            owner.inventory(self.plan)

    def test_silent_status_cannot_hide_publication(self):
        directory = self.call('SILENT')
        result = read(directory / 'RESULT.json')
        result['sent_unix'] = 1
        (directory / 'RESULT.json').write_text(json.dumps(result))
        with self.assertRaisesRegex(ValueError, 'silent_result'):
            owner.inventory(self.plan)

    def test_ambiguous_MISSING_result_is_not_drained(self):
        self.call('MISSING')
        with self.assertRaisesRegex(ValueError, 'reconciliation'):
            owner.inventory(self.plan)

    def test_queued_publication_waits_for_consumption(self):
        self.call('PUBLISHED')
        with self.assertRaisesRegex(ValueError, 'not_yet_consumed'):
            owner.inventory(self.plan)

    def test_all_ledgers_sidecars_and_cursor_are_preserved(self):
        self.call('SILENT')
        (self.output / 'R233_HUMAN_PRIORITY.jsonl').write_text('preserved')
        before = owner.inventory(self.plan)
        dependency = self.fence()
        receipt = read(dependency['path'])
        self.assertEqual(receipt['inventory'], before)
        self.assertEqual(before['reserved_response_count'], 12)
        self.assertIn(str(self.output / 'R233_HUMAN_PRIORITY.jsonl'), before['ledger_pins'])
        self.assertEqual(self.cpu.actions, [('service', 'stop'), ('publisher', 'stop')])

    def test_idle_race_resumes_same_CPU_owners_and_requires_review(self):
        self.disable()
        self.cpu.race = lambda: (self.output / 'raced.json').write_text('{}')
        with self.assertRaises(ValueError):
            owner.fence(self.plan, self.approval('fence'), self.cpu, self.remote)
        self.assertEqual(self.cpu.actions[-2:], [('publisher', 'resume'), ('service', 'resume')])
        self.assertFalse(self.cpu.stopped)
        with self.assertRaises(FileExistsError):
            owner.fence(self.plan, self.approval('fence'), self.cpu, self.remote)

    def test_stop_timeout_recovers_role_even_when_signal_did_not_return(self):
        self.disable()
        signal_action = self.cpu.signal
        def uncertain_stop(plan, role, operation):
            signal_action(plan, role, operation)
            if role == 'publisher' and operation == 'stop':
                raise ValueError('simulated_stop_timeout_after_effect')
        with patch.object(self.cpu, 'signal', side_effect=uncertain_stop):
            with self.assertRaisesRegex(ValueError, 'simulated_stop_timeout'):
                owner.fence(self.plan, self.approval('fence'), self.cpu, self.remote)
        self.assertFalse(self.cpu.stopped)
        refusal = read(Path(self.plan['transaction_dir']) / 'FENCE_REFUSED.json')
        self.assertTrue(refusal['same_CPU_owners_resumed'])
        self.assertEqual(refusal['recovered_roles'], ['publisher', 'service'])

    def test_failed_recovery_never_claims_both_owners_resumed(self):
        self.disable()
        self.cpu.race = lambda: (self.output / 'raced.json').write_text('{}')
        recover = self.cpu.recover
        def refuse_publisher(plan, role):
            if role == 'publisher':
                raise ValueError('identity_changed_or_signal_outcome_unknown')
            return recover(plan, role)
        with patch.object(self.cpu, 'recover', side_effect=refuse_publisher):
            with self.assertRaises(ValueError):
                owner.fence(self.plan, self.approval('fence'), self.cpu, self.remote)
        refusal = read(Path(self.plan['transaction_dir']) / 'FENCE_REFUSED.json')
        self.assertFalse(refusal['same_CPU_owners_resumed'])
        self.assertIn('publisher', refusal['uncertain_roles'])
        self.assertNotIn('service', self.cpu.stopped)

    def test_original_owner_RPC_rechecks_both_processes_and_ledger(self):
        dependency = self.fence()
        result = owner.verify_fence(dependency, self.cpu)
        self.assertTrue(result['ledger_pins_verified'])
        (self.output / 'altered.json').write_text('{}')
        with self.assertRaises(ValueError):
            owner.verify_fence(dependency, self.cpu)

    def test_rebind_requires_actual_loaded_before_retirement(self):
        dependency = self.fence()
        binding = dict(path='/new/binding', sha256='b' * 64)
        approval = dict(self.approval('rebind'), dependency=dependency, successor_binding=binding)
        self.remote.side_effect = ValueError('not_loaded')
        with self.assertRaises(ValueError):
            successor.rebind(self.plan, approval, dependency, binding, self.cpu, self.remote)
        self.assertEqual(self.cpu.actions, [('service', 'stop'), ('publisher', 'stop')])

    def test_rebind_preserves_policy_and_reserves_cursor(self):
        self.call('SILENT')
        dependency = self.fence()
        binding = dict(path='/new/binding', sha256='b' * 64)
        approval = dict(self.approval('rebind'), dependency=dependency, successor_binding=binding)
        receipt = successor.rebind(self.plan, approval, dependency, binding, self.cpu, self.remote)
        rebound = read(receipt['path'])
        manifest = read(rebound['manifest']['path'])
        config = read(manifest['config_path'])
        old = read(read(self.plan['manifest']['path'])['config_path'])
        self.assertEqual({key: value for key, value in config.items() if key not in successor.CONFIG_DELTA},
            {key: value for key, value in old.items() if key not in successor.CONFIG_DELTA})
        self.assertEqual(config['start_after_response_count'], 12)
        self.assertEqual(config['native_binding_path'], binding['path'])
        self.assertEqual(self.cpu.actions[-2:], [('service', 'retire'), ('publisher', 'retire')])
        self.assertFalse(rebound['started'])
        successor.validate_successor_manifest(self.plan, rebound, rebound['manifest'])
        manifest['policy_addendum'] = '/different-policy'
        Path(rebound['manifest']['path']).write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'manifest_except'):
            successor.validate_successor_manifest(self.plan, rebound, reference(rebound['manifest']['path']))
        with self.assertRaises(ValueError):
            owner.verify_fence(dependency, self.cpu)

    def test_parent_port_changes_only_one_import_and_rejects_changed_source(self):
        actual_path = Path(__file__).resolve().parents[2] / 'rohin233_recovery_node4_20260918/checkpoint_tail_parent_strong.py'
        original = actual_path.read_bytes()
        local = self.previous / 'checkpoint_tail_parent_strong.py'
        local.write_bytes(original)
        self.plan['source_pins'][str(local)] = sha(local)
        candidate = successor.ported_parent_source(self.plan)
        self.assertEqual(candidate, original.replace(b'from checkpoint_tail_parent_binding import verify;verify(',
            b'from c2_owner_binding import verify;verify(', 1))
        compile(candidate, str(local), 'exec')
        self.assertEqual(local.read_bytes(), original)
        local.write_bytes(original + b'\n')
        with self.assertRaisesRegex(ValueError, 'pinned_original'):
            successor.ported_parent_source(self.plan)

    def test_successor_enable_requires_actual_service_identity_and_original_lock(self):
        dependency = self.fence()
        binding = dict(path='/new/binding', sha256='b' * 64)
        approval = dict(self.approval('rebind'), dependency=dependency, successor_binding=binding)
        rebound = successor.rebind(self.plan, approval, dependency, binding, self.cpu, self.remote)
        expected = successor.successor_registry(self.plan, rebound)
        actor = dict(pid=303, uid=158984, start_ticks='30', boot_id='boot', cwd=str(self.repo),
            argv=expected['argv'], state='S')
        service = write_once(Path(self.plan['transaction_dir']) / 'SERVICE_303.json',
            dict(identity=actor, rebound=rebound, service_lock=self.plan['locks']['service']))
        approval = dict(self.approval('enable-successor'), rebound=rebound, service_receipt=service)
        with patch.object(core, 'process_identity', return_value=actor), patch.object(core, 'lock_owners', return_value=[]):
            with self.assertRaisesRegex(ValueError, 'holds_original_lock'):
                successor.enable_successor(self.plan, approval, rebound, service)
        with patch.object(core, 'process_identity', return_value=actor), patch.object(core, 'lock_owners', return_value=[303]):
            successor.enable_successor(self.plan, approval, rebound, service)
        self.assertEqual(read(self.registry), expected)
        self.assertEqual(expected['singleton_lock'], self.plan['locks']['service'])
        self.assertEqual(expected['until_unix'], DEADLINE)

    def test_linux_signal_rejects_native_role_before_opening_pidfd(self):
        with patch.object(owner.os, 'pidfd_open') as opened:
            with self.assertRaisesRegex(ValueError, 'CPU_only_operations'):
                owner.LinuxCPU().signal(self.plan, 'old_life', 'stop')
            opened.assert_not_called()

    def test_linux_stop_and_recovery_use_exact_pidfd_no_real_signal(self):
        controller = owner.LinuxCPU()
        actor = dict(self.plan['publisher'], state='T')
        with patch.object(controller, 'check'), patch.object(owner.os, 'pidfd_open', return_value=12345) as opened, \
                patch.object(owner.os, 'close') as closed, patch.object(owner.select, 'select', return_value=([], [], [])), \
                patch.object(core, 'process_identity', return_value=actor), patch.object(owner.signal, 'pidfd_send_signal') as sent:
            controller.signal(self.plan, 'publisher', 'stop')
            opened.assert_called_once_with(202)
            sent.assert_called_once_with(12345, signal.SIGSTOP)
            closed.assert_called_once_with(12345)
        with patch.object(core, 'process_identity', return_value=dict(actor, state='S')), patch.object(controller, 'signal') as sent:
            self.assertTrue(controller.recover(self.plan, 'publisher'))
            sent.assert_not_called()

    def test_linux_identity_and_original_lock_owner_are_not_assumed(self):
        controller = owner.LinuxCPU()
        actor = dict(self.plan['publisher'], state='S')
        with patch.object(core, 'process_identity', return_value=dict(actor, start_ticks='REUSED')):
            with self.assertRaisesRegex(ValueError, 'exact_CPU_pid'):
                controller.check(self.plan, 'publisher')
        with patch.object(core, 'process_identity', return_value=actor), patch.object(core, 'lock_owners', return_value=[999]):
            with self.assertRaisesRegex(ValueError, 'sole_original_lock_owner'):
                controller.check(self.plan, 'publisher')

    def test_rpc_nonce_and_original_dependency_not_a_boolean(self):
        dependency = self.fence()
        request = dict(schema='C2_OWNER_CHECK_REQUEST_V1', nonce='nonce', dependency=dependency,
            life_binding_sha256=digest(self.plan['old_life']), source_epoch=self.plan['source_epoch'], source_pins=self.plan['source_pins'])
        response = transport.owner_exchange(request, dependency, self.cpu)
        bridge = transport.OwnerBridge(['never-executed'], dependency, self.plan['source_pins'])
        with patch.object(transport.secrets, 'token_hex', return_value='nonce'), patch.object(transport.subprocess, 'run',
                return_value=SimpleNamespace(stdout=json.dumps(response).encode())) as run:
            bridge.check(self.plan['old_life'], self.plan['source_epoch'])
            self.assertEqual(run.call_args.kwargs['timeout'], 2)
            response['nonce'] = 'replayed'
            run.return_value.stdout = json.dumps(response).encode()
            with self.assertRaises(ValueError):
                bridge.check(self.plan['old_life'], self.plan['source_epoch'])

    def test_boolean_false_is_not_numeric_inflight_count(self):
        dependency = self.fence()
        request = dict(schema='C2_OWNER_CHECK_REQUEST_V1', nonce='nonce', dependency=dependency,
            life_binding_sha256=digest(self.plan['old_life']), source_epoch=self.plan['source_epoch'], source_pins=self.plan['source_pins'])
        response = transport.owner_exchange(request, dependency, self.cpu)
        response['recheck']['inflight_deliveries'] = False
        bridge = transport.OwnerBridge(['never-executed'], dependency, self.plan['source_pins'])
        with patch.object(transport.secrets, 'token_hex', return_value='nonce'), patch.object(transport.subprocess, 'run',
                return_value=SimpleNamespace(stdout=json.dumps(response).encode())):
            with self.assertRaisesRegex(ValueError, 'fresh_actual'):
                bridge.check(self.plan['old_life'], self.plan['source_epoch'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
