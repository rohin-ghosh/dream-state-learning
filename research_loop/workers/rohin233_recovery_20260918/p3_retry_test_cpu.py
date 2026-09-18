import copy
import fcntl
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

import p3_retry_endpoint as endpoint
import p3_retry_observe as observer
import p3_retry_waiter as waiter


class RetryFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.control = self.root / 'r233_lease_continuation_retry1/control'
        self.source = self.control.parent / 'source'
        self.cpu = self.root / 'r233_recovery'
        self.records = self.root / 'life/stream/records'
        for path in (self.control, self.source, self.cpu, self.records):
            path.mkdir(parents=True)
        for name, value in dict(ROOT=self.root, CONTROL=self.control, SOURCE=self.source,
                CPU=self.cpu, BINDING=self.cpu / 'P3_RETRY_BINDING.json').items():
            current = patch.object(observer, name, value)
            current.start()
            self.addCleanup(current.stop)
        current = patch.object(observer.time, 'time', return_value=observer.END_UNIX - 100)
        current.start()
        self.addCleanup(current.stop)
        self.state = dict(deadline_unix=observer.END_UNIX - 200, pending=None)
        complete = self.entry(5243, 'SLEEP_COMPLETE', dict(cycle=153, status='COMPLETE'))
        self.recovery = dict(journal_id=observer.JOURNAL_ID, old_native_absent=True,
            old_native_pid=598987, old_native_start_ticks='32509102',
            complete_path=str(self.records / f'{5243:020d}.json'), complete_sha256=complete['sha256'],
            old_head_index=5314, old_head_sha256='a' * 64, saved_state_sha256=observer.content_digest(self.state))
        self.write(self.control / 'RECOVERY.json', self.recovery)
        self.recovered = self.entry(5315, 'R233_P3_RECOVERED_BOUNDARY', dict(
            receipt_path=str(self.control / 'RECOVERY.json'), receipt_sha256=observer.digest(self.control / 'RECOVERY.json'),
            state=dict(state=self.state, sha256=observer.content_digest(self.state))), previous='a' * 64)
        self.write(self.control / 'RECOVERY_APPENDED.json', dict(index=5315, sha256=self.recovered['sha256']))
        wall_state = dict(self.state, deadline_unix=observer.END_UNIX)
        self.entry(5316, 'WALL_EXTENDED', dict(authorization=dict(new_deadline_unix=observer.END_UNIX),
            state=dict(state=wall_state, sha256=observer.content_digest(wall_state))))
        self.entry(5317, 'LOADED', dict(pid=777777, loaded_unix=observer.END_UNIX - 110,
            optimizer_steps=153, resume=True))
        self.source.joinpath('native.py').write_text('pass\n')
        self.write(self.control / 'PLAN.json', dict(source_root=str(self.source), hard_end_unix=observer.END_UNIX))
        self.write(self.control / 'LEASE.json', dict(hard_end_unix=observer.END_UNIX,
            lease_end_unix=observer.END_UNIX + 21600))
        self.guard = dict(hard_end_unix=observer.END_UNIX,
            source_pins={'native.py': observer.digest(self.source / 'native.py')})
        for name in ('plan', 'lease'):
            self.guard[name + '_path'] = str(self.control / (name.upper() + '.json'))
            self.guard[name + '_sha256'] = observer.digest(self.guard[name + '_path'])
        self.write(self.control / 'GUARD.json', self.guard)
        self.native = dict(pid=777777, start_ticks='123456', source=str(self.source),
            state='R', command_sha256='d' * 64, guard_argument_present=True)
        current = patch.object(observer, 'process', return_value=self.native)
        self.process = current.start()
        self.addCleanup(current.stop)

    def write(self, path, value):
        path.write_text(json.dumps(value, sort_keys=True) + '\n')

    def entry(self, index, kind, document, previous='b' * 64):
        value = dict(index=index, kind=kind, document=document, journal_id=observer.JOURNAL_ID,
            previous_sha256=previous)
        value['sha256'] = observer.content_digest(value)
        self.write(self.records / f'{index:020d}.json', value)
        return value


