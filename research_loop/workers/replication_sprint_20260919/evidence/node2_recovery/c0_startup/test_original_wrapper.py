from contextlib import ExitStack
from copy import deepcopy
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import c0_pending_entry as entry
import c0_startup as startup
import test_support as support
from test_c0_startup import StopAfterActualAct


class OriginalWrapperTests(unittest.TestCase):
    def setUp(self):
        self.stack = self.enterContext(ExitStack())
        self.sources = support.load_originals(self.stack)
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory(dir=support.HERE)))
        self.fixture = support.build(self.root, self.sources, self.stack)
        self.original_guard = json.loads((support.HERE / 'fixtures/ORIGINAL_GUARD.json').read_bytes())
        self.config = deepcopy(self.original_guard)
        additions = {name: hashlib.sha256((support.HERE / Path(name).name).read_bytes()).hexdigest()
            for name in ['c0_kernel.py', 'c0_applied_wall_validation.py', 'c0_restart_contract.py',
                'c0_tail.py', 'c0_startup.py', 'gpu/c0_pending_entry.py']}
        self.delta = dict(schema='C0_EXECUTION_SOURCE_DELTA_V1',
            original_source_pins=self.original_guard['source_pins'], additions=additions,
            original_plan_sha256=self.fixture.manifest['original_plan']['sha256'],
            execution_plan_sha256=self.fixture.manifest['execution_plan_sha256'])
        self.fixture.manifest['source_delta'] = support.bound_file(self.root / 'SOURCE_DELTA.json',
            json.dumps(self.delta).encode())
        self.config.update(plan_path=startup.CONTROL + '/PLAN.json',
            plan_sha256=self.fixture.manifest['execution_plan_sha256'], attempt_dir=startup.CONTROL,
            allocation_path=startup.CONTROL + '/ALLOCATION.json', allocation_sha256='f' * 64,
            source_pins=dict(self.original_guard['source_pins'], **additions),
            pending_sleep_recovery=support.bound_file(self.root / 'STARTUP.json',
                json.dumps(self.fixture.manifest).encode()))
        self.config_path = self.root / 'GUARD.json'
        self.config_path.write_bytes(json.dumps(self.config).encode())
        real_path = Path

        def mapped(value, *parts):
            path = real_path(value, *parts)
            if path == real_path(startup.CONTROL) or path.is_relative_to(startup.CONTROL):
                return self.root / path.relative_to(startup.CONTROL)
            return path

        for module in (entry, self.sources.guard, self.sources.runtime):
            self.enterContext(patch.object(module, 'Path', mapped))
        startup_path = startup.Path
        self.enterContext(patch.object(startup, 'Path', lambda value, *parts:
            mapped(value, *parts) if real_path(value, *parts).is_relative_to(startup.CONTROL)
            else startup_path(value, *parts)))
        self.original_validate = self.sources.guard.validate
        self.validate = self.enterContext(patch.object(self.sources.guard, 'validate',
            return_value=(self.config, self.fixture.execution)))
        self.enterContext(patch.object(self.sources.guard, 'await_startup'))
        self.enterContext(patch.object(startup.signal, 'signal'))
        self.enterContext(patch.object(startup.signal, 'setitimer'))
        self.enterContext(patch.object(self.sources.guard.time, 'time', return_value=1000))
        self.enterContext(patch.dict(os.environ, CUDA_VISIBLE_DEVICES=self.fixture.execution['gpu_uuid']))
        from gpu import orch_r107_base_anchors_inventory
        self.enterContext(patch.object(orch_r107_base_anchors_inventory, 'build_inventory',
            return_value=(['CPU anchors'], dict(cpu_fixture=True))))
        (self.root / 'DISPATCH_ONCE').mkdir()
        self.report = dict(scanner_euid=0, clear=True, blocking_reasons=[],
            gpu=dict(uuid=self.fixture.execution['gpu_uuid']))
        self.admission()

    def admission(self, age=0):
        raw = json.dumps(self.report).encode()
        (self.root / 'ADMISSION.json').write_bytes(raw)
        ticks = Path('/proc', str(os.getppid()), 'stat').read_text().rsplit(')', 1)[1].split()[19]
        (self.root / 'LAUNCH.json').write_text(json.dumps(dict(pid=os.getppid(), parent_start_ticks=ticks,
            guard_sha256=hashlib.sha256(self.config_path.read_bytes()).hexdigest(),
            admission_sha256=hashlib.sha256(raw).hexdigest(), admission_verified_unix=1000 - age)))

    def native_entry(self):
        with patch.object(sys, 'argv', ['gpu.c0_pending_entry', 'native', '--config', str(self.config_path)]):
            return entry.main()

    def test_full_original_wrapper_native_guard_kernel_original_driver(self):
        with patch.object(self.sources.driver.ThinkActLearn, 'prepare_sleep', side_effect=StopAfterActualAct):
            with self.assertRaises(StopAfterActualAct):
                self.native_entry()
        self.assertGreaterEqual(self.validate.call_count, 2)
        self.assertEqual(self.sources.wrapper.MODULE, startup.MODULE)
        self.assertEqual(self.sources.runtime.MODULE, startup.MODULE)
        self.assertEqual(os.environ['R125_ADMISSION_PLAN_SHA256'], self.fixture.manifest['execution_plan_sha256'])
        self.assertEqual(self.fixture.fake.instances[0].optimizer_steps, 8460)
        records = [json.loads(path.read_bytes()) for path in (self.fixture.journal_root / 'records').glob('*.json')
            if '.intent.' not in path.name]
        self.assertTrue(any(record['kind'] == 'R184_ACT' for record in records))
        self.assertEqual(sum(record['kind'] == 'R184_LEARN_COMPLETE' for record in records), 1)
        self.assertEqual(self.sources.driver.run_loop.__code__.co_filename,
            str(support.HERE / 'source_evidence/gpu/orch_r184_think_act_learn.py'))
        trace_path = os.environ.get('C0_CPU_TRACE')
        if trace_path:
            new = sorted((record for record in records if record['index'] > self.fixture.head),
                key=lambda record: record['index'])
            trace = dict(schema='C0_SYNTHETIC_ORIGINAL_CHAIN_CPU_TRACE_V1', synthetic=True,
                model_or_GPU=False, live_readiness=False, original_guard_validate_mocked=True,
                actual_original_functions=['r233_node2_recovery.main', 'r205_runtime.main',
                    'orch_r125_continual_guard.native_entry', 'orch_r184_think_act_learn.run_loop',
                    'ThinkActLearn.wake', 'ThinkActLearn.act'],
                optimizer_start=8412, optimizer_end=8460,
                rng_origin='DURABLE_COMPLETE_NOT_UNSAVED_POST_GENERATION_STATE',
                records=[dict(index=record['index'], kind=record['kind'], sha256=record['sha256'],
                    **(dict(stage=record['document']['stage']) if record['kind'] == 'R184_STAGE' else {}))
                    for record in new],
                input_original_plan_sha256=self.fixture.manifest['original_plan']['sha256'],
                execution_plan_sha256=self.fixture.manifest['execution_plan_sha256'])
            Path(trace_path).write_text(json.dumps(trace, indent=2, sort_keys=True) + '\n')

    def test_original_admission_rejects_nonroot_scanner_before_child(self):
        self.report['scanner_euid'] = 2524
        self.admission()
        with self.assertRaisesRegex(ValueError, 'fresh_clear_admission'):
            self.native_entry()
        self.assertFalse(self.fixture.fake.instances)

    def test_original_admission_rejects_stale_report_before_child(self):
        self.admission(age=121)
        with self.assertRaisesRegex(ValueError, 'fresh_clear_admission'):
            self.native_entry()
        self.assertFalse(self.fixture.fake.instances)

    def test_original_admission_rejects_busy_GPU_report(self):
        self.report.update(clear=False, blocking_reasons=['busy'])
        self.admission()
        with self.assertRaisesRegex(ValueError, 'fresh_clear_admission'):
            self.native_entry()
        self.assertFalse(self.fixture.fake.instances)

    def test_original_admission_rejects_wrong_device_environment(self):
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='different-device'):
            with self.assertRaisesRegex(ValueError, 'native_GPU_binding'):
                self.native_entry()
        self.assertFalse(self.fixture.fake.instances)

    def test_original_node2_command_and_supervisor_propagate_sidecar(self):
        capture = {}
        def capture_command():
            capture['command'] = self.sources.runtime.contained_command(self.config_path, 'child')
        with patch.object(self.sources.runtime, 'main', capture_command), \
                patch.object(sys, 'argv', ['entry', 'child', '--config', str(self.config_path)]):
            entry.main()
        command = capture['command']
        for argument in ['--property=DevicePolicy=strict', '--property=NoNewPrivileges=yes',
                '--property=CapabilityBoundingSet=', '--property=User=2524', '--property=Group=2524',
                '--property=DeviceAllow=/dev/nvidia4 rw',
                '--property=BindPaths=' + startup.RAW + ':' + startup.ROOT, startup.MODULE]:
            self.assertIn(argument, command)
        self.assertNotIn('--property=DeviceAllow=/dev/nvidia3 rw', command)
        generated = self.sources.wrapper.supervisor_source(inspect.getsource(self.sources.guard.supervise))
        self.assertEqual(generated.count(repr(startup.MODULE)), 2)
        self.assertIn('report = preadmitted_report(config_path)', generated)
        self.assertIn('fresh_exclusive_admission', generated)

    def test_guard_delta_keeps_original_namespace_lease_device_policy(self):
        startup.validate_guard_binding(self.config, self.fixture.manifest, self.fixture.plan_path.read_bytes())
        for field, value in [('copy_raw', '/tmp/new-life'), ('lease_path', '/tmp/new-lease'),
                ('hard_end_unix', 1789927201), ('next_reserved_unix', 9999999999), ('resume', False)]:
            with self.subTest(field=field):
                changed = dict(self.config, **{field: value})
                with self.assertRaises(ValueError):
                    startup.validate_guard_binding(changed, self.fixture.manifest, self.fixture.plan_path.read_bytes())

    def test_original_source_edit_not_allowed_in_delta(self):
        changed = deepcopy(self.config)
        changed['source_pins']['gpu/orch_r125_continual_native.py'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'only_six_additions'):
            startup.validate_guard_binding(changed, self.fixture.manifest, self.fixture.plan_path.read_bytes())

    def test_new_module_cannot_replace_guard_source(self):
        delta = deepcopy(self.delta)
        delta['additions']['gpu/orch_r125_continual_guard.py'] = 'f' * 64
        manifest = dict(self.fixture.manifest, source_delta=support.bound_file(
            self.root / 'MUTATED_SOURCE_DELTA.json', json.dumps(delta).encode()))
        with self.assertRaisesRegex(ValueError, 'only_six_additions'):
            startup.validate_guard_binding(self.config, manifest, self.fixture.plan_path.read_bytes())

    def test_original_guard_full_source_lease_and_allocation_checks(self):
        source = support.HERE / 'source_evidence'
        config = deepcopy(self.config)
        config.update(plan_path=str(self.fixture.plan_path), attempt_dir=str(self.root),
            host_sha256=hashlib.sha256(b'CPU-fixture-node').hexdigest(),
            source_pins={str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in source.rglob('*.py')})
        for field, document in [('lease', dict(lease_end_unix=self.fixture.execution['lease_end_unix'],
                hard_end_unix=self.fixture.execution['hard_end_unix'])),
                ('allocation', dict(plan_sha256=config['plan_sha256'], cpu_tests_passed=True,
                    gpu_uuid=self.fixture.execution['gpu_uuid'], physical=4,
                    builder_entry_pushed=True, declared_unix=900))]:
            binding = support.bound_file(self.root / (field + '.json'), json.dumps(document).encode())
            config[field + '_path'], config[field + '_sha256'] = binding['path'], binding['sha256']
        path = self.root / 'SYNTHETIC_VALIDATED_GUARD.json'
        path.write_text(json.dumps(config))
        with patch.object(self.sources.guard.socket, 'gethostname', return_value='CPU-fixture-node'), \
                patch.object(self.sources.guard, 'Path', lambda value, *parts:
                    source if str(value) == startup.STAGED_SOURCE and not parts else Path(value, *parts)):
            actual, plan = self.original_validate(path)
            self.assertEqual(actual, config)
            self.assertEqual(plan, self.fixture.execution)
            for field in ['source_pins', 'lease_sha256', 'allocation_sha256']:
                changed = dict(config, **{field: {} if field == 'source_pins' else '0' * 64})
                path.write_text(json.dumps(changed))
                with self.subTest(field=field), self.assertRaises(ValueError):
                    self.original_validate(path)


if __name__ == '__main__':
    unittest.main()
