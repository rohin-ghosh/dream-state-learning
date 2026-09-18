import copy
import importlib.util
from pathlib import Path
import unittest

from gpu import ny_caption_vision as vision


specification = importlib.util.spec_from_file_location('vision_owner_entry', Path(__file__).with_name('owner_entry.py'))
owner = importlib.util.module_from_spec(specification)
specification.loader.exec_module(owner)


class OwnerEntryTests(unittest.TestCase):
    def setUp(self):
        self.metadata_pin = dict(path='/metadata', sha256='a' * 64)
        self.config_pin = dict(path='/config', sha256='b' * 64)
        self.metadata = dict(code=dict(sha256='c' * 64), packet=dict(sha256='d' * 64),
            snapshot=dict(sha256='e' * 64), cpu_receipt=dict(path='/cpu', sha256='f' * 64),
            entrypoint=dict(path='/entry'), max_gpu_seconds=3600)
        self.config = dict(metadata_pins=[self.metadata_pin], entrypoint='/entry', command=['/entry'],
            physical=5, minor=6, gpu_uuid=vision.GPU_UUID, hard_end_unix=owner.HARD_END,
            seconds=3570, created_unix=100, end_unix=3670, unit='orch-r177-slot5-' + 'a' * 32,
            lease=dict(path='/lease', sha256='0' * 64))
        self.scan = dict(config=self.config_pin, original_scanner_unmodified=True, verified_unix=100,
            report=dict(path='/scan', sha256='1' * 64))
        self.execute = dict(pid=55, config=self.config_pin, command=['/entry'], no_retry=True,
            status='EXEC_REQUESTED_NOT_MODEL_LOAD')
        self.containment = dict(pid=55, configuration=self.config_pin, physical=5,
            gpu_uuid=vision.GPU_UUID, minor=6, target_open_close=True,
            denied_foreign_minors=[0, 1, 2, 3, 4, 5, 7])

    def build(self, **overrides):
        arguments = dict(metadata=self.metadata, metadata_pin=self.metadata_pin, config=self.config,
            config_pin=self.config_pin, scan_binding=self.scan, owner_exec=self.execute,
            containment=self.containment, now=105, process_id=55)
        arguments.update(overrides)
        return owner.build_admission(**arguments)

    def test_exact_bound_admission_has_kernel_minor_six_and_cleanup_allowance(self):
        admission = self.build()
        self.assertEqual(admission['kernel_minor'], 6)
        self.assertEqual(admission['outer_slot_config'], self.config_pin)
        self.assertEqual(admission['hard_end_unix'], owner.HARD_END)
        self.assertEqual(admission['max_gpu_seconds'], 3600)

    def test_wrong_exec_pid_or_command_is_never_replayed(self):
        for fields in ({'pid': 99}, {'command': ['/other']}, {'no_retry': False}):
            with self.subTest(fields=fields), self.assertRaises(vision.VisionError):
                self.build(owner_exec=dict(self.execute, **fields))

    def test_stale_future_or_changed_scan_fails(self):
        for fields in ({'verified_unix': 0}, {'verified_unix': 106}, {'original_scanner_unmodified': False}):
            with self.subTest(fields=fields), self.assertRaises(vision.VisionError):
                self.build(scan_binding=dict(self.scan, **fields))

    def test_wrong_minor_or_incomplete_denials_fail(self):
        for fields in ({'minor': 5}, {'denied_foreign_minors': [0, 1]}, {'target_open_close': False}):
            with self.subTest(fields=fields), self.assertRaises(vision.VisionError):
                self.build(containment=dict(self.containment, **fields))

    def test_full_hour_runtime_plus_cleanup_is_rejected(self):
        with self.assertRaises(vision.VisionError):
            self.build(config=dict(self.config, seconds=3600))

    def test_unbound_metadata_or_other_device_fails(self):
        for fields in ({'metadata_pins': []}, {'physical': 2}, {'gpu_uuid': 'different'},
                       {'hard_end_unix': owner.HARD_END + 1}):
            with self.subTest(fields=fields), self.assertRaises(vision.VisionError):
                self.build(config=dict(self.config, **fields))

    def test_no_model_or_service_is_called_by_admission_construction(self):
        before = copy.deepcopy(self.config)
        self.build()
        self.assertEqual(self.config, before)


if __name__ == '__main__':
    unittest.main()