class ObserverTests(RetryFixture):
    def test_actual_retry_LOAD_and_wall_produce_binding_without_writes(self):
        before = {str(path): observer.digest(path) for path in self.root.rglob('*') if path.is_file()}
        evidence = observer.observe()
        self.assertEqual(evidence['status'], 'RETRY_LOADED_ALIVE_WALL_VERIFIED')
        self.assertEqual(evidence['binding']['loaded_index'], 5317)
        self.assertEqual(evidence['binding']['journal_id'], observer.JOURNAL_ID)
        self.assertEqual(before, {str(path): observer.digest(path) for path in self.root.rglob('*') if path.is_file()})

    def test_staged_and_replaying_do_not_bind(self):
        self.control.joinpath('RECOVERY_APPENDED.json').unlink()
        self.assertIsNone(observer.observe()['binding'])
        self.process.assert_not_called()
        self.control.joinpath('RECOVERY.json').unlink()
        self.assertEqual(observer.observe()['status'], 'WAITING_RETRY_CONTROL')

    def test_old_LOAD_alone_does_not_count(self):
        self.records.joinpath(f'{5317:020d}.json').unlink()
        self.entry(5299, 'LOADED', dict(pid=598987))
        self.assertIsNone(observer.observe()['loaded'])
        self.process.assert_not_called()

    def test_dead_process_never_binds(self):
        for actual in (None, dict(self.native, state='Z'), dict(self.native, state='X')):
            with self.subTest(actual=actual):
                self.process.return_value = actual
                self.assertEqual(observer.observe()['status'], 'RETRY_LOADED_BUT_NATIVE_EXITED_NO_PARENT')

    def test_state_scheduling_change_is_not_identity_change(self):
        self.process.side_effect = [self.native, dict(self.native, state='S')]
        self.assertIsNotNone(observer.observe()['binding'])

    def test_identity_or_guard_change_rejected(self):
        for key, value in (('pid', 888888), ('start_ticks', '654321'), ('source', '/elsewhere'),
                ('command_sha256', 'e' * 64), ('guard_argument_present', False), ('state', 'Z')):
            with self.subTest(key=key):
                self.process.side_effect = [self.native, dict(self.native, **{key: value})]
                with self.assertRaises(ValueError):
                    observer.observe()

    def test_source_manifest_mismatch_rejected(self):
        self.source.joinpath('native.py').write_text('changed\n')
        with self.assertRaisesRegex(ValueError, 'unchanged_guard_bound_native_source'):
            observer.observe()

    def test_recovery_record_must_match_immutable_receipt(self):
        changed = copy.deepcopy(self.recovered['document'])
        changed['state']['state']['pending'] = 'untrusted'
        value = self.entry(5315, 'R233_P3_RECOVERED_BOUNDARY', changed, previous='a' * 64)
        self.write(self.control / 'RECOVERY_APPENDED.json', dict(index=5315, sha256=value['sha256']))
        with self.assertRaisesRegex(ValueError, 'verified_original_or_retry'):
            observer.observe()

    def test_appended_hash_must_match_journal(self):
        self.write(self.control / 'RECOVERY_APPENDED.json', dict(index=5315, sha256='f' * 64))
        with self.assertRaisesRegex(ValueError, 'exact_appended_retry'):
            observer.observe()

    def test_wall_must_be_actual_and_within_bound(self):
        self.records.joinpath(f'{5316:020d}.json').unlink()
        with self.assertRaisesRegex(ValueError, 'LOAD_after_WALL'):
            observer.observe()

    def test_unresumed_LOAD_rejected(self):
        self.entry(5317, 'LOADED', dict(pid=777777, loaded_unix=0, optimizer_steps=0, resume=False))
        with self.assertRaisesRegex(ValueError, 'saved_boundary'):
            observer.observe()

    def test_record_checksum_rejected(self):
        path = self.records / f'{5317:020d}.json'
        value = observer.read(path)
        value['document']['pid'] = 123
        self.write(path, value)
        with self.assertRaisesRegex(ValueError, 'journal_record_integrity'):
            observer.observe()

    def test_immutable_binding_never_overwritten(self):
        path = self.cpu / 'P3_RETRY_BINDING.json'
        observer.immutable(path, {'pid': 1})
        observer.immutable(path, {'pid': 1})
        with self.assertRaisesRegex(ValueError, 'preserve_existing_immutable'):
            observer.immutable(path, {'pid': 2})
        self.assertEqual(observer.read(path), {'pid': 1})


