from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r145_a40r7_readmission as readmission


class BeforeNativeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.control = Path(temporary.name)
        self.config = dict(attempt_dir=str(self.control))
        patcher = patch.object(readmission.recovery, 'RECOVERY', self.control / 'recovery')
        patcher.start()
        self.addCleanup(patcher.stop)
        (self.control / 'SUPERVISOR.log').write_text('ValueError: unchanged_global_exclusive_admission\n')
        self.write('ADMISSION.json',dict(clear=False,scanner_euid=0,blocking_reasons=['process_identity_drift:123']))
        self.write('SUPERVISOR_DISPATCH.json',dict(pid=999999999))

    def write(self,name,value):
        (self.control / name).write_text(json.dumps(value))

    def validate(self):
        return readmission.validate_denial(self.control,self.config)

    def test_exact_denial_allows_new_scan_not_waiver(self):
        self.assertFalse(self.validate()['clear'])

    def test_possible_native_or_admission_time_blocks(self):
        for name in ('CONTAINED_COMMAND.json','CONTAINMENT_VERIFIED.json','LAUNCH.json','NATIVE.log',
                     'EXIT.json','SERVICE_EXIT.json','ADMISSION_TIME.json'):
            with self.subTest(name=name):
                self.write(name,{})
                with self.assertRaisesRegex(ValueError,'no_possible_native_dispatch'):
                    self.validate()
                (self.control / name).unlink()

    def test_no_OOM_or_started_recovery_retry(self):
        (self.control / 'recovery').mkdir()
        with self.assertRaisesRegex(ValueError,'no_started_recovery'):
            self.validate()

    def test_foreign_device_nonroot_clear_or_empty_rejected(self):
        for report in (dict(clear=False,scanner_euid=0,blocking_reasons=['open_device_pid:1']),
                       dict(clear=False,scanner_euid=0,blocking_reasons=[]),
                       dict(clear=False,scanner_euid=2524,blocking_reasons=['process_identity_drift:123']),
                       dict(clear=True,scanner_euid=0,blocking_reasons=['process_identity_drift:123'])):
            with self.subTest(report=report):
                self.write('ADMISSION.json',report)
                with self.assertRaises(ValueError):
                    self.validate()

    def test_live_supervisor_rejected(self):
        self.write('SUPERVISOR_DISPATCH.json',dict(pid=1))
        with self.assertRaisesRegex(ValueError,'previous_supervisor_exited'):
            self.validate()

    def test_other_failure_rejected(self):
        (self.control / 'SUPERVISOR.log').write_text('CUDA OOM')
        with self.assertRaisesRegex(ValueError,'only_original_pre_native_admission_error'):
            self.validate()

    def test_config_only_relocates_unit_and_attempt(self):
        config = dict(attempt_dir='/old', device_containment=dict(unit='old',minor=4,uid=2524,gid=2524),
                      lease='same',source_pins={'source':'same'},ack={'sha':'same'})
        before = deepcopy(config)
        result = readmission.revised_config(config,'/new','newunit')
        self.assertEqual(config,before)
        result['attempt_dir'] = config['attempt_dir']
        result['device_containment']['unit'] = config['device_containment']['unit']
        self.assertEqual(result,config)


if __name__ == '__main__':
    unittest.main()
