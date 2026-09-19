"""Offline regression tests; all process, signal and patch execution is mocked."""

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import signal
import subprocess
import tempfile
import types
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('c2_scoped_handoff', HERE / 'handoff.py')
handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handoff)


def ready(**changes):
    return dict(dict(pending=[], last_status='SILENT', signature='fixture-ledger',
                     reserved=564, failures=[dict(error_type='HTTPError', retry=False)]), **changes)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='c2-handoff-test-')
        self.addCleanup(self.temporary.cleanup)
        self.target = Path(self.temporary.name) / 'seed' / 'MANIFEST.json'
        self.seed, self.seed_bytes, self.install_bytes, original = handoff.load_bundle()
        self.validator = types.SimpleNamespace(
            no_question_bank=original.no_question_bank,
            seed_preflight=mock.Mock(side_effect=lambda seed: ready()))
        self.states = {325487: 'S', 361010: 'S'}
        self.overrides = {}
        self.events = []
        self.handlers = {}
        self.on_stop = lambda: None
        self.on_term = lambda: None
        self.on_continue = lambda: None
        self.descriptors = {325487: 101, 361010: 202}

        def patcher(target, name, **options):
            patch = mock.patch.object(target, name, **options)
            value = patch.start()
            self.addCleanup(patch.stop)
            return value

        patcher(handoff, 'TARGET', new=self.target)
        patcher(handoff, 'load_bundle', return_value=(
            self.seed, self.seed_bytes, self.install_bytes, self.validator))
        self.identity = patcher(handoff, 'process_identity', side_effect=self.fake_identity)
        self.open_pidfd = patcher(handoff.os, 'pidfd_open', side_effect=lambda pid, flags: self.descriptors[pid])
        self.close = patcher(handoff.os, 'close')
        self.poller = mock.Mock()
        self.poller.poll.return_value = []
        patcher(handoff.select, 'poll', return_value=self.poller)
        patcher(handoff.fcntl, 'flock')
        self.send = patcher(handoff.signal, 'pidfd_send_signal', side_effect=self.fake_signal)
        self.numeric_kill = patcher(handoff.os, 'kill', side_effect=AssertionError('numeric kill forbidden'))
        self.handler_changes = patcher(handoff.signal, 'signal', side_effect=self.set_handler)
        patcher(handoff.signal, 'getitimer', return_value=(0.0, 0.0))
        self.timer = patcher(handoff.signal, 'setitimer')
        self.patch_process = patcher(handoff.subprocess, 'run', side_effect=self.fake_patch)
        self.which = patcher(handoff.shutil, 'which', return_value='/fixture/apply_patch')
        patcher(handoff.time, 'time', return_value=1789800000.0)
        patcher(handoff.time, 'sleep')

    def fake_identity(self, expected):
        return dict(dict(expected, state=self.states[expected['pid']], threads=1, children=[]),
                    **self.overrides.get(expected['pid'], {}))

    def set_handler(self, number, handler):
        previous = self.handlers.get(number, signal.SIG_DFL)
        self.handlers[number] = handler
        return previous

    def fake_signal(self, descriptor, number):
        self.assertEqual(descriptor, 101, 'only the original publisher pidfd can receive signals')
        self.events.append(number)
        if number == signal.SIGSTOP:
            self.states[325487] = 'T'
            self.on_stop()
        elif number == signal.SIGTERM:
            self.on_term()
        elif number == signal.SIGCONT:
            self.states[325487] = 'S'
            self.on_continue()
        else:
            self.fail('unexpected signal')

    def fake_patch(self, command, **options):
        self.events.append('apply_patch')
        self.assertEqual(command, ['/fixture/apply_patch'])
        self.assertEqual(options['input'], self.install_bytes)
        self.assertEqual(options['cwd'], handoff.REPO)
        self.assertEqual(options['env'], {'PATH': '/usr/bin:/bin'})
        self.assertTrue(options['check'])
        self.assertEqual(options['timeout'], 3.0)
        self.assertEqual(self.states[325487], 'T')
        self.target.parent.mkdir()
        self.target.write_bytes(self.seed_bytes)
        return subprocess.CompletedProcess(command, 0)

    def execute(self):
        return handoff.run(execute=True, seed_sha256=handoff.SEED_SHA256,
                           install_sha256=handoff.INSTALL_SHA256)

    def assert_resumed_without_term(self):
        self.assertIn(signal.SIGSTOP, self.events)
        self.assertEqual(self.events[-1], signal.SIGCONT)
        self.assertNotIn(signal.SIGTERM, self.events)
        self.assertEqual(self.states[325487], 'S')
        self.numeric_kill.assert_not_called()

    def test_default_is_read_only_and_closes_both_pidfds(self):
        report = handoff.run()
        self.assertEqual(report['status'], 'DRY_RUN_NOT_AUTHORIZATION')
        self.assertTrue(report['settled_current_ledger'])
        self.send.assert_not_called()
        self.patch_process.assert_not_called()
        self.handler_changes.assert_not_called()
        self.assertEqual(self.close.call_args_list, [mock.call(202), mock.call(101)])
        self.assertFalse(self.target.exists())

    def test_execute_requires_both_exact_hashes_before_reading_processes(self):
        for seed_hash, patch_hash in ((None, None), (handoff.SEED_SHA256, None),
                                      ('changed', handoff.INSTALL_SHA256)):
            with self.subTest(seed_hash=seed_hash, patch_hash=patch_hash):
                with self.assertRaisesRegex(ValueError, 'exact_approved_hashes'):
                    handoff.run(execute=True, seed_sha256=seed_hash, install_sha256=patch_hash)
        self.open_pidfd.assert_not_called()
        self.send.assert_not_called()

    def test_success_is_stop_patch_term_continue_only_original_publisher(self):
        report = self.execute()
        self.assertEqual(self.events, [signal.SIGSTOP, 'apply_patch', signal.SIGTERM, signal.SIGCONT])
        self.assertEqual(report['status'], 'OLD_PUBLISHER_TERM_REQUESTED')
        self.assertFalse(report['old_publisher_exit_observed'])
        self.assertFalse(report['successor_verified'])
        self.assertFalse(report['native_checked'])
        self.assertEqual(report['ledger']['reserved'], 564)
        self.assertEqual(self.target.read_bytes(), self.seed_bytes)
        self.assertEqual(self.open_pidfd.call_args_list, [mock.call(325487, 0), mock.call(361010, 0)])
        self.assertTrue(all(handler == signal.SIG_DFL for handler in self.handlers.values()))
        self.assertEqual(self.timer.call_args_list[-1], mock.call(signal.ITIMER_REAL, 0.0))

    def test_not_ready_precheck_never_pauses_or_retries_failures(self):
        for ledger in (ready(pending=[{'kind': 'publication_consumption_unknown'}]),
                       ready(last_status='MISSING'), ready(last_status=None)):
            with self.subTest(ledger=ledger):
                self.validator.seed_preflight.side_effect = lambda seed: ledger
                report = self.execute()
                self.assertEqual(report['status'], 'NOT_READY')
        self.send.assert_not_called()
        self.patch_process.assert_not_called()

    def test_readiness_race_after_stop_resumes_without_install(self):
        for ledger in (ready(pending=[{'kind': 'incomplete_or_unknown_attempt'}]),
                       ready(last_status='MISSING')):
            with self.subTest(ledger=ledger):
                self.events.clear()
                self.validator.seed_preflight.side_effect = [ready(), ledger]
                with self.assertRaisesRegex(ValueError, 'frozen_ledger_not_settled'):
                    self.execute()
                self.assert_resumed_without_term()
        self.patch_process.assert_not_called()

    def test_pin_failure_before_and_after_stop_fails_closed(self):
        self.validator.seed_preflight.side_effect = ValueError('pinned_source_changed')
        with self.assertRaisesRegex(ValueError, 'pinned_source_changed'):
            self.execute()
        self.send.assert_not_called()
        self.validator.seed_preflight.side_effect = [ready(), ValueError('pinned_source_changed')]
        with self.assertRaisesRegex(ValueError, 'pinned_source_changed'):
            self.execute()
        self.assert_resumed_without_term()

    def test_seed_and_install_are_rehashed_inside_pause(self):
        for changed in (handoff.SEED, handoff.INSTALL):
            self.events.clear()

            def verify(path, expected):
                if path == changed:
                    raise ValueError('changed_pinned_file')
                return b'unused'

            with self.subTest(changed=changed), mock.patch.object(handoff, 'checked_bytes', side_effect=verify):
                with self.assertRaisesRegex(ValueError, 'changed_pinned_file'):
                    self.execute()
                self.assert_resumed_without_term()

    def test_exact_identity_fields_required_for_both_processes(self):
        for pid in (325487, 361010):
            for field, value in (('start_ticks', 'wrong'), ('cwd', '/elsewhere'), ('argv', ['wrong'])):
                with self.subTest(pid=pid, field=field):
                    self.overrides = {pid: {field: value}}
                    with self.assertRaisesRegex(ValueError, 'identity_mismatch'):
                        self.execute()
        self.send.assert_not_called()

    def test_already_stopped_process_is_not_resumed_by_us(self):
        self.states[325487] = 'T'
        with self.assertRaisesRegex(ValueError, 'required_state'):
            self.execute()
        self.send.assert_not_called()

    def test_unavailable_pidfd_never_falls_back_to_numeric_pid(self):
        self.open_pidfd.side_effect = OSError('pidfd unsupported')
        with self.assertRaisesRegex(OSError, 'unsupported'):
            self.execute()
        self.send.assert_not_called()
        self.numeric_kill.assert_not_called()

    def test_dead_pidfd_rejects_reused_proc_identity(self):
        self.poller.poll.return_value = [(101, handoff.select.POLLIN)]
        with self.assertRaisesRegex(ValueError, 'bound_process_exited'):
            self.execute()
        self.identity.assert_not_called()
        self.send.assert_not_called()

    def test_pid_reuse_after_stop_still_continues_only_original_pidfd(self):
        self.on_stop = lambda: self.overrides.update({325487: {'start_ticks': 'reused'}})
        with self.assertRaisesRegex(ValueError, 'identity_mismatch'):
            self.execute()
        self.assert_resumed_without_term()

    def test_child_and_thread_checks_prevent_uncontained_inflight_work(self):
        for fields in ({'children': ['400000']}, {'threads': 2}):
            with self.subTest(fields=fields):
                self.overrides = {325487: fields}
                with self.assertRaisesRegex(ValueError, 'inflight_child'):
                    self.execute()
        self.send.assert_not_called()

    def test_child_spawn_race_is_checked_again_while_stopped(self):
        self.on_stop = lambda: self.overrides.update({325487: {'children': ['400000']}})
        with self.assertRaisesRegex(ValueError, 'inflight_child'):
            self.execute()
        self.assert_resumed_without_term()

    def test_stop_ack_timeout_resumes(self):
        self.on_stop = lambda: self.states.update({325487: 'S'})
        with mock.patch.object(handoff.time, 'monotonic', side_effect=[0, 2]):
            with self.assertRaisesRegex(ValueError, 'stop_not_observed'):
                self.execute()
        self.assert_resumed_without_term()

    def test_uncertain_stop_syscall_exception_also_continues(self):
        def uncertain_stop():
            raise OSError('uncertain stop syscall')

        self.on_stop = uncertain_stop
        with self.assertRaisesRegex(OSError, 'uncertain stop'):
            self.execute()
        self.assert_resumed_without_term()

    def test_patch_failure_is_not_retried_and_always_resumes(self):
        self.patch_process.side_effect = subprocess.CalledProcessError(1, ['apply_patch'])
        with self.assertRaises(subprocess.CalledProcessError):
            self.execute()
        self.assert_resumed_without_term()
        self.assertEqual(self.patch_process.call_count, 1)

    def test_partial_seed_on_patch_failure_is_preserved_for_owner_reconciliation(self):
        def partial_failure(*args, **kwargs):
            self.target.parent.mkdir()
            self.target.write_bytes(self.seed_bytes[:100])
            raise subprocess.CalledProcessError(1, ['apply_patch'])

        self.patch_process.side_effect = partial_failure
        with self.assertRaises(subprocess.CalledProcessError):
            self.execute()
        self.assert_resumed_without_term()
        self.assertEqual(self.target.read_bytes(), self.seed_bytes[:100])
        self.assertEqual(self.patch_process.call_count, 1)
        with self.assertRaisesRegex(ValueError, 'already_exists_owner_must_reconcile'):
            self.execute()
        self.assertEqual(self.patch_process.call_count, 1)

    def test_patch_timeout_after_complete_install_does_not_claim_rollback(self):
        def installed_then_timeout(*args, **kwargs):
            self.fake_patch(*args, **kwargs)
            raise subprocess.TimeoutExpired(['apply_patch'], 3.0)

        self.patch_process.side_effect = installed_then_timeout
        with self.assertRaises(subprocess.TimeoutExpired):
            self.execute()
        self.assert_resumed_without_term()
        self.assertEqual(self.target.read_bytes(), self.seed_bytes)
        self.assertEqual(self.patch_process.call_count, 1)

    def test_keyboard_interrupt_in_patch_resumes(self):
        self.patch_process.side_effect = KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            self.execute()
        self.assert_resumed_without_term()

    def test_term_hup_int_and_alarm_raise_into_resume_cleanup(self):
        for number in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT, signal.SIGALRM):
            with self.subTest(number=number):
                self.events.clear()
                self.patch_process.side_effect = lambda *args, **kwargs: self.handlers[number](number, None)
                with self.assertRaises(InterruptedError):
                    self.execute()
                self.assert_resumed_without_term()

    def test_repeated_interrupt_during_cleanup_does_not_skip_continue(self):
        self.patch_process.side_effect = KeyboardInterrupt
        self.on_continue = lambda: self.handlers[signal.SIGTERM](signal.SIGTERM, None)
        with self.assertRaises(KeyboardInterrupt):
            self.execute()
        self.assert_resumed_without_term()

    def test_term_failure_still_continues(self):
        def term_failure():
            raise PermissionError('term denied')

        self.on_term = term_failure
        with self.assertRaisesRegex(PermissionError, 'term denied'):
            self.execute()
        self.assertEqual(self.events[-2:], [signal.SIGTERM, signal.SIGCONT])
        self.assertEqual(self.states[325487], 'S')

    def test_exited_original_during_cleanup_is_safe_without_retargeting(self):
        self.patch_process.side_effect = ValueError('original exited')

        def already_exited():
            raise ProcessLookupError('original pidfd is dead')

        self.on_continue = already_exited
        with self.assertRaisesRegex(ValueError, 'original exited'):
            self.execute()
        self.assert_resumed_without_term()

    def test_resume_permission_failure_is_reported_not_silently_swallowed(self):
        self.patch_process.side_effect = ValueError('patch failure')

        def denied():
            raise PermissionError('cannot resume')

        self.on_continue = denied
        with self.assertRaisesRegex(PermissionError, 'cannot resume'):
            self.execute()
        self.assertEqual(self.events[-1], signal.SIGCONT)

    def test_changed_supervisor_after_install_prevents_term(self):
        def install_then_supervisor_changes(*args, **kwargs):
            self.fake_patch(*args, **kwargs)
            self.overrides[361010] = {'start_ticks': 'reused'}

        self.patch_process.side_effect = install_then_supervisor_changes
        with self.assertRaisesRegex(ValueError, 'identity_mismatch'):
            self.execute()
        self.assert_resumed_without_term()
        self.assertTrue(self.target.exists(), 'no unapproved automatic rollback')

    def test_external_ledger_change_after_install_prevents_term_without_faking_receipts(self):
        self.validator.seed_preflight.side_effect = [ready(), ready(), ready(signature='external-change')]
        with self.assertRaisesRegex(ValueError, 'ledger_changed_after_install'):
            self.execute()
        self.assert_resumed_without_term()
        self.assertEqual(list(self.target.parent.iterdir()), [self.target])

    def test_wrong_installed_bytes_prevent_term(self):
        def corrupt_install(*args, **kwargs):
            self.fake_patch(*args, **kwargs)
            self.target.write_bytes(b'not the seed')

        self.patch_process.side_effect = corrupt_install
        with self.assertRaisesRegex(ValueError, 'installed_seed_bytes_mismatch'):
            self.execute()
        self.assert_resumed_without_term()

    def test_existing_seed_and_symlink_parent_are_never_overwritten(self):
        self.target.parent.mkdir()
        self.target.write_bytes(b'existing')
        with self.assertRaisesRegex(ValueError, 'already_exists'):
            self.execute()
        self.assertEqual(self.target.read_bytes(), b'existing')
        with mock.patch.object(handoff, 'TARGET', new=Path(self.temporary.name) / 'link' / 'MANIFEST.json'):
            (Path(self.temporary.name) / 'link').symlink_to(self.target.parent)
            with self.assertRaisesRegex(ValueError, 'symlinks'):
                self.execute()
        self.send.assert_not_called()

    def test_missing_apply_patch_does_not_pause(self):
        self.which.return_value = None
        with self.assertRaisesRegex(ValueError, 'apply_patch_required'):
            self.execute()
        self.send.assert_not_called()


