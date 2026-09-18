"""CPU admission-contract tests; actual NODE4 device denial is a receiving test."""

from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

from gpu import orch_r179_node4_legacy_containment as containment


class LegacyContainmentTests(unittest.TestCase):
    def setUp(self):
        self.plan = dict(physical=0, gpu_uuid=containment.DEVICES[0], root=containment.ROOTS[0],
            hard_end_unix=1789754400.0, source_root='/localhome/local-rohing/context/source')
        self.config = dict(host_sha256=containment.HOST_SHA, resume=True,
            hard_end_unix=self.plan['hard_end_unix'], device_containment=dict(uid=2524, gid=2524,
                minor=5, unit='orch-r136-native-' + 'a'*32))

    def command(self, **changes):
        parameters = dict(physical=0, minor=5, uid=2524, gid=2524,
            unit=self.config['device_containment']['unit'], source=self.plan['source_root'],
            command=['python', '-B', '-m', 'example'], lifetime=120)
        parameters.update(changes)
        return containment.device_containment_command(**parameters)

    def test_scope_is_exact_existing_life_device_and_saved_resume(self):
        containment.validate_scope(self.config, self.plan)
        for change in ({'physical': 2}, {'physical': True}, {'gpu_uuid': containment.DEVICES[1]},
                       {'root': '/localhome/local-rohing/other/run1'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                containment.validate_scope(self.config, dict(self.plan, **change))
        for change in ({'host_sha256': '0'*64}, {'resume': False}, {'hard_end_unix': 0}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                containment.validate_scope(dict(self.config, **change), self.plan)

    def test_command_allows_only_mapped_minor_with_no_privilege_escape(self):
        command = self.command()
        for expected in ('--property=DevicePolicy=strict', '--property=NoNewPrivileges=yes',
                         '--property=CapabilityBoundingSet=', '--property=AmbientCapabilities=',
                         '--property=ProtectControlGroups=yes', '--property=DeviceAllow=',
                         '--property=DeviceAllow=/dev/nvidia5 rw', '--property=RuntimeMaxSec=120',
                         'CUDA_VISIBLE_DEVICES=' + containment.DEVICES[0], '-i'):
            self.assertIn(expected, command)
        for minor in range(8):
            if minor != 5:
                self.assertNotIn('--property=DeviceAllow=/dev/nvidia' + str(minor) + ' rw', command)

    def test_command_rejects_broad_scope_or_unbounded_service(self):
        for changes in ({'physical': 3}, {'minor': 8}, {'minor': True}, {'uid': 0}, {'gid': 0},
                        {'unit': 'reused'}, {'source': 'relative'}, {'source': '/tmp/../other'},
                        {'lifetime': 0}, {'lifetime': 172801}, {'command': 'sh -c anything'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.command(**changes)

    def verify(self, foreign_open=None, descriptors=None, minor=5, cgroup=None):
        if cgroup is None:
            cgroup = '0::/system.slice/' + self.config['device_containment']['unit'] + '.service'
        with patch.object(containment, 'require_host'), patch.object(containment.os, 'getuid', return_value=2524), \
             patch.object(containment.os, 'getgid', return_value=2524), \
             patch.object(Path, 'read_text', return_value=cgroup), \
             patch.object(containment, 'device_minor', return_value=minor), \
             patch.object(containment, 'gpu_descriptors', return_value=descriptors or []), \
             patch.object(containment.os, 'open', side_effect=foreign_open or PermissionError()) as opened, \
             patch.object(containment.os, 'close') as closed, \
             patch.dict(containment.os.environ, CUDA_VISIBLE_DEVICES=self.plan['gpu_uuid']):
            result = containment.verify_device_containment(self.config, self.plan)
            return result, opened.call_args_list, closed.call_count

    def test_probe_requires_all_seven_foreign_minor_denials(self):
        result, opened, closed = self.verify()
        self.assertEqual(result['denied_foreign_minors'], [0, 1, 2, 3, 4, 6, 7])
        self.assertEqual(len(opened), 7)
        self.assertEqual(closed, 0)

    def test_one_foreign_success_is_fatal(self):
        with self.assertRaisesRegex(ValueError, 'foreign_GPU_not_denied'):
            self.verify(foreign_open=lambda *arguments: 99)

    def test_probe_rejects_inherited_fd_wrong_minor_and_wrong_cgroup(self):
        for changes in ({'descriptors': [{'fd': 9}]}, {'minor': 0}, {'cgroup': '0::/user.slice'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.verify(**changes)

    def test_other_nonroot_identity_is_not_silently_substituted(self):
        changed = deepcopy(self.config)
        changed['device_containment']['uid'] = 1000
        with self.assertRaisesRegex(ValueError, 'node4_nonroot_identity'):
            containment.validate_scope(changed, self.plan)


if __name__ == '__main__':
    unittest.main()
