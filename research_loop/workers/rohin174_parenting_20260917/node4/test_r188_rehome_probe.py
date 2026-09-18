"""CPU tests for the narrow receiving-device probe, without GPU access."""

from pathlib import Path
import unittest

import r188_rehome_probe as probe


class ReceivingProbeTests(unittest.TestCase):
    def setUp(self):
        self.reference = (Path(__file__).resolve().parents[4] / 'gpu/orch_r137_node4_containment.py').read_text()

    def test_exact_three_target_mappings_and_seven_device_exclusions(self):
        for physical, (gpu_uuid, minor) in probe.DEVICES.items():
            command, policy = probe.command(physical, self.reference, 'orch-r136-nvml-' + 'a' * 32)
            self.assertEqual(policy, dict(uid=2524, gid=2524, minor=minor, unit='orch-r136-nvml-' + 'a' * 32))
            self.assertIn('CUDA_VISIBLE_DEVICES=' + gpu_uuid, command)
            self.assertIn('--property=DevicePolicy=strict', command)
            self.assertIn('--property=DeviceAllow=', command)
            self.assertIn('--property=DeviceAllow=/dev/nvidia' + str(minor) + ' rw', command)
            for foreign in set(range(8)) - {minor}:
                self.assertNotIn('--property=DeviceAllow=/dev/nvidia' + str(foreign) + ' rw', command)
            self.assertIn('--property=RuntimeMaxSec=45', command)
            self.assertIn('--property=CapabilityBoundingSet=', command)
            self.assertIn('--property=NoNewPrivileges=yes', command)

    def test_other_devices_and_changed_reference_rejected(self):
        for physical in (0, 1, 2, 3, 4, 8, True):
            with self.assertRaisesRegex(ValueError, 'only_reserved'):
                probe.command(physical, self.reference, 'orch-r136-nvml-' + 'a' * 32)
        with self.assertRaisesRegex(ValueError, 'unchanged_R137'):
            probe.command(5, self.reference + '\n', 'orch-r136-nvml-' + 'a' * 32)

    def test_invalid_service_name_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unique_probe_unit'):
            probe.command(7, self.reference, 'existing-service')


if __name__ == '__main__':
    unittest.main()