class EndpointTests(RetryFixture):
    def test_original_and_retry_recovery_records_only(self):
        called = []
        snapshot = types.SimpleNamespace(_reduce=lambda state, value: called.append(value))
        original = copy.deepcopy(self.recovery)
        original.update(old_head_index=5296, old_head_sha256='c' * 64)
        receipts = {'original': (original, '1' * 64), 'retry': (self.recovery, '2' * 64)}
        endpoint.bind_recovery_reducer(snapshot, receipts)
        for label, (receipt, checksum) in receipts.items():
            value = copy.deepcopy(self.recovered)
            value.update(index=receipt['old_head_index'] + 1, previous_sha256=receipt['old_head_sha256'])
            value['document'].update(receipt_path=label, receipt_sha256=checksum)
            state = dict(pending='discarded', response='discarded', delivered={'existing': 5})
            snapshot._reduce(state, value)
            self.assertEqual(state, dict(pending=None, response=None, delivered={'existing': 5}))
        snapshot._reduce({}, {'kind': 'RESPONSE'})
        self.assertEqual(called, [{'kind': 'RESPONSE'}])
        value['document']['receipt_path'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'only_two_immutable'):
            snapshot._reduce({}, value)

    def test_reducer_rejects_wrong_head_receipt_or_state(self):
        checksum = observer.digest(self.control / 'RECOVERY.json')
        for changed in ('index', 'previous_sha256', 'receipt_sha256', 'state'):
            with self.subTest(changed=changed):
                value = copy.deepcopy(self.recovered)
                if changed == 'index':
                    value['index'] += 1
                elif changed == 'previous_sha256':
                    value['previous_sha256'] = '0' * 64
                elif changed == 'receipt_sha256':
                    value['document']['receipt_sha256'] = '0' * 64
                else:
                    value['document']['state']['state']['pending'] = 'tampered'
                with self.assertRaises(ValueError):
                    observer.verify_recovery_record(value, self.recovery, checksum)

    def test_exact_wall_and_incarnation_guard(self):
        binding = observer.observe()['binding']
        lease = observer.read(self.control / 'LEASE.json')
        endpoint.verify_bound(binding, self.guard, lease, observer.END_UNIX - 1)
        for changed in (dict(binding, pid=598987), dict(binding, loaded_index=5299),
                dict(binding, source='/wrong'), dict(binding, journal_id='wrong')):
            with self.assertRaises(ValueError):
                endpoint.verify_bound(changed, self.guard, lease, observer.END_UNIX - 1)
        with self.assertRaises(ValueError):
            endpoint.verify_bound(binding, self.guard, lease, observer.END_UNIX)
        with self.assertRaises(ValueError):
            endpoint.verify_bound(binding, self.guard, dict(lease, lease_end_unix=observer.END_UNIX), observer.END_UNIX - 1)

    def test_publish_revalidates_after_lock_and_has_no_opening_operation(self):
        binding = observer.observe()['binding']
        self.root.joinpath('r210').mkdir()
        calls = []
        publisher = types.ModuleType('gpu.orch_r127_pilot_console')
        publisher.publish_parent = lambda *args: calls.append('publish') or {'id': 'own-parent'}
        with patch.object(endpoint, 'configure', return_value=(None, binding)), \
                patch.object(endpoint.previous, 'ROOT', self.root), \
                patch.object(endpoint.previous, 'incarnation', side_effect=lambda source: calls.append('incarnation')), \
                patch.object(endpoint, 'verify_live', side_effect=lambda value: calls.append('live')), \
                patch.dict('sys.modules', {'gpu.orch_r127_pilot_console': publisher}), \
                patch('sys.stdin', io.StringIO(json.dumps(dict(physical=3, op='publish', message='Question?')))), \
                patch('sys.stdout', io.StringIO()):
            endpoint.main()
        self.assertEqual(calls, ['live', 'incarnation', 'publish'])
        for request in (dict(physical=3, op='open'), dict(physical=4, op='poll')):
            with self.assertRaises(ValueError):
                endpoint.previous.check_request(request)


