import ast
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).with_name('RECOVERY_OPERATOR.py')
spec = spec_from_file_location('node3_terminal_recovery', SOURCE)
module = module_from_spec(spec)
spec.loader.exec_module(module)


class RecoveryTests(unittest.TestCase):
    def test_stage_candidate_import_path_precedes_policy_verification(self):
        tree = ast.parse(SOURCE.read_bytes())
        stage = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'stage')
        calls = [(node.lineno, ast.unparse(node.func)) for node in ast.walk(stage) if isinstance(node, ast.Call)]
        inserted = next(line for line, name in calls if name == 'sys.path.insert')
        verified = next(line for line, name in calls if name == "family['verify_source']")
        self.assertLess(inserted, verified)
        result = subprocess.run([sys.executable, '-I', '-B', '-c',
            'import sys; sys.path.insert(0,sys.argv[1]); import gpu.orch_r179_context_survival', str(SOURCE.parents[4])],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_repeatable_inbox_is_deduped_by_saved_history_not_assumed_empty(self):
        from unittest.mock import Mock
        history = SimpleNamespace(checkpoint=lambda: {'saved': True}, append=Mock(return_value=False))
        journal = SimpleNamespace(read_inbox=lambda: ['already-known-parent-event'],
                                  latest_checkpoint=lambda: {'expected_sha256': 'saved'})
        module.verify_saved_inbox(journal, SimpleNamespace(history=history), 'saved')
        history.append.assert_called_once_with('already-known-parent-event')
        history.append.return_value = True
        with self.assertRaisesRegex(ValueError, 'already_in_history'):
            module.verify_saved_inbox(journal, SimpleNamespace(history=history), 'saved')

    def test_all_subprocess_transitions_parse(self):
        tree = ast.parse(SOURCE.read_bytes())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        choices = next(keyword.value for node in ast.walk(main) if isinstance(node, ast.Call)
            for keyword in node.keywords if keyword.arg == 'choices' and isinstance(keyword.value, ast.Tuple))
        self.assertEqual(ast.literal_eval(choices), ('stage', 'preflight', 'branch-cpu', 'dispatch', 'supervise', 'contained'))
        with patch.object(module, 'ROOT', Path('/localhome/local-rohing/orch_r179_node3_recovery_test')):
            for action in ('stage', 'preflight', 'branch-cpu', 'dispatch', 'supervise', 'contained'):
                with self.subTest(action=action):
                    with patch.object(module, 'stage', return_value={}), patch.object(module, 'preflight', return_value={}), \
                            patch.object(module, 'branch_cpu', return_value={}), patch.object(module, 'dispatch', return_value={}), \
                            patch.object(module, 'contained', return_value={}), patch.object(module, 'launch_gate',
                                return_value=(None, {'supervise': lambda output: {}}, None, None, None)), \
                            patch.object(sys, 'argv', [str(SOURCE), '--action', action, '--physical', '1', '--policy', '{}']):
                        module.main()

    def test_real_subprocess_cli_help(self):
        result = subprocess.run([sys.executable, '-B', str(SOURCE), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('branch-cpu', result.stdout)
        self.assertIn('contained', result.stdout)

    def test_reject_other_devices_and_noncanonical_roots(self):
        with patch.object(module, 'ROOT', Path('/localhome/local-rohing/orch_r179_node3_recovery_test')):
            for physical in (True, '1', 5, 6, 8, -1):
                with self.subTest(physical=physical), self.assertRaises(ValueError):
                    module.output_path(physical)
        with patch.object(module, 'ROOT', Path('/tmp/orch_r179_node3_recovery_test')), self.assertRaises(ValueError):
            module.output_path(1)

    def test_create_only_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            module.write(path, {'original': True})
            with self.assertRaises(FileExistsError):
                module.write(path, {'original': False})
            self.assertEqual(module.read(path), {'original': True})

    def test_canonical_no_symlinks_or_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'target').write_text('x')
            (root / 'link').symlink_to(root / 'target')
            for path in (root / 'link', root / 'foo/../target', Path('relative')):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    module.regular(path)

    def test_owned_exits_required_every_role(self):
        actors = {role: {'pid': 10**10 + index, 'absent': True} for index, role in enumerate(('actor', 'timer', 'supervisor'))}
        module.verify_exits(actors)
        for role in actors:
            changed = deepcopy(actors)
            changed[role]['absent'] = False
            with self.subTest(role=role), self.assertRaises(ValueError):
                module.verify_exits(changed)
        with self.assertRaises(ValueError):
            module.verify_exits({'actor': actors['actor']})

    def test_existing_pid_not_treated_as_terminal(self):
        actors = {role: {'pid': 10**10, 'absent': True} for role in ('actor', 'timer', 'supervisor')}
        actors['timer']['pid'] = __import__('os').getpid()
        with self.assertRaisesRegex(ValueError, 'still_absent'):
            module.verify_exits(actors)

    def test_prefix_copy_exact_independent_and_saved_inbox_only(self):
        recovery = module.load(SOURCE.parents[4] / 'gpu/orch_r154_repo_reader_recover.py', module.R154_SHA)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / 'original'
            original.mkdir()
            (original / 'records').mkdir()
            (original / 'inbox').mkdir()
            (original / 'JOURNAL.json').write_text('{}')
            for index in range(2):
                message = original / 'inbox' / (str(index) + '.json')
                message.write_text(json.dumps({'id': index}))
                record = {'kind': 'INBOX', 'document': {'source_id': str(message), 'source_sha256': module.sha(message)}}
                (original / 'records' / ('%020d.json' % index)).write_text(json.dumps(record))
                (original / 'records' / ('%020d.intent.json' % index)).write_text('{}')
            copied = root / 'copy'
            recovery.copy_prefix(original, copied, 0)
            inbox = recovery.copy_saved_inbox(original, copied, 0)
            self.assertEqual(set(inbox), {'0.json'})
            self.assertFalse((copied / 'records/00000000000000000001.json').exists())
            self.assertTrue((original / 'records/00000000000000000001.json').exists())
            self.assertNotEqual((copied / 'JOURNAL.json').stat().st_ino, (original / 'JOURNAL.json').stat().st_ino)

    def test_checkpoint_copy_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / 'old'
            original.mkdir()
            (original / 'optimizer.pt').write_bytes(b'saved')
            pins = module.independent_tree(original, root / 'new')
            self.assertEqual(pins, {'optimizer.pt': module.sha(original / 'optimizer.pt')})
            self.assertNotEqual((original / 'optimizer.pt').stat().st_ino, (root / 'new/optimizer.pt').stat().st_ino)

    def test_every_historical_readout_marker_required_no_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'old').mkdir()
            (root / 'new').mkdir()
            (root / 'old/sleep_000000_r2_DISPATCH.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'every_consumed'):
                module.readout_markers({'readout_revision': 2}, 1, root / 'old', root / 'new')
            (root / 'old/sleep_000001_r2_DISPATCH.json').write_text('{}')
            (root / 'old/sleep_000002_r2_DISPATCH.json').write_text('{}')
            result = module.readout_markers({'readout_revision': 2}, 1, root / 'old', root / 'new')
            self.assertEqual(len(result), 3)
            self.assertEqual(len(list((root / 'new').iterdir())), 3)

    def test_host_namespace_refused_private_mount_required(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / 'old').mkdir()
            (output / 'run1').mkdir()
            state = (output / 'old').stat()
            module.write(output / 'RECOVERY_SEGMENT.json', dict(logical_root=str(output / 'old'),
                original_root_device=state.st_dev, original_root_inode=state.st_ino))
            with self.assertRaisesRegex(ValueError, 'private_new_segment'):
                module.verify_mount(output)

    def test_mapped_command_retains_original_device_constructor_all_lanes(self):
        captured = []
        def construct(*args):
            captured.append(args)
            return ['sudo', '-n', 'systemd-run', '--property=DevicePolicy=strict', '/usr/bin/env', '-i', *args[-2]]
        family = {'direct_command': construct}
        original = SimpleNamespace(programmes=SimpleNamespace(device_containment_command=construct, containment_command=construct))
        for physical in module.PHYSICALS:
            with self.subTest(physical=physical):
                policy = dict(minor=physical, uid=2524, gid=2524, unit='unit')
                plan = dict(physical=physical, source_root='/source', root='/logical')
                result = module.mapped_command(family, plan, dict(device_containment=policy), original,
                    Path('/new/control'), 'contained', 300)
                self.assertIn('--property=DevicePolicy=strict', result)
                self.assertIn('--property=BindPaths=/new/control/run1:/logical', result)
                self.assertIn('--property=ReadOnlyPaths=/source', result)
                self.assertEqual(result[-4:], ['--action', 'contained', '--physical', str(physical)])
        self.assertEqual(len(captured), 6)

    def test_recovery_does_not_patch_native_or_kill_owners(self):
        tree = ast.parse(SOURCE.read_bytes())
        calls = [ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
        self.assertFalse(set(calls) & {'os.kill', 'os.killpg', 'signal.pidfd_send_signal', 'shutil.rmtree', 'native.NativeChild'})
        namespace = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'namespaces')
        assignments = [node for node in ast.walk(namespace) if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Subscript) for target in node.targets)]
        self.assertEqual(len(assignments), 1)
        self.assertIn("family['contained_command']", ast.unparse(assignments[0]))

    def test_private_source_invokes_unchanged_lower_lifecycle(self):
        tree = ast.parse(SOURCE.read_bytes())
        contained = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'contained')
        text = ast.unparse(contained)
        self.assertIn("family['contained'](output)", text)
        self.assertIn('original.programmes.contained_native', text)
        self.assertIn('verify_mount(output)', text)