class ArtifactAndLedgerTests(unittest.TestCase):
    def setUp(self):
        self.seed, self.seed_bytes, self.install_bytes, self.validator = handoff.load_bundle()
        self.temporary = tempfile.TemporaryDirectory(prefix='c2-handoff-ledger-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def put(self, path, document):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.validator.encoded(document))

    def test_exact_seed_patch_and_candidate_are_bound_without_importing_live_service(self):
        self.assertEqual(hashlib.sha256(self.seed_bytes).hexdigest(), handoff.SEED_SHA256)
        self.assertEqual(hashlib.sha256(self.install_bytes).hexdigest(), handoff.INSTALL_SHA256)
        self.assertEqual(self.seed['local_source_sha256'][str(handoff.CANDIDATE)], handoff.CANDIDATE_SHA256)
        self.assertEqual(self.install_bytes.count(b'*** Add File:'), 1)
        self.assertNotIn(b'*** Update File:', self.install_bytes)

    def test_any_changed_artifact_is_rejected_before_execution(self):
        for name in ('SEED', 'INSTALL', 'CANDIDATE'):
            damaged = self.root / name
            damaged.write_bytes(getattr(handoff, name).read_bytes() + b'\n')
            with self.subTest(name=name), mock.patch.object(handoff, name, new=damaged):
                with self.assertRaisesRegex(ValueError, 'changed_pinned_file'):
                    handoff.load_bundle()

    def test_real_validator_checks_all_seed_pins(self):
        source = self.root / 'source.py'
        source.write_bytes(b'fixture')
        pins = {'local_source_sha256': {str(source): hashlib.sha256(b'fixture').hexdigest()}}
        self.validator.check_pins(pins)
        source.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'pinned_source_changed'):
            self.validator.check_pins(pins)

    def test_questions_bank_keys_including_null_and_nested_are_rejected(self):
        for config in ({'questions_only_bank_path': None},
                       {'nested': [{'questions_only_bank_path': '/bank'}]},
                       {'nested': {'questions_only_first_id': None}}):
            with self.subTest(config=config), self.assertRaisesRegex(ValueError, 'question_bank_mode_conflicts'):
                self.validator.no_question_bank(config)

    def test_published_requires_real_bound_delivery_and_never_writes_it(self):
        self.put(self.root / 'STARTED.json', {'branch': 'C2'})
        attempt = self.root / 'parent_000001'
        self.put(attempt / 'SOURCE.json', {'response_count': 564})
        result = attempt / 'RESULT.json'
        self.put(result, {'status': 'PUBLISHED', 'inbox_publication': {'id': 'actual-id'}})
        config = dict(branch='C2', start_after_response_count=560)
        before = {path: path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        ledger = self.validator.ledger(self.root, config)
        self.assertFalse(handoff.settled(ledger))
        self.assertEqual(ledger['pending'][0]['kind'], 'publication_consumption_unknown')
        self.assertEqual(before, {path: path.read_bytes() for path in self.root.rglob('*') if path.is_file()})
        self.put(attempt / 'DELIVERED.json', dict(status='COMPLETE', inbox_id='actual-id',
                                               result_sha256=self.validator.sha(result)))
        self.assertTrue(handoff.settled(self.validator.ledger(self.root, config)))
        self.put(attempt / 'DELIVERED.json', dict(status='COMPLETE', inbox_id='wrong',
                                               result_sha256=self.validator.sha(result)))
        with self.assertRaisesRegex(ValueError, 'delivery_bound_to_actual_publication'):
            self.validator.ledger(self.root, config)

    def test_historical_http_failures_remain_reserved_but_last_failure_blocks_handoff(self):
        self.put(self.root / 'STARTED.json', {'branch': 'C2'})
        self.put(self.root / 'parent_000001/SOURCE.json', {'response_count': 564})
        self.put(self.root / 'parent_000001/RESULT.json', dict(status='MISSING', error_type='HTTPError'))
        config = dict(branch='C2', start_after_response_count=560)
        self.assertFalse(handoff.settled(self.validator.ledger(self.root, config)))
        self.put(self.root / 'parent_000002/SOURCE.json', {'response_count': 565})
        self.put(self.root / 'parent_000002/RESULT.json', {'status': 'SILENT'})
        ledger = self.validator.ledger(self.root, config)
        self.assertTrue(handoff.settled(ledger))
        self.assertEqual(ledger['reserved'], 565)
        self.assertEqual(ledger['counts']['MISSING'], 1)
        self.assertFalse(ledger['failures'][0]['retry'])
        (self.root / 'parent_000003').mkdir()
        self.assertFalse(handoff.settled(self.validator.ledger(self.root, config)))


class ProcessReaderAndCliTests(unittest.TestCase):
    def test_proc_reader_only_reads_identity_and_children_not_environment(self):
        fields = ['0'] * 50
        fields[0], fields[17], fields[19] = 'S', '1', '753205'
        stat = '325487 (publisher with ) brackets) ' + ' '.join(fields)
        paths = []

        def read_text(path):
            paths.append(path)
            return '' if path.name == 'children' else stat

        with mock.patch.object(Path, 'read_text', autospec=True, side_effect=read_text), \
                mock.patch.object(Path, 'read_bytes', return_value='\0'.join(handoff.PUBLISHER['argv']).encode() + b'\0'), \
                mock.patch.object(handoff.os, 'readlink', return_value=handoff.PUBLISHER['cwd']):
            actual = handoff.process_identity(handoff.PUBLISHER)
        self.assertEqual(actual['start_ticks'], '753205')
        self.assertEqual(actual['argv'], handoff.PUBLISHER['argv'])
        self.assertEqual(actual['threads'], 1)
        self.assertEqual([path.name for path in paths], ['stat', 'children', 'stat'])

    def test_changed_start_ticks_during_proc_read_are_rejected(self):
        fields = ['0'] * 50
        fields[0], fields[17], fields[19] = 'S', '1', '753205'
        before = '325487 (publisher) ' + ' '.join(fields)
        fields[19] = 'different'
        after = '325487 (publisher) ' + ' '.join(fields)
        with mock.patch.object(Path, 'read_text', side_effect=[before, '', after]), \
                mock.patch.object(Path, 'read_bytes', return_value=b'ignored\0'), \
                mock.patch.object(handoff.os, 'readlink', return_value=handoff.PUBLISHER['cwd']):
            with self.assertRaisesRegex(ValueError, 'process_changed_during_proc_read'):
                handoff.process_identity(handoff.PUBLISHER)

    def test_cli_default_is_dry_and_requires_exact_hashes_for_execute(self):
        with mock.patch.object(handoff, 'run', return_value=dict(settled_current_ledger=True)) as run:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(handoff.main([]), 0)
            run.assert_called_once_with(execute=False, seed_sha256=None, install_sha256=None)
            run.reset_mock()
            for arguments in (['--execute'], ['--pid', '1'], ['--signal', 'TERM'],
                              ['--execute', '--seed-sha256', 'wrong']):
                with self.subTest(arguments=arguments), redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        handoff.main(arguments)
            run.assert_not_called()

    def test_cli_errors_explicitly_require_install_reconciliation(self):
        output = io.StringIO()
        with mock.patch.object(handoff, 'run', side_effect=ValueError('uncertain_install')), redirect_stdout(output):
            self.assertEqual(handoff.main([]), 2)
        report = json.loads(output.getvalue())
        self.assertEqual(report['status'], 'REFUSED_OR_INTERRUPTED')
        self.assertTrue(report['inspect_seed_install_before_any_retry'])


if __name__ == '__main__':
    unittest.main()