class WaiterTests(RetryFixture):
    def setUp(self):
        super().setUp()
        current = patch.object(waiter, 'HERE', self.cpu)
        current.start()
        self.addCleanup(current.stop)
        self.evidence = observer.observe()
        self.evidence['binding_persisted'] = True

    def test_ready_requires_all_identity_and_actual_receipts(self):
        self.assertTrue(waiter.ready(self.evidence))
        for section, key, value in (('native', 'start_ticks', 'wrong'), ('loaded', 'pid', 598987),
                ('loaded', 'resume', False), ('wall_extended', 'sha256', 'wrong'),
                ('native', 'guard_argument_present', False), ('binding', 'loaded_index', 5299)):
            with self.subTest(section=section, key=key):
                evidence = copy.deepcopy(self.evidence)
                evidence[section][key] = value
                self.assertFalse(waiter.ready(evidence))
        self.assertFalse(waiter.ready(dict(status='STAGED', binding=None)))

    def test_poll_error_retries_but_staging_does_not_start(self):
        with patch.object(waiter, 'remote', side_effect=[RuntimeError('offline'),
                dict(status='REPLAY', binding=None), self.evidence, self.evidence]) as remote, \
                patch.object(waiter, 'start_parent') as start, patch.object(waiter, 'status'), \
                patch.object(waiter.time, 'sleep') as sleep:
            waiter.wait_for_load()
        self.assertEqual(sleep.call_args_list, [unittest.mock.call(30), unittest.mock.call(30)])
        start.assert_called_once_with(self.evidence)
        self.assertEqual(remote.call_args_list[-1], unittest.mock.call(bind=True))

    def test_attachment_failure_is_terminal_not_poll_retry(self):
        with patch.object(waiter, 'remote', return_value=self.evidence), \
                patch.object(waiter, 'start_parent', side_effect=RuntimeError('uncertain')) as start, \
                patch.object(waiter, 'status') as status, patch.object(waiter.time, 'sleep') as sleep:
            with self.assertRaises(RuntimeError):
                waiter.wait_for_load()
        start.assert_called_once()
        sleep.assert_not_called()
        self.assertEqual(status.call_args.args[0]['status'], 'ATTACHMENT_FAILED_NO_AUTORETRY')

    def test_binding_race_does_not_start(self):
        changed = copy.deepcopy(self.evidence)
        changed['binding']['start_ticks'] = 'changed'
        with patch.object(waiter, 'remote', side_effect=[self.evidence, changed]), \
                patch.object(waiter, 'start_parent') as start, patch.object(waiter, 'status'):
            with self.assertRaises(ValueError):
                waiter.wait_for_load()
        start.assert_not_called()

    def test_no_launch_if_validation_fails(self):
        with patch.object(waiter.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'validate')), \
                patch.object(waiter.subprocess, 'Popen') as launch:
            with self.assertRaises(subprocess.CalledProcessError):
                waiter.start_parent(self.evidence)
        launch.assert_not_called()
        self.assertFalse(self.cpu.joinpath('P3_RETRY_PARENT_ATTEMPT.json').exists())

    def test_success_starts_only_original_parent_entrypoint_with_inherited_environment(self):
        self.cpu.joinpath('p3_retry_parent.py').write_text('pass\n')
        parent = types.SimpleNamespace(pid=os.getpid(), poll=lambda: None)
        with patch.object(waiter.subprocess, 'run', return_value=types.SimpleNamespace(stdout='{}')) as validate, \
                patch.object(waiter.subprocess, 'Popen', return_value=parent) as launch, \
                patch.object(waiter.time, 'sleep'), patch.object(waiter, 'status') as status:
            waiter.start_parent(self.evidence)
        self.assertEqual(validate.call_args.args[0][-1], 'validate')
        self.assertEqual(launch.call_args.args[0][-2:], [str(self.cpu / 'p3_retry_parent.py'), 'serve'])
        self.assertTrue(launch.call_args.kwargs['start_new_session'])
        self.assertTrue(launch.call_args.kwargs['close_fds'])
        self.assertNotIn('env', launch.call_args.kwargs)
        self.assertTrue(self.cpu.joinpath('P3_RETRY_PARENT_ATTEMPT.json').is_file())
        receipt = observer.read(self.cpu / 'P3_RETRY_PARENT_STARTED.json')
        self.assertEqual(receipt['loaded_index'], 5317)
        self.assertFalse(receipt['publication_claim'])
        self.assertEqual(status.call_args.args[0]['status'], 'PARENT_PROCESS_STARTED_RENDER_PENDING')

    def test_spawn_failure_leaves_nonretryable_attempt_receipt(self):
        with patch.object(waiter.subprocess, 'run', return_value=types.SimpleNamespace(stdout='{}')), \
                patch.object(waiter.subprocess, 'Popen', side_effect=OSError('spawn failed')):
            with self.assertRaises(OSError):
                waiter.start_parent(self.evidence)
        with self.assertRaisesRegex(ValueError, 'no_ambiguous_attachment_retry'):
            waiter.start_parent(self.evidence)

    def test_waiter_lock_prevents_second_controller(self):
        with self.cpu.joinpath('P3_RETRY_WAITER.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with patch.object(waiter, 'wait_for_load') as poll:
                with self.assertRaises(BlockingIOError):
                    waiter.main()
        poll.assert_not_called()
        self.assertFalse(self.cpu.joinpath('P3_RETRY_WAITER_STARTED.json').exists())

    def test_public_projection_drops_operational_paths_and_binding(self):
        projected = waiter.public_evidence(self.evidence)
        encoded = json.dumps(projected)
        self.assertNotIn(str(self.root), encoded)
        self.assertNotIn('binding_sha256', encoded)
        self.assertEqual(projected['loaded']['index'], 5317)

    def test_existing_or_ambiguous_parent_never_duplicated(self):
        for name in ('P3_RETRY_PARENT_STARTED.json', 'P3_RETRY_PARENT_ATTEMPT.json', 'P3_CONTINUED_PARENT_STARTED.json'):
            with self.subTest(name=name):
                self.cpu.joinpath(name).write_text('{}')
                with patch.object(waiter.subprocess, 'Popen') as launch:
                    with self.assertRaises(ValueError):
                        waiter.start_parent(self.evidence)
                launch.assert_not_called()
                self.cpu.joinpath(name).unlink()

    def test_horizon_exits_without_remote_or_parent(self):
        with patch.object(waiter.time, 'time', return_value=observer.END_UNIX), \
                patch.object(waiter, 'remote') as remote, patch.object(waiter, 'start_parent') as start, \
                patch.object(waiter, 'status') as status:
            waiter.wait_for_load()
        remote.assert_not_called()
        start.assert_not_called()
        self.assertEqual(status.call_args.args[0]['status'], 'LEASE_AWARE_WAITER_HORIZON_REACHED_NO_PARENT')

    def test_parent_uses_fixed_loader_original_ledger_and_no_native_control(self):
        source = Path(__file__).with_name('p3_retry_parent.py').read_text()
        self.assertIn('p3_lease_parent.load_on_renewed_wall()', source)
        self.assertIn("output = module.base.OWN / 'r210_parent3'", source)
        self.assertIn('module.serve(3)', source)
        self.assertIn("reasoning_effort='xhigh', cadence_responses=1", source)
        for name in ('p3_retry_observe.py', 'p3_retry_endpoint.py', 'p3_retry_parent.py', 'p3_retry_waiter.py'):
            text = Path(__file__).with_name(name).read_text()
            for forbidden in ('os.kill(', 'SIGSTOP', 'SIGTERM', 'cuda.', 'systemctl', 'nvidia-smi'):
                self.assertNotIn(forbidden, text)


if __name__ == '__main__':
    unittest.main()
