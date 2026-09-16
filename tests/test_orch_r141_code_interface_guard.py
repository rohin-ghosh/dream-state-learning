import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r133_code_feedback_guard as frozen
from gpu import orch_r141_code_interface as collection
from gpu import orch_r141_code_interface_guard as guard


class GuardAdapterTests(unittest.TestCase):
    def config(self):
        return dict(schema='R133_MAIN_GUARD_V1', wrapper='ovx3', physical=7,
                    gpu_uuid=guard.GPU_UUID, created_unix=guard.HARD_END_UNIX - 6000,
                    hard_end_unix=guard.HARD_END_UNIX, next_reserved_unix=guard.NEXT_RESERVED_UNIX,
                    lease_end_unix=guard.HARD_END_UNIX + 30000, max_native_calls=96)

    def test_same_slot_with_tighter_deadline_and_reservation(self):
        guard.validate_scope(self.config(), guard.HARD_END_UNIX - 100)
        self.assertEqual(guard.NEXT_RESERVED_UNIX - guard.HARD_END_UNIX, 1200)
        self.assertEqual(guard.GPU_UUID, 'GPU-9e6cdf73-7181-4405-2aec-787cc73a3e5b')

    def test_rebinding_extra_calls_and_extended_wall_rejected(self):
        for changes in (dict(physical=6), dict(wrapper='ovx'), dict(gpu_uuid='GPU-other'),
                        dict(max_native_calls=97), dict(hard_end_unix=guard.HARD_END_UNIX + 1),
                        dict(next_reserved_unix=guard.NEXT_RESERVED_UNIX + 1),
                        dict(lease_end_unix=guard.HARD_END_UNIX + 21600)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                guard.validate_scope(dict(self.config(), **changes), guard.HARD_END_UNIX - 100)
        with self.assertRaises(ValueError):
            guard.validate_scope(self.config(), guard.HARD_END_UNIX)

    def test_exact_frozen_guard_checks_no_global_mutation(self):
        for name in ('validate', 'scan', 'supervise'):
            if name != 'supervise':
                self.assertIs(getattr(guard, name).__code__, getattr(frozen, name).__code__)
            self.assertIs(getattr(guard, name).__globals__['collection'], collection)
        self.assertEqual(guard.supervise.__code__.co_code, frozen.supervise.__code__.co_code)
        differences = [(before, after) for before, after in
                       zip(frozen.supervise.__code__.co_consts, guard.supervise.__code__.co_consts)
                       if before != after]
        self.assertEqual(differences, [('gpu.orch_r133_code_feedback_guard', 'gpu.orch_r141_code_interface_guard')])
        for name in ('validate_checkpoint', 'validate_inventory', 'validate_allocation',
                     'reference', 'publish_launch', 'reap_owned_child'):
            self.assertIs(guard._namespace[name], getattr(frozen, name))
        self.assertIs(guard._namespace['validate'], guard.validate)
        self.assertIs(guard._namespace['validate_scope'], guard.validate_scope)
        self.assertEqual(guard._namespace['__file__'], guard.__file__)
        self.assertIs(frozen.validate.__globals__['collection'], frozen.collection)
        self.assertIsNot(frozen.collection, collection)
        self.assertIs(frozen.supervise.__globals__['subprocess'], guard._namespace['subprocess'])

    def test_launch_receipt_hash_matches_actual_dispatch_argv(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = dict(output_root=str(root), source_root=str(root / 'source'),
                          hard_end_unix=time.time() + 300)
            config_path = root / 'GUARD.json'
            collection.write(config_path, config)
            process = Mock(pid=os.getpid())
            process.wait.return_value = 0
            process.poll.return_value = 0
            dispatched = []

            def launch(command, **kwargs):
                dispatched.append((list(command), kwargs))
                collection.write(root / 'NATIVE_TERMINAL.json', dict(status='COMPLETE'))
                return process

            def startup_token(token):
                receipt = collection.read(root / 'LAUNCH.json')
                actual = dispatched[0][0]
                self.assertEqual(receipt['command_sha256'], hashlib.sha256(json.dumps(actual).encode()).hexdigest())
                self.assertEqual(token, b'LAUNCH_READY\n')

            process.stdin.write.side_effect = startup_token
            scanner = Mock(return_value=json.dumps(dict(clear=True, scanner_euid=0, blocking_reasons=[])))
            fake_subprocess = SimpleNamespace(check_output=scanner, Popen=Mock(side_effect=launch), PIPE=-1, STDOUT=-2)
            with patch.dict(guard._namespace, validate=Mock(return_value=(config, {})), subprocess=fake_subprocess):
                guard.supervise(config_path)
            actual, options = dispatched[0]
            self.assertEqual(actual[:3], ['timeout', '--signal=TERM', '--kill-after=5s'])
            self.assertLessEqual(int(actual[3][:-1]), 290)
            self.assertGreater(int(actual[3][:-1]), 0)
            self.assertEqual(actual[4:], [sys.executable, '-B', '-m', 'gpu.orch_r141_code_interface_guard',
                                          'native', '--config', str(config_path)])
            receipt = collection.read(root / 'LAUNCH.json')
            self.assertEqual(receipt['command_sha256'], hashlib.sha256(json.dumps(actual).encode()).hexdigest())
            old_command = list(actual)
            old_command[7] = 'gpu.orch_r133_code_feedback_guard'
            self.assertNotEqual(receipt['command_sha256'], hashlib.sha256(json.dumps(old_command).encode()).hexdigest())
            self.assertEqual(options['env']['CUDA_VISIBLE_DEVICES'], guard.GPU_UUID)
            self.assertEqual(options['env']['PYTHONPATH'], config['source_root'])
            self.assertEqual(options['env']['HF_HUB_OFFLINE'], '1')
            self.assertTrue(options['start_new_session'])
            self.assertEqual(options['cwd'], config['source_root'])
            scan_command = scanner.call_args.args[0]
            self.assertIn(str(Path(guard.__file__).resolve()), scan_command)
            self.assertIn('CUDA_VISIBLE_DEVICES=', scan_command)
            self.assertFalse(receipt.get('retry_allowed', False))
            self.assertEqual(collection.read(root / 'SUPERVISOR_COMPLETE.json')['status'], 'COMPLETE')

    def test_native_cli_runs_all_barriers_before_collection(self):
        events = []
        config = dict(output_root='/fake/fresh')
        authorization = {'test': True}
        with patch.object(sys, 'argv', ['guard', 'native', '--config', '/fake/GUARD.json']), \
                patch.object(guard, 'validate', side_effect=lambda path: (events.append('validate') or (config, authorization))), \
                patch.object(frozen, 'await_startup', side_effect=lambda *args: events.append('startup')), \
                patch.object(frozen, 'validate_native_entry', side_effect=lambda *args: events.append('entry')), \
                patch.object(collection, 'collect', side_effect=lambda *args, **kwargs: events.append('collect')) as collect:
            guard.main()
            collect.assert_called_once_with(Path('/fake/fresh'), authorization, expected_gpu_uuid=guard.GPU_UUID)
        self.assertEqual(events, ['validate', 'startup', 'entry', 'collect'])

    def test_native_cli_refuses_failed_startup_or_entry(self):
        for failing in ('await_startup', 'validate_native_entry'):
            with self.subTest(failing=failing), \
                    patch.object(sys, 'argv', ['guard', 'native', '--config', '/fake/GUARD.json']), \
                    patch.object(guard, 'validate', return_value=(dict(output_root='/fake'), {})), \
                    patch.object(frozen, 'await_startup', Mock()), \
                    patch.object(frozen, 'validate_native_entry', Mock()), \
                    patch.object(collection, 'collect') as collect:
                getattr(frozen, failing).side_effect = ValueError('blocked')
                with self.assertRaisesRegex(ValueError, 'blocked'):
                    guard.main()
                collect.assert_not_called()


if __name__ == '__main__':
    unittest.main()
