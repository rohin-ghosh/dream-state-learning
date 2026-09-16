"""Non-material CPU guard regressions using local receipts, never launches."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r125_continual_guard as guard
from gpu import orch_r125_continual_native as native


class GuardBindingsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.source = self.directory/'source'
        self.module = self.source/'gpu'/'orch_r125_continual_guard.py'
        self.module.parent.mkdir(parents=True)
        self.module.write_text('synthetic source closure\n')
        self.dependency = self.source/'nested'/'dependency.py'
        self.dependency.parent.mkdir()
        self.dependency.write_text('VALUE = 1\n')
        self.attempt = self.directory/'attempt'
        self.attempt.mkdir()
        self.plan = dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256,
            system_prompt=native.SYSTEM, birth_prompt=native.BIRTH,
            compaction_invitation=native.COMPACTION_INVITATION,
            new_presentations=16, rehearsal_presentations=1, anchor_lambda=0.25,
            seed=0, segments_per_sleep=2, segment_tokens=16, context_limit=8192,
            max_sleeps=2, physical=0, gpu_uuid='GPU-synthetic',
            hard_end_unix=700, lease_end_unix=1100,
            decoder=dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05,
                         no_repeat_ngram_size=16),
            root=str(self.directory/'life'), model_dir=str(self.directory/'model'),
            anchors=str(self.directory/'anchors'), source_root=str(self.source))
        self.plan_path = self.directory/'plan.json'
        self.write(self.plan_path, self.plan)
        self.allocation_path = self.directory/'allocation.json'
        self.allocation = dict(plan_sha256=native.sha(self.plan_path), cpu_tests_passed=True,
            gpu_uuid=self.plan['gpu_uuid'], physical=0, builder_entry_pushed=True, declared_unix=100)
        self.write(self.allocation_path, self.allocation)
        self.lease_path = self.directory/'lease.json'
        self.lease = dict(schema='R119_GRID_LEASE_BUDGET_V1', hard_end_unix=700, lease_end_unix=1100)
        self.write(self.lease_path, self.lease)
        self.config_path = self.directory/'guard.json'
        self.config = dict(schema='R125_CONTINUAL_GUARD_V1', plan_path=str(self.plan_path),
            plan_sha256=native.sha(self.plan_path),
            source_pins={str(path.relative_to(self.source)):native.sha(path)
                         for path in self.source.rglob('*.py')},
            host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
            hard_end_unix=700, next_reserved_unix=820, allocation_path=str(self.allocation_path),
            allocation_sha256=native.sha(self.allocation_path), lease_path=str(self.lease_path),
            lease_sha256=native.sha(self.lease_path), attempt_dir=str(self.attempt), resume=True)
        self.write(self.config_path, self.config)
        self.start_patch(patch.object(guard, '__file__', str(self.module)))
        self.start_patch(patch.object(guard.time, 'time', return_value=100))
        self.start_patch(patch.dict(os.environ, CUDA_VISIBLE_DEVICES=self.plan['gpu_uuid']))
        self.start_patch(patch.object(guard.subprocess, 'Popen', side_effect=AssertionError('no launches')))
        self.start_patch(patch.object(guard.subprocess, 'check_output', side_effect=AssertionError('no scans')))
        self.run = self.start_patch(patch.object(native, 'run'))

    def start_patch(self, patcher):
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    @staticmethod
    def write(path, document):
        Path(path).write_text(json.dumps(document, sort_keys=True)+'\n')

    def test_exact_source_plan_host_allocation_lease_and_margin_are_accepted(self):
        config, plan = guard.validate(self.config_path)
        self.assertEqual(config, self.config)
        self.assertEqual(plan, self.plan)
        self.run.assert_not_called()

    def test_config_mutations_reject_individual_bindings(self):
        cases = [
            ('schema', 'other', 'guard_schema'),
            ('plan_sha256', '0'*64, 'guard_plan_bytes'),
            ('source_pins', {}, 'entire_python_source_closure'),
            ('host_sha256', '0'*64, 'hashed_node_binding'),
            ('hard_end_unix', 701, 'one_bound_wall'),
            ('next_reserved_unix', 819, 'preserve_next_reservation'),
            ('allocation_sha256', '0'*64, 'posted_allocation_and_CPU_provenance'),
            ('lease_sha256', '0'*64, 'lease_receipt_bytes'),
            ('attempt_dir', 'relative', 'attempt_outside_source'),
            ('attempt_dir', str(self.source/'attempt'), 'attempt_outside_source'),
        ]
        alias = self.directory/'source-alias'
        alias.symlink_to(self.source, target_is_directory=True)
        cases.append(('attempt_dir', str(alias/'attempt'), 'attempt_outside_source'))
        for key, value, reason in cases:
            self.write(self.config_path, dict(self.config, **{key: value}))
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, reason):
                guard.validate(self.config_path)

    def test_semantically_identical_plan_with_different_bytes_is_rejected(self):
        self.plan_path.write_text(json.dumps(self.plan, indent=2))
        with self.assertRaisesRegex(ValueError, 'guard_plan_bytes'):
            guard.validate(self.config_path)

    def test_source_closure_detects_edits_additions_and_deletions(self):
        self.dependency.write_text('VALUE = 2\n')
        with self.assertRaisesRegex(ValueError, 'entire_python_source_closure'):
            guard.validate(self.config_path)
        self.dependency.write_text('VALUE = 1\n')
        extra = self.source/'extra.py'
        extra.write_text('EXTRA = True\n')
        with self.assertRaisesRegex(ValueError, 'entire_python_source_closure'):
            guard.validate(self.config_path)
        extra.unlink()
        self.dependency.unlink()
        with self.assertRaisesRegex(ValueError, 'entire_python_source_closure'):
            guard.validate(self.config_path)

    def test_rebound_plan_cannot_relocate_frozen_source(self):
        self.write(self.plan_path, dict(self.plan, source_root=str(self.directory/'elsewhere')))
        self.write(self.config_path, dict(self.config, plan_sha256=native.sha(self.plan_path)))
        with self.assertRaisesRegex(ValueError, 'frozen_source_location'):
            guard.validate(self.config_path)

    def test_rehashed_allocation_cannot_change_cpu_provenance_or_identity(self):
        cases = [('plan_sha256', '0'*64), ('cpu_tests_passed', False), ('cpu_tests_passed', 1),
                 ('gpu_uuid', 'GPU-other'), ('physical', 1), ('builder_entry_pushed', False),
                 ('builder_entry_pushed', 1)]
        for key, value in cases:
            self.write(self.allocation_path, dict(self.allocation, **{key: value}))
            self.write(self.config_path, dict(self.config, allocation_sha256=native.sha(self.allocation_path)))
            with self.subTest(key=key, value=value), \
                    self.assertRaisesRegex(ValueError, 'posted_allocation_and_CPU_provenance'):
                guard.validate(self.config_path)

    def test_allocation_cannot_be_dated_in_future(self):
        self.write(self.allocation_path, dict(self.allocation, declared_unix=100.001))
        self.write(self.config_path, dict(self.config, allocation_sha256=native.sha(self.allocation_path)))
        with self.assertRaisesRegex(ValueError, 'allocation_not_future'):
            guard.validate(self.config_path)

    def test_lease_byte_drift_is_rejected_without_rebinding(self):
        self.write(self.lease_path, dict(self.lease, hard_end_unix=701))
        with self.assertRaisesRegex(ValueError, 'lease_receipt_bytes'):
            guard.validate(self.config_path)

    def test_rehashed_lease_still_cannot_drift_end_or_shorten_hard_wall(self):
        for changes in (dict(lease_end_unix=1099), dict(lease_end_unix=1101), dict(hard_end_unix=699)):
            self.write(self.lease_path, dict(self.lease, **changes))
            self.write(self.config_path, dict(self.config, lease_sha256=native.sha(self.lease_path)))
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, 'existing_lease_margin_preserved'):
                guard.validate(self.config_path)

    def test_rebound_plan_cannot_extend_posted_lease_wall(self):
        for changes in (dict(hard_end_unix=701), dict(lease_end_unix=1101)):
            plan = dict(self.plan, **changes)
            self.write(self.plan_path, plan)
            self.write(self.config_path, dict(self.config, plan_sha256=native.sha(self.plan_path),
                hard_end_unix=plan['hard_end_unix'], next_reserved_unix=900))
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, 'existing_lease_margin_preserved'):
                guard.validate(self.config_path)

    def test_documented_lease_receipt_is_accepted_at_exact_hard_wall(self):
        lease = dict(schema='R119_GRID_LEASE_BUDGET_V1', hard_end_unix=1789596240, lease_end_unix=1789617840)
        plan = dict(self.plan, hard_end_unix=lease['hard_end_unix'], lease_end_unix=lease['lease_end_unix'])
        self.write(self.plan_path, plan)
        self.write(self.lease_path, lease)
        self.write(self.allocation_path, dict(self.allocation, plan_sha256=native.sha(self.plan_path)))
        self.write(self.config_path, dict(self.config, plan_sha256=native.sha(self.plan_path),
            allocation_sha256=native.sha(self.allocation_path), lease_sha256=native.sha(self.lease_path),
            hard_end_unix=lease['hard_end_unix'], next_reserved_unix=lease['hard_end_unix']+120))
        self.assertEqual(guard.validate(self.config_path)[1], plan)

    def prepare_launch(self):
        (self.attempt/'DISPATCH_ONCE').mkdir()
        self.report = dict(scanner_euid=0, clear=True, blocking_reasons=[], gpu=dict(uuid=self.plan['gpu_uuid']))
        self.write(self.attempt/'ADMISSION.json', self.report)
        parent_pid = os.getppid()
        ticks = Path('/proc', str(parent_pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
        self.launch = dict(pid=parent_pid, parent_start_ticks=ticks, guard_sha256=native.sha(self.config_path),
            admission_sha256=native.sha(self.attempt/'ADMISSION.json'), admission_verified_unix=100)
        self.write(self.attempt/'LAUNCH.json', self.launch)

    def enter(self, startup=b'LAUNCH_READY\n'):
        reader, writer = os.pipe()
        with os.fdopen(reader, 'rb') as stream:
            try:
                os.write(writer, startup)
            finally:
                os.close(writer)
            with patch.object(guard.sys, 'stdin', stream):
                guard.native_entry(self.config_path)

    def test_native_entry_binds_real_parent_startup_and_resume_flag(self):
        self.prepare_launch()
        observed = []
        self.run.side_effect = lambda *args, **kwargs: observed.append(os.environ['R125_ADMISSION_PLAN_SHA256'])
        self.enter()
        self.run.assert_called_once_with(self.config['plan_path'], resume=True)
        self.assertEqual(observed, [self.config['plan_sha256']])

    def test_native_startup_requires_exact_signal_before_running(self):
        self.prepare_launch()
        for startup in (b'', b'READY\n', b'LAUNCH_READY\nextra'):
            with self.subTest(startup=startup), self.assertRaisesRegex(ValueError, 'supervisor_startup_barrier'):
                self.enter(startup)
        self.run.assert_not_called()

    def test_native_launch_mutations_fail_before_run(self):
        self.prepare_launch()
        cases = [('pid', os.getppid()+1, 'actual_timeout_parent'),
                 ('parent_start_ticks', 'not-parent-start', 'launch_process_and_config_binding'),
                 ('guard_sha256', '0'*64, 'launch_process_and_config_binding'),
                 ('admission_sha256', '0'*64, 'fresh_clear_admission'),
                 ('admission_verified_unix', -20.001, 'fresh_clear_admission'),
                 ('admission_verified_unix', 100.001, 'fresh_clear_admission')]
        for key, value, reason in cases:
            self.write(self.attempt/'LAUNCH.json', dict(self.launch, **{key: value}))
            with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, reason):
                self.enter()
        self.run.assert_not_called()

    def test_exact_admission_age_boundary_is_accepted(self):
        self.prepare_launch()
        self.write(self.attempt/'LAUNCH.json', dict(self.launch, admission_verified_unix=-20))
        self.enter()
        self.run.assert_called_once()

    def test_rehashed_admission_cannot_change_owner_clearance_or_gpu(self):
        self.prepare_launch()
        for changes in (dict(scanner_euid=1000), dict(clear=False), dict(blocking_reasons=['open_device_pid:42']),
                        dict(gpu=dict(uuid='GPU-other'))):
            self.write(self.attempt/'ADMISSION.json', dict(self.report, **changes))
            self.write(self.attempt/'LAUNCH.json', dict(self.launch,
                admission_sha256=native.sha(self.attempt/'ADMISSION.json')))
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, 'fresh_clear_admission'):
                self.enter()
        self.run.assert_not_called()

    def test_gpu_environment_and_dispatch_directory_required(self):
        self.prepare_launch()
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='GPU-other'):
            with self.assertRaisesRegex(ValueError, 'native_GPU_binding'):
                self.enter()
        (self.attempt/'DISPATCH_ONCE').rmdir()
        with self.assertRaisesRegex(ValueError, 'actual_timeout_parent'):
            self.enter()
        self.run.assert_not_called()

    def test_scan_uses_route_admission_and_preserves_device_ownership_checks(self):
        from gpu import orch_r111_route_admission as admission
        from gpu import orch_rich_hot_a100_minor_scan as minor
        identity = dict(pid=41, uid=1000, start_ticks='555', boot_id='synthetic', command_sha256='first')
        samples = [dict(identity, command_sha256=command, executable_identity=[1, 2],
            target_open=False, visibility_complete=True, cvd=None) for command in ('first', 'second', 'second')]
        report = dict(scanner_euid=0, gpu=dict(uuid=self.plan['gpu_uuid'], memory_used_mib=1),
            compute_processes=[], processes=[dict(identity, pinned_identity=identity, target_device_open=False, cvd=None)],
            blocking_reasons=['process_identity_drift:41', 'minor_scan_identity_changed:41'], clear=False)
        service_path = self.attempt/'SERVICE_IDENTITY.json'
        native.write_once(service_path, {'synthetic': True})

        def scanner(index, service):
            self.assertEqual(index, self.plan['physical'])
            self.assertEqual(service, service_path)
            self.assertEqual(minor.pinned.policy.HOST_SHA, self.config['host_sha256'])
            self.assertEqual(minor.pinned.policy.DEVICES, {index: self.plan['gpu_uuid']})
            minor.pinned.policy.allocation(index)
            with self.assertRaisesRegex(ValueError, 'only_allocated_device'):
                minor.pinned.policy.allocation(index+1)
            return admission.reconcile(report, {41: samples})

        with patch.object(minor.pinned, 'policy'), patch.object(minor.pinned, 'service') as service, \
                patch.object(admission, 'scan', side_effect=scanner) as scan, \
                patch.object(guard.os, 'geteuid', return_value=0), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=''):
            before = deepcopy(report)
            result = guard.scan(self.config_path)
            self.assertTrue(result['clear'])
            self.assertEqual(report, before)
            self.assertEqual(result['gpu']['memory_used_mib'], 1)
            self.assertTrue(result['target_device_ownership_checks_unchanged'])
            self.assertEqual(result['unreconciled_blocking_reasons'], before['blocking_reasons'])
            for key, value in (('target_open', True), ('visibility_complete', False),
                               ('start_ticks', 'reused'), ('cvd', self.plan['gpu_uuid'])):
                original = samples[1][key]
                samples[1][key] = value
                with self.subTest(key=key):
                    self.assertFalse(guard.scan(self.config_path)['clear'])
                samples[1][key] = original
            report['gpu']['memory_used_mib'] = 2
            self.assertFalse(guard.scan(self.config_path)['clear'])
            report['gpu']['memory_used_mib'] = 1
            report['blocking_reasons'].append('open_device_pid:41')
            self.assertFalse(guard.scan(self.config_path)['clear'])
            self.assertEqual(scan.call_count, 7)
            service.assert_not_called()

    def test_scan_refuses_nonprivileged_or_visible_gpu_environment(self):
        from gpu import orch_r111_route_admission as admission
        with patch.object(admission, 'scan') as scan:
            for uid, visibility in ((1000, ''), (0, self.plan['gpu_uuid'])):
                with self.subTest(uid=uid, visibility=visibility), \
                        patch.object(guard.os, 'geteuid', return_value=uid), \
                        patch.dict(os.environ, CUDA_VISIBLE_DEVICES=visibility), \
                        self.assertRaisesRegex(ValueError, 'privileged_CPU_scan'):
                    guard.scan(self.config_path)
            scan.assert_not_called()


if __name__ == '__main__':
    unittest.main()
