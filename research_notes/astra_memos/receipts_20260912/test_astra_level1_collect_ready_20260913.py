"""CPU-only fixtures: no runtime import, native subprocess, remote call, or GPU."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('level1_collect_ready_test', '/tmp/astra_level1_collect_ready_20260913.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class CollectorTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='level1_collect_cpu_', dir='/tmp')
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.roster_dir = self.home / 'roster'
        self.roster_dir.mkdir()
        self.runtime = self.home / 'frozen_runtime.py'
        self.runtime.write_text('CPU fixture only; never execute')
        self.runtime_pin = collector.digest(self.runtime)
        self.entries = [dict(node=node, name=f'{node}_cell{index}', gpu_index=index,
                       gpu_uuid=f'GPU-CPU-FIXTURE-{node}-{index}', root=str(self.home / f'{node}_root{index}'),
                       spec=dict(path=str(self.home / f'{node}_spec{index}.json'), sha256='a' * 64))
                       for node in ('node1', 'node2') for index in range(6)]
        self.roster = self.roster_dir / 'roster.json'
        collector.write(self.roster, dict(entries=self.entries, prechecks=dict(path='CPU_UNUSED', sha256='b' * 64)))
        self.roster_pin = collector.digest(self.roster)
        self.batch = self.roster_dir / 'batch_node1_parentfix'
        self.batch.mkdir()
        collector.write(self.batch / 'started.json', dict(roster_sha256=self.roster_pin))
        self.patch('ROSTER', self.roster)
        self.patch('ROSTER_SHA256', self.roster_pin)
        self.patch('RUNTIME', self.runtime)
        self.patch('RUNTIME_SHA256', self.runtime_pin)
        self.patch('check_node', side_effect=lambda roster, node: None)
        self.present = self.patch('controller_present', return_value=False)
        process = patch.object(collector.subprocess, 'run', side_effect=AssertionError('native calls forbidden'))
        self.native = process.start()
        self.addCleanup(process.stop)

    def patch(self, name, *args, **kwargs):
        patcher = patch.object(collector, name, *args, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def ready(self, index=0):
        entry = self.entries[index]
        root = Path(entry['root'])
        root.mkdir()
        cell = self.batch / entry['name']
        cell.mkdir()
        plan = {key: entry[key] for key in ('root', 'gpu_index', 'gpu_uuid')}
        plan.update(spec_sha256=entry['spec']['sha256'], self_sha256=self.runtime_pin,
                    python=os.path.abspath(sys.executable), python_sha256=collector.digest(sys.executable))
        collector.write(root / 'plan.json', plan)
        pin = collector.digest(root / 'plan.json')
        pid = 90000 + index
        command = [plan['python'], '-B', str(self.runtime), 'controller', '--root', str(root), '--plan-sha256', pin, '--allow-gpu']
        launch = {key: entry[key] for key in ('node', 'name', 'root', 'gpu_index', 'gpu_uuid')}
        launch.update(pid=pid, pgid=pid, identity=dict(pid=pid), plan_sha256=pin, command=command)
        collector.write(cell / 'launched.json', launch)
        collector.write(root / 'controller_started.json', dict(plan_sha256=pin))
        collector.write(root / 'capture_complete.json', dict(plan_sha256=pin, calls=120, scored=False, stages={}))
        return entry, root, cell

    def fake_collect(self, command, **kwargs):
        self.assertEqual(command[:4], [os.path.abspath(sys.executable), '-B', str(self.runtime), 'collect'])
        self.assertNotIn('--allow-gpu', command)
        self.assertEqual(kwargs['timeout'], 180)
        self.assertEqual(kwargs['env']['CUDA_VISIBLE_DEVICES'], '')
        self.assertTrue(kwargs['start_new_session'])
        root = Path(command[command.index('--root') + 1])
        out = Path(command[command.index('--out') + 1])
        completion = command[command.index('--completion-sha256') + 1]
        self.assertEqual(completion, collector.digest(root / 'capture_complete.json'))
        self.assertEqual(out, root.with_name(root.name + '_collected'))
        self.assertNotIn(root, Path(kwargs['stdout'].name).parents)
        collector.write(root.with_name(root.name + '.collection_claim.json'), dict(out=str(out), retry=False))
        out.mkdir()
        collector.write(out / 'scores.json', dict(CPU_fixture=True))
        collector.write(out / 'collection.json', dict(completion_sha256=completion, scores_sha256=collector.digest(out / 'scores.json')))
        kwargs['stdout'].write(b'CPU mock native collection\n')
        return SimpleNamespace(returncode=0)

    def test_pending_no_launch_or_no_completion(self):
        result = collector.collect_cell(self.entries[0], self.batch)
        self.assertEqual(result['status'], 'pending')
        entry, root, _ = self.ready()
        (root / 'capture_complete.json').unlink()
        self.assertEqual(collector.collect_cell(entry, self.batch)['status'], 'pending')
        self.native.assert_not_called()
        self.assertFalse(root.with_name(root.name + '_collection_driver').exists())

    def test_present_controller_even_completed_is_pending(self):
        entry, root, _ = self.ready()
        self.present.return_value = True
        self.assertEqual(collector.collect_cell(entry, self.batch)['status'], 'pending')
        self.native.assert_not_called()
        self.assertFalse(root.with_name(root.name + '_collected').exists())

    def test_complete_collect_once_exact_pins_external_logs_immutable_root(self):
        entry, root, _ = self.ready()
        before = {path.name: path.read_bytes() for path in root.iterdir()}
        self.native.side_effect = self.fake_collect
        result = collector.collect_cell(entry, self.batch)
        self.assertEqual(result['status'], 'collected')
        self.assertEqual({path.name: path.read_bytes() for path in root.iterdir()}, before)
        self.assertTrue(Path(result['logs'], 'stdout.log').exists())
        self.assertTrue(Path(result['logs'], 'stderr.log').exists())
        self.assertTrue(Path(result['logs'], 'result.json').exists())
        self.assertEqual(collector.collect_cell(entry, self.batch)['status'], 'claimed')
        self.native.assert_called_once()

    def test_all_existing_claim_kinds_skip_without_retry(self):
        for index, suffix in enumerate(('.collection_claim.json', '_collected', '_collection_driver')):
            entry = self.entries[index]
            Path(entry['root'] + suffix).mkdir()
            self.assertEqual(collector.collect_cell(entry, self.batch)['status'], 'claimed')
        self.native.assert_not_called()

    def test_controller_failure_never_scores(self):
        entry, root, _ = self.ready()
        collector.write(root / 'controller_failure.json', dict(error='CPU fixture'))
        self.assertEqual(collector.collect_cell(entry, self.batch)['status'], 'failed')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(collector.run('node1', self.batch), 1)
        self.native.assert_not_called()

    def test_completion_plan_mismatch_no_collect(self):
        entry, root, _ = self.ready()
        (root / 'capture_complete.json').write_text(json.dumps(dict(plan_sha256='bad', calls=120, scored=False)))
        with self.assertRaisesRegex(ValueError, 'completion/launch'):
            collector.collect_cell(entry, self.batch)
        self.native.assert_not_called()

    def test_plan_hash_and_interpreter_drift_no_collect(self):
        entry, root, _ = self.ready()
        with patch.object(collector, 'digest', return_value='wrong'):
            with self.assertRaisesRegex(ValueError, 'interpreter'):
                collector.collect_cell(entry, self.batch)
        (root / 'plan.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'file pin'):
            collector.collect_cell(entry, self.batch)
        self.native.assert_not_called()

    def test_native_nonzero_visible_error_never_retried(self):
        entry, root, _ = self.ready()
        self.native.side_effect = None
        self.native.return_value = SimpleNamespace(returncode=17)
        result = collector.collect_cell(entry, self.batch)
        self.assertEqual(result['status'], 'error')
        self.assertIn('17', result['error'])
        self.assertFalse(root.with_name(root.name + '.collection_claim.json').exists())
        self.assertEqual(collector.collect_cell(entry, self.batch)['status'], 'claimed')
        self.native.assert_called_once()

    def test_timeout_visible_and_subsequent_invocation_claimed(self):
        entry, _, _ = self.ready()
        self.native.side_effect = subprocess.TimeoutExpired('CPU fixture', 180)
        result = collector.collect_cell(entry, self.batch)
        self.assertEqual((result['status'], result['error_type']), ('error', 'TimeoutExpired'))
        self.assertEqual(collector.collect_cell(entry, self.batch)['status'], 'claimed')
        self.native.assert_called_once()

    def test_zero_exit_without_native_receipt_is_error(self):
        entry, _, _ = self.ready()
        self.native.side_effect = None
        self.native.return_value = SimpleNamespace(returncode=0)
        self.assertEqual(collector.collect_cell(entry, self.batch)['status'], 'error')

    def test_single_pass_node_selection_and_failure_exit_status(self):
        self.ready()
        self.native.side_effect = self.fake_collect
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(collector.run('node1', self.batch), 0)
        reports = [json.loads(line) for line in stdout.getvalue().splitlines()]
        self.assertEqual(len(reports), 6)
        self.assertEqual([row['status'] for row in reports], ['collected'] + ['pending'] * 5)
        self.native.assert_called_once()
        with self.assertRaisesRegex(ValueError, 'exact existing'):
            collector.load_roster('node2', self.batch)

    def test_errors_return_nonzero_and_roster_runtime_batch_pins(self):
        self.ready()
        self.native.side_effect = None
        self.native.return_value = SimpleNamespace(returncode=2)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(collector.run('node1', self.batch), 1)
        with patch.object(collector, 'RUNTIME_SHA256', 'wrong'):
            with self.assertRaisesRegex(ValueError, 'runtime pin'):
                collector.load_roster('node1', self.batch)
        with patch.object(collector, 'ROSTER_SHA256', 'wrong'):
            with self.assertRaisesRegex(ValueError, 'file pin'):
                collector.load_roster('node1', self.batch)


if __name__ == '__main__':
    unittest.main()
