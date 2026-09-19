import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import register
import restart
import runner


class RestartTests(unittest.TestCase):
    def test_live_parent_causes_no_preflight_no_exec(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'HERE', Path(directory)), \
                patch.object(restart, 'active_parent', return_value=True), \
                patch.object(restart, 'validate_prior') as validate, \
                patch.object(restart.preflight, 'main') as preflight, \
                patch.object(restart.os, 'execv') as execute:
            self.assertEqual(restart.main(), 75)
            validate.assert_not_called()
            preflight.assert_not_called()
            execute.assert_not_called()

    def test_reused_pid_from_another_boot_is_not_live_owner(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'HERE', Path(directory)):
            expected = dict(pid=1234, start_ticks='123', boot_id='old')
            runner.save(Path(directory) / 'PROCESS.json', dict(process=expected))
            with patch.object(runner, 'process', return_value=dict(expected, boot_id='new', state='S')):
                self.assertFalse(restart.active_parent())

    def test_expired_lease_refuses_before_source_or_provider(self):
        with patch.object(restart.time, 'time', return_value=restart.UNTIL), patch.object(runner, 'sha') as digest:
            with self.assertRaisesRegex(ValueError, 'lease_expired'):
                restart.validate_prior()
            digest.assert_not_called()

    def test_preflight_failure_is_sanitized_and_never_executes(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'HERE', Path(directory)), \
                patch.object(restart, 'active_parent', return_value=False), \
                patch.object(restart, 'validate_prior'), patch.object(restart, 'preserve_previous'), \
                patch.object(restart.preflight, 'main', side_effect=ValueError('do-not-persist-sensitive-detail')), \
                patch.object(restart.os, 'execv') as execute:
            self.assertEqual(restart.main(), 1)
            stored = (Path(directory) / 'RESTART_LAST_RESULT.json').read_text()
            self.assertNotIn('do-not-persist', stored)
            self.assertEqual(json.loads(stored)['phase'], 'FRESH_NATIVE_LEDGER_PREFLIGHT')
            execute.assert_not_called()

    def test_success_refreshes_preflight_before_same_pid_exec(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'HERE', Path(directory)), \
                patch.object(restart, 'active_parent', return_value=False), \
                patch.object(restart, 'validate_prior', side_effect=lambda: calls.append('validate')), \
                patch.object(restart, 'preserve_previous', side_effect=lambda: calls.append('archive')), \
                patch.object(restart.preflight, 'main', side_effect=lambda: calls.append('preflight')), \
                patch.object(restart.time, 'time', return_value=1), \
                patch.object(runner, 'sha', return_value='digest'), \
                patch.object(restart.os, 'execv', side_effect=SystemExit(123)) as execute:
            with self.assertRaises(SystemExit) as caught:
                restart.main()
            self.assertEqual(caught.exception.code, 123)
            self.assertEqual(calls, ['validate', 'archive', 'preflight'])
            execute.assert_called_once_with('/usr/bin/python3', ['/usr/bin/python3', '-B', str(Path(directory) / 'runner.py')])


class RegistrationTests(unittest.TestCase):
    def test_registration_is_atomic_idempotent_and_never_overwrites_conflict(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'HERE', Path(directory)):
            target = Path(directory) / 'registry.json'
            document = dict(name='p3-parent', enabled=True)
            self.assertTrue(register.publish_registry(document, target))
            self.assertFalse(register.publish_registry(document, target))
            with self.assertRaisesRegex(ValueError, 'conflicting'):
                register.publish_registry(dict(document, enabled=False), target)
            self.assertEqual(json.loads(target.read_text()), document)

    def test_entry_binds_only_existing_p3_lock_and_original_lease(self):
        document = register.entry()
        self.assertEqual(document['until_unix'], restart.UNTIL)
        self.assertEqual(document['singleton_lock'], str(runner.LEDGER / 'PARENT_OPERATOR.lock'))
        self.assertEqual(document['lease_evidence']['json_pointer'], '/hard_end_unix')
        self.assertEqual(document['argv'], ['/usr/bin/python3', '-B', str(runner.HERE / 'restart.py')])
        self.assertNotIn('env', document)
        self.assertNotIn('environment', document)


if __name__ == '__main__':
    unittest.main()
