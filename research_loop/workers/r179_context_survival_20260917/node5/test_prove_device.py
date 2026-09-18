import importlib.util
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('node5_device_probe', Path(__file__).with_name('prove_device.py'))
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


class DeviceProbeTests(unittest.TestCase):
    def provider(self, physical):
        def read(path):
            if path.name == 'GUARD.json':
                return {'device_containment': {'unit': 'original'}}
            return {'physical': physical}

        def strict_command(saved, config, plan, root):
            if physical == 7:
                self.assertIsNotNone(re.fullmatch(r'orch-r136-native-[a-f0-9]{32}',
                                                 config['device_containment']['unit']))
            return ['strict-prefix', '/python', '-B', str(root / 'rollout_operator.py'),
                    'contained', '--output', str(root)]

        return SimpleNamespace(read=read, PYTHON='/python', load_auxiliary=lambda name: None,
                               strict_command=strict_command)

    def test_one_construction_error_preserves_other_receipts(self):
        with patch.object(probe, 'ATTEMPTS', {'first': 1, 'second': 2}), \
             patch.object(probe, 'load_operator', side_effect=[ValueError('exact_test_failure'), self.provider(0)]), \
             patch.object(probe.subprocess, 'run', return_value=SimpleNamespace(returncode=0,
                 stdout=json.dumps({'status': 'PASS'}), stderr='')):
            rows = probe.remote('source')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['error_type'], 'ValueError')
        self.assertEqual(rows[0]['error'], 'exact_test_failure')
        self.assertIsNone(rows[0]['returncode'])
        self.assertEqual(rows[1]['result']['status'], 'PASS')

    def test_reader_CPU_probe_respects_exact_capsule_unit_rule(self):
        with patch.object(probe, 'ATTEMPTS', {'repo_reader': 2}), \
             patch.object(probe, 'load_operator', return_value=self.provider(7)), \
             patch.object(probe.subprocess, 'run', return_value=SimpleNamespace(returncode=0,
                 stdout=json.dumps({'status': 'PASS'}), stderr='')) as run:
            rows = probe.remote('source')
        self.assertEqual(rows[0]['returncode'], 0)
        command = run.call_args.args[0]
        self.assertIn('--check', command)
        self.assertIsNotNone(re.fullmatch(r'orch-r136-native-[a-f0-9]{32}', command[-1]))


if __name__ == '__main__':
    unittest.main()
