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
from gpu import orch_r141_code_interface_guard as prior
from gpu import orch_r142_base_reasoning_collection as collection
from gpu import orch_r142_base_reasoning_guard as guard


class GuardTests(unittest.TestCase):
    def config(self):
        return dict(schema='R133_MAIN_GUARD_V1', wrapper='ovx3', physical=7, gpu_uuid=guard.GPU_UUID,
                    created_unix=guard.HARD_END_UNIX - 6000, hard_end_unix=guard.HARD_END_UNIX,
                    next_reserved_unix=guard.NEXT_RESERVED_UNIX, lease_end_unix=guard.HARD_END_UNIX + 30000,
                    max_native_calls=96)

    def test_exact_frozen_guards_and_single_module_delta(self):
        self.assertIs(guard.validate_scope, prior.validate_scope)
        self.assertIs(guard.validate.__code__, frozen.validate.__code__)
        self.assertIs(guard.scan.__code__, frozen.scan.__code__)
        self.assertEqual(guard.supervise.__code__.co_code, frozen.supervise.__code__.co_code)
        self.assertEqual(len(guard.supervise.__code__.co_consts), len(frozen.supervise.__code__.co_consts))
        changes = [(before, after) for before, after in zip(frozen.supervise.__code__.co_consts,
                   guard.supervise.__code__.co_consts) if before != after]
        self.assertEqual(changes, [('gpu.orch_r133_code_feedback_guard', 'gpu.orch_r142_base_reasoning_guard')])
        for name in ('validate_checkpoint', 'validate_inventory', 'validate_allocation', 'reference',
                     'publish_launch', 'reap_owned_child'):
            self.assertIs(guard._namespace[name], getattr(frozen, name))
        self.assertIs(guard._namespace['collection'], collection)
        self.assertIs(guard._namespace['validate'], guard.validate)
        self.assertEqual(guard._namespace['__file__'], guard.__file__)
        self.assertIsNot(frozen.collection, collection)

    def test_same_slot_0540_ceiling_0600_reservation_and_no_extension(self):
        guard.validate_scope(self.config(), guard.HARD_END_UNIX - 100)
        self.assertEqual((guard.HARD_END_UNIX, guard.NEXT_RESERVED_UNIX), (1789537200, 1789538400))
        for changes in (dict(physical=6), dict(gpu_uuid='GPU-other'), dict(max_native_calls=97),
                        dict(hard_end_unix=guard.HARD_END_UNIX + 1), dict(next_reserved_unix=guard.NEXT_RESERVED_UNIX + 1),
                        dict(lease_end_unix=guard.HARD_END_UNIX + 21600)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                guard.validate_scope(dict(self.config(), **changes), guard.HARD_END_UNIX - 100)

    def test_actual_R142_argv_hash_before_startup_and_after_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = dict(output_root=str(root), source_root=str(root / 'source'), hard_end_unix=time.time() + 300)
            path = root / 'GUARD.json'
            collection.write(path, config)
            process = Mock(pid=os.getpid())
            process.wait.return_value = 0
            process.poll.return_value = 0
            commands = []

            def launch(command, **kwargs):
                commands.append((list(command), kwargs))
                collection.write(root / 'NATIVE_TERMINAL.json', dict(status='COMPLETE'))
                return process

            def startup(token):
                self.assertEqual(token, b'LAUNCH_READY\n')
                self.assertEqual(collection.read(root / 'LAUNCH.json')['command_sha256'],
                                 hashlib.sha256(json.dumps(commands[0][0]).encode()).hexdigest())

            process.stdin.write.side_effect = startup
            scanner = Mock(return_value=json.dumps(dict(clear=True, scanner_euid=0, blocking_reasons=[])))
            fake = SimpleNamespace(check_output=scanner, Popen=Mock(side_effect=launch), PIPE=-1, STDOUT=-2)
            with patch.dict(guard._namespace, validate=Mock(return_value=(config, {})), subprocess=fake):
                guard.supervise(path)
            command, options = commands[0]
            self.assertEqual(command[:3], ['timeout', '--signal=TERM', '--kill-after=5s'])
            self.assertLessEqual(int(command[3][:-1]), 290)
            self.assertEqual(command[4:], [sys.executable, '-B', '-m', 'gpu.orch_r142_base_reasoning_guard',
                                         'native', '--config', str(path)])
            self.assertEqual(collection.read(root / 'LAUNCH.json')['command_sha256'], hashlib.sha256(json.dumps(command).encode()).hexdigest())
            self.assertEqual(options['env']['CUDA_VISIBLE_DEVICES'], guard.GPU_UUID)
            self.assertEqual(options['env']['PYTHONPATH'], config['source_root'])
            self.assertTrue(options['start_new_session'])
            self.assertIn(str(Path(guard.__file__).resolve()), scanner.call_args.args[0])
            self.assertIn('CUDA_VISIBLE_DEVICES=', scanner.call_args.args[0])

    def test_native_barriers_precede_R142_collection(self):
        events = []
        config = dict(output_root='/fake/R142')
        authorization = {'fake': True}
        with patch.object(sys, 'argv', ['guard', 'native', '--config', '/fake/GUARD.json']), \
                patch.object(guard, 'validate', side_effect=lambda path: (events.append('validate') or (config, authorization))), \
                patch.object(frozen, 'await_startup', side_effect=lambda *args: events.append('startup')), \
                patch.object(frozen, 'validate_native_entry', side_effect=lambda *args: events.append('entry')), \
                patch.object(collection, 'collect', side_effect=lambda *args, **kwargs: events.append('collect')) as collect:
            guard.main()
            collect.assert_called_once_with(Path('/fake/R142'), authorization, expected_gpu_uuid=guard.GPU_UUID)
        self.assertEqual(events, ['validate', 'startup', 'entry', 'collect'])

    def test_rejected_startup_does_not_collect(self):
        with patch.object(sys, 'argv', ['guard', 'native', '--config', '/fake/GUARD.json']), \
                patch.object(guard, 'validate', return_value=({'output_root': '/fake'}, {})), \
                patch.object(frozen, 'await_startup', side_effect=ValueError('blocked')), \
                patch.object(collection, 'collect') as collect:
            with self.assertRaisesRegex(ValueError, 'blocked'):
                guard.main()
            collect.assert_not_called()


if __name__ == '__main__':
    unittest.main()
