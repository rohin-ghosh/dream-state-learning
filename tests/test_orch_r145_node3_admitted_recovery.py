import ast
from copy import deepcopy
import inspect
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r145_node3_admitted_recovery as admitted
from gpu import orch_r145_node3_capacity_recovery as capacity
from gpu import orch_r145_node3_stage_recovery as staging


def plan(physical=5):
    return dict(physical=physical, gpu_uuid=capacity.DEVICES[physical],
        root='/localhome/local-rohing/orch_r133_node3_' + capacity.LANES[physical]['name'] + '_20260916_attempt1/run1')


def command(physical=5):
    return ['sudo', '-n', 'systemd-run', '--property=DevicePolicy=strict',
            '--property=DeviceAllow=/dev/nvidia' + str(physical) + ' rw',
            '--property=DeviceAllow=/dev/nvidiactl rw', '--property=DeviceAllow=/dev/nvidia-uvm rw',
            '/usr/bin/env', '-i', 'CUDA_VISIBLE_DEVICES=' + capacity.DEVICES[physical], '/usr/bin/python3']


class ContainmentTests(unittest.TestCase):
    def test_allocator_only_addition_for_both_owned_lanes(self):
        for physical in (5, 6):
            original = command(physical)
            changed = admitted.allocator_command(original, plan(physical), dict(minor=physical))
            changed.remove('PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True')
            self.assertEqual(changed, original)

    def test_foreign_device_allowed_is_rejected(self):
        value = command()
        value.insert(3, '--property=DeviceAllow=/dev/nvidia4 rw')
        with self.assertRaisesRegex(ValueError, 'only_target'):
            admitted.allocator_command(value, plan(), dict(minor=5))

    def test_wrong_minor_and_healthy_lane_rejected(self):
        with self.assertRaises(ValueError):
            admitted.allocator_command(command(), plan(), dict(minor=6))
        value = plan()
        value['physical'] = 4
        with self.assertRaises(ValueError):
            admitted.allocator_command(command(), value, dict(minor=4))

    def test_conflicting_allocator_rejected(self):
        for variable in ('PYTORCH_ALLOC_CONF=x', 'PYTORCH_CUDA_ALLOC_CONF=x'):
            with self.assertRaisesRegex(ValueError, 'conflicting_allocator'):
                admitted.allocator_command(command() + [variable], plan(), dict(minor=5))

    def test_loss_of_strict_or_clean_environment_rejected(self):
        for missing in ('--property=DevicePolicy=strict', '-i'):
            value = command()
            value.remove(missing)
            with self.assertRaises(ValueError):
                admitted.allocator_command(value, plan(), dict(minor=5))


class IntegrationTests(unittest.TestCase):
    def test_exact_original_launcher_relocation_preserves_scan_and_checks(self):
        path = Path(__file__).resolve().parents[1] / 'gpu/orch_r133_node3_programmes.py'
        self.assertEqual(capacity.file_sha(path), capacity.LAUNCHER_SHA)
        tree = ast.parse(path.read_text())
        for action in ('supervise', 'contained_native'):
            function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == action)
            original = ast.get_source_segment(path.read_text(), function)
            modified = admitted.relocated_source(original, action)
            before = 'gpu.orch_r133_node3_programmes' if action == 'supervise' else 'gpu.orch_r125_continual_guard'
            self.assertEqual(modified.replace(repr(admitted.MODULE), repr(before)), original)
            self.assertIn('fresh_global_admission' if action == 'contained_native' else 'unchanged_global_exclusive_admission', modified)

    def test_unknown_relocation_rejected(self):
        with self.assertRaises(ValueError):
            admitted.relocated_source('def supervise():\n    pass\n', 'supervise')
        with self.assertRaises(ValueError):
            admitted.relocated_source('pass', 'scan')

    def test_plan_relocates_source_and_startup_only(self):
        original = dict(plan(), source_root='/localhome/local-rohing/source_old',
            context_limit=16384, new_presentations=16, rehearsal_presentations=1,
            anchor_fraction=.25, startup_context=dict(path='/localhome/local-rohing/source_old/STARTUP.md', sha256='fixed'))
        before = deepcopy(original)
        new = staging.unchanged_plan(original, Path('/localhome/local-rohing/source_r145_test'))
        self.assertEqual(original, before)
        new['source_root'] = original['source_root']
        new['startup_context']['path'] = original['startup_context']['path']
        self.assertEqual(new, original)

    def test_probe_uses_all_actual_children_without_modifying_anchors(self):
        rows = [dict(source_sha256='pending'), dict(source_sha256='older')]
        stream = SimpleNamespace(pending_rows=lambda: rows[:1], rows=rows[1:], sleep_frontier=1)
        child = SimpleNamespace(tokenizer=object(), plan=dict(context_limit=16384))
        anchors = object()
        native = SimpleNamespace(encode_own=lambda row, tokenizer, limit: (row['source_sha256'], tokenizer, limit))
        with patch.dict('sys.modules', {'gpu.orch_r125_continual_native': native}), \
                patch.object(capacity, 'bounded_train_probe', return_value={'status': 'PASS'}) as probe:
            from gpu import orch_r125_continual_native
            with patch.object(orch_r125_continual_native, 'encode_own', native.encode_own):
                admitted.admitted_probe(child, stream, anchors, '/output')
        arguments = probe.call_args.args
        self.assertEqual(set(arguments[1]), {'pending', 'older'})
        self.assertIs(arguments[2], anchors)
        self.assertEqual(arguments[3], admitted.RUNTIME_SHA)

    def test_reference_rejects_changed_bytes_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            path.write_text('{}')
            reference = staging.reference(path)
            self.assertEqual(admitted.raw_reference(reference), b'{}')
            link = path.with_name('link.json')
            link.symlink_to(path)
            with self.assertRaises(ValueError):
                admitted.raw_reference(dict(reference, path=str(link)))
            path.write_text('{"changed":true}')
            with self.assertRaises(ValueError):
                admitted.raw_reference(reference)

    def test_recovery_is_before_unmodified_continuation_and_no_standalone_probe(self):
        source = inspect.getsource(admitted.entrypoint)
        self.assertLess(source.index('recover_admitted_sleep(plan_path, manifest)'), source.index('original_run(plan_path, resume=True)'))
        self.assertIn('guard.native_entry(arguments.config)', source)
        self.assertNotIn("'probe'", source)


if __name__ == '__main__':
    unittest.main()
