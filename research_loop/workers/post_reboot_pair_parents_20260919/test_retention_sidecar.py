"""Synthetic sidecar tests; every signal, SSH call, provider and launch is forbidden."""

from copy import deepcopy
import json
import os
from pathlib import Path
import signal
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import retention_sidecar as sidecar
import retention_sidecar_remote as remote


def put(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(sidecar.content(document))
    return str(path)


class FakeCPU:
    def __init__(self):
        self.stopped = False
        self.retired = False
        self.signals = []

    def check(self, expected, lock, stopped=False):
        sidecar.require(self.stopped == stopped and not self.retired, 'synthetic_exact_CPU_state')

    def signal_exact(self, expected, lock, operation):
        self.signals.append(operation)
        if operation == signal.SIGSTOP:
            self.stopped = True
        elif operation == signal.SIGKILL:
            self.retired = True
        else:
            raise AssertionError('unexpected signal')

    def wait_stopped(self, expected, lock):
        self.check(expected, lock, stopped=True)

    def wait_exited(self, expected):
        sidecar.require(self.retired, 'synthetic_exit')


class SidecarTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=sidecar.HERE)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.worker = self.root / 'worker'
        self.directory = self.worker / 'private/learner'
        self.directory.mkdir(parents=True)
        self.transaction = self.worker / 'retention_transactions/synthetic'
        self.transaction.mkdir(parents=True)
        self.addCleanup(patch.stopall)
        patch.object(sidecar, 'HERE', self.worker).start()
        patch.object(sidecar, 'REPO', self.root).start()
        patch.object(sidecar.time, 'time', return_value=1000).start()
        self.actual_signal = patch.object(signal, 'pidfd_send_signal', side_effect=AssertionError('no live signals')).start()
        self.actual_ssh = patch.object(sidecar.subprocess, 'run', side_effect=AssertionError('no SSH/provider calls')).start()
        self.actual_launch = patch.object(sidecar.subprocess, 'Popen', side_effect=AssertionError('no launches')).start()
        self.lock = self.directory / 'PUBLISHER.lock'
        self.lock.touch()
        old_native = dict(pid=99990001, start_ticks='old-start', boot_id='native-boot',
            argv=['python', '-B', '-m', 'gpu.r232_recovery', 'native', '--config', '/native/old/GUARD.json'],
            cwd='/native/source', root='/native', journal_id='journal')
        old_parent = dict(pid=99990002, start_ticks='cpu-start', boot_id='cpu-boot', uid=1000,
            argv=['/usr/bin/python3', '-B', str(self.worker / 'parent_service.py'), '--arm', 'learner'], cwd=str(self.root))
        for name in ('parent_service.py', 'remote_io.py', 'retention_sidecar.py', 'retention_sidecar_remote.py'):
            (self.worker / name).write_text('synthetic source for ' + name)
        sources = {str(self.worker / name): sidecar.sha(self.worker / name) for name in ('parent_service.py', 'remote_io.py')}
        self.process_path = self.directory / 'PROCESS_original.json'
        put(self.process_path, dict(old_parent, native=old_native, sources=sources))
        self.registry = self.root / 'registry.json'
        put(self.registry, dict(enabled=False, name='pair-curriculum-learner', argv=old_parent['argv'],
            singleton_lock=str(self.lock), until_unix=sidecar.CEILING))
        self.turn = self.directory / 'turn_000001'
        self.turn.mkdir()
        put(self.turn / 'RESULT.json', dict(response=dict(message='One concrete task.'), model='unchanged-model'))
        put(self.turn / 'stdout.json', dict(actual='synthetic-provider'))
        publication = dict(publication=dict(id='first-id', sha256='inbox-hash'), journal_id='journal',
            provider_response_sha256=sidecar.sha(self.turn / 'stdout.json'),
            text_sha256=remote.hashlib.sha256(b'One concrete task.').hexdigest())
        put(self.turn / 'PUBLICATION.json', publication)
        put(self.turn / 'DISPATCH.json', dict(started=True))
        self.state = dict(native=old_native, stage=5, first_turn=False, last_parent_cycle=1,
            events=[dict(cycle=1, response=dict(document=dict(response=dict(raw='Unfiltered incorrect 鸟 text.'))))],
            assessments=[dict(unchanged=True)], messages=['One concrete task.'], next_index=5, previous_sha256='cursor',
            deliveries=[dict(directory=str(self.turn), receipt=publication, text='One concrete task.', parent_process=old_parent)],
            pending_turn=None, provider_inflight=None, provider_blocked=None, publication_blocked=None,
            transport_blocked=None, provider_429_attempts=2, request=dict(pending_child_work=True),
            response=None, committed=None, act_stage=None)
        put(self.directory / 'STATE.json', self.state)
        put(self.directory / 'STATUS.json', dict(health='OBSERVING', caught_up=True, observed_unix=1000))
        binding = dict(pid=old_native['pid'], start_ticks=old_native['start_ticks'], boot_id=old_native['boot_id'], uid=1000,
            command=old_native['argv'], journal_id='journal', journal_root='/native/raw/stream', hard_end_unix=sidecar.CEILING)
        self.plan = dict(schema='PAIR_PARENT_FENCE_PLAN_V1', arm='learner', transaction_id='synthetic', owner='synthetic-owner',
            directory=str(self.directory), lock=str(self.lock), transaction_dir=str(self.transaction),
            old_parent=old_parent, old_process_receipt=dict(path=str(self.process_path), sha256=sidecar.sha(self.process_path)),
            old_native=dict(old_native, uid=1000), life_binding=binding, source_epoch='synthetic-epoch',
            state_sha256=sidecar.sha(self.directory / 'STATE.json'),
            source_pins={str(path): sidecar.sha(path) for path in self.worker.glob('*.py')},
            transport_source_path=str(self.worker / 'remote_io.py'), remote_transport_pins={'/native/parent_io.py': 'transport-hash'},
            disabled_registry=dict(path=str(self.registry), sha256=sidecar.sha(self.registry)),
            until_unix=sidecar.CEILING, created_unix=990, not_after_unix=1100)
        put(self.transaction / 'PLAN.json', self.plan)
        self.cpu = FakeCPU()
        self.calls = []

    def fake_remote(self, plan, action, state=None, deliveries=None, approval=None, dependency_sha256=None, request=None):
        self.calls.append(action)
        return dict(native=approval['new_native'] if approval else plan['old_native'], acknowledged_deliveries=1)

    def fenced(self):
        return sidecar.fence(self.plan, self.cpu, self.fake_remote)

    def approved(self):
        gate = self.transaction / 'MAIN_GATE.json'
        put(gate, dict(synthetic_test_only=True, passed=True))
        return dict(schema='PAIR_PARENT_POST_LOADED_APPROVAL_V1', transaction_id='synthetic', plan_sha256=sidecar.digest(self.plan),
            dependency_sha256=sidecar.sha(self.transaction / 'PARENT_DEPENDENCIES.json'), owner='synthetic-owner',
            source_epoch='synthetic-epoch', until_unix=sidecar.CEILING, created_unix=990, not_after_unix=1100,
            checkpoint_gate_receipt=dict(path=str(gate), sha256=sidecar.sha(gate)), checkpoint_gate_passed=True,
            new_native=dict(self.plan['old_native'], pid=99990003, start_ticks='new-start'),
            guard_path='/native/new/GUARD.json', receiver_pins={'/native/new/GUARD.json': 'pinned-guard'})

    def committed(self):
        self.fenced()
        approval = self.approved()
        return sidecar.rebind(self.plan, approval, self.cpu, self.fake_remote)

    def test_fence_issues_actual_interface_preserves_ledger_and_keeps_CPU_lock(self):
        before = sidecar.file_bytes(self.directory / 'STATE.json')
        dependency = self.fenced()
        self.assertEqual(dependency['schema'], 'PAIR_RETENTION_PARENT_DEPENDENCIES_V1')
        self.assertEqual(dependency['life_binding_sha256'], sidecar.digest(self.plan['life_binding']))
        self.assertTrue(dependency['delivery_fenced'])
        self.assertEqual(dependency['inflight_deliveries'], 0)
        self.assertEqual(dependency['ledger_pins'], sidecar.ledger_pins(self.directory))
        self.assertEqual(before, sidecar.file_bytes(self.directory / 'STATE.json'))
        self.assertEqual(self.cpu.signals, [signal.SIGSTOP])
        self.assertEqual(self.calls, ['fence_check', 'fence_check'])
        self.actual_signal.assert_not_called()
        self.actual_ssh.assert_not_called()
        self.actual_launch.assert_not_called()

    def test_receiver_consumes_real_sidecar_dependency_schema(self):
        from research_loop.workers.post_recovery_pair_retention_receiver_20260919.receiver import PairReceiver
        self.fenced()
        receiving = SimpleNamespace(parent_dependency_receipt_path=self.transaction / 'PARENT_DEPENDENCIES.json',
            binding=self.plan['life_binding'])
        proof = PairReceiver.verify_parent_dependencies(receiving, self.plan['source_epoch'])
        self.assertEqual(proof['sha256'], sidecar.sha(self.transaction / 'PARENT_DEPENDENCIES.json'))

    def test_changed_source_refused_before_signal(self):
        (self.worker / 'parent_service.py').write_text('changed source')
        with self.assertRaisesRegex(ValueError, 'pinned_source'):
            self.fenced()
        self.assertFalse(self.cpu.signals)

    def test_wrong_native_or_CPU_scope_refused(self):
        for field, value in (('pid', 493500), ('argv', ['python', '-m', 'gpu.native'])):
            changed = deepcopy(self.plan)
            changed['old_parent'][field] = value
            with self.assertRaises(ValueError):
                sidecar.fence(changed, self.cpu, self.fake_remote)
        self.assertFalse(self.cpu.signals)

    def test_expired_or_unbounded_activation_refused(self):
        for deadline in (999, 9999):
            changed = dict(self.plan, not_after_unix=deadline)
            with self.assertRaises(ValueError):
                sidecar.fence(changed, self.cpu, self.fake_remote)
        self.assertFalse(self.cpu.signals)

    def test_supervisor_must_be_disabled_with_exact_pinned_manifest(self):
        manifest = sidecar.read(self.registry)
        manifest['enabled'] = True
        put(self.registry, manifest)
        self.plan['disabled_registry']['sha256'] = sidecar.sha(self.registry)
        with self.assertRaisesRegex(ValueError, 'disabled_registry'):
            self.fenced()
        self.assertFalse(self.cpu.signals)

    def test_busy_blocked_and_pending_turns_never_fenced(self):
        for field in ('provider_inflight', 'pending_turn', 'provider_blocked', 'publication_blocked', 'transport_blocked'):
            state = dict(self.state, **{field: 'preserved-unknown'})
            put(self.directory / 'STATE.json', state)
            with self.assertRaisesRegex(ValueError, 'unresolved_'):
                sidecar.drained(self.plan)
        self.assertFalse(self.cpu.signals)

    def test_due_turn_or_birth_opening_refuses_fence(self):
        for state in (dict(self.state, first_turn=True), dict(self.state, stage=0, last_parent_cycle=0)):
            put(self.directory / 'STATE.json', state)
            with self.assertRaisesRegex(ValueError, 'not_idle'):
                sidecar.drained(self.plan)

    def test_unknown_provider_attempt_and_orphan_result_rejected(self):
        turn = self.directory / 'turn_000002'
        put(turn / 'DISPATCH.json', dict(started=True))
        put(turn / 'FAILURE_DISPOSITION.json', dict(explicit_429=False))
        put(turn / 'http_error_response.txt', dict(error=dict(code=500)))
        with self.assertRaisesRegex(ValueError, 'unknown_provider'):
            sidecar.drained(self.plan)
        put(turn / 'RESULT.json', dict(response=dict(message='do not regenerate')))
        with self.assertRaisesRegex(ValueError, 'orphan_result'):
            sidecar.drained(self.plan)

    def test_explicit_429_budget_is_preserved_without_retry(self):
        turn = self.directory / 'turn_000002'
        put(turn / 'DISPATCH.json', dict(started=True))
        put(turn / 'FAILURE_DISPOSITION.json', dict(explicit_429=True))
        put(turn / 'http_error_response.txt', dict(error=dict(code='429')))
        state, deliveries = sidecar.drained(self.plan)
        self.assertEqual(state['provider_429_attempts'], 2)
        self.assertEqual(len(deliveries), 1)

    def test_fence_race_leaves_stopped_CPU_no_false_dependency(self):
        previous = self.cpu.wait_stopped
        def raced(expected, lock):
            previous(expected, lock)
            put(self.directory / 'STATE.json', dict(self.state, provider_inflight='uncertain'))
        self.cpu.wait_stopped = raced
        with self.assertRaisesRegex(ValueError, 'state_changed'):
            self.fenced()
        self.assertTrue(self.cpu.stopped)
        self.assertTrue((self.transaction / 'FENCE_BLOCKED.json').exists())
        self.assertFalse((self.transaction / 'PARENT_DEPENDENCIES.json').exists())
        self.assertEqual(self.cpu.signals, [signal.SIGSTOP])

    def test_fence_is_single_use_even_when_the_outcome_is_unknown(self):
        put(self.transaction / 'FENCE_CLAIM.json', dict(outcome='unknown'))
        with self.assertRaisesRegex(ValueError, 'claim_exists'):
            self.fenced()
        self.assertFalse(self.cpu.signals)

    def test_partial_ledger_and_symlink_rejected(self):
        partial = self.directory / 'STATE.partial'
        partial.write_text('partial')
        with self.assertRaisesRegex(ValueError, 'partial_ledger'):
            sidecar.ledger_pins(self.directory)
        partial.unlink()
        (self.directory / 'linked.json').symlink_to(self.directory / 'STATE.json')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            sidecar.ledger_pins(self.directory)

    def test_rebind_changes_only_native_preserving_cursor_policy_budget_and_authorship(self):
        receipt = self.committed()
        carried = sidecar.read(self.directory / 'STATE.json')
        self.assertEqual(carried, sidecar.rebound_state(self.state, receipt['approval']['new_native']))
        self.assertEqual(carried['deliveries'], self.state['deliveries'])
        self.assertEqual(carried['events'], self.state['events'])
        self.assertEqual(self.cpu.signals, [signal.SIGSTOP, signal.SIGKILL])
        self.assertFalse(receipt['successor_started'])
        self.assertEqual(self.calls, ['fence_check', 'fence_check', 'rebind_check', 'rebind_check'])

    def test_rebind_refuses_changed_ledger_before_CPU_retirement(self):
        self.fenced()
        approval = self.approved()
        put(self.turn / 'stdout.json', dict(changed=True))
        with self.assertRaisesRegex(ValueError, 'pinned_source_or_ledger'):
            sidecar.rebind(self.plan, approval, self.cpu, self.fake_remote)
        self.assertEqual(self.cpu.signals, [signal.SIGSTOP])

    def test_rebind_refuses_wrong_dependency_and_expired_approval(self):
        self.fenced()
        for field, value in (('dependency_sha256', 'wrong'), ('not_after_unix', 999), ('checkpoint_gate_passed', False)):
            approval = dict(self.approved(), **{field: value})
            with self.assertRaises(ValueError):
                sidecar.rebind(self.plan, approval, self.cpu, self.fake_remote)
        self.assertEqual(self.cpu.signals, [signal.SIGSTOP])

    def test_remote_LOADED_rejection_precedes_CPU_retirement(self):
        self.fenced()
        def rejected(*arguments):
            raise ValueError('actual_LOADED_required')
        with self.assertRaisesRegex(ValueError, 'actual_LOADED'):
            sidecar.rebind(self.plan, self.approved(), self.cpu, rejected)
        self.assertEqual(self.cpu.signals, [signal.SIGSTOP])

    def test_duplicate_rebind_cannot_retire_or_launch_again(self):
        self.committed()
        with self.assertRaisesRegex(ValueError, 'claim_exists'):
            sidecar.rebind(self.plan, self.approved(), self.cpu, self.fake_remote)
        self.assertEqual(len(self.cpu.signals), 2)

    def test_competing_publisher_lock_fails_closed_after_old_CPU_exit(self):
        self.fenced()
        with sidecar.publisher_lock(self.lock):
            with self.assertRaises(BlockingIOError):
                sidecar.rebind(self.plan, self.approved(), self.cpu, self.fake_remote)
        self.assertTrue(self.cpu.retired)
        self.assertEqual(sidecar.read(self.directory / 'STATE.json'), self.state)
        self.assertTrue((self.transaction / 'REBIND_BLOCKED.json').exists())

    def successor_environment(self, run):
        receipt = self.transaction / 'REBIND_RECEIPT.json'
        argv = ['/usr/bin/python3', '-B', str(self.worker / 'retention_sidecar.py'), 'serve',
            '--receipt', str(receipt), '--execute-sha256', sidecar.sha(receipt)]
        return patch.multiple(sidecar.service, run=run), patch.object(sidecar, 'lock_owners', return_value=[os.getpid()]), \
            patch.object(sidecar, 'process_identity', return_value=dict(argv=argv))

    def test_successor_uses_original_loop_and_truthful_process_argv(self):
        self.committed()
        receipt = self.transaction / 'REBIND_RECEIPT.json'
        def run(arm):
            binding = sidecar.service.remote(arm, dict(action='bind'))
            self.assertEqual(binding['native']['pid'], 99990003)
            sidecar.service.write(self.directory / 'PROCESS_successor.json', dict(argv=['old-wrong-argv']))
        patches = self.successor_environment(run)
        with patches[0], patches[1], patches[2]:
            sidecar.serve(receipt, sidecar.sha(receipt), self.fake_remote)
        process = sidecar.read(self.directory / 'PROCESS_successor.json')
        self.assertIn('serve', process['argv'])
        self.assertEqual(process['rebind_receipt']['sha256'], sidecar.sha(receipt))
        self.assertTrue((self.transaction / 'SUCCESSOR_ADMISSION.json').exists())

    def test_successor_never_converts_unknown_publish_outcome_into_retry(self):
        self.committed()
        receipt = self.transaction / 'REBIND_RECEIPT.json'
        def uncertain(plan, action, *positional, **arguments):
            if action == 'publish':
                raise TimeoutError('unknown network result')
            return self.fake_remote(plan, action, *positional, **arguments)
        def run(arm):
            binding = sidecar.service.remote(arm, dict(action='bind'))
            with self.assertRaises(TimeoutError):
                sidecar.service.remote(arm, dict(action='publish', delivery_id='a' * 64), binding['native'])
        patches = self.successor_environment(run)
        with patches[0], patches[1], patches[2]:
            sidecar.serve(receipt, sidecar.sha(receipt), uncertain)
        state = sidecar.read(self.directory / 'STATE.json')
        self.assertIsNotNone(state['publication_blocked'])
        self.assertEqual(state['deliveries'], self.state['deliveries'])

    def test_fence_recheck_is_read_only_and_rejects_new_ledger_files(self):
        self.fenced()
        path = self.transaction / 'PARENT_DEPENDENCIES.json'
        proof = sidecar.verify_fence(path, sidecar.sha(path), self.cpu)
        self.assertTrue(proof['delivery_fenced'])
        put(self.directory / 'NEW_LEDGER.json', dict(unknown=True))
        with self.assertRaisesRegex(ValueError, 'ledger_inventory'):
            sidecar.verify_fence(path, sidecar.sha(path), self.cpu)
        self.assertEqual(self.cpu.signals, [signal.SIGSTOP])

    def test_durable_send_claim_blocks_crash_or_timeout_replay(self):
        request = dict(action='publish', delivery_id='a' * 64)
        approval = dict(new_native=dict(pid=7))
        attempts = []
        def unknown(*arguments, **keywords):
            attempts.append(True)
            raise TimeoutError('unknown')
        with self.assertRaises(TimeoutError):
            sidecar.guarded_publication(self.plan, approval, request, unknown)
        with self.assertRaisesRegex(ValueError, 'unknown_sidecar_publication'):
            sidecar.guarded_publication(self.plan, approval, request, unknown)
        self.assertEqual(len(attempts), 1)

    def test_durable_ack_returns_same_receipt_without_a_second_send(self):
        request = dict(action='publish', delivery_id='a' * 64)
        approval = dict(new_native=dict(pid=7))
        first = sidecar.guarded_publication(self.plan, approval, request, self.fake_remote)
        second = sidecar.guarded_publication(self.plan, approval, request, self.fake_remote)
        self.assertEqual(first, second)
        self.assertEqual(self.calls, ['publish'])
        with self.assertRaisesRegex(ValueError, 'intent_changed'):
            sidecar.guarded_publication(self.plan, approval, dict(request, text='changed'), self.fake_remote)

    def test_native_rebound_state_never_resets_blockers_or_parent_history(self):
        original = dict(self.state, provider_blocked=dict(reason='unknown'), pending_turn='preserved')
        carried = sidecar.rebound_state(original, dict(pid=555))
        self.assertEqual({key: value for key, value in carried.items() if key != 'native'},
            {key: value for key, value in original.items() if key != 'native'})

    def test_unchanged_real_parent_loop_runs_one_synthetic_poll_without_provider_or_replay(self):
        self.committed()
        receipt = self.transaction / 'REBIND_RECEIPT.json'
        original = self.root / 'original'
        recovery = original / 'recovery'
        put(recovery / 'ALLOCATION_DATE_CORRECTION.json', dict(hard_end_unix=sidecar.CEILING,
            lease_end_unix=sidecar.CEILING + 21600))
        put(original / 'r232_pair/PARENT_SOURCE.py', dict(synthetic=True))
        put(self.root / 'gpu/orch_route_parent_campaign_providers.py', dict(synthetic=True))
        carried = sidecar.read(self.directory / 'STATE.json')
        ticks = iter([1000, 1000, 1000, sidecar.CEILING])
        clock = SimpleNamespace(time=lambda: next(ticks), sleep=lambda seconds: None)
        argv = ['/usr/bin/python3', '-B', str(self.worker / 'retention_sidecar.py'), 'serve',
            '--receipt', str(receipt), '--execute-sha256', sidecar.sha(receipt)]
        def observation(plan, action, *positional, **keywords):
            result = self.fake_remote(plan, action, *positional, **keywords)
            if action == 'poll':
                result.update(records=[], next_index=carried['next_index'], previous_sha256=carried['previous_sha256'], caught_up=True)
            return result
        with patch.multiple(sidecar.service, HERE=self.worker, REPO=self.root, ORIGINAL=original, RECOVERY=recovery, time=clock), \
                patch.object(sidecar.service, 'source_parent', return_value=SimpleNamespace()) as original_scaffold, \
                patch.object(sidecar, 'lock_owners', return_value=[os.getpid()]), \
                patch.object(sidecar, 'process_identity', return_value=dict(argv=argv)), \
                patch.dict(os.environ, NVIDIA_API_KEY='synthetic-never-sent'):
            sidecar.serve(receipt, sidecar.sha(receipt), observation)
        original_scaffold.assert_called_once()
        self.assertIn('poll', self.calls)
        self.assertNotIn('publish', self.calls)
        self.assertEqual(sidecar.read(self.directory / 'STATE.json'), carried)
        self.actual_ssh.assert_not_called()
        self.actual_launch.assert_not_called()
        self.actual_signal.assert_not_called()

    def test_Linux_check_rejects_wrong_boot_start_UID_argv_and_lock_owner(self):
        identity = dict(self.plan['old_parent'], state='S')
        for field, value in (('boot_id', 'other'), ('start_ticks', 'reused'), ('uid', 1), ('argv', ['native'])):
            with patch.object(sidecar, 'process_identity', return_value=dict(identity, **{field: value})):
                with self.assertRaisesRegex(ValueError, 'CPU_identity'):
                    sidecar.LinuxCPU().check(self.plan['old_parent'], self.lock)
        with patch.object(sidecar, 'process_identity', return_value=identity), patch.object(sidecar, 'lock_owners', return_value=[9]):
            with self.assertRaisesRegex(ValueError, 'lock_owner'):
                sidecar.LinuxCPU().check(self.plan['old_parent'], self.lock)


class ReceiverEvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=sidecar.HERE)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.life = self.root / 'life'
        (self.life / 'raw/stream/records').mkdir(parents=True)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.guard_path = self.root / 'new/GUARD.json'
        self.old_guard = self.root / 'old/GUARD.json'
        self.plan_path = self.root / 'new/PLAN.json'
        receiving_plan = dict(source_root=str(self.source), hard_end_unix=sidecar.CEILING)
        put(self.plan_path, receiving_plan)
        (self.source / 'gpu').mkdir()
        (self.source / 'gpu/runtime.py').write_text('synthetic receiving source')
        pins = {'gpu/runtime.py': sidecar.sha(self.source / 'gpu/runtime.py')}
        put(self.old_guard, dict(physical=0, hard_end_unix=sidecar.CEILING, source_pins={'old': 'hash'}, plan_path='/old/plan'))
        put(self.guard_path, dict(physical=0, hard_end_unix=sidecar.CEILING, source_pins=pins,
            plan_path=str(self.plan_path), plan_sha256=sidecar.sha(self.plan_path)))
        binding = dict(guard_path=str(self.old_guard), guard_sha256=sidecar.sha(self.old_guard), uid=1000)
        self.plan = dict(old_native=dict(root=str(self.life), journal_id='journal', pid=999999999, start_ticks='old', boot_id='boot'),
            life_binding=binding, source_epoch='epoch', until_unix=sidecar.CEILING)
        checkpoint = dict(adapter_state_sha256='adapter', optimizer_steps=3, base_sha256='base')
        state = dict(pending=None, sleep_frontier=1, rows=['all-authentic 鸟'], deadline_unix=sidecar.CEILING)
        saved = dict(state=state, sha256=remote.digest(state))
        self.records = []
        complete = self.record('SLEEP_COMPLETE', dict(status='COMPLETE', checkpoint=checkpoint, resume_state=saved, cycle=1))
        learned = self.record('R184_LEARN_COMPLETE', dict(checkpoint=checkpoint, cycle=1))
        parent_path = self.root / 'new/PARENT_REBIND_REQUIRED.json'
        put(parent_path, dict(dependency_proof=dict(sha256='dependency')))
        receiver = dict(source_epoch='epoch', same_journal_root=str(self.life / 'raw/stream'), plan=receiving_plan,
            plan_sha256=remote.digest(receiving_plan), parent_handoff_path=str(parent_path),
            artifact_pins={str(parent_path): sidecar.sha(parent_path)}, guard_path=str(self.guard_path))
        boundary = dict(complete_index=complete['index'], complete_sha256=complete['sha256'], learn_index=learned['index'],
            learn_sha256=learned['sha256'], checkpoint=checkpoint, resume_state=saved)
        self.token = dict(old_native_exited=True, life_binding_sha256=remote.digest(binding), epoch_id='epoch',
            deadline_unix=sidecar.CEILING, receiver=receiver, exact_complete=boundary, new_source_pins=pins)
        self.token['sha256'] = remote.digest(self.token)
        token_path = self.root / 'new/RETENTION_HANDOFF.json'
        put(token_path, self.token)
        adoption = self.record('RETENTION_SOURCE_ADOPTED', dict(schema='RETENTION_SOURCE_ADOPTION_V1', epoch_id='epoch',
            handoff_sha256=self.token['sha256'], source_pins_sha256=remote.digest(pins), complete_index=complete['index'],
            complete_sha256=complete['sha256'], state_sha256=saved['sha256'], deadline_unix=sidecar.CEILING,
            wall_extended=False, historical_rows_changed=False))
        loaded = self.record('LOADED', dict(pid=7777, resume=True, adapter_sha256='adapter', optimizer_steps=3, base_sha256='base'))
        self.approval = dict(new_native=dict(pid=7777, start_ticks='new', uid=1000, boot_id='boot', journal_id='journal',
            root=str(self.life), cwd=str(self.source), argv=['python', '-m', 'gpu.r232_recovery', 'native', '--config', str(self.guard_path)]),
            receiver_pins={str(token_path): sidecar.sha(token_path), str(self.guard_path): sidecar.sha(self.guard_path)},
            handoff_path=str(token_path), guard_path=str(self.guard_path), source_adoption=self.reference(adoption), loaded=self.reference(loaded))
        self.addCleanup(patch.stopall)
        self.identity = patch.object(remote, 'native_identity', side_effect=lambda value: value).start()
        self.signal = patch.object(signal, 'pidfd_send_signal', side_effect=AssertionError('no live signals')).start()

    def reference(self, record):
        return dict(index=record['index'], sha256=record['sha256'])

    def record(self, kind, document):
        index = len(self.records)
        record = dict(index=index, schema='R125_STREAM_JOURNAL_V1', journal_id='journal', kind=kind, document=document,
            previous_sha256=self.records[-1]['sha256'] if self.records else 'genesis')
        record['sha256'] = remote.digest(record)
        self.records.append(record)
        self.write_record(record)
        return record

    def write_record(self, record):
        directory = self.life / 'raw/stream/records'
        put(directory / f"{record['index']:020d}.json", record)
        put(directory / f"{record['index']:020d}.intent.json", dict(schema=record['schema'], journal_id=record['journal_id'],
            index=record['index'], previous_sha256=record['previous_sha256'], record_sha256=record['sha256']))

    def verify(self):
        return remote.verify_loaded(self.plan, self.approval, 'dependency')

    def test_actual_canonical_join_checks_COMPLETE_source_epoch_LOADED_without_loading_checkpoint(self):
        self.assertTrue(self.verify()['verified'])
        self.assertEqual(self.identity.call_count, 2)
        self.signal.assert_not_called()

    def test_changed_loaded_adapter_optimizer_pid_resume_or_base_is_rejected(self):
        original = deepcopy(self.records[-1])
        for field, value in (('adapter_sha256', 'other'), ('optimizer_steps', 9), ('pid', 999), ('resume', False), ('base_sha256', 'other')):
            altered = deepcopy(original)
            altered['document'][field] = value
            altered['sha256'] = remote.digest({key: value for key, value in altered.items() if key != 'sha256'})
            self.write_record(altered)
            self.approval['loaded'] = self.reference(altered)
            with self.assertRaisesRegex(ValueError, 'actual_LOADED'):
                self.verify()

    def test_wrong_dependency_cannot_authorize_LOADED(self):
        with self.assertRaisesRegex(ValueError, 'parent_dependency'):
            remote.verify_loaded(self.plan, self.approval, 'wrong')

    def test_guard_metadata_or_source_epoch_change_is_rejected(self):
        guard = sidecar.read(self.guard_path)
        guard['physical'] = 1
        put(self.guard_path, guard)
        self.approval['receiver_pins'][str(self.guard_path)] = sidecar.sha(self.guard_path)
        with self.assertRaisesRegex(ValueError, 'same_allocation'):
            self.verify()

    def test_missing_intent_never_becomes_a_LOADED_receipt(self):
        (self.life / 'raw/stream/records/00000000000000000003.intent.json').unlink()
        with self.assertRaises(FileNotFoundError):
            self.verify()

    def test_new_root_journal_host_or_same_incarnation_is_rejected(self):
        original = deepcopy(self.approval['new_native'])
        for field, value in (('root', '/other'), ('journal_id', 'other'), ('boot_id', 'other'), ('uid', 9)):
            self.approval['new_native'] = dict(original, **{field: value})
            with self.assertRaises(ValueError):
                self.verify()

    def test_dispatch_marker_without_acknowledgement_blocks_read_only_reconciliation(self):
        control = self.life / 'control'
        control.mkdir()
        (control / 'PARENT_unknown.dispatch').mkdir()
        cursor = dict(next_index=4, previous_sha256=self.records[-1]['sha256'])
        with self.assertRaisesRegex(ValueError, 'ambiguous_remote_dispatch'):
            remote.reconcile(str(self.life), dict(journal_id='journal'), cursor, [])

    def test_missing_or_changed_cursor_is_not_reset(self):
        with self.assertRaisesRegex(ValueError, 'record_hash'):
            remote.reconcile(str(self.life), dict(journal_id='journal'), dict(next_index=4, previous_sha256='wrong'), [])


if __name__ == '__main__':
    unittest.main()
